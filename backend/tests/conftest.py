import pytest
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["TESTING"] = "true"
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
os.environ["TELEGRAM_CHAT_ID"] = "123456"


@pytest.fixture
def mock_database():
    with patch("modules.services.database_manager.DatabaseManager") as mock:
        instance = MagicMock()
        instance.get_todays_articles.return_value = []
        instance.get_all_sources.return_value = []
        instance.verify_credentials.return_value = True
        instance.get_all_admins.return_value = []
        instance.get_ai_stats.return_value = {}
        instance.get_article_by_url.return_value = None
        instance.get_all_news_manager.return_value = []
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_scheduler():
    with patch("apscheduler.schedulers.asyncio.AsyncIOScheduler") as mock:
        instance = MagicMock()
        instance.add_job.return_value = None
        instance.start.return_value = None
        instance.get_job.return_value = None
        mock.return_value = instance
        yield instance


@pytest.fixture
def sample_article():
    return {
        "id": 1,
        "title": "Test Article",
        "url": "https://example.com/article",
        "source": "Test Source",
        "region": "colombia",
        "department": "Caldas",
        "image_url": "https://example.com/image.jpg",
        "processed_at": "2026-05-04T10:00:00",
    }


@pytest.fixture
def sample_source():
    return {
        "id": 1,
        "name": "Test Source",
        "url": "https://example.com/feed",
        "type": "rss"
    }