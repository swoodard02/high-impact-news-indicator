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

HIGH_IMPACT_KEYWORDS = ['high impact', 'important', 'critical', 'major']
MEDIUM_IMPACT_KEYWORDS = ['medium impact', 'moderate', 'watch']

def load_posted_events():
    if os.path.exists(POSTED_EVENTS_FILE):
        with open(POSTED_EVENTS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_posted_events(posted):
    with open(POSTED_EVENTS_FILE, "w") as f:
        json.dump(list(posted), f)

def parse_pubdate(pubdate_str):
    """
    Try multiple formats to parse the event time string.
    Returns a datetime object in UTC or None if parsing fails.
    """
    date_formats = [
        '%a, %d %b %Y %H:%M:%S %Z',  # Thu, 22 May 2025 00:00:00 GMT
        '%a, %d %b %Y %H:%M %Z',     # Thu, 22 May 2025 00:00 GMT
        '%a, %d %b %Y %H:%M:%S',     # Without timezone
        '%a, %d %b %Y %H:%M',        # Without seconds/timezone
    ]

    for fmt in date_formats:
        try:
            dt = datetime.strptime(pubdate_str, fmt)
            # If timezone naive, assume UTC
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            return dt.astimezone(pytz.UTC)
        except Exception:
            continue
    print(f"Time parsing error: time data '{pubdate_str}' does not match expected formats")
    return None

def is_within_next_60_minutes(event_time):
    """
    Check if the event_time is within the next 60 minutes from now (UTC).
    """
    if not event_time:
        return False
    now = datetime.now(pytz.UTC)
    delta = event_time - now
    return timedelta(0) <= delta <= timedelta(minutes=60)

def determine_impact(title):
    """
    Determine impact level from the title string.
    """
    title_lower = title.lower()
    for kw in HIGH_IMPACT_KEYWORDS:
        if kw in title_lower:
            return 'High Impact'
    for kw in MEDIUM_IMPACT_KEYWORDS:
        if kw in title_lower:
            return 'Medium Impact'
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

    print(f"Fetched {len(feed.entries)} entries from RSS feed.\n")

    for entry in feed.entries:
        title = entry.title
        pub_date_raw = entry.published
        event_time = parse_pubdate(pub_date_raw)
        pub_date_formatted = event_time.strftime('%Y-%m-%d %H:%M:%S') if event_time else pub_date_raw

        impact = determine_impact(title)
        impact_text = f" | Impact: {impact}" if impact else ""

        print(f"Title: {title} | Published: {pub_date_formatted}{impact_text}")

        if is_within_next_60_minutes(event_time):
            print(f"⏰ Event within 60 minutes: {title}")

        # Use a unique event key: could be title+pubdate to prevent duplicates
        event_key = f"{title}::{pub_date_formatted}"

        if is_within_next_60_minutes(event_time) and event_key not in posted_events:
            message = f"<b>{title}</b>\nPublished: {pub_date_formatted}{impact_text}"
            success = send_telegram_message(message)
            if success:
                posted_events.add(event_key)

    save_posted_events(posted_events)

def send_test_message():
    test_message = "<b>✅ Test Alert:</b> This is a test message from your bot."
    success = send_telegram_message(test_message)
    print("Test message sent!" if success else "Failed to send test message.")

if __name__ == "__main__":
    # send_test_message()
    fetch_and_post_events()



