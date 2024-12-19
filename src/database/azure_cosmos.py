# Replace with async cosmos client

import logging
import hashlib
import pandas as pd
from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceExistsError

logging.getLogger(__file__)

class AzureCosmos:
    def __init__(self) -> None:
        self.COSMOS_HOST = "" # TODO: get from .env
        self.COSMOS_MASTER_KEY = "" # TODO: get from .env

    def initialize_cosmosdb(self, DATABASE_ID, CONTAINER_NAME):
        try:
            self.client = CosmosClient(self.COSMOS_HOST, {'masterKey': self.COSMOS_MASTER_KEY})
            self.database = self.client.get_database_client(DATABASE_ID)
            self.container = self.database.get_container_client(CONTAINER_NAME)
            print("[INFO] Cosmos client created")
        except Exception as e:
            print("Error initializing Cosmos DB:", e)
        
    def list_containers(self, DATABASE_ID):
        try:
            client = CosmosClient(self.COSMOS_HOST, {'masterKey': self.COSMOS_MASTER_KEY})
            database = client.get_database_client(DATABASE_ID)
            containers = database.list_containers()
            container_names = [container['id'] for container in containers]
            return container_names
        except Exception as e:
            print("Error initializing Cosmos DB:", e)
            return None
        
    def fetch_record(self, id):
        '''
        Fetches a conversation by ID from the Cosmos DB.
        '''
        try:
            items = list(self.container.query_items(
                query=f'SELECT * FROM Conversations c WHERE c.id = "{id}"',
                enable_cross_partition_query=True))
            return items
        except CosmosHttpResponseError as e:
            print("Error fetching conversation:", e)
            return None
        
    def execute_query(self, query):
        pass


    def create_conversation(self, data):
        if self.container is None:
            print("[ERROR] Cosmos DB container is not initialized.")
            return False
        
        try:
            self.container.create_item(body=data)
            print("[INFO] Conversation created successfully")
            return True
        except CosmosHttpResponseError as e:
            raise e

    def delete_conversation(self, id, partition_key):
        '''
        Deletes a conversation from the Cosmos DB by ID.
        '''
        try:
            self.container.delete_item(item=id, partition_key=partition_key)
            print("[INFO] Conversation deleted successfully")
            return True
        except CosmosHttpResponseError as e:
            print("Error deleting conversation:", e)
            return False
        

if __name__ == "__main__":
    azure_cosmos = AzureCosmos()
    azure_cosmos.DATABASE_ID, azure_cosmos.CONTAINER_NAME = "Scraper", "eventbrite_events"
    azure_cosmos.container = azure_cosmos.initialize_cosmosdb()