from src import utils

async def process(record, page):
    """
    record: dict from cosmos db (must contain 'url')
    page: playwright async page object used for data extraction
    """
    record['ngos'] = []
    try:
        # each NGO "row" has a logo and name, so use that as the parent selector
        rows = page.locator("div.row").filter(has=page.locator("h3.ngo_name"))
        row_count = await rows.count()

        for i in range(row_count):
            row = rows.nth(i)

            # NGO Name
            name_el = row.locator("h3.ngo_name a").first
            ngo_name = (await name_el.inner_text()).strip()

            # Website URL (may be missing)
            website_el = row.locator("a[title*='Nonprofit website']").first
            website_url = await website_el.get_attribute("href") if await website_el.count() > 0 else None

            # Facebook URL (may be missing)
            fb_el = row.locator("a[title*='facebook']").first
            fb_url = await fb_el.get_attribute("href") if await fb_el.count() > 0 else None

            ngo_record = {
                "name": ngo_name,
                "website": website_url,
                "facebook": fb_url
            }
            if ngo_record not in record['ngos']:
                record['ngos'].append(ngo_record)

        print(record['ngos'])

    except Exception as e:
        print(f"Error fetching NGO details for url -> {record['url']}: {e}")

    return record
