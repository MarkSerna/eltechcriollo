import json
import asyncio
import re
from dotenv import load_dotenv

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

# Concurrency limits
# Avoid blasting Ollama with dozens of heavy inferences simultaneously
ai_semaphore = asyncio.Semaphore(2)

async def main_orchestrator():
    """Lógica principal de orquestación 100% asíncrona y ultrarrápida."""
    logger.info("=========================================")
    logger.info("🤖 Iniciando Orquestador El Tech Criollo (ASYNC)")
    logger.info("=========================================")
    
    db_manager = DatabaseManager()
    await asyncio.to_thread(db_manager.initialize_schema)
    
    scraper_manager = ScraperManager()
    report_manager = ReportManager()
    notification_manager = NotificationManager()
    ai_manager = AIManager()
    
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
        
    logger.info(f"Se cargaron correctamente {len(sources)} fuentes para escanear en paralelo.")
    
    filtered_and_novel_articles = []
    
    async def process_source(source):
        logger.info(f"🕷 Escaneando: {source.name} via {source.type.upper()}")
        articles = await scraper_manager.fetch(source)
        
        valid_source_articles = []
        
        # Pasa 1: Filtro de Novedad BATCH (No estar en BD)
        urls = [a.link for a in articles]
        processed_urls = await asyncio.to_thread(db_manager.get_processed_urls, urls)
        
        for article in articles:
            if article.link in processed_urls:
                continue

            # Pasa 2: Filtro Semántico/Palabras Calientes
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
                async with ai_semaphore:
                    is_tech_ai = await ai_manager.is_tech_news(article)
                    
                if is_tech_ai is True:
                    is_valid = True
                elif is_tech_ai is False:
                    is_valid = False
                    logger.debug(f"❌ Rechazado por IA (No es tech): {article.title}")
                else:
                    has_strict = has_keyword(config.scraper.strict_keywords, content)
                    supporting_count = sum(1 for kw in config.scraper.supporting_keywords if re.search(r'\b' + re.escape(kw.lower()) + r'\b', content))
                    if not (has_strict or supporting_count >= 2):
                        is_valid = False
                        logger.debug(f"❌ Rechazado por Fallback: {article.title}")

            if is_valid:
                def do_translate(text):
                    try:
                        return GoogleTranslator(source='auto', target='es').translate(text)
                    except Exception as e:
                        logger.warning(f"Error ocasional traduciendo: {e}")
                        return None
                        
                translated_title = await asyncio.to_thread(do_translate, article.title)
                if translated_title:
                    article.title = translated_title

                if article.region == "colombia":
                    article.department = department_detector.detect(article.title, article.summary or "")
                    if article.department:
                        logger.debug(f"📍 Departamento detectado: {article.department}")

                logger.info(f"🤖 Invocando Inteligencia Artificial OLLAMA para: {article.title[:20]}...")
                
                async with ai_semaphore:
                    # Invocamos en paralelo la petición del comentario y la del reel a Ollama
                    comment, reel = await asyncio.gather(
                        ai_manager.generate_comment(article),
                        ai_manager.generate_reel_script(article)
                    )
                    article.ai_comment = comment
                    article.reel_script = reel

                # Anotamos en base de datos
                success = await asyncio.to_thread(db_manager.mark_as_processed, article)
                if success:
                    valid_source_articles.append(article)
                    logger.debug(f"+ Aceptado y Comentado: {article.title}")
                    
        return valid_source_articles

    # Esperamos a que todas las fuentes terminen en paralelo
    results = await asyncio.gather(*[process_source(src) for src in sources])
    for res_list in results:
        filtered_and_novel_articles.extend(res_list)
                    
    logger.info(f"Total de noticias potentes extraídas hoy: {len(filtered_and_novel_articles)}")
    
    # 4. Reportabilidad
    report_path = await asyncio.to_thread(report_manager.generate_markdown, filtered_and_novel_articles)
    
    # 5. Notificación Multi-canal
    if report_path:
        await notification_manager.send_discord_file(report_path)
        await notification_manager.send_telegram_file(report_path)
        
        for article in filtered_and_novel_articles[:5]:
            await notification_manager.send_telegram_visual_news(article)
        
    logger.info("🏁 Orquestación asíncrona finalizada exitosamente.")
    return filtered_and_novel_articles

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main_orchestrator()))
