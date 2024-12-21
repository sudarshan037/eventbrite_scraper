from src import utils

async def process(record, page):
    """
    record: whatever is present in cosmos db for that record [mandatory "url"]
    page: playwright page object used for data extraction
    """
    try:
        record['event_name'] = await utils.get_text(page, "//h1[contains(@class, 'event-title')]")
        record['date'] = await utils.get_text(page, "//time[contains(@class, 'start-date')]")
        record['price'] = await utils.get_text(page, "//div[@class='conversion-bar__panel-info']")
        record['location'] = await utils.get_text(page, "//div[contains(@class, 'location-info__address')]")
        record['organiser_name'] = await utils.get_text(page, "//strong[contains(@class, 'organizer-listing-info-variant-b__name-link')]")
        record['followers'] = await utils.get_text(page, "//span[contains(@class, 'organizer-stats__highlight')]//strong")
    except Exception as e:
        print("Error Fetching details for url -> {url}: {e}")
    return record