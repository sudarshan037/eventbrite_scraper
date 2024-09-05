import logging
import hashlib
import pandas as pd
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError

class AzureCosmos:
    def __init__(self) -> None:
        logging.getLogger('azure').setLevel(logging.CRITICAL)

        self.COSMOS_HOST = "https://cosmos-scraper.documents.azure.com:443/"
        self.COSMOS_MASTER_KEY = "bBgVEeSnEQaSss88e8zZU5pjpiVzPjba5qpe6alFqU548KcW2eMkCeUf7J99RWVUPw6ASV32W8pGACDb5ZhxrA=="
        self.DATABASE_ID = "Scraper"
        self.CONTAINER_NAME = "eventBrite_events"
        self.container = self.initialize_cosmosdb()

    def initialize_cosmosdb(self):
        try:
            client = CosmosClient(self.COSMOS_HOST, {'masterKey': self.COSMOS_MASTER_KEY})
            database = client.get_database_client(self.DATABASE_ID)
            container = database.get_container_client(self.CONTAINER_NAME)
            print("[INFO] Cosmos client created")
            return container
        except Exception as e:
            print("Error initializing Cosmos DB:", e)
            return None
        
    def fetch_conversation(self, conversation_id):
        '''
        Fetches a conversation by ID from the Cosmos DB.
        '''
        try:
            items = list(self.container.query_items(
                query=f'SELECT * FROM Conversations c WHERE c.id = "{conversation_id}"',
                enable_cross_partition_query=True))
            return items
        except CosmosHttpResponseError as e:
            print("Error fetching conversation:", e)
            return None
        
    def fetch_one_record(self):
        try:
            item = list(self.container.query_items(
                query=f'SELECT TOP 1 * FROM c WHERE c.processed = true OR NOT IS_DEFINED(c.followers)',
                enable_cross_partition_query=True))
            return item
        except CosmosHttpResponseError as e:
            print("Error fetching conversation:", e)
            return None
        
    def pop_one_record(self, data):
        try:
            data["processed"] = True
            self.container.replace_item(item=data["id"], body=data)
            print(f"{data['url']} removed from cosmos")
        except CosmosHttpResponseError as e:
            print("Error fetching conversation:", e)


    def create_conversation(self, conversation_data):
        if self.container is None:
            print("[ERROR] Cosmos DB container is not initialized.")
            return False
        
        conversation_id = conversation_data["id"]
        existing_conversation = self.fetch_conversation(conversation_id)

        if existing_conversation:
            print(f"[INFO] Record already exists in {self.CONTAINER_NAME}, skipping insertion.")
            return False

        try:
            self.container.create_item(body=conversation_data)
            print("[INFO] Conversation created successfully")
            return True
        except CosmosHttpResponseError as e:
            print("Error creating conversation:", e)
            return False

    def update_conversation(self, conversation_id, update_data):
        '''
        Updates an existing conversation in the Cosmos DB by ID.
        '''
        try:
            item = self.container.read_item(item=conversation_id, partition_key=conversation_id)
            for key, value in update_data.items():
                item[key] = value
            self.container.replace_item(item=conversation_id, body=item)
            print("[INFO] Conversation updated successfully")
            return True
        except CosmosHttpResponseError as e:
            print("Error updating conversation:", e)
            return False

    def delete_conversation(self, conversation_id):
        '''
        Deletes a conversation from the Cosmos DB by ID.
        '''
        try:
            self.container.delete_item(item=conversation_id, partition_key=conversation_id)
            print("[INFO] Conversation deleted successfully")
            return True
        except CosmosHttpResponseError as e:
            print("Error deleting conversation:", e)
            return False
        

if __name__ == "__main__":
    df = pd.read_csv("data/inputs/Dating events - Sheet4.csv")
    # df = pd.read_excel("data/inputs/links.xlsx")
    # df = df.head(2)
    urls = df["Event_link"].to_list()
    # urls = df["links"].to_list()

    azure_cosmos = AzureCosmos()
    # azure_cosmos.DATABASE_ID, azure_cosmos.CONTAINER_NAME = "Scraper", "eventBrite_links"
    azure_cosmos.DATABASE_ID, azure_cosmos.CONTAINER_NAME = "Scraper", "eventBrite_events"
    azure_cosmos.container = azure_cosmos.initialize_cosmosdb()
    # print(azure_cosmos.fetch_one_record())
    for url in urls:
        print(url)
        data = {
            "id": hashlib.sha256(url.encode()).hexdigest(),
            "url": url,
            "processed": False
        }
        azure_cosmos.create_conversation(conversation_data=data)