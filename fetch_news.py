import feedparser
import pytz
from datetime import datetime, timedelta
import os
import requests
import json

FEED_URL = "https://www.myfxbook.com/rss/forex-economic-calendar-events"
POSTED_EVENTS_FILE = "posted_events.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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
        # Strip GMT and parse as naive datetime
        event_time_str = event_time_str.replace(" GMT", "")
        event_time = datetime.strptime(event_time_str, '%a, %d %b %Y %H:%M')

        # Assume UTC since the feed says GMT
        event_time = pytz.UTC.localize(event_time)

        now = datetime.now(pytz.UTC)
        return timedelta(0) <= (event_time - now) <= timedelta(minutes=60)
    except Exception as e:
        print(f"Time parsing error: {e}")
        return False

def convert_to_eastern(event_time_str):
    try:
        event_time_str = event_time_str.replace(" GMT", "")
        event_time = datetime.strptime(event_time_str, '%a, %d %b %Y %H:%M')
        event_time_utc = pytz.UTC.localize(event_time)

        eastern = pytz.timezone("US/Eastern")
        event_time_eastern = event_time_utc.astimezone(eastern)

        return event_time_eastern
    except Exception as e:
        print(f"Time conversion error: {e}")
        return None

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

        # Determine impact emoji
        impact = ""
        for tag in entry.get("tags", []):
            term = tag.get("term", "").lower()
            if term == "high-impact":
                impact = "🔴"
                break
            elif term == "medium-impact":
                impact = "🟠"

        # Convert published date to Eastern time
        eastern_dt = convert_to_eastern(pub_date)
        if eastern_dt is None:
            continue
        date_str = eastern_dt.strftime("%m/%d/%Y")
        time_str = eastern_dt.strftime("%H:%M")

        # Compose the message with impact emoji outside bold tags
        message = f"{impact} <b>{title}</b>\n{date_str} {time_str} ET"

        print(f"{impact} {title} at {date_str} {time_str} ET")

        if is_within_next_30_minutes(pub_date) and title not in posted_events:
            success = send_telegram_message(message)
            if success:
                posted_events.add(title)

    save_posted_events(posted_events)

def send_test_message():
    test_message = "<b>✅ Test Alert:</b> This is a test message from your bot."
    success = send_telegram_message(test_message)
    print("Test message sent!" if success else "Failed to send test message.")

if __name__ == "__main__":
    # send_test_message()
    fetch_and_post_events()



