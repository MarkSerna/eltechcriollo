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
        """Emite una petición de inferencia a Ollama obteniendo una redacción periodística objetiva de la noticia tecnológica."""
        if not await self.ping():
            logger.warning(f"Ollama inalcanzable en {self.base_url}. Se omite inferencia.")
            return "Ollama no está disponible. Requiere verificar host local."

        prompt = f"""Escribe una noticia original y profesional sobre tecnología, como si fueras el periodista primario (redactor de "El Tech Criollo").
        
        REGLAS ESTRICTAS:
        1. Escribe en tercera persona de forma clara, relatando los hechos periodísticos principales (qué, quién, cómo, por qué).
        2. NO hables sobre la noticia, simplemente DA LA NOTICIA como contenido propio. Prohibido usar introducciones como "La noticia dice", o actuar como si fueras una IA analizándola.
        3. Si la noticia trata sobre becas, convocatorias o educación (ej. SENA, MinTIC), DEBES extraer y listar mediante viñetas (-) los cursos, áreas de tecnología o habilidades específicas mencionadas.
        4. AL FINAL DEL TEXTO DEBES CITAR OBLIGATORIAMENTE LA FUENTE ORIGINAL de forma natural. Por ejemplo: "Según el reporte publicado por X..." o "De acuerdo con la investigación de Y...".
        5. DEBES insertar OBLIGATORIAMENTE el siguiente enlace exacto en la mención a la fuente: {article.link}
        
        Noticia Base (Título): {article.title}
        Extracto Original: {article.summary[:500]}
        
        Devuelve SOLO la noticia redactada final, estructurada en un par de párrafos, con su esquema de citación y link integrado. Salida:"""

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

    async def chat(self, user_message: str) -> str:
        """Permite interactuar de manera conversacional libre con el modelo Ollama."""
        if not await self.ping():
            return "Lo siento, mi servidor cerebral (Ollama) está apagado o fuera de línea."

        prompt = user_message

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_ctx": 4096
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload, timeout=120.0)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()
        except Exception as e:
            logger.error(f"Error en chat libre con IA: {e}")
            return "Se me fundieron los cables intentando procesar esa petición."
