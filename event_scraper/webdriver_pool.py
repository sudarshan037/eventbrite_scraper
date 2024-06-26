import os
import time
import threading
from queue import Queue
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class WebDriverPool:
    def __init__(self, maxsize=1):
        self.pool = Queue(maxsize=maxsize)
        for _ in range(maxsize):
            self.pool.put(self._create_driver())
        # self.lock = threading.Lock()

    def _create_driver(self):
        os.system('rm -rf ~/.wdm')
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        return driver

    def get_driver(self):
        return self.pool.get()

    def release_driver(self, driver):
        self.pool.put(driver)

    def close_all(self):
        print("closing the pool")
        while not self.pool.empty():
            driver = self.pool.get()
            driver.quit()

webdriver_pool = WebDriverPool(maxsize=1)