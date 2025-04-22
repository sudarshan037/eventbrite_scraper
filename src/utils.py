import time
import asyncio
import hashlib
import random
from src.scrapers import letsdo_links, classpass_links
from src.scrapers import eventbrite_events, dice_events, shotgun_events, letsdo_events, ra_events
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import os
import sqlite3
import signal
from src import bulk_upload

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
        # await page.route("**/*.{woff,woff2,ttf,otf}", block_unwanted)  # Block fonts

        # Apply stealth mode
        if scraper_name in ["letsdo_links", "classpass_links"]:
            wait_until="networkidle"
        else:
            wait_until="domcontentloaded"
            await stealth_async(page)

        for attempt in range(3):
            try:
                await page.goto(url, wait_until=wait_until, timeout=30000)
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
        # await page.screenshot(path=f"screenshots/screenshot_{record['id']}.png", full_page=True)
                
        record["processed"] = True
        record["processing"] = False

        record = {key: value for key, value in record.items() if not key.startswith('_')}
        if scraper_name=="dice_events":
            record = await dice_events.process(record, page)
        elif scraper_name=="eventbrite_events":
            record = await eventbrite_events.process(record, page)
        elif scraper_name=="shotgun_events":
            record = await shotgun_events.process(record, page)
        elif scraper_name=="letsdo_links":
            record = await letsdo_links.process(record, page)
        elif scraper_name=="letsdo_events":
            record = await letsdo_events.process(record, page)
        elif scraper_name=="ra_events":
            record = await ra_events.process(record, page)
        elif scraper_name=="classpass_links":
            record = await classpass_links.process(record, page)
        else:
            pass
        
        # await asyncio.sleep(30)
        print(f"{bcolors.OKBLUE}OUTPUT: {record}{bcolors.ESCAPE}")
        if "_links" in scraper_name:
            await bulk_upload.intermediate_upload(record["events"], record["url"], record["sheet_name"], scraper_name.replace("links", "events"))
            record.pop("events", None)
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

async def migrate_data_to_cosmos_and_cleanup(azure_cosmos, sqlite_db_path, cosmos_container_name, batch_size=100):
    """
    Move data from the SQLite 'events' table to the specified Cosmos container
    using bulk upload and delete the SQLite database afterward.
    """
    try:
        # Connect to SQLite database and fetch data
        conn = sqlite3.connect(sqlite_db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT source_url, url, sheet_name FROM letsdo_events")
        rows = cursor.fetchall()
        print(rows)
        # Divide rows into batches
        total_rows = len(rows)
        print(f"Total records fetched from SQLite: {total_rows}")

        for i in range(0, total_rows, batch_size):
            batch = rows[i:i + batch_size]
            print(f"Processing batch {i // batch_size + 1} with {len(batch)} records.")

            # Prepare items for bulk upload
            valid_items = []
            for source_url, url, sheet_name in batch:
                if source_url and url:  # Validate critical fields
                    hash_key = sheet_name + url
                    item = {
                        "id": hashlib.sha256(hash_key.encode()).hexdigest(),
                        "source_url": source_url,
                        "url": url,
                        "sheet_name": sheet_name or "",  # Default empty string if None
                    }
                    valid_items.append(item)
                else:
                    print(f"Skipping invalid record: source_url={source_url}, url={url}")

            # Perform bulk upload
            await azure_cosmos.initialize_cosmosdb("Scraper", cosmos_container_name)
            for item in valid_items:
                try:
                    await azure_cosmos.container.upsert_item(item)
                except Exception as e:
                    print(f"Error inserting item {item.get('id', '<missing id>')}: {e}")

        # Close SQLite connection
        conn.close()

        # Delete SQLite database
        os.remove(sqlite_db_path)
        print(f"SQLite database {sqlite_db_path} deleted successfully.")

    except Exception as e:
        print(f"Error during migration or cleanup: {e}")

async def process_urls_concurrently(azure_cosmos, scraper_name, vm_offset, batch_size=100, max_workers=1, vm_name="local"):
    print(f"max_workers: {max_workers}")
    """Process URLs fetched from CosmosDB."""
    async with azure_cosmos.client:
        try:
            while True:
                t1_batch = time.perf_counter()
                # Fetch a batch of URLs for this VM
                records = await fetch_urls_for_vm(azure_cosmos.container, vm_offset=vm_offset, batch_size=batch_size, vm_name=vm_name, max_workers=max_workers)
                if not records:
                    print("No unprocessed URLs found. Exiting.")
                    raise Exception("No unprocessed URLs found.")
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
        except:
            if scraper_name == "letsdo_links" and os.path.exists("Scraper.db"):
                await migrate_data_to_cosmos_and_cleanup(azure_cosmos, "Scraper.db", "letsdo_events")