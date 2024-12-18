import requests
from bs4 import BeautifulSoup
import telegram
import os
import asyncio
from datetime import datetime

async def send_message(bot, chat_id, message):
    """Helper function to send messages"""
    print(f"Sending message: {message}")  # Debug log
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode='HTML'
    )
    print("Message sent successfully")  # Debug log

async def check_announcements():
    """Check for new delisting announcements"""
    try:
        print("Starting announcement check...")  # Debug log
        
        # Get credentials
        bot_token = os.environ['TELEGRAM_BOT_TOKEN']
        chat_id = os.environ['TELEGRAM_CHAT_ID']
        print(f"Got credentials. Chat ID length: {len(str(chat_id))}")  # Debug log
        
        bot = telegram.Bot(token=bot_token)
        print("Bot initialized")  # Debug log

        # Binance delisting announcement URL
        url = "https://www.binance.com/en/support/announcement/delisting?c=161&navId=161"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        print("Fetching Binance page...")  # Debug log
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(f"Got response: {response.status_code}")  # Debug log
        
        soup = BeautifulSoup(response.text, 'html.parser')
        print("Parsed HTML")  # Debug log
        
        # Try multiple possible selectors for announcements
        announcements = (
            soup.select('.css-1wr4jig') or
            soup.select('.announcement-item') or
            soup.select('div[class*="announcement"]') or
            soup.select('a[href*="/support/announcement"]')
        )
        
        print(f"Found {len(announcements)} announcements")  # Debug log
        
        found_delisting = False
        for announcement in announcements:
            # Get title and link
            title_element = announcement.select_one('[class*="title"]') or announcement
            title = title_element.get_text().strip()
            print(f"Found title: {title}")  # Debug log
            
            # Only process if it's a specific delisting announcement
            if title.startswith('Binance Will Delist'):
                print(f"Found delisting announcement: {title}")  # Debug log
                link_element = announcement if announcement.name == 'a' else announcement.find_parent('a')
                link = link_element.get('href', '') if link_element else ''
                
                if not link.startswith('http'):
                    link = 'https://www.binance.com' + link

                message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
                await send_message(bot, chat_id, message)
                found_delisting = True
        
        if not found_delisting:
            print("No delisting announcements found")  # Debug log
                
    except Exception as e:
        print(f"Error occurred: {str(e)}")  # Debug log
        error_message = f"⚠️ Error checking announcements: {str(e)}"
        if 'bot' in locals() and 'chat_id' in locals():
            await send_message(bot, chat_id, error_message)
        raise e

async def main():
    print("Starting main function...")  # Debug log
    await check_announcements()
    print("Finished checking announcements")  # Debug log

if __name__ == "__main__":
    asyncio.run(main())
