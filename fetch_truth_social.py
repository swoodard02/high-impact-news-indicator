import feedparser
import pytz
from datetime import datetime, timedelta
import os
import requests
import json

FEED_URL = "https://trumpstruth.org/feed"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "@tsvipform"

EASTERN_TZ = pytz.timezone("US/Eastern")
POSTED_LOG = "posted_truths.json"
LOOKBACK_WINDOW = timedelta(minutes=5)

def load_posted_titles():
    if os.path.exists(POSTED_LOG):
        with open(POSTED_LOG, "r") as f:
            return json.load(f)
    return {}

def save_posted_titles(data):
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

def fetch_and_post_recent_truths():
    feed = feedparser.parse(FEED_URL)
    posted_titles = load_posted_titles()
    now_utc = datetime.now(pytz.UTC)
    now_et = now_utc.astimezone(EASTERN_TZ)

    print(f"Fetched {len(feed.entries)} entries.")
    updated_titles = {}

    for entry in feed.entries:
        title = entry.title.strip()

        if "[No Title]" in title:
            print(f"Skipping entry with no title: {title}")
            continue

        # Parse published time
        published = entry.get("published", "")
        try:
            published_dt = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z")
        except Exception as e:
            print(f"Skipping due to time parsing error: {e}")
            continue

        # Only allow posts published in the last 5 minutes
        if now_utc - published_dt > LOOKBACK_WINDOW:
            continue

        # Check if already posted
        if title in posted_titles:
            print(f"Skipping already posted: {title}")
            continue

        # Format time string
        post_time_et = published_dt.astimezone(EASTERN_TZ)
        time_str = post_time_et.strftime("%I:%M %p ET")

        message = f"🧑‍🦱 <b>{title}</b>\n{time_str}"
        print(f"Posting: {message}")
        if send_telegram_message(message):
            updated_titles[title] = now_et.isoformat()

    # Save posted titles
    posted_titles.update(updated_titles)
    save_posted_titles(posted_titles)

if __name__ == "__main__":
    fetch_and_post_recent_truths()

