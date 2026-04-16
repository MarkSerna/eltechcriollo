import requests, feedparser
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}

def test_site(name, candidates):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print('='*60)
    for url in candidates:
        try:
            r = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
            ct = r.headers.get("content-type", "")
            feed = feedparser.parse(r.content)
            n = len(feed.entries)
            print(f"[{r.status_code}] {n:>3} art | {ct[:40]}")
            print(f"  -> {r.url[:90]}")
            if n > 0:
                print(f"  sample: {feed.entries[0].title[:70]}")
            elif "json" in ct and r.status_code == 200:
                print(f"  json preview: {r.text[:200]}")
        except Exception as e:
            print(f"[ERR] {url}: {e}")

# ── Fondo Emprender ──────────────────────────────────────────
test_site("Fondo Emprender", [
    "https://www.fondoemprender.com/SitePages/Home.aspx",
    "https://www.fondoemprender.com/Lists/Noticias/rss",
    "https://www.fondoemprender.com/rss",
    "https://www.fondoemprender.com/feed",
    "https://www.fondoemprender.com/SitePages/Noticias.aspx",
])

# ── SENA ─────────────────────────────────────────────────────
test_site("SENA", [
    "https://www.sena.edu.co/es-co/Noticias/Paginas/noticias.aspx",
    "https://www.sena.edu.co/rss",
    "https://www.sena.edu.co/feed",
    "https://www.sena.edu.co/es-co/Noticias/rss",
    "https://www.sena.edu.co/Lists/Noticias/rss.aspx",
])
