import requests
from bs4 import BeautifulSoup
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
        
        url = "https://www.binance.com/bapi/composite/v1/public/cms/article/catalog/list/query?catalogId=161&pageNo=1&pageSize=20&rnd=" + str(datetime.now().timestamp())
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        print("Fetching Binance API...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(f"Got response: {response.status_code}")
        
        data = response.json()
        if 'data' in data and 'articles' in data['data']:
            articles = data['data']['articles']
            print(f"Found {len(articles)} announcements")
            
            for article in articles:
                title = article.get('title', '').strip()
                print(f"Found title: {title}")
                
                if title.startswith('Binance Will Delist'):
                    code = article.get('code', '')
                    link = f"https://www.binance.com/en/support/announcement/{code}"
                    message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
                    await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
                    print(f"Sent delisting notification for: {title}")
            
            if not any(a.get('title', '').startswith('Binance Will Delist') for a in articles):
                print("No delisting announcements found")
                
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
