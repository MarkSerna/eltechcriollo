"""
Usa Playwright para explorar Fondo Emprender y SENA, interceptar APIs y hallar links de noticias.
"""
import sys
sys.path.insert(0, "/app")
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def explore(name, url, news_path_hints):
    print(f"\n{'='*65}")
    print(f"  {name}")
    print(f"  {url}")
    print('='*65)

    api_calls = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36")

        def on_response(response):
            ct = response.headers.get("content-type", "")
            if ("json" in ct or "xml" in ct) and response.status == 200:
                skip = ["google", "facebook", "twitter", "doubleclick", "analytics", "fonts", "cdn"]
                if not any(s in response.url for s in skip):
                    api_calls.append({"url": response.url[:120], "ct": ct[:40]})

        page.on("response", on_response)
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(2000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)
        except Exception as e:
            print(f"  [WARN] goto: {e}")

        content = page.content()
        browser.close()

    soup = BeautifulSoup(content, "html.parser")

    # APIs interceptadas
    if api_calls:
        print(f"\n  📡 APIs JSON/XML interceptadas ({len(api_calls)}):")
        for c in api_calls[:8]:
            print(f"    {c['ct'][:30]} | {c['url']}")

    # Links a noticias
    news_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if len(text) < 20:
            continue
        full = href if href.startswith("http") else urljoin(url, href)
        if any(hint.lower() in full.lower() for hint in news_path_hints):
            news_links.append((full, text))

    if news_links:
        print(f"\n  📰 Links de noticias encontrados ({len(news_links)}):")
        for link, text in news_links[:8]:
            print(f"    {text[:70]}")
            print(f"    -> {link[:90]}")
    else:
        print("\n  ⚠️  No se encontraron links de noticias con los hints dados.")
        print("  Primeros links con texto largo:")
        for a in soup.find_all("a", href=True)[:20]:
            t = a.get_text(strip=True)
            if len(t) > 25:
                href = a["href"]
                full = href if href.startswith("http") else urljoin(url, href)
                cls = " ".join(a.parent.get("class", []))[:30]
                print(f"    [{cls}] {t[:60]}")
                print(f"           {full[:80]}")


explore(
    "Fondo Emprender - Noticias",
    "https://www.fondoemprender.com/SitePages/Noticias.aspx",
    ["noticia", "novedad", "news", "articulo", "prensa", "sala"]
)

explore(
    "SENA - Noticias Tecnología",
    "https://www.sena.edu.co/es-co/Noticias/Paginas/noticias.aspx",
    ["noticia", "novedad", "news", "tecnologia", "prensa"]
)
