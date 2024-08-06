# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pandas as pd
from datetime import datetime
from eventbrite_scraper.utils import bcolors

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
        if spider.name == "events":
            df = pd.DataFrame(self.items)
            df.to_excel(f"data/outputs/events_{str(timestamp)}.xlsx", index=False)
        elif spider.name == "links":
            data =[]
            for item in self.items:
                link_name = item['link_name']
                print(f"{bcolors.OKCYAN}{link_name}{bcolors.ESCAPE}")
                extracted_links = set(item['links'])
                for link in extracted_links:
                    data.append({'main_link': link_name, 'Event_link': link})
            # link_name = self.items[0]['link_name']
            # print(f"{bcolors.OKCYAN}{link_name}{bcolors.ESCAPE}")
            # extracted_links = list(set(self.items[0]['links']))
            df = pd.DataFrame(data)
            # df['main_link'] = link_name
            df.to_excel(f"data/inputs/events_{str(timestamp)}.xlsx", index=False)
        else:
            print("Excel file not saved.")

    def process_item(self, item, spider):
        self.items.append(dict(item))
        return item