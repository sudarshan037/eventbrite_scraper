from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError

class AzureCosmos:
    def __init__(self) -> None:
        self.COSMOS_HOST = "https://cosmos-scraper.documents.azure.com:443/"
        self.COSMOS_MASTER_KEY = "bBgVEeSnEQaSss88e8zZU5pjpiVzPjba5qpe6alFqU548KcW2eMkCeUf7J99RWVUPw6ASV32W8pGACDb5ZhxrA=="
        self.DATABASE_ID = "Scraper"
        self.CONTAINER_NAME = "eventBrite_links"
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
            for item in self.container.query_items(
                query=f'SELECT * FROM Conversations c WHERE c.id = "{conversation_id}"',
                enable_cross_partition_query=True):
                conversation_array = item['conversationArray']
            return conversation_array
        except CosmosHttpResponseError as e:
            print("Error fetching conversation:", e)
            return None

    def create_conversation(self, conversation_data):
        if self.container is None:
            print("[ERROR] Cosmos DB container is not initialized.")
            return False
        try:
            # No need to pass partition_key as a separate argument
            self.container.create_item(body=conversation_data)
            print("[INFO] Conversation created successfully with partition key")
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
