import feedparser
import pytz
from datetime import datetime, timedelta
import os
import requests
import json
import re

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
    if not response.ok:
        print(f"Failed to send message: {response.text}")
    return response.ok

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def fetch_and_post_truths():
    feed = feedparser.parse(FEED_URL)
    posted_truths = load_posted_truths()
    now_utc = datetime.now(pytz.UTC)

    print(f"Fetched {len(feed.entries)} entries.")
    print(f"Current UTC time: {now_utc.isoformat()}")

    updated_truths = {}

    for entry in feed.entries:
        raw_title = entry.get("title", "").strip()
        if raw_title.startswith("<![CDATA[") and raw_title.endswith("]]>"):
            title = raw_title[9:-3].strip()
        else:
            title = raw_title

        # Handle [No Title] entries by using description or link as fallback
        if "[No Title]" in title or title == "":
            description = entry.get("description", "").strip()
            if description.startswith("<![CDATA[") and description.endswith("]]>"):
                description = description[9:-3].strip()
            fallback_text = clean_html(description)
            if not fallback_text:
                fallback_text = entry.get("link", "No content available")
            title = f"(No Title) {fallback_text}"

        published = entry.get("published", "")
        print(f"\nProcessing entry: '{title}' Published: '{published}'")

        try:
            dt_utc = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z")
        except Exception as e:
            print(f"Failed to parse date for '{title}': {e}")
            continue

        age = now_utc - dt_utc
        print(f"Entry age (seconds): {age.total_seconds()}")

        if age > POST_WINDOW:
            print("Skipped: older than 5 minutes")
            continue

        posted_time_str = posted_truths.get(title)
        if posted_time_str:
            posted_dt = datetime.fromisoformat(posted_time_str)
            if posted_dt.date() == now_utc.date():
                print("Skipped: already posted today")
                continue

        dt_et = dt_utc.astimezone(EASTERN_TZ)
        time_str = dt_et.strftime("%I:%M %p ET").lstrip("0")

        message = f"🧑‍🦱 <b>{title}</b>\n{time_str}"
        print(f"Posting message:\n{message}")
        if send_telegram_message(message):
            updated_truths[title] = now_utc.isoformat()

    # Update log
    posted_truths.update(updated_truths)
    save_posted_truths(posted_truths)

if __name__ == "__main__":
    # Uncomment this block to send a manual test message to Telegram:
    # print("Sending manual test message to Telegram...")
    # send_telegram_message("Test message from fetch_truth_social.py script")
    
    fetch_and_post_truths()


