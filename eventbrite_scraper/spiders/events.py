import scrapy
import pandas as pd
from eventbrite_scraper.items import EventItem
from eventbrite_scraper.utils import bcolors

class EventsSpider(scrapy.Spider):
    name = "events"
    url_counter = 0
    
    def start_requests(self):
        df = pd.read_excel("data/inputs/inputs.xlsx")
        df = df.sample(30)
        for url in df["Event_link"].to_list():
            yield scrapy.Request(url)
        

    def parse(self, response):
        item = EventItem()
        self.url_counter += 1

        item['event_link'] = response.url
        item['event_name'] = response.xpath("//h1[contains(@class, 'event-title')]/text()").get()
        item['date'] = response.xpath("//time[contains(@class, 'start-date')]/text()").get()
        item['price'] = response.css('#root > div > div > div.eds-structure__body > div > div > div > div.eds-fixed-bottom-bar-layout__content > div > main > div.event-listing.event-listing--has-image > div.event-details.event-details--has-hero-section > div.event-details__wrapper > div.Layout-module__layout___1vM08 > div.Layout-module__module___2eUcs.Layout-module__aside___2Tdmd > div > div.conversion-bar-bordered > div.conversion-bar.conversion-bar--checkout-opener > div.conversion-bar__body > div::text').get()
        item['location'] = response.xpath("//div[contains(@class, 'location-info__address')]/text()").get()
        item['organiser_name'] = response.xpath("//strong[contains(@class, 'organizer-listing-info-variant-b__name-link')]/text()").get()
        item['followers'] = response.xpath("//span[contains(@class, 'organizer-stats__highlight')]/text()").get()
        print(f"{bcolors.OKGREEN}{self.url_counter} URL: {response.url}{bcolors.ESCAPE}{item}")
        yield item