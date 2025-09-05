from playwright.async_api import async_playwright


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
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15"

import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent=user_agent,locale="en-US",
    viewport={"width": 1440, "height": 900})

        # Load Cloudflare cookie
        await context.add_cookies(x)

        page = await context.new_page()
        await page.goto("https://ngobase.org/ci/US.WA.1/seattle-ngos-charities", wait_until="networkidle")

        print(await page.title())
        await browser.close()

import asyncio
asyncio.run(run())
