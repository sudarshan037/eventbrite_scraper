import os

if "notebooks" in os.getcwd():
    os.chdir("..")

import time
import requests
import pandas as pd
from tqdm import tqdm

SCRAPER_NAME = "shotgun_links"
INPUT_FILE_PATH = "data/inputs/Shotgun Analysis - Non Duplicates.csv"
SHEET_NAME = ""

SHEET_NAME, extension = os.path.splitext(os.path.basename(INPUT_FILE_PATH))

if extension==".csv":
    df = pd.read_csv(INPUT_FILE_PATH)
elif extension==".xlsx":
    df = pd.read_excel(INPUT_FILE_PATH, sheet_name="Sheet4")

print(f"Total: {df.shape}")
df.drop_duplicates(inplace=True)
print(f"Unique: {df.shape}")

print(SHEET_NAME)

urls = df["Non Duplicates Organisers"].to_list()

counter, df_redirection = 0, []

for url in tqdm(urls, desc=f"Uploading {len(urls)} URLs to {SCRAPER_NAME}"):
    secure_url = url.replace("http://", "https://")

    try:
        response = requests.get(secure_url, allow_redirects=True)
        
        if response.url != secure_url:
            counter += 1
            data = {
                "actual_url": secure_url,
                "redirected_url": response.url
            }
            df_redirection.append(data)
            print(f"The URL '{secure_url}' redirects to '{response.url}'")
    except requests.RequestException as e:
        print(f"An error occurred: {secure_url} | {e}")

df_redirection = pd.DataFrame(df_redirection)
print(df_redirection)

df_redirection.to_excel("data/redirection.xlsx", index=False)