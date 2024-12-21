import time
import asyncio
import hashlib
import random
from src.scrapers import eventbrite_events, dice_events
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ESCAPE = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


async def get_text(page, selector):
    element = await page.query_selector(selector)
    return await element.inner_text() if element else ""

async def process_page(container, scraper_name, record):
    url = record["url"]
    print(f"{bcolors.OKGREEN}URL: {url}{bcolors.ESCAPE}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=[
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-renderer-backgrounding",
                "--disable-background-timer-throttling",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
            headless=False,
        )
        context = await browser.new_context()
        page = await context.new_page()

        async def block_unwanted(route):
            await route.abort()

        await page.route("**/*.{png,jpeg,webp,gif,svg}", block_unwanted)  # Block images
        await page.route("**/*.jpg?*", block_unwanted)  # Block images
        await page.route("**/*.{woff,woff2,ttf,otf}", block_unwanted)  # Block fonts

        # Apply stealth mode
        await stealth_async(page)

        for attempt in range(3):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                break
            except Exception as e:
                await asyncio.sleep(random.uniform(2, 5))
                if attempt == 2:  # Final attempt
                    print(f"Error navigating to {url}: {e}")
                    record["processed"] = True
                    record["error"] = f"Navigation error: {e}"
                    await container.replace_item(
                        item=record["id"],
                        body=record
                    )
                    return
        await page.screenshot(path=f"screenshots/screenshot_3.png")
                
        record["processed"] = True
        record["processing"] = False

        record = {key: value for key, value in record.items() if not key.startswith('_')}


        match scraper_name:
            case "dice_events":
                record = await dice_events.process(record, page)
            case "eventbrite_events":
                record = await eventbrite_events.process(record, page)
            case _:
                pass

        print(f"{bcolors.OKBLUE}OUTPUT: {record}{bcolors.ESCAPE}")
        await container.replace_item(item=record["id"], body=record)
        await context.close()
        await browser.close()


async def fetch_urls_for_vm(container_client, vm_offset=0, batch_size=100, vm_name="local", max_workers=1):
    """Fetch a batch of unprocessed URLs and mark them as processing."""
    query = f"SELECT * FROM c WHERE c.processed = false AND (NOT IS_DEFINED(c.processing) OR c.processing = '{vm_name}') OFFSET {vm_offset} LIMIT {batch_size}"
    items = [item async for item in container_client.query_items(query=query)]

    if not items:
        query = f"SELECT * FROM c WHERE c.processed = false AND (NOT IS_DEFINED(c.processing) OR c.processing = '{vm_name}') OFFSET 0 LIMIT {batch_size}"
        items = [item async for item in container_client.query_items(query=query)]

    if not items:
        query = f"SELECT * FROM c WHERE c.processed = false OFFSET 0 LIMIT {batch_size//2}"
        items = [item async for item in container_client.query_items(query=query)]

    semaphore = asyncio.Semaphore(max_workers)

    async def upsert_with_semaphore(item):
        async with semaphore:
            item['processing'] = vm_name
            await container_client.replace_item(item=item["id"], body=item)
    
    # Lock items for processing concurrently with semaphore
    tasks = [upsert_with_semaphore(item) for item in items]

    # Run all tasks concurrently
    await asyncio.gather(*tasks)
    
    return [item for item in items]

async def process_urls_concurrently(azure_cosmos, scraper_name, vm_offset, batch_size=100, max_workers=1, vm_name="local"):
    print(f"max_workers: {max_workers}")
    """Process URLs fetched from CosmosDB."""
    while True:
        t1_batch = time.perf_counter()
        # Fetch a batch of URLs for this VM
        records = await fetch_urls_for_vm(azure_cosmos.container, vm_offset=vm_offset, batch_size=batch_size, vm_name=vm_name, max_workers=max_workers)
        if not records:
            print("No unprocessed URLs found. Exiting.")
            break
        t2_batch = time.perf_counter()
        print(f"{bcolors.FAIL}Records Fetch: {round(t2_batch-t1_batch, 2)} sec.{bcolors.ESCAPE}")

        semaphore = asyncio.Semaphore(max_workers)

        async def process_with_semaphore(record):
            async with semaphore:
                await process_page(azure_cosmos.container, scraper_name, record)

        # Create tasks with concurrency control
        tasks = [process_with_semaphore(record) for record in records]
        await asyncio.gather(*tasks)

        t3_batch = time.perf_counter()
        print(f"{bcolors.FAIL}Records Fetch: {round(t2_batch-t1_batch, 2)} sec.\nBatch Scrapping: {round(t3_batch-t2_batch, 2)} sec.\nBatch Total: {round(t3_batch-t1_batch, 2)} sec.{bcolors.ESCAPE}")
    await azure_cosmos.client.close()