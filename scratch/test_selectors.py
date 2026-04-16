import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}

# --- Forbes CO ---
print("=== Forbes CO ===")
r = requests.get("https://forbes.co/seccion/tecnologia/", headers=headers, timeout=15)
print("Status:", r.status_code)
soup = BeautifulSoup(r.content, "html.parser")

for sel in ["div.card-article", "article", ".entry-card", ".post-card", "div.td-module-thumb", "div.td_module_flex", "div.td_module_10", ".jeg_post"]:
    items = soup.select(sel)
    if items:
        print(f"  [{len(items)} items] selector: {sel}")
        sample = items[0]
        a = sample.find("a", href=True)
        h = sample.find(["h1","h2","h3","h4"])
        img = sample.find("img")
        link_text = a["href"][:70] if a else "None"
        title_text = h.get_text(strip=True)[:70] if h else (a.get("title","")[:70] if a else "None")
        img_text = (img.get("src","") or img.get("data-src",""))[:70] if img else "None"
        print(f"    link: {link_text}")
        print(f"    title: {title_text}")
        print(f"    img: {img_text}")
        break

# Fallback: mostrar todos los links de la pagina
if not any(soup.select(s) for s in ["div.card-article","article",".entry-card"]):
    print("  [FALLBACK] Primers 5 links con texto:")
    for a in soup.find_all("a", href=True)[:10]:
        txt = a.get_text(strip=True)
        if txt and len(txt) > 20:
            print(f"    {a['href'][:60]} | {txt[:60]}")

print()

# --- MinTIC ---
print("=== MinTIC Sala de Prensa ===")
r2 = requests.get("https://www.mintic.gov.co/portal/inicio/Sala-de-prensa/Noticias/", headers=headers, timeout=15)
print("Status:", r2.status_code)
soup2 = BeautifulSoup(r2.content, "html.parser")

for sel in ["div.col-md-6", ".news-item", "article", ".noticias-item", "div.list-group-item", "li", "div.item", ".view-row"]:
    items = soup2.select(sel)
    with_links = [i for i in items if i.find("a", href=True)]
    if with_links:
        print(f"  [{len(with_links)} items con link] selector: {sel}")
        sample = with_links[0]
        a = sample.find("a", href=True)
        h = sample.find(["h2","h3","h4"])
        link_text = a["href"][:80] if a else "None"
        title_text = h.get_text(strip=True)[:80] if h else a.get_text(strip=True)[:80]
        print(f"    link: {link_text}")
        print(f"    title: {title_text}")
        break

# Fallback
print("  [FALLBACK] Primeros links con texto en MinTIC:")
for a in soup2.find_all("a", href=True)[:15]:
    txt = a.get_text(strip=True)
    if txt and len(txt) > 20:
        print(f"    {a['href'][:70]} | {txt[:60]}")
