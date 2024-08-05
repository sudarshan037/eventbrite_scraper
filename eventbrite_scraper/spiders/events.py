import scrapy
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
        df = pd.read_excel("data/inputs/inputs.xlsx")
        urls = df["Event_link"].to_list()
        # urls = [
        #     "https://www.eventbrite.com/e/oregon-wedding-day-best-of-2024-awards-gala-tickets-881507160647?aff=ebdssbdestsearch",
        # ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
            )

    def parse(self, response):
        item = EventItem()
        item['event_link'] = response.url
        print(f"{bcolors.OKGREEN}{self.url_counter} URL: {item['event_link']}{bcolors.ESCAPE}")

        self.driver.get(response.url)
        wait = WebDriverWait(self.driver, 10)
        try:
            # press button 1
            button1_text = 'View event'
            button1 = self.driver.find_element(By.XPATH, f"//button[text()='{button1_text}']")
            button1.click()
            # press button 2
            button2_text = 'View all event details'
            button2 = self.driver.find_element(By.XPATH, f"//button[text()='{button2_text}']")
            button2.click()
        except:
            pass
        wait.until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'organizer-stats__highlight')]"))
                    )
        body = self.driver.page_source
        response = Selector(text=body)
        
        self.url_counter += 1
        
        item['event_name'] = response.xpath("//h1[contains(@class, 'event-title')]/text()").get()
        item['date'] = response.xpath("//time[contains(@class, 'start-date')]/text()").get()
        item['price'] = response.xpath("//div[contains(@class, 'conversation-bar-container')]/text()").get()
        # item['price'] = response.css('#root > div > div > div.eds-structure__body > div > div > div > div.eds-fixed-bottom-bar-layout__content > div > main > div.event-listing.event-listing--has-image > div.event-details.event-details--has-hero-section > div.event-details__wrapper > div.Layout-module__layout___1vM08 > div.Layout-module__module___2eUcs.Layout-module__aside___2Tdmd > div > div.conversion-bar-bordered > div.conversion-bar.conversion-bar--checkout-opener > div.conversion-bar__body > div::text').get()
        item['location'] = response.xpath("//div[contains(@class, 'location-info__address')]/text()").get()
        item['organiser_name'] = response.xpath("//strong[contains(@class, 'organizer-listing-info-variant-b__name-link')]/text()").get()
        item['followers'] = response.xpath("//span[contains(@class, 'organizer-stats__highlight')]/text()").get()
        print(item)
        yield item
