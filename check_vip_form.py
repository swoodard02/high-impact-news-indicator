import os
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "@tsvipform"
CHECK_URL = "https://www.topstep.tv/topstepvip/"

def check_vip_form():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(CHECK_URL, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        form = soup.find("form")

        if form:
            print("VIP form is available.")
            return True
        else:
            print("VIP form not found.")
            return False

    except Exception as e:
        print(f"Error checking the site: {e}")
        return False

async def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials are missing.")
        return
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def main():
    if check_vip_form():
        message = "✅ VIP Form is available!"
        asyncio.run(send_telegram_message(message))
        print("Notification sent.")
    else:
        print("No form detected or error occurred.")

if __name__ == "__main__":
    main()

