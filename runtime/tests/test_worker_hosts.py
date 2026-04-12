"""Tests for SSH worker host selection in orchestrator."""

import pytest
from pathlib import Path
from symphony.orchestrator import (
    Orchestrator,
    OrchestratorState,
    RunningEntry,
)
from symphony.config import Config


class TestWorkerHostSelection:
    """Tests for worker host selection logic."""

    @pytest.fixture
    def config(self):
        """Create a test config with SSH worker hosts."""
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
            worker_ssh_hosts=["host1", "host2", "host3"],
            worker_max_concurrent_agents_per_host=2,
            # Codex
            codex_command="codex",
            codex_approval_policy=None,
            codex_thread_sandbox=None,
            codex_turn_sandbox_policy=None,
            codex_turn_timeout_ms=3600000,
            codex_read_timeout_ms=5000,
            codex_stall_timeout_ms=300000,
            # Server
            server_port=None,
        )

    @pytest.fixture
    def orchestrator_state(self):
        """Create an empty orchestrator state."""
        return OrchestratorState()

    @pytest.fixture
    def orchestrator(self, config, orchestrator_state):
        """Create an orchestrator instance."""
        # Mock tracker, workspace_manager, and agent_runner
        from unittest.mock import MagicMock

        orchestrator = Orchestrator(
            config=config,
            tracker=MagicMock(),
            workspace_manager=MagicMock(),
            agent_runner=MagicMock(),
        )
        orchestrator.state = orchestrator_state
        return orchestrator

    def test_worker_host_slots_available_empty(self, orchestrator):
        """Test that slots are available when no hosts are running."""
        assert orchestrator._worker_host_slots_available("host1")

    def test_worker_host_slots_available_below_limit(self, orchestrator):
        """Test that slots are available when below limit."""
        # Add one running entry to host1
        orchestrator.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            worker_host="host1",
        )

        # Should still have slots (limit is 2)
        assert orchestrator._worker_host_slots_available("host1")

    def test_worker_host_slots_available_at_limit(self, orchestrator):
        """Test that slots are not available when at limit."""
        # Add two running entries to host1 (at limit)
        orchestrator.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            worker_host="host1",
        )
        orchestrator.state.running["issue2"] = RunningEntry(
            issue_id="issue2",
            issue_identifier="ISSUE-2",
            state="In Progress",
            worker_host="host1",
        )

        # Should not have slots (limit is 2)
        assert not orchestrator._worker_host_slots_available("host1")

    def test_running_worker_host_count(self, orchestrator):
        """Test counting running agents on a host."""
        # Add running entries to different hosts
        orchestrator.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            worker_host="host1",
        )
        orchestrator.state.running["issue2"] = RunningEntry(
            issue_id="issue2",
            issue_identifier="ISSUE-2",
            state="In Progress",
            worker_host="host1",
        )
        orchestrator.state.running["issue3"] = RunningEntry(
            issue_id="issue3",
            issue_identifier="ISSUE-3",
            state="In Progress",
            worker_host="host2",
        )

        assert orchestrator._running_worker_host_count("host1") == 2
        assert orchestrator._running_worker_host_count("host2") == 1
        assert orchestrator._running_worker_host_count("host3") == 0

    def test_least_loaded_worker_host(self, orchestrator):
        """Test selecting least loaded host."""
        # Add different loads to hosts
        orchestrator.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            worker_host="host1",
        )
        orchestrator.state.running["issue2"] = RunningEntry(
            issue_id="issue2",
            issue_identifier="ISSUE-2",
            state="In Progress",
            worker_host="host1",
        )
        orchestrator.state.running["issue3"] = RunningEntry(
            issue_id="issue3",
            issue_identifier="ISSUE-3",
            state="In Progress",
            worker_host="host2",
        )

        # host3 is least loaded (0 vs 1 vs 2)
        selected = orchestrator._least_loaded_worker_host(["host1", "host2", "host3"])
        assert selected == "host3"

    def test_select_worker_host_empty_state(self, orchestrator):
        """Test selecting host when all hosts are empty."""
        selected = orchestrator._select_worker_host()
        # Should select first host (all empty)
        assert selected in ["host1", "host2", "host3"]

    def test_select_worker_host_least_loaded(self, orchestrator):
        """Test selecting least loaded host."""
        # Load host1
        orchestrator.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            worker_host="host1",
        )
        orchestrator.state.running["issue2"] = RunningEntry(
            issue_id="issue2",
            issue_identifier="ISSUE-2",
            state="In Progress",
            worker_host="host1",
        )

        # host2 and host3 should be selected (both empty)
        selected = orchestrator._select_worker_host()
        assert selected in ["host2", "host3"]

    def test_select_worker_host_no_capacity(self, orchestrator):
        """Test that None is returned when no hosts have capacity."""
        # Fill all hosts to capacity
        for i, host in enumerate(["host1", "host2", "host3"]):
            for j in range(2):  # max_concurrent_agents_per_host is 2
                orchestrator.state.running[f"issue{i}{j}"] = RunningEntry(
                    issue_id=f"issue{i}{j}",
                    issue_identifier=f"ISSUE-{i}{j}",
                    state="In Progress",
                    worker_host=host,
                )

        # No capacity available
        selected = orchestrator._select_worker_host()
        assert selected is None

    def test_can_dispatch_with_worker_hosts(self, orchestrator):
        """Test _can_dispatch respects worker host limits."""
        # Fill host1 to capacity
        orchestrator.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            worker_host="host1",
        )
        orchestrator.state.running["issue2"] = RunningEntry(
            issue_id="issue2",
            issue_identifier="ISSUE-2",
            state="In Progress",
            worker_host="host1",
        )

        # Other hosts have capacity
        assert orchestrator._can_dispatch()

        # Fill all hosts to capacity
        for i, host in enumerate(["host2", "host3"]):
            for j in range(2):
                orchestrator.state.running[f"issue{2 + i}{j}"] = RunningEntry(
                    issue_id=f"issue{2 + i}{j}",
                    issue_identifier=f"ISSUE-{2 + i}{j}",
                    state="In Progress",
                    worker_host=host,
                )

        # No capacity available
        assert not orchestrator._can_dispatch()

    def test_can_dispatch_without_worker_hosts(self, orchestrator):
        """Test _can_dispatch works when no SSH hosts configured."""
        orchestrator.config.worker_ssh_hosts = []

        # Should only check global limit
        for i in range(9):  # Below limit of 10
            orchestrator.state.running[f"issue{i}"] = RunningEntry(
                issue_id=f"issue{i}",
                issue_identifier=f"ISSUE-{i}",
                state="In Progress",
            )
        assert orchestrator._can_dispatch()

        # At limit
        orchestrator.state.running["issue9"] = RunningEntry(
            issue_id="issue9",
            issue_identifier="ISSUE-9",
            state="In Progress",
        )
        assert not orchestrator._can_dispatch()

    def test_preferred_worker_host_available(self, orchestrator):
        """Test preferred worker host selection."""
        # Load host1
        orchestrator.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="In Progress",
            worker_host="host1",
        )

        # host2 has capacity and is preferred
        selected = orchestrator._select_worker_host(preferred_worker_host="host2")
        assert selected == "host2"

        # host1 is at capacity and should not be selected even if preferred
        orchestrator.state.running["issue2"] = RunningEntry(
            issue_id="issue2",
            issue_identifier="ISSUE-2",
            state="In Progress",
            worker_host="host1",
        )
        selected = orchestrator._select_worker_host(preferred_worker_host="host1")
        assert selected != "host1"
