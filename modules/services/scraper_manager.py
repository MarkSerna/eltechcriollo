import httpx
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Optional

from modules.utils.logger import logger
from modules.models.config import config
from modules.models.source import SourceConfig, ScrapedArticle

class ScraperManager:
    """Clase principal que aísla la lógica HTTP/Browser asíncrona y parsing."""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Ch-Ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "\"Windows\"",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Upgrade-Insecure-Requests": "1"
        }
        self.timeout = float(config.scraper.timeout)

    def _extract_image_from_entry(self, entry) -> Optional[str]:
        if 'media_content' in entry:
            for media in entry.media_content:
                if media.get('type', '').startswith('image/') or media.get('medium') == 'image':
                    return media.get('url')
        
        if 'enclosures' in entry:
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('image/'):
                    return enclosure.get('href')
                    
        if 'links' in entry:
            for link in entry.links:
                if link.get('type', '').startswith('image/'):
                    return link.get('href')

        content = entry.get('summary', '') + entry.get('content', [{}])[0].get('value', '')
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            img = soup.find('img')
            if img and img.get('src'):
                return img.get('src')
                
        return None

    async def fetch_rss(self, source: SourceConfig) -> List[ScrapedArticle]:
        """Extrae la información asíncronamente vía httpx y parsea con feedparser."""
        from datetime import datetime, timedelta
        import time
        results = []
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(source.url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                
            feed = feedparser.parse(response.content)
            logger.debug(f"[{source.name}] RSS extrajo {len(feed.entries)} entradas brutas.")
            
            one_week_ago = datetime.utcnow() - timedelta(days=7)
            
            for entry in feed.entries:
                title = entry.get('title', '')
                link = entry.get('link', '')
                summary = entry.get('summary', '')
                image_url = self._extract_image_from_entry(entry)
                
                if source.region == "colombia":
                    pub_parsed = entry.get('published_parsed') or entry.get('updated_parsed')
                    if pub_parsed:
                        pub_date = datetime.fromtimestamp(time.mktime(pub_parsed))
                        if pub_date < one_week_ago:
                            continue
                
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
            logger.error(f"Error en RSS de {source.name} ({source.url}): {e}")
            
        return results

    def _parse_html_content(self, soup: BeautifulSoup, source: SourceConfig) -> List[ScrapedArticle]:
        results = []
        selectors = source.selectors or {}
        container_selector = selectors.get("container", "article")
        title_selector = selectors.get("title", "h2")
        link_selector = selectors.get("link", "a")
        image_selector = selectors.get("image", "img")
        
        articles = soup.select(container_selector)
        for article in articles:
            title_node = article.select_one(title_selector) if title_selector else article
            title = title_node.get_text(strip=True) if title_node else ""
            
            link_node = article if not link_selector else article.select_one(link_selector)
            link = None
            if link_node and link_node.has_attr('href'):
                link = link_node.get('href')
            elif article.has_attr('href'):
                link = article.get('href')
            
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

    async def fetch_html(self, source: SourceConfig) -> List[ScrapedArticle]:
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(source.url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                return self._parse_html_content(soup, source)
        except Exception as e:
            logger.error(f"Error en parseo estático de {source.name}: {e}")
            return []

    async def fetch_dynamic(self, source: SourceConfig) -> List[ScrapedArticle]:
        from playwright.async_api import async_playwright
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(user_agent=self.headers["User-Agent"])
                page = await context.new_page()
                
                logger.info(f"🌐 [Playwright] Navegando a fuente dinámica: {source.name}")
                await page.goto(source.url, wait_until="networkidle", timeout=60000)
                
                selectors = source.selectors or {}
                container_selector = selectors.get("container", "article")
                await page.wait_for_selector(container_selector, timeout=30000)
                
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                await browser.close()
                
                return self._parse_html_content(soup, source)
        except Exception as e:
            logger.error(f"Error en Playwright para {source.name}: {e}")
            return []

    async def fetch_wpapi(self, source: SourceConfig) -> List[ScrapedArticle]:
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
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers, timeout=self.timeout)
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

    async def fetch_mintic(self, source: SourceConfig) -> List[ScrapedArticle]:
        BASE = "https://www.mintic.gov.co"
        results = []
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(source.url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")

            seen = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)

                if ("Sala-de-prensa/Noticias/" not in href
                        or len(text) < 20
                        or href.endswith("/Sala-de-prensa/Noticias/")
                        or "#" in href):
                    continue

                full_link = href if href.startswith("http") else BASE + href
                if full_link in seen:
                    continue
                seen.add(full_link)

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

    async def fetch_sharepoint(self, source: SourceConfig) -> List[ScrapedArticle]:
        BASE = "https://www.fondoemprender.com"
        results = []
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(user_agent=self.headers["User-Agent"])
                await page.goto(source.url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(2000)
                for _ in range(2):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(800)
                content = await page.content()
                await browser.close()

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

    async def fetch_sena(self, source: SourceConfig) -> List[ScrapedArticle]:
        BASE = "https://www.sena.edu.co"
        results = []
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(user_agent=self.headers["User-Agent"])
                try:
                    await page.goto(source.url, wait_until="domcontentloaded", timeout=45000)
                except Exception:
                    pass
                await page.wait_for_timeout(3000)
                content = await page.content()
                await browser.close()

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

    async def fetch(self, source: SourceConfig) -> List[ScrapedArticle]:
        """Delega automáticamente la petición iterando de forma ASÍNCRONA la fuente."""
        if source.type == 'rss':
            return await self.fetch_rss(source)
        elif source.type == 'html':
            return await self.fetch_html(source)
        elif source.type == 'dynamic':
            return await self.fetch_dynamic(source)
        elif source.type == 'wpapi':
            return await self.fetch_wpapi(source)
        elif source.type == 'sharepoint':
            return await self.fetch_sharepoint(source)
        elif source.type == 'sena':
            return await self.fetch_sena(source)
        elif source.type == 'mintic':
            return await self.fetch_mintic(source)
        else:
            logger.warning(f"Tipo desconocido de fuente '{source.type}' para {source.name}")
            return []

    async def capture_screenshot(self, url: str, article_id: str):
        """Usa Playwright para tomar una captura limpia del sitio en caso de no tener imagen."""
        from playwright.async_api import async_playwright
        from pathlib import Path
        
        screenshots_dir = Path("static/screenshots")
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{article_id}.png"
        filepath = screenshots_dir / filename
        
        if filepath.exists():
            return f"/static/screenshots/{filename}"
            
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(user_agent=self.headers["User-Agent"])
                await page.set_viewport_size({"width": 1280, "height": 720})
                await page.goto(url, wait_until="domcontentloaded", timeout=40000)
                await page.wait_for_timeout(3000)
                await page.screenshot(path=str(filepath))
                await browser.close()
                return f"/static/screenshots/{filename}"
        except Exception as e:
            logger.error(f"Error capturando screenshot de fallback para {url}: {e}")
            return None
