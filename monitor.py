import requests
from bs4 import BeautifulSoup
import telegram
import os
import asyncio
from datetime import datetime
import logging

logging.basicConfig(level=logging.DEBUG)

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

        # Binance delisting announcement URL
        url = "https://www.binance.com/en/support/announcement/delisting?c=161&navId=161"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        
        session = requests.Session()
        response = session.get(url, headers=headers)
        response.raise_for_status()
        
        # Save HTML for debugging
        with open('debug.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Updated selectors based on current Binance structure
        announcements = []
        selectors = [
            'div.css-1ntn2ef',  # Current main container class
            'div.css-1vy2xbg',  # Current item container class
            'a[href*="/support/announcement"]',  # Announcement links
            'div[class^="css-"] a'  # Any CSS module styled links
        ]
        
        for selector in selectors:
            found = soup.select(selector)
            if found:
                announcements.extend(found)
                logging.debug(f"Found {len(found)} items with selector: {selector}")
        
        found_delisting = False
        seen_titles = set()
        
        for announcement in announcements:
            # Try different ways to get the title
            title_element = (
                announcement.select_one('div[class^="css-"]') or 
                announcement.select_one('h3[class^="css-"]') or 
                announcement
            )
            
            title = title_element.get_text().strip()
            
            if not title or title in seen_titles:
                continue
                
            seen_titles.add(title)
            
            if title.startswith('Binance Will Delist'):
                # Get the link
                link = announcement.get('href', '')
                if not link and announcement.name != 'a':
                    link_element = announcement.find_parent('a')
                    link = link_element.get('href', '') if link_element else ''
                
                if link and not link.startswith('http'):
                    link = 'https://www.binance.com' + link

                if link:
                    message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
                    await send_message(bot, chat_id, message)
                    found_delisting = True
                    logging.info(f"Found delisting: {title}")
        
        if found_delisting:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await send_message(bot, chat_id, f"⚠️ Please check the delisting announcements carefully!")
                
    except Exception as e:
        error_message = f"⚠️ Error checking announcements: {str(e)}"
        if 'bot' in locals() and 'chat_id' in locals():
            await send_message(bot, chat_id, error_message)
        logging.error(error_message)
        raise e

async def main():
    while True:
        try:
            await check_announcements()
            # Check every 5 minutes
            await asyncio.sleep(300)
        except Exception as e:
            logging.error(f"Error in main loop: {str(e)}")
            # Wait 1 minute before retrying
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
