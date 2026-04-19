from duckduckgo_search import DDGS
from modules.utils.logger import logger

class SearchManager:
    """Servicio para realizar búsquedas rápidas en internet usando DuckDuckGo."""
    
    def __init__(self):
        self.ddgs = DDGS()

    async def search(self, query: str, max_results: int = 5) -> str:
        """Busca en internet y devuelve un resumen textual de los resultados."""
        logger.info(f"🔍 Investigando en internet: {query}")
        try:
            # duckduckgo-search es síncrono por defecto, pero DDGS soporta context manager
            results = []
            with DDGS() as ddgs:
                ddgs_gen = ddgs.text(query, region='wt-wt', safesearch='moderate', timelimit='y', max_results=max_results)
                for r in ddgs_gen:
                    results.append(f"- {r['title']}: {r['body']} (Fuente: {r['href']})")
            
            if not results:
                return "No se encontraron resultados recientes en internet."
            
            return "\n".join(results)
            
        except Exception as e:
            logger.error(f"Error investigando en internet: {e}")
            return f"Hubo un error en la investigación: {e}"

    async def get_news(self, query: str, max_results: int = 5) -> str:
        """Busca específicamente en la sección de noticias."""
        logger.info(f"📰 Buscando noticias frescas sobre: {query}")
        try:
            results = []
            with DDGS() as ddgs:
                ddgs_gen = ddgs.news(query, region='wt-wt', safesearch='moderate', timelimit='m', max_results=max_results)
                for r in ddgs_gen:
                    results.append(f"- {r['title']} ({r['date']}): {r['body']} (Link: {r['url']})")
            
            if not results:
                return "No hay noticias de última hora sobre este tema."
            
            return "\n".join(results)
        except Exception as e:
            logger.error(f"Error buscando noticias: {e}")
            return f"Error en búsqueda de noticias: {e}"
