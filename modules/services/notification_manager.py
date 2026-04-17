import httpx
import os
from pathlib import Path

from modules.utils.logger import logger
from modules.models.config import config

class NotificationManager:
    """Clase que encapsula notificaciones a servicios externos (Discord, Telegram)."""
    
    def __init__(self):
        self.discord_webhook = config.discord.webhook_url
        
    async def send_discord_file(self, filepath: Path) -> bool:
        """Toma un archivo local y lo empuja a Discord usando Multi-part."""
        if not self.discord_webhook:
            logger.debug("Discord webhook no proporcionado, saltando notificación.")
            return False
            
        if not filepath.exists() or not filepath.is_file():
            logger.error(f"El archivo a enviar no existe en: {filepath}")
            return False
            
        try:
            with open(filepath, 'rb') as f:
                file_content = f.read()

            files = {
                'file': (filepath.name, file_content, 'text/markdown')
            }
            data = {
                'content': '🚀 **¡Nuevo Boletín Diario del Tech Criollo Listo Para Grabar/Publicar!**'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.discord_webhook, data=data, files=files, timeout=20.0)
                response.raise_for_status()
                
            logger.info("Notificación enviada a Discord exitosamente.")
            return True
            
        except httpx.RequestError as e:
            logger.error(f"Error HTTP enviando notificación a Discord: {e}")
            return False
        except Exception as e:
            logger.error(f"Error asíncrono inesperado enviando notificación: {e}")
            return False

    async def send_telegram_file(self, filepath: Path) -> bool:
        """Toma un archivo local y lo empuja a Telegram usando document endpoint."""
        bot_token = config.telegram.bot_token
        chat_id = config.telegram.chat_id
        
        if not bot_token or not chat_id:
            logger.debug("Credenciales de Telegram no proporcionadas, saltando notificación.")
            return False
            
        if not filepath.exists() or not filepath.is_file():
            logger.error(f"El archivo a enviar no existe en: {filepath}")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
            with open(filepath, 'rb') as f:
                file_content = f.read()
                
            data = {
                'chat_id': chat_id,
                'caption': '🚀 **¡Nuevo Boletín Diario del Tech Criollo Listo!**\nRevísalo para grabar tus Reels.'
            }
            files = {
                'document': (filepath.name, file_content, 'text/markdown')
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data, files=files, timeout=20.0)
                response.raise_for_status()
                
            logger.info("Notificación enviada a Telegram exitosamente.")
            return True
            
        except httpx.RequestError as e:
            logger.error(f"Error HTTP enviando notificación a Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"Error asíncrono inesperado enviando notificación a Telegram: {e}")
            return False

    async def send_telegram_visual_news(self, article) -> bool:
        """Envía una foto con un pie de página atractivo (resumen + comentario AI)."""
        bot_token = config.telegram.bot_token
        chat_id = config.telegram.chat_id
        
        if not bot_token or not chat_id:
            logger.debug("Credenciales de Telegram no proporcionadas, saltando envío visual.")
            return False
            
        try:
            # Sanitización para modo HTML de Telegram
            import html
            safe_title = html.escape(article.title)
            safe_comment = html.escape(article.ai_comment)
            safe_source = html.escape(article.source_name)
            
            # Construir el pie de página (Caption) usando HTML
            caption = (
                f"📰 <b>{safe_title}</b>\n\n"
                f"📝 <b>Resumen del Analista:</b>\n{safe_comment}\n\n"
                f"📍 <b>Fuente:</b> {safe_source}\n"
                f"🔗 <a href='{article.link}'>Leer noticia original</a>"
            )
            
            data = {
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': 'HTML'
            }
            
            async with httpx.AsyncClient() as client:
                # Si hay imagen, la enviamos por URL, si no, fallamos al modo texto simple
                if article.image_url:
                    data['photo'] = article.image_url
                    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                    response = await client.post(url, data=data, timeout=20.0)
                    response.raise_for_status()
                else:
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    data['text'] = caption
                    response = await client.post(url, data=data, timeout=20.0)
                    response.raise_for_status()
                    
            logger.info(f"Noticia visual enviada a Telegram: {article.title[:30]}...")
            return True
            
        except httpx.RequestError as e:
            logger.error(f"Error HTTP enviando noticia visual a Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado en envío visual: {e}")
            return False
