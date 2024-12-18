import requests
from bs4 import BeautifulSoup
import telegram
import os
import asyncio
from datetime import datetime
import time

async def check_announcements():
    try:
        print("Starting announcement check...")
        bot_token = os.environ['TELEGRAM_BOT_TOKEN']
        chat_id = os.environ['TELEGRAM_CHAT_ID']
        bot = telegram.Bot(token=bot_token)
        
        # Using regular web URL with full browser-like headers
        url = "https://www.binance.com/en/support/announcement/delisting?c=161&navId=161"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.binance.com',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        print("Fetching Binance page...")
        session = requests.Session()
        response = session.get(url, headers=headers)
        response.raise_for_status()
        print(f"Got response: {response.status_code}")
        
        # Save response for debugging
        print(f"Response content length: {len(response.text)}")
        print("First 500 chars of response:", response.text[:500])
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try different selectors
        selectors = [
            'div.css-1wr4jig',
            '.announcement-item',
            'a[href*="/announcement"]',
            'div[class*="title"]'
        ]
        
        announcements = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                announcements.extend(found)
                print(f"Found {len(found)} items with selector {selector}")
        
        if announcements:
            for announcement in announcements:
                # Try to get the text content
                title = announcement.get_text().strip()
                print(f"Found announcement: {title}")
                
                if 'Binance Will Delist' in title:
                    link = announcement.get('href', '')
                    if not link and announcement.find_parent('a'):
                        link = announcement.find_parent('a').get('href', '')
                    
                    if link and not link.startswith('http'):
                        link = 'https://www.binance.com' + link
                    
                    message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
                    await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
                    print(f"Sent notification for: {title}")
        else:
            print("No announcements found with any selector")
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        if 'bot' in locals() and 'chat_id' in locals():
            error_message = f"⚠️ Error checking announcements: {str(e)}"
            await bot.send_message(chat_id=chat_id, text=error_message)
        raise e

async def main():
    await check_announcements()

if __name__ == "__main__":
    asyncio.run(main())
