"""Tests for tracker models and factory."""

import pytest
from symphony.tracker import Issue, create_tracker, UnsupportedTrackerKind
from symphony.config import Config
from pathlib import Path


def test_issue_dataclass():
    """Test Issue dataclass creation."""
    issue = Issue(
        id="abc-123",
        identifier="TEST-1",
        title="Test issue",
        description="Description here",
        priority=1,
        state="Todo",
        branch_name="feature/test",
        url="https://linear.app/test/1",
        labels=["bug", "urgent"],
        blocked_by=[],
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-02T00:00:00Z",
    )

    assert issue.id == "abc-123"
    assert issue.identifier == "TEST-1"
    assert issue.labels == ["bug", "urgent"]


def test_create_linear_tracker():
    """Test Linear tracker creation via factory."""
    cfg = Config(
        tracker_kind="linear",
        tracker_endpoint="https://api.linear.app/graphql",
        tracker_api_key="test-key",
        tracker_project_slug="test-project",
        tracker_active_states=["Todo", "In Progress"],
        tracker_terminal_states=["Done", "Cancelled"],
        polling_interval_ms=30000,
        workspace_root=Path("/tmp"),
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

    tracker = create_tracker(cfg)

    assert tracker.endpoint == "https://api.linear.app/graphql"
    assert tracker.api_key == "test-key"
    assert tracker.project_slug == "test-project"


def test_create_unsupported_tracker():
    """Test error for unsupported tracker kind."""
    cfg = Config(
        tracker_kind="jira",
        tracker_endpoint="",
        tracker_api_key=None,
        tracker_project_slug=None,
        tracker_active_states=[],
        tracker_terminal_states=[],
        polling_interval_ms=30000,
        workspace_root=Path("/tmp"),
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

    with pytest.raises(UnsupportedTrackerKind, match="Unsupported tracker kind"):
        create_tracker(cfg)
