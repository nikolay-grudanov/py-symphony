"""Main orchestrator - coordinates all operations."""

import time
from datetime import datetime
from typing import Dict, Any, Optional

from .state import OrchestratorState
from .scheduler import Scheduler


class Orchestrator:
    """Main orchestrator."""

    def __init__(self):
        self._state = OrchestratorState()
        self._scheduler = Scheduler(self._state)
        # Polling state
        self._poll_check_in_progress = False
        self._next_poll_due_at_ms: Optional[int] = None

    def start(self):
        """Start orchestrator."""
        # TODO: Validate config, cleanup, start scheduler
        pass

    def stop(self):
        """Stop orchestrator."""
        pass

    def get_state_snapshot(self) -> Dict[str, Any]:
        """
        Get a snapshot of current orchestrator state for dashboards/monitoring.

        Returns:
            Dict containing:
                - running: list of active sessions with full info
                - retrying: list of retry queue entries
                - codex_totals: aggregated tokens and runtime seconds
                - rate_limits: latest known rate limits (if any)
                - polling: polling status (checking?, next_poll_in_ms, interval)
        """
        now = datetime.utcnow()
        now_ms = int(time.time() * 1000)

        # Build running sessions list
        running = []
        for issue_id, metadata in self._state.running.items():
            started_at = metadata.get("started_at")
            runtime_seconds = self._compute_runtime_seconds(started_at, now)

            running_entry = {
                "issue_id": issue_id,
                "identifier": metadata.get("identifier"),
                "state": metadata.get("issue", {}).get("state")
                if metadata.get("issue")
                else None,
                "worker_host": metadata.get("worker_host"),
                "workspace_path": metadata.get("workspace_path"),
                "session_id": metadata.get("session_id"),
                "codex_app_server_pid": metadata.get("codex_app_server_pid"),
                "codex_input_tokens": metadata.get("codex_input_tokens", 0),
                "codex_output_tokens": metadata.get("codex_output_tokens", 0),
                "codex_total_tokens": metadata.get("codex_total_tokens", 0),
                "turn_count": metadata.get("turn_count", 0),
                "started_at": started_at,
                "last_codex_timestamp": metadata.get("last_codex_timestamp"),
                "last_codex_message": metadata.get("last_codex_message"),
                "last_codex_event": metadata.get("last_codex_event"),
                "runtime_seconds": runtime_seconds,
            }
            running.append(running_entry)

        # Build retry queue list
        retrying = []
        for issue_id, retry_entry in self._state.retry_attempts.items():
            due_at_ms = retry_entry.get("due_at_ms")
            due_in_ms = max(0, due_at_ms - now_ms) if due_at_ms is not None else None

            retry_entry_info = {
                "issue_id": issue_id,
                "attempt": retry_entry.get("attempt"),
                "due_in_ms": due_in_ms,
                "identifier": retry_entry.get("identifier"),
                "error": retry_entry.get("error"),
                "worker_host": retry_entry.get("worker_host"),
                "workspace_path": retry_entry.get("workspace_path"),
            }
            retrying.append(retry_entry_info)

        # Build polling status
        polling = {
            "checking?": self._poll_check_in_progress,
            "next_poll_in_ms": self._compute_next_poll_in_ms(
                self._next_poll_due_at_ms, now_ms
            ),
            "poll_interval_ms": self._state.poll_interval_ms,
        }

        # Get rate limits (if available in state)
        rate_limits = getattr(self._state, "codex_rate_limits", None)

        return {
            "running": running,
            "retrying": retrying,
            "codex_totals": self._state.codex_totals,
            "rate_limits": rate_limits,
            "polling": polling,
        }

    def _compute_runtime_seconds(
        self, started_at: Optional[Any], now: datetime
    ) -> float:
        """
        Compute runtime seconds for a session.

        Args:
            started_at: Session start time (datetime or None)
            now: Current time

        Returns:
            Runtime seconds as float, or 0 if started_at is None
        """
        if started_at is None:
            return 0.0

        if isinstance(started_at, datetime):
            return (now - started_at).total_seconds()

        return 0.0

    def _compute_next_poll_in_ms(
        self, next_poll_due_at_ms: Optional[int], now_ms: int
    ) -> Optional[int]:
        """
        Compute time until next poll in milliseconds.

        Args:
            next_poll_due_at_ms: Next poll due time (monotonic timestamp) or None
            now_ms: Current time in milliseconds

        Returns:
            Milliseconds until next poll, or None if not scheduled
        """
        if next_poll_due_at_ms is None:
            return None

        return max(0, next_poll_due_at_ms - now_ms)

    # Polling state management methods (to be used by scheduler)
    def _set_poll_check_in_progress(self, in_progress: bool):
        """Set polling check in progress flag."""
        self._poll_check_in_progress = in_progress

    def _set_next_poll_due_at_ms(self, due_at_ms: Optional[int]):
        """Set next poll due time in milliseconds (monotonic timestamp)."""
        self._next_poll_due_at_ms = due_at_ms
