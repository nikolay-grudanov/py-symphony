"""Tests for token accounting and rate limits in orchestrator.

Per SPEC.md Section 13.5 - token accounting rules and rate limit tracking.
"""

import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from symphony.orchestrator import (
    Orchestrator,
    OrchestratorState,
    RunningEntry,
)
from symphony.config import Config


class TestTokenAccounting:
    """Tests for token accounting logic."""

    @pytest.fixture
    def config(self):
        """Create a test config."""
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
            codex_stall_timeout_ms=0,
            # Server
            server_port=None,
        )

    @pytest.fixture
    def orchestrator(self, config):
        """Create an orchestrator instance for testing."""
        from symphony.tracker import LinearTracker
        from symphony.workspace import WorkspaceManager
        from symphony.agent import AgentRunner

        tracker = LinearTracker(
            endpoint=config.tracker_endpoint,
            api_key=config.tracker_api_key,
            project_slug=config.tracker_project_slug,
            active_states=config.tracker_active_states,
            terminal_states=config.tracker_terminal_states,
        )
        workspace_manager = WorkspaceManager(config)
        agent_runner = AgentRunner(config, workspace_manager)

        orch = Orchestrator(config, tracker, workspace_manager, agent_runner)
        return orch

    def test_integer_like_extracts_integers(self, orchestrator):
        """Test that integer_like extracts integers correctly."""
        # Positive integers
        assert orchestrator._integer_like(0) == 0
        assert orchestrator._integer_like(100) == 100
        assert orchestrator._integer_like(999999) == 999999

        # String integers
        assert orchestrator._integer_like("0") == 0
        assert orchestrator._integer_like("100") == 100
        assert orchestrator._integer_like("  50  ") == 50

        # Negative or invalid values
        assert orchestrator._integer_like(-1) is None
        assert orchestrator._integer_like("-1") is None
        assert orchestrator._integer_like("abc") is None
        assert orchestrator._integer_like(None) is None
        assert orchestrator._integer_like([]) is None

    def test_integer_token_map_identifies_token_maps(self, orchestrator):
        """Test identification of token usage maps."""
        # Valid token maps
        assert orchestrator._integer_token_map({"input_tokens": 10, "output_tokens": 5})
        assert orchestrator._integer_token_map(
            {"prompt_tokens": 10, "completion_tokens": 5}
        )
        assert orchestrator._integer_token_map({"total_tokens": 15})

        # Mixed case variants
        assert orchestrator._integer_token_map({"inputTokens": 10})
        assert orchestrator._integer_token_map({"INPUT_TOKENS": 10})

        # Invalid maps
        assert not orchestrator._integer_token_map({"not_a_token": 10})
        assert not orchestrator._integer_token_map({"random_field": "value"})
        assert not orchestrator._integer_token_map({})

    def test_get_token_usage_extracts_common_fields(self, orchestrator):
        """Test extraction of token counts from usage maps."""
        usage = {
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
        }

        assert orchestrator._get_token_usage(usage, "input") == 10
        assert orchestrator._get_token_usage(usage, "output") == 5
        assert orchestrator._get_token_usage(usage, "total") == 15

        # Test alternative field names
        usage_alt = {
            "prompt_tokens": 20,
            "completion_tokens": 10,
        }

        assert orchestrator._get_token_usage(usage_alt, "input") == 20
        assert orchestrator._get_token_usage(usage_alt, "output") == 10

    def test_compute_token_delta_uses_last_reported(self, orchestrator):
        """Test that token delta is computed relative to last reported."""
        entry = RunningEntry(
            issue_id="test-id",
            issue_identifier="TEST-1",
            state="In Progress",
            codex_last_reported_input_tokens=100,
            codex_last_reported_output_tokens=50,
            codex_last_reported_total_tokens=150,
        )

        # New totals higher than last reported
        usage = {
            "input_tokens": 150,
            "output_tokens": 75,
            "total_tokens": 225,
        }

        input_delta = orchestrator._compute_token_delta(
            entry, "input", usage, "codex_last_reported_input_tokens"
        )
        output_delta = orchestrator._compute_token_delta(
            entry, "output", usage, "codex_last_reported_output_tokens"
        )
        total_delta = orchestrator._compute_token_delta(
            entry, "total", usage, "codex_last_reported_total_tokens"
        )

        # Delta should be difference
        assert input_delta["delta"] == 50
        assert input_delta["reported"] == 150

        assert output_delta["delta"] == 25
        assert output_delta["reported"] == 75

        assert total_delta["delta"] == 75
        assert total_delta["reported"] == 225

    def test_compute_token_delta_handles_no_increase(self, orchestrator):
        """Test delta computation when totals don't increase."""
        entry = RunningEntry(
            issue_id="test-id",
            issue_identifier="TEST-1",
            state="In Progress",
            codex_last_reported_input_tokens=100,
        )

        # Same totals
        usage = {"input_tokens": 100}

        delta = orchestrator._compute_token_delta(
            entry, "input", usage, "codex_last_reported_input_tokens"
        )

        assert delta["delta"] == 0
        assert delta["reported"] == 100

    def test_extract_token_usage_from_various_locations(self, orchestrator):
        """Test extraction of usage from different payload locations."""
        # Direct usage field
        update1 = {
            "event": "turn/completed",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
        usage1 = orchestrator._extract_token_usage(update1)
        assert usage1["input_tokens"] == 10

        # Nested in params
        update2 = {
            "event": "turn/completed",
            "params": {"usage": {"input_tokens": 20}},
        }
        usage2 = orchestrator._extract_token_usage(update2)
        assert usage2["input_tokens"] == 20

        # tokenUsage variant
        update3 = {
            "event": "turn/completed",
            "params": {"tokenUsage": {"total": 30}},
        }
        usage3 = orchestrator._extract_token_usage(update3)
        assert usage3["total"] == 30

    def test_extract_rate_limits_identifies_rate_limit_maps(self, orchestrator):
        """Test identification and extraction of rate limits."""
        # Valid rate limits map
        update = {
            "rate_limits": {
                "limit_id": "gpt-4",
                "primary": {"remaining": 1000, "reset_at": "2024-01-01T00:00:00Z"},
                "secondary": {"remaining": 500},
            }
        }

        limits = orchestrator._extract_rate_limits(update)
        assert limits is not None
        assert limits["limit_id"] == "gpt-4"
        assert "primary" in limits

        # Alternative field names
        update_alt = {
            "rateLimits": {
                "limitName": "gpt-4",
                "credits": {"remaining": 100},
            }
        }

        limits_alt = orchestrator._extract_rate_limits(update_alt)
        assert limits_alt is not None

        # Invalid rate limits
        invalid = {"not_rate_limits": {"value": 100}}
        assert orchestrator._extract_rate_limits(invalid) is None

    def test_is_rate_limits_map_validates_structure(self, orchestrator):
        """Test validation of rate limits map structure."""
        # Valid with primary bucket
        valid1 = {
            "limit_id": "test-limit",
            "primary": {"remaining": 100},
        }
        assert orchestrator._is_rate_limits_map(valid1)

        # Valid with credits bucket
        valid2 = {
            "limit_name": "test-limit",
            "credits": {"remaining": 100},
        }
        assert orchestrator._is_rate_limits_map(valid2)

        # Missing limit identifier
        invalid1 = {"primary": {"remaining": 100}}
        assert not orchestrator._is_rate_limits_map(invalid1)

        # Missing buckets
        invalid2 = {"limit_id": "test", "other_field": 100}
        assert not orchestrator._is_rate_limits_map(invalid2)

    def test_extract_token_delta_from_update(self, orchestrator):
        """Test full extraction of token delta from update."""
        entry = RunningEntry(
            issue_id="test-id",
            issue_identifier="TEST-1",
            state="In Progress",
            codex_last_reported_input_tokens=50,
            codex_last_reported_output_tokens=25,
            codex_last_reported_total_tokens=75,
        )

        update = {
            "event": "turn/completed",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150,
            },
        }

        delta = orchestrator._extract_token_delta(entry, update)

        assert delta["input_tokens"] == 50  # 100 - 50
        assert delta["output_tokens"] == 25  # 50 - 25
        assert delta["total_tokens"] == 75  # 150 - 75
        assert delta["input_reported"] == 100
        assert delta["output_reported"] == 50
        assert delta["total_reported"] == 150

    def test_apply_codex_token_delta_updates_entry_and_state(self, orchestrator):
        """Test that token delta is applied to entry and state."""
        entry = RunningEntry(
            issue_id="test-id",
            issue_identifier="TEST-1",
            state="In Progress",
            codex_input_tokens=10,
            codex_output_tokens=5,
            codex_total_tokens=15,
        )

        token_delta = {
            "input_tokens": 20,
            "output_tokens": 10,
            "total_tokens": 30,
            "input_reported": 100,
            "output_reported": 50,
            "total_reported": 150,
        }

        orchestrator._apply_codex_token_delta(entry, token_delta)

        # Check entry updated
        assert entry.codex_input_tokens == 30  # 10 + 20
        assert entry.codex_output_tokens == 15  # 5 + 10
        assert entry.codex_total_tokens == 45  # 15 + 30

        # Check last reported updated
        assert entry.codex_last_reported_input_tokens == 100
        assert entry.codex_last_reported_output_tokens == 50
        assert entry.codex_last_reported_total_tokens == 150

        # Check state aggregates updated
        assert orchestrator.state.codex_totals["input_tokens"] == 20
        assert orchestrator.state.codex_totals["output_tokens"] == 10
        assert orchestrator.state.codex_totals["total_tokens"] == 30

    def test_apply_codex_rate_limits_stores_in_state(self, orchestrator):
        """Test that rate limits are stored in orchestrator state."""
        rate_limits = {
            "limit_id": "gpt-4",
            "primary": {"remaining": 1000, "reset_at": "2024-01-01T00:00:00Z"},
        }

        orchestrator._apply_codex_rate_limits(rate_limits)

        assert orchestrator.state.rate_limits == rate_limits

    def test_integrate_codex_update_full_integration(self, orchestrator):
        """Test full integration of Codex update."""
        entry = RunningEntry(
            issue_id="test-id",
            issue_identifier="TEST-1",
            state="In Progress",
        )

        update = {
            "event": "turn/completed",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150,
            },
            "rate_limits": {
                "limit_id": "gpt-4",
                "primary": {"remaining": 1000},
            },
        }

        orchestrator._integrate_codex_update(entry, update)

        # Check tokens updated
        assert entry.codex_input_tokens == 100
        assert entry.codex_output_tokens == 50
        assert entry.codex_total_tokens == 150

        # Check last reported
        assert entry.codex_last_reported_input_tokens == 100
        assert entry.codex_last_reported_output_tokens == 50
        assert entry.codex_last_reported_total_tokens == 150

        # Check state aggregates
        assert orchestrator.state.codex_totals["input_tokens"] == 100
        assert orchestrator.state.codex_totals["output_tokens"] == 50

        # Check rate limits stored
        assert orchestrator.state.rate_limits is not None
        assert orchestrator.state.rate_limits["limit_id"] == "gpt-4"

    def test_token_accounting_avoids_double_counting(self, orchestrator):
        """Test that token accounting avoids double-counting the same totals."""
        entry = RunningEntry(
            issue_id="test-id",
            issue_identifier="TEST-1",
            state="In Progress",
        )

        # First update with totals
        update1 = {
            "event": "turn/completed",
            "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        }

        orchestrator._integrate_codex_update(entry, update1)

        assert entry.codex_input_tokens == 100
        assert orchestrator.state.codex_totals["input_tokens"] == 100

        # Second update with SAME totals (should not count again)
        update2 = {
            "event": "turn/completed",
            "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        }

        orchestrator._integrate_codex_update(entry, update2)

        # Totals should remain the same (delta was 0)
        assert entry.codex_input_tokens == 100
        assert orchestrator.state.codex_totals["input_tokens"] == 100

        # Third update with higher totals
        update3 = {
            "event": "turn/completed",
            "usage": {"input_tokens": 150, "output_tokens": 75, "total_tokens": 225},
        }

        orchestrator._integrate_codex_update(entry, update3)

        # Should only count the delta
        assert entry.codex_input_tokens == 150  # 100 + 50
        assert orchestrator.state.codex_totals["input_tokens"] == 150  # 100 + 50

    def test_state_snapshot_includes_token_information(self, orchestrator):
        """Test that state snapshot includes token information for running entries."""
        entry = RunningEntry(
            issue_id="test-id",
            issue_identifier="TEST-1",
            state="In Progress",
            session_id="session-123",
            codex_input_tokens=100,
            codex_output_tokens=50,
            codex_total_tokens=150,
        )

        orchestrator.state.running["test-id"] = entry

        snapshot = orchestrator.get_state_snapshot()

        # Check that running entry includes token fields
        running_entry = snapshot["running"][0]
        assert "codex_input_tokens" in running_entry
        assert "codex_output_tokens" in running_entry
        assert "codex_total_tokens" in running_entry

        assert running_entry["codex_input_tokens"] == 100
        assert running_entry["codex_output_tokens"] == 50
        assert running_entry["codex_total_tokens"] == 150

    def test_absolute_token_usage_from_payload(self, orchestrator):
        """Test extraction of absolute token usage from known paths."""
        # Path: params.tokenUsage.total
        payload1 = {
            "params": {
                "tokenUsage": {
                    "total": {
                        "input_tokens": 100,
                        "output_tokens": 50,
                    }
                }
            }
        }

        usage1 = orchestrator._absolute_token_usage_from_payload(payload1)
        assert usage1 is not None
        assert usage1["input_tokens"] == 100

        # Path: params.msg.payload.info.total_token_usage
        payload2 = {
            "params": {
                "msg": {
                    "payload": {
                        "info": {
                            "total_token_usage": {
                                "input_tokens": 200,
                                "output_tokens": 100,
                            }
                        }
                    }
                }
            }
        }

        usage2 = orchestrator._absolute_token_usage_from_payload(payload2)
        assert usage2 is not None
        assert usage2["input_tokens"] == 200

        # Invalid path
        payload3 = {"random": {"nested": {"path": 100}}}
        usage3 = orchestrator._absolute_token_usage_from_payload(payload3)
        assert usage3 is None

    def test_multiple_sessions_accumulate_tokens_correctly(self, orchestrator):
        """Test that multiple sessions accumulate tokens correctly in state."""
        entry1 = RunningEntry(
            issue_id="test-id-1",
            issue_identifier="TEST-1",
            state="In Progress",
        )

        entry2 = RunningEntry(
            issue_id="test-id-2",
            issue_identifier="TEST-2",
            state="In Progress",
        )

        # Update first session
        update1 = {
            "event": "turn/completed",
            "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        }

        orchestrator._integrate_codex_update(entry1, update1)

        assert orchestrator.state.codex_totals["input_tokens"] == 100

        # Update second session
        update2 = {
            "event": "turn/completed",
            "usage": {"input_tokens": 200, "output_tokens": 100, "total_tokens": 300},
        }

        orchestrator._integrate_codex_update(entry2, update2)

        # Both sessions should be accumulated
        assert orchestrator.state.codex_totals["input_tokens"] == 300  # 100 + 200
        assert orchestrator.state.codex_totals["output_tokens"] == 150  # 50 + 100
        assert orchestrator.state.codex_totals["total_tokens"] == 450  # 150 + 300
