import time
import asyncio
import hashlib
import random
import pandas as pd
from playwright.async_api import async_playwright

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ESCAPE = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15"
x = [
  {
    "name": "cf_clearance",
    "value": "R10QA9neEKPt6ic8YJy4r7SxxytRjKR.6hG4k4rSkaE-1756999914-1.2.1.1-jgSc3.rvCIXon.VyX1ziBR9b14S9rbFod7IvUZnePCfKv.8kbvvc1i85PyfURjxV9FFP8tlewDLyUp9PAwFMQIkGmykL_Py.m.duLZFO5IAeMjC_M8zT6clE9CYRnmcVm8nLQn4ha72XYIJok1IF7OiPqjiFfhr8tzOUKsRhD81wqfgTiLYPwF5sGjml.ETeI6SvuPzvcjNGoWbXgtDgSX3.JDT3nFeTj9yiOXhN00s",
    "domain": "ngobase.org",
    "path": "/",
    "httpOnly": True,
    "secure": True
  }
]

async def process_idealist(page, filename):
    # Each org card in the results
    org_cards = await page.query_selector_all('[data-qa-id="search-result"]')
    data = []

    for card in org_cards:
        # --- Get link element ---
        link_el = await card.query_selector("a.sc-9gxixl-5")  # the <a> tag itself
        link = await link_el.get_attribute("href") if link_el else ""
        if link and not link.startswith("http"):
            link = f"https://www.idealist.org{link}"

        # --- Org name ---
        name = ""
        if link_el:
            name_span = await link_el.query_selector('[data-qa-id="search-result-link"]')
            if name_span:
                name = (await name_span.inner_text()) or ""

        # --- Tags ---
        tags = []
        tag_els = await card.query_selector_all(".sc-1eme1mj-2")
        for t in tag_els:
            tag_text = await t.inner_text()
            if tag_text:
                tags.append(tag_text.strip())

        # --- Posted date ---
        posted = await get_text(card, ".sc-1oq5f4p-0") or ""

        # --- Logo ---
        logo_el = await card.query_selector("img[data-qa-id='logo-uploaded-image']")
        logo = await logo_el.get_attribute("src") if logo_el else ""

        data.append({
            "Name": name.strip(),
            "Link": (link or "").strip(),
            "Tags": ", ".join(tags),
            "Posted": posted.strip(),
            "Logo": (logo or "").strip()
        })

    # Save / append to Excel
    df = pd.DataFrame(data)
    try:
        existing = pd.read_excel(filename)
        df = pd.concat([existing, df], ignore_index=True)
    except FileNotFoundError:
        pass

    df.to_excel(filename, index=False)
    print(f"{bcolors.OKGREEN}Saved {len(data)} records to {filename}{bcolors.ESCAPE}")




async def get_text(page, selector):
    element = await page.query_selector(selector)
    return await element.inner_text() if element else ""


async def process_urls_concurrently(url):
    filename = f"data/temp_{hashlib.sha256(url.encode()).hexdigest()}.xlsx"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=[
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-renderer-backgrounding",
                "--disable-background-timer-throttling",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
            headless=False,
        )
        context = await browser.new_context(user_agent=user_agent,locale="en-US",
            viewport={"width": 1440, "height": 900})
        await context.add_cookies(x)
        page = await context.new_page()

        async def block_unwanted(route):
            await route.abort()

        await page.route("**/*.{png,jpeg,webp,gif,svg}", block_unwanted)  # Block images
        await page.route("**/*.jpg?*", block_unwanted)  # Block images

        await page.goto(url, wait_until="networkidle", timeout=30000)

        while True:
            await process_idealist(page, filename)  # your scraper function for each page

            # Try to find the "Next page" link
            next_link = await page.query_selector('a[data-qa-id="pagination-link-next"]')
            if not next_link:
                print("Reached last page, no next link.")
                break

            # Extract next page number (optional, just for logging)
            next_href = await next_link.get_attribute("href")
            if next_href and "page=" in next_href:
                page_number = next_href.split("page=")[-1]
                print(f"{bcolors.OKBLUE}Navigating to page {page_number}{bcolors.ESCAPE}")
            
            # Click next
            await next_link.click()
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(2000)  # wait for results to render



if __name__=="__main__":
    url = "https://www.idealist.org/en/organizations?page=1"

    async def run():
        await process_urls_concurrently(url)
    
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Script interrupted by user.")