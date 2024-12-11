import time
import random
import hashlib
import pandas as pd
from azure.cosmos import CosmosClient
from eventbrite_scraper.utils import bcolors
from azure.cosmos.exceptions import CosmosHttpResponseError
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

COSMOS_DB_URI = "https://cosmos-scraper.documents.azure.com:443/"
COSMOS_DB_KEY = "bBgVEeSnEQaSss88e8zZU5pjpiVzPjba5qpe6alFqU548KcW2eMkCeUf7J99RWVUPw6ASV32W8pGACDb5ZhxrA=="
COSMOS_DB_DATABASE = "Scraper"
COSMOS_DB_CONTAINER = "dice_events"

client = CosmosClient(COSMOS_DB_URI, COSMOS_DB_KEY)
database = client.get_database_client(COSMOS_DB_DATABASE)
container = database.get_container_client(COSMOS_DB_CONTAINER)

offset_flag = True
max_offset = 32

t1 = time.perf_counter()
count = 0
total_count = 0

while True:
    if count and count%10==0:
        t2 = time.perf_counter()
        print(f"{bcolors.WARNING}TOTAL: {total_count} |---| {count} records processed in {int(t2-t1)}sec. @ {int((t2-t1)/count)} sec/rec.{bcolors.ESCAPE}")
        t1 = time.perf_counter()
        count = 0
    if not offset_flag:
        offset_flag = True
        max_offset = max_offset//2
        print(f"max_offset = {max_offset}")
    if max_offset == 0:
        random_offset = 0
    else:
        random_offset = random.randrange(0, max_offset)
    print(f"random offset: {random_offset}")

    query = f"SELECT * FROM c WHERE c.processed = false OFFSET {random_offset} LIMIT 1"

    try:
        records = list(container.query_items(
            query=query,
            enable_cross_partition_query=True))
    except CosmosHttpResponseError as e:
        print("Error fetching conversation:", e)
        records = None

    # records = [{
    #     "url": "https://dice.fm/event/avngaq-rebel-rebel-pres-adiel-14th-dec-cieloterra-roma-tickets",
    #     "sheet_name": "DICE Partner Links - Sheet3"
    # }
    # ]

    if records:
        record = records[0]
    else:
        break
    url, sheet_name = record["url"], record["sheet_name"]

    print(url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        stealth_sync(page)  # Apply stealth mode

        try:
            page.goto(url, wait_until="domcontentloaded")
        except:
            hash_key = sheet_name + url
            item = {
                "id": hashlib.sha256(hash_key.encode()).hexdigest(),
                "url": url,
                "processed": True,
                "sheet_name": sheet_name,
                "event_name": "REDIRECTION ERROR"
            }
            container.upsert_item(item)
            continue
        # page.screenshot(path="screenshot_1.png")
        try:
            page.wait_for_selector("//h1[@class='EventDetailsTitle__Title-sc-8ebcf47a-0 iLdkPz']", timeout=5000)
            page.wait_for_selector("//div[contains(@class, 'EventDetailsTitle__Date-sc-8ebcf47a-2')]", timeout=5000)
        except:
            print("Some items are not found")

        hash_key = sheet_name + url
        item = {}
        item["id"] = hashlib.sha256(hash_key.encode()).hexdigest()
        # page.screenshot(path=f"screenshot_{item['id']}.png")
        item["url"] = url
        item["processed"] = True
        item["sheet_name"] = sheet_name

        item['event_name'] = page.query_selector("//h1[@class='EventDetailsTitle__Title-sc-8ebcf47a-0 iLdkPz']")
        item['event_name'] = item['event_name'].inner_text() if item['event_name'] else ""

        item['date'] = page.query_selector("//div[contains(@class, 'EventDetailsTitle__Date-sc-8ebcf47a-2')]")
        item['date'] = item['date'].inner_text() if item['date'] else ""

        item['location'] = page.query_selector("//div[@class='EventDetailsVenue__Address-sc-42637e02-5 cxsjwk']/span")
        item['location'] = item['location'].inner_text() if item['location'] else ""

        organiser_name_element = page.query_selector("//div[contains(@class, 'EventDetailsBase__Highlight-sc-d40475af-0')][.//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'pr')]]/div/span")
        if organiser_name_element and organiser_name_element.inner_text().strip():
            item['organiser_name'] = organiser_name_element.inner_text().strip()
        else:
            organiser_name_element = page.query_selector("(//div[contains(@class, 'EventDetailsBase__Highlight-sc-d40475af-0')]/div/span)[2]")
            if organiser_name_element and organiser_name_element.inner_text().strip():
                item['organiser_name'] = organiser_name_element.inner_text().strip()
            else:
                item['organiser_name'] = ""

        print(f"{bcolors.OKBLUE}OUTPUT: {item}{bcolors.ESCAPE}")
        container.upsert_item(item)

        count += 1
        total_count += 1