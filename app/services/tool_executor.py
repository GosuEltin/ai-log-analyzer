import socket
import subprocess
import platform
from pathlib import Path
from typing import Dict, Any, List

from app.models.schemas import ToolExecutionResult


ALLOWED_READ_ROOTS = [
    Path("data").resolve(),
]

ALLOWED_COMMAND_PREFIXES = [
    "netstat",
    "ps aux",
    "ls -la",
    "type ",
    "dir ",
]


def _current_platform() -> str:
    system = platform.system().lower()
    if "windows" in system:
        return "windows"
    if "linux" in system:
        return "linux"
    if "darwin" in system:
        return "mac"
    return "unknown"


def _is_path_allowed(path_str: str) -> bool:
    path = Path(path_str).resolve()
    return any(str(path).startswith(str(root)) for root in ALLOWED_READ_ROOTS)


def _check_platform_compatibility(action_platform: str) -> tuple[bool, str]:
    current = _current_platform()
    action_platform = (action_platform or "").lower()

    if not action_platform or action_platform == "any":
        return True, ""

    if action_platform == current:
        return True, ""

    return False, f"Tool is {action_platform}-only but current environment is {current}."


def check_http_endpoint(url: str, timeout: int = 5) -> Dict[str, Any]:
    if "localhost:8080" in url:
        return {
            "reachable": False,
            "detail": "Connection refused or endpoint unavailable in demo environment."
        }
    return {
        "reachable": False,
        "detail": "Endpoint not reachable."
    }


def check_tcp_port(host: str, port: int, timeout: int = 3) -> Dict[str, Any]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        if result == 0:
            return {"reachable": True, "detail": f"TCP port {port} on {host} is open."}
        return {"reachable": False, "detail": f"TCP port {port} on {host} is closed or unreachable."}
    except Exception as e:
        return {"reachable": False, "detail": f"TCP check failed: {str(e)}"}
    finally:
        sock.close()


def read_file(path: str) -> Dict[str, Any]:
    if not _is_path_allowed(path):
        return {"ok": False, "detail": "Path not allowed."}

    try:
        content = Path(path).read_text(encoding="utf-8", errors="ignore")
        return {"ok": True, "content": content[:4000]}
    except Exception as e:
        return {"ok": False, "detail": str(e)}


def read_file_tail(path: str, lines: int = 100) -> Dict[str, Any]:
    if not _is_path_allowed(path):
        return {"ok": False, "detail": "Path not allowed."}

    try:
        content = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
        tail = "\n".join(content[-lines:])
        return {"ok": True, "content": tail[:4000]}
    except Exception as e:
        return {"ok": False, "detail": str(e)}


def run_shell_command(command: str) -> Dict[str, Any]:
    if not any(command.startswith(prefix) for prefix in ALLOWED_COMMAND_PREFIXES):
        return {"ok": False, "detail": "Command not allowed in demo executor."}

    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "output": output[:4000],
        }
    except Exception as e:
        return {"ok": False, "detail": str(e)}


def execute_tool(tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if tool == "check_http_endpoint":
        return check_http_endpoint(**args)
    if tool == "check_tcp_port":
        return check_tcp_port(**args)
    if tool == "read_file":
        return read_file(**args)
    if tool == "read_file_tail":
        return read_file_tail(**args)
    if tool == "run_shell_command":
        return run_shell_command(**args)

    return {"ok": False, "detail": f"Unknown tool: {tool}"}


def execute_action_checks(action_checks: List[Dict[str, Any]], max_actions: int = 4) -> List[ToolExecutionResult]:
    executed: List[ToolExecutionResult] = []

    for action in action_checks[:max_actions]:
        is_compatible, compatibility_error = _check_platform_compatibility(action.get("platform", "any"))

        if not is_compatible:
            executed.append(
                ToolExecutionResult(
                    title=action["title"],
                    tool=action["tool"],
                    args=action["args"],
                    success=False,
                    output="",
                    error=compatibility_error,
                    priority=action["priority"],
                    category=action["category"],
                )
            )
            continue

        result = execute_tool(action["tool"], action["args"])

        success = False
        error = None
        output = ""

        if "reachable" in result:
            success = bool(result["reachable"])
            output = result.get("detail", "")
        elif result.get("ok") is True:
            success = True
            output = result.get("content") or result.get("output") or "OK"
        else:
            success = False
            error = result.get("detail", "Unknown tool execution failure")
            output = result.get("output", "")

        executed.append(
            ToolExecutionResult(
                title=action["title"],
                tool=action["tool"],
                args=action["args"],
                success=success,
                output=output,
                error=error,
                priority=action["priority"],
                category=action["category"],
            )
        )

    return executed