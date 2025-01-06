from src import utils

async def process(record, page):
    """
    record: whatever is present in cosmos db for that record [mandatory "url"]
    page: playwright page object used for data extraction
    """
    try:
        record['event_name'] = await utils.get_text(page, "//h1[contains(@class, 'font-title')]")
        record['date'] = await utils.get_text(page, "//a[contains(@href, 'venues')]")
        record['date'] = await utils.get_text(page, "//svg[contains(@d, 'text-muted-foreground mt-2 max-w-96')]//text()")
        record['location'] = await utils.get_text(page, 'div.text-muted-foreground > div:nth-child(2) > a')
        record['organiser_name'] = await utils.get_text(page, "//strong[contains(@class, 'organizer-listing-info-variant-b__name-link')]")
        record['followers'] = await utils.get_text(page, "//span[contains(@class, 'organizer-stats__highlight')]//strong")
    except Exception as e:
        print(f"Error Fetching details for url -> {record['url']}: {e}")
    return record