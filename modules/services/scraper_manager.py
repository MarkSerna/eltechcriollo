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
                page.wait_for_selector(container_selector, timeout=30000)
                
                # Scroll suave para disparar lazy-loading si existe
                page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                browser.close()
                
                return self._parse_html_content(soup, source)
        except Exception as e:
            logger.error(f"Error en Playwright para {source.name}: {e}")
            return []

    def fetch_wpapi(self, source: SourceConfig) -> List[ScrapedArticle]:
        """Extrae artículos desde una WordPress REST API (wp-json/wp/v2/posts).
        
        Requiere en source.extra:
          - api_base: URL base de la API (ej: https://editorial.forbes.co/wp-json/wp/v2)
          - category_id: int con el ID de categoría a filtrar (opcional)
          - per_page: cantidad de posts a traer (default 15)
        """
        from bs4 import BeautifulSoup as _BS
        extra = source.extra or {}
        api_base = extra.get("api_base", "").rstrip("/")
        category_id = extra.get("category_id", "")
        per_page = extra.get("per_page", 15)

        params = f"per_page={per_page}&_fields=title,link,date,excerpt,jetpack_featured_media_url"
        if category_id:
            params += f"&categories={category_id}"

        url = f"{api_base}/posts?{params}"
        results = []
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            posts = response.json()
            logger.debug(f"[{source.name}] WP API retornó {len(posts)} posts.")
            for post in posts:
                title_raw = post.get("title", {})
                title = title_raw.get("rendered", "") if isinstance(title_raw, dict) else str(title_raw)
                title = _BS(title, "html.parser").get_text(strip=True)

                link = post.get("link", "")

                excerpt_raw = post.get("excerpt", {})
                excerpt = excerpt_raw.get("rendered", "") if isinstance(excerpt_raw, dict) else ""
                summary = _BS(excerpt, "html.parser").get_text(strip=True)

                image_url = post.get("jetpack_featured_media_url") or None

                if title and link:
                    results.append(ScrapedArticle(
                        title=title,
                        link=link,
                        source_name=source.name,
                        region=source.region,
                        summary=summary,
                        image_url=image_url,
                    ))
        except Exception as e:
            logger.error(f"Error en WP API de {source.name} ({url}): {e}", exc_info=True)
        return results

    def fetch_mintic(self, source: SourceConfig) -> List[ScrapedArticle]:
        """Scraper especializado para el portal de noticias de MinTIC (Drupal).
        
        El HTML estático contiene links con el patrón:
          /portal/inicio/Sala-de-prensa/Noticias/XXXXXX:titulo-slug
        Los extrae y construye las URLs absolutas.
        """
        BASE = "https://www.mintic.gov.co"
        results = []
        try:
            response = requests.get(source.url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            seen = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)

                # Solo links que sean noticias internas y con título suficiente
                if ("Sala-de-prensa/Noticias/" not in href
                        or len(text) < 20
                        or href.endswith("/Sala-de-prensa/Noticias/")
                        or "#" in href):
                    continue

                full_link = href if href.startswith("http") else BASE + href
                if full_link in seen:
                    continue
                seen.add(full_link)

                # Buscar imagen en el elemento padre o hermano cercano
                parent = a.parent
                img_node = parent.find("img") if parent else None
                image_url = None
                if img_node:
                    image_url = img_node.get("src") or img_node.get("data-src")
                    if image_url and not image_url.startswith("http"):
                        image_url = BASE + image_url

                results.append(ScrapedArticle(
                    title=text,
                    link=full_link,
                    source_name=source.name,
                    region=source.region,
                    summary="",
                    image_url=image_url,
                ))

            logger.debug(f"[{source.name}] MinTIC extrajo {len(results)} noticias.")
        except Exception as e:
            logger.error(f"Error en scraper MinTIC ({source.url}): {e}", exc_info=True)
        return results

    def fetch_sharepoint(self, source: SourceConfig) -> List[ScrapedArticle]:
        """Scraper para portales SharePoint como Fondo Emprender.

        Extrae noticias usando Playwright y busca links con el patrón
        DispForm.aspx?id=XXXX que usa SharePoint para ver ítems de lista.
        """
        BASE = "https://www.fondoemprender.com"
        results = []
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=self.headers["User-Agent"])
                page.goto(source.url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(2000)
                # Scroll suave para disparar lazy load
                for _ in range(2):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(800)
                content = page.content()
                browser.close()

            soup = BeautifulSoup(content, "html.parser")
            seen = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)
                if ("DispForm.aspx" not in href or len(text) < 15
                        or text.lower().startswith("turn")):
                    continue
                full = href if href.startswith("http") else BASE + href
                if full in seen:
                    continue
                seen.add(full)

                parent = a.parent
                img_node = parent.find("img") if parent else None
                image_url = None
                if img_node:
                    image_url = img_node.get("src") or img_node.get("data-src")
                    if image_url and not image_url.startswith("http"):
                        image_url = BASE + image_url

                results.append(ScrapedArticle(
                    title=text,
                    link=full,
                    source_name=source.name,
                    region=source.region,
                    summary="",
                    image_url=image_url,
                ))

            logger.debug(f"[{source.name}] SharePoint extrajo {len(results)} noticias.")
        except Exception as e:
            logger.error(f"Error en scraper SharePoint ({source.url}): {e}", exc_info=True)
        return results

    def fetch_sena(self, source: SourceConfig) -> List[ScrapedArticle]:
        """Scraper para el portal de noticias del SENA.

        El SENA usa SharePoint y los artículos siguen el patrón:
          /es-co/Noticias/Paginas/noticia.aspx?IdNoticia=XXXX
        Se carga desde el home con Playwright (networkidle + timeout parcial).
        """
        BASE = "https://www.sena.edu.co"
        results = []
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=self.headers["User-Agent"])
                # El SENA es lento — usamos domcontentloaded y esperamos poco más
                try:
                    page.goto(source.url, wait_until="domcontentloaded", timeout=45000)
                except Exception:
                    pass  # Si hace timeout parcial, igual extraemos lo que cargó
                page.wait_for_timeout(3000)
                content = page.content()
                browser.close()

            soup = BeautifulSoup(content, "html.parser")
            seen = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)

                if (("IdNoticia=" not in href and "noticia.aspx" not in href)
                        or len(text) < 20):
                    continue

                full = href if href.startswith("http") else BASE + href
                if full in seen:
                    continue
                seen.add(full)

                parent = a.parent
                img_node = parent.find("img") if parent else None
                image_url = None
                if img_node:
                    image_url = img_node.get("src") or img_node.get("data-src")
                    if image_url and not image_url.startswith("http"):
                        image_url = BASE + image_url

                results.append(ScrapedArticle(
                    title=text,
                    link=full,
                    source_name=source.name,
                    region=source.region,
                    summary="",
                    image_url=image_url,
                ))

            logger.debug(f"[{source.name}] SENA extrajo {len(results)} noticias.")
        except Exception as e:
            logger.error(f"Error en scraper SENA ({source.url}): {e}", exc_info=True)
        return results

    def fetch(self, source: SourceConfig) -> List[ScrapedArticle]:
        """Delega automáticamente la petición basada en el tipo de fuente configurado."""
        if source.type == 'rss':
            return self.fetch_rss(source)
        elif source.type == 'html':
            return self.fetch_html(source)
        elif source.type == 'dynamic':
            return self.fetch_dynamic(source)
        elif source.type == 'wpapi':
            return self.fetch_wpapi(source)
        elif source.type == 'sharepoint':
            return self.fetch_sharepoint(source)
        elif source.type == 'sena':
            return self.fetch_sena(source)
        elif source.type == 'mintic':
            return self.fetch_mintic(source)
        else:
            logger.warning(f"Tipo desconocido de fuente '{source.type}' para {source.name}")
            return []
