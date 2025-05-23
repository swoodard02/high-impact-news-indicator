import feedparser
import pytz
from datetime import datetime
import os
import json
import requests

FEED_URL = "https://trumpstruth.org/feed"
POSTED_FILE = "posted_truths.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID= "@tsvipform"
#TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID2")

EASTERN_TZ = pytz.timezone("US/Eastern")

def load_posted_links():
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_posted_links(posted):
    with open(POSTED_FILE, "w") as f:
        json.dump(list(posted), f)

def convert_to_et(published):
    dt = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z")
    dt_et = dt.astimezone(EASTERN_TZ)
    return dt_et.strftime("%Y-%m-%d %I:%M %p ET")

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
    posted = load_posted_links()
    new_posts = []

    print(f"Fetched {len(feed.entries)} entries.")

    for entry in feed.entries:
        title = entry.title.strip()
        link = entry.link
        published = entry.published

        if title == "[No Title]":
            continue

        if link in posted:
            print(f"Skipping already posted: {title}")
            continue

        time_et = convert_to_et(published)
        message = f"🧑‍🦱 <b>{title}</b>\n🕒 {time_et}\n🔗 {link}"
        new_posts.append((message, link))

    for message, link in new_posts:
        if send_telegram_message(message):
            posted.add(link)

    if new_posts:
        save_posted_links(posted)
    else:
        print("No new posts to send.")

if __name__ == "__main__":
    fetch_and_post_truths()
    print(f"Using chat ID: {TELEGRAM_CHAT_ID}")

