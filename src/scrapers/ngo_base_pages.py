from src import utils

async def process(record, page):
    """
    record: dict from cosmos db (must contain 'url')
    page: playwright async page object used for data extraction
    """
    record['pages'] = []
    try:
        # if page number is 1, add all pages to links, else skip this step
        if record['url'].split('=')[-1]=="1" and record["processed"] is False:
            pagination_selector = "ul.pagination li.page-item a.page-link"
        
            # Await async Playwright call
            page_numbers = await page.eval_on_selector_all(
                pagination_selector,
                "elements => elements.map(e => e.textContent.trim())"
            )

            # Filter numeric values only
            numeric_pages = [int(num) for num in page_numbers if num.isdigit()]

            if numeric_pages:
                for page_num in range(1, max(numeric_pages)+1):
                    record['pages'].append(f"{record['url'].split('?')[0]}?page={page_num}")

    except Exception as e:
        print(f"Error fetching NGO details for url -> {record['url']}: {e}")

    return record
