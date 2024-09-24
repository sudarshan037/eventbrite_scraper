import time
import random
import hashlib
import scrapy
from azure.cosmos.exceptions import CosmosHttpResponseError
from scrapy import signals
from scrapy.exceptions import DontCloseSpider
from scrapy.spiders import Spider

from eventbrite_scraper.items import ShotgunLink
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
        self.cosmos_db_container_name = "shotgun_links"

        self.client = CosmosClient(self.cosmos_db_uri, self.cosmos_db_key)
        self.database = self.client.get_database_client(self.cosmos_db_database)
        self.container = self.database.get_container_client(self.cosmos_db_container_name)
        self.events_container = self.database.get_container_client("shotgun_events")

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

        if not records:
            return None
        
        record = records[0]
        url = self.process_cosmos_db_record(record)
        
        if not url:
            return None
        
        output =  scrapy.Request(
                    url=url,
                    callback=self.parse,
                    headers={
                        'User-Agent': random.choice(self.USER_AGENTS)
                    },
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

    def extract_first_link_by_event_type(self):
        try:
        # Check for the "Upcoming Events" section
            upcoming_events_header = self.driver.find_element(By.XPATH, "//h2[text()='Upcoming Events']")
            print(f"{bcolors.HEADER}Found 'Upcoming Events' section{bcolors.ESCAPE}")
            
            # Extract the first link under "Upcoming Events"
            first_upcoming_event_link = self.driver.find_element(By.XPATH, "(//h2[text()='Upcoming Events']/following-sibling::div//a)[1]")
            print(f"{bcolors.HEADER}First 'Upcoming Event' link: {first_upcoming_event_link.get_attribute('href')}{bcolors.ESCAPE}")
            return first_upcoming_event_link.get_attribute('href')
        
        except Exception as e:
            print(f"{bcolors.HEADER}Upcoming Events section not found or no link present: {str(e)}{bcolors.ESCAPE}")

        try:
        # Check for the "Past Events" section if "Upcoming Events" wasn't found
            past_events_header = self.driver.find_element(By.XPATH, "//h2[text()='Past Events']")
            print(f"{bcolors.HEADER}Found 'Past Events' section{bcolors.ESCAPE}")
            
            # Extract the first link under "Past Events"
            first_past_event_link = self.driver.find_element(By.XPATH, "(//h2[text()='Past Events']/following-sibling::div//a)[1]")
            print(f"{bcolors.HEADER}First 'Past Event' link: {first_past_event_link.get_attribute('href')}{bcolors.ESCAPE}")
            return first_past_event_link.get_attribute('href')
        
        except Exception as e:
            print(f"{bcolors.HEADER}Past Events section not found or no link present: {str(e)}{bcolors.ESCAPE}")
    
        return ""

    def parse(self, response):
        print(f"{bcolors.OKGREEN}URL: {response.meta.get('url')}{bcolors.ESCAPE}")
        if response.meta.get('url') != response.url:
            print(f"{bcolors.FAIL}REDIRECTION: [{response.meta.get('url')}] -> [{response.url}]")

        if response.status in [400, 403, 404]:
            print(f"{bcolors.FAIL}{response.status} Error: {response.url}{bcolors.ESCAPE}")
            # self.container.delete_item(item=item_id, partition_key=response.meta.get('sheet_name'))
            item = {
                "id": hashlib.sha256(response.meta.get('url').encode()).hexdigest(),
                "url": response.meta.get('url'),
                "processed": True,
                "event_url": f"ERROR: {str(response.status)}",
                "sheet_name": response.meta.get('sheet_name')
            }
            self.container.upsert_item(item)
            return
        
        elif response.status == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            retry_after += 10
            print(f"{bcolors.FAIL}Rate limited. Retrying after {retry_after} seconds.{bcolors.ESCAPE}")
            time.sleep(retry_after)
            return

        item = ShotgunLink()

        try:
            self.driver.get(response.url)
            # wait = WebDriverWait(self.driver, 10)
            # body = self.driver.page_source
            # selector_response = Selector(text=body)
            event_url = self.extract_first_link_by_event_type()
            data = {
                "id": hashlib.sha256(event_url.encode()).hexdigest(),
                "url": event_url,
                "processed": False,
                "source_url": response.meta.get('url'),
                "sheet_name": response.meta.get('sheet_name'),
            }
            print(f"{bcolors.OKBLUE}{data}{bcolors.ESCAPE}")

            try:
                self.events_container.create_item(data)
            except:
                print(f"{bcolors.FAIL}Record already exists in cosmos: {data['url']}{bcolors.ESCAPE}")

        except Exception as e:
            print(f"{bcolors.FAIL}Error processing {response.url}: {str(e)}{bcolors.ESCAPE}")
            item = {
                "id": hashlib.sha256(response.meta.get('url').encode()).hexdigest(),
                "url": response.meta.get('url'),
                "processed": True,
                "event_url": f"ERROR in processing URL",
                "sheet_name": response.meta.get('sheet_name')
            }
            self.container.upsert_item(item)
            return

        item["id"] = hashlib.sha256(response.meta.get('url').encode()).hexdigest()
        item["url"] = response.meta.get('url')
        item["processed"] = True
        item["sheet_name"] = response.meta.get('sheet_name')

        print(f"{bcolors.OKBLUE}OUTPUT: {item}{bcolors.ESCAPE}")
        if item:
            self.container.upsert_item(item)
        return item
        

class EventsSpider(CosmosDBSpiderMixin, Spider):
    name = "shotgun_links"

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
        
    def start_requests(self):
        """
        Override start_requests to use the custom method for generating initial requests.
        """
        req = self.next_request()
        if req:
            yield req

    def closed(self, reason):
        self.driver.quit()
