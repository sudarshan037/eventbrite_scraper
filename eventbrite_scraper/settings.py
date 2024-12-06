# Scrapy settings for eventbrite_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "eventbrite_scraper"

SPIDER_MODULES = ["eventbrite_scraper.spiders"]
NEWSPIDER_MODULE = "eventbrite_scraper.spiders"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'scrapy.utils.log': {
            'level': 'WARNING',
        },
        'selenium.webdriver.common.service': {
            'level': 'WARNING',
        },
        'selenium.webdriver.common.driver_finder': {
            'level': 'WARNING',
        },
        'WDM': {
            'level': 'WARNING',
        },
        'asyncio': {
            'level': 'WARNING',
        },
    },
}

LOG_ENABLED = True  # Enable logging (default: True)
LOG_LEVEL = 'INFO'  # Set the logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
LOG_FILE = 'scrapy.log'  # Log to a file instead of the console (optional)
LOG_STDOUT = False  # Redirect stdout (e.g., print statements) to Scrapy log


FEEDS = {
    "data/%(name)s/%(name)s_%(time)s.json": {"format": "json"}
}

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "eventbrite_scraper (+http://www.yourdomain.com)"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 0.5
# AUTOTHROTTLE_ENABLED = True
# AUTOTHROTTLE_START_DELAY = 5  # Initial download delay
# AUTOTHROTTLE_MAX_DELAY = 60   # Maximum download delay

# The download delay setting will honor only one of:
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 1

DUPEFILTER_CLASS = 'scrapy.dupefilters.BaseDupeFilter'
HTTPERROR_ALLOWED_CODES = [400, 404, 429, 403]

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "eventbrite_scraper.middlewares.EventbriteScraperSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "eventbrite_scraper.middlewares.EventbriteScraperDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "eventbrite_scraper.pipelines.ExcelExportPipeline": 300,
    # "eventbrite_scraper.pipelines.CosmosUploadPipeline": 300,
    # "eventbrite_scraper.pipelines.EventbriteScraperPipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

DOWNLOADER_MIDDLEWARES = {
    'scrapy_selenium.SeleniumMiddleware': 800
}

COSMOS_DB_URI = "https://cosmos-scraper.documents.azure.com:443/"
COSMOS_DB_KEY = "bBgVEeSnEQaSss88e8zZU5pjpiVzPjba5qpe6alFqU548KcW2eMkCeUf7J99RWVUPw6ASV32W8pGACDb5ZhxrA=="
COSMOS_DB_DATABASE = "Scraper"
COSMOS_DB_CONTAINER = "eventBrite_events"

RETRY_HTTP_CODES = [429, 500, 502, 503, 504]
RETRY_TIMES = 2
