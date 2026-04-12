"""Tests for per-state concurrency limits in orchestrator."""

import pytest
from pathlib import Path
from symphony.orchestrator import (
    Orchestrator,
    OrchestratorState,
    RunningEntry,
)
from symphony.config import Config
from symphony.tracker import Issue


class TestPerStateConcurrency:
    """Tests for per-state concurrency limit logic."""

    @pytest.fixture
    def base_config(self):
        """Create a base test config."""
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
            codex_stall_timeout_ms=300000,
            # Server
            server_port=None,
        )

    @pytest.fixture
    def orchestrator_state(self):
        """Create an empty orchestrator state."""
        return OrchestratorState()

    @pytest.fixture
    def orchestrator(self, base_config, orchestrator_state):
        """Create an orchestrator instance."""
        from unittest.mock import MagicMock

        orchestrator = Orchestrator(
            config=base_config,
            tracker=MagicMock(),
            workspace_manager=MagicMock(),
            agent_runner=MagicMock(),
        )
        orchestrator.state = orchestrator_state
        return orchestrator

    def test_normalize_issue_state(self, orchestrator):
        """Test state normalization to lowercase."""
        assert orchestrator._normalize_issue_state("Todo") == "todo"
        assert orchestrator._normalize_issue_state("IN PROGRESS") == "in progress"
        assert orchestrator._normalize_issue_state("In Progress") == "in progress"
        assert orchestrator._normalize_issue_state("") == ""
        assert orchestrator._normalize_issue_state(None) == ""

    def test_running_issue_count_for_state_empty(self, orchestrator):
        """Test counting running issues when none are running."""
        count = orchestrator._running_issue_count_for_state(
            orchestrator.state.running, "Todo"
        )
        assert count == 0

    def test_running_issue_count_for_state_single(self, orchestrator):
        """Test counting a single running issue."""
        # Add one running entry
        orchestrator.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="Todo",
        )

        count = orchestrator._running_issue_count_for_state(
            orchestrator.state.running, "Todo"
        )
        assert count == 1

        # Different state should have 0 count
        count_in_progress = orchestrator._running_issue_count_for_state(
            orchestrator.state.running, "In Progress"
        )
        assert count_in_progress == 0

    def test_running_issue_count_for_state_multiple(self, orchestrator):
        """Test counting multiple running issues."""
        # Add multiple running entries with different states
        orchestrator.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="Todo",
        )
        orchestrator.state.running["issue2"] = RunningEntry(
            issue_id="issue2",
            issue_identifier="ISSUE-2",
            state="Todo",
        )
        orchestrator.state.running["issue3"] = RunningEntry(
            issue_id="issue3",
            issue_identifier="ISSUE-3",
            state="In Progress",
        )

        # Count Todo state
        count = orchestrator._running_issue_count_for_state(
            orchestrator.state.running, "Todo"
        )
        assert count == 2

        # Count In Progress state
        count_in_progress = orchestrator._running_issue_count_for_state(
            orchestrator.state.running, "In Progress"
        )
        assert count_in_progress == 1

    def test_running_issue_count_for_state_case_insensitive(self, orchestrator):
        """Test that state counting is case-insensitive."""
        # Add running entries with mixed case states
        orchestrator.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="TODO",  # uppercase
        )
        orchestrator.state.running["issue2"] = RunningEntry(
            issue_id="issue2",
            issue_identifier="ISSUE-2",
            state="todo",  # lowercase
        )
        orchestrator.state.running["issue3"] = RunningEntry(
            issue_id="issue3",
            issue_identifier="ISSUE-3",
            state="ToDo",  # mixed case
        )

        # All should be counted regardless of case
        count = orchestrator._running_issue_count_for_state(
            orchestrator.state.running, "Todo"
        )
        assert count == 3

    def test_state_slots_available_no_limit_configured(self, orchestrator, base_config):
        """Test that slots are available when no per-state limit is configured."""
        # No per-state limits configured (empty dict)
        base_config.agent_max_concurrent_agents_by_state = {}

        # Create a test issue
        issue = Issue(
            id="issue1",
            identifier="ISSUE-1",
            title="Test Issue",
            description="Test description",
            priority=1,
            state="Todo",
            branch_name=None,
            url=None,
            labels=[],
            blocked_by=[],
            created_at=None,
            updated_at=None,
        )

        # Should return True (fallback to global limit)
        assert orchestrator._state_slots_available(issue, orchestrator.state.running)

    def test_state_slots_available_with_limit(self, orchestrator, base_config):
        """Test state slot availability with a configured limit."""
        # Configure limit for Todo state
        base_config.agent_max_concurrent_agents_by_state = {"todo": 2}

        # Create a test issue
        issue = Issue(
            id="issue1",
            identifier="ISSUE-1",
            title="Test Issue",
            description="Test description",
            priority=1,
            state="Todo",
            branch_name=None,
            url=None,
            labels=[],
            blocked_by=[],
            created_at=None,
            updated_at=None,
        )

        # No running issues - should have slots
        assert orchestrator._state_slots_available(issue, orchestrator.state.running)

        # Add one running Todo issue
        orchestrator.state.running["issue2"] = RunningEntry(
            issue_id="issue2",
            issue_identifier="ISSUE-2",
            state="Todo",
        )

        # Should still have slots (1 used, limit is 2)
        assert orchestrator._state_slots_available(issue, orchestrator.state.running)

        # Add another running Todo issue (at limit)
        orchestrator.state.running["issue3"] = RunningEntry(
            issue_id="issue3",
            issue_identifier="ISSUE-3",
            state="Todo",
        )

        # Should not have slots (2 used, limit is 2)
        assert not orchestrator._state_slots_available(
            issue, orchestrator.state.running
        )

    def test_state_slots_available_different_states(self, orchestrator, base_config):
        """Test that state limits are independent per state."""
        # Configure limits for different states
        base_config.agent_max_concurrent_agents_by_state = {
            "todo": 2,
            "in progress": 1,
        }

        # Fill Todo state to limit
        orchestrator.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="Todo",
        )
        orchestrator.state.running["issue2"] = RunningEntry(
            issue_id="issue2",
            issue_identifier="ISSUE-2",
            state="Todo",
        )

        # Create a Todo issue - should not have slots
        todo_issue = Issue(
            id="issue3",
            identifier="ISSUE-3",
            title="Test Issue",
            description="Test description",
            priority=1,
            state="Todo",
            branch_name=None,
            url=None,
            labels=[],
            blocked_by=[],
            created_at=None,
            updated_at=None,
        )
        assert not orchestrator._state_slots_available(
            todo_issue, orchestrator.state.running
        )

        # Create an In Progress issue - should have slots (only 1 used out of 1 limit)
        in_progress_issue = Issue(
            id="issue4",
            identifier="ISSUE-4",
            title="Test Issue",
            description="Test description",
            priority=1,
            state="In Progress",
            branch_name=None,
            url=None,
            labels=[],
            blocked_by=[],
            created_at=None,
            updated_at=None,
        )
        assert orchestrator._state_slots_available(
            in_progress_issue, orchestrator.state.running
        )

    def test_state_slots_available_case_insensitive_lookup(
        self, orchestrator, base_config
    ):
        """Test that state limit lookup is case-insensitive."""
        # Configure limit with mixed case key
        base_config.agent_max_concurrent_agents_by_state = {"TODO": 1}

        # Create issue with lowercase state
        issue = Issue(
            id="issue1",
            identifier="ISSUE-1",
            title="Test Issue",
            description="Test description",
            priority=1,
            state="todo",
            branch_name=None,
            url=None,
            labels=[],
            blocked_by=[],
            created_at=None,
            updated_at=None,
        )

        # Should find the limit (case-insensitive)
        assert orchestrator._state_slots_available(issue, orchestrator.state.running)

    def test_state_slots_available_no_limit_for_state(self, orchestrator, base_config):
        """Test fallback to global limit when state has no configured limit."""
        # Configure limit only for Todo state
        base_config.agent_max_concurrent_agents_by_state = {"todo": 1}

        # Create issue with In Progress state (no limit configured)
        issue = Issue(
            id="issue1",
            identifier="ISSUE-1",
            title="Test Issue",
            description="Test description",
            priority=1,
            state="In Progress",
            branch_name=None,
            url=None,
            labels=[],
            blocked_by=[],
            created_at=None,
            updated_at=None,
        )

        # Should return True (fallback to global limit)
        assert orchestrator._state_slots_available(issue, orchestrator.state.running)

    def test_can_dispatch_with_per_state_limits(self, orchestrator, base_config):
        """Test _can_dispatch respects per-state limits."""
        # Configure per-state limits
        base_config.agent_max_concurrent_agents_by_state = {"todo": 1}

        # Add one running Todo issue (at state limit)
        orchestrator.state.running["issue1"] = RunningEntry(
            issue_id="issue1",
            issue_identifier="ISSUE-1",
            state="Todo",
        )

        # Create a new Todo issue
        todo_issue = Issue(
            id="issue2",
            identifier="ISSUE-2",
            title="Test Issue",
            description="Test description",
            priority=1,
            state="Todo",
            branch_name=None,
            url=None,
            labels=[],
            blocked_by=[],
            created_at=None,
            updated_at=None,
        )

        # Should not be able to dispatch (state limit reached)
        assert not orchestrator._can_dispatch(todo_issue)

        # Create an In Progress issue (different state)
        in_progress_issue = Issue(
            id="issue3",
            identifier="ISSUE-3",
            title="Test Issue",
            description="Test description",
            priority=1,
            state="In Progress",
            branch_name=None,
            url=None,
            labels=[],
            blocked_by=[],
            created_at=None,
            updated_at=None,
        )

        # Should be able to dispatch (no state limit configured for In Progress)
        assert orchestrator._can_dispatch(in_progress_issue)

    def test_can_dispatch_without_issue(self, orchestrator):
        """Test _can_dispatch works when no issue is provided."""
        # Should only check global limit when no issue provided
        for i in range(9):  # Below global limit of 10
            orchestrator.state.running[f"issue{i}"] = RunningEntry(
                issue_id=f"issue{i}",
                issue_identifier=f"ISSUE-{i}",
                state="Todo",
            )
        assert orchestrator._can_dispatch()  # No issue provided

        # At global limit
        orchestrator.state.running["issue9"] = RunningEntry(
            issue_id="issue9",
            issue_identifier="ISSUE-9",
            state="Todo",
        )
        assert not orchestrator._can_dispatch()  # No issue provided

    def test_can_dispatch_with_global_limit_exceeded(self, orchestrator, base_config):
        """Test _can_dispatch respects global limit even with per-state limits."""
        # Configure per-state limits
        base_config.agent_max_concurrent_agents_by_state = {"todo": 20}  # High limit

        # Fill to global limit (10)
        for i in range(10):
            orchestrator.state.running[f"issue{i}"] = RunningEntry(
                issue_id=f"issue{i}",
                issue_identifier=f"ISSUE-{i}",
                state="Todo",
            )

        # Create a Todo issue
        issue = Issue(
            id="issue11",
            identifier="ISSUE-11",
            title="Test Issue",
            description="Test description",
            priority=1,
            state="Todo",
            branch_name=None,
            url=None,
            labels=[],
            blocked_by=[],
            created_at=None,
            updated_at=None,
        )

        # Should not be able to dispatch (global limit reached)
        assert not orchestrator._can_dispatch(issue)

    def test_integration_dispatch_loop_with_state_limits(
        self, orchestrator, base_config
    ):
        """Test that dispatch loop respects state limits."""
        # Configure per-state limits
        base_config.agent_max_concurrent_agents_by_state = {"todo": 2}

        # Create candidate issues
        todo_issue1 = Issue(
            id="issue1",
            identifier="ISSUE-1",
            title="Test Issue 1",
            description="Test description",
            priority=1,
            state="Todo",
            branch_name=None,
            url=None,
            labels=[],
            blocked_by=[],
            created_at=None,
            updated_at=None,
        )
        todo_issue2 = Issue(
            id="issue2",
            identifier="ISSUE-2",
            title="Test Issue 2",
            description="Test description",
            priority=2,
            state="Todo",
            branch_name=None,
            url=None,
            labels=[],
            blocked_by=[],
            created_at=None,
            updated_at=None,
        )
        todo_issue3 = Issue(
            id="issue3",
            identifier="ISSUE-3",
            title="Test Issue 3",
            description="Test description",
            priority=3,
            state="Todo",
            branch_name=None,
            url=None,
            labels=[],
            blocked_by=[],
            created_at=None,
            updated_at=None,
        )
        in_progress_issue = Issue(
            id="issue4",
            identifier="ISSUE-4",
            title="Test Issue 4",
            description="Test description",
            priority=4,
            state="In Progress",
            branch_name=None,
            url=None,
            labels=[],
            blocked_by=[],
            created_at=None,
            updated_at=None,
        )

        candidates = [todo_issue1, todo_issue2, todo_issue3, in_progress_issue]

        # Sort by priority
        sorted_issues = orchestrator._sort_candidates(candidates)

        # Simulate dispatch loop
        dispatched = []
        for issue in sorted_issues:
            if orchestrator._can_dispatch(issue) and orchestrator._is_dispatch_eligible(
                issue
            ):
                dispatched.append(issue)
                # Simulate adding to running
                orchestrator.state.running[issue.id] = RunningEntry(
                    issue_id=issue.id,
                    issue_identifier=issue.identifier,
                    state=issue.state,
                )

        # Should dispatch exactly 2 Todo issues (state limit) and 1 In Progress issue
        assert len(dispatched) == 3
        assert any(i.id == "issue1" for i in dispatched)
        assert any(i.id == "issue2" for i in dispatched)
        assert any(i.id == "issue4" for i in dispatched)
        assert not any(i.id == "issue3" for i in dispatched)  # Over Todo limit
