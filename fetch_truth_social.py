import feedparser
import pytz
from datetime import datetime
import os
import requests

FEED_URL = "https://trumpstruth.org/feed"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "@tsvipform"

EASTERN_TZ = pytz.timezone("US/Eastern")
POSTED_LOG = "posted_truth_titles.txt"


def load_posted_titles():
    if os.path.exists(POSTED_LOG):
        with open(POSTED_LOG, "r") as f:
            return set(line.strip() for line in f)
    return set()


def save_posted_titles(titles):
    with open(POSTED_LOG, "w") as f:
        f.write("\n".join(titles))


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
    posted_titles = load_posted_titles()

    print(f"Fetched {len(feed.entries)} entries.")

    new_titles = set()
    for entry in feed.entries:
        title = entry.title.strip()

        if title == "[No Title]":
            print(f"Skipping entry with no title.")
            continue

        if title in posted_titles:
            continue

        # Parse and convert publish time
        published = entry.get("published", "")
        try:
            dt_utc = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z")
            dt_et = dt_utc.astimezone(EASTERN_TZ)
            time_str = dt_et.strftime("%Y-%m-%d %I:%M %p ET")
        except Exception as e:
            print(f"Error parsing time: {e}")
            time_str = ""

        message = f"🧑‍🦱 <b>{title}</b>\n{time_str}"
        print(f"Posting: {message}")
        if send_telegram_message(message):
            new_titles.add(title)

    if new_titles:
        posted_titles.update(new_titles)
        save_posted_titles(posted_titles)
    else:
        print("No new entries to post.")


if __name__ == "__main__":
    fetch_and_post_truths()

