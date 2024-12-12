import asyncio
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
    print(f"{bcolors.OKGREEN}OUTPUT: {item}{bcolors.ESCAPE}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Use headless for faster processing
        context = await browser.new_context()
        page = await context.new_page()

        # Apply stealth mode
        await stealth_async(page)

        # Navigate to the URL
        try:
            await page.goto(url, wait_until="domcontentloaded")
        except Exception as e:
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
            print(f"Items found on {url}")
        except Exception as e:
            print(f"Some items are not found for {url}: {e}")

        hash_key = sheet_name + url
        item = {}
        item["id"] = hashlib.sha256(hash_key.encode()).hexdigest()
        item["url"] = url
        item["processed"] = True
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

async def process_urls_concurrently(records, max_workers=4):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [
            loop.run_in_executor(
                executor,
                lambda record=record: asyncio.run(process_page(record["url"], record["sheet_name"]))
            )
            for record in records
        ]
        await asyncio.gather(*tasks)

def fetch_urls_for_vm(batch_size=100):
    """Fetch a batch of unprocessed URLs and mark them as processing."""
    query = f"SELECT * FROM c WHERE c.processed = false AND NOT IS_DEFINED(c.processing) OFFSET 0 LIMIT {batch_size}"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    
    # Lock items for processing
    for item in items:
        item['processing'] = True
        container.upsert_item(item)
    
    return [{"url": item["url"], "sheet_name": item["sheet_name"]} for item in items]

def fetch_unprocessed_urls(batch_size=100):
    query = f"SELECT * FROM c WHERE c.processed = false AND NOT IS_DEFINED(c.processing) OFFSET 0 LIMIT {batch_size}"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    
    # Lock items for processing
    for item in items:
        item['processing'] = True
        container.upsert_item(item)

    return [{"url": item["url"], "sheet_name": item["sheet_name"]} for item in items]


if __name__ == "__main__":
    t1 = time.perf_counter()

    records = fetch_unprocessed_urls(batch_size=50)
    if records:
        asyncio.run(process_urls_concurrently(records, max_workers=5))
    else:
        print("No unprocessed URLs found in CosmosDB.")

    t2 = time.perf_counter()
    print(f"{bcolors.FAIL}Elapsed time: {t2 - t1} seconds{bcolors.ESCAPE}")
