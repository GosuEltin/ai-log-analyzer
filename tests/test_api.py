"""
Integration tests for the /analyze-log API endpoint.

Validates:
- Successful end-to-end analysis (upload log → get results)
- Error handling: missing file, empty file
- Response schema validation
- All result fields present
"""
import io
import pytest

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


SAMPLE_LOG = """\
[Sun Dec 04 04:47:44 2005] [notice] workerEnv.init() ok /etc/httpd/conf/workers2.properties
[Sun Dec 04 04:47:44 2005] [error] mod_jk child workerEnv in error state 6
[Sun Dec 04 04:47:44 2005] [error] mod_jk child workerEnv in error state 6
[Sun Dec 04 04:47:45 2005] [error] [client 192.168.1.1] Directory index forbidden by rule: /var/www/html/
[Sun Dec 04 04:47:46 2005] [error] jk2_init() Can't find child 1566 in scoreboard
[Sun Dec 04 04:47:46 2005] [notice] jk2_init() Found child 1567 in scoreboard
[Sun Dec 04 04:47:47 2005] [error] mod_jk child workerEnv in error state 7
"""


# =============================================================================
# Health & Root
# =============================================================================

class TestHealthEndpoints:
    """Test basic health and root endpoints."""

    def test_root(self):
        res = client.get("/")
        assert res.status_code == 200
        assert "message" in res.json()

    def test_health(self):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


# =============================================================================
# Analyze Endpoint
# =============================================================================

class TestAnalyzeLogEndpoint:
    """Test the main /analyze-log POST endpoint."""

    def test_successful_analysis(self):
        """End-to-end: upload log → receive structured analysis."""
        file = io.BytesIO(SAMPLE_LOG.encode("utf-8"))
        res = client.post(
            "/analyze-log",
            files={"file": ("test.log", file, "text/plain")},
            data={"user_query": ""},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["filename"] == "test.log"

    def test_result_has_all_fields(self):
        """Verify response contains all required fields."""
        file = io.BytesIO(SAMPLE_LOG.encode("utf-8"))
        res = client.post(
            "/analyze-log",
            files={"file": ("test.log", file, "text/plain")},
            data={"user_query": ""},
        )
        result = res.json()["result"]

        required_fields = [
            "overview", "clusters", "probable_causes",
            "recommendations", "evidence", "summary",
            "retrieved_knowledge", "severity",
            "action_checks", "executed_actions",
            "final_summary", "final_diagnosis",
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_overview_structure(self):
        """Verify overview contains expected metrics."""
        file = io.BytesIO(SAMPLE_LOG.encode("utf-8"))
        res = client.post(
            "/analyze-log",
            files={"file": ("test.log", file, "text/plain")},
            data={"user_query": ""},
        )
        overview = res.json()["result"]["overview"]
        assert overview["total_lines"] == 7
        assert overview["parsed_lines"] == 7
        assert overview["error_count"] >= 4

    def test_clusters_not_empty(self):
        file = io.BytesIO(SAMPLE_LOG.encode("utf-8"))
        res = client.post(
            "/analyze-log",
            files={"file": ("test.log", file, "text/plain")},
            data={"user_query": ""},
        )
        clusters = res.json()["result"]["clusters"]
        assert len(clusters) > 0

    def test_with_user_query(self):
        """Test with focus-mode query for backend connectivity."""
        file = io.BytesIO(SAMPLE_LOG.encode("utf-8"))
        res = client.post(
            "/analyze-log",
            files={"file": ("test.log", file, "text/plain")},
            data={"user_query": "check backend tomcat AJP"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True

    def test_empty_file_returns_400(self):
        """Empty file should return error."""
        file = io.BytesIO(b"")
        res = client.post(
            "/analyze-log",
            files={"file": ("empty.log", file, "text/plain")},
            data={"user_query": ""},
        )
        assert res.status_code == 400

    def test_severity_is_string(self):
        file = io.BytesIO(SAMPLE_LOG.encode("utf-8"))
        res = client.post(
            "/analyze-log",
            files={"file": ("test.log", file, "text/plain")},
            data={"user_query": ""},
        )
        severity = res.json()["result"]["severity"]
        assert isinstance(severity, str)
        assert severity in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
