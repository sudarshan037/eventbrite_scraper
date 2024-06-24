import os
import time
import threading
from queue import Queue
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class WebDriverPool:
    def __init__(self, size=1):
        self.size = size
        self.pool = Queue(maxsize=size)
        self.lock = threading.Lock()

        # Clear the WebDriverManager cache and reinstall ChromeDriver
        os.system('rm -rf ~/.wdm')
        chrome_driver_path = ChromeDriverManager().install()

        for _ in range(size):
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Ensure GUI is off
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(service=ChromeService(chrome_driver_path), options=chrome_options)
            self.pool.put(driver)

    def get_driver(self):
        return self.pool.get()

    def release_driver(self, driver):
        self.pool.put(driver)

    def close_all(self):
        while not self.pool.empty():
            driver = self.pool.get()
            driver.quit()

# Create a singleton instance of WebDriverPool
webdriver_pool = WebDriverPool(size=1)