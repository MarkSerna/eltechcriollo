import sys
sys.path.insert(0, "/app")
from modules.models.config import config
from modules.models.source import SourceConfig
from modules.services.scraper_manager import ScraperManager
import json

with open(config.paths.sources_path) as f:
    sources = [SourceConfig.from_dict(s) for s in json.load(f)]

sm = ScraperManager()
kws = [k.lower() for k in config.scraper.keywords]

# Solo probar los nuevos
targets = [s for s in sources if s.type in ("sena", "sharepoint")]
for src in targets:
    try:
        arts = sm.fetch(src)
        hits = [a for a in arts if any(k in a.get_content_snapshot() for k in kws)]
        print(f"  [{src.type}] {src.name}")
        print(f"  Extraídos: {len(arts)}  |  Match keywords: {len(hits)}")
        for a in arts[:3]:
            print(f"    - {a.title[:70]}")
        print()
    except Exception as e:
        print(f"  ERR {src.name}: {e}")
