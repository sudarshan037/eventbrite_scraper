import asyncio
import argparse
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import time
import random
import hashlib
import pandas as pd
from azure.cosmos import CosmosClient
from eventbrite_scraper.utils import bcolors

COSMOS_DB_URI = "https://cosmos-scraper.documents.azure.com:443/"
COSMOS_DB_KEY = "bBgVEeSnEQaSss88e8zZU5pjpiVzPjba5qpe6alFqU548KcW2eMkCeUf7J99RWVUPw6ASV32W8pGACDb5ZhxrA=="
COSMOS_DB_DATABASE = "Scraper"
COSMOS_DB_CONTAINER = "dice_events"

client = CosmosClient(COSMOS_DB_URI, COSMOS_DB_KEY)
database = client.get_database_client(COSMOS_DB_DATABASE)
container = database.get_container_client(COSMOS_DB_CONTAINER)

async def process_page(url, sheet_name):
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
        )  # Use headless for faster processing
        context = await browser.new_context()
        page = await context.new_page()

        # Apply stealth mode
        await stealth_async(page)

        for attempt in range(3):
            try:
                await page.goto(url, wait_until="domcontentloaded")
                break
            except Exception as e:
                if attempt == 2:  # Final attempt
                    print(f"Error navigating to {url}: {e}")
                    container.upsert_item({
                        "id": hashlib.sha256((sheet_name + url).encode()).hexdigest(),
                        "url": url,
                        "sheet_name": sheet_name,
                        "processed": False,
                        "error": f"Navigation error: {e}"
                    })
                    return

        try:
            await page.wait_for_selector("//h1[@class='EventDetailsTitle__Title-sc-8ebcf47a-0 iLdkPz']", timeout=5000)
            await page.wait_for_selector("//div[contains(@class, 'EventDetailsTitle__Date-sc-8ebcf47a-2')]", timeout=5000)
        except Exception as e:
            print(f"{bcolors.WARNING}Some items are not found for {url}: {e}{bcolors.ESCAPE}")

        hash_key = sheet_name + url
        item = {}
        item["id"] = hashlib.sha256(hash_key.encode()).hexdigest()
        item["url"] = url
        item["processed"] = True
        item["processing"] = False
        item["sheet_name"] = sheet_name

        # await page.screenshot(path=f"screenshots/screenshot_{hashlib.sha256(hash_key.encode()).hexdigest()}.png")

        # Safe data extraction
        async def get_text(selector):
            element = await page.query_selector(selector)
            return await element.inner_text() if element else ""

        try:
            item["event_name"] = await get_text("//h1[@class='EventDetailsTitle__Title-sc-8ebcf47a-0 iLdkPz']")
            item["date"] = await get_text("//div[contains(@class, 'EventDetailsTitle__Date-sc-8ebcf47a-2')]")
            item["location"] = await get_text("//div[@class='EventDetailsVenue__Address-sc-42637e02-5 cxsjwk']/span")
            item["organiser_name"] = await get_text("//div[contains(@class, 'EventDetailsBase__Highlight-sc-d40475af-0')][.//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'pr')]]/div/span")
            if not item["organiser_name"]:
                item["organiser_name"] = await get_text("//div[contains(@class, 'EventDetailsBase__Highlight-sc-d40475af-0')]/div/span")

            print(f"{bcolors.OKBLUE}OUTPUT: {item}{bcolors.ESCAPE}")
            container.upsert_item(item)
        except Exception as e:
            print(f"Error processing {url}: {e}")
        finally:
            await browser.close()

async def process_urls_concurrently(vm_offset, batch_size=100, max_workers=1, vm_name="local"):
    print(f"max_workers: {max_workers}")
    """Process URLs fetched from CosmosDB."""
    while True:
        t1_batch = time.perf_counter()
        # Fetch a batch of URLs for this VM
        records = fetch_urls_for_vm(vm_offset=vm_offset, batch_size=batch_size, vm_name=vm_name)
        if not records:
            print("No unprocessed URLs found. Exiting.")
            break
        t2_batch = time.perf_counter()
        semaphore = asyncio.Semaphore(max_workers)

        async def process_with_semaphore(record):
            async with semaphore:
                await process_page(record["url"], record["sheet_name"])

        # Create tasks with concurrency control
        tasks = [process_with_semaphore(record) for record in records]
        await asyncio.gather(*tasks)

        t3_batch = time.perf_counter()
        print(f"{bcolors.FAIL}Records Fetch: {round(t2_batch-t1_batch, 2)} sec.\nBatch Scrapping: {round(t3_batch-t2_batch, 2)} sec.\nBatch Total: {round(t3_batch-t1_batch, 2)} sec.{bcolors.ESCAPE}")

def fetch_urls_for_vm(vm_offset=0, batch_size=100, vm_name="local"):
    """Fetch a batch of unprocessed URLs and mark them as processing."""
    query = f"SELECT * FROM c WHERE c.processed = false AND (NOT IS_DEFINED(c.processing) OR c.processing = '{vm_name}') OFFSET {vm_offset} LIMIT {batch_size}"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    
    # Lock items for processing
    for item in items:
        item['processing'] = vm_name
        container.upsert_item(item)
    
    return [{"url": item["url"], "sheet_name": item["sheet_name"]} for item in items]

def get_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Scraper script")
    parser.add_argument("--vm_offset", type=int, default=1000, help="VM offset for processing URLs")
    parser.add_argument("--batch_size", type=int, default=100, help="Number of URLs to process per batch")
    parser.add_argument("--vm_name", type=str, default="local", help="Name of the VM used for processing flag")
    
    # Parse arguments and return them
    return parser.parse_args()

if __name__ == "__main__":
    t1 = time.perf_counter()

    args = get_args()
    # Determine the number of CPUs on the machine
    num_cpus = multiprocessing.cpu_count()
    print(f"Detected {num_cpus} CPUs on this machine.")

    try:
        asyncio.run(process_urls_concurrently(vm_offset=args.vm_offset, batch_size=args.batch_size, max_workers=num_cpus*2, vm_name=args.vm_name))
    except Exception as e:
        import traceback
        print(f"An error occurred: {traceback.format_exc()}")

    t2 = time.perf_counter()
    print(f"{bcolors.FAIL}Elapsed time: {t2 - t1} seconds{bcolors.ESCAPE}")