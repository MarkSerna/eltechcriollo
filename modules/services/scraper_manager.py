import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Optional

from modules.utils.logger import logger
from modules.models.config import config
from modules.models.source import SourceConfig, ScrapedArticle

class ScraperManager:
    """Clase principal que aísla la lógica de HTTP requests y parsing."""
    
    def __init__(self):
        self.headers = {
            "User-Agent": config.scraper.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        self.timeout = config.scraper.timeout

    def _extract_image_from_entry(self, entry) -> Optional[str]:
        """Intenta encontrar una imagen en una entrada de feed RSS."""
        # 1. Buscar en media_content (estándar común)
        if 'media_content' in entry:
            for media in entry.media_content:
                if media.get('type', '').startswith('image/') or media.get('medium') == 'image':
                    return media.get('url')
        
        # 2. Buscar en enclosures
        if 'enclosures' in entry:
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('image/'):
                    return enclosure.get('href')
                    
        # 3. Buscar en links
        if 'links' in entry:
            for link in entry.links:
                if link.get('type', '').startswith('image/'):
                    return link.get('href')

        # 4. Fallback: buscar en el contenido HTML (summary o description)
        content = entry.get('summary', '') + entry.get('content', [{}])[0].get('value', '')
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            img = soup.find('img')
            if img and img.get('src'):
                return img.get('src')
                
        return None

    def fetch_rss(self, source: SourceConfig) -> List[ScrapedArticle]:
        """Extrae la información básica de un feed RSS mediante feedparser y añade filtro de tiempo e imágenes."""
        from datetime import datetime, timedelta
        import time
        results = []
        try:
            feed = feedparser.parse(source.url)
            logger.debug(f"[{source.name}] RSS extrajo {len(feed.entries)} entradas brutas.")
            
            one_week_ago = datetime.utcnow() - timedelta(days=7)
            
            for entry in feed.entries:
                title = entry.get('title', '')
                link = entry.get('link', '')
                summary = entry.get('summary', '')
                
                # Extraer imagen
                image_url = self._extract_image_from_entry(entry)
                
                # Filtro agresivo: Si es Colombia, rechazar lo que tenga más de 1 semana de antigüedad
                if source.region == "colombia":
                    pub_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
                    if pub_parsed:
                        pub_date = datetime.fromtimestamp(time.mktime(pub_parsed))
                        if pub_date < one_week_ago:
                            continue # Noticia muy vieja descartada
                
                if title and link:
                    results.append(ScrapedArticle(
                        title=title,
                        link=link,
                        source_name=source.name,
                        region=source.region,
                        summary=summary,
                        image_url=image_url
                    ))
        except Exception as e:
            logger.error(f"Error en RSS de {source.name} ({source.url}): {e}", exc_info=True)
            
        return results

    def _parse_html_content(self, soup: BeautifulSoup, source: SourceConfig) -> List[ScrapedArticle]:
        """Lógica común para extraer artículos de un objeto BeautifulSoup."""
        results = []
        selectors = source.selectors or {}
        container_selector = selectors.get("container", "article")
        title_selector = selectors.get("title", "h2")
        link_selector = selectors.get("link", "a")
        image_selector = selectors.get("image", "img")
        
        articles = soup.select(container_selector)
        for article in articles:
            # Título
            title_node = article.select_one(title_selector) if title_selector else article
            title = title_node.get_text(strip=True) if title_node else ""
            
            # Enlace
            link_node = article if not link_selector else article.select_one(link_selector)
            link = None
            if link_node and link_node.has_attr('href'):
                link = link_node.get('href')
            elif article.has_attr('href'):
                link = article.get('href')
            
            # Imagen
            image_url = None
            img_node = article.select_one(image_selector)
            if img_node:
                image_url = img_node.get('src') or img_node.get('data-src')

            if title and link:
                if not link.startswith("http"):
                    link = urljoin(source.url, link)
                if image_url and not image_url.startswith("http"):
                    image_url = urljoin(source.url, image_url)
                    
                results.append(ScrapedArticle(
                    title=title,
                    link=link,
                    source_name=source.name,
                    region=source.region,
                    summary="",
                    image_url=image_url
                ))
        return results

    def fetch_html(self, source: SourceConfig) -> List[ScrapedArticle]:
        """Extrae la información a partir de sitios estáticos usando requests."""
        try:
            response = requests.get(source.url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._parse_html_content(soup, source)
        except Exception as e:
            logger.error(f"Error en parseo estático de {source.name}: {e}")
            return []

    def fetch_dynamic(self, source: SourceConfig) -> List[ScrapedArticle]:
        """Extrae información de sitios que requieren renderizado de JS usando Playwright."""
        from playwright.sync_api import sync_playwright
        results = []
        try:
            with sync_playwright() as p:
                # Lanzar navegador con User-Agent para saltar protecciones
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=self.headers["User-Agent"])
                page = context.new_page()
                
                logger.info(f"🌐 [Playwright] Navegando a fuente dinámica: {source.name}")
                page.goto(source.url, wait_until="networkidle", timeout=60000)
                
                # Esperar a que el contenedor principal sea visible
                selectors = source.selectors or {}
                container_selector = selectors.get("container", "article")
                page.wait_for_selector(container_selector, timeout=20000)
                
                # Scroll suave para disparar lazy-loading si existe
                page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                browser.close()
                
                return self._parse_html_content(soup, source)
        except Exception as e:
            logger.error(f"Error en Playwright para {source.name}: {e}")
            return []

    def fetch(self, source: SourceConfig) -> List[ScrapedArticle]:
        """Delega automáticamente la petición basada en el tipo de fuente configurado."""
        if source.type == 'rss':
            return self.fetch_rss(source)
        elif source.type == 'html':
            return self.fetch_html(source)
        elif source.type == 'dynamic':
            return self.fetch_dynamic(source)
        else:
            logger.warning(f"Tipo desconocido de fuente '{source.type}' para {source.name}")
            return []
