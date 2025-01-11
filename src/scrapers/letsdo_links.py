from src import utils

async def process(record, page):
    """
    record: whatever is present in cosmos db for that record [mandatory "url"]
    page: playwright page object used for data extraction
    """
    try:
        record['event_name'] = await utils.get_text(page,"/html/body/div[2]/div[1]/div[2]/main/div/div[2]/div[1]/div[1]/h1",is_xpath=True)
    except Exception as e:
        print(f"Error Fetching details for url -> {record['url']}: {e}")
    return record