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
        self.provider = config.ai.ai_provider.lower()
        self.gemini_cooldown = config.ai.gemini_cooldown
        self.db = DatabaseManager()
        self.search_service = SearchManager()
        
        # Configurar Gemini si hay llave disponible
        if self.gemini_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.gemini_key)
            self.gemini_model = genai.GenerativeModel('gemini-3-flash-preview')
            if self.provider == "gemini":
                logger.info("⚡ IA de Google Gemini configurada como Proveedor Principal (Cloud).")
            else:
                logger.info("⚡ IA de Google Gemini configurada como Proveedor de Fallback.")
        else:
            self.gemini_model = None

    async def _call_llm(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """Helper para decidir entre Gemini y Ollama basado en configuración."""
        
        # Lógica de Prioridades
        # 1. Si el proveedor es 'gemini', intentamos Gemini -> Ollama (Fallback)
        # 2. Si el proveedor es 'local', intentamos Ollama -> Gemini (Fallback)
        
        first_attempt = self.provider
        
        if first_attempt == "gemini":
            response = await self._try_gemini(prompt, temperature, max_tokens)
            if response: return response
            return await self._try_ollama(prompt, temperature, max_tokens)
        else:
            response = await self._try_ollama(prompt, temperature, max_tokens)
            if response: return response
            return await self._try_gemini(prompt, temperature, max_tokens)

    async def _try_gemini(self, prompt: str, temperature: float, max_tokens: int, retries: int = 3) -> str | None:
        """Intento de llamada a Gemini con manejo de cuota y reintentos automáticos."""
        if not self.gemini_model:
            return None
            
        for attempt in range(retries):
            try:
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens
                    )
                )
                
                # Cooldown configurable para respetar RPM
                if self.gemini_cooldown > 0:
                    import asyncio
                    await asyncio.sleep(self.gemini_cooldown)
                
                self.db.log_ai_usage("gemini", "success")
                return response.text.strip()
            except Exception as e:
                err_str = str(e)
                if "429" in err_str:
                    self.db.log_ai_usage("gemini", "429")
                    wait_time = (attempt + 1) * 10
                    logger.warning(f"⏳ Cuota excedida (429). Reintentando en {wait_time}s... (Intento {attempt+1}/{retries})")
                    import asyncio
                    await asyncio.sleep(wait_time)
                    continue # Reintentar
                
                logger.error(f"Error llamando a Gemini API: {err_str}")
                break # Otro error, no reintentar
                
        return None

    async def _try_ollama(self, prompt: str, temperature: float, max_tokens: int) -> str | None:
        """Intento de llamada a Ollama Local, silenciado en entornos donde no existe."""
        # Evitar inundar logs si sabemos que no está disponible (ej. Render)
        if getattr(self, '_ollama_failed_dns', False):
            return None

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
                self.db.log_ai_usage("ollama", "success")
                return data.get("response", "").strip()
        except Exception as e:
            err_str = str(e)
            if "Name or service not known" in err_str or "ConnectionRefusedError" in err_str:
                self._ollama_failed_dns = True # Desactivar para esta sesión
                logger.debug("🔕 Ollama no disponible (Localhost no encontrado). Fallback desactivado.")
            else:
                self.db.log_ai_usage("ollama", "error")
                logger.debug(f"Info: Ollama fallback omitido: {err_str}")
            return None

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
        4. Devuelve el texto en formato PLANO, SIN Markdown (no uses asteriscos ni negritas).
        
        Noticia Base (Título): {article.title}
        Extracto Original: {article.summary[:500]}
        
        Devuelve SOLO la noticia redactada final. No incluyas títulos extra."""
        
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

    async def reprocess_article_by_url(self, url: str) -> bool:
        """Regenera el contenido de IA para un artículo específico y actualiza la BD."""
        article_data = await asyncio.to_thread(self.db.get_article_by_url, url)
        if not article_data:
            return False
            
        # Reconstruir el objeto ScrapedArticle
        # Nota: Usamos el título como resumen para el re-procesamiento si el resumen original no está disponible
        article = ScrapedArticle(
            title=article_data.get('title'),
            link=article_data.get('url'),
            source_name=article_data.get('source'),
            summary=article_data.get('title') 
        )
        article.region = article_data.get('region')
        article.department = article_data.get('department')
        article.image_url = article_data.get('image_url')
        
        # Generar contenido
        import asyncio
        results = await asyncio.gather(
            self.generate_comment(article),
            self.generate_reel_script(article),
            return_exceptions=True
        )
        
        comment = results[0] if not isinstance(results[0], Exception) else None
        reel = results[1] if not isinstance(results[1], Exception) else ""
        
        if comment:
            return await asyncio.to_thread(self.db.update_article_ai_content, url, comment, str(reel))
        return False
