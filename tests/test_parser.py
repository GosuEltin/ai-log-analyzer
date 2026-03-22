"""
Tests for app.services.parser — Log parsing and normalization.

Validates:
- Apache error log format parsing
- Log level normalization (notice→INFO, error→ERROR, etc.)
- Service inference from message content
- Edge cases: empty input, malformed lines, mixed content
"""
import pytest

from app.services.parser import parse_log_text, normalize_level, infer_service_from_message


# =============================================================================
# Log Level Normalization
# =============================================================================

class TestNormalizeLevel:
    """Test log-level string normalization."""

    @pytest.mark.parametrize("raw_level,expected", [
        ("notice", "INFO"),
        ("info", "INFO"),
        ("warn", "WARN"),
        ("warning", "WARN"),
        ("error", "ERROR"),
        ("crit", "ERROR"),
        ("critical", "ERROR"),
        ("debug", "DEBUG"),
    ])
    def test_known_levels(self, raw_level, expected):
        assert normalize_level(raw_level) == expected

    def test_unknown_level_uppercased(self):
        assert normalize_level("alert") == "ALERT"

    def test_whitespace_handling(self):
        assert normalize_level("  error  ") == "ERROR"


# =============================================================================
# Service Inference
# =============================================================================

class TestInferService:
    """Test service name inference from log message."""

    def test_mod_jk_message(self):
        assert infer_service_from_message("mod_jk child workerEnv in error state 6") == "mod_jk"

    def test_workerenv_message(self):
        assert infer_service_from_message("workerEnv.init() ok /etc/httpd/conf/workers2.properties") == "workerEnv"

    def test_jk2_init_message(self):
        assert infer_service_from_message("jk2_init() Found child 1567 in scoreboard") == "jk2_init"

    def test_client_message(self):
        assert infer_service_from_message("[client 192.168.1.1] Directory index forbidden") == "client_request"

    def test_generic_message(self):
        assert infer_service_from_message("something else happened") == "apache"


# =============================================================================
# Full Log Parsing
# =============================================================================

class TestParseLogText:
    """Test full log text parsing pipeline."""

    def test_parses_valid_lines(self, sample_log_text):
        records, failed = parse_log_text(sample_log_text)
        assert len(records) == 7
        assert len(failed) == 0

    def test_record_fields_populated(self, sample_log_text):
        records, _ = parse_log_text(sample_log_text)
        first = records[0]
        assert first.timestamp == "Sun Dec 04 04:47:44 2005"
        assert first.level == "INFO"  # notice → INFO
        assert first.service == "workerEnv"
        assert "workerEnv.init()" in first.message

    def test_error_level_parsed(self, sample_log_text):
        records, _ = parse_log_text(sample_log_text)
        error_records = [r for r in records if r.level == "ERROR"]
        assert len(error_records) >= 4

    def test_empty_input(self):
        records, failed = parse_log_text("")
        assert records == []
        assert failed == []

    def test_blank_lines_skipped(self):
        records, failed = parse_log_text("\n\n\n")
        assert records == []
        assert failed == []

    def test_malformed_lines_go_to_failed(self):
        text = "this is not a valid log line\nanother bad line"
        records, failed = parse_log_text(text)
        assert len(records) == 0
        assert len(failed) == 2

    def test_mixed_valid_and_invalid(self):
        text = (
            "[Sun Dec 04 04:47:44 2005] [error] mod_jk child workerEnv in error state 6\n"
            "random garbage line\n"
            "[Sun Dec 04 04:47:45 2005] [notice] workerEnv.init() ok\n"
        )
        records, failed = parse_log_text(text)
        assert len(records) == 2
        assert len(failed) == 1

    def test_raw_field_preserves_original(self, sample_log_text):
        records, _ = parse_log_text(sample_log_text)
        for r in records:
            assert r.raw.strip() != ""
            assert "[" in r.raw  # original format preserved
