import requests
import os
from pathlib import Path

from modules.utils.logger import logger
from modules.models.config import config

class NotificationManager:
    """Clase que encapsula notificaciones a servicios externos (Discord, Telegram)."""
    
    def __init__(self):
        self.discord_webhook = config.discord.webhook_url
        
    def send_discord_file(self, filepath: Path) -> bool:
        """Toma un archivo local y lo empuja a Discord usando Multi-part."""
        if not self.discord_webhook:
            logger.debug("Discord webhook no proporcionado, saltando notificación.")
            return False
            
        if not filepath.exists() or not filepath.is_file():
            logger.error(f"El archivo a enviar no existe en: {filepath}")
            return False
            
        try:
            with open(filepath, 'rb') as f:
                files = {
                    'file': (filepath.name, f, 'text/markdown')
                }
                payload = {
                    'content': '🚀 **¡Nuevo Boletín Diario del Tech Criollo Listo Para Grabar/Publicar!**'
                }
                
                response = requests.post(self.discord_webhook, data=payload, files=files, timeout=20)
                response.raise_for_status()
                
            logger.info("Notificación enviada a Discord exitosamente.")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error HTTP enviando notificación a Discord: {e}")
            return False
        except Exception as e:
            logger.error(f"Error asíncrono inesperado enviando notificación: {e}")
            return False

    def send_telegram_file(self, filepath: Path) -> bool:
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
                payload = {
                    'chat_id': chat_id,
                    'caption': '🚀 **¡Nuevo Boletín Diario del Tech Criollo Listo!**\nRevísalo para grabar tus Reels.'
                }
                files = {
                    'document': (filepath.name, f, 'text/markdown')
                }
                response = requests.post(url, data=payload, files=files, timeout=20)
                response.raise_for_status()
                
            logger.info("Notificación enviada a Telegram exitosamente.")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error HTTP enviando notificación a Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"Error asíncrono inesperado enviando notificación a Telegram: {e}")
            return False

    def send_telegram_visual_news(self, article) -> bool:
        """Envía una foto con un pie de página atractivo (resumen + comentario AI)."""
        bot_token = config.telegram.bot_token
        chat_id = config.telegram.chat_id
        
        if not bot_token or not chat_id:
            logger.debug("Credenciales de Telegram no proporcionadas, saltando envío visual.")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            
            # Sanitización para modo HTML de Telegram
            import html
            safe_title = html.escape(article.title)
            safe_comment = html.escape(article.ai_comment)
            safe_source = html.escape(article.source_name)
            
            # Construir el pie de página (Caption) usando HTML (más robusto para links con caracteres especiales)
            caption = (
                f"📰 <b>{safe_title}</b>\n\n"
                f"📝 <b>Resumen del Analista:</b>\n{safe_comment}\n\n"
                f"📍 <b>Fuente:</b> {safe_source}\n"
                f"🔗 <a href='{article.link}'>Leer noticia original</a>"
            )
            
            payload = {
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': 'HTML'
            }
            
            # Si hay imagen, la enviamos por URL, si no, fallamos al modo texto simple
            if article.image_url:
                payload['photo'] = article.image_url
                response = requests.post(url, data=payload, timeout=20)
                response.raise_for_status()
            else:
                # Enviar solo texto si no hay imagen
                text_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload.pop('photo', None)
                payload['text'] = caption
                response = requests.post(text_url, data=payload, timeout=20)
                response.raise_for_status()
                
            logger.info(f"Noticia visual enviada a Telegram: {article.title[:30]}...")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error HTTP enviando noticia visual a Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado en envío visual: {e}")
            return False
