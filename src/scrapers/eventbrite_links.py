from src import utils

async def process(record, page):
    """
    record: whatever is present in cosmos db for that record [mandatory "url"]
    page: playwright page object used for data extraction
    """
    record['events'] = []
    try:
        record['events'] = await page.eval_on_selector_all("a.event-card-link", "elements => elements.map(el => el.href)")
    except Exception as e:
        print(f"Error Fetching details for url -> {record['url']}: {e}")
    return record