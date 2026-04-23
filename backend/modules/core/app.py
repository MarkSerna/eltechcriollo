import json
import asyncio
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
from modules.services import tech_filter as TechFilter
from deep_translator import GoogleTranslator

# Concurrency limits
# Avoid blasting Ollama with dozens of heavy inferences simultaneously
ai_semaphore = asyncio.Semaphore(2)

async def repair_placeholder_articles(db_manager, ai_manager):
    """Ciclo de reparación de noticias con análisis fallidos."""
    placeholder = "Análisis en progreso: El robot está procesando los detalles técnicos de esta noticia de alto impacto."
    articles_data = await asyncio.to_thread(db_manager.get_articles_with_placeholder, placeholder, 5)
    
    if not articles_data:
        return
        
    logger.info(f"🔧 Iniciando ciclo de reparación: {len(articles_data)} noticias detectadas con placeholder.")
    
    from modules.models.source import ScrapedArticle
    
    for data in articles_data:
        article = ScrapedArticle(
            title=data['title'],
            link=data['link'],
            source_name=data['source_name'],
            region=data['region'],
            department=data['department'],
            image_url=data['image_url'],
            summary=data['title'] 
        )
        
        async with ai_semaphore:
            logger.info(f"♻️ Re-generando análisis para: {article.title[:20]}...")
            # Peticiones en paralelo
            results = await asyncio.gather(
                ai_manager.generate_comment(article),
                ai_manager.generate_reel_script(article),
                return_exceptions=True
            )
            
            comment = results[0] if not isinstance(results[0], Exception) else None
            reel = results[1] if not isinstance(results[1], Exception) else ""
            
            if comment and placeholder not in comment:
                success = await asyncio.to_thread(
                    db_manager.update_article_ai_content, 
                    article.link, 
                    comment, 
                    str(reel)
                )
                if success:
                    logger.info(f"✅ Noticia reparada con éxito: {article.title[:40]}")
                    # Notificar a Telegram inmediatamente tras la reparación
                    article.ai_comment = comment
                    article.reel_script = reel
                    from modules.services.notification_manager import NotificationManager
                    nm = NotificationManager()
                    sent = await nm.send_telegram_visual_news(article)
                    if sent:
                        await asyncio.to_thread(db_manager.mark_as_sent_to_telegram, article.link)
                        logger.info(f"📲 Noticia reparada enviada a Telegram: {article.title[:40]}")
            else:
                logger.warning(f"⚠️ Reintento de IA fallido para: {article.title[:40]}")

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
    
    # Cargar fuentes desde la Base de Datos
    db_sources = await asyncio.to_thread(db_manager.get_all_sources)
    sources = []
    for s_dict in db_sources:
        if not s_dict.get("is_active", True):
            continue
        try:
            sources.append(SourceConfig.from_dict(s_dict))
        except Exception as e:
            logger.error(f"Error cargando configuración para fuente {s_dict.get('name')}: {e}")
            
    if not sources:
        logger.warning("⚠️ No se encontraron fuentes activas para procesar.")
        return []
        
    logger.info(f"Se cargaron correctamente {len(sources)} fuentes para escanear en paralelo.")
    
    filtered_and_novel_articles = []
    
    async def process_source(source):
        from datetime import datetime, timedelta
        logger.info(f"🕷 Escaneando: {source.name} via {source.type.upper()}")
        articles = await scraper_manager.fetch(source)
        
        valid_source_articles = []
        recent_threshold = datetime.utcnow() - timedelta(days=3)
        
        # Pasa 1: Filtro de Novedad BATCH (No estar en BD)
        urls = [a.link for a in articles]
        processed_urls = await asyncio.to_thread(db_manager.get_processed_urls, urls)
        
        for article in articles:
            if article.link in processed_urls:
                continue
            
            # Pasa 1.5: Filtro de Fecha (si está disponible en el modelo)
            if article.pub_date and article.pub_date < recent_threshold:
                logger.debug(f"⏩ [{source.name}] Omitiendo por antigüedad: {article.title[:40]}")
                continue

            # Pasa 2: Filtro TechFilter (scoring ponderado + exclusión negativa)
            content = article.get_content_snapshot()
            require_ai = getattr(source, 'require_ai', False)

            send_to_ai, tf_score, tf_reason = TechFilter.needs_ai_validation(content, require_ai)

            # Si el score es 0 y es fuente require_ai → descarte inmediato sin consultar IA
            if not send_to_ai and tf_score == 0 and require_ai:
                logger.debug(f"⛔ [{source.name}] Sin señal tech. Descartado antes de IA: {article.title[:60]}")
                continue

            # Si no requiere IA y el score ya supera el umbral → pasa directamente
            is_valid = False
            if not require_ai and not send_to_ai and tf_score >= 5:
                is_valid = True
                logger.debug(f"✅ [{source.name}] Pasa filtro keyword (score={tf_score}): {article.title[:60]}")
            elif send_to_ai or (not require_ai and tf_score >= 1):
                # Hay señal tech o fuente requiere IA → consultar modelo
                async with ai_semaphore:
                    is_tech_ai = await ai_manager.is_tech_news(article)

                if is_tech_ai is True:
                    is_valid = True
                elif is_tech_ai is False:
                    is_valid = False
                    logger.debug(f"❌ [{source.name}] Rechazado por IA: {article.title[:60]}")
                else:
                    # Ollama no disponible — fallback más estricto: score >= 5
                    if require_ai:
                        is_valid = False  # Fuentes require_ai NUNCA pasan sin IA
                        logger.debug(f"⛔ [{source.name}] Ollama no disponible. Fuente require_ai → descartado: {article.title[:60]}")
                    else:
                        is_valid = tf_score >= 5
                        logger.debug(f"{'✅' if is_valid else '❌'} [{source.name}] Ollama no disponible. Fallback score={tf_score}: {article.title[:60]}")

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
                    # Invocamos en paralelo la petición del comentario y la del reel a Ollama/Gemini
                    results = await asyncio.gather(
                        ai_manager.generate_comment(article),
                        ai_manager.generate_reel_script(article),
                        return_exceptions=True
                    )
                    comment = results[0] if not isinstance(results[0], Exception) else None
                    reel = results[1] if not isinstance(results[1], Exception) else ""

                    # Fallbacks si la IA falla (cuota excedida o caída)
                    article.ai_comment = comment or "Análisis en progreso: El robot está procesando los detalles técnicos de esta noticia de alto impacto."
                    article.reel_script = reel or "Guión no disponible momentáneamente por alta demanda de procesamiento."

                # Si no hay imagen disponible, capturar un screenshot de fallback
                if not article.image_url:
                    import hashlib
                    url_hash = hashlib.md5(article.link.encode('utf-8')).hexdigest()
                    logger.info(f"📸 Tomando captura de pantalla de respaldo para: {article.title[:20]}...")
                    fallback_img = await scraper_manager.capture_screenshot(article.link, url_hash)
                    if fallback_img:
                        article.image_url = fallback_img

                # Anotamos en base de datos
                success = await asyncio.to_thread(db_manager.mark_as_processed, article)
                if success:
                    valid_source_articles.append(article)
                    logger.debug(f"+ Aceptado y Comentado: {article.title}")
                    
        return valid_source_articles

    # Proceso SECUENCIAL con retraso para respetar la cuota de la IA (Solicitud del usuario)
    results = []
    for src in sources:
        try:
            res_list = await process_source(src)
            results.append(res_list)
            # Pequeña pausa entre fuentes para no saturar la API
            await asyncio.sleep(5) 
        except Exception as e:
            logger.error(f"Falla procesando fuente {src.name}: {e}")

    for res_list in results:
        filtered_and_novel_articles.extend(res_list)
                    
    logger.info(f"Total de noticias potentes extraídas hoy: {len(filtered_and_novel_articles)}")
    
    # 4. Reportabilidad
    report_path = await asyncio.to_thread(report_manager.generate_markdown, filtered_and_novel_articles)
    
    # 5. Notificación Multi-canal (Solo si hay novedades potentes)
    if report_path and filtered_and_novel_articles:
        await notification_manager.send_discord_file(report_path)
        
        # Notificar las top 10 al canal de Telegram directo
        # Evitar enviar noticias que tengan el mensaje de "placeholder" (esperarán a la reparación)
        news_to_send = [a for a in filtered_and_novel_articles if "Análisis en progreso" not in a.ai_comment][:10]
        
        for article in news_to_send:
            success = await notification_manager.send_telegram_visual_news(article)
            if success:
                await asyncio.to_thread(db_manager.mark_as_sent_to_telegram, article.link)
            
    # 6. Auto-reparación de fallos previos
    await repair_placeholder_articles(db_manager, ai_manager)
        
    logger.info("🏁 Orquestación secuencial finalizada exitosamente.")
    return filtered_and_novel_articles

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main_orchestrator()))
