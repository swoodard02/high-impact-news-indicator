import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import requests

# --- CONFIGURATION ---
URL = "https://www.myfxbook.com/rss/forex-economic-calendar-events"
IMPACT_KEYWORDS = [
    'span class="sprite sprite-common sprite-high-impact',
    'span class="sprite sprite-common sprite-medium-impact'
]
TELEGRAM_BOT_TOKEN = 'your_bot_token_here'
TELEGRAM_CHAT_ID = '@your_channel_username_or_chat_id'  # e.g., @myfxalerts or -1001234567890

def is_within_30_minutes(pub_date_str):
    pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
    now = datetime.now(pytz.utc)
    return now <= pub_date <= now + timedelta(minutes=30)

def fetch_and_filter_events():
    feed = feedparser.parse(URL)
    filtered_events = []

    for entry in feed.entries:
        description = entry.get("description", "")
        pub_date = entry.get("published", "")

        if any(keyword in description for keyword in IMPACT_KEYWORDS):
            if is_within_30_minutes(pub_date):
                soup = BeautifulSoup(description, "html.parser")
                text_description = soup.get_text()
                filtered_events.append({
                    "title": entry.title,
                    "time": pub_date,
                    "description": text_description.strip()
                })

    return filtered_events

def post_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)
    if not response.ok:
        print(f"Failed to post to Telegram: {response.text}")

if __name__ == "__main__":
    events = fetch_and_filter_events()
    if events:
        for event in events:
            message = (
                f"<b>{event['title']}</b>\n"
                f"<i>{event['time']}</i>\n"
                f"{event['description']}"
            )
            post_to_telegram(message)
    else:
        print("No high or medium impact events in the next 30 minutes.")
