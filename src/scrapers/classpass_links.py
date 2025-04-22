from src import utils

async def process(record, page):
    """
    record: whatever is present in cosmos db for that record [mandatory "url"]
    page: playwright page object used for data extraction
    """
    record['events'] = []
    try:
        while True:
            ul_selector = 'ul[data-component="SearchResultsList"]'
            list_items = await page.query_selector_all(f'{ul_selector} > li')
            for item in list_items:
                try:
                    name_node = await item.query_selector('a[data-qa="VenueItem.name"]')
                    url = await name_node.get_attribute('href')
                    if url:
                        record['events'].append(f"https://www.classpass.com{url}" if url else None,)
                except Exception as e:
                    print(f"⚠️ Error processing an event: {e}")

            next_button = await page.query_selector('button[aria-label="Next page"]')
            if not next_button:
                print("exiting")
                break

            await next_button.scroll_into_view_if_needed()
            await next_button.wait_for_element_state("visible", timeout=3000)
            await next_button.wait_for_element_state("enabled", timeout=3000)

            banner_close_button = await page.query_selector('button[aria-label="hide promotion"]')
            if banner_close_button:
                try:
                    await banner_close_button.click()
                    print("✅ Banner closed")
                except Exception as e:
                    print(f"⚠️ Could not close banner: {e}")

            await next_button.click()
            await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"Error Fetching details for url -> {record['url']}: {e}")
    return record