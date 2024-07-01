import scrapy
import time
import pandas as pd
from eventbrite_scraper.items import EventItem
from eventbrite_scraper.utils import bcolors
from scrapy.selector import Selector
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait

import logging
logger = logging.getLogger(__name__)

# Suppress logging from selenium and urllib3
logging.getLogger('selenium.webdriver.remote.remote_connection').setLevel(logging.WARNING)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
logging.getLogger('scrapy.utils.log').setLevel(logging.WARNING)
logging.getLogger('scrapy.middleware').setLevel(logging.WARNING)
logging.getLogger('scrapy.extensions.telnet').setLevel(logging.WARNING)
logging.getLogger('WDM').setLevel(logging.WARNING)

class EventsSpider(scrapy.Spider):
    name = "events"
    url_counter = 0

    def __init__(self, *args, **kwargs):
        super(EventsSpider, self).__init__(*args, **kwargs)
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Ensure GUI is off
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


    def start_requests(self):
        urls = [
            "https://www.instagram.com/desireenicolexxo",
            # "https://www.instagram.com/keychron",
            # "https://www.instagram.com/arushi082"
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
            )

    def parse(self, response):
        item = EventItem()
        item['link'] = response.url
        self.url_counter += 1
        print(f"{bcolors.OKGREEN}{self.url_counter} URL: {item['link']}{bcolors.ESCAPE}")

        self.driver.get(response.url)
        wait = WebDriverWait(self.driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'header section')))
        # wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'agx')] | //div[contains(@class, '_aagx')]")))
        
        body = self.driver.page_source
        response = Selector(text=body)
        # name, follower, following, is_professional, bio with links, media count, is_verified, 
        
        username_xpath = (
            "//h2[contains(@class, 'x1lliihq x1plvlek xryxfnj x1n2onr6 x193iq5w xeuugli x1fj9vlw x13faqbe x1vvkbs x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1i0vuye x1ms8i2q xo1l8bm x5n08af x10wh9bi x1wdrske x8viiok x18hxmgj')]/text()"
            " | "
            "//span[contains(@class, 'x1lliihq x193iq5w x6ikm8r x10wlt62 xlyipyv xuxw1ft')]/text()"
        )
        item['username'] = response.xpath(username_xpath).get()
        item['posts'] = response.css('header section ul li:nth-child(1) span span::text').get()
        item['followers'] = response.css('header section ul li:nth-child(2) span span::text').get()
        item['following'] = response.css('header section ul li:nth-child(3) span span::text').get()
        item['bio'] = response.css('header section div.-vDIg span').get()
        item['professional'] = response.xpath("//div[contains(@class, '_ap3a _aaco _aacu _aacy _aad6 _aade')]/text()").get()
        item['verified'] = response.xpath("//svg[@aria-label='Verified']").get() is not None
        yield item