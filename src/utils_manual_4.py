import re
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

async def process_greatnonprofits(page):
    details = {
        'ein': None,
        'email': None,
        'phone': None,
        'address': None,
        'website': None,
        'facebook': None,
        'twitter': None
    }
    
    # --- Extract EIN ---
    try:
        ein_li = await page.wait_for_selector("li:has(img[src*='vuesax_linear_message-text'])", timeout=100)
        details["ein"] = await ein_li.inner_text()
        # details['ein'] = await get_text(page, "li:has-text('EIN')", timeout=0)
    except:
        pass
    print("EIN:", details["ein"])
    
    try:
        address_li = await page.wait_for_selector("li:has(img[src*='vuesax_linear_location'])", timeout=100)
        details["address"] = await address_li.inner_text()
    except:
        pass
    print("Address:", details["address"])
    
    try:
        email_li = await page.wait_for_selector("li:has(img[src*='vuesax_linear_sms'])",  state="visible", timeout=100)
        li_elements = await page.query_selector_all("li:has(img[src*='vuesax_linear_sms'])")
        for li in li_elements:
            text = (await li.inner_text()).strip()
            # Apply simple email regex
            match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
            if match:
                details["email"] = match.group()
                break  # stop at first match
    except:
        pass
    print("Email:", details["email"])

    try:
        mobile_li = await page.wait_for_selector("li:has(img[src*='call-incoming-2'])", timeout=100)
        details["phone"] = await mobile_li.inner_text()
    except:
        pass
    print("Phone:", details["phone"])

    try:
        domain_li = await page.wait_for_selector("li:has(img[src*='vuesax_linear_global'])", timeout=100)
        details["website"] = await domain_li.inner_text()
    except:
        pass
    print("Website:", details["website"])

    try:
        facebook_li = await page.wait_for_selector("li:has(img[src*='Icon_awesome-facebook']) a", timeout=100)
        details["facebook"] = await facebook_li.get_attribute("href")
    except:
        pass
    print("Facebook:", details["facebook"])

    try:
        twitter_li = await page.wait_for_selector("li:has(img[src*='Path_43478']) a", timeout=100)
        details["twitter"] = await twitter_li.get_attribute("href")
    except:
        pass
    print("Twitter:", details["twitter"])

    return details

async def get_attr(page, selector: str, attr: str) -> str:
    el = await page.query_selector(selector)
    if el:
        value = await el.get_attribute(attr)
        return value.strip() if value else ""
    return ""

async def get_text(page, selector):
    element = await page.query_selector(selector)
    return await element.inner_text() if element else ""


async def process_urls_concurrently(path):
    df = pd.read_excel(path)
    df = df.drop_duplicates(subset=["link"]).reset_index(drop=True)

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
            # if not pd.notna(row["error"]):
            #     continue
            try:
                print(f"{bcolors.OKGREEN}Processing {index+1}/{len(df)}: {row['link']}{bcolors.ESCAPE}")
                await page.goto(row["link"], wait_until="networkidle", timeout=30000)
                # await page.wait_for_load_state("domcontentloaded")
                # await page.wait_for_timeout(2000)  # wait for results to render

                data = await process_greatnonprofits(page)  # your scraper function for each page
                # append data dictionary to the row
                for key, value in data.items():
                    df.at[index, key] = value
                # await asyncio.sleep(random.uniform(2, 4))  # Random delay between requests
            except Exception as e:
                error_message = f"Failed to process {row.get('link', 'N/A')}: {e}"
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
        await process_urls_concurrently("data/v2_e1cbd2adda2b7148a96dbfba238d61d251a95aba5f2e3f5380d3fca0e49be76d.xlsx")
    
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Script interrupted by user.")