# Replace with async cosmos client
import os
import asyncio
import logging
import hashlib
from dotenv import load_dotenv
import pandas as pd
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey, exceptions

logging.getLogger(__file__)
load_dotenv()

class AzureCosmos:
    def __init__(self) -> None:
        self.COSMOS_HOST = os.getenv("COSMOS_HOST")
        self.COSMOS_MASTER_KEY = os.getenv("COSMOS_MASTER_KEY")
        self.client = CosmosClient(self.COSMOS_HOST, {'masterKey': self.COSMOS_MASTER_KEY})
        
    async def list_containers(self, database_name):
        database = self.client.get_database_client(database_name)
        return [container['id'] async for container in database.list_containers()]
        
    async def query_items(self, database_name, container_name, query):
        container = self.client.get_database_client(database_name).get_container_client(container_name)
        items = container.query_items(
            query=query,
            enable_cross_partition_query=True
        )
        return [item async for item in items]
    
    async def read_item(self, database_name, container_name, item_id):
        container = self.client.get_database_client(database_name).get_container_client(container_name)
        return await container.read_item(item=item_id, enable_cross_partition_query=True)
        
    async def create_item(self, database_name, container_name, item):
        container = self.client.get_database_client(database_name).get_container_client(container_name)
        return await container.create_item(item)
    
    async def upsert_item(self, database_name, container_name, item):
        container = self.client.get_database_client(database_name).get_container_client(container_name)
        return await container.upsert_item(item)

    async def delete_item(self, database_name, container_name, item_id, partition_key):
        container = self.client.get_database_client(database_name).get_container_client(container_name)
        return await container.delete_item(item=item_id, partition_key=partition_key)
        

if __name__ == "__main__":
    async def run():
        azure_cosmos = AzureCosmos()
        # await azure_cosmos.initialize_cosmosdb("Scraper", "eventbrite_events")
        records = await azure_cosmos.list_containers("Scraper")
        # records = await azure_cosmos.fetch_record("some-id")
        # query = "SELECT * FROM c OFFSET 0 LIMIT 2"
        # records = await azure_cosmos.execute_query(query)
        print(records)
        await azure_cosmos.client.close()

    asyncio.run(run())