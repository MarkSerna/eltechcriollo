"""
Intercepta las peticiones de red para encontrar APIs JSON de Forbes CO y MinTIC.
"""
import sys
sys.path.insert(0, "/app")
from playwright.sync_api import sync_playwright
import json

def intercept_apis(name, url):
    print(f"\n{'='*60}")
    print(f"  {name} -> {url}")
    print('='*60)
    api_calls = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36")

        def on_response(response):
            ct = response.headers.get("content-type", "")
            req_url = response.url
            # Filtrar solo respuestas JSON o XML que puedan ser feeds/APIs
            if ("json" in ct or "xml" in ct or "rss" in ct) and response.status == 200:
                if any(skip in req_url for skip in ["google", "facebook", "twitter", "doubleclick", "analytics", "fonts"]):
                    return
                api_calls.append({
                    "url": req_url[:120],
                    "ct": ct[:50],
                    "status": response.status,
                })

        page.on("response", on_response)
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)

        # Scroll para activar lazy loading
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        browser.close()

    if api_calls:
        print(f"  Encontradas {len(api_calls)} APIs/feeds:")
        for c in api_calls[:15]:
            print(f"    [{c['status']}] {c['ct'][:30]}")
            print(f"           {c['url']}")
    else:
        print("  ⚠️  No se encontraron APIs JSON/XML")

intercept_apis("Forbes CO - Tecnología", "https://forbes.co/seccion/tecnologia/")
intercept_apis("MinTIC - Noticias", "https://www.mintic.gov.co/portal/inicio/Sala-de-prensa/Noticias/")
