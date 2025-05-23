import feedparser
import pytz
from datetime import datetime
import os
import requests
import json

FEED_URL = "https://trumpstruth.org/feed"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "@tsvipform"

EASTERN_TZ = pytz.timezone("US/Eastern")
POSTED_LOG = "posted_truths.json"

def load_posted_truths():
    if os.path.exists(POSTED_LOG):
        with open(POSTED_LOG, "r") as f:
            return json.load(f)
    return {}

def save_posted_truths(data):
    with open(POSTED_LOG, "w") as f:
        json.dump(data, f)

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

def fetch_and_post_truths():
    feed = feedparser.parse(FEED_URL)
    posted_truths = load_posted_truths()
    now = datetime.now(pytz.UTC).astimezone(EASTERN_TZ)  # Use Eastern time for daily tracking

    print(f"Fetched {len(feed.entries)} entries.")

    updated_truths = {}

    for entry in feed.entries:
        title = entry.title.strip()

        if "[No Title]" in title:
            print(f"Skipping entry with no title: {title}")
            continue

        last_posted_str = posted_truths.get(title)
        if last_posted_str:
            try:
                last_posted_time = datetime.fromisoformat(last_posted_str).astimezone(EASTERN_TZ)
                if last_posted_time.date() == now.date():
                    print(f"Skipping entry already posted today: {title}")
                    continue
            except Exception as e:
                print(f"Error parsing last posted time for '{title}': {e}")

        message = f"🧑‍🦱 <b>{title}</b>"
        print(f"Posting: {message}")
        if send_telegram_message(message):
            updated_truths[title] = now.isoformat()

    posted_truths.update(updated_truths)
    save_posted_truths(posted_truths)

if __name__ == "__main__":
    fetch_and_post_truths()

