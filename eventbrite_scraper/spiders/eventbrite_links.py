import time
import hashlib
import scrapy
from azure.cosmos.exceptions import CosmosHttpResponseError
from scrapy import signals
from scrapy.exceptions import DontCloseSpider
from scrapy.spiders import Spider

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

from azure.cosmos import CosmosClient, PartitionKey

import logging
logging.getLogger('azure').setLevel(logging.CRITICAL)

class CosmosDBSpiderMixin(object):

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
        self.cosmos_db_container_name = "eventbrite_links"

        self.client = CosmosClient(self.cosmos_db_uri, self.cosmos_db_key)
        self.database = self.client.get_database_client(self.cosmos_db_database)
        self.container = self.database.get_container_client(self.cosmos_db_container_name)
        self.events_container = self.database.get_container_client("eventbrite_events")

        self.crawler.signals.connect(self.spider_idle, signal=signals.spider_idle)
        self.crawler.signals.connect(self.item_scraped, signal=signals.item_scraped)
        print(f"Reading records from Cosmos DB container '{self.cosmos_db_container_name}'")

    def next_request(self):
        """
        Returns a request to be scheduled.

        :rtype: scrapy.Request or None
        """
        query = "SELECT * FROM c WHERE c.processed = false OFFSET 0 LIMIT 1"
        try:
            records = list(self.container.query_items(query=query, enable_cross_partition_query=True))
        except CosmosHttpResponseError as e:
            print("Error fetching conversation:", e)
            records = None
        
        if not records:
            return None
        
        record = records[0]
        url = self.process_cosmos_db_record(record)
        
        if not url:
            return None
        
        output =  scrapy.Request(
                    url=url,
                    callback=self.parse,
                    meta={
                        'sheet_name': record.get("sheet_name", ""),
                        "url": url
                        }
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
            print("No records found, waiting for 120 seconds before trying again...")
            time.sleep(120)
        else:
            self.crawler.engine.crawl(req)

        raise DontCloseSpider

    def item_scraped(self, *args, **kwargs):
        """Avoids waiting for the spider to idle before scheduling the next request"""
        self.schedule_next_request()

    def parse(self, response):
        item = EventLink()

        print(f"{bcolors.OKGREEN}URL: {response.meta.get('url')}{bcolors.ESCAPE}")
        if response.meta.get('url') != response.url:
            print(f"{bcolors.FAIL}REDIRECTION: [{response.meta.get('url')}] -> [{response.url}]")

        self.driver.get(response.url)
        wait = WebDriverWait(self.driver, 10)
        
        body = self.driver.page_source
        selector_response = Selector(text=body)
        
        # Extract all hrefs from a tags with class 'event-card-link'
        links = selector_response.xpath("//a[contains(@class, 'event-card-link')]/@href").getall()
        for url in list(set(links)):
            hash_key = response.meta.get('sheet_name') + url
            data = {
                "id": hashlib.sha256(hash_key.encode()).hexdigest(),
                "url": url,
                "processed": False,
                "source_url": response.meta.get('url'),
                "sheet_name": response.meta.get('sheet_name')
                }
            print(f"{bcolors.OKBLUE}{data}{bcolors.ESCAPE}")
            try:
                self.events_container.create_item(data)
            except:
                print(f"{bcolors.FAIL}Record already exists in cosmos: {url}{bcolors.ESCAPE}")

        hash_key = response.meta.get('sheet_name') + response.meta.get('url')
        item["id"] = hashlib.sha256(hash_key.encode()).hexdigest()
        item["url"] = response.meta.get('url')
        item["processed"] = True
        item["sheet_name"] = response.meta.get('sheet_name')

        self.container.upsert_item(item)
        return item


class EventsSpider(CosmosDBSpiderMixin, Spider):
    name = "eventbrite_links"

    """
    Spider that reads records from a Cosmos DB container when idle.

    This spider will exit only if stopped, otherwise it keeps
    listening to records in the given container.

    Specify the container to listen to by setting the spider's `cosmos_db_container`.

    Records are assumed to contain URLs. To do custom
    processing of Cosmos DB records, override the spider's `process_cosmos_db_record`
    method.
    """

    def __init__(self, *args, **kwargs):
        super(EventsSpider, self).__init__(*args, **kwargs)

        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Ensure GUI is off
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


    def _set_crawler(self, crawler):
        """
        :type crawler: scrapy.crawler.Crawler
        """
        super(EventsSpider, self)._set_crawler(crawler)
        self.setup_cosmos_db(crawler.settings)

    def closed(self, reason):
        self.driver.quit()
