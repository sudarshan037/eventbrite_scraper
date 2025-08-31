from src import utils
import aiohttp

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

async def process(record, page):
    """
    record: whatever is present in cosmos db for that record [mandatory "url"]
    page: playwright page object used for data extraction
    """
    try:
        # get organiser_id
        organiser_id_element = await page.query_selector("//a[contains(@class, 'OrganizerLink-module__OrganizerLink')]")
        organiser_id = await organiser_id_element.get_attribute("href") if organiser_id_element else ""
        organiser_id = organiser_id.split("-")[-1]


        # pass organiser_id to fetch event_details
        event_details = await fetch_event_details(organiser_id)
        follow_status = event_details.get("follow_status", {})

        # TODO: pass organiser_id to fetch price details
        # https://www.eventbrite.com/api/v3/organizers/61124586823/events/?expand=ticket_availability&status=live&only_public=true
        
        record['event_name'] = await utils.get_text(page, "//h1[contains(@class, 'event-title')]")
        record['date'] = await utils.get_text(page, "//time[contains(@class, 'start-date')]")
        record['price'] = await utils.get_text(page, "//div[@class='conversion-bar__panel-info']")
        record['location'] = await utils.get_text(page, "//div[contains(@class, 'location-info__address')]")
        record['organiser_name'] = await utils.get_text(page, "//a[contains(@class, 'OrganizerLink-module__OrganizerLink')]")
        record['followers'] = follow_status.get("num_followers", 0)
    except Exception as e:
        print(f"Error Fetching details for url -> {record['url']}: {e}")
    return record