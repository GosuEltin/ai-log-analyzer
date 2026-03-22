import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple

from app.models.schemas import LogRecord, ErrorCluster, Overview


def normalize_message(message: str) -> str:
    msg = message.lower()

    # Loại bỏ id động để gom nhóm tốt hơn
    msg = re.sub(r"request_id=\w+", "request_id=<id>", msg)
    msg = re.sub(r"user=\d+", "user=<id>", msg)
    msg = re.sub(r"\b\d+\b", "<num>", msg)

    return msg


def classify_message(message: str) -> str:
    msg = message.lower()

    if "mod_jk child workerenv in error state" in msg:
        return "mod_jk workerEnv error state"

    if "directory index forbidden by rule" in msg:
        return "Directory access forbidden"

    if "can't find child" in msg and "scoreboard" in msg:
        return "Apache scoreboard child mismatch"

    if "child init" in msg:
        return "Apache child initialization issue"

    if "workerenv.init() ok" in msg:
        return "workerEnv initialized successfully"

    if "jk2_init() found child" in msg:
        return "jk2 child discovered"

    if "client" in msg and "forbidden" in msg:
        return "Client access forbidden"

    return "Other apache issue"


def build_overview(records: List[LogRecord], failed_lines: List[str]) -> Overview:
    level_counter = Counter(r.level for r in records)
    service_counter = Counter(r.service for r in records)

    return Overview(
        total_lines=len(records) + len(failed_lines),
        parsed_lines=len(records),
        failed_lines=len(failed_lines),
        failed_lines_content=failed_lines[:50],  # Limit to 50 for performance
        info_count=level_counter.get("INFO", 0),
        warn_count=level_counter.get("WARN", 0),
        error_count=level_counter.get("ERROR", 0),
        top_services=dict(service_counter.most_common(5)),
    )


def build_clusters(records: List[LogRecord]) -> List[ErrorCluster]:
    grouped: Dict[str, List[LogRecord]] = defaultdict(list)

    # Chỉ gom WARN/ERROR để có ý nghĩa hơn
    for record in records:
        if record.level in {"WARN", "ERROR"}:
            label = classify_message(record.message)
            grouped[label].append(record)

    clusters: List[ErrorCluster] = []

    for label, items in grouped.items():
        service_counts = Counter(item.service for item in items)
        services = [svc for svc, _ in service_counts.most_common(3)]
        
        # Get ALL unique samples (deduplicate identical raw log lines)
        seen = set()
        samples = []
        for item in items:
            if item.raw not in seen:
                if len(samples) < 50:  # Limit max samples retained per cluster
                    samples.append(item.raw)
                seen.add(item.raw)

        clusters.append(
            ErrorCluster(
                label=label,
                count=len(items),
                services=services,
                samples=samples,
            )
        )

    clusters.sort(key=lambda c: c.count, reverse=True)
    return clusters


def derive_probable_causes(clusters):
    labels = [c.label for c in clusters]
    causes = []

    if "mod_jk workerEnv error state" in labels:
        causes.append(
            "It is highly likely that the backend worker or Tomcat is not responding, timing out, or not accepting connections from Apache."
        )
        causes.append(
            "The AJP connection between Apache and the backend might be failing, or the backend port is not correctly open."
        )
        causes.append(
            "Configuration issues in workers2.properties could be related, but should be checked after confirming backend connectivity."
        )

    if "Apache scoreboard child mismatch" in labels:
        causes.append(
            "There are signs that Apache or jk2 is having issues synchronizing child process states within the scoreboard."
        )

    if "Apache child initialization issue" in labels:
        causes.append(
            "The child process or mod_jk initialization might have failed while the backend was not yet ready."
        )

    if "Directory access forbidden" in labels or "Client access forbidden" in labels:
        causes.append(
            "There is a secondary issue regarding access control or a missing index file in /var/www/html/."
        )

    if not causes:
        causes.append(
            "The primary cause is not yet clearly identified; check backend status, AJP connectivity, and mod_jk specific logs."
        )

    return causes
def derive_recommendations(clusters):
    labels = [c.label for c in clusters]
    recommendations = []

    if "mod_jk workerEnv error state" in labels:
        recommendations.extend([
            "Prioritize confirming if backend/Tomcat is still running.",
            "Verify if Apache can connect to the backend via the AJP port.",
            "Check if the AJP port on the backend is actually open.",
            "Inspect the dedicated mod_jk log file (e.g., mod_jk.log or similar).",
            "Only review workers2.properties or workers.properties after confirming backend health.",
        ])

    if "Apache scoreboard child mismatch" in labels:
        recommendations.extend([
            "Check for Apache restart or reload events near the time of scoreboard errors.",
            "Verify if child processes are restarting unexpectedly.",
        ])

    if "Apache child initialization issue" in labels:
        recommendations.extend([
            "Ensure the backend is fully initialized before Apache starts forwarding requests.",
        ])

    if "Directory access forbidden" in labels or "Client access forbidden" in labels:
        recommendations.extend([
            "Secondary task: check DirectoryIndex, index.html, Require, AllowOverride, and .htaccess for /var/www/html/.",
        ])

    return list(dict.fromkeys(recommendations))
def collect_evidence(clusters: List[ErrorCluster]) -> List[str]:
    evidence = []
    for cluster in clusters[:3]:
        evidence.extend(cluster.samples[:2])
    return evidence[:6]
def derive_severity(clusters) -> str:
    label_counts = {c.label: c.count for c in clusters}

    if label_counts.get("mod_jk workerEnv error state", 0) >= 100:
        return "HIGH"
    if label_counts.get("Directory access forbidden", 0) >= 20:
        return "MEDIUM"
    return "LOW"
def derive_action_checks(clusters):
    labels = [c.label for c in clusters]
    checks = []

    if "mod_jk workerEnv error state" in labels:
        checks.extend([
            {
                "title": "Check Frontend-to-Backend HTTP",
                "tool": "check_http_endpoint",
                "args": {
                    "url": "http://localhost:8080",
                    "timeout": 5
                },
                "command": "curl http://localhost:8080",
                "purpose": "Verify if Tomcat or the backend is responding to HTTP requests.",
                "priority": 1,
                "category": "backend_health",
                "platform": "any",
            },
            {
                "title": "Check Backend AJP Port",
                "tool": "check_tcp_port",
                "args": {
                    "host": "localhost",
                    "port": 8009,
                    "timeout": 3
                },
                "command": "telnet localhost 8009",
                "purpose": "Confirm if the AJP port is open and accessible from the web server.",
                "priority": 1,
                "category": "network_connectivity",
                "platform": "any",
            },
            {
                "title": "Inspect Dedicated mod_jk Logs",
                "tool": "read_file_tail",
                "args": {
                    "path": "data/mock_runtime/mod_jk.log",
                    "lines": 80
                },
                "command": "tail -n 80 data/mock_runtime/mod_jk.log",
                "purpose": "Examine specific mod_jk logs for low-level connection errors.",
                "priority": 2,
                "category": "log_inspection",
                "platform": "any",
            },
            {
                "title": "Review workers2.properties Config",
                "tool": "read_file",
                "args": {
                    "path": "data/mock_runtime/workers2.properties"
                },
                "command": "cat data/mock_runtime/workers2.properties",
                "purpose": "Check host/port/route mappings in the connector configuration.",
                "priority": 3,
                "category": "config_review",
                "platform": "any",
            },
            {
                "title": "Identify Listening AJP Port",
                "tool": "run_shell_command",
                "args": {
                    "command": "netstat -tulnp | grep 8009"
                },
                "command": "netstat -tulnp | grep 8009",
                "purpose": "Verify which process is actually listening on the AJP port.",
                "priority": 3,
                "category": "port_inspection",
                "platform": "linux",
            },
        ])

    if "Apache scoreboard child mismatch" in labels:
        checks.append(
            {
                "title": "Check Apache Lifecycle Events",
                "tool": "read_file_tail",
                "args": {
                    "path": "data/mock_runtime/error_log",
                    "lines": 120
                },
                "command": "tail -n 120 data/mock_runtime/error_log",
                "purpose": "Determine if scoreboard issues correlate with recent restarts or reloads.",
                "priority": 2,
                "category": "log_inspection",
                "platform": "any",
            }
        )

    if "Apache child initialization issue" in labels:
        checks.append(
            {
                "title": "Check Backend Process Status",
                "tool": "run_shell_command",
                "args": {
                    "command": "ps aux | grep -i tomcat"
                },
                "command": "ps aux | grep -i tomcat",
                "purpose": "Ensure the backend process is running before it accepts traffic.",
                "priority": 2,
                "category": "process_inspection",
                "platform": "linux",
            }
        )

    if "Directory access forbidden" in labels or "Client access forbidden" in labels:
        checks.append(
            {
                "title": "Verify Index Files in WebRoot",
                "tool": "run_shell_command",
                "args": {
                    "command": "ls -la /var/www/html/"
                },
                "command": "ls -la /var/www/html/",
                "purpose": "Confirm existence of index.html; this is a secondary issue.",
                "priority": 4,
                "category": "filesystem_check",
                "platform": "linux",
            }
        )

    checks.sort(key=lambda x: x["priority"])
    return checks