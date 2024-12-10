import telegram
import os
import asyncio

async def main():
    try:
        # Get credentials
        bot_token = os.environ['TELEGRAM_BOT_TOKEN']
        chat_id = os.environ['TELEGRAM_CHAT_ID']
        
        # Print for debugging
        print(f"Starting with chat_id: {chat_id}")
        
        # Create bot and send message
        bot = telegram.Bot(token=bot_token)
        await bot.send_message(
            chat_id=chat_id,
            text="🔥 Test: Bot is running!"
        )
        print("Message sent successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise e

if __name__ == "__main__":
    asyncio.run(main())
