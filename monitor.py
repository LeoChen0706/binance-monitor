import requests
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

        # Direct data endpoint
        url = "https://www.binance.com/gateway-api/v1/public/cms/article/list/query"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "bnc-uuid": "web_" + str(int(datetime.now().timestamp() * 1000)),
            "clienttype": "web",
            "lang": "en"
        }
        
        params = {
            "type": "1",
            "pageNo": "1",
            "pageSize": "20",
            "catalogId": "161"
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        if response.status_code != 200:
            print(f"Got status code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return

        try:
            data = response.json()
        except Exception as e:
            print(f"Failed to parse JSON: {str(e)}")
            print(f"Raw response: {response.text[:200]}")
            return

        if 'data' in data and 'articles' in data['data']:
            announcements = data['data']['articles']
            
            for announcement in announcements:
                title = announcement.get('title', '').strip()
                print(f"Found announcement: {title}")  # Debug print
                
                if title.startswith('Binance Will Delist'):
                    code = announcement.get('code', '')
                    link = f"https://www.binance.com/en/support/announcement/{code}"
                    
                    message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
                    await send_message(bot, chat_id, message)
        else:
            print("Unexpected data structure:", data.keys())

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        if 'response' in locals():
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text[:200]}")
        raise e

async def main():
    await check_announcements()

if __name__ == "__main__":
    asyncio.run(main())
