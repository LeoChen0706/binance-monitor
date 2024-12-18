import requests
import telegram
import os
import asyncio
from datetime import datetime
import json

async def check_announcements():
    try:
        print("Starting announcement check...")
        bot_token = os.environ['TELEGRAM_BOT_TOKEN']
        chat_id = os.environ['TELEGRAM_CHAT_ID']
        bot = telegram.Bot(token=bot_token)

        # Direct API endpoint that Binance's frontend uses
        url = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
        
        # Request payload
        payload = {
            "type": "1",
            "pageSize": 20,
            "pageNo": 1,
            "catalogId": "161"
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'content-type': 'application/json',
            'lang': 'en',
            'x-request-source': 'web'
        }
        
        print("Fetching Binance API...")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Got response: {response.status_code}")
        
        # Print first part of response for debugging
        print(f"Response preview: {str(response.text)[:200]}")
        
        data = response.json()
        if 'data' in data and 'catalogs' in data['data']:
            announcements = data['data']['catalogs']
            print(f"Found {len(announcements)} announcements")
            
            for announcement in announcements:
                title = announcement.get('title', '').strip()
                print(f"Checking announcement: {title}")
                
                if title.startswith('Binance Will Delist'):
                    code = announcement.get('code', '')
                    link = f"https://www.binance.com/en/support/announcement/{code}"
                    
                    message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
                    await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
                    print(f"Sent notification for: {title}")
            
            if not any(a.get('title', '').startswith('Binance Will Delist') for a in announcements):
                print("No delisting announcements found")
        else:
            print("Unexpected API response structure")
            print(f"Response Keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
                
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        if 'response' in locals():
            print(f"Response text: {response.text[:500]}")
        if 'bot' in locals() and 'chat_id' in locals():
            error_message = f"⚠️ Error checking announcements: {str(e)}"
            await bot.send_message(chat_id=chat_id, text=error_message)
        raise e

async def main():
    await check_announcements()

if __name__ == "__main__":
    asyncio.run(main())
