"""
Shared fixtures for all tests.
"""
import pytest
from app.models.schemas import LogRecord, ErrorCluster


# =============================================================================
# Sample log data fixtures
# =============================================================================

SAMPLE_APACHE_LOG = """\
[Sun Dec 04 04:47:44 2005] [notice] workerEnv.init() ok /etc/httpd/conf/workers2.properties
[Sun Dec 04 04:47:44 2005] [error] mod_jk child workerEnv in error state 6
[Sun Dec 04 04:47:44 2005] [error] mod_jk child workerEnv in error state 6
[Sun Dec 04 04:47:45 2005] [error] [client 192.168.1.1] Directory index forbidden by rule: /var/www/html/
[Sun Dec 04 04:47:46 2005] [error] jk2_init() Can't find child 1566 in scoreboard
[Sun Dec 04 04:47:46 2005] [notice] jk2_init() Found child 1567 in scoreboard
[Sun Dec 04 04:47:47 2005] [error] mod_jk child workerEnv in error state 7
"""


@pytest.fixture
def sample_log_text():
    """Raw Apache error log text (7 lines)."""
    return SAMPLE_APACHE_LOG


@pytest.fixture
def parsed_records():
    """Pre-parsed LogRecord list from the sample log."""
    from app.services.parser import parse_log_text
    records, _ = parse_log_text(SAMPLE_APACHE_LOG)
    return records


@pytest.fixture
def sample_clusters(parsed_records):
    """Pre-built clusters from the sample log."""
    from app.services.analyzer import build_clusters
    return build_clusters(parsed_records)


@pytest.fixture
def sample_error_cluster():
    """Single ErrorCluster for unit testing."""
    return ErrorCluster(
        label="mod_jk workerEnv error state",
        count=120,
        services=["mod_jk"],
        samples=[
            "[Sun Dec 04 04:47:44 2005] [error] mod_jk child workerEnv in error state 6",
        ],
    )
