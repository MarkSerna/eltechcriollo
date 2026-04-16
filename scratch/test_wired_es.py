import requests, feedparser

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}

candidates = [
    "https://es.wired.com/feed/rss",
    "https://es.wired.com/rss",
    "https://es.wired.com/feed",
    "https://es.wired.com/feed/category/tecnologia/rss",
    "https://feeds.feedburner.com/WiredES",
]
for url in candidates:
    try:
        r = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
        feed = feedparser.parse(r.content)
        n = len(feed.entries)
        ct = r.headers.get("content-type","")[:40]
        title = feed.entries[0].title[:60] if n > 0 else ""
        print(f"[{r.status_code}] {n:>3} art | {ct}")
        print(f"  url: {url}")
        if title:
            print(f"  sample: {title}")
    except Exception as e:
        print(f"[ERR] {url}: {e}")
