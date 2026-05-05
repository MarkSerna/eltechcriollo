import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestServicesExist:
    def test_ai_manager_module_exists(self):
        from modules.services import ai_manager
        assert ai_manager is not None

    def test_database_manager_module_exists(self):
        from modules.services import database_manager
        assert database_manager is not None

    def test_notification_manager_module_exists(self):
        from modules.services import notification_manager
        assert notification_manager is not None

    def test_scraper_manager_module_exists(self):
        from modules.services import scraper_manager
        assert scraper_manager is not None

    def test_report_manager_module_exists(self):
        from modules.services import report_manager
        assert report_manager is not None

    def test_search_manager_module_exists(self):
        from modules.services import search_manager
        assert search_manager is not None


class TestAIManagerClass:
    def test_ai_manager_class_exists(self):
        from modules.services.ai_manager import AIManager
        assert AIManager is not None


class TestDatabaseManagerClass:
    def test_database_manager_class_exists(self):
        from modules.services.database_manager import DatabaseManager
        assert DatabaseManager is not None


class TestNotificationManagerClass:
    def test_notification_manager_class_exists(self):
        from modules.services.notification_manager import NotificationManager
        assert NotificationManager is not None


class TestScraperManagerClass:
    def test_scraper_manager_class_exists(self):
        from modules.services.scraper_manager import ScraperManager
        assert ScraperManager is not None


class TestSearchManagerClass:
    def test_search_manager_class_exists(self):
        from modules.services.search_manager import SearchManager
        assert SearchManager is not None