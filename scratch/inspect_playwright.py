"""
Usa Playwright para inspeccionar la estructura real (JS-rendered) de Forbes CO y MinTIC.
"""
import sys
sys.path.insert(0, "/app")
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def inspect_site(name, url, candidate_selectors):
    print(f"\n{'='*60}")
    print(f"  {name} -> {url}")
    print('='*60)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36")
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)
        content = page.content()
        browser.close()

    soup = BeautifulSoup(content, "html.parser")

    found = False
    for sel in candidate_selectors:
        items = soup.select(sel)
        if items:
            with_links = [i for i in items if i.find("a", href=True)]
            if with_links:
                print(f"  ✅ [{len(with_links)} items] selector: '{sel}'")
                for sample in with_links[:3]:
                    a = sample.find("a", href=True)
                    h = sample.find(["h1","h2","h3","h4"])
                    img = sample.find("img")
                    link = a["href"][:80] if a else "–"
                    title = (h.get_text(strip=True) if h else a.get_text(strip=True))[:70]
                    img_src = (img.get("src") or img.get("data-src",""))[:70] if img else "–"
                    print(f"    TITLE: {title}")
                    print(f"    LINK:  {link}")
                    print(f"    IMG:   {img_src}")
                    print()
                found = True
                break

    if not found:
        print("  ❌ Ningún selector funcionó. Mostrando primeros links con texto largo:")
        for a in soup.find_all("a", href=True)[:20]:
            txt = a.get_text(strip=True)
            if txt and len(txt) > 25:
                # buscar clase del padre
                parent_cls = " ".join(a.parent.get("class", []))[:40]
                print(f"    [{parent_cls}] {a['href'][:60]} | {txt[:60]}")

# ─── Forbes CO ───────────────────────────────────────────────
inspect_site(
    "Forbes CO - Tecnología",
    "https://forbes.co/seccion/tecnologia/",
    [
        "article", ".post", ".td_module_flex", ".td_module_10",
        ".jeg_post", ".entry", "div.card", ".story", ".item-list li",
        ".article-card", "div.story-card", "div.post-item",
        "h2 a", "h3 a"
    ]
)

# ─── MinTIC ──────────────────────────────────────────────────
inspect_site(
    "MinTIC - Noticias",
    "https://www.mintic.gov.co/portal/inicio/Sala-de-prensa/Noticias/",
    [
        "div.views-row", ".view-content .views-row",
        "article", ".news-item", ".noticias",
        "div.col-sm-4", "div.col-md-4", "div.col-sm-6",
        "div.field-content a", ".field-items .field-item",
        "h3 a", "h2 a",
    ]
)
