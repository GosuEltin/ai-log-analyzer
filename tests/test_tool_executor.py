"""
Tests for app.services.tool_executor — Tool execution engine.

Validates:
- Individual tool functions (HTTP check, TCP check, file read, tail, shell)
- Path security checks (sandboxing)
- Platform compatibility checks
- Tool dispatch (execute_tool)
- Batch execution (execute_action_checks)
"""
import pytest
from pathlib import Path
from unittest.mock import patch

from app.services.tool_executor import (
    check_http_endpoint,
    check_tcp_port,
    read_file,
    read_file_tail,
    run_shell_command,
    execute_tool,
    execute_action_checks,
    _is_path_allowed,
    _check_platform_compatibility,
    _current_platform,
)


# =============================================================================
# Path Security
# =============================================================================

class TestPathSecurity:
    """Test file path sandboxing."""

    def test_allowed_path(self):
        assert _is_path_allowed("data/mock_runtime/mod_jk.log") is True

    def test_disallowed_path(self):
        assert _is_path_allowed("/etc/passwd") is False
        assert _is_path_allowed("C:\\Windows\\System32\\config") is False


# =============================================================================
# Platform Compatibility
# =============================================================================

class TestPlatformCompatibility:
    """Test platform compatibility checks."""

    def test_any_platform_allowed(self):
        ok, err = _check_platform_compatibility("any")
        assert ok is True

    def test_empty_platform_allowed(self):
        ok, err = _check_platform_compatibility("")
        assert ok is True

    def test_current_platform_allowed(self):
        current = _current_platform()
        ok, err = _check_platform_compatibility(current)
        assert ok is True

    def test_wrong_platform_rejected(self):
        fake = "commodore64"
        ok, err = _check_platform_compatibility(fake)
        assert ok is False
        assert "commodore64" in err


# =============================================================================
# HTTP Endpoint Check
# =============================================================================

class TestCheckHttpEndpoint:
    """Test HTTP endpoint checking (mock/demo mode)."""

    def test_localhost_8080_unreachable(self):
        result = check_http_endpoint("http://localhost:8080")
        assert result["reachable"] is False

    def test_unknown_endpoint(self):
        result = check_http_endpoint("http://example.com:9999")
        assert result["reachable"] is False


# =============================================================================
# TCP Port Check
# =============================================================================

class TestCheckTcpPort:
    """Test TCP port connectivity."""

    def test_closed_port(self):
        result = check_tcp_port("127.0.0.1", 39999, timeout=1)
        assert result["reachable"] is False
        assert "closed" in result["detail"].lower() or "unreachable" in result["detail"].lower()


# =============================================================================
# File Operations
# =============================================================================

class TestReadFile:
    """Test file reading with security."""

    def test_read_allowed_file(self):
        result = read_file("data/mock_runtime/workers2.properties")
        assert result["ok"] is True
        assert "worker1" in result.get("content", "")

    def test_read_disallowed_path(self):
        result = read_file("/etc/passwd")
        assert result["ok"] is False


class TestReadFileTail:
    """Test file tail reading."""

    def test_read_tail(self):
        result = read_file_tail("data/mock_runtime/mod_jk.log", lines=10)
        assert result["ok"] is True
        assert "content" in result

    def test_disallowed_path(self):
        result = read_file_tail("/etc/shadow", lines=10)
        assert result["ok"] is False


# =============================================================================
# Shell Command
# =============================================================================

class TestRunShellCommand:
    """Test shell command execution with allowlist."""

    def test_blocked_command(self):
        result = run_shell_command("rm -rf /")
        assert result["ok"] is False
        assert "not allowed" in result["detail"].lower()

    def test_allowed_dir_command(self):
        """dir command should be in allowlist."""
        result = run_shell_command("dir data")
        assert "ok" in result


# =============================================================================
# Tool Dispatch
# =============================================================================

class TestExecuteTool:
    """Test central tool dispatch."""

    def test_unknown_tool(self):
        result = execute_tool("unknown_tool", {})
        assert result["ok"] is False
        assert "Unknown tool" in result["detail"]

    def test_dispatch_check_http(self):
        result = execute_tool("check_http_endpoint", {"url": "http://localhost:8080"})
        assert "reachable" in result

    def test_dispatch_read_file(self):
        result = execute_tool("read_file", {"path": "data/mock_runtime/workers2.properties"})
        assert result["ok"] is True


# =============================================================================
# Batch Execution
# =============================================================================

class TestExecuteActionChecks:
    """Test batch action check execution."""

    def test_respects_max_actions(self):
        actions = [
            {
                "title": f"Action {i}",
                "tool": "check_http_endpoint",
                "args": {"url": "http://localhost:8080"},
                "priority": 1,
                "category": "test",
                "platform": "any",
            }
            for i in range(10)
        ]
        results = execute_action_checks(actions, max_actions=3)
        assert len(results) == 3

    def test_returns_tool_execution_results(self):
        actions = [
            {
                "title": "Test HTTP",
                "tool": "check_http_endpoint",
                "args": {"url": "http://localhost:8080"},
                "priority": 1,
                "category": "backend_health",
                "platform": "any",
            }
        ]
        results = execute_action_checks(actions)
        assert len(results) == 1
        r = results[0]
        assert r.title == "Test HTTP"
        assert r.tool == "check_http_endpoint"
        assert r.category == "backend_health"

    def test_incompatible_platform_handled(self):
        actions = [
            {
                "title": "Linux only",
                "tool": "run_shell_command",
                "args": {"command": "ps aux"},
                "priority": 1,
                "category": "process_inspection",
                "platform": "commodore64",
            }
        ]
        results = execute_action_checks(actions)
        assert len(results) == 1
        assert results[0].success is False
        assert "commodore64" in results[0].error
