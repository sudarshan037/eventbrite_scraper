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
    link = scrapy.Field()
    username = scrapy.Field()
    posts = scrapy.Field()
    followers = scrapy.Field()
    following = scrapy.Field()
    bio = scrapy.Field()
    bio_links = scrapy.Field()
    professional = scrapy.Field()
    verified = scrapy.Field()