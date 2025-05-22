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

HIGH_IMPACT_KEYWORDS = ['high-impact']
MEDIUM_IMPACT_KEYWORDS = ['medium-impact']

def load_posted_events():
    if os.path.exists(POSTED_EVENTS_FILE):
        with open(POSTED_EVENTS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_posted_events(posted):
    with open(POSTED_EVENTS_FILE, "w") as f:
        json.dump(list(posted), f)

def parse_pubdate(pub_date_str):
    try:
        # Remove ' GMT' suffix if present
        pub_date_str = pub_date_str.replace(" GMT", "")
        # Parse datetime without seconds
        dt = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M')
        # Localize as UTC
        return pytz.UTC.localize(dt)
    except Exception as e:
        print(f"Time parsing error: {e}")
        return None

def format_datetime_et(dt):
    if dt is None:
        return ("Unknown Date", "Unknown Time")
    eastern = pytz.timezone("US/Eastern")
    dt_et = dt.astimezone(eastern)
    date_str = dt_et.strftime("%m/%d/%Y")
    time_str = dt_et.strftime("%H:%M")
    return date_str, time_str

def is_within_next_60_minutes(event_dt):
    if event_dt is None:
        return False
    now = datetime.now(pytz.UTC)
    delta = event_dt - now
    return timedelta(0) <= delta <= timedelta(minutes=60)

def determine_impact(title):
    title_lower = title.lower()
    for kw in HIGH_IMPACT_KEYWORDS:
        if kw in title_lower:
            return 'High Impact'
    for kw in MEDIUM_IMPACT_KEYWORDS:
        if kw in title_lower:
            return 'Medium Impact'
    return None

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram token or chat ID not set in environment variables.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload)
        print(f"Telegram response: {response.status_code} - {response.text}")
        return response.ok
    except Exception as e:
        print(f"Failed to send telegram message: {e}")
        return False

def fetch_and_post_events():
    feed = feedparser.parse(FEED_URL)
    posted_events = load_posted_events()

    print(f"Fetched {len(feed.entries)} entries from RSS feed.\n")

    for entry in feed.entries:
        title = entry.title
        pub_date_raw = entry.published
        event_time = parse_pubdate(pub_date_raw)

        impact = determine_impact(title)
        icon = ''
        if impact == 'High Impact':
            icon = '🔴'
        elif impact == 'Medium Impact':
            icon = '🟠'

        date_str, time_str = format_datetime_et(event_time)

        # One-line display with icon, title, and datetime in ET
        output_line = f"{icon} {title} at {date_str} {time_str} ET"
        print(output_line)

        event_key = f"{title}::{date_str} {time_str}"

        if is_within_next_60_minutes(event_time) and event_key not in posted_events:
            # Telegram message same as output line
            message = output_line
            success = send_telegram_message(message)
            if success:
                posted_events.add(event_key)

    save_posted_events(posted_events)

def send_test_message():
    test_message = "<b>✅ Test Alert:</b> This is a test message from your bot."
    success = send_telegram_message(test_message)
    print("Test message sent!" if success else "Failed to send test message.")

if __name__ == "__main__":
    #send_test_message()
    fetch_and_post_events()



