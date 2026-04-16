import requests, json

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}

# Forbes - WordPress REST API
print("=== Forbes CO - WP REST API ===")
apis = [
    "https://editorial.forbes.co/wp-json/wp/v2/categories?search=tecnologia",
    "https://editorial.forbes.co/wp-json/wp/v2/posts?per_page=10&_fields=title,link,date,excerpt,featured_media",
]
for url in apis:
    try:
        r = requests.get(url, headers=headers, timeout=12)
        print(f"[{r.status_code}] {url[:90]}")
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                print(f"  -> {len(data)} items")
                if data:
                    first = data[0]
                    print(f"  keys: {list(first.keys())[:10]}")
                    title = first.get("title", {})
                    title_str = title.get("rendered", "") if isinstance(title, dict) else str(title)
                    print(f"  title: {title_str[:70]}")
                    print(f"  link:  {first.get('link','')[:70]}")
                    print(f"  id:    {first.get('id','')}")
                    # categorias
                    cats = first.get("categories", [])
                    print(f"  cats:  {cats}")
            elif isinstance(data, dict):
                print(f"  keys: {list(data.keys())[:10]}")
    except Exception as e:
        print(f"  ERR: {e}")

# Buscar categoria tecnologia en Forbes
print()
print("=== Forbes CO - buscar cat_id tecnologia ===")
try:
    r = requests.get("https://editorial.forbes.co/wp-json/wp/v2/categories?search=tecnolog&per_page=20", headers=headers, timeout=12)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        cats = r.json()
        for c in cats:
            print(f"  id={c['id']} slug={c['slug']} name={c['name']} count={c.get('count',0)}")
except Exception as e:
    print(f"ERR: {e}")

# MinTIC - buscar API Drupal
print()
print("=== MinTIC - APIs alternativas ===")
mintic_candidates = [
    "https://www.mintic.gov.co/portal/inicio/Sala-de-prensa/Noticias/?_format=json",
    "https://www.mintic.gov.co/portal/inicio/Sala-de-prensa/Noticias/?format=json",
    "https://www.mintic.gov.co/api/news",
    "https://www.mintic.gov.co/portal/inicio/Sala-de-prensa/Noticias/feed.rss",
]
for url in mintic_candidates:
    try:
        r = requests.get(url, headers=headers, timeout=10)
        ct = r.headers.get("content-type", "")
        print(f"[{r.status_code}] {ct[:35]} | {url}")
        if r.status_code == 200 and "json" in ct:
            preview = r.text[:200]
            print(f"  preview: {preview}")
    except Exception as e:
        print(f"  ERR: {e}")
