import scrapy
import pandas as pd
from eventbrite_scraper.items import EventLink
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
    name = "links"
    url_counter = 0

    def __init__(self, *args, **kwargs):
        super(EventsSpider, self).__init__(*args, **kwargs)
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Ensure GUI is off
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


    def start_requests(self):
        urls = [
            "https://www.eventbrite.com/d/united-states/paid--festivals/student-welcome-week/?page=1",
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
            )

    def parse(self, response):
        item = EventLink()
        item['links'] = response.url
        print(f"{bcolors.OKGREEN}{self.url_counter} URL: {item['links']}{bcolors.ESCAPE}")

        self.driver.get(response.url)
        wait = WebDriverWait(self.driver, 10)
        try:
            # Example of clicking a button if needed
            # button1_text = 'event-card-link'
            # button1 = self.driver.find_element(By.XPATH, f"//button[text()='{button1_text}']")
            # button1.click()
            pass
        except Exception as e:
            logger.warning(f"Button not found or not clickable: {e}")

        body = self.driver.page_source
        response = Selector(text=body)
        
        self.url_counter += 1
        
        # Extract all hrefs from a tags with class 'event-card-link'
        links = response.xpath("//a[contains(@class, 'event-card-link')]/@href").getall()
        item['links'] = links

        print(item)
        yield item

    def closed(self, reason):
        self.driver.quit()