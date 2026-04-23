import httpx
import os
from pathlib import Path

from modules.utils.logger import logger
from modules.models.config import config

class NotificationManager:
    """Clase que encapsula notificaciones a servicios externos (Discord, Telegram)."""
    
    def __init__(self):
        self.discord_webhook = config.discord.webhook_url
        # Normalización de chat_id: Telegram funciona mejor con IDs numéricos directos o strings sin espacios
        raw_chat_id = config.telegram.chat_id
        try:
            self.chat_id = int(str(raw_chat_id).strip())
        except (ValueError, TypeError):
            self.chat_id = str(raw_chat_id).strip()
            
    def _safe_escape(self, text) -> str:
        """Escapa texto para HTML de Telegram evitando errores con valores None."""
        if text is None:
            return ""
        import html
        return html.escape(str(text))
        
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

    async def send_telegram_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Envía un mensaje de texto simple o formateado a Telegram."""
        bot_token = config.telegram.bot_token
        chat_id = config.telegram.chat_id
        
        if not bot_token or not chat_id:
            logger.debug("Credenciales de Telegram no proporcionadas, saltando notificación.")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data, timeout=20.0)
                response.raise_for_status()
                
            logger.info("Mensaje de texto enviado a Telegram exitosamente.")
            return True
            
        except httpx.RequestError as e:
            logger.error(f"Error HTTP enviando mensaje a Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"Error asíncrono inesperado enviando mensaje a Telegram: {e}")
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
            safe_title = self._safe_escape(article.title)
            safe_comment = self._safe_escape(article.ai_comment)
            safe_source = self._safe_escape(article.source_name)
            
            # Si el comentario está vacío (falló la IA), usar un fallback digno
            if not safe_comment:
                safe_comment = "<i>La IA está analizando los detalles de esta noticia. Mientras tanto, puedes leer el original abajo.</i>"
            
            # Construir el pie de página usando HTML
            caption = (
                f"⚡ <b>ÚLTIMA HORA TECH</b> ⚡\n\n"
                f"💻 <b>{safe_title}</b>\n\n"
                f"<blockquote>{safe_comment}</blockquote>\n\n"
                f"📡 <b>Vía:</b> <i>{safe_source}</i>\n"
                f"🔗 <a href='{article.link}'>Leer artículo completo</a>\n\n"
                f"#TechCriollo #Noticias #Tecnología"
            )
            
            async with httpx.AsyncClient() as client:
                sent = False
                
                # Intento 1: enviar con foto si hay imagen
                if article.image_url:
                    photo_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                    photo_data = {
                        'chat_id': self.chat_id,
                        'caption': caption,
                        'parse_mode': 'HTML',
                        'photo': article.image_url
                    }
                    try:
                        response = await client.post(photo_url, data=photo_data, timeout=20.0)
                        if response.status_code == 200:
                            sent = True
                            logger.info(f"Noticia visual enviada a Telegram (foto): {article.title[:50]}")
                        else:
                            tg_error = response.json().get('description', 'desconocido')
                            logger.warning(f"sendPhoto falló ({response.status_code}): {tg_error}. Intentando texto puro...")
                    except Exception as photo_err:
                        logger.warning(f"Error en sendPhoto: {photo_err}. Intentando texto puro...")

                # Intento 2 (fallback): enviar como texto si la foto falló o no hay imagen
                if not sent:
                    msg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    msg_data = {
                        'chat_id': self.chat_id,
                        'text': caption,
                        'parse_mode': 'HTML'
                    }
                    response = await client.post(msg_url, data=msg_data, timeout=20.0)
                    if response.status_code == 200:
                        sent = True
                        logger.info(f"Noticia enviada a Telegram (texto): {article.title[:50]}")
                    else:
                        tg_error = response.json().get('description', 'desconocido')
                        logger.error(f"sendMessage falló ({response.status_code}): {tg_error}")

            return sent
            
        except httpx.RequestError as e:
            logger.error(f"Error de red enviando noticia a Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado en envío visual: {e}")
            return False
