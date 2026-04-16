import requests, json
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}

# ─── FORBES: Probar WP REST API con categoria tecnologia ─────────────────
print("=== Forbes CO - WP REST API cat=5 (Tecnología) ===")
url = "https://editorial.forbes.co/wp-json/wp/v2/posts?categories=5&per_page=10&_fields=title,link,date,excerpt,featured_media,jetpack_featured_media_url"
r = requests.get(url, headers=headers, timeout=12)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    posts = r.json()
    print(f"Total posts: {len(posts)}")
    for p in posts[:5]:
        title = p.get("title", {}).get("rendered", "").strip()
        link = p.get("link", "")
        img = p.get("jetpack_featured_media_url", "") or ""
        excerpt = BeautifulSoup(p.get("excerpt", {}).get("rendered", ""), "html.parser").get_text(strip=True)[:80]
        print(f"\n  TITLE:   {title[:70]}")
        print(f"  LINK:    {link[:70]}")
        print(f"  IMG:     {img[:60]}")
        print(f"  EXCERPT: {excerpt}")

# ─── MINTIC: Inspeccionar con requests + buscar links a noticias ──────────
print()
print("=== MinTIC - HTML con links a noticias ===")
r2 = requests.get("https://www.mintic.gov.co/portal/inicio/Sala-de-prensa/Noticias/", headers=headers, timeout=15)
print(f"Status: {r2.status_code}")
soup = BeautifulSoup(r2.content, "html.parser")

# Buscar todos los links que apunten a noticias internas
news_links = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    text = a.get_text(strip=True)
    # Los links de noticias MinTIC tienen este patrón
    if "Sala-de-prensa/Noticias" in href and len(text) > 20 and href != "/portal/inicio/Sala-de-prensa/Noticias/":
        news_links.append((href, text))

print(f"Links a noticias encontrados: {len(news_links)}")
for href, text in news_links[:10]:
    print(f"  {text[:70]}")
    print(f"  -> {href[:90]}")
    print()
