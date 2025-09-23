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

PAGE_NUM = 1

async def process_idealist(page, filename):
    global PAGE_NUM
    PAGE_NUM += 1
    # Each org card in the results
    org_cards = await page.query_selector_all('div.search-fav-box')
    data = []

    for card in org_cards:
        # --- Get link element ---
        link_el = await card.query_selector("a[href]")  # the <a> tag itself
        link = await link_el.get_attribute("href") if link_el else ""
        if link and not link.startswith("http"):
            link = f"https://greatnonprofits.org{link}"

        # --- Org name ---
        name = ""
        if link_el:
            name_el = await card.query_selector("h2")
            if name_el:
                name = (await name_el.inner_text()) or ""
        data.append({
            "name": name.strip(),
            "link": link.strip(),
        })
        print(data[-1])

    # Save / append to Excel
    df = pd.DataFrame(data)
    try:
        existing = pd.read_excel(filename)
        df = pd.concat([existing, df], ignore_index=True)
    except FileNotFoundError:
        pass

    df.to_excel(filename, index=False)
    print(f"{bcolors.OKGREEN}Page: {PAGE_NUM} | Saved {len(data)} records to {filename}{bcolors.ESCAPE}")

async def get_text(page, selector):
    element = await page.query_selector(selector)
    return await element.inner_text() if element else ""


async def process_urls_concurrently(url):
    filename = f"data/v2_{hashlib.sha256(url.encode()).hexdigest()}.xlsx"

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
            try:
                await process_idealist(page, filename)  # your scraper function for each page

                # Try to find the "Next page" link
                # try 3 times with delays
                next_link = None
                for attempt in range(3):
                    next_link = await page.query_selector('li.next-view.page-item a.page-link')
                    if next_link:
                        break
                    await asyncio.sleep(2)  # wait before retrying

                # Click next
                await next_link.click()
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_timeout(2000)  # wait for results to render
                # TODO: last page exit not working
            except Exception as e:
                print(f"{bcolors.FAIL}No more pages or error occurred: {e}{bcolors.ESCAPE}")
                break


if __name__=="__main__":
    url = "https://greatnonprofits.org/city/minneapolis/MN"

    async def run():
        await process_urls_concurrently(url)
    
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Script interrupted by user.")