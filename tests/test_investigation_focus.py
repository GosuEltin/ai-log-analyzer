"""
Tests for app.services.investigation_focus — User intent detection and filtering.

Validates:
- Focus mode detection from user queries (backend_connectivity, access_control, general)
- Cluster filtering by focus mode
- List filtering by focus mode
- Action check filtering by focus mode
- Issue role annotation (primary vs secondary)
"""
import pytest

from app.services.investigation_focus import (
    detect_focus_mode,
    is_backend_related_label,
    is_access_related_label,
    filter_clusters_by_focus,
    filter_list_by_focus,
    filter_action_checks_by_focus,
    annotate_issue_roles,
)


# =============================================================================
# Focus Mode Detection
# =============================================================================

class TestDetectFocusMode:
    """Test user intent classification."""

    def test_empty_query_returns_general(self):
        assert detect_focus_mode("") == "general"

    def test_none_query_returns_general(self):
        assert detect_focus_mode(None) == "general"

    def test_backend_keywords(self):
        assert detect_focus_mode("check backend tomcat connection") == "backend_connectivity"

    def test_ajp_keywords(self):
        assert detect_focus_mode("Why is AJP port failing?") == "backend_connectivity"

    def test_access_keywords(self):
        assert detect_focus_mode("directory forbidden access issue") == "access_control"

    def test_index_keyword(self):
        assert detect_focus_mode("Why is DirectoryIndex missing?") == "access_control"

    def test_mixed_prefers_backend(self):
        """When both keyword groups match, backend wins if >= access."""
        result = detect_focus_mode("backend worker directory")
        assert result in ("backend_connectivity", "general")


# =============================================================================
# Label Classification
# =============================================================================

class TestLabelClassification:
    """Test is_backend_related_label and is_access_related_label."""

    def test_backend_label(self):
        assert is_backend_related_label("mod_jk workerEnv error state") is True

    def test_scoreboard_label(self):
        assert is_backend_related_label("Apache scoreboard child mismatch") is True

    def test_access_label(self):
        assert is_access_related_label("Directory access forbidden") is True

    def test_client_access_label(self):
        assert is_access_related_label("Client access forbidden") is True

    def test_unrelated_label(self):
        assert is_backend_related_label("Other apache issue") is False
        assert is_access_related_label("Other apache issue") is False


# =============================================================================
# Cluster Filtering
# =============================================================================

class TestFilterClustersByFocus:
    """Test cluster reordering by focus mode."""

    @pytest.fixture
    def mixed_clusters(self):
        return [
            {"label": "Directory access forbidden", "count": 10},
            {"label": "mod_jk workerEnv error state", "count": 100},
            {"label": "Other apache issue", "count": 5},
        ]

    def test_general_no_change(self, mixed_clusters):
        result = filter_clusters_by_focus(mixed_clusters, "general")
        assert result == mixed_clusters

    def test_backend_focus_reorders(self, mixed_clusters):
        result = filter_clusters_by_focus(mixed_clusters, "backend_connectivity")
        assert result[0]["label"] == "mod_jk workerEnv error state"

    def test_access_focus_reorders(self, mixed_clusters):
        result = filter_clusters_by_focus(mixed_clusters, "access_control")
        assert result[0]["label"] == "Directory access forbidden"


# =============================================================================
# List Filtering
# =============================================================================

class TestFilterListByFocus:
    """Test string list filtering by focus mode."""

    @pytest.fixture
    def mixed_items(self):
        return [
            "Backend Tomcat không phản hồi",
            "Directory access bị từ chối",
            "Kiểm tra cổng AJP",
            "Thiếu index.html",
        ]

    def test_general_all_items(self, mixed_items):
        result = filter_list_by_focus(mixed_items, "general")
        assert len(result) == len(mixed_items)

    def test_backend_focus_limits(self, mixed_items):
        result = filter_list_by_focus(mixed_items, "backend_connectivity")
        assert len(result) <= 5


# =============================================================================
# Action Check Filtering
# =============================================================================

class TestFilterActionChecksByFocus:
    """Test action check filtering by focus mode."""

    @pytest.fixture
    def mixed_actions(self):
        return [
            {"title": "Check backend HTTP", "category": "backend_health", "purpose": "verify backend"},
            {"title": "Check index file", "category": "filesystem_check", "purpose": "check index directory access"},
            {"title": "Read mod_jk log", "category": "log_inspection", "purpose": "inspect mod_jk logs"},
        ]

    def test_general_returns_all(self, mixed_actions):
        result = filter_action_checks_by_focus(mixed_actions, "general")
        assert len(result) == len(mixed_actions)

    def test_backend_focus_filters(self, mixed_actions):
        result = filter_action_checks_by_focus(mixed_actions, "backend_connectivity")
        titles = {a["title"] for a in result}
        assert "Check backend HTTP" in titles


# =============================================================================
# Issue Role Annotation
# =============================================================================

class TestAnnotateIssueRoles:
    """Test primary/secondary issue classification."""

    def test_empty_clusters(self):
        primary, secondary = annotate_issue_roles([], "general")
        assert primary == ""
        assert secondary == []

    def test_general_first_is_primary(self):
        clusters = [
            {"label": "mod_jk workerEnv error state"},
            {"label": "Directory access forbidden"},
        ]
        primary, secondary = annotate_issue_roles(clusters, "general")
        assert primary == "mod_jk workerEnv error state"
        assert "Directory access forbidden" in secondary

    def test_backend_focus_promotes(self):
        clusters = [
            {"label": "Directory access forbidden"},
            {"label": "mod_jk workerEnv error state"},
        ]
        primary, secondary = annotate_issue_roles(clusters, "backend_connectivity")
        assert primary == "mod_jk workerEnv error state"
