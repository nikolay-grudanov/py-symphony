"""Tests for get_state_snapshot() method in Orchestrator.

Per SPEC.md Section 13.3 - Runtime Snapshot / Monitoring Interface.
"""

import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from symphony.orchestrator import (
    Orchestrator,
    OrchestratorState,
    RunningEntry,
    RetryEntry,
)
from symphony.config import Config


class TestGetStateSnapshot:
    """Tests for get_state_snapshot() method."""

    @pytest.fixture
    def config(self):
        """Create a test config."""
        return Config(
            # Server
            server_port=8080,
            # Tracker
            tracker_kind="linear",
            tracker_endpoint="https://api.linear.app/graphql",
            tracker_api_key="test_key",
            tracker_project_slug="test",
            tracker_active_states=["Todo", "In Progress"],
            tracker_terminal_states=["Closed"],
            # Polling
            polling_interval_ms=30000,
            # Workspace
            workspace_root=Path("/tmp/test"),
            # Hooks
            hooks_after_create=None,
            hooks_before_run=None,
            hooks_after_run=None,
            hooks_before_remove=None,
            hooks_timeout_ms=60000,
            # Agent
            agent_max_concurrent_agents=10,
            agent_max_concurrent_agents_by_state={},
            agent_max_retry_backoff_ms=300000,
            agent_max_turns=20,
            # Worker
            worker_ssh_hosts=[],
            worker_max_concurrent_agents_per_host=3,
            # Codex
            codex_command="codex app-server",
            codex_approval_policy="auto_approve",
            codex_thread_sandbox="enabled",
            codex_turn_sandbox_policy=None,
            codex_turn_timeout_ms=3600000,
            codex_read_timeout_ms=5000,
            codex_stall_timeout_ms=300000,
        )

    @pytest.fixture
    def orchestrator(
        self, config, mock_tracker, mock_workspace_manager, mock_agent_runner
    ):
        """Create an orchestrator instance."""
        return Orchestrator(
            config, mock_tracker, mock_workspace_manager, mock_agent_runner
        )

    @pytest.fixture
    def mock_tracker(self):
        """Create a mock tracker."""

        class MockTracker:
            async def fetch_candidate_issues(self):
                return []

            async def fetch_issues_by_states(self, states):
                return []

            async def fetch_issue_states_by_ids(self, issue_ids):
                return {}

        return MockTracker()

    @pytest.fixture
    def mock_workspace_manager(self):
        """Create a mock workspace manager."""

        class MockWorkspaceManager:
            async def cleanup_workspace(self, identifier):
                pass

        return MockWorkspaceManager()

    @pytest.fixture
    def mock_agent_runner(self):
        """Create a mock agent runner."""

        class MockAgentRunner:
            async def run(self, issue, orchestrator, attempt=None, worker_host=None):
                pass

        return MockAgentRunner()

    def test_get_state_snapshot_empty_state(self, orchestrator):
        """Test get_state_snapshot with empty state."""
        snapshot = orchestrator.get_state_snapshot()

        assert isinstance(snapshot, dict)
        assert "running" in snapshot
        assert "retrying" in snapshot
        assert "codex_totals" in snapshot
        assert "rate_limits" in snapshot
        assert "polling" in snapshot

        assert snapshot["running"] == []
        assert snapshot["retrying"] == []
        assert snapshot["codex_totals"] == {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "seconds_running": 0.0,
        }
        assert snapshot["rate_limits"] is None
        assert snapshot["polling"]["checking?"] is False
        # next_poll_in_ms is None when orchestrator hasn't started yet
        assert snapshot["polling"]["next_poll_in_ms"] is None
        assert snapshot["polling"]["poll_interval_ms"] == 30000

    def test_get_state_snapshot_with_running_entries(self, orchestrator):
        """Test get_state_snapshot with running entries."""
        # Add running entries
        now = datetime.now(timezone.utc)
        past_time = (now - timedelta(seconds=60)).isoformat().replace("+00:00", "Z")

        entry1 = RunningEntry(
            issue_id="issue-1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            session_id="thread-1-turn-1",
            turn_count=2,
            last_event="turn_completed",
            last_event_at=past_time,
            worker_host=None,
            workspace_path="/tmp/test/issue-1",
            codex_app_server_pid="12345",
            started_at=past_time,
            codex_input_tokens=100,
            codex_output_tokens=200,
            codex_total_tokens=300,
        )

        entry2 = RunningEntry(
            issue_id="issue-2",
            issue_identifier="ISSUE-2",
            state="Todo",
            session_id=None,
            turn_count=0,
            last_event=None,
            last_event_at=None,
            worker_host=None,
            workspace_path="/tmp/test/issue-2",
            codex_app_server_pid=None,
            started_at=past_time,
            codex_input_tokens=0,
            codex_output_tokens=0,
            codex_total_tokens=0,
        )

        orchestrator.state.running = {
            "issue-1": entry1,
            "issue-2": entry2,
        }

        snapshot = orchestrator.get_state_snapshot()

        assert len(snapshot["running"]) == 2

        # Check first entry
        running1 = snapshot["running"][0]
        assert running1["issue_id"] == "issue-1"
        assert running1["identifier"] == "ISSUE-1"
        assert running1["state"] == "In Progress"
        assert running1["session_id"] == "thread-1-turn-1"
        assert running1["turn_count"] == 2
        assert running1["last_codex_timestamp"] == past_time
        assert running1["last_codex_message"] == "turn_completed"
        assert running1["last_codex_event"] == "turn_completed"
        assert running1["worker_host"] is None
        assert running1["workspace_path"] == "/tmp/test/issue-1"
        assert running1["codex_app_server_pid"] == "12345"
        assert running1["codex_input_tokens"] == 100
        assert running1["codex_output_tokens"] == 200
        assert running1["codex_total_tokens"] == 300
        assert running1["runtime_seconds"] >= 60  # Approximately 60 seconds

        # Check second entry
        running2 = snapshot["running"][1]
        assert running2["issue_id"] == "issue-2"
        assert running2["identifier"] == "ISSUE-2"
        assert running2["state"] == "Todo"
        assert running2["session_id"] is None
        assert running2["turn_count"] == 0
        assert running2["workspace_path"] == "/tmp/test/issue-2"
        assert running2["codex_app_server_pid"] is None
        assert running2["codex_input_tokens"] == 0
        assert running2["codex_output_tokens"] == 0
        assert running2["codex_total_tokens"] == 0
        assert running2["runtime_seconds"] >= 60

    def test_get_state_snapshot_with_retry_entries(self, orchestrator):
        """Test get_state_snapshot with retry entries."""
        import time

        # Add retry entries
        now_ms = int(time.time() * 1000)

        retry1 = RetryEntry(
            issue_id="issue-1",
            identifier="ISSUE-1",
            attempt=1,
            due_at_ms=now_ms + 5000,
            error="test error",
            worker_host=None,
            workspace_path="/tmp/test/issue-1",
        )

        retry2 = RetryEntry(
            issue_id="issue-2",
            identifier="ISSUE-2",
            attempt=2,
            due_at_ms=now_ms + 10000,
            error=None,
            worker_host=None,
            workspace_path="/tmp/test/issue-2",
        )

        orchestrator.state.retry_attempts = {
            "issue-1": retry1,
            "issue-2": retry2,
        }

        snapshot = orchestrator.get_state_snapshot()

        assert len(snapshot["retrying"]) == 2

        # Check first retry
        retrying1 = snapshot["retrying"][0]
        assert retrying1["issue_id"] == "issue-1"
        assert retrying1["attempt"] == 1
        assert retrying1["identifier"] == "ISSUE-1"
        assert retrying1["error"] == "test error"
        assert retrying1["worker_host"] is None
        assert retrying1["workspace_path"] == "/tmp/test/issue-1"
        assert 0 <= retrying1["due_in_ms"] <= 5000

        # Check second retry
        retrying2 = snapshot["retrying"][1]
        assert retrying2["issue_id"] == "issue-2"
        assert retrying2["attempt"] == 2
        assert retrying2["identifier"] == "ISSUE-2"
        assert retrying2["error"] is None
        assert retrying2["worker_host"] is None
        assert retrying2["workspace_path"] == "/tmp/test/issue-2"
        assert 0 <= retrying2["due_in_ms"] <= 10000

    def test_get_state_snapshot_with_codex_totals(self, orchestrator):
        """Test get_state_snapshot with codex totals."""
        orchestrator.state.codex_totals = {
            "input_tokens": 1000,
            "output_tokens": 2000,
            "total_tokens": 3000,
            "seconds_running": 100.5,
        }

        snapshot = orchestrator.get_state_snapshot()

        assert snapshot["codex_totals"] == {
            "input_tokens": 1000,
            "output_tokens": 2000,
            "total_tokens": 3000,
            "seconds_running": 100.5,
        }

    def test_get_state_snapshot_with_rate_limits(self, orchestrator):
        """Test get_state_snapshot with rate limits."""
        orchestrator.state.rate_limits = {
            "limit_id": "gpt-4o",
            "primary": {"remaining": 1000, "reset_at": "2024-01-01T00:00:00Z"},
            "secondary": {"remaining": 500, "reset_at": "2024-01-01T00:00:00Z"},
        }

        snapshot = orchestrator.get_state_snapshot()

        assert snapshot["rate_limits"] == {
            "limit_id": "gpt-4o",
            "primary": {"remaining": 1000, "reset_at": "2024-01-01T00:00:00Z"},
            "secondary": {"remaining": 500, "reset_at": "2024-01-01T00:00:00Z"},
        }

    def test_get_state_snapshot_polling_status(self, orchestrator):
        """Test get_state_snapshot polling status."""
        orchestrator._poll_check_in_progress = True
        orchestrator._next_poll_due_at_ms = (
            int(__import__("time").time() * 1000) + 15000
        )

        snapshot = orchestrator.get_state_snapshot()

        assert snapshot["polling"]["checking?"] is True
        assert snapshot["polling"]["next_poll_in_ms"] is not None
        assert 0 <= snapshot["polling"]["next_poll_in_ms"] <= 15000
        assert snapshot["polling"]["poll_interval_ms"] == 30000

        # Test with poll check not in progress
        orchestrator._poll_check_in_progress = False
        snapshot = orchestrator.get_state_snapshot()

        assert snapshot["polling"]["checking?"] is False
