import time
import csv
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

def scrape_url(url):
    print(url)
    """Scrape data from a single URL."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            stealth_sync(page)  # Apply stealth mode

            page.goto(url, wait_until="domcontentloaded")
            page.screenshot(path="screenshot_1.png")
            page.wait_for_selector("//h1[@class='EventDetailsTitle__Title-sc-8ebcf47a-0 iLdkPz']", timeout=5000)
            page.wait_for_selector("//div[contains(@class, 'EventDetailsTitle__Date-sc-8ebcf47a-2')]", timeout=5000)

            # Extract event details
            event_name = page.query_selector("//h1[@class='EventDetailsTitle__Title-sc-8ebcf47a-0 iLdkPz']").inner_text()
            date = page.query_selector("//div[contains(@class, 'EventDetailsTitle__Date-sc-8ebcf47a-2')]").inner_text()
            location = page.query_selector("//div[@class='EventDetailsVenue__Address-sc-42637e02-5 cxsjwk']/span").inner_text()
            organiser_name = page.query_selector("(//div[contains(@class, 'EventDetailsBase__Highlight-sc-d40475af-0')]/div/span)[2]").inner_text()

            print({"url": url, "event_name": event_name, "date": date, "location": location, "organiser_name": organiser_name})

            browser.close()
            return {"url": url, "event_name": event_name, "date": date, "location": location, "organiser_name": organiser_name}
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {"url": url, "error": str(e)}

if __name__ == "__main__":
    # Example URL list (replace with your 1 million URLs)

    input_file = "data/inputs/DICE Partner Links - Sheet3.csv"
    df = pd.read_csv(input_file)
    urls = df.sample(1)["Links"].to_list()
    scrape_url(urls[0])
