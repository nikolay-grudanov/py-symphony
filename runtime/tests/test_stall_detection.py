"""Tests for stall detection in orchestrator."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from symphony.orchestrator import (
    Orchestrator,
    OrchestratorState,
    RunningEntry,
)
from symphony.config import Config


class TestStallDetection:
    """Tests for stall detection logic."""

    @pytest.fixture
    def config(self):
        """Create a test config with stall timeout."""
        return Config(
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
            codex_command="codex",
            codex_approval_policy=None,
            codex_thread_sandbox=None,
            codex_turn_sandbox_policy=None,
            codex_turn_timeout_ms=3600000,
            codex_read_timeout_ms=5000,
            codex_stall_timeout_ms=60000,  # 1 minute for testing
            # Server
            server_port=None,
        )

    @pytest.fixture
    def config_no_stall_timeout(self):
        """Create a test config with stall timeout disabled."""
        return Config(
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
            codex_command="codex",
            codex_approval_policy=None,
            codex_thread_sandbox=None,
            codex_turn_sandbox_policy=None,
            codex_turn_timeout_ms=3600000,
            codex_read_timeout_ms=5000,
            codex_stall_timeout_ms=0,  # Disabled
            # Server
            server_port=None,
        )

    @pytest.fixture
    def orchestrator(self, config):
        """Create an orchestrator instance."""
        from unittest.mock import MagicMock

        orchestrator = Orchestrator(
            config=config,
            tracker=MagicMock(),
            workspace_manager=MagicMock(),
            agent_runner=MagicMock(),
        )
        orchestrator.state = OrchestratorState()
        return orchestrator

    @pytest.fixture
    def orchestrator_no_stall(self, config_no_stall_timeout):
        """Create an orchestrator with stall timeout disabled."""
        from unittest.mock import MagicMock

        orchestrator = Orchestrator(
            config=config_no_stall_timeout,
            tracker=MagicMock(),
            workspace_manager=MagicMock(),
            agent_runner=MagicMock(),
        )
        orchestrator.state = OrchestratorState()
        return orchestrator

    def test_reconcile_stalled_running_issues_disabled(self, orchestrator_no_stall):
        """Test that stall detection is skipped when timeout is disabled."""
        # Add a stalled issue
        old_time = (datetime.utcnow() - timedelta(minutes=10)).isoformat() + "Z"
        orchestrator_no_stall.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            last_event_at=old_time,
        )

        # Reconcile should not restart the issue
        import asyncio

        asyncio.run(orchestrator_no_stall._reconcile_stalled_running_issues())

        # Issue should still be running (not stopped and retried)
        assert "issue1" in orchestrator_no_stall.state.running
        assert "issue1" not in orchestrator_no_stall.state.retry_attempts

    def test_reconcile_stalled_running_issues_no_running(self, orchestrator):
        """Test that stall detection handles no running issues gracefully."""
        import asyncio

        # Should not raise an error
        asyncio.run(orchestrator._reconcile_stalled_running_issues())

    def test_restart_stalled_issue(self, orchestrator):
        """Test restarting a stalled issue."""
        # Create an entry that has stalled
        old_time = (datetime.utcnow() - timedelta(minutes=10)).isoformat() + "Z"
        orchestrator.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            last_event_at=old_time,
            session_id="session123",
        )

        import asyncio

        # Restart the stalled issue
        asyncio.run(
            orchestrator._restart_stalled_issue(
                "issue1",
                orchestrator.state.running["issue1"],
                60000,  # 1 minute timeout
            )
        )

        # Issue should be removed from running
        assert "issue1" not in orchestrator.state.running

        # Issue should be scheduled for retry
        assert "issue1" in orchestrator.state.retry_attempts
        retry = orchestrator.state.retry_attempts["issue1"]
        assert retry.attempt == 1  # First attempt after stall restart
        assert "stalled" in retry.error.lower()

    def test_restart_stalled_issue_not_stalled(self, orchestrator):
        """Test that non-stalled issues are not restarted."""
        # Create an entry with recent activity
        recent_time = (datetime.utcnow() - timedelta(seconds=10)).isoformat() + "Z"
        orchestrator.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            last_event_at=recent_time,
        )

        import asyncio

        # Try to restart (should not happen)
        asyncio.run(
            orchestrator._restart_stalled_issue(
                "issue1",
                orchestrator.state.running["issue1"],
                60000,  # 1 minute timeout
            )
        )

        # Issue should still be running
        assert "issue1" in orchestrator.state.running

    def test_stall_elapsed_ms_with_last_event(self, orchestrator):
        """Test calculating elapsed time with last event timestamp."""
        # Create an entry with activity 5 minutes ago
        old_time = datetime.utcnow() - timedelta(minutes=5)
        entry = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            last_event_at=old_time.isoformat() + "Z",
        )

        elapsed = orchestrator._stall_elapsed_ms(entry)

        # Should be approximately 5 minutes (300000 ms)
        assert elapsed is not None
        assert 299000 <= elapsed <= 301000  # Allow for some variance

    def test_stall_elapsed_ms_with_started_at(self, orchestrator):
        """Test calculating elapsed time using started_at when no last_event."""
        # Create an entry started 3 minutes ago with no last_event
        old_time = datetime.utcnow() - timedelta(minutes=3)
        entry = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            started_at=old_time.isoformat() + "Z",
        )

        elapsed = orchestrator._stall_elapsed_ms(entry)

        # Should be approximately 3 minutes (180000 ms)
        assert elapsed is not None
        assert 179000 <= elapsed <= 181000  # Allow for some variance

    def test_stall_elapsed_ms_invalid_timestamp(self, orchestrator):
        """Test handling of invalid timestamps."""
        entry = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            last_event_at="invalid-timestamp",
        )

        elapsed = orchestrator._stall_elapsed_ms(entry)

        # Should return None for invalid timestamp
        assert elapsed is None

    def test_last_activity_timestamp_with_last_event(self, orchestrator):
        """Test getting last activity timestamp from last_event_at."""
        now = datetime.utcnow().isoformat() + "Z"
        entry = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            last_event_at=now,
        )

        timestamp = orchestrator._last_activity_timestamp(entry)

        assert timestamp == now

    def test_last_activity_timestamp_fallback_to_started_at(self, orchestrator):
        """Test falling back to started_at when last_event_at is missing."""
        started = datetime.utcnow().isoformat() + "Z"
        entry = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            started_at=started,
        )

        timestamp = orchestrator._last_activity_timestamp(entry)

        assert timestamp == started

    def test_last_activity_timestamp_no_timestamp(self, orchestrator):
        """Test when no timestamp is available."""
        # Manually create an entry with neither last_event_at nor started_at
        # This is a bit of a hack since started_at has a default factory
        entry = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
        )

        timestamp = orchestrator._last_activity_timestamp(entry)

        # Should return started_at (which has a default value)
        assert timestamp is not None

    def test_multiple_stalled_issues(self, orchestrator):
        """Test handling multiple stalled issues."""
        # Create multiple stalled issues
        old_time = (datetime.utcnow() - timedelta(minutes=10)).isoformat() + "Z"
        orchestrator.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            last_event_at=old_time,
        )
        orchestrator.state.running["issue2"] = RunningEntry(
            issue_id="issue2",
            issue_identifier="ISSUE-2",
            state="In Progress",
            last_event_at=old_time,
        )
        orchestrator.state.running["issue3"] = RunningEntry(
            issue_id="issue3",
            issue_identifier="ISSUE-3",
            state="In Progress",
            last_event_at=old_time,
        )

        import asyncio

        # Reconcile should restart all stalled issues
        asyncio.run(orchestrator._reconcile_stalled_running_issues())

        # All issues should be removed from running
        assert len(orchestrator.state.running) == 0

        # All issues should be scheduled for retry
        assert len(orchestrator.state.retry_attempts) == 3
        assert "issue1" in orchestrator.state.retry_attempts
        assert "issue2" in orchestrator.state.retry_attempts
        assert "issue3" in orchestrator.state.retry_attempts

    def test_mixed_stalled_and_active_issues(self, orchestrator):
        """Test handling mix of stalled and active issues."""
        # Add stalled issues
        old_time = (datetime.utcnow() - timedelta(minutes=10)).isoformat() + "Z"
        orchestrator.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            last_event_at=old_time,
        )

        # Add active issues
        recent_time = (datetime.utcnow() - timedelta(seconds=10)).isoformat() + "Z"
        orchestrator.state.running["issue2"] = RunningEntry(
            issue_id="issue2",
            issue_identifier="ISSUE-2",
            state="In Progress",
            last_event_at=recent_time,
        )

        import asyncio

        # Reconcile
        asyncio.run(orchestrator._reconcile_stalled_running_issues())

        # Stalled issue should be removed
        assert "issue1" not in orchestrator.state.running
        assert "issue1" in orchestrator.state.retry_attempts

        # Active issue should remain
        assert "issue2" in orchestrator.state.running
        assert "issue2" not in orchestrator.state.retry_attempts

    def test_stall_timeout_boundary(self, orchestrator):
        """Test stall detection at timeout boundary."""
        # Create entry exactly at timeout boundary (minus 1 second)
        boundary_time = datetime.utcnow() - timedelta(
            seconds=orchestrator.config.codex_stall_timeout_ms / 1000 - 1
        )
        entry = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            last_event_at=boundary_time.isoformat() + "Z",
        )

        elapsed = orchestrator._stall_elapsed_ms(entry)

        # Should be just under the timeout
        assert elapsed < orchestrator.config.codex_stall_timeout_ms

    def test_stall_timeout_exceeded(self, orchestrator):
        """Test stall detection when timeout is exceeded."""
        # Create entry just over timeout boundary (plus 1 second)
        over_time = datetime.utcnow() - timedelta(
            seconds=orchestrator.config.codex_stall_timeout_ms / 1000 + 1
        )
        entry = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            last_event_at=over_time.isoformat() + "Z",
        )

        elapsed = orchestrator._stall_elapsed_ms(entry)

        # Should be just over the timeout
        assert elapsed > orchestrator.config.codex_stall_timeout_ms
