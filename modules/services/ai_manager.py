import httpx
from modules.utils.logger import logger
from modules.models.config import config
from modules.models.source import ScrapedArticle

class AIManager:
    """Clase para la conexión abstracta con Inteligencia Artificial vía Ollama HTTP API."""

    def __init__(self):
        self.base_url = config.ai.ollama_url
        self.model = config.ai.ollama_model
        
    async def ping(self) -> bool:
        """Revisa si el servidor de ollama está disponible y vivo."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=5.0)
                return response.status_code == 200
        except httpx.RequestError:
            return False

    async def generate_comment(self, article: ScrapedArticle) -> str:
        """Emite una petición de inferencia a Ollama obteniendo comentario sátirico / tech del Tech Criollo."""
        if not await self.ping():
            logger.warning(f"Ollama inalcanzable en {self.base_url}. Se omite inferencia.")
            return "Ollama no está disponible. Requiere verificar host local."

        prompt = f"""Actúa como un Analista de Tecnología experto y redactor profesional. 
        Tu tarea es redactar una versión propia y original de la siguiente noticia en español formal. 
        
        REGLAS ESTRICTAS:
        1. NO utilices jergas, modismos locales ni palabras informales (PROHIBIDO usar 'parce', 'bacán', etc.).
        2. El tono debe ser profesional, serio y experto.
        3. Redacta un párrafo detallado de entre 3 y 4 líneas que resuma los puntos clave.
        4. Asegúrate que la redacción sea original para evitar que parezca un plagio directo de la fuente.
        
        Noticia Título: {article.title}
        Extracto/Contexto: {article.summary[:500]}
        
        Devuelve SOLO la redacción original como string directo, sin prefijos ni títulos. Salida directa:"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.8,
                "num_ctx": 2048
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload, timeout=120.0)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()
        except httpx.RequestError as e:
            logger.error(f"Falla HTTP interactuando con Ollama: {e}")
            return "Error contactando a la Inteligencia Artificial Local."
        except Exception as e:
            logger.error(f"Error inesperado en inferencia LLM: {e}")
            return "Error interno en Generación IA."

    async def generate_reel_script(self, article: ScrapedArticle) -> str:
        """Emite una petición secundaria para crear un guion explosivo de formato vertical."""
        if not await self.ping():
            return "Ollama inaccesible."

        prompt = f"""Actúa como un creador de contenido viral. Escribe un guion corto (máximo 45 segundos) para un Reel/TikTok basado en esta noticia tecnológica. 
        DEBE tener:
        1. Un HOOK (gancho) explosivo en los primeros 3 segundos.
        2. Desarrollo ultra-rápido de la noticia.
        3. Call to Action (CTA) polémico o que invite a comentar.
        
        Noticia Título: {article.title}
        Extracto/Contexto: {article.summary[:300]}
        
        Devuelve de forma limpia SOLO el texto del guion, sin anotaciones o introducciones tuyas."""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.9,
                "num_ctx": 2048
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload, timeout=120.0)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()
        except Exception as e:
            logger.error(f"Error generando guion: {e}")
            return "Fallo generando guion viral."

    async def is_tech_news(self, article: ScrapedArticle) -> bool | None:
        """Determinas con IA si la noticia es puramente tecnológica o de digitalización gubernamental/general."""
        if not await self.ping():
            return None # Fallback a validación de palabras clave si Ollama no está disponible

        prompt = f"""Responde únicamente con SI o NO.
¿Es el siguiente artículo estrictamente sobre tecnología emergente, innovación tecnológica, ciberseguridad, startups tecnológicas, inteligencia artificial o desarrollo de software? Si es sobre trámites de gobierno, política, subsidios, nombramientos (incluso si son en ministerios de TIC) o noticias generales, debes responder NO.

Título: {article.title}
Extracto: {article.summary[:500]}

Tu respuesta (SI o NO):"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": 1024
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                answer = data.get("response", "").strip().upper()
                return answer.startswith("SI")
        except Exception as e:
            logger.error(f"Error comprobando validez de tech en IA: {e}")
            return None
