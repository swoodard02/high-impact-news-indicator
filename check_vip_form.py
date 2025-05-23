import requests
from bs4 import BeautifulSoup
from telegram import Bot
import os
import json
from datetime import datetime
import pytz

# Configuration
URL = "https://www.topstep.tv/topstepvip/"
TARGET_TEXT = "THE VIP CHECK-IN FORM IS CURRENTLY CLOSED."
STATUS_FILE = "status.json"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Eastern Time Zone
eastern = pytz.timezone("US/Eastern")

def is_vip_form_closed():
    try:
        response = requests.get(URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return TARGET_TEXT in soup.get_text().upper()
    except Exception as e:
        print(f"Error checking the site: {e}")
        return None

def get_daypart():
    now_et = datetime.now(eastern)
    hour = now_et.hour
    return "morning" if 6 <= hour < 18 else "night"

def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    return {"last_status": "closed", "last_alert_daypart": None}

def save_status(status_data):
    with open(STATUS_FILE, "w") as f:
        json.dump(status_data, f)

def send_telegram_message(message):
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=message)

def main():
    current_closed = is_vip_form_closed()
    if current_closed is None:
        return

    current_status = "closed" if current_closed else "open"
    status_data = load_status()
    current_daypart = get_daypart()

    should_alert = (
        current_status == "open"
        and status_data["last_status"] != "open"
        and status_data.get("last_alert_daypart") != current_daypart
    )

    if should_alert:
        send_telegram_message(
            "🚨 The Topstep VIP Form is LIVE! Go check it out: https://www.topstep.tv/topstepvip/"
        )
        status_data["last_alert_daypart"] = current_daypart

    status_data["last_status"] = current_status
    save_status(status_data)

if __name__ == "__main__":
    main()
