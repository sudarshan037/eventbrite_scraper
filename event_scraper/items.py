# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EventScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class EventItem(scrapy.Item):
    event_link = scrapy.Field()
    event_name = scrapy.Field()
    date = scrapy.Field()
    price = scrapy.Field()
    location = scrapy.Field()
    organiser_name = scrapy.Field()
    followers = scrapy.Field()

