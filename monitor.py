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

        # Send debug start message
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await send_message(bot, chat_id, f"🔍 Debug: Starting check at {current_time}")

        # Binance delisting announcement URL
        url = "https://www.binance.com/en/support/announcement/delisting?c=161&navId=161"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple possible selectors for announcements
        announcements = (
            soup.select('.css-1wr4jig') or
            soup.select('.announcement-item') or
            soup.select('div[class*="announcement"]') or
            soup.select('a[href*="/support/announcement"]')
        )
        
        # Debug: Print number of announcements found
        await send_message(bot, chat_id, f"Debug: Found {len(announcements)} total announcements")
        
        found_delisting = False
        
        for announcement in announcements:
            # Get title and link
            title_element = announcement.select_one('[class*="title"]') or announcement
            title = title_element.get_text().strip()
            
            # Debug: Print each title found
            await send_message(bot, chat_id, f"Debug: Found title: {title}")
            
            # Only process if it's a specific delisting announcement
            if title.startswith('Binance Will Delist'):
                link_element = announcement if announcement.name == 'a' else announcement.find_parent('a')
                link = link_element.get('href', '') if link_element else ''
                
                if not link.startswith('http'):
                    link = 'https://www.binance.com' + link

                message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
                await send_message(bot, chat_id, message)
                found_delisting = True
        
        # Send completion message
        await send_message(bot, chat_id, f"Debug: Check completed. Found delisting: {found_delisting}")
                
    except Exception as e:
        error_message = f"⚠️ Error checking announcements: {str(e)}"
        if 'bot' in locals() and 'chat_id' in locals():
            await send_message(bot, chat_id, error_message)
        print(error_message)
        raise e

async def main():
    await check_announcements()

if __name__ == "__main__":
    asyncio.run(main())
