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
POST_WINDOW = timedelta(minutes=5)

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
    now_utc = datetime.now(pytz.UTC)

    print(f"Fetched {len(feed.entries)} entries.")

    updated_truths = {}

    for entry in feed.entries:
        # Safely extract and clean title
        raw_title = entry.get("title", "").strip()
        if raw_title.startswith("<![CDATA[") and raw_title.endswith("]]>"):
            title = raw_title[9:-3].strip()
        else:
            title = raw_title

        # Skip if title is empty or a placeholder
        if "[No Title]" in title or title == "":
            print(f"Skipping entry with no valid title: {title}")
            continue

        # Parse publish date
        published = entry.get("published", "")
        try:
            dt_utc = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z")
        except Exception as e:
            print(f"Failed to parse date for '{title}': {e}")
            continue

        # Check if post is recent (within last 5 minutes)
        if now_utc - dt_utc > POST_WINDOW:
            continue

        # Check if already posted today
        posted_time_str = posted_truths.get(title)
        if posted_time_str:
            posted_dt = datetime.fromisoformat(posted_time_str)
            if posted_dt.date() == now_utc.date():
                print(f"Already posted today: {title}")
                continue

        # Format time string (Eastern Time)
        dt_et = dt_utc.astimezone(EASTERN_TZ)
        time_str = dt_et.strftime("%I:%M %p ET").lstrip("0")

        # Send to Telegram
        message = f"🧑‍🦱 <b>{title}</b>\n{time_str}"
        print(f"Posting: {message}")
        if send_telegram_message(message):
            updated_truths[title] = now_utc.isoformat()

    # Update log
    posted_truths.update(updated_truths)
    save_posted_truths(posted_truths)

if __name__ == "__main__":
    fetch_and_post_truths()
