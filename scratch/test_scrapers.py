
import sys
from pathlib import Path
import json

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.models.source import SourceConfig
from modules.services.scraper_manager import ScraperManager
from modules.models.config import config

def test_sources():
    sources_path = Path("data/sources.json")
    with open(sources_path, 'r', encoding='utf-8') as f:
        raw_sources = json.load(f)
        sources = [SourceConfig.from_dict(src) for src in raw_sources]
    
    scraper_manager = ScraperManager()
    
    print(f"Testing {len(sources)} sources...")
    
    for source in sources:
        print(f"\n--- Testing: {source.name} ({source.type}) ---")
        try:
            articles = scraper_manager.fetch(source)
            print(f"Found {len(articles)} articles.")
            
            if articles:
                # Check how many would pass the keyword filter
                matched = 0
                for art in articles:
                    content = art.get_content_snapshot()
                    matches = [kw for kw in config.scraper.keywords if kw.lower() in content]
                    if matches:
                        matched += 1
                        # print(f"  [MATCH] {art.title[:50]}... (Keywords: {matches})")
                    # else:
                    #     print(f"  [SKIP] {art.title[:50]}...")
                
                print(f"Articles matching keywords: {matched}/{len(articles)}")
                if len(articles) > 0:
                   print(f"Sample article title: {articles[0].title}")
            else:
                print("No articles found.")
        except Exception as e:
            print(f"Error testing {source.name}: {e}")

if __name__ == "__main__":
    test_sources()
