import requests
import pandas as pd

API_URL = "https://prodapi.greatnonprofits.org/front/api/v1/nonprofits"
state = "MN"
city = "minneapolis"
page = 1

payload = {}
headers = {}

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ESCAPE = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

while True:
    url = f"{API_URL}?all=false&search&zipcode&country&state={state}&city={city}&category&page={page}&size=25"
    filename = "data/greatnonprofits_mn.xlsx"
    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code != 200:
        break
    df = pd.DataFrame(response.json()["results"])
    try:
        existing = pd.read_excel(filename)
        df = pd.concat([existing, df], ignore_index=True)
    except FileNotFoundError:
        pass
    df.to_excel(filename, index=False)
    page += 1

    print(f"{bcolors.OKGREEN}Saved {df.shape} records to {filename}{bcolors.ESCAPE}")
