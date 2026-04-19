import httpx
from modules.utils.logger import logger
from modules.models.config import config
from modules.models.source import ScrapedArticle
from modules.services.database_manager import DatabaseManager
from modules.services.search_manager import SearchManager

# Soporte opcional para Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class AIManager:
    """Clase para la conexión con IA, soportando Ollama (Local) y Gemini (Cloud)."""

    def __init__(self):
        self.ollama_url = config.ai.ollama_url
        self.ollama_model = config.ai.ollama_model
        self.gemini_key = config.ai.gemini_api_key
        self.db = DatabaseManager()
        self.search_service = SearchManager()
        
        # Configurar Gemini si hay llave
        if self.gemini_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.gemini_key)
            self.gemini_model = genai.GenerativeModel('gemini-3-flash-preview')
            logger.info("⚡ IA de Google Gemini configurada y lista (Modo Cloud).")
        else:
            self.gemini_model = None

    async def _call_llm(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """Helper para decidir entre Gemini y Ollama automáticamente."""
        
        # Opción 1: Gemini (Si hay llave)
        if self.gemini_model:
            try:
                # El SDK de google-generativeai es síncrono por defecto en llamadas simples, 
                # pero gemma4 es para el caso local. Gemini es mucho más rápido.
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens
                    )
                )
                
                # Throttling: Esperar 60 segundos (1 RPM) para asegurar que no chocamos con la cuota.
                # El usuario prefiere máxima seguridad para evitar errores 429.
                import asyncio
                await asyncio.sleep(60)
                
                return response.text.strip()
            except Exception as e:
                if "429" in str(e):
                    logger.warning("⏳ Cuota de Gemini excedida (Rate Limit). Esperando 60 segundos antes de reintentar...")
                    import asyncio
                    await asyncio.sleep(60)
                logger.error(f"Error llamando a Gemini API: {e}. Reintentando con Ollama si es posible...")
                # Si falla Gemini, intentamos fallback a Ollama si está vivo

        # Opción 2: Ollama (Fallback o por defecto)
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": 4096
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.ollama_url}/api/generate", json=payload, timeout=180.0)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()
        except Exception as e:
            logger.error(f"Falla total de IA (Ollama/Gemini): {e}")
            return "Lo siento, todos mis motores de pensamiento están fuera de línea."

    async def ping(self) -> bool:
        """Revisa si al menos un motor de IA responde."""
        if self.gemini_model: return True
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_url}/api/tags", timeout=5.0)
                return response.status_code == 200
        except Exception:
            return False

    async def generate_comment(self, article: ScrapedArticle) -> str:
        """Redacta la noticia de forma profesional."""
        prompt = f"""Escribe una noticia original y profesional sobre tecnología, como si fueras el periodista primario (redactor de "El Tech Criollo").
        
        REGLAS ESTRICTAS:
        1. Escribe en tercera persona de forma clara.
        2. NO actúes como IA, simplemente DA LA NOTICIA.
        3. CITA LA FUENTE OBLIGATORIAMENTE con este enlace exacto: {article.link}
        
        Noticia Base (Título): {article.title}
        Extracto Original: {article.summary[:500]}
        
        Devuelve SOLO la noticia redactada final."""
        
        return await self._call_llm(prompt, temperature=0.8)

    async def generate_reel_script(self, article: ScrapedArticle) -> str:
        """Crea un guion corto para TikTok/Reels."""
        prompt = f"""Escribe un guion explosivo (máximo 45 seg) para un Reel basado en:
        Título: {article.title}
        Contexto: {article.summary[:300]}
        Salida limpia sin anotaciones."""
        
        return await self._call_llm(prompt, temperature=0.9)

    async def is_tech_news(self, article: ScrapedArticle) -> bool | None:
        """Filtro de calidad tech."""
        prompt = f"""Responde únicamente con SI o NO.
¿Es el siguiente artículo estrictamente sobre tecnología emergente, innovación o desarrollo?
Título: {article.title}
Extracto: {article.summary[:500]}
Respuesta:"""
        
        ans = await self._call_llm(prompt, temperature=0.1, max_tokens=10)
        return "SI" in ans.upper()

    async def chat(self, user_message: str) -> str:
        """Chat conversacional con búsqueda e investigación."""
        
        # 1. Definición del Sistema
        system_context = "Eres el asistente inteligente de 'El Tech Criollo'. Tono profesional y experto en tecnología colombiana."
        
        # 2. Investigación (RAG / Internet)
        research_context = ""
        trigger_keywords = ["noticia", "que paso", "últimas", "actualidad", "analiza", "investiga", "manizales"]
        
        if any(w in user_message.lower() for w in trigger_keywords):
            local_news = self.db.get_todays_articles()
            if local_news:
                research_context += "\n--- NOTICIAS LOCALES RECIENTES ---\n"
                for n in local_news[:5]:
                    research_context += f"- {n['title']}: {n['ai_comment'][:200]}...\n"
            
            search_results = await self.search_service.search(user_message, max_results=4)
            research_context += f"\n--- INVESTIGACIÓN EN INTERNET ---\n{search_results}\n"

        prompt = f"""<SYSTEM>{system_context}</SYSTEM>
<CONTEXT>{research_context}</CONTEXT>
<USER>{user_message}</USER>
<ASSISTANT>"""

        return await self._call_llm(prompt)
