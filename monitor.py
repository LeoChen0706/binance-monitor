import asyncio
import websockets
import json
import telegram
import os
import logging
import aiohttp
import time
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('binance_ws_monitor.log'),
        logging.StreamHandler()
    ]
)

class BinanceMonitor:
    def __init__(self):
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        if not self.bot_token or not self.chat_id:
            raise ValueError("Missing environment variables: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        self.bot = telegram.Bot(token=self.bot_token)
        self.ws_url = "wss://stream.binance.com:9443/ws"
        self.http_url = "https://www.binance.com/bapi/composite/v1/public/cms/article/catalog/list/query"
        self.last_check = time.time()
        self.check_interval = 300  # 5 minutes

    async def send_telegram_message(self, message):
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            logging.info(f"Sent message to Telegram: {message[:100]}...")
        except Exception as e:
            logging.error(f"Failed to send Telegram message: {str(e)}")

    async def check_announcements_api(self):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            payload = {
                "catalogId": "161",
                "pageNo": 1,
                "pageSize": 20,
                "rnd": time.time()
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.http_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'data' in data and 'articles' in data['data']:
                            for article in data['data']['articles']:
                                title = article.get('title', '').strip()
                                if title.lower().startswith('binance will delist'):
                                    code = article.get('code', '')
                                    link = f"https://www.binance.com/en/support/announcement/{code}"
                                    message = f"🚨 New Delisting Announcement 🚨\n\nTitle: {title}\nLink: {link}"
                                    await self.send_telegram_message(message)
                                    logging.info(f"Found delisting announcement: {title}")

        except Exception as e:
            logging.error(f"Error checking announcements API: {str(e)}")
            await self.send_telegram_message(f"⚠️ Error checking announcements API: {str(e)}")

    async def handle_websocket(self):
        while True:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    # Send heartbeat message
                    subscribe_message = {
                        "method": "SET_PROPERTY",
                        "params": ["combined", True],
                        "id": 1
                    }
                    await websocket.send(json.dumps(subscribe_message))
                    
                    # Main loop
                    while True:
                        # Check announcements periodically through API
                        current_time = time.time()
                        if current_time - self.last_check >= self.check_interval:
                            await self.check_announcements_api()
                            self.last_check = current_time
                        
                        # Keep connection alive with ping/pong
                        try:
                            # Wait for messages with a timeout
                            message = await asyncio.wait_for(websocket.recv(), timeout=180)
                            # Process any received messages
                            data = json.loads(message)
                            logging.debug(f"Received WebSocket message: {data}")
                            
                        except asyncio.TimeoutError:
                            # Send ping to keep connection alive
                            pong_frame = json.dumps({"method": "PING"})
                            await websocket.send(pong_frame)
                            continue
                            
            except Exception as e:
                logging.error(f"WebSocket error: {str(e)}")
                await self.send_telegram_message(f"⚠️ WebSocket connection error: {str(e)}")
                # Wait before reconnecting
                await asyncio.sleep(5)

    async def start(self):
        await self.send_telegram_message("🟢 Binance Monitor started")
        try:
            await self.handle_websocket()
        except Exception as e:
            logging.error(f"Fatal error: {str(e)}")
            await self.send_telegram_message(f"🔴 Fatal error: {str(e)}")

async def main():
    monitor = BinanceMonitor()
    await monitor.start()

if __name__ == "__main__":
    asyncio.run(main())
