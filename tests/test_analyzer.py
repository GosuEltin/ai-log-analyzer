"""
Tests for app.services.analyzer — Log analysis logic.

Validates:
- Overview computation (line counts, level counts, top services)
- Error clustering by label
- Probable cause derivation from clusters
- Recommendation generation
- Severity classification
- Evidence collection
- Action check derivation
"""
import pytest

from app.models.schemas import LogRecord, ErrorCluster
from app.services.analyzer import (
    normalize_message,
    classify_message,
    build_overview,
    build_clusters,
    derive_probable_causes,
    derive_recommendations,
    collect_evidence,
    derive_severity,
    derive_action_checks,
)


# =============================================================================
# Message Normalization
# =============================================================================

class TestNormalizeMessage:
    """Test dynamic-ID stripping for clustering."""

    def test_strips_request_id(self):
        msg = "Failed request_id=abc123 timeout"
        result = normalize_message(msg)
        assert "request_id=<id>" in result

    def test_strips_user_id(self):
        msg = "Error for user=42 in service"
        result = normalize_message(msg)
        assert "user=<id>" in result

    def test_strips_numbers(self):
        msg = "Error state 6"
        result = normalize_message(msg)
        assert "<num>" in result


# =============================================================================
# Message Classification
# =============================================================================

class TestClassifyMessage:
    """Test rule-based classification of log messages."""

    def test_mod_jk_error(self):
        assert classify_message("mod_jk child workerEnv in error state 6") == "mod_jk workerEnv error state"

    def test_directory_forbidden(self):
        assert classify_message("Directory index forbidden by rule: /var/www/html/") == "Directory access forbidden"

    def test_scoreboard_child(self):
        assert classify_message("jk2_init() Can't find child 1566 in scoreboard") == "Apache scoreboard child mismatch"

    def test_child_init(self):
        assert classify_message("child init something") == "Apache child initialization issue"

    def test_workerenv_ok(self):
        assert classify_message("workerEnv.init() ok /etc/httpd/conf/workers2.properties") == "workerEnv initialized successfully"

    def test_jk2_found_child(self):
        assert classify_message("jk2_init() Found child 1567 in scoreboard slot") == "jk2 child discovered"

    def test_client_forbidden(self):
        assert classify_message("[client 192.168.1.1] Forbidden access") == "Client access forbidden"

    def test_other(self):
        assert classify_message("something completely unknown") == "Other apache issue"


# =============================================================================
# Overview
# =============================================================================

class TestBuildOverview:
    """Test overview summary computation."""

    def test_total_lines(self, parsed_records):
        overview = build_overview(parsed_records, failed_lines=[])
        assert overview.total_lines == len(parsed_records)
        assert overview.parsed_lines == len(parsed_records)
        assert overview.failed_lines == 0

    def test_counts_errors(self, parsed_records):
        overview = build_overview(parsed_records, [])
        assert overview.error_count >= 4

    def test_includes_info(self, parsed_records):
        overview = build_overview(parsed_records, [])
        assert overview.info_count >= 1  # notice → INFO

    def test_top_services(self, parsed_records):
        overview = build_overview(parsed_records, [])
        assert isinstance(overview.top_services, dict)
        assert len(overview.top_services) > 0

    def test_failed_lines_counted(self, parsed_records):
        overview = build_overview(parsed_records, ["bad line 1", "bad line 2"])
        assert overview.failed_lines == 2
        assert overview.total_lines == len(parsed_records) + 2


# =============================================================================
# Clustering
# =============================================================================

class TestBuildClusters:
    """Test error clustering logic."""

    def test_clusters_created(self, parsed_records):
        clusters = build_clusters(parsed_records)
        assert len(clusters) > 0

    def test_only_warn_error_clustered(self, parsed_records):
        """INFO-level records should NOT appear in clusters."""
        clusters = build_clusters(parsed_records)
        for c in clusters:
            # workerEnv initialized (INFO) should not be clustered
            assert "workerEnv initialized successfully" not in c.label

    def test_sorted_by_count_desc(self, parsed_records):
        clusters = build_clusters(parsed_records)
        for i in range(len(clusters) - 1):
            assert clusters[i].count >= clusters[i + 1].count

    def test_cluster_has_samples(self, parsed_records):
        clusters = build_clusters(parsed_records)
        for c in clusters:
            assert len(c.samples) > 0
            assert len(c.samples) <= 3

    def test_mod_jk_cluster_exists(self, parsed_records):
        clusters = build_clusters(parsed_records)
        labels = [c.label for c in clusters]
        assert "mod_jk workerEnv error state" in labels


# =============================================================================
# Probable Causes
# =============================================================================

class TestDeriveProbableCauses:
    """Test cause derivation from clusters."""

    def test_mod_jk_causes(self, sample_clusters):
        causes = derive_probable_causes(sample_clusters)
        assert len(causes) > 0
        assert any("backend" in c.lower() or "tomcat" in c.lower() for c in causes)

    def test_no_clusters_fallback(self):
        causes = derive_probable_causes([])
        assert len(causes) == 1
        # Check English fallback message
        assert "not yet clearly identified" in causes[0].lower()


# =============================================================================
# Recommendations
# =============================================================================

class TestDeriveRecommendations:
    """Test recommendation generation from clusters."""

    def test_generates_recommendations(self, sample_clusters):
        recs = derive_recommendations(sample_clusters)
        assert len(recs) > 0

    def test_no_duplicates(self, sample_clusters):
        recs = derive_recommendations(sample_clusters)
        assert len(recs) == len(set(recs))


# =============================================================================
# Severity
# =============================================================================

class TestDeriveSeverity:
    """Test severity classification."""

    def test_high_severity(self):
        clusters = [
            ErrorCluster(label="mod_jk workerEnv error state", count=150, services=["mod_jk"], samples=["x"]),
        ]
        assert derive_severity(clusters) == "HIGH"

    def test_medium_severity(self):
        clusters = [
            ErrorCluster(label="Directory access forbidden", count=30, services=["apache"], samples=["x"]),
        ]
        assert derive_severity(clusters) == "MEDIUM"

    def test_low_severity(self):
        clusters = [
            ErrorCluster(label="Other apache issue", count=2, services=["apache"], samples=["x"]),
        ]
        assert derive_severity(clusters) == "LOW"


# =============================================================================
# Evidence
# =============================================================================

class TestCollectEvidence:
    """Test evidence collection from clusters."""

    def test_collects_samples(self, sample_clusters):
        evidence = collect_evidence(sample_clusters)
        assert len(evidence) > 0
        assert len(evidence) <= 6


# =============================================================================
# Action Checks
# =============================================================================

class TestDeriveActionChecks:
    """Test action check generation for tool execution."""

    def test_mod_jk_generates_checks(self, sample_clusters):
        checks = derive_action_checks(sample_clusters)
        assert len(checks) > 0
        tools_used = {c["tool"] for c in checks}
        assert "check_http_endpoint" in tools_used
        assert "check_tcp_port" in tools_used

    def test_checks_have_required_fields(self, sample_clusters):
        checks = derive_action_checks(sample_clusters)
        required = {"title", "tool", "args", "command", "purpose", "priority", "category"}
        for check in checks:
            assert required.issubset(check.keys())

    def test_sorted_by_priority(self, sample_clusters):
        checks = derive_action_checks(sample_clusters)
        for i in range(len(checks) - 1):
            assert checks[i]["priority"] <= checks[i + 1]["priority"]
