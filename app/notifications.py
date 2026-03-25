"""
Telegram Notifier - wysyła powiadomienia przez Commander bota
"""
import httpx
import logging

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    async def send(self, message: str):
        """Send notification to Telegram"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json={
                        "chat_id": self.chat_id,
                        "text": f"🌐 *WordPress Agent*\n\n{message}",
                        "parse_mode": "Markdown"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Telegram notification sent: {message[:50]}...")
                else:
                    logger.warning(f"⚠️ Telegram notification failed: {response.status_code}")
        
        except Exception as e:
            logger.error(f"❌ Telegram error: {e}")
