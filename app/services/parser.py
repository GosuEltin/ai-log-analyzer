import re
from typing import List, Tuple
from app.models.schemas import LogRecord

# Ví dụ:
# [Sun Dec 04 04:47:44 2005] [notice] workerEnv.init() ok /etc/httpd/conf/workers2.properties
# [Sun Dec 04 04:47:44 2005] [error] mod_jk child workerEnv in error state 6

APACHE_LOG_PATTERN = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\]\s+\[(?P<level>[^\]]+)\]\s+(?P<message>.+)$",
    re.IGNORECASE
)


def infer_service_from_message(message: str) -> str:
    msg = message.lower()

    if "mod_jk" in msg:
        return "mod_jk"
    if "workerenv" in msg:
        return "workerEnv"
    if "jk2_init" in msg:
        return "jk2_init"
    if "client" in msg:
        return "client_request"
    return "apache"


def normalize_level(level: str) -> str:
    level = level.strip().lower()

    mapping = {
        "notice": "INFO",
        "info": "INFO",
        "warn": "WARN",
        "warning": "WARN",
        "error": "ERROR",
        "debug": "DEBUG",
        "crit": "ERROR",
        "critical": "ERROR",
    }

    return mapping.get(level, level.upper())


def parse_log_text(text: str) -> Tuple[List[LogRecord], List[str]]:
    parsed_records: List[LogRecord] = []
    failed_lines: List[str] = []

    for line in text.splitlines():
        raw = line.strip()
        if not raw:
            continue

        match = APACHE_LOG_PATTERN.match(raw)
        if match:
            message = match.group("message")
            record = LogRecord(
                timestamp=match.group("timestamp"),
                level=normalize_level(match.group("level")),
                service=infer_service_from_message(message),
                message=message,
                raw=raw,
            )
            parsed_records.append(record)
        else:
            failed_lines.append(raw)

    return parsed_records, failed_lines