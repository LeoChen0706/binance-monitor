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

        # Correct Binance delisting announcement URL
        url = "https://www.binance.com/en/support/announcement/delisting?c=161&navId=161"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        print(f"Response status: {response.status_code}")
        print(f"Response URL: {response.url}")
        print(f"Response content length: {len(response.text)}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Debug: Print the first part of the HTML to see the structure
        print("First 500 chars of HTML:", response.text[:500])
        
        # Try multiple possible selectors for announcements
        announcements = (
            soup.select('.css-1wr4jig') or  # Try first selector
            soup.select('.announcement-item') or  # Try second selector
            soup.select('div[class*="announcement"]') or  # Try general announcement class
            soup.select('a[href*="/support/announcement"]')  # Try links containing announcement
        )
        
        print(f"Found {len(announcements)} announcements")
        
        found_delisting = False
        
        for announcement in announcements:
            # Try different ways to get the title and link
            title_element = (
                announcement.select_one('[class*="title"]') or 
                announcement.select_one('h4') or 
                announcement.select_one('h3') or 
                announcement
            )
            title = title_element.get_text().strip()
            
            # Get link from parent if announcement is not already a link
            link_element = announcement if announcement.name == 'a' else announcement.find_parent('a')
            link = link_element.get('href', '') if link_element else ''
            
            if not link.startswith('http'):
                link = 'https://www.binance.com' + link
            
            print(f"Found announcement - Title: {title}, Link: {link}")
            
            if title and link:  # Only process if we have both title and link
                message = f"📢 Announcement Found:\nTitle: {title}\nLink: {link}"
                await send_message(bot, chat_id, message)
                found_delisting = True
        
        # Send completion message
        status = "Found announcements" if found_delisting else "No new announcements found"
        await send_message(bot, chat_id, f"✅ Check completed: {status}")
                
    except Exception as e:
        error_message = f"⚠️ Error: {str(e)}"
        if 'response' in locals():
            error_message += f"\nStatus Code: {response.status_code}"
        if 'bot' in locals() and 'chat_id' in locals():
            await send_message(bot, chat_id, error_message)
        print(error_message)
        raise e

async def main():
    await check_announcements()

if __name__ == "__main__":
    asyncio.run(main())
