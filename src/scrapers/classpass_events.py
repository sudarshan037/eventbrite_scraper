from src import utils

async def process(record, page):
    """
    record: whatever is present in cosmos db for that record [mandatory "url"]
    page: playwright page object used for data extraction
    """
    try:
        record["title"] = await utils.get_text(page, "//h1[contains(@class, 'gamma')]")

        address_links = await page.query_selector_all("a[data-component='InventoryDetailFindUsRow']")
        for element in address_links:
            href = await element.get_attribute("href")
            text = (await element.inner_text()).strip()

            if href and "https://www.google.com/maps" in href:
                record["address"] = text
            elif href and href.startswith("tel:"):
                record["phone_number"] = text
            if href and href.startswith("https://") and not any(domain in href for domain in ["google.com/maps", "instagram", "facebook", "twitter"]):
                record["website"] = href

        social_links = await page.query_selector_all("#find-us-social-links a")
        for element in social_links:
            href = await element.get_attribute("href")
            if "instagram" in href:
                record["instagram_link"] = href
                record["instagram_handle"] = text.strip()
            elif "facebook" in href:
                record["facebook_link"] = href
                record["facebook_handle"] = text.strip()
            elif "x.com" in href or "twitter.com" in href:
                record["twitter_link"] = href
                record["twitter_handle"] = text.strip()
            elif "youtube" in href:
                record["youtube_link"] = href
                record["youtube_handle"] = text.strip()
    except Exception as e:
        print(f"Error Fetching details for url -> {record['url']}: {e}")
    return record