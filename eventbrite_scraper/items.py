# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EventbriteScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class EventLink(scrapy.Item):
    id = scrapy.Field()
    url = scrapy.Field()
    processed = scrapy.Field()
    sheet_name = scrapy.Field()

class EventItem(scrapy.Item):
    id = scrapy.Field()
    url = scrapy.Field()
    processed = scrapy.Field()
    source_url = scrapy.Field()
    sheet_name = scrapy.Field()

    event_name = scrapy.Field()
    date = scrapy.Field()
    price = scrapy.Field()
    location = scrapy.Field()
    organiser_name = scrapy.Field()
    followers = scrapy.Field()



class DiceLink(scrapy.Item):
    id = scrapy.Field()
    url = scrapy.Field()
    processed = scrapy.Field()
    sheet_name = scrapy.Field()

    event_name = scrapy.Field()
    date = scrapy.Field()
    location = scrapy.Field()
    organiser_name = scrapy.Field()
    

class ShotgunLink(scrapy.Item):
    id = scrapy.Field()
    url = scrapy.Field()
    processed = scrapy.Field()
    sheet_name = scrapy.Field()

class ShotgunEvents(scrapy.Item):
    id = scrapy.Field()
    url = scrapy.Field()
    processed = scrapy.Field()
    source_url = scrapy.Field()
    sheet_name = scrapy.Field()

    event_name = scrapy.Field()
    date = scrapy.Field()
    location = scrapy.Field()
    followers_1 = scrapy.Field()
    followers_2 = scrapy.Field()
    organiser_name_1 = scrapy.Field()
    organiser_name_2 = scrapy.Field()