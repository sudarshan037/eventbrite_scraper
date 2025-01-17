from src import utils
from src import bulk_upload
from src import sqlite_handler 

async def run(record, urls):
    """
    Handle SQLite insertion for the extracted URLs asynchronously.
    """
    conn = await sqlite_handler.initialize_sqlite()
    try:
        await sqlite_handler.insert_into_sqlite(conn, record["url"], urls, record.get("sheet_name", "abc"))
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
    url = None
    try:
        # Get all the anchor elements with href in the main tag
        links = await page.query_selector_all("main a[href]")
        
        if links:  # Ensure there are links available
            # Try to get the second link, fallback to the first if only one exists
            target_link = links[1] if len(links) > 1 else links[0]
            href = await target_link.get_attribute("href")  # Extract href
            
            if href:  # Ensure href exists
                url = f"https://www.letsdothis.com{href}"  # Prepend the prefix
        
        # Run with the single URL if extracted
        if url:
            await run(record, [url])
    except Exception as e:
        print(f"Error Fetching details for url -> {record['url']}: {e}")
    
    # Add the single URL and its presence as a count to the record
    record["url"] = url
    record["urls_count"] = 1 if url else 0
    return record

