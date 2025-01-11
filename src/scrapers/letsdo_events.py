from src import utils

async def process(record, page):
    """
    record: whatever is present in cosmos db for that record [mandatory "url"]
    page: playwright page object used for data extraction
    """
    try:
        record['event_name'] = await utils.get_text(page, '//h1')
        record['event_date'] = await utils.get_text(page,'//div[contains(text(), "View logistics")]/preceding-sibling::h6[contains(text(), ",")]')
        record['location'] = await utils.get_text(page,'//div[contains(text(), "Where and when")]/following-sibling::div//div[contains(text(), "Location")]/following-sibling::div')
        record['organizer_name'] = await utils.get_text(page,'//div[contains(@id, "organiser") or contains(@class, "organiser")]//div/text()')

    except Exception as e:
        print(f"Error Fetching details for url -> {record['url']}: {e}")
    return record