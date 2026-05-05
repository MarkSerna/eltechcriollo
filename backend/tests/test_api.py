import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestRootEndpoint:
    @patch("api.db")
    def test_root_returns_ok(self, mock_db):
        from api import app
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"


class TestAuthEndpoints:
    @patch("api.db")
    def test_login_success(self, mock_db):
        from api import app
        mock_db.verify_credentials.return_value = True
        with TestClient(app) as client:
            response = client.post(
                "/api/login",
                json={"username": "admin", "password": "password123"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["user"]["authenticated"] is True

    @patch("api.db")
    def test_login_failure(self, mock_db):
        from api import app
        mock_db.verify_credentials.return_value = False
        with TestClient(app) as client:
            response = client.post(
                "/api/login",
                json={"username": "admin", "password": "wrongpassword"}
            )
            assert response.status_code == 401


class TestNewsEndpoints:
    @patch("api.db")
    def test_get_news_returns_structure(self, mock_db, sample_article):
        from api import app
        mock_db.get_todays_articles.return_value = [sample_article]
        mock_db.get_all_sources.return_value = []
        
        with TestClient(app) as client:
            response = client.get("/api/news")
            assert response.status_code == 200
            data = response.json()
            assert "colombia" in data
            assert "global" in data
            assert "featured" in data


class TestStatsEndpoint:
    @patch("api.db")
    @patch("api.scheduler")
    def test_get_stats_requires_auth(self, mock_scheduler, mock_db):
        from api import app
        mock_scheduler.get_job.return_value = None
        with TestClient(app) as client:
            response = client.get("/api/stats")
            assert response.status_code == 401


class TestAdminEndpoints:
    @patch("api.db")
    def test_get_admins_requires_auth(self, mock_db):
        from api import app
        with TestClient(app) as client:
            response = client.get("/api/admins")
            assert response.status_code == 401

    @patch("api.db")
    def test_get_sources_requires_auth(self, mock_db):
        from api import app
        with TestClient(app) as client:
            response = client.get("/api/sources")
            assert response.status_code == 401


class TestScrapeEndpoint:
    @patch("api.db")
    def test_trigger_scrape_requires_auth(self, mock_db):
        from api import app
        with TestClient(app) as client:
            response = client.post("/api/scrape")
            assert response.status_code == 401


class TestDictionaryEndpoint:
    @patch("api.db")
    def test_get_dictionary_requires_auth(self, mock_db):
        from api import app
        with TestClient(app) as client:
            response = client.get("/api/dictionary")
            assert response.status_code == 401


class TestLogsEndpoint:
    @patch("api.db")
    def test_get_logs_requires_auth(self, mock_db):
        from api import app
        with TestClient(app) as client:
            response = client.get("/api/logs")
            assert response.status_code == 401


class TestAIStatsEndpoint:
    @patch("api.db")
    def test_get_ai_stats_requires_auth(self, mock_db):
        from api import app
        with TestClient(app) as client:
            response = client.get("/api/ai-stats")
            assert response.status_code == 401