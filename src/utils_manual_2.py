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

async def process_idealist(page):
    data = {}
    data["phone"] = await get_text(page, "a[href^='tel:']")
    data["address"] = await get_text(page, "li:has(div[aria-label='location icon']) > div:nth-of-type(2)")
    city_state_text = await get_text(page, "div.sc-1pfcxqe-0.cWkWDU > div:first-of-type")
    data["city"] = city_state_text.split(",")[0].strip() if len(city_state_text.split(",")) > 0 else ""
    data["state"] = ",".join(city_state_text.split(",")[1:]).strip() if len(city_state_text.split(",")) > 1 else ""
    data["domain"] = await get_text(page, "header a[href^='http']")
    print(data)
    return data

async def get_text(page, selector):
    element = await page.query_selector(selector)
    return await element.inner_text() if element else ""


async def process_urls_concurrently(path):
    df = pd.read_excel(path)

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

        for index, row in df.iterrows():
            if not pd.notna(row["error"]):
                continue
            try:
                print(f"{bcolors.OKGREEN}Processing {index+1}/{len(df)}: {row['Link']}{bcolors.ESCAPE}")
                await page.goto(row["Link"], wait_until="domcontentloaded", timeout=30000)
                # await page.wait_for_load_state("domcontentloaded")
                # await page.wait_for_timeout(2000)  # wait for results to render

                data = await process_idealist(page)  # your scraper function for each page
                # append data dictionary to the row
                for key, value in data.items():
                    df.at[index, key] = value
                # await asyncio.sleep(random.uniform(2, 4))  # Random delay between requests
            except Exception as e:
                error_message = f"Failed to process {row.get('Link', 'N/A')}: {e}"
                print(f"{bcolors.FAIL}{error_message}{bcolors.ESCAPE}")
                if 'error' not in df.columns:
                    df['error'] = ''
                df.at[index, 'error'] = str(e)
                continue # Continue to the next row
        await context.close()
        await browser.close()

    df.to_excel(path.replace(".xlsx", "_updated.xlsx"), index=False)
            



if __name__=="__main__":
    async def run():
        await process_urls_concurrently("data/temp_e61880e699a2796a33ecdfde30f1ff7952fa984f33abbcc06af70c464c05935c_updated.xlsx")
    
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Script interrupted by user.")