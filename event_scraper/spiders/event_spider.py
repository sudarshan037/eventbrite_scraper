import scrapy
import pandas as pd
from scrapy.selector import Selector
from event_scraper.items import EventItem  # Assuming you'll define EventItem in items.py

class EventSpider(scrapy.Spider):
    name = 'event_spider'
    allowed_domains = ['eventbrite.com']  # Add other domains if scraping other websites
    df = pd.read_excel("inputs.xlsx")
    # df = df.head(3)
    # df = df[df[["event_name", "followers", "date", "price", "location", "organiser_name"]].isna().all(axis=1)]
    # start_urls = df["event_link"].to_list()
    # start_urls = [
    #     'https://www.eventbrite.com/e/the-rolling-tones-at-hudak-house-tickets-926567788197`',
    #     'https://www.eventbrite.com/e/club-privata-vip-suite-reservations-tickets-321505992077'
    # ]

    def parse(self, response):
        item = EventItem()

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
            self.logger.error(f"Error extracting followers: {e}")
        yield item