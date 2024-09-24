# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pandas as pd
from datetime import datetime
from eventbrite_scraper.utils import bcolors
from azure_cosmos_db import AzureCosmos

class EventbriteScraperPipeline:
    def process_item(self, item, spider):
        return item

class ExcelExportPipeline:
    def open_spider(self, spider):
        self.items = []

    def close_spider(self, spider):
        print(f"{bcolors.OKGREEN}{self.items}{bcolors.ESCAPE}")
        
        timestamp = datetime.now()
        print(f"SPIDER_NAME: {spider.name}")
        if spider.name in ["eventbrite_events", "eventbrite_links", "dice_events", "shotgun_links", "shotgun_events"]:
            df = pd.DataFrame(self.items)
            df.to_excel(f"data/outputs/{spider.name}_{str(timestamp)}.xlsx", index=False)
        else:
            print("Excel file not saved.")

    def process_item(self, item, spider):
        self.items.append(dict(item))
        return item