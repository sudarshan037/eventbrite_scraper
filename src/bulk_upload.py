import os
import time
import hashlib
import pandas as pd
from tqdm import tqdm
import asyncio
from src.database.azure_cosmos_v2 import *
from azure.cosmos.exceptions import CosmosResourceExistsError, CosmosHttpResponseError

async def process_url(azure_cosmos, url, source_url, database_name, container_name, sheet_name, semaphore):
    async with semaphore:
        secure_url = url.replace("http://", "https://")
        hash_key = sheet_name + secure_url
        data = {
            "id": hashlib.sha256(hash_key.encode()).hexdigest(),
            "url": secure_url,
            "processed": False,
            "sheet_name": sheet_name,
            "source_url": source_url
        }

        retries = 0
        max_retries = 3

        while retries < max_retries:
            try:
                await azure_cosmos.create_item(database_name=database_name, container_name=container_name, item=data)
                return True
            except CosmosResourceExistsError:
                print(f"[INFO] Record already exists in {container_name}, skipping insertion.")
                return True
            except CosmosHttpResponseError as e:
                if e.status_code == 429:
                    retry_after = int(e.headers.get("x-ms-retry-after-ms", 1000)) / 1000
                    print(f"[WARNING] Rate limit exceeded. Retrying in {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                    retries += 1
                else:
                    print(f"[ERROR] {e}")
                    return False
        return False

async def upload_urls(azure_cosmos, urls, source_url, database_name, container_name, sheet_name, max_concurrent_tasks=10):
    semaphore = asyncio.Semaphore(max_concurrent_tasks)
    tasks = [
        process_url(azure_cosmos, url, source_url, database_name, container_name, sheet_name, semaphore)
        for url in urls
    ]
    results = await asyncio.gather(*tasks)
    success_count = sum(results)
    print(f"Out of {len(urls)} URLs, {success_count} were uploaded successfully.")
    return success_count


async def intermediate_upload(azure_cosmos, urls, source_url, database_name, SCRAPER_NAME, SHEET_NAME):
    await upload_urls(azure_cosmos, urls, source_url, database_name, SCRAPER_NAME, SHEET_NAME)

async def run():
    azure_cosmos = AzureCosmos()
    database_name = "Scraper"

    containers = await azure_cosmos.list_containers(database_name)
    print(f"Existing containers: {containers}")

    SCRAPER_NAME = input("Enter container name: ") # container_name
    INPUT_FILE_PATH = input("Enter input file path: ")

    if not os.path.exists(INPUT_FILE_PATH):
        print("[ERROR] Input file does not exist.")
        return

    SHEET_NAME, extension = os.path.splitext(os.path.basename(INPUT_FILE_PATH))
    source_url = ""
    df = pd.read_csv(INPUT_FILE_PATH)

    if "Links" not in df.columns:
        print("[ERROR] Input file does not contain a 'Links' column.")
        return

    df.drop_duplicates(inplace=True)
    urls = df["Links"].to_list()

    print(f"Starting upload of {len(urls)} URLs to container '{SCRAPER_NAME}'...")
    await upload_urls(azure_cosmos, urls, source_url, database_name, SCRAPER_NAME, SHEET_NAME)

    await azure_cosmos.client.close()

if __name__ == "__main__":
    asyncio.run(run())