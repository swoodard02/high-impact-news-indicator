import feedparser
from datetime import datetime, timezone, timedelta
import requests
import pytz

FEED_URL = 'https://example.com/rss'  # replace with your actual feed URL

def parse_pub_date(pub_date_str):
    """
    Parse publication date string with flexible handling of formats.
    Example dates:
    - 'Thu, 22 May 2025 00:30:00 +0000'
    - 'Thu, 22 May 2025 00:30 GMT'
    """
    from email.utils import parsedate_to_datetime

    try:
        # Try parsing with email.utils which is robust for RFC 2822 dates
        dt = parsedate_to_datetime(pub_date_str)
        # Ensure timezone-aware in UTC if no tzinfo
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as e:
        print(f"Failed to parse date '{pub_date_str}': {e}")
        return None

def is_within_30_minutes(pub_date):
    if pub_date is None:
        return False
    now = datetime.now(timezone.utc)
    delta = now - pub_date
    return timedelta(0) <= delta <= timedelta(minutes=30)

def fetch_and_filter_events():
    feed = feedparser.parse(FEED_URL)
    recent_events = []
    for entry in feed.entries:
        pub_date = parse_pub_date(entry.published)
        if is_within_30_minutes(pub_date):
            recent_events.append(entry)
    return recent_events

def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    response = requests.post(url, data=data)
    if not response.ok:
        print(f"Failed to send message: {response.text}")

if __name__ == "__main__":
    import os

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    events = fetch_and_filter_events()

    if not events:
        print("No recent events found.")
    else:
        for event in events:
            message = f"*{event.title}*\n{event.link}\nPublished: {event.published}"
            send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)
