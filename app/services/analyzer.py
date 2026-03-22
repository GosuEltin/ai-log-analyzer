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
        samples = [item.raw for item in items[:3]]

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
            "Nhiều khả năng backend worker/Tomcat không phản hồi, timeout, hoặc không accept kết nối từ Apache."
        )
        causes.append(
            "Có thể kết nối Apache tới backend qua AJP bị lỗi hoặc cổng backend không mở đúng."
        )
        causes.append(
            "Cấu hình workers2.properties có thể liên quan, nhưng nên kiểm tra sau khi đã xác nhận backend và kết nối."
        )

    if "Apache scoreboard child mismatch" in labels:
        causes.append(
            "Có dấu hiệu Apache hoặc jk2 đang gặp vấn đề đồng bộ trạng thái child process trong scoreboard."
        )

    if "Apache child initialization issue" in labels:
        causes.append(
            "Có thể quá trình khởi tạo child process/mod_jk gặp lỗi khi backend chưa sẵn sàng."
        )

    if "Directory access forbidden" in labels or "Client access forbidden" in labels:
        causes.append(
            "Có một issue phụ về access control hoặc thiếu index file trong /var/www/html/."
        )

    if not causes:
        causes.append(
            "Chưa xác định rõ nguyên nhân chính, cần kiểm tra backend, kết nối AJP và log riêng của mod_jk."
        )

    return causes
def derive_recommendations(clusters):
    labels = [c.label for c in clusters]
    recommendations = []

    if "mod_jk workerEnv error state" in labels:
        recommendations.extend([
            "Ưu tiên xác nhận backend/Tomcat còn chạy hay không.",
            "Kiểm tra Apache có kết nối được tới backend qua AJP hay không.",
            "Kiểm tra cổng AJP của backend có đang mở không.",
            "Kiểm tra log riêng của mod_jk bằng JkLogFile, ví dụ logs/mod_jk.log.",
            "Chỉ sau đó mới rà lại workers2.properties hoặc workers.properties.",
        ])

    if "Apache scoreboard child mismatch" in labels:
        recommendations.extend([
            "Kiểm tra log restart/reload Apache gần thời điểm phát sinh lỗi scoreboard.",
            "Kiểm tra child process có bị restart bất thường hay không.",
        ])

    if "Apache child initialization issue" in labels:
        recommendations.extend([
            "Kiểm tra backend có sẵn sàng trước khi Apache chuyển tiếp request hay không.",
        ])

    if "Directory access forbidden" in labels or "Client access forbidden" in labels:
        recommendations.extend([
            "Xử lý sau: kiểm tra DirectoryIndex, index.html, Require, AllowOverride và .htaccess cho /var/www/html/.",
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
                "title": "Kiểm tra backend HTTP trực tiếp",
                "tool": "check_http_endpoint",
                "args": {
                    "url": "http://localhost:8080",
                    "timeout": 5
                },
                "command": "curl http://localhost:8080",
                "purpose": "Xác nhận Tomcat/backend có phản hồi hay không.",
                "priority": 1,
                "category": "backend_health",
                "platform": "any",
            },
            {
                "title": "Kiểm tra cổng AJP của backend",
                "tool": "check_tcp_port",
                "args": {
                    "host": "localhost",
                    "port": 8009,
                    "timeout": 3
                },
                "command": "telnet localhost 8009",
                "purpose": "Xác nhận Apache có thể mở kết nối tới backend qua AJP hay không.",
                "priority": 1,
                "category": "network_connectivity",
                "platform": "any",
            },
            {
                "title": "Đọc log riêng của mod_jk",
                "tool": "read_file_tail",
                "args": {
                    "path": "data/mock_runtime/mod_jk.log",
                    "lines": 80
                },
                "command": "tail -n 80 data/mock_runtime/mod_jk.log",
                "purpose": "Xem log debug chuyên biệt của mod_jk để xác định lỗi kết nối/backend.",
                "priority": 2,
                "category": "log_inspection",
                "platform": "any",
            },
            {
                "title": "Rà cấu hình workers2.properties",
                "tool": "read_file",
                "args": {
                    "path": "data/mock_runtime/workers2.properties"
                },
                "command": "cat data/mock_runtime/workers2.properties",
                "purpose": "Kiểm tra host, port, route, timeout và mapping sau khi đã xác nhận backend/kết nối.",
                "priority": 3,
                "category": "config_review",
                "platform": "any",
            },
            {
                "title": "Kiểm tra port AJP đang listen",
                "tool": "run_shell_command",
                "args": {
                    "command": "netstat -tulnp | grep 8009"
                },
                "command": "netstat -tulnp | grep 8009",
                "purpose": "Xác nhận backend đang mở cổng AJP.",
                "priority": 3,
                "category": "port_inspection",
                "platform": "linux",
            },
        ])

    if "Apache scoreboard child mismatch" in labels:
        checks.append(
            {
                "title": "Kiểm tra restart hoặc reload Apache",
                "tool": "read_file_tail",
                "args": {
                    "path": "data/mock_runtime/error_log",
                    "lines": 120
                },
                "command": "tail -n 120 data/mock_runtime/error_log",
                "purpose": "Xác định lỗi scoreboard có liên quan đến restart hoặc reload bất thường hay không.",
                "priority": 2,
                "category": "log_inspection",
                "platform": "any",
            }
        )

    if "Apache child initialization issue" in labels:
        checks.append(
            {
                "title": "Kiểm tra tiến trình backend",
                "tool": "run_shell_command",
                "args": {
                    "command": "ps aux | grep -i tomcat"
                },
                "command": "ps aux | grep -i tomcat",
                "purpose": "Xác nhận backend đã sẵn sàng trước khi Apache/mod_jk chuyển tiếp request.",
                "priority": 2,
                "category": "process_inspection",
                "platform": "linux",
            }
        )

    if "Directory access forbidden" in labels or "Client access forbidden" in labels:
        checks.append(
            {
                "title": "Kiểm tra file index trong /var/www/html/",
                "tool": "run_shell_command",
                "args": {
                    "command": "ls -la /var/www/html/"
                },
                "command": "ls -la /var/www/html/",
                "purpose": "Xác nhận thư mục có index.html hoặc file index phù hợp; đây là issue phụ, xử lý sau.",
                "priority": 4,
                "category": "filesystem_check",
                "platform": "linux",
            }
        )

    checks.sort(key=lambda x: x["priority"])
    return checks