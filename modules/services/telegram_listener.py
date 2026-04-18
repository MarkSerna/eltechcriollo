import asyncio
import httpx
from modules.utils.logger import logger
from modules.models.config import config
from modules.services.ai_manager import AIManager

class TelegramBotListener:
    """Clase para escuchar mensajes entrantes de Telegram (Long Polling) y conectar con la IA."""
    def __init__(self):
        self.bot_token = config.telegram.bot_token
        self.ai = AIManager()
        self.offset = 0

    async def poll(self):
        """Inicia el ciclo infinito (long-polling) para atrapar mensajes de Telegram."""
        if not self.bot_token:
            logger.warning("No hay token de Telegram configurado. Ignorando polling (chat de Bot desactivado).")
            return

        logger.info("🤖 Listener de Telegram activado: Esperando mensajes para conversar...")
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        
        # Timeout largo para el Long Polling real de Telegram (60s)
        timeout_client = httpx.Timeout(65.0)
        
        async with httpx.AsyncClient(timeout=timeout_client) as client:
            while True:
                try:
                    # 'timeout=60' instruye a Telegram a retener la conexión hasta 60s si no hay mensajes
                    response = await client.get(url, params={"offset": self.offset, "timeout": 60})
                    if response.status_code == 200:
                        data = response.json()
                        for update in data.get("result", []):
                            self.offset = update["update_id"] + 1
                            
                            # Validar que sea un mensaje de texto
                            if "message" in update and "text" in update["message"]:
                                chat_id = update["message"]["chat"]["id"]
                                text = update["message"]["text"]
                                # Derivar la respuesta a otra tarea para no bloquear el polling si hay varios mensajes
                                asyncio.create_task(self.handle_message(chat_id, text))
                except httpx.ReadTimeout:
                    # Normal en Long Polling cuando expira el minuto libre
                    continue
                except asyncio.CancelledError:
                    logger.info("🔴 Polling de Telegram cancelado.")
                    break
                except Exception as e:
                    logger.error(f"Error en polling de telegram: {e}")
                    await asyncio.sleep(5)
                
    async def handle_message(self, chat_id, text):
        logger.info(f"💬 Conversación por Telegram recibida: {text}")
        
        # Avisar al usuario que estamos pensando (Telegram 'typing' action)
        try:
            typing_url = f"https://api.telegram.org/bot{self.bot_token}/sendChatAction"
            async with httpx.AsyncClient() as c:
                await c.post(typing_url, json={"chat_id": chat_id, "action": "typing"})
        except Exception:
            pass

        # Conectar con Ollama
        reply = await self.ai.chat(text)
        
        # Responder al instante
        send_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            async with httpx.AsyncClient() as c:
                await c.post(send_url, json={"chat_id": chat_id, "text": reply, "parse_mode": "Markdown"})
        except Exception as e:
            logger.error(f"Telegram Handler: Error enviando la respuesta de la IA: {e}")
