import asyncio
import httpx
from modules.utils.logger import logger
from modules.models.config import config
from modules.services.ai_manager import AIManager
from modules.services.database_manager import DatabaseManager
import os

class TelegramBotListener:
    """Clase para escuchar mensajes entrantes de Telegram (Long Polling) y conectar con la IA."""
    def __init__(self):
        self.bot_token = config.telegram.bot_token
        self.admin_chat_id = str(config.telegram.chat_id) # Asegurar que es string para comparar
        self.ai = AIManager()
        self.db = DatabaseManager()
        self.offset = 0
        self.is_scraping = False # Flag para evitar ejecuciones concurrentes via bot

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
        logger.info(f"💬 Mensaje de Telegram ({chat_id}): {text}")
        
        # 1. Seguridad: Verificar si el usuario es el administrador
        is_admin = str(chat_id) == self.admin_chat_id
        
        # 2. Despachador de Comandos
        if text.startswith("/"):
            if not is_admin:
                await self.send_reply(chat_id, "🚫 **Acceso Denegado**\n\nNo tienes permisos para ejecutar comandos en este bot. Solo el administrador configurado en `.env` puede hacerlo.")
                return

            command = text.split()[0].lower()
            
            if command == "/start" or command == "/help":
                msg = (
                    "👋 **¡Hola! Soy el asistente de El Tech Criollo.**\n\n"
                    "Puedes usar estos comandos para controlar el proyecto:\n"
                    "🚀 `/scrape` - Inicia un escaneo de noticias ahora mismo.\n"
                    "📊 `/stats` - Muestra estadísticas de lo procesado hoy.\n"
                    "❓ `/help` - Muestra este mensaje de ayuda.\n\n"
                    "También puedes simplemente escribirme para hacerme preguntas sobre tecnología."
                )
                await self.send_reply(chat_id, msg)
            
            elif command == "/scrape":
                if self.is_scraping:
                    await self.send_reply(chat_id, "⏳ **Ya hay un proceso de scraping en ejecución.** Por favor espera a que termine.")
                else:
                    asyncio.create_task(self.run_manual_scrape(chat_id))
            
            elif command == "/stats":
                articles = self.db.get_todays_articles()
                count = len(articles)
                msg = (
                    f"📊 **Estadísticas de Hoy**\n\n"
                    f"Se han procesado **{count}** noticias potentes hasta el momento.\n"
                    f"Última actualización: _hace unos instantes._"
                )
                await self.send_reply(chat_id, msg)
            
            else:
                await self.send_reply(chat_id, "❌ Comando no reconocido. Escribe `/help` para ver la lista.")
            
            return

        # 3. Respuesta de IA (Charla libre)
        # Avisar al usuario que estamos pensando
        await self.send_action(chat_id, "typing")
        
        reply = await self.ai.chat(text)
        await self.send_reply(chat_id, reply)

    async def run_manual_scrape(self, chat_id):
        """Ejecuta el orquestador principal y notifica al finalizar."""
        from modules.core.app import main_orchestrator
        
        self.is_scraping = True
        await self.send_reply(chat_id, "🚀 **Iniciando escaneo manual...**\nEsto puede tardar un par de minutos dependiendo de las fuentes. Te avisaré cuando termine.")
        
        try:
            # Ejecutamos el orquestador
            # Nota: main_orchestrator ya envía noticias individuales al terminar
            new_articles = await main_orchestrator()
            
            count = len(new_articles)
            if count > 0:
                msg = f"✅ **¡Escaneo Finalizado!**\n\nSe encontraron e integraron **{count}** nuevas noticias tecnológicas de alto impacto. Ya están disponibles en el Dashboard."
            else:
                msg = "✅ **¡Escaneo Finalizado!**\n\nNo se encontraron noticias nuevas en esta ejecución."
            
            await self.send_reply(chat_id, msg)
        except Exception as e:
            logger.error(f"Error en scrape manual vía Telegram: {e}")
            await self.send_reply(chat_id, f"❌ **Error durante el escaneo:**\n{str(e)}")
        finally:
            self.is_scraping = False

    async def send_action(self, chat_id, action="typing"):
        """Envía una acción de estado al chat (escribiendo...)."""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendChatAction"
        try:
            async with httpx.AsyncClient() as c:
                await c.post(url, json={"chat_id": chat_id, "action": action})
        except Exception:
            pass

    async def send_reply(self, chat_id, text):
        """Envía un mensaje de respuesta al chat."""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            async with httpx.AsyncClient() as c:
                response = await c.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
                if response.status_code != 200:
                    await c.post(url, json={"chat_id": chat_id, "text": text})
        except Exception as e:
            logger.error(f"Error enviando respuesta Telegram: {e}")
