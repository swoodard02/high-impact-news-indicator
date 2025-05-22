import feedparser
from datetime import datetime, timezone
import pytz
import requests
from bs4 import BeautifulSoup
import os

def parse_pub_date(pub_date_str):
    try:
        # Try parsing with seconds
        return datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        # Fallback to parsing without seconds
        return datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M %z")

def is_within_30_minutes(pub_date):
    now = datetime.now(timezone.utc)
    delta = abs((now - pub_date).total_seconds())
    return delta <= 30 * 60  # 30 minutes

def fetch_and_filter_events():
    url = 'https://www.forexfactory.com/ffcal_week_this.xml'
    feed = feedparser.parse(url)

    filtered_events = []

    for entry in feed.entries:
        # Check if event is marked as high impact
        if '<span class="sprite sprite-common sprite-high-impact">' in entry.summary:
            pub_date = parse_pub_date(entry.published)
            if is_within_30_minutes(pub_date):
                filtered_events.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.published,
                })

    return filtered_events

def send_telegram_message(token, chat_id, message):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
    }
    response = requests.post(url, data=payload)
    return response.json()

if __name__ == '__main__':
    events = fetch_and_filter_events()
    if events:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        for event in events:
            message = f"<b>{event['title']}</b>\nPublished: {event['published']}\nLink: {event['link']}"
            send_telegram_message(token, chat_id, message)

