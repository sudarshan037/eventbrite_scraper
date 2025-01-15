from src import utils
from src import bulk_upload


async def run(record, urls):
    print(urls, record)
    await bulk_upload.azure_cosmos.initialize_cosmosdb("Scraper", "letsdo_events")
    await bulk_upload.upload_urls(urls, record.get("sheet_name", ""), "letsdo_events")
    await bulk_upload.azure_cosmos.client.close()

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
    except Exception as e:
        print(f"Error Fetching details for url -> {record['url']}: {e}")
    if urls:
        await run(record, urls)
        record["urls_count"] = len(urls)
    return record