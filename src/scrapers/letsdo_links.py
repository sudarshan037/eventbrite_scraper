from src import utils
from src import bulk_upload

from src import sqlite_handler 

async def run(record, urls):
    """
    Handle SQLite insertion for the extracted URLs asynchronously.
    """
    conn = await sqlite_handler.initialize_sqlite()
    try:
        await sqlite_handler.insert_into_sqlite(conn, record["url"], urls, record.get("sheet_name", ""))
    except Exception as e:
        print(f"Error inserting into SQLite: {e}")
    finally:
        await conn.close()

# async def run(record, urls):
#     # connect with Scraper.db
#     # create table if it does not exists -> schema -> events cosmos (id, source_url, url, sheet_name)
#     # insert into sqlite
#     print(urls, record)
#     await bulk_upload.azure_cosmos.initialize_cosmosdb("Scraper", "letsdo_events")
#     await bulk_upload.upload_urls(urls, record.get("sheet_name", ""), "letsdo_events")
#     await bulk_upload.azure_cosmos.client.close()

async def process(record, page):
    """
    record: whatever is present in cosmos db for that record [mandatory "url"]
    page: playwright page object used for data extraction
    """
    urls = []
    try:
        links = await page.query_selector_all("main a[href]")
        for link in links:
            href = await link.get_attribute("href")
            urls.append(href)
        if urls:
            await run(record, urls)
    except Exception as e:
        print(f"Error Fetching details for url -> {record['url']}: {e}")
    record["urls_count"] = len(urls)
    return record