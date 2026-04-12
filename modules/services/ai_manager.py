import requests
from modules.utils.logger import logger
from modules.models.config import config
from modules.models.source import ScrapedArticle

class AIManager:
    """Clase para la conexión abstracta con Inteligencia Artificial vía Ollama HTTP API."""

    def __init__(self):
        self.base_url = config.ai.ollama_url
        self.model = config.ai.ollama_model
        
    def ping(self) -> bool:
        """Revisa si el servidor de ollama está disponible y vivo."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def generate_comment(self, article: ScrapedArticle) -> str:
        """Emite una petición de inferencia a Ollama obteniendo comentario sátirico / tech del Dev Criollo."""
        if not self.ping():
            logger.warning(f"Ollama inalcanzable en {self.base_url}. Se omite inferencia.")
            return "Ollama no está disponible. Requiere verificar host local."

        # Prompt system engineering
        prompt = f"""Escribe un comentario breve y satírico pero profesional (máximo 2 oraciones)
        como si fueras el 'Dev Criollo' (un Ingeniero de Software latinoamericano agobiado pero experto),
        dando tu opinión o reacción frente a esta noticia de IA/Tecnología. 
        Habla como un programador de Medellín, Colombia (usa 'parce' suave u otras jergas tech, pero serio).
        
        Noticia Título: {article.title}
        Extracto/Contexto: {article.summary[:300]}
        
        Devuelve SOLO el comentario como string directo, sin prefijos ni títulos. Salida directa:"""

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
            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except requests.RequestException as e:
            logger.error(f"Falla HTTP interactuando con Ollama: {e}")
            return "Error contactando a la Inteligencia Artificial Local."
        except Exception as e:
            logger.error(f"Error inesperado en inferencia LLM: {e}")
            return "Error interno en Generación IA."

    def generate_reel_script(self, article: ScrapedArticle) -> str:
        """Emite una petición secundaria para crear un guion explosivo de formato vertical."""
        if not self.ping():
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
            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except Exception as e:
            logger.error(f"Error generando guion: {e}")
            return "Fallo generando guion viral."
