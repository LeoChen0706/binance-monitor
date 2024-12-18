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

        # Binance API endpoint for announcements
        url = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'content-type': 'application/json'
        }
        payload = {
            "type": "1",
            "pageSize": 20,
            "pageNo": 1,
            "catalogId": "161"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        found_delisting = False
        
        if 'data' in data and 'catalogs' in data['data']:
            announcements = data['data']['catalogs']
            
            for announcement in announcements:
                title = announcement.get('title', '').strip()
                
                if title.startswith('Binance Will Delist'):
                    code = announcement.get('code', '')
                    link = f"https://www.binance.com/en/support/announcement/{code}"
                    
                    message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
                    await send_message(bot, chat_id, message)
                    found_delisting = True
        
            # Only send status message if delisting found
            if found_delisting:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await send_message(bot, chat_id, f"⚠️ Please check the delisting announcements carefully!")
                
    except Exception as e:
        error_message = f"⚠️ Error checking announcements: {str(e)}"
        if 'bot' in locals() and 'chat_id' in locals():
            await send_message(bot, chat_id, error_message)
        print(error_message)
        raise e

async def main():
    await check_announcements()

if __name__ == "__main__":
    asyncio.run(main())
