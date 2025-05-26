import feedparser
import pytz
from datetime import datetime
import os
import requests
import json
import re

FEED_URL = "https://trumpstruth.org/feed"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "@tsvipform"

EASTERN_TZ = pytz.timezone("US/Eastern")
POSTED_LOG = "posted_truths.json"

def load_posted_data():
    if os.path.exists(POSTED_LOG):
        with open(POSTED_LOG, "r") as f:
            return json.load(f)
    return {"last_post_time": None}

def save_posted_data(data):
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

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def fetch_and_post_truths():
    feed = feedparser.parse(FEED_URL)
    posted_data = load_posted_data()
    last_post_time_str = posted_data.get("last_post_time")
    last_post_time = datetime.fromisoformat(last_post_time_str) if last_post_time_str else None

    print(f"Fetched {len(feed.entries)} entries.")
    print(f"Last posted time: {last_post_time_str}")

    new_entries = []

    for entry in feed.entries:
        raw_title = entry.get("title", "").strip()
        if raw_title.startswith("<![CDATA[") and raw_title.endswith("]]>"):
            title = raw_title[9:-3].strip()
        else:
            title = raw_title

        if "[No Title]" in title or title == "":
            description = entry.get("description", "").strip()
            if description.startswith("<![CDATA[") and description.endswith("]]>"):
                description = description[9:-3].strip()
            fallback_text = clean_html(description)
            if not fallback_text:
                fallback_text = entry.get("link", "No content available")
            title = f"(No Title) {fallback_text}"

        published = entry.get("published", "")
        try:
            dt_utc = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z")
        except Exception as e:
            print(f"Failed to parse date for '{title}': {e}")
            continue

        if last_post_time and dt_utc <= last_post_time:
            print(f"Stopping at previously posted item: {title}")
            break

        new_entries.append((dt_utc, title))

    # Reverse to send oldest first
    new_entries.reverse()

    latest_time_posted = last_post_time

    for dt_utc, title in new_entries:
        dt_et = dt_utc.astimezone(EASTERN_TZ)
        time_str = dt_et.strftime("%I:%M %p ET").lstrip("0")

        message = f"🧑‍🦱 <b>{title}</b>\n{time_str}"
        print(f"Posting:\n{message}")
        if send_telegram_message(message):
            if latest_time_posted is None or dt_utc > latest_time_posted:
                latest_time_posted = dt_utc

    # Update last post time
    if latest_time_posted:
        posted_data["last_post_time"] = latest_time_posted.isoformat()
        save_posted_data(posted_data)

if __name__ == "__main__":
    fetch_and_post_truths()

