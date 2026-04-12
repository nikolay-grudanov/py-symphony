"""Tests for workspace manager."""

import pytest
import tempfile
from pathlib import Path
from symphony.config import Config
from symphony.workspace import WorkspaceManager, sanitize_workspace_key


def test_sanitize_workspace_key():
    """Test workspace key sanitization."""
    assert sanitize_workspace_key("MT-123") == "MT-123"
    assert sanitize_workspace_key("MT-123!@#") == "MT-123___"
    assert sanitize_workspace_key("abc def") == "abc_def"


def test_workspace_creation():
    """Test workspace directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Config(
            tracker_kind="linear",
            tracker_endpoint="",
            tracker_api_key=None,
            tracker_project_slug=None,
            tracker_active_states=[],
            tracker_terminal_states=[],
            polling_interval_ms=30000,
            workspace_root=Path(tmpdir),
            hooks_after_create=None,
            hooks_before_run=None,
            hooks_after_run=None,
            hooks_before_remove=None,
            hooks_timeout_ms=60000,
            agent_max_concurrent_agents=10,
            agent_max_retry_backoff_ms=300000,
            agent_max_turns=20,
            codex_command="codex app-server",
            codex_approval_policy=None,
            codex_thread_sandbox=None,
            codex_turn_sandbox_policy=None,
            codex_turn_timeout_ms=3600000,
            codex_read_timeout_ms=5000,
            codex_stall_timeout_ms=300000,
            server_port=None,
        )

        wm = WorkspaceManager(cfg)
        ws = wm.ensure_workspace("TEST-123")

        assert ws.path.exists()
        assert ws.issue_identifier == "TEST-123"
        assert ws.created_now is True


def test_workspace_reuse():
    """Test workspace reuse on second call."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Config(
            tracker_kind="linear",
            tracker_endpoint="",
            tracker_api_key=None,
            tracker_project_slug=None,
            tracker_active_states=[],
            tracker_terminal_states=[],
            polling_interval_ms=30000,
            workspace_root=Path(tmpdir),
            hooks_after_create=None,
            hooks_before_run=None,
            hooks_after_run=None,
            hooks_before_remove=None,
            hooks_timeout_ms=60000,
            agent_max_concurrent_agents=10,
            agent_max_retry_backoff_ms=300000,
            agent_max_turns=20,
            codex_command="codex app-server",
            codex_approval_policy=None,
            codex_thread_sandbox=None,
            codex_turn_sandbox_policy=None,
            codex_turn_timeout_ms=3600000,
            codex_read_timeout_ms=5000,
            codex_stall_timeout_ms=300000,
            server_port=None,
        )

        wm = WorkspaceManager(cfg)

        # First call creates
        ws1 = wm.ensure_workspace("TEST-456")
        assert ws1.created_now is True

        # Second call reuses
        ws2 = wm.ensure_workspace("TEST-456")
        assert ws2.created_now is False
