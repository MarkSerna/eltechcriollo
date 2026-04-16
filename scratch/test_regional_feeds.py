import requests, feedparser

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}

regional = [
    # Antioquia
    ("El Colombiano - Medellín",   "https://www.elcolombiano.com/feed"),
    ("El Colombiano RSS2",         "https://www.elcolombiano.com/rss"),
    # Valle del Cauca
    ("El País de Cali",            "https://www.elpais.com.co/feed/"),
    ("El País RSS2",               "https://www.elpais.com.co/rss/"),
    # Atlántico/Barranquilla
    ("El Heraldo",                 "https://www.elheraldo.co/rss"),
    ("El Heraldo feed",            "https://www.elheraldo.co/feed"),
    # Santander/Bucaramanga
    ("Vanguardia Liberal",         "https://www.vanguardia.com/feed"),
    ("Vanguardia RSS",             "https://www.vanguardia.com/rss"),
    # Caldas/Manizales
    ("La Patria",                  "https://www.lapatria.com/feed"),
    ("La Patria RSS",              "https://www.lapatria.com/rss.xml"),
    # Risaralda/Pereira
    ("El Diario del Otún",         "https://www.eldiario.com.co/feed"),
    ("El Diario RSS",              "https://www.eldiario.com.co/rss"),
    # Quindío/Armenia
    ("Crónica del Quindío",        "https://www.cronicadelquindio.com/feed"),
    ("La Crónica RSS",             "https://www.cronicadelquindio.com/rss"),
    # Norte de Santander
    ("La Opinión Cúcuta",          "https://www.laopinion.com.co/feed"),
    ("La Opinión RSS",             "https://www.laopinion.com.co/rss"),
    # Bolívar/Cartagena
    ("El Universal Cartagena",     "https://www.eluniversal.com.co/feed"),
    ("El Universal RSS",           "https://www.eluniversal.com.co/rss"),
    # Córdoba
    ("El Meridiano",               "https://www.elmeridiano.co/feed"),
    # Tolima
    ("El Nuevo Día",               "https://www.elnuevodia.com.co/feed"),
    # Huila/Neiva
    ("Diario del Huila",           "https://www.diariodelhuila.com/feed"),
    # Meta/Villavicencio
    ("Llano 7 días",               "https://www.llano7dias.com/feed"),
    # Nariño/Pasto
    ("Diario del Sur",             "https://diariodelsur.com.co/feed"),
]

print(f"{'Fuente':<35} {'Status':>7} {'Art':>5}  URL final")
print("-"*80)
working = []
for name, url in regional:
    try:
        r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        feed = feedparser.parse(r.content)
        n = len(feed.entries)
        status = "✅" if n > 0 else "❌"
        print(f"{name:<35} [{r.status_code}]  {n:>4}  {r.url[:55]}")
        if n > 0:
            working.append((name, r.url, n))
    except Exception as e:
        print(f"{name:<35}  [ERR]       {str(e)[:50]}")

print()
print("=== FEEDS FUNCIONALES ===")
for name, url, n in working:
    print(f"  {n:>3} art | {name:<35} -> {url}")
