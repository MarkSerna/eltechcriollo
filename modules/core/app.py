import json
from dotenv import load_dotenv

# Cargar variables de entorno primordiales
load_dotenv()

from modules.models.config import config
from modules.models.source import SourceConfig
from modules.utils.logger import logger

from modules.services.database_manager import DatabaseManager
from modules.services.scraper_manager import ScraperManager
from modules.services.report_manager import ReportManager
from modules.services.notification_manager import NotificationManager
from modules.services.ai_manager import AIManager
from deep_translator import GoogleTranslator

def main_orchestrator():
    """Lógica principal de orquestación, aislada y sin acoplamiento a scripts en crudo."""
    logger.info("=========================================")
    logger.info("🤖 Iniciando Orquestador El Dev Criollo")
    logger.info("=========================================")
    
    # 1. Inicialización e Indentificación de dependencias
    db_manager = DatabaseManager()
    scraper_manager = ScraperManager()
    report_manager = ReportManager()
    notification_manager = NotificationManager()
    ai_manager = AIManager()
    
    db_manager.initialize_schema()
    
    # 2. Cargar Fuentes de Datos
    sources_path = config.paths.sources_path
    if not sources_path.exists():
        logger.error(f"El archivo de fuentes no existe en la ruta configurada: {sources_path}")
        return []
        
    try:
        with open(sources_path, 'r', encoding='utf-8') as f:
            raw_sources = json.load(f)
            sources = [SourceConfig(**src) for src in raw_sources]
    except Exception as e:
        logger.error(f"Error interpretando sources.json: {e}")
        return []
        
    logger.info(f"Se cargaron correctamente {len(sources)} fuentes para escanear.")
    
    # 3. Escanear e Inteligencia Cautelosa
    filtered_and_novel_articles = []
    
    for source in sources:
        logger.info(f"🕷 Escaneando: {source.name} via {source.type.upper()}")
        articles = scraper_manager.fetch(source)
        
        for article in articles:
            # Pasa 1: Filtro de Novedad (No estar en BD)
            if db_manager.is_processed(article.link):
                continue
                
            # Pasa 2: Filtro Semántico/Palabras Calientes
            content = article.get_content_snapshot()
            if any(kw.lower() in content for kw in config.scraper.keywords):
                
                # TRADUCCIÓN: Convertimos automáticamente títulos en inglés al español
                try:
                    translated_title = GoogleTranslator(source='auto', target='es').translate(article.title)
                    if translated_title:
                        article.title = translated_title
                except Exception as e:
                    logger.warning(f"Error ocasional traduciendo título {article.title[:15]}: {e}")

                # REEMPLAZO AI: Pedimos opinión al modelo Local de cada noticia valiosa
                logger.info(f"🤖 Invocando Inteligencia Artificial OLLAMA para: {article.title[:20]}...")
                article.ai_comment = ai_manager.generate_comment(article)
                
                # REEL SCRIPT: Guion viral para TikTok y YouTube
                logger.info(f"🎬 Escribiendo guion TikTok para: {article.title[:20]}...")
                article.reel_script = ai_manager.generate_reel_script(article)
                
                # Anotamos en base de datos el modelo completo (para UI y evitar duplicados)
                if db_manager.mark_as_processed(article):
                    filtered_and_novel_articles.append(article)
                    logger.debug(f"+ Aceptado y Comentado: {article.title}")
                    
    logger.info(f"Total de noticias potentes extraídas hoy: {len(filtered_and_novel_articles)}")
    
    # 4. Reportabilidad
    report_path = report_manager.generate_markdown(filtered_and_novel_articles)
    
    # 5. Notificación Multi-canal
    if report_path:
        notification_manager = NotificationManager()
        # 5a. Enviar el reporte completo (Discord / Telegram File)
        notification_manager.send_discord_file(report_path)
        notification_manager.send_telegram_file(report_path)
        
        # 5b. Enviar noticias destacadas visualmente (Limitado a 5 para evitar spam)
        # Solo enviamos las que acabamos de filtrar como novedosas en esta sesión
        for article in filtered_and_novel_articles[:5]:
            notification_manager.send_telegram_visual_news(article)
        
    logger.info("🏁 Orquestación finalizada exitosamente.")
    return filtered_and_novel_articles

if __name__ == "__main__":
    import sys
    sys.exit(main_orchestrator())
