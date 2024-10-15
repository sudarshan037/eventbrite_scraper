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
    def __init__(self):
        self.offset_flag = True
        self.max_offset = 32
        print(f"max_offset = {self.max_offset}")

        self.USER_AGENTS = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/602.3.12 (KHTML, like Gecko) Version/10.1.2 Safari/602.3.12',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15',
        ]

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
        # query = "SELECT TOP 1 * FROM c WHERE c.processed = false"
        if not self.offset_flag:
            self.offset_flag = True
            self.max_offset = self.max_offset//2
            print(f"max_offset = {self.max_offset}")

        random_offset = random.randrange(0, self.max_offset)
        print(f"random offset: {random_offset}")
        query = f"SELECT * FROM c WHERE c.processed = false OFFSET {random_offset} LIMIT 1"
        # try:
        #     records = list(self.container.query_items(
        #         query=query,
        #         enable_cross_partition_query=True))
        # except CosmosHttpResponseError as e:
        #     print("Error fetching conversation:", e)
        #     records = None
        records = [
            {"url": "https://dice.fm/partner/announcement-3-band-link/event/kr3ap-portals-festival-2023-27th-may-earth-london-tickets", "sheet_name": "dice"},
            {"url": "https://dice.fm/partner/stil-runnin/event/m8w7w-stil-runnin-w-redamancy-estin-the-86d-22nd-apr-the-coast-fort-collins-tickets", "sheet_name": "dice"}
            ]
        
        if not records:
            return None
        
        record = random.choice(records)
        url = self.process_cosmos_db_record(record)
        
        if not url:
            return None
        
        output = scrapy.Request(
                    url=url,
                    callback=self.parse,
                    headers={
                        'User-Agent': random.choice(self.USER_AGENTS)
                    },
                    meta={'sheet_name': record.get("sheet_name", "")}
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
            print("No records found, waiting for 60 seconds before trying again...")
            if self.max_offset <= 1:
                time.sleep(60)
            else:
                self.offset_flag = False
        else:
            self.crawler.engine.crawl(req)

        raise DontCloseSpider

    def item_scraped(self, *args, **kwargs):
        """Avoids waiting for the spider to idle before scheduling the next request"""
        self.schedule_next_request()

    def parse(self, response):
        self.driver = webdriver.Chrome(service=Service(self.chromedriver_path), options=self.chrome_options)
        item = DiceLink()
        item['event_link'] = response.url
        item["url"] = response.url
        print(f"{bcolors.OKGREEN}URL: {item['event_link']}{bcolors.ESCAPE}")
        try:
            self.driver.get(response.url)
            wait = WebDriverWait(self.driver, 10)
            body = self.driver.page_source
            selenium_response = Selector(text=body)
            item['event_name'] = selenium_response.xpath("//h1[@class='EventDetailsTitle__Title-sc-8ebcf47a-0 iLdkPz']/text()").get()
            item['event_date'] = selenium_response.xpath("//div[contains(@class, 'EventDetailsBase__Highlight-sc-d40475af-0')]/div/span/text()").get()
            item['organizer'] = selenium_response.xpath("//div[contains(@class, 'EventDetailsBase__Highlight-sc-d40475af-0')]/div/span/text()").get()
            item['location'] = selenium_response.xpath("//div[@class='EventDetailsVenue__Address-sc-42637e02-5 cxsjwk']/span/text()").get()
        except Exception as e:
            print(f"{bcolors.FAIL}Error processing {response.url}: {str(e)}{bcolors.ESCAPE}")
        item["processed"] = True
        item["sheet_name"] = response.meta.get('sheet_name')
        print(f"{bcolors.OKBLUE}OUTPUT: {item}{bcolors.ESCAPE}")
        # if item:
        #     self.container.upsert_item(item)
        self.driver.quit()
        return item
        

class EventsSpider(CosmosDBSpiderMixin, Spider):
    name = "dice"

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

        home_dir = os.path.expanduser("~")
        current_os = platform.system()

        if current_os == "Linux":
            drivers_dir = f"{home_dir}/.wdm/drivers/chromedriver/linux64/"
            chromedriver_subpath = "chromedriver-linux64/chromedriver"
        elif current_os == "Darwin":  # macOS
            drivers_dir = f"{home_dir}/.wdm/drivers/chromedriver/mac64/"
            chromedriver_subpath = "chromedriver-mac-arm64/chromedriver"
        else:
            raise OSError(f"Unsupported OS: {current_os}")

        versions = glob.glob(os.path.join(drivers_dir, "*"))
        latest_version = sorted(versions, key=os.path.getmtime)[-1]

        self.chromedriver_path = os.path.join(latest_version, chromedriver_subpath)

        if os.path.exists(self.chromedriver_path):
            print(f"Using chromedriver at {self.chromedriver_path}")
            
            # Give the chromedriver file executable permissions
            os.chmod(self.chromedriver_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        else:
            print(f"Chromedriver not found at {self.chromedriver_path}")
            exit()

        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")  # Ensure GUI is off
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        # self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver = webdriver.Chrome(service=Service(self.chromedriver_path), options=self.chrome_options)


    def _set_crawler(self, crawler):
        """
        :type crawler: scrapy.crawler.Crawler
        """
        super(EventsSpider, self)._set_crawler(crawler)
        self.setup_cosmos_db(crawler.settings)
        
    # def start_requests(self):
    #     """
    #     Override start_requests to use the custom method for generating initial requests.
    #     """
    #     req = self.next_request()
    #     if req:
    #         yield req

    def closed(self, reason):
        self.driver.quit()
