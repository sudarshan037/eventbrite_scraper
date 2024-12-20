# Replace with async cosmos client
import os
import asyncio
import logging
import hashlib
from dotenv import load_dotenv
import pandas as pd
from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError

logging.getLogger(__file__)
load_dotenv()

class AzureCosmos:
    def __init__(self) -> None:
        self.COSMOS_HOST = os.getenv("COSMOS_HOST")
        self.COSMOS_MASTER_KEY = os.getenv("COSMOS_MASTER_KEY")

    async def initialize_cosmosdb(self, DATABASE_ID, CONTAINER_NAME):
        try:
            # Create CosmosClient and store it in the instance variable to keep it alive
            self.client = CosmosClient(self.COSMOS_HOST, {'masterKey': self.COSMOS_MASTER_KEY})
            self.database = self.client.get_database_client(DATABASE_ID)
            self.container = self.database.get_container_client(CONTAINER_NAME)
            print("[INFO] Cosmos client created")
        except Exception as e:
            print("Error initializing Cosmos DB:", e)
        
    async def list_containers(self, DATABASE_ID):
        try:
            container_names = [item["id"] async for item in self.database.list_containers()]
            return container_names
        except Exception as e:
            print("Error initializing Cosmos DB:", e)
            return None
        
    async def fetch_record(self, id):
        '''
        Fetches a conversation by ID from the Cosmos DB.
        '''
        try:
            query=f'SELECT * FROM Conversations c WHERE c.id = "{id}"'
            items = []
            async for item in self.container.query_items(query=query):
                items.append(item)
            return items
        except CosmosHttpResponseError as e:
            print("Error fetching conversation:", e)
            return None
        
    async def execute_query(self, query):
        '''
        Fetches a conversation by ID from the Cosmos DB.
        '''
        try:
            items = []
            async for item in self.container.query_items(query=query):
                items.append(item)
            return items
        except CosmosHttpResponseError as e:
            print("Error fetching conversation:", e)
            return None


    async def create_conversation(self, data):
        if self.container is None:
            print("[ERROR] Cosmos DB container is not initialized.")
            return False
        
        try:
            await self.container.create_item(body=data)
            print("[INFO] Conversation created successfully")
            return True
        except CosmosHttpResponseError as e:
            raise e

    async def delete_conversation(self, id, partition_key):
        '''
        Deletes a conversation from the Cosmos DB by ID.
        '''
        try:
            await self.container.delete_item(item=id, partition_key=partition_key)
            print("[INFO] Conversation deleted successfully")
            return True
        except CosmosHttpResponseError as e:
            print("Error deleting conversation:", e)
            return False
        

if __name__ == "__main__":
    azure_cosmos = AzureCosmos()
    
    async def run():
        await azure_cosmos.initialize_cosmosdb("Scraper", "eventbrite_events")
        # records = await azure_cosmos.list_containers("Scraper")
        # records = await azure_cosmos.fetch_record("some-id")
        query = "SELECT * FROM c OFFSET 0 LIMIT 2"
        # records = await azure_cosmos.execute_query(query)
        # print(records)
        await azure_cosmos.client.close()

    asyncio.run(run())