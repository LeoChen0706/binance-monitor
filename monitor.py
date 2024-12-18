import requests
from bs4 import BeautifulSoup
import telegram
import os
import asyncio
from datetime import datetime
import logging
import json

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('binance_monitor.log'),
        logging.StreamHandler()
    ]
)

async def send_message(bot, chat_id, message):
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
    try:
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            raise ValueError("Missing environment variables: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        
        bot = telegram.Bot(token=bot_token)
        
        # Try both API endpoint and web scraping
        found_delisting = False
        
        # 1. Try Binance API endpoint first
        api_url = "https://www.binance.com/bapi/composite/v1/public/cms/article/catalog/list/query"
        api_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        api_payload = {
            "catalogId": "161",
            "pageNo": 1,
            "pageSize": 20,
            "rnd": datetime.now().timestamp()
        }
        
        logging.info("Trying API endpoint...")
        api_response = requests.post(api_url, headers=api_headers, json=api_payload, timeout=30)
        
        if api_response.status_code == 200:
            try:
                data = api_response.json()
                if 'data' in data and 'articles' in data['data']:
                    for article in data['data']['articles']:
                        title = article.get('title', '').strip()
                        if title.lower().startswith('binance will delist'):
                            code = article.get('code', '')
                            link = f"https://www.binance.com/en/support/announcement/{code}"
                            message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
                            await send_message(bot, chat_id, message)
                            found_delisting = True
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse API response: {str(e)}")
        
        # 2. If API fails, try web scraping as backup
        if not found_delisting:
            logging.info("API method didn't find announcements, trying web scraping...")
            url = "https://www.binance.com/en/support/announcement/delisting?c=161&navId=161"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Log the full HTML for debugging
            logging.debug("Full HTML content:")
            logging.debug(response.text)
            
            # Try multiple selectors including new ones
            selectors = [
                'div[class*="css-"]', # Generic CSS module class
                '.announcement-catalog-list a',
                'a[href*="/support/announcement"]',
                'div[class*="list"] a',
                '.css-1vy2xbg',
                '.css-1ntn2ef'
            ]
            
            for selector in selectors:
                announcements = soup.select(selector)
                if announcements:
                    logging.info(f"Found {len(announcements)} items with selector: {selector}")
                    for announcement in announcements:
                        # Try to find title in multiple ways
                        title = None
                        title_element = announcement.select_one('[class*="title"]')
                        if title_element:
                            title = title_element.get_text().strip()
                        else:
                            # Try to find any text that looks like a title
                            text = announcement.get_text().strip()
                            if "binance will delist" in text.lower():
                                title = text
                        
                        if title and title.lower().startswith('binance will delist'):
                            link = announcement.get('href', '')
                            if not link.startswith('http'):
                                link = 'https://www.binance.com' + link
                            
                            message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
                            await send_message(bot, chat_id, message)
                            found_delisting = True
                            break
                    
                    if found_delisting:
                        break
        
        # Send status message
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "✅ Monitor running successfully"
        if not found_delisting:
            status += " (No new delisting announcements)"
        logging.info(f"Status at {current_time}: {status}")
        await send_message(bot, chat_id, status)
                
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
