import os
import stat
import glob
import time
import platform
import random
import hashlib
import scrapy
from azure.cosmos.exceptions import CosmosHttpResponseError
from scrapy import signals
from scrapy.exceptions import DontCloseSpider
from scrapy.spiders import Spider

from eventbrite_scraper.items import DiceLink
from eventbrite_scraper.utils import bcolors
from scrapy_splash import SplashRequest
from scrapy.selector import Selector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from azure.cosmos import CosmosClient, PartitionKey

import logging
logging.getLogger('azure').setLevel(logging.CRITICAL)

class CosmosDBSpiderMixin(object):
    def __init__(self):
        self.offset_flag = True
        self.max_offset = 32
        print(f"max_offset = {self.max_offset}")

    """
    Mixin class to implement reading records from a Cosmos DB container.

    :type cosmos_db_container: str
    """
    cosmos_db_container = ""

    def process_cosmos_db_record(self, record):
        """"
        Tell this spider how to extract URLs from a Cosmos DB record.

        :param record: A Cosmos DB record (document)
        :type record: dict
        :rtype: str or None
        """
        if not record:
            return None
        return record.get('url')

    def setup_cosmos_db(self, settings):
        """Setup Cosmos DB connection and idle signal.

        This should be called after the spider has set its crawler object.

        :param settings: The current Scrapy settings being used
        :type settings: scrapy.settings.Settings
        """
        self.cosmos_db_uri = settings.get('COSMOS_DB_URI', 'your_cosmos_db_uri')
        self.cosmos_db_key = settings.get('COSMOS_DB_KEY', 'your_cosmos_db_key')
        self.cosmos_db_database = settings.get('COSMOS_DB_DATABASE', 'your_database')
        self.cosmos_db_container_name = "dice_events"

        self.client = CosmosClient(self.cosmos_db_uri, self.cosmos_db_key)
        self.database = self.client.get_database_client(self.cosmos_db_database)
        self.container = self.database.get_container_client(self.cosmos_db_container_name)

        self.crawler.signals.connect(self.spider_idle, signal=signals.spider_idle)
        self.crawler.signals.connect(self.item_scraped, signal=signals.item_scraped)
        print(f"Reading records from Cosmos DB container '{self.cosmos_db_container_name}'")

    def next_request(self):
        """
        Returns a request to be scheduled.

        :rtype: scrapy.Request or None
        """
        if not self.offset_flag:
            self.offset_flag = True
            self.max_offset = self.max_offset//2
            print(f"max_offset = {self.max_offset}")
        if self.max_offset == 0:
            random_offset = 0
        else:
            random_offset = random.randrange(0, self.max_offset)
        print(f"random offset: {random_offset}")
        query = f"SELECT * FROM c WHERE c.processed = false OFFSET {random_offset} LIMIT 1"
        try:
            records = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True))
        except CosmosHttpResponseError as e:
            print("Error fetching conversation:", e)
            records = None
        # records = [
        #     {"url": "https://dice.fm/partner/announcement-3-band-link/event/kr3ap-portals-festival-2023-27th-may-earth-london-tickets", "sheet_name": "dice"},
        #     {"url": "https://dice.fm/partner/stil-runnin/event/m8w7w-stil-runnin-w-redamancy-estin-the-86d-22nd-apr-the-coast-fort-collins-tickets", "sheet_name": "dice"}
        #     ]
        
        if not records:
            return None
        
        record = records[0]
        url = self.process_cosmos_db_record(record)
        
        if not url:
            return None
        
        output = SplashRequest(
            url, self.parse,
            args={'wait': 5},
            meta={
                'sheet_name': record.get("sheet_name", ""),
                'url': url
                },
            )
        return output

    def schedule_next_request(self):
        """Schedules a request if available"""
        req = self.next_request()
        if req:
            self.crawler.engine.crawl(req)

    def spider_idle(self):
        """Schedules a request if available, otherwise waits."""
        self.schedule_next_request()
        
        req = self.next_request()
        if not req:
            if self.max_offset <= 0:
                print("No records found, waiting for 120 seconds before trying again...")
                time.sleep(120)
                self.max_offset = 8
                self.offset_flag = True
                print(f"max_offset: {self.max_offset}")
            else:
                self.offset_flag = False
        else:
            self.crawler.engine.crawl(req)

        raise DontCloseSpider

    def item_scraped(self, *args, **kwargs):
        """Avoids waiting for the spider to idle before scheduling the next request"""
        self.schedule_next_request()

    def parse(self, response):
        print(f"{bcolors.OKGREEN}URL: {response.meta.get('url')}{bcolors.ESCAPE}")
        if response.meta.get('url') != response.url:
            print(f"{bcolors.FAIL}REDIRECTION: [{response.meta.get('url')}] -> [{response.url}]")

        if response.status == 400:
            print(f"{bcolors.FAIL}{response.status} Error 400: {response.url}{bcolors.ESCAPE}")
            return
        
        if response.status in [403, 404]:
            print(f"{bcolors.FAIL}{response.status} Error: {response.url}{bcolors.ESCAPE}")
            hash_key = response.meta.get('sheet_name') + response.meta.get('url')
            item = {
                "id": hashlib.sha256(hash_key.encode()).hexdigest(),
                "url": response.meta.get('url'),
                "processed": True,
                "sheet_name": response.meta.get('sheet_name'),

                "event_name": f"ERROR: {str(response.status)}",
                "date": "",
                "location": "",
                "organiser_name": "",
            }
            self.container.upsert_item(item)
            return
        
        elif response.status == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            retry_after += 10
            print(f"{bcolors.FAIL}Rate limited. Retrying after {retry_after} seconds.{bcolors.ESCAPE}")
            time.sleep(retry_after)
            return
        
        item = DiceLink()

        splash_response = Selector(response)

        hash_key = response.meta.get('sheet_name') + response.meta.get('url')
        item["id"] = hashlib.sha256(hash_key.encode()).hexdigest()
        item["url"] = response.meta.get('url')
        item["processed"] = True
        item["sheet_name"] = response.meta.get('sheet_name')

        item['event_name'] = splash_response.xpath("//h1[@class='EventDetailsTitle__Title-sc-8ebcf47a-0 iLdkPz']/text()").get()
        item['date'] = splash_response.xpath("//div[contains(@class, 'EventDetailsBase__Highlight-sc-d40475af-0')]/div/span/text()").get()
        item['location'] = splash_response.xpath("//div[@class='EventDetailsVenue__Address-sc-42637e02-5 cxsjwk']/span/text()").get()
        item['organiser_name'] = splash_response.xpath("//div[contains(@class, 'EventDetailsBase__Highlight-sc-d40475af-0')]/div/span/text()").get()
        
        print(f"{bcolors.OKBLUE}OUTPUT: {item}{bcolors.ESCAPE}")

        self.container.upsert_item(item)
        return item
        

class EventsSpider(CosmosDBSpiderMixin, Spider):
    name = "dice_events"

    """
    Spider that reads records from a Cosmos DB container when idle.

    This spider will exit only if stopped, otherwise it keeps
    listening to records in the given container.

    Specify the container to listen to by setting the spider's `cosmos_db_container`.

    Records are assumed to contain URLs. To do custom
    processing of Cosmos DB records, override the spider's `process_cosmos_db_record`
    method.
    """

    # Middleware and other settings specific to this spider
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_selenium.SeleniumMiddleware': 800,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        'SPLASH_URL': 'http://4.240.117.176:8050',
    }

    def __init__(self, *args, **kwargs):
        super(EventsSpider, self).__init__(*args, **kwargs)

    def _set_crawler(self, crawler):
        """
        :type crawler: scrapy.crawler.Crawler
        """
        super(EventsSpider, self)._set_crawler(crawler)
        self.setup_cosmos_db(crawler.settings)

    def closed(self, reason):
        pass