# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from tqdm import tqdm

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suppress logging from selenium and urllib3
logging.getLogger('selenium.webdriver.remote.remote_connection').setLevel(logging.WARNING)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)


class EventScraperSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class EventScraperDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

import time
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from scrapy.http import HtmlResponse
from .webdriver_pool import webdriver_pool

class SeleniumMiddleware:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def scroll_to_bottom(self, driver):
        self.logger.debug("Scrolling to the bottom of the page.")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Adjust the sleep time as needed

    def click_button_with_retry(self, driver, button_text, retries=1):
        attempt = 0
        while attempt < retries:
            try:
                self.logger.debug(f"Attempting to click button with text '{button_text}', attempt {attempt + 1}")

                # Attempt to find and click the button
                wait = WebDriverWait(driver, 3)
                button = wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[text()='{button_text}']")))
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                button.click()
                wait.until(EC.staleness_of(button))
                self.logger.debug(f"Successfully clicked button with text '{button_text}'")
                return True
            except Exception as e:
                self.logger.error(f"Error clicking the button: {e}, attempt {attempt + 1} of {retries}")
                attempt += 1
        self.logger.error(f"Failed to click button with text '{button_text}' after {retries} attempts")
        return False


    def process_request(self, request, spider):
        driver = webdriver_pool.get_driver()
        self.logger.debug(f"Processing request for URL: {request.url}")
        driver.get(request.url)
        time.sleep(2)

        # Use the text content to find buttons
        button1_text = 'View event'
        button2_text = 'View all event details'

        # # Attempt to click the buttons with retry mechanism
        # if not self.click_button_with_retry(driver, button1_text):
        #     self.logger.error("Failed to click button1 after multiple attempts")

        # if not self.click_button_with_retry(driver, button2_text):
        #     self.logger.error("Failed to click button2 after multiple attempts")

        # Wait for the page to load
        wait = WebDriverWait(driver, 5)
        try:
            wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
            self.logger.debug("Page loaded successfully.")
        except Exception as e:
            self.logger.error(f"Error waiting for page to load: {e}")

        body = driver.page_source
        response = HtmlResponse(driver.current_url, body=body, encoding='utf-8', request=request)
        print(f"response -> {response}")
        
        # Release the driver back to the pool
        webdriver_pool.release_driver(driver)
        
        return response


    def __del__(self):
        webdriver_pool.close_all()