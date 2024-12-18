import os
import asyncio
import telegram
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

async def send_message(bot, chat_id, message):
    """Helper function to send messages"""
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode='HTML'
    )

async def check_announcements():
    """Check for new delisting announcements using Selenium"""
    try:
        # Get credentials
        bot_token = os.environ['TELEGRAM_BOT_TOKEN']
        chat_id = os.environ['TELEGRAM_CHAT_ID']
        bot = telegram.Bot(token=bot_token)

        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        print("Browser initialized")
        
        try:
            # Navigate to the page
            url = "https://www.binance.com/en/support/announcement/delisting?c=161&navId=161"
            print(f"Navigating to {url}")
            driver.get(url)
            
            # Wait for announcements to load
            print("Waiting for announcements to load...")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "css-1wr4jig"))
            )
            
            # Let the page fully load
            time.sleep(5)
            
            # Find all announcements
            announcements = driver.find_elements(By.CLASS_NAME, "css-1wr4jig")
            print(f"Found {len(announcements)} announcements")
            
            found_delisting = False
            for announcement in announcements:
                try:
                    title = announcement.text.strip()
                    print(f"Found announcement: {title}")
                    
                    if title.startswith("Binance Will Delist"):
                        link = announcement.find_element(By.TAG_NAME, "a").get_attribute("href")
                        message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
                        await send_message(bot, chat_id, message)
                        found_delisting = True
                        print(f"Sent notification for: {title}")
                except Exception as e:
                    print(f"Error processing announcement: {str(e)}")
                    continue
            
            if not found_delisting:
                print("No new delisting announcements found")
                
        finally:
            driver.quit()
            print("Browser closed")

    except Exception as e:
        error_message = f"⚠️ Error checking announcements: {str(e)}"
        print(error_message)
        if 'bot' in locals() and 'chat_id' in locals():
            await send_message(bot, chat_id, error_message)
        raise e

async def main():
    await check_announcements()

if __name__ == "__main__":
    asyncio.run(main())
