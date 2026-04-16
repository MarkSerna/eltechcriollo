"""
Explorar SENA con Playwright (buscar noticias reales) y validar el patrón de Fondo Emprender.
"""
import sys
sys.path.insert(0, "/app")
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}

# ── 1. Fondo Emprender: confirmar patrón y obtener más noticias ───────────
print("=== Fondo Emprender - patrón DispForm ===")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(user_agent=headers["User-Agent"])
    page.goto("https://www.fondoemprender.com/SitePages/Noticias.aspx", wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2000)
    # Scroll para cargar más
    for _ in range(3):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
    content = page.content()
    browser.close()

soup = BeautifulSoup(content, "html.parser")
seen = set()
for a in soup.find_all("a", href=True):
    href = a["href"]
    text = a.get_text(strip=True)
    if "DispForm.aspx" in href and len(text) > 15 and "Turn" not in text:
        full = href if href.startswith("http") else "https://www.fondoemprender.com" + href
        if full not in seen:
            seen.add(full)
            print(f"  {text[:70]}")
            print(f"  -> {full[:90]}")

# ── 2. SENA: buscar noticias desde la página principal ────────────────────
print()
print("=== SENA - Home y sección noticias ===")
sena_urls = [
    "https://www.sena.edu.co/",
    "https://www.sena.edu.co/es-co/noticias",
]
for url in sena_urls:
    print(f"\n  URL: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=headers["User-Agent"])
        try:
            page.goto(url, wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"  WARN: {e}")
        content = page.content()
        browser.close()

    soup = BeautifulSoup(content, "html.parser")
    news_links = []
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]
        if len(text) < 20 or href.startswith("javascript"):
            continue
        full = href if href.startswith("http") else urljoin(url, href)
        # Detectar links que parezcan noticias (no son menús de navegación)
        if any(kw in full.lower() for kw in ["noticia", "articulo", "prensa", "detalle", "DispForm", "noticias/"]):
            news_links.append((text, full))

    if news_links:
        print(f"  Noticias encontradas: {len(news_links)}")
        for t, l in news_links[:6]:
            print(f"    {t[:70]}")
            print(f"    -> {l[:90]}")
    else:
        # Mostrar titulos de todo lo que hay
        headings = [h.get_text(strip=True) for h in soup.find_all(["h1","h2","h3","h4"]) if h.get_text(strip=True)]
        print(f"  Headings encontrados: {len(headings)}")
        for h in headings[:10]:
            print(f"    {h[:80]}")
