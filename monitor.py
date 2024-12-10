import requests
from bs4 import BeautifulSoup
import telegram
import os
import asyncio
from datetime import datetime

async def send_message(bot, chat_id, message):
    """Helper function to send messages"""
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode='HTML'
    )

async def check_announcements():
    """Check for new delisting announcements"""
    try:
        # Get credentials
        bot_token = os.environ['TELEGRAM_BOT_TOKEN']
        chat_id = os.environ['TELEGRAM_CHAT_ID']
        bot = telegram.Bot(token=bot_token)

        # Send starting message
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await send_message(bot, chat_id, f"🔄 Starting check at {current_time}")

        # Check Binance announcements
        url = "https://www.binance.com/en/support/announcement/delisting"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        announcements = soup.select('.announcement-item')
        found_delisting = False
        
        for announcement in announcements:
            title = announcement.select_one('.title').text.strip()
            link = announcement.select_one('a')['href']
            
            if 'delist' in title.lower():
                found_delisting = True
                message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
                await send_message(bot, chat_id, message)
        
        # Send completion message
        status = "Found delisting announcements" if found_delisting else "No new delisting announcements"
        await send_message(bot, chat_id, f"✅ Check completed: {status}")
                
    except Exception as e:
        if 'bot' in locals() and 'chat_id' in locals():
            await send_message(bot, chat_id, f"⚠️ Error: {str(e)}")
        raise e

async def main():
    await check_announcements()

if __name__ == "__main__":
    asyncio.run(main())
