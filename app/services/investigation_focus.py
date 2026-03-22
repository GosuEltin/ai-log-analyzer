from typing import List, Dict, Any


BACKEND_FOCUS_KEYWORDS = [
    "tomcat",
    "ajp",
    "port",
    "backend",
    "connectivity",
    "connection",
    "worker",
    "workerenv",
]

ACCESS_FOCUS_KEYWORDS = [
    "directory",
    "forbidden",
    "access",
    "htaccess",
    "allowoverride",
    "index",
    "directoryindex",
]


def detect_focus_mode(user_query: str) -> str:
    q = (user_query or "").lower().strip()
    if not q:
        return "general"

    backend_hits = sum(1 for kw in BACKEND_FOCUS_KEYWORDS if kw in q)
    access_hits = sum(1 for kw in ACCESS_FOCUS_KEYWORDS if kw in q)

    if backend_hits >= access_hits and backend_hits > 0:
        return "backend_connectivity"

    if access_hits > backend_hits and access_hits > 0:
        return "access_control"

    return "general"


def is_backend_related_label(label: str) -> bool:
    label = (label or "").lower()
    return any(x in label for x in [
        "workerenv",
        "scoreboard",
        "child initialization",
        "mod_jk",
        "backend",
        "ajp",
    ])


def is_access_related_label(label: str) -> bool:
    label = (label or "").lower()
    return any(x in label for x in [
        "directory access",
        "client access",
        "forbidden",
        "htaccess",
    ])


def filter_clusters_by_focus(clusters: List[Dict[str, Any]], focus_mode: str) -> List[Dict[str, Any]]:
    if focus_mode == "general":
        return clusters

    primary = []
    secondary = []

    for cluster in clusters:
        label = cluster.get("label", "")

        if focus_mode == "backend_connectivity":
            if is_backend_related_label(label):
                primary.append(cluster)
            else:
                secondary.append(cluster)

        elif focus_mode == "access_control":
            if is_access_related_label(label):
                primary.append(cluster)
            else:
                secondary.append(cluster)

    return primary + secondary


def filter_list_by_focus(items: List[str], focus_mode: str) -> List[str]:
    if focus_mode == "general":
        return items

    primary = []
    secondary = []

    for item in items:
        lower = item.lower()

        if focus_mode == "backend_connectivity":
            if any(k in lower for k in [
                "tomcat", "backend", "ajp", "worker", "port", "connect", "timeout", "scoreboard"
            ]):
                primary.append(item)
            else:
                secondary.append(item)

        elif focus_mode == "access_control":
            if any(k in lower for k in [
                "directory", "access", "forbidden", "index", "htaccess", "allowoverride"
            ]):
                primary.append(item)
            else:
                secondary.append(item)

    # Cắt gọn mạnh theo focus mode
    if focus_mode == "backend_connectivity":
        return (primary[:4] if primary else []) + (secondary[:1] if secondary else [])

    if focus_mode == "access_control":
        return (primary[:4] if primary else []) + (secondary[:1] if secondary else [])

    return primary + secondary


def filter_action_checks_by_focus(action_checks: List[Dict[str, Any]], focus_mode: str) -> List[Dict[str, Any]]:
    if focus_mode == "general":
        return action_checks

    primary = []
    secondary = []

    for action in action_checks:
        category = action.get("category", "").lower()
        title = action.get("title", "").lower()
        purpose = action.get("purpose", "").lower()

        if focus_mode == "backend_connectivity":
            if category in {
                "backend_health",
                "network_connectivity",
                "port_inspection",
                "log_inspection",
                "process_inspection",
                "config_review",
            } and not any(x in title or x in purpose for x in ["index", "directory", "html", "htaccess"]):
                primary.append(action)
            else:
                secondary.append(action)

        elif focus_mode == "access_control":
            if category in {"filesystem_check", "config_review", "log_inspection"} and any(
                x in title or x in purpose for x in ["index", "directory", "access", "htaccess"]
            ):
                primary.append(action)
            else:
                secondary.append(action)

    if focus_mode == "backend_connectivity":
        return primary[:4]

    if focus_mode == "access_control":
        return primary[:4]

    return primary + secondary


def annotate_issue_roles(clusters: List[Dict[str, Any]], focus_mode: str) -> tuple[str, List[str]]:
    if not clusters:
        return "", []

    primary_issue = clusters[0].get("label", "")
    secondary_issues = [c.get("label", "") for c in clusters[1:] if c.get("label", "")]

    if focus_mode == "backend_connectivity":
        backend_first = [c.get("label", "") for c in clusters if is_backend_related_label(c.get("label", ""))]
        non_backend = [c.get("label", "") for c in clusters if not is_backend_related_label(c.get("label", ""))]
        if backend_first:
            primary_issue = backend_first[0]
            secondary_issues = backend_first[1:] + non_backend

    if focus_mode == "access_control":
        access_first = [c.get("label", "") for c in clusters if is_access_related_label(c.get("label", ""))]
        non_access = [c.get("label", "") for c in clusters if not is_access_related_label(c.get("label", ""))]
        if access_first:
            primary_issue = access_first[0]
            secondary_issues = access_first[1:] + non_access

    seen = set()
    dedup_secondary = []
    for item in secondary_issues:
        if item and item != primary_issue and item not in seen:
            seen.add(item)
            dedup_secondary.append(item)

    return primary_issue, dedup_secondary[:3]