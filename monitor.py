import requests
import telegram
import os
import asyncio
from datetime import datetime
import json

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

        # V2 API endpoint
        url = "https://www.binance.com/api/v2/cms/public-info/get-list"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Referer": "https://www.binance.com/en/support/announcement/delisting",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Pragma": "no-cache"
        }
        
        params = {
            "catalogId": "161",
            "pageNo": "1",
            "pageSize": "20"
        }
        
        print("Making request to Binance...")
        session = requests.Session()
        # First get the main page to get any necessary cookies
        session.get("https://www.binance.com/en/support/announcement/delisting", headers=headers)
        
        # Then make the API request
        response = session.get(url, headers=headers, params=params)
        response.raise_for_status()
        print(f"Got response: {response.status_code}")
        
        try:
            data = response.json()
            print("Successfully parsed JSON response")
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {str(e)}")
            print(f"Response text: {response.text[:200]}")
            return

        if 'data' in data and isinstance(data['data'], list):
            announcements = data['data']
            print(f"Found {len(announcements)} announcements")
            
            for announcement in announcements:
                title = announcement.get('title', '').strip()
                print(f"Checking announcement: {title}")
                
                if title.startswith('Binance Will Delist'):
                    code = announcement.get('code', '')
                    link = f"https://www.binance.com/en/support/announcement/{code}"
                    
                    message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
                    await send_message(bot, chat_id, message)
                    print(f"Sent notification for: {title}")
        else:
            print(f"Unexpected data structure. Keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")

    except Exception as e:
        error_message = f"⚠️ Error checking announcements: {str(e)}"
        print(error_message)
        if 'response' in locals():
            print(f"Response status: {getattr(response, 'status_code', 'N/A')}")
            print(f"Response text: {getattr(response, 'text', 'N/A')[:200]}")
        if 'bot' in locals() and 'chat_id' in locals():
            await send_message(bot, chat_id, error_message)
        raise e

async def main():
    await check_announcements()

if __name__ == "__main__":
    asyncio.run(main())
