import requests
from bs4 import BeautifulSoup
import telegram
import os
import asyncio
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('binance_monitor.log'),
        logging.StreamHandler()
    ]
)

async def send_message(bot, chat_id, message):
    """Helper function to send messages"""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML'
        )
        logging.info(f"Message sent successfully: {message[:100]}...")
    except Exception as e:
        logging.error(f"Failed to send message: {str(e)}")
        raise

async def check_announcements():
    """Check for new delisting announcements"""
    try:
        # Get credentials
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            raise ValueError("Missing environment variables: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        
        bot = telegram.Bot(token=bot_token)
        
        # Binance delisting announcement URL
        url = "https://www.binance.com/en/support/announcement/delisting?c=161&navId=161"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        
        logging.info(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Log the response for debugging
        logging.debug(f"Response status code: {response.status_code}")
        logging.debug(f"Response content preview: {response.text[:500]}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple possible selectors for announcements
        selectors = [
            '.css-1wr4jig',
            '.announcement-item',
            'div[class*="announcement"]',
            'a[href*="/support/announcement"]',
            # Add new selectors based on current HTML structure
            '.css-1ntn2ef',  # Add more potential class names
            '.css-1vy2xbg'
        ]
        
        announcements = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                logging.info(f"Found {len(found)} announcements with selector: {selector}")
                announcements.extend(found)
                break
        
        if not announcements:
            logging.warning("No announcements found with any selector")
            # Send debugging information to Telegram
            await send_message(
                bot, 
                chat_id, 
                "⚠️ Monitor Status: No announcements found. Please check if the website structure has changed."
            )
            return
        
        found_delisting = False
        
        for announcement in announcements:
            # Get title and link
            title_element = announcement.select_one('[class*="title"]') or announcement
            title = title_element.get_text().strip()
            
            logging.debug(f"Processing announcement: {title}")
            
            # Only process if it's a specific delisting announcement
            if title.lower().startswith('binance will delist'):
                link_element = announcement if announcement.name == 'a' else announcement.find_parent('a')
                link = link_element.get('href', '') if link_element else ''
                
                if not link.startswith('http'):
                    link = 'https://www.binance.com' + link

                message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
                await send_message(bot, chat_id, message)
                found_delisting = True
        
        # Send status message
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "Found delisting announcement" if found_delisting else "No new delisting announcements"
        logging.info(f"Status at {current_time}: {status}")
                
    except requests.exceptions.RequestException as e:
        error_message = f"⚠️ Network error: {str(e)}"
        logging.error(error_message)
        if 'bot' in locals() and 'chat_id' in locals():
            await send_message(bot, chat_id, error_message)
        raise
    except Exception as e:
        error_message = f"⚠️ Error checking announcements: {str(e)}"
        logging.error(error_message)
        if 'bot' in locals() and 'chat_id' in locals():
            await send_message(bot, chat_id, error_message)
        raise

async def main():
    while True:
        try:
            await check_announcements()
            # Wait for 5 minutes before checking again
            await asyncio.sleep(300)
        except Exception as e:
            logging.error(f"Error in main loop: {str(e)}")
            # Wait for 1 minute before retrying after an error
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
