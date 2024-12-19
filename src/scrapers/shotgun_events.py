import utils

async def process(record, page):
    """
    record: whatever is present in cosmos db for that record [mandatory "url"]
    page: playwright page object used for data extraction
    """
    try:
        pass
    except Exception as e:
        print("Error Fetching details for url -> {url}: {e}")
    return record