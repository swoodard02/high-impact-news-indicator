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

EASTERN_TZ = pytz.timezone("US/Eastern")

def load_posted_events():
    if os.path.exists(POSTED_EVENTS_FILE):
        with open(POSTED_EVENTS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_posted_events(posted):
    with open(POSTED_EVENTS_FILE, "w") as f:
        json.dump(list(posted), f)

def is_within_next_60_minutes(event_time_str):
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

def get_impact_from_tags(tags):
    for tag in tags:
        term = tag.get('term', '') if isinstance(tag, dict) else str(tag)
        if 'sprite-high-impact' in term:
            return "High Impact"
        if 'sprite-medium-impact' in term:
            return "Medium Impact"
    return "Low Impact"

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
        tags = entry.get('tags', [])

        impact = get_impact_from_tags(tags)

        # Parse event time and convert to Eastern
        try:
            event_time_utc = datetime.strptime(pub_date.replace(" GMT", ""), '%a, %d %b %Y %H:%M')
            event_time_utc = pytz.UTC.localize(event_time_utc)
            event_time_et = event_time_utc.astimezone(EASTERN_TZ)
            event_time_str = event_time_et.strftime("%m/%d/%Y %H:%M ET")
        except Exception as e:
            print(f"Error parsing date for event '{title}': {e}")
            event_time_str = pub_date

        # Use emojis for impact instead of text color
        impact_emoji = ""
        if impact == "High Impact":
            impact_emoji = "🔴"
        elif impact == "Medium Impact":
            impact_emoji = "🟠"
        else:
            impact_emoji = "⚪"

        message = f"{impact_emoji} <b>{title}</b> at {event_time_str}"

        if is_within_next_60_minutes(pub_date) and title not in posted_events:
            print(f"Posting event: {message}")
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


