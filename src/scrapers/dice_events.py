import utils

async def process(record, page):
    """
    record: whatever is present in cosmos db for that record [mandatory "url"]
    page: playwright page object used for data extraction
    """
    try:
        record["event_name"] = await utils.get_text(page, "//h1[@class='EventDetailsTitle__Title-sc-8ebcf47a-0 iLdkPz']")
        record["date"] = await utils.get_text(page, "//div[contains(@class, 'EventDetailsTitle__Date-sc-8ebcf47a-2')]")
        record["location"] = await utils.get_text(page, "//div[@class='EventDetailsVenue__Address-sc-42637e02-5 cxsjwk']/span")
        record["organiser_name"] = await utils.get_text(page, "//div[contains(@class, 'EventDetailsBase__Highlight-sc-d40475af-0')][.//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'pr')]]/div/span")
        if not record["organiser_name"]:
            record["organiser_name"] = await utils.get_text(page, "//div[contains(@class, 'EventDetailsBase__Highlight-sc-d40475af-0')]/div/span")
    except Exception as e:
        print("Error Fetching details for url -> {url}: {e}")
    return record