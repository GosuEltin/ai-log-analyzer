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
from app.api.routes import _extract_line_limit

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
        content_type = res.headers.get("content-type", "")
        if "application/json" in content_type:
            assert "message" in res.json()
        else:
            assert "text/html" in content_type

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


# =============================================================================
# Line Limit Extraction
# =============================================================================

class TestExtractLineLimit:
    """Test the line limit extraction from user query."""

    # Vietnamese patterns WITH number
    def test_vietnamese_100_dong_dau(self):
        assert _extract_line_limit("100 dòng đầu") == 100

    def test_vietnamese_1_dong_dau(self):
        assert _extract_line_limit("1 dòng đầu") == 1

    def test_vietnamese_50_phan_tich_dong(self):
        assert _extract_line_limit("phân tích 50 dòng") == 50

    def test_vietnamese_200_dong_dau_tien(self):
        assert _extract_line_limit("200 dòng đầu tiên") == 200

    # Vietnamese patterns WITHOUT number (default to 1)
    def test_vietnamese_dong_dau_only(self):
        assert _extract_line_limit("dòng đầu") == 1

    def test_vietnamese_dong_dau_tien_only(self):
        assert _extract_line_limit("dòng đầu tiên") == 1

    # English patterns WITH number
    def test_english_first_100_lines(self):
        assert _extract_line_limit("first 100 lines") == 100

    def test_english_top_50_lines(self):
        assert _extract_line_limit("top 50 lines") == 50

    def test_english_analyze_200_lines(self):
        assert _extract_line_limit("analyze 200 lines") == 200

    def test_english_only_1_line(self):
        assert _extract_line_limit("only 1 line") == 1

    # English patterns WITHOUT number (default to 1)
    def test_english_first_line(self):
        assert _extract_line_limit("first line") == 1

    def test_english_top_line(self):
        assert _extract_line_limit("top line") == 1

    # Edge cases
    def test_empty_string_returns_none(self):
        assert _extract_line_limit("") is None

    def test_no_match_returns_none(self):
        assert _extract_line_limit("some random text") is None

    def test_order_independent_vietnamese(self):
        assert _extract_line_limit("phân tích 100 dòng") == 100

    def test_case_insensitive(self):
        assert _extract_line_limit("FIRST 100 LINES") == 100
        assert _extract_line_limit("DÒNG ĐẦU") == 1
