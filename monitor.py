import requests
from bs4 import BeautifulSoup
import telegram
import os
import asyncio
import logging
from datetime import datetime

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
        
        url = "https://www.binance.com/en/support/announcement/delisting?c=161&navId=161"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.binance.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        
        logging.info(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Log the HTML for debugging
        with open('last_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try different selectors to find announcements
        selectors = [
            'div[class*="css-"]',  # Generic CSS module class
            'a[href*="/support/announcement"]',
            'div[class*="list"] a',
            'div[class*="title"]',
            'h3[class*="css-"]',
            'div[class*="content"]'
        ]
        
        found_delisting = False
        seen_titles = set()
        
        for selector in selectors:
            elements = soup.select(selector)
            logging.info(f"Found {len(elements)} elements with selector: {selector}")
            
            for element in elements:
                # Try to find title in multiple ways
                title = element.get_text().strip()
                
                # Skip if already processed this title
                if title in seen_titles:
                    continue
                    
                seen_titles.add(title)
                
                if title.startswith('Binance Will Delist'):
                    # Try to find the link
                    link_element = element if element.name == 'a' else element.find_parent('a')
                    link = link_element.get('href', '') if link_element else ''
                    
                    if not link.startswith('http'):
                        link = 'https://www.binance.com' + link
                        
                    message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
                    await send_message(bot, chat_id, message)
                    found_delisting = True
                    logging.info(f"Found delisting announcement: {title}")
        
        if not found_delisting:
            logging.info("No new delisting announcements found")
            
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
