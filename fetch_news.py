import feedparser
import pytz
from datetime import datetime, timedelta
import os
import requests
import json
from bs4 import BeautifulSoup

FEED_URL = "https://www.myfxbook.com/rss/forex-economic-calendar-events"
POSTED_EVENTS_FILE = "posted_events.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

EASTERN_TZ = pytz.timezone("US/Eastern")

# Country slug-to-code mapping
COUNTRY_CODES = {
    "united-states": "US",
    "canada": "CA",
    "united-kingdom": "GB",
    "euro-area": "EU",
    "japan": "JP",
    "australia": "AU",
    "new-zealand": "NZ",
    "china": "CN",
    "germany": "DE",
    "france": "FR",
    "italy": "IT",
    "mexico": "MX",
    "brazil": "BR",
    "russia": "RU",
    "india": "IN",
    "south-korea": "KR",
    "switzerland": "CH",
    "sweden": "SE",
    "norway": "NO",
    "denmark": "DK",
    "hong-kong": "HK",
    "singapore": "SG",
    "paraguay": "PY",
    "peru": "PE",
    "hungary": "HU",
    "poland": "PL",
    "turkey": "TR",
    "nigeria": "NG",
}

# Only allow Medium Impact events from these countries
ALLOWED_MEDIUM_IMPACT_COUNTRIES = {"AU", "NZ", "CA", "US", "CH", "EU", "GB", "JP"}

def load_posted_events():
    if os.path.exists(POSTED_EVENTS_FILE):
        with open(POSTED_EVENTS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_posted_events(posted):
    with open(POSTED_EVENTS_FILE, "w") as f:
        json.dump(list(posted), f)

def is_within_next_30_minutes(event_time_str):
    try:
        event_time_str = event_time_str.replace(" GMT", "")
        event_time = datetime.strptime(event_time_str, '%a, %d %b %Y %H:%M')
        event_time = pytz.UTC.localize(event_time)
        now = datetime.now(pytz.UTC)
        return timedelta(0) <= (event_time - now) <= timedelta(minutes=40)
    except Exception as e:
        print(f"Time parsing error: {e}")
        return False

def get_impact_from_description(description_html):
    soup = BeautifulSoup(description_html, 'html.parser')
    span = soup.find("span", class_="sprite")
    if span and 'sprite-high-impact' in span.get('class', []):
        return "High Impact"
    if span and 'sprite-medium-impact' in span.get('class', []):
        return "Medium Impact"
    return "Low Impact"

def country_code_to_emoji(code):
    if not code or len(code) != 2:
        return ""
    return chr(ord(code[0].upper()) + 127397) + chr(ord(code[1].upper()) + 127397)

def extract_country_and_flag(link):
    try:
        parts = link.strip("/").split("/")
        if "forex-economic-calendar" in parts:
            idx = parts.index("forex-economic-calendar")
            if len(parts) > idx + 1:
                slug = parts[idx + 1].lower()
                country_name = slug.replace("-", " ").title()
                iso_code = COUNTRY_CODES.get(slug)
                flag = country_code_to_emoji(iso_code) if iso_code else ""
                return flag, country_name, iso_code
    except Exception as e:
        print(f"Error extracting country from link '{link}': {e}")
    return "", "Unknown", None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)
    print(f"Telegram response: {response.status_code} - {response.text}")
    return response.ok

def fetch_and_post_events():
    feed = feedparser.parse(FEED_URL)
    posted_events = load_posted_events()

    print(f"Fetched {len(feed.entries)} entries from RSS feed.")

    events_to_post = []

    for entry in feed.entries:
        title = entry.title
        pub_date = entry.published
        description = entry.get('description', '')
        link = entry.link

        impact = get_impact_from_description(description)
        print(f"Event: {title} | Impact: {impact} | Published: {pub_date}")

        if not is_within_next_30_minutes(pub_date):
            print(f"Skipping '{title}' due to time check.")
            continue

        flag, country, iso_code = extract_country_and_flag(link)

        # Impact filtering
        if impact == "Medium Impact" and (iso_code not in ALLOWED_MEDIUM_IMPACT_COUNTRIES):
            print(f"Skipping '{title}' due to medium impact from unlisted country ({country}).")
            continue
        elif impact == "Low Impact":
            print(f"Skipping '{title}' due to low impact.")
            continue

        if title in posted_events:
            print(f"Skipping '{title}' because already posted.")
            continue

        try:
            event_time_utc = datetime.strptime(pub_date.replace(" GMT", ""), '%a, %d %b %Y %H:%M')
            event_time_utc = pytz.UTC.localize(event_time_utc)
            event_time_et = event_time_utc.astimezone(EASTERN_TZ)
            event_time_str = event_time_et.strftime("%H:%M ET")
        except Exception as e:
            print(f"Error parsing date for event '{title}': {e}")
            event_time_str = pub_date

        emoji = "🔴" if impact == "High Impact" else "🟠"
        event_line = f"{emoji}  {flag} <b>{title}</b>  -  {event_time_str}"
        events_to_post.append(event_line)
        posted_events.add(title)

    if events_to_post:
        full_message = "<b>🗓 Upcoming Economic Events (Within 30 Minutes):</b>\n\n" + "\n".join(events_to_post)
        print(f"Posting events:\n{full_message}")
        success = send_telegram_message(full_message)
        if success:
            save_posted_events(posted_events)
    else:
        print("No new events to post.")

if __name__ == "__main__":
    fetch_and_post_events()


