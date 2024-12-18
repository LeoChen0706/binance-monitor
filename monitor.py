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
        logging.FileHandler('delisting_monitor.log'),
        logging.StreamHandler()
    ]
)

async def send_telegram(bot, chat_id, message):
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML'
        )
        logging.info(f"Sent message: {message[:100]}...")
    except Exception as e:
        logging.error(f"Failed to send message: {str(e)}")

async def check_delisting():
    try:
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        
        bot = telegram.Bot(token=bot_token)
        
        url = "https://www.binance.com/en/support/announcement/delisting?c=161&navId=161"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save HTML for debugging
        with open('last_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # Try to find any elements that might contain announcements
        selectors = [
            'div[class*="css-"] a',  # Most common pattern for announcement links
            'a[href*="/support/announcement"]',  # Links to announcements
            'h3[class*="css-"]',  # Title elements
            'div[class*="title"]'  # Title containers
        ]
        
        found_elements = []
        for selector in selectors:
            elements = soup.select(selector)
            found_elements.extend(elements)
        
        seen_titles = set()
        found_delisting = False
        
        for element in found_elements:
            title = element.get_text().strip()
            
            if not title or title in seen_titles:
                continue
                
            seen_titles.add(title)
            
            if title.startswith('Binance Will Delist'):
                link_element = element if element.name == 'a' else element.find_parent('a')
                link = link_element.get('href', '') if link_element else ''
                
                if link and not link.startswith('http'):
                    link = 'https://www.binance.com' + link
                
                if link:
                    message = f"🚨 New Delisting Found 🚨\n\n{title}\n\nLink: {link}"
                    await send_telegram(bot, chat_id, message)
                    found_delisting = True
                    logging.info(f"Found delisting: {title}")
        
        if not found_delisting:
            logging.info("No new delisting announcements found")
            
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logging.error(error_msg)
        if 'bot' in locals() and 'chat_id' in locals():
            await send_telegram(bot, chat_id, f"⚠️ {error_msg}")

async def main():
    while True:
        try:
            await check_delisting()
            await asyncio.sleep(300)  # Check every 5 minutes
        except Exception as e:
            logging.error(f"Main loop error: {str(e)}")
            await asyncio.sleep(60)  # Wait 1 minute after error

if __name__ == "__main__":
    asyncio.run(main())
