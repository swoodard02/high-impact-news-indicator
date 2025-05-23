import feedparser
import pytz
from datetime import datetime, timedelta
import os
import requests
import json
import time

FEED_URL = "https://www.myfxbook.com/rss/forex-economic-calendar-events"
POSTED_EVENTS_FILE = "posted_events.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

EASTERN_TZ = pytz.timezone("US/Eastern")

def load_posted_events():
    if os.path.exists(POSTED_EVENTS_FILE):
        with open(POSTED_EVENTS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_posted_events(posted):
    with open(POSTED_EVENTS_FILE, "w") as f:
        json.dump(list(posted), f)

def is_within_next_1440_minutes(event_time_str):
    try:
        event_time_str = event_time_str.replace(" GMT", "")
        event_time = datetime.strptime(event_time_str, '%a, %d %b %Y %H:%M')
        event_time = pytz.UTC.localize(event_time)
        now = datetime.now(pytz.UTC)
        return timedelta(0) <= (event_time - now) <= timedelta(minutes=1440)
    except Exception as e:
        print(f"Time parsing error: {e}")
        return False

def get_impact_from_description(description):
    """Search for impact class in the HTML from description"""
    if "sprite-high-impact" in description:
        return "High Impact"
    elif "sprite-medium-impact" in description:
        return "Medium Impact"
    elif "sprite-low-impact" in description:
        return "Low Impact"
    return "Unknown"

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

    for entry in feed.entries:
        title = entry.title
        pub_date = entry.published
        description = entry.get("description", "")

        impact = get_impact_from_description(description)

        print(f"\nEvent: {title}")
        print(f"Impact: {impact}")
        print(f"Description snippet: {description[:80]}...")

        try:
            event_time_utc = datetime.strptime(pub_date.replace(" GMT", ""), '%a, %d %b %Y %H:%M')
            event_time_utc = pytz.UTC.localize(event_time_utc)
            event_time_et = event_time_utc.astimezone(EASTERN_TZ)
            event_time_str = event_time_et.strftime("%m/%d/%Y %H:%M ET")
        except Exception as e:
            print(f"Error parsing date for event '{title}': {e}")
            event_time_str = pub_date

        if title in posted_events:
            print(f"Already posted: {title}")
            continue

        if is_within_next_1440_minutes(pub_date):
            # Use emoji
            if impact == "High Impact":
                emoji = "🔴"
            elif impact == "Medium Impact":
                emoji = "🟠"
            elif impact == "Low Impact":
                emoji = "⚪"
            else:
                emoji = "⚪"

            message = f"{emoji} <b>{title}</b> at {event_time_str}"
            print(f"Posting event: {message}")

            if send_telegram_message(message):
                posted_events.add(title)
                time.sleep(1.5)  # Avoid hitting rate limits

    save_posted_events(posted_events)

if __name__ == "__main__":
    fetch_and_post_events()



