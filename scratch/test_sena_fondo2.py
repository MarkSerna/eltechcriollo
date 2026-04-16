import requests, feedparser
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}

# ── Fondo Emprender: el portal SharePoint tiene RSS nativo ───────────────
print("=== Fondo Emprender - RSS SharePoint ===")
fe_candidates = [
    "https://www.fondoemprender.com/_layouts/listfeed.aspx?List=Noticias",
    "https://www.fondoemprender.com/Lists/Noticias/rss.aspx",
    "https://www.fondoemprender.com/_layouts/15/listfeed.aspx?List=Noticias",
    "https://www.fondoemprender.com/SitePages/Noticias.aspx/_layouts/15/listfeed.aspx",
    "https://www.fondoemprender.com/Lists/Noticias/AllItems.aspx",
]
for url in fe_candidates:
    try:
        r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        ct = r.headers.get("content-type","")
        feed = feedparser.parse(r.content)
        n = len(feed.entries)
        print(f"[{r.status_code}] {n:>3} art | {ct[:40]} | {url[-60:]}")
        if n > 0:
            print(f"  sample: {feed.entries[0].title[:60]}")
    except Exception as e:
        print(f"[ERR] {url[-60:]}: {e}")

# ── SENA: intentar URLs alternativas ─────────────────────────────────────
print()
print("=== SENA - URLs alternativas ===")
sena_candidates = [
    "https://www.sena.edu.co/es-co/Noticias/Paginas/noticias.aspx",
    "https://www.sena.edu.co/",
    "https://ctpi.sena.edu.co/",
    "https://www.sena.edu.co/rss/noticias.xml",
    "https://www.sena.edu.co/Lists/Noticias/rss.aspx",
    "https://noticias.sena.edu.co/",
    "https://www.sena.edu.co/es-co/noticias",
]
for url in sena_candidates:
    try:
        r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        ct = r.headers.get("content-type","")
        feed = feedparser.parse(r.content)
        n = len(feed.entries)
        print(f"[{r.status_code}] {n:>3} art | {ct[:35]} | {url}")
        if n > 0:
            print(f"  sample: {feed.entries[0].title[:60]}")
        elif r.status_code == 200 and "html" in ct:
            soup = BeautifulSoup(r.content, "html.parser")
            links_with_text = [(a.get_text(strip=True), a["href"]) for a in soup.find_all("a", href=True) if len(a.get_text(strip=True)) > 25]
            if links_with_text:
                print(f"  → {len(links_with_text)} links con texto largo")
                for t, h in links_with_text[:3]:
                    print(f"    {t[:60]} | {h[:60]}")
    except Exception as e:
        print(f"[ERR] {url}: {e}")
