import feedparser
import json
import datetime
import requests
import os

def parse_pub_date(pub_date_str):
    from datetime import datetime
    try:
        # Try with seconds
        return datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        # Fallback to no seconds
        return datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M %z")

def is_within_30_minutes(pub_date):
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = abs((now - pub_date).total_seconds())
    return delta <= 30 * 60  # 30 minutes in seconds

def fetch_and_filter_events():
    feed_url = "https://www.myfxbook.com/rss/forex-economic-calendar-events"
    feed = feedparser.parse(feed_url)
    filtered_events = []

    for entry in feed.entries:
        if '<span class="sprite sprite-common sprite-high-impact">' in entry.summary:
            pub_date = parse_pub_date(entry.published)
            if is_within_30_minutes(pub_date):
                filtered_events.append({
                    "title": entry.title,
                    "published": pub_date.isoformat()
                })

    return filtered_events

def send_to_telegram(events):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Telegram token or chat ID not set in environment variables.")
        return

    for event in events:
        message = f"High Impact Event:\n{event['title']}\nTime: {event['published']}"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print(f"Failed to send message: {response.text}")

if __name__ == "__main__":
    events = fetch_and_filter_events()
    if events:
        send_to_telegram(events)
    else:
        print("No high impact events within the last 30 minutes.")
