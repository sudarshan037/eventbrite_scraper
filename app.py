# app.py

import pandas as pd
from azure_cosmos_db import AzureCosmos  # Importing the adapter

def main():
    # Load Excel data
    excel_file = '/Users/arushigogia/Downloads/Personal/Event_Scraper/eventbrite_scraper/eventbrite_scraper/data/inputs/links.xlsx'  # Replace with your Excel file path
    df = pd.read_excel(excel_file)

    # Initialize Cosmos DB client
    cosmos = AzureCosmos()

    # Insert each row into Cosmos DB
    for index, row in df.iterrows():
        link_data = {
            'id': str(index),  # Using the index as a unique ID, modify as needed
            'links': row[0],  # Assuming the URLs are in the first column
        }
        cosmos.create_conversation(link_data)

if __name__ == "__main__":
    main()
