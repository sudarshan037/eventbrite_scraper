import asyncio
from concurrent.futures import ThreadPoolExecutor
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import time
import random
import hashlib
import pandas as pd
from azure.cosmos import CosmosClient
from eventbrite_scraper.utils import bcolors

records = [    {
            "url": "https://dice.fm/partner/-la-folie/event/229qp-future-is-steffi-rachel-noon-rag-pepiita-10th-apr-la-folie-paris-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/23-meadow-llc-dba-the-monarch-new-york/event/rxgby-hulderspitemorbid-romance-3rd-dec-the-kingsland-new-york-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/3615/event/9gww9",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/agenda-web/event/3a2ml-lescop-15th-mar-rock-school-barbey-bordeaux-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/agenda-web/event/a39v2-nick-waterhouse-21st-nov-rock-school-barbey-bordeaux-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/all-nighters/event/2d32p-los-fresones-rebeldes-1st-apr-el-sol-madrid-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/antidote-booking/event/lv8pw",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/association-orizon-sud/event/r5v3q-treize-carats-2nd-apr-le-makeda-marseille-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/cha-chdiversica-media-sl/event/3ew38-la-discoteca-1st-jul-sala-coco-madrid-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/cult-of-ya---eur/event/o8xnm-haon-berlin-8th-apr-columbia-theater-berlin-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/dem-lancio-primi-artisti/event/wyvbn-spring-attitude-festival-abbonamento-2022-16th-sep-studi-di-cinecitt-roma-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/dice/event/2wro7o-black-lotus-halloween-night-2-31st-oct-secret-location-m",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/dice/event/2xxm6-chaos-theory-festival-2023-day-3-4th-mar-signature-brew-blackhorse-road-london-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/dice/event/3db6x-a-place-to-bury-strangers-teatro-perla-25th-mar-cinema-perla-bologna-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/dice/event/3e9q8-a-dark-summer-garden-party-30th-jul-once-at-boynton-yards-somerville-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/dice/event/57mxy-the-warm-up-block-party-ft-desert-hearts-takeover-18th-jun-marrs-building-sacramento-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/dice/event/5addl-walking-memories-29th-oct-artificerie-almagi-ravenna-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/dice/event/5qndy-slow-dance-presents-yaang-31st-mar-dream-bags-jaguar-shoes-london-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/mailchimp/event/dx3oe-this-railyards-ft-chris-lake-vnssa-17th-sep-the-railyards-sacramento-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        },
        {
            "url": "https://dice.fm/partner/la-boule-noire/event/qbopa-ckraft-14th-nov-la-boule-noire-paris-tickets",
            "sheet_name": "DICE Partner Links - Sheet3"
        }
    ]

async def process_page(url, sheet_name):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Use headless for faster processing
        context = await browser.new_context()
        page = await context.new_page()

        # Apply stealth mode
        await stealth_async(page)

        # Navigate to the URL
        await page.goto(url, wait_until="domcontentloaded")

        try:
            # Wait for selectors
            await page.wait_for_selector("//h1[@class='EventDetailsTitle__Title-sc-8ebcf47a-0 iLdkPz']", timeout=5000)
            await page.wait_for_selector("//div[contains(@class, 'EventDetailsTitle__Date-sc-8ebcf47a-2')]", timeout=5000)
            print(f"Items found on {url}")
        except Exception as e:
            print(f"Some items are not found for {url}: {e}")

        # Screenshot
        hash_key = sheet_name + url
        await page.screenshot(path=f"screenshot_{hashlib.sha256(hash_key.encode()).hexdigest()}.png")

        # Close the browser
        await browser.close()

        # Log result
        item = {
            "id": hashlib.sha256(hash_key.encode()).hexdigest(),
            "url": url,
            "processed": True,
            "sheet_name": sheet_name,
        }
        print(f"Processed: {item}")

async def process_urls_concurrently(records, max_workers=4):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [
            loop.run_in_executor(
                executor,
                lambda record=record: asyncio.run(process_page(record["url"], record["sheet_name"]))
            )
            for record in records
        ]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    t1 = time.perf_counter()
    asyncio.run(process_urls_concurrently(records[:4], max_workers=2))
    t2 = time.perf_counter()
    print(f"Elapsed time: {t2 - t1} seconds")

