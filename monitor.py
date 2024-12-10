import requests
from bs4 import BeautifulSoup
import telegram
import os

def send_notification(bot_token, chat_id, title, link):
    """Send notification via Telegram"""
    bot = telegram.Bot(token=bot_token)
    message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
    bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')

def check_announcements(bot_token, chat_id):
    """Check for new delisting announcements"""
    url = "https://www.binance.com/en/support/announcement/delisting"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find announcement elements
        announcements = soup.select('.announcement-item')
        
        for announcement in announcements:
            title = announcement.select_one('.title').text.strip()
            link = announcement.select_one('a')['href']
            
            if 'delist' in title.lower():
                send_notification(bot_token, chat_id, title, link)
                
    except Exception as e:
        send_notification(bot_token, chat_id, "Monitor Error", f"Error checking announcements: {str(e)}")

def main():
    bot_token = os.environ['TELEGRAM_BOT_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    send_notification(bot_token, chat_id, "Test", "Bot is running successfully!")
    check_announcements(bot_token, chat_id)

if __name__ == "__main__":
    main()
