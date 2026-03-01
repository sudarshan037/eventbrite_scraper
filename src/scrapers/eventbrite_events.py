from src import utils
import aiohttp

abbreviation_to_name = {
    # https://en.wikipedia.org/wiki/List_of_states_and_territories_of_the_United_States#States.
    "AK": "Alaska",
    "AL": "Alabama",
    "AR": "Arkansas",
    "AZ": "Arizona",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "IA": "Iowa",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "MA": "Massachusetts",
    "MD": "Maryland",
    "ME": "Maine",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MO": "Missouri",
    "MS": "Mississippi",
    "MT": "Montana",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "NE": "Nebraska",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NV": "Nevada",
    "NY": "New York",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VA": "Virginia",
    "VT": "Vermont",
    "WA": "Washington",
    "WI": "Wisconsin",
    "WV": "West Virginia",
    "WY": "Wyoming",
    # https://en.wikipedia.org/wiki/List_of_states_and_territories_of_the_United_States#Federal_district.
    "DC": "District of Columbia",
    # https://en.wikipedia.org/wiki/List_of_states_and_territories_of_the_United_States#Inhabited_territories.
    "AS": "American Samoa",
    "GU": "Guam GU",
    "MP": "Northern Mariana Islands",
    "PR": "Puerto Rico PR",
    "VI": "U.S. Virgin Islands",
}

async def fetch_event_details(organiser_id):
    url = f"https://www.eventbrite.com/api/v3/organizers/{organiser_id}/?expand.organizer=follow_status"
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                print(f"Failed to fetch organizer data. Status code: {response.status}")
                return None

import json

async def process(record, page):
    """
    Extracts event data directly from the __NEXT_DATA__ JSON blob.
    """
    try:
        # 1. Locate the script tag and get its content
        script_element = await page.query_selector("script#__NEXT_DATA__")
        if not script_element:
            print(f"Could not find JSON data for {record['url']}")
            return record

        raw_json = await script_element.inner_text()
        data = json.loads(raw_json)

        # 2. Navigate the JSON structure (Step-by-step to avoid KeyErrors)
        page_props = data.get("props", {}).get("pageProps", {})
        basic_info = page_props.get("context", {}).get("basicInfo", {})
        venue = basic_info.get("venue", {})
        seo_info = page_props.get("context", {}).get("seo", {})
        offers_schema = seo_info.get("offersSchema", [])

        # 3. Map values to your record
        record['event_name'] = basic_info.get("name", "")
        record['organiser_id'] = basic_info.get("organizer", {}).get("id", "")
        record['organiser_name'] = basic_info.get("organizer", {}).get("name", "")
        
        # Use UTC or Local depending on your preference
        record['date'] = basic_info.get("startDate", {}).get("utc", "")

        # 4. Extract Price from SEO schema
        if offers_schema and len(offers_schema) > 0:
            first_offer = offers_schema[0]
            currency = first_offer.get("priceCurrency", "")
            price = first_offer.get("lowPrice", "")
            
            # Save it to your record
            if price:
                record['price'] = f"{currency} {price}".strip()
            else:
                record['price'] = "Price Not Found"
        
        # 5. Location details
        address_list = venue.get("address", {}).get("localizedMultiLineAddressDisplay", [])
        record['location'] = ", ".join(address_list)
        record['city'] = venue.get("address", {}).get("city", "")
        record['state'] = venue.get("address", {}).get("region", "")

        # 6. Follower Logic (unchanged)
        if record['organiser_id']:
            event_details = await fetch_event_details(record['organiser_id'])
            if event_details:
                record['followers'] = event_details.get("follow_status", {}).get("num_followers", 0)

    except Exception as e:
        print(f"Error parsing JSON for {record.get('url')}: {e}")
        
    return record