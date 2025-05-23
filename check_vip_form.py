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

URL = "https://www.topstep.tv/topstepvip/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}


async def notify_telegram(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print("Notification sent.")
    else:
        print("Telegram credentials are missing.")


def check_vip_form():
    try:
        response = requests.get(URL, headers=HEADERS)
        response.raise_for_status()
        print(response.text)  # Useful for debugging

        soup = BeautifulSoup(response.content, "html.parser")
        form = soup.find("form")

        if form:
            message = "VIP form is available!"
            print(message)
            asyncio.run(notify_telegram(message))
        else:
            print("VIP form not found.")
    except Exception as e:
        print(f"Error checking the site: {e}")
        print("No form detected or error occurred.")


if __name__ == "__main__":
    check_vip_form()
