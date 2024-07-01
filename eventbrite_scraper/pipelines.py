# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pandas as pd
from datetime import datetime

class EventbriteScraperPipeline:
    def process_item(self, item, spider):
        return item

class ExcelExportPipeline:
    def open_spider(self, spider):
        self.items = []

    def close_spider(self, spider):
        df = pd.DataFrame(self.items)
        timestamp = datetime.now()
        df.to_excel(f"data/outputs/events_{str(timestamp)}.xlsx", index=False)
        print("Excel file saved.")

    def process_item(self, item, spider):
        self.items.append(dict(item))
        return item