import requests
from bs4 import BeautifulSoup
from telegram import Bot
import os

# Telegram bot token and chat ID from GitHub secrets or environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID2")

URL = "https://www.topstep.tv/topstepvip/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials are missing.")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="HTML")
        print("✅ Message sent to Telegram.")
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")

def check_vip_form():
    try:
        response = requests.get(URL, headers=HEADERS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Customize this to extract specific content (e.g., headings, forms, divs)
        title = soup.title.string.strip() if soup.title else "VIP Page Checked"

        message = f"🧑‍🦱 <b>{title}</b>\nVIP form page is accessible."
        send_telegram_message(message)

    except requests.exceptions.RequestException as e:
        print(f"Error checking the site: {e}")
        send_telegram_message(f"❌ Failed to access VIP form page.\nError: {e}")

if __name__ == "__main__":
    check_vip_form()
