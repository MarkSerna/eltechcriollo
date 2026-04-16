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
from modules.services import department_detector
from deep_translator import GoogleTranslator

def main_orchestrator():
    """Lógica principal de orquestación, aislada y sin acoplamiento a scripts en crudo."""
    logger.info("=========================================")
    logger.info("🤖 Iniciando Orquestador El Tech Criollo")
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
            sources = [SourceConfig.from_dict(src) for src in raw_sources]
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
            import re
            content = article.get_content_snapshot().lower()
            
            def has_keyword(kw_list, text):
                for kw in kw_list:
                    kw_lower = kw.lower()
                    if len(kw_lower) <= 3:
                        if re.search(r'\b' + re.escape(kw_lower) + r'\b', text):
                            return True
                    else:
                        if re.search(r'\b' + re.escape(kw_lower) + r'(s|es|a|o|as|os)?\b', text):
                            return True
                return False

            is_valid = has_keyword(config.scraper.keywords, content)
            
            if is_valid and article.region == "colombia":
                is_tech_ai = ai_manager.is_tech_news(article)
                if is_tech_ai is True:
                    is_valid = True
                elif is_tech_ai is False:
                    is_valid = False
                    logger.debug(f"❌ Rechazado por IA (No es tech puramente): {article.title}")
                else:
                    has_strict = has_keyword(config.scraper.strict_keywords, content)
                    supporting_count = sum(1 for kw in config.scraper.supporting_keywords if re.search(r'\b' + re.escape(kw.lower()) + r'\b', content))
                    if not (has_strict or supporting_count >= 2):
                        is_valid = False
                        logger.debug(f"❌ Rechazado por Fallback (No es tech): {article.title}")

            if is_valid:

                # TRADUCCIÓN: Convertimos automáticamente títulos en inglés al español
                try:
                    translated_title = GoogleTranslator(source='auto', target='es').translate(article.title)
                    if translated_title:
                        article.title = translated_title
                except Exception as e:
                    logger.warning(f"Error ocasional traduciendo título {article.title[:15]}: {e}")

                # DETECCIÓN DE DEPARTAMENTO: Solo para noticias colombianas
                if article.region == "colombia":
                    article.department = department_detector.detect(
                        article.title, article.summary or ""
                    )
                    if article.department:
                        logger.debug(f"📍 Departamento detectado: {article.department} → {article.title[:40]}")

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
