import os
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from dotenv import load_dotenv
load_dotenv()


# Load environment variables from a .env file (optional for local development)
load_dotenv()

URL = "https://www.topstep.tv/topstepvip/"

# Custom headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://google.com",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Environment variables for Telegram bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "@tsvipform"

def check_site_and_notify():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials are missing.")
        return

    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # You can refine this logic to detect specific changes or content
        message = "📢 VIP Form page is live and accessible."
        import asyncio
	bot = Bot(token=TELEGRAM_BOT_TOKEN)
	asyncio.run(bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message))

        print("Notification sent.")

    except requests.exceptions.RequestException as e:
        print(f"Error checking the site: {e}")

if __name__ == "__main__":
    check_site_and_notify()

