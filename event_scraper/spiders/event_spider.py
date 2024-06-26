import scrapy
import pandas as pd
from scrapy.selector import Selector
from event_scraper.items import EventItem  # Assuming you'll define EventItem in items.py

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ESCAPE = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class EventSpider(scrapy.Spider):
    name = 'event_spider'
    allowed_domains = ['eventbrite.com']  # Add other domains if scraping other websites
    def __init__(self):
        self.url_counter = 0
        df = pd.read_excel("inputs.xlsx")
        df = df.sample(30)
        self.start_urls = df["Event_link"].to_list()
        # start_urls = [
        #     'https://www.eventbrite.com/e/the-rolling-tones-at-hudak-house-tickets-926567788197`',
        #     'https://www.eventbrite.com/e/club-privata-vip-suite-reservations-tickets-321505992077',
        #     'https://www.eventbrite.com/e/july-asl-wine-tasting-at-community-wine-bar-tickets-872767159067'
        # ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        item = EventItem()
        self.url_counter += 1

        # Extracting data using XPath selectors
        item['event_link'] = response.url
        try:
            # item['event_name'] = response.css('#root > div > div > div.eds-structure__body > div > div > div > div.eds-fixed-bottom-bar-layout__content > div > main > div.event-listing.event-listing--has-image > div.event-details.event-details--has-hero-section > div.event-details__wrapper > div.Layout-module__layout___1vM08 > div.Layout-module__module___2eUcs.Layout-module__mainContent___1b1nj > div.Layout-module__module___2eUcs.Layout-module__title___2YUKj > div > h1::text').get()
            item['event_name'] = response.xpath("//h1[contains(@class, 'event-title')]/text()").get()
        except Exception as e:
            self.logger.error(f"Error extracting event_name: {e}")
        try:
            # item['date'] = response.css('#root > div > div > div.eds-structure__body > div > div > div > div.eds-fixed-bottom-bar-layout__content > div > main > div.event-listing.event-listing--has-image > div.event-details.event-details--has-hero-section > div.event-details__wrapper > div.Layout-module__layout___1vM08 > div.Layout-module__module___2eUcs.Layout-module__mainContent___1b1nj > div.Layout-module__module___2eUcs.Layout-module__startDate___NRUA4 > div > time::text').get()
            item['date'] = response.xpath("//time[contains(@class, 'start-date')]/text()").get()
        except Exception as e:
            self.logger.error(f"Error extracting date: {e}")
        try:
            item['price'] = response.css('#root > div > div > div.eds-structure__body > div > div > div > div.eds-fixed-bottom-bar-layout__content > div > main > div.event-listing.event-listing--has-image > div.event-details.event-details--has-hero-section > div.event-details__wrapper > div.Layout-module__layout___1vM08 > div.Layout-module__module___2eUcs.Layout-module__aside___2Tdmd > div > div.conversion-bar-bordered > div.conversion-bar.conversion-bar--checkout-opener > div.conversion-bar__body > div::text').get()
        except Exception as e:
            self.logger.error(f"Error extracting price: {e}")
        try:
            # item['location'] = response.css('#root > div > div > div.eds-structure__body > div > div > div > div.eds-fixed-bottom-bar-layout__content > div > main > div.event-listing.event-listing--has-image > div.event-details.event-details--has-hero-section > div.event-details__wrapper > div.Layout-module__layout___1vM08 > div.Layout-module__module___2eUcs.Layout-module__mainContent___1b1nj > div.Layout-module__module___2eUcs.Layout-module__location___-D6BU > section > div > div > div > div.location-info > div::text').get()
            item['location'] = response.xpath("//div[contains(@class, 'location-info__address')]/text()").get()
        except Exception as e:
            self.logger.error(f"Error extracting location: {e}")
        try:
            # item['organiser_name'] = response.css('#root > div > div > div.eds-structure__body > div > div > div > div.eds-fixed-bottom-bar-layout__content > div > main > div.event-listing.event-listing--has-image > div.event-details.event-details--has-hero-section > div.event-details__wrapper > div.Layout-module__layout___1vM08 > div.Layout-module__module___2eUcs.Layout-module__mainContent___1b1nj > div.Layout-module__module___2eUcs.Layout-module__organizerBrief___2a4uj > div > div > section > div.organizer-listing-info-variant-b__profile.reverse-image > div.organizer-listing-info-variant-b__details > div.organizer-listing-info-variant-b__card-info > span > strong::text').get()
            item['organiser_name'] = response.xpath("//strong[contains(@class, 'organizer-listing-info-variant-b__name-link')]/text()").get()
        except Exception as e:
            self.logger.error(f"Error extracting organiser_name: {e}")
        try:
            # item['followers'] = response.css('#root > div > div > div.eds-structure__body > div > div > div > div.eds-fixed-bottom-bar-layout__content > div > main > div.event-listing.event-listing--has-image > div.event-details.event-details--has-hero-section > div.event-details__wrapper > div.Layout-module__layout___1vM08 > div.Layout-module__module___2eUcs.Layout-module__mainContent___1b1nj > div.Layout-module__module___2eUcs.Layout-module__organizerPanel___2A34d > div > section > section > div.descriptive-organizer-info-mobile > div.descriptive-organizer-info-heading-signal-container > div.descriptive-organizer-info-mobile__followers-stats > div.organizer-stats.organizer-stats--condensed-full-width > div > span.organizer-stats__highlight::text').get()
            item['followers'] = response.xpath("//span[contains(@class, 'organizer-stats__highlight')]/text()").get()
        except Exception as e:
            print(f"Error extracting followers: {e}")
        print(f"{bcolors.OKGREEN}{self.url_counter} URL: {response.url}{bcolors.ESCAPE}\n{item}")
        yield item