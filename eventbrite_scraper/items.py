# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EventbriteScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class EventItem(scrapy.Item):
    id = scrapy.Field()
    links = scrapy.Field()
    processed = scrapy.Field()
    sheet_name = scrapy.Field()

    event_link = scrapy.Field()
    event_name = scrapy.Field()
    date = scrapy.Field()
    price = scrapy.Field()
    location = scrapy.Field()
    organiser_name = scrapy.Field()
    followers = scrapy.Field()

class EventLink(scrapy.Item):
    id = scrapy.Field()
    processed = scrapy.Field()
    sheet_name = scrapy.Field()

    link_name = scrapy.Field()

class DiceLink(scrapy.Item):
    id = scrapy.Field()
    links = scrapy.Field()
    processed = scrapy.Field()
    sheet_name = scrapy.Field()

    url = scrapy.Field()
    event_link = scrapy.Field()
    event_name = scrapy.Field()
    event_date = scrapy.Field()
    organizer = scrapy.Field()
    location = scrapy.Field()
    

class Shotgun(scrapy.Item):
    id = scrapy.Field()
    links = scrapy.Field()
    processed = scrapy.Field()
    sheet_name = scrapy.Field()

    event_link = scrapy.Field()
    event_name = scrapy.Field()