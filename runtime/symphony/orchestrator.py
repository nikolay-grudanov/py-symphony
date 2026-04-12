"""Orchestrator - poll loop, state machine, dispatch, reconciliation, retry."""

import asyncio
import logging
import time
import datetime as dt
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from .config import Config
from .tracker import Issue
from .workspace import WorkspaceManager
from .agent import AgentRunner, AgentEvent, RunAttempt
from ..tracker.facade import TrackerFacade


logger = logging.getLogger(__name__)


class IssueState(Enum):
    """Orchestrator's internal claim state (per SPEC.md Section 7.1)."""

    UNCLAIMED = "unclaimed"
    CLAIMED = "claimed"
    RUNNING = "running"
    RETRY_QUEUED = "retry_queued"
    RELEASED = "released"


@dataclass
class RunningEntry:
    """An issue currently being worked on."""

    issue_id: str
    issue_identifier: str
    state: str  # tracker state (Todo, In Progress, etc.)
    session_id: Optional[str] = None
    turn_count: int = 0
    last_event: Optional[str] = None
    last_event_at: Optional[str] = None
    worker_host: Optional[str] = None  # SSH worker host if configured
    workspace_path: Optional[str] = None  # Workspace path for this issue
    codex_app_server_pid: Optional[str] = None  # Codex app-server process ID
    started_at: str = field(
        default_factory=lambda: (
            dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        )
    )
    # Token accounting (per SPEC.md Section 13.5)
    codex_input_tokens: int = 0
    codex_output_tokens: int = 0
    codex_total_tokens: int = 0
    codex_last_reported_input_tokens: int = 0
    codex_last_reported_output_tokens: int = 0
    codex_last_reported_total_tokens: int = 0


@dataclass
class RetryEntry:
    """Scheduled retry for an issue."""

    issue_id: str
    identifier: str  # human-readable
    attempt: int  # 1-based
    due_at_ms: int  # monotonic timestamp
    error: Optional[str] = None
    worker_host: Optional[str] = None  # SSH worker host if configured
    workspace_path: Optional[str] = None  # Workspace path for this issue


@dataclass
class OrchestratorState:
    """In-memory runtime state (per SPEC.md Section 4.1.8)."""

    running: dict[str, RunningEntry] = field(default_factory=dict)
    claimed: set[str] = field(default_factory=set)
    retry_attempts: dict[str, RetryEntry] = field(default_factory=dict)
    completed: set[str] = field(default_factory=set)

    # Aggregate metrics
    codex_totals: dict = field(
        default_factory=lambda: {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "seconds_running": 0.0,
        }
    )
    rate_limits: Optional[dict] = None


class Orchestrator:
    """
    Main orchestration engine.

    Per SPEC.md Section 3, this is the central coordinator that:
    - Owns the poll tick
    - Owns in-memory runtime state
    - Decides which issues to dispatch, retry, stop, or release
    - Tracks session metrics and retry queue state
    """

    def __init__(
        self,
        config: Config,
        tracker_facade: TrackerFacade,
        workspace_manager: WorkspaceManager,
        agent_runner: AgentRunner,
    ):
        self.config = config
        self.tracker_facade = tracker_facade
        self.workspace_manager = workspace_manager
        self.agent_runner = agent_runner

        self.state = OrchestratorState()
        self._running = False
        self._poll_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

        # Polling state for observability
        self._poll_check_in_progress = False
        self._next_poll_due_at_ms: Optional[int] = None

    async def start(self) -> None:
        """Start the orchestrator."""
        self._running = True

        # Startup cleanup: remove workspaces for terminal issues (SPEC.md Section 8.6)
        await self._startup_terminal_cleanup()

        # Schedule immediate first tick
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("Orchestrator started")

    async def stop(self) -> None:
        """Stop the orchestrator."""
        self._running = False
        self._stop_event.set()

        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

        # Cancel all running sessions
        for issue_id in list(self.state.running.keys()):
            await self._release_issue(issue_id, "orchestrator_stopped")

        logger.info("Orchestrator stopped")

    async def _poll_loop(self) -> None:
        """Main poll loop (per SPEC.md Section 8.1)."""
        while self._running:
            try:
                # Set next poll due time
                self._next_poll_due_at_ms = (
                    int(time.time() * 1000) + self.config.polling_interval_ms
                )

                # Run tick
                await self._tick()
            except Exception as e:
                logger.error(f"Poll tick error: {e}")

            # Wait for next tick
            await asyncio.sleep(self.config.polling_interval_ms / 1000)

    async def _tick(self) -> None:
        """
        Per SPEC.md Section 8.1 Tick Sequence:
        1. Reconcile running issues
        2. Run dispatch preflight validation
        3. Fetch candidate issues from tracker
        4. Sort issues by dispatch priority
        5. Dispatch eligible issues while slots remain
        6. Notify observability/status consumers
        """
        # Mark poll check in progress
        self._poll_check_in_progress = True

        try:
            # Part 1: Reconciliation (stall detection + state refresh)
            await self._reconcile_running()

            # Part 2: Preflight validation
            if not self._validate_dispatch():
                logger.warning("Dispatch validation failed, skipping dispatch")
                return

            # Part 3: Fetch candidates
            try:
                candidates = await self.tracker_facade.fetch_candidate_issues()
            except Exception as e:
                logger.error(f"Failed to fetch candidates: {e}")
                return

            # Part 4: Sort by priority (SPEC.md Section 8.2)
            sorted_issues = self._sort_candidates(candidates)

            # Part 5: Dispatch eligible issues
            for issue in sorted_issues:
                if not self._can_dispatch(issue):
                    break
                if self._is_dispatch_eligible(issue):
                    await self._dispatch_issue(issue)

        finally:
            # Mark poll check complete
            self._poll_check_in_progress = False

    async def _startup_terminal_cleanup(self) -> None:
        """Per SPEC.md Section 8.6: clean up workspaces for terminal issues."""
        logger.info("Running startup terminal cleanup")

        try:
            terminal_issues = await self.tracker_facade.fetch_issues_by_states(
                self.config.tracker_terminal_states
            )

            for issue in terminal_issues:
                self.workspace_manager.cleanup_workspace(issue.identifier)

            logger.info(f"Cleaned {len(terminal_issues)} terminal workspaces")
        except Exception as e:
            logger.warning(f"Startup terminal cleanup failed: {e}")

    async def _reconcile_running(self) -> None:
        """
        Per SPEC.md Section 8.5: Active Run Reconciliation.

        Part A: Stall detection
        Part B: Tracker state refresh
        """
        # Part A: Stall detection
        await self._reconcile_stalled_running_issues()

        # Part B: Tracker state refresh
        running_ids = list(self.state.running.keys())

        if not running_ids:
            return

        # Part B: Fetch current states
        try:
            current_states = await self.tracker_facade.fetch_issue_states(running_ids)
        except Exception as e:
            logger.warning(f"Failed to refresh issue states: {e}")
            return

        # Check each running issue
        for issue_id, tracker_state in current_states.items():
            entry = self.state.running.get(issue_id)
            if not entry:
                continue

            # Check if terminal
            if tracker_state.lower() in [
                s.lower() for s in self.config.tracker_terminal_states
            ]:
                logger.info(
                    f"Issue {entry.issue_identifier} became terminal, cleaning up"
                )
                await self._stop_and_release_issue(issue_id, "became_terminal")
                continue

            # Check if no longer active
            if tracker_state.lower() not in [
                s.lower() for s in self.config.tracker_active_states
            ]:
                logger.info(
                    f"Issue {entry.issue_identifier} no longer active, stopping"
                )
                await self._stop_and_release_issue(issue_id, "no_longer_active")
                continue

            # Update in-memory state
            entry.state = tracker_state

    async def _reconcile_stalled_running_issues(self) -> None:
        """
        Per SPEC.md Section 8.5 Part A: Stall detection.

        Check all running issues for inactivity and restart those that have stalled.
        """
        timeout_ms = self.config.codex_stall_timeout_ms

        # Disabled if timeout <= 0
        if timeout_ms <= 0:
            return

        # No running issues to check
        if not self.state.running:
            return

        # Check each running issue
        for issue_id, running_entry in list(self.state.running.items()):
            await self._restart_stalled_issue(issue_id, running_entry, timeout_ms)

    async def _restart_stalled_issue(
        self, issue_id: str, running_entry: RunningEntry, timeout_ms: int
    ) -> None:
        """
        Check if an issue has stalled and restart it with backoff if needed.

        Args:
            issue_id: The issue identifier
            running_entry: The running entry for the issue
            timeout_ms: The stall timeout in milliseconds
        """
        elapsed_ms = self._stall_elapsed_ms(running_entry)

        if elapsed_ms is not None and elapsed_ms > timeout_ms:
            session_id = running_entry.session_id

            logger.warning(
                f"Issue stalled: issue_id={issue_id} issue_identifier={running_entry.issue_identifier} "
                f"session_id={session_id} elapsed_ms={elapsed_ms}; restarting with backoff"
            )

            # Stop and release the issue
            await self._stop_and_release_issue(issue_id, "stalled")

            # Schedule retry with backoff (start with attempt=1 for stall restart)
            await self._schedule_retry(
                issue_id,
                running_entry.issue_identifier,
                attempt_num=1,
                error=f"stalled for {elapsed_ms}ms without codex activity",
            )

    def _stall_elapsed_ms(self, running_entry: RunningEntry) -> Optional[int]:
        """
        Calculate the elapsed time since the last activity.

        Args:
            running_entry: The running entry to check

        Returns:
            Elapsed time in milliseconds, or None if cannot be determined
        """
        timestamp = self._last_activity_timestamp(running_entry)

        if timestamp is None:
            return None

        try:
            # Parse ISO format timestamp (handle both "Z" and "+00:00" suffixes)
            if timestamp.endswith("Z"):
                timestamp = timestamp[:-1] + "+00:00"
            activity_time = dt.datetime.fromisoformat(timestamp)

            # Get current UTC time (timezone-aware)
            now = dt.datetime.now(dt.timezone.utc)

            # Calculate elapsed time in milliseconds
            elapsed = now - activity_time
            return max(0, int(elapsed.total_seconds() * 1000))
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse activity timestamp: {e}")
            return None

    def _last_activity_timestamp(self, running_entry: RunningEntry) -> Optional[str]:
        """
        Get the timestamp of the last activity for a running entry.

        Per SPEC.md Section 8.5 Part A: use last_event_at if available,
        otherwise fall back to started_at.

        Args:
            running_entry: The running entry to check

        Returns:
            ISO format timestamp string or None
        """
        return running_entry.last_event_at or running_entry.started_at

    def _validate_dispatch(self) -> bool:
        """Per SPEC.md Section 6.3: dispatch preflight validation."""
        if not self.config.tracker_kind:
            return False
        if not self.config.tracker_api_key:
            return False
        if not self.config.tracker_project_slug:
            return False
        if not self.config.codex_command:
            return False
        return True

    def _sort_candidates(self, issues: list[Issue]) -> list[Issue]:
        """Per SPEC.md Section 8.2: sort by priority, created_at, identifier."""
        return sorted(
            issues,
            key=lambda i: (
                i.priority if i.priority is not None else 999,
                i.created_at or "",
                i.identifier,
            ),
        )

    def _can_dispatch(self, issue: Optional[Issue] = None) -> bool:
        """
        Check if we have available concurrency slots.

        Per SPEC.md Section 8.3:
        - Check per-state limit if present (state key normalized)
        - Otherwise fallback to global limit

        Args:
            issue: Optional issue to check per-state limits

        Returns:
            True if dispatch is possible, False otherwise
        """
        # Check global agent limit
        running_count = len(self.state.running)
        if running_count >= self.config.agent_max_concurrent_agents:
            return False

        # Check per-state limit if issue provided and state limits configured
        if issue and self.config.agent_max_concurrent_agents_by_state:
            if not self._state_slots_available(issue, self.state.running):
                return False

        # Check worker host slots if SSH hosts configured
        if self.config.worker_ssh_hosts:
            return self._worker_slots_available()

        return True

    def _worker_slots_available(
        self, preferred_worker_host: Optional[str] = None
    ) -> bool:
        """Check if any worker host has available slots."""
        return self._select_worker_host(preferred_worker_host) is not None

    def _select_worker_host(
        self, preferred_worker_host: Optional[str] = None
    ) -> Optional[str]:
        """
        Select the best worker host for a new agent.

        Args:
            preferred_worker_host: Preferred host if it has available slots

        Returns:
            Selected host or None if no capacity available
        """
        hosts = self.config.worker_ssh_hosts

        if not hosts:
            return None

        # Filter hosts with available slots
        available_hosts = [
            host for host in hosts if self._worker_host_slots_available(host)
        ]

        if not available_hosts:
            logger.warning("No worker hosts with available capacity")
            return None

        # Use preferred host if available
        if self._preferred_worker_host_available(
            preferred_worker_host, available_hosts
        ):
            return preferred_worker_host

        # Otherwise select least loaded host
        return self._least_loaded_worker_host(available_hosts)

    def _preferred_worker_host_available(
        self, preferred_worker_host: Optional[str], hosts: list[str]
    ) -> bool:
        """Check if preferred worker host is available and has slots."""
        if not preferred_worker_host or not hosts:
            return False
        return preferred_worker_host in hosts

    def _least_loaded_worker_host(self, hosts: list[str]) -> str:
        """Select the host with the fewest running agents."""
        # Sort by load (count) then by index for determinism
        host_counts = [
            (host, self._running_worker_host_count(host), idx)
            for idx, host in enumerate(hosts)
        ]
        # Select host with minimum (count, idx)
        min_host = min(host_counts, key=lambda x: (x[1], x[2]))
        return min_host[0]

    def _running_worker_host_count(self, worker_host: str) -> int:
        """Count number of agents currently running on a specific host."""
        return sum(
            1
            for entry in self.state.running.values()
            if entry.worker_host == worker_host
        )

    def _worker_host_slots_available(self, worker_host: str) -> bool:
        """Check if a specific worker host has available slots."""
        limit = self.config.worker_max_concurrent_agents_per_host

        # If limit is None or 0, treat as unlimited
        if limit is None or limit <= 0:
            return True

        return self._running_worker_host_count(worker_host) < limit

    def _normalize_issue_state(self, state: str) -> str:
        """Normalize issue state to lowercase for consistent matching."""
        return state.lower() if state else ""

    def _running_issue_count_for_state(
        self, running: dict[str, RunningEntry], issue_state: str
    ) -> int:
        """
        Count number of issues currently running for a specific state.

        Per SPEC.md Section 8.3: count issues by their current tracked state
        in the running map.

        Args:
            running: The running entries dictionary
            issue_state: The state to count (will be normalized)

        Returns:
            Count of running issues with the matching state
        """
        normalized_state = self._normalize_issue_state(issue_state)
        return sum(
            1
            for entry in running.values()
            if self._normalize_issue_state(entry.state) == normalized_state
        )

    def _state_slots_available(
        self, issue: Issue, running: dict[str, RunningEntry]
    ) -> bool:
        """
        Check if there are available slots for the issue's state.

        Per SPEC.md Section 8.3:
        - Check per-state limit if present (state key normalized)
        - Otherwise fallback to global limit

        Args:
            issue: The issue to check
            running: The running entries dictionary

        Returns:
            True if state has available slots, False otherwise
        """
        # Get per-state limits (normalized keys)
        per_state_limits = self.config.agent_max_concurrent_agents_by_state

        # Normalize the issue state for lookup
        normalized_state = self._normalize_issue_state(issue.state)

        # Check if there's a specific limit for this state
        if normalized_state in per_state_limits:
            limit = per_state_limits[normalized_state]
            used = self._running_issue_count_for_state(running, issue.state)
            return limit > used

        # No per-state limit configured - fallback to global limit
        # This is handled by the caller (_can_dispatch)
        return True

    def _is_dispatch_eligible(self, issue: Issue) -> bool:
        """Per SPEC.md Section 8.2: check if issue can be dispatched."""
        # Must have required fields
        if not all([issue.id, issue.identifier, issue.title, issue.state]):
            return False

        # Must be in active state
        if issue.state.lower() not in [
            s.lower() for s in self.config.tracker_active_states
        ]:
            return False

        # Must not be in terminal state (belt and suspenders check)
        if issue.state.lower() in [
            s.lower() for s in self.config.tracker_terminal_states
        ]:
            return False

        # Must not already be claimed or running
        if issue.id in self.state.claimed or issue.id in self.state.running:
            return False

        # Blocker rule for Todo state
        if issue.state.lower() == "todo" and issue.blocked_by:
            for blocker in issue.blocked_by:
                if blocker.get("state", "").lower() not in [
                    s.lower() for s in self.config.tracker_terminal_states
                ]:
                    return False  # Has unblocked blocker

        return True

    async def _dispatch_issue(self, issue: Issue) -> None:
        """Dispatch an eligible issue to the agent runner."""
        # Select worker host if SSH hosts configured
        worker_host = self._select_worker_host()

        logger.info(f"Dispatching issue {issue.identifier}")

        if worker_host:
            logger.info(f"Selected worker host: {worker_host}")

        # Claim the issue
        self.state.claimed.add(issue.id)

        # Ensure workspace
        workspace = self.workspace_manager.ensure_workspace(issue.identifier)

        # Create running entry
        entry = RunningEntry(
            issue_id=issue.id,
            issue_identifier=issue.identifier,
            state=issue.state,
            worker_host=worker_host,
        )
        self.state.running[issue.id] = entry

        # Run the agent (async, will complete later)
        asyncio.create_task(self._run_agent(issue, workspace))

    async def _run_agent(self, issue: Issue, workspace) -> None:
        """Run agent for an issue and handle the result."""
        # TODO: Load prompt template and render with issue data
        prompt = f"Work on {issue.identifier}: {issue.title}"

        try:
            attempt = await self.agent_runner.run(
                issue=issue,
                workspace=workspace,
                prompt=prompt,
                event_callback=self._handle_agent_event,
            )

            # Handle result
            if attempt.status == "succeeded":
                await self._handle_success(issue.id, attempt)
            else:
                await self._handle_failure(issue.id, attempt)

        except Exception as e:
            logger.error(f"Agent run failed for {issue.identifier}: {e}")
            await self._handle_failure(issue.id, None, str(e))

    def _handle_agent_event(self, event: AgentEvent) -> None:
        """Handle agent lifecycle events."""
        # Update running entry
        entry = self.state.running.get(event.issue_id)
        if entry:
            entry.last_event = event.event
            entry.last_event_at = event.timestamp

            if event.session_id:
                entry.session_id = event.session_id

            # Integrate Codex update (token accounting + rate limits)
            if event.usage:
                update = {
                    "event": event.event,
                    "timestamp": event.timestamp,
                    "usage": event.usage,
                }
                self._integrate_codex_update(entry, update)

    async def _handle_success(self, issue_id: str, attempt: RunAttempt) -> None:
        """Per SPEC.md Section 7.3: handle successful worker exit."""
        logger.info(f"Issue {attempt.issue_identifier} succeeded")

        # Update totals
        # (Would add runtime seconds here)

        # Schedule continuation retry (short delay, attempt=1)
        await self._schedule_retry(
            issue_id,
            attempt.issue_identifier,
            attempt_num=1,
            error=None,
            continuation=True,
        )

        # Remove from running
        if issue_id in self.state.running:
            del self.state.running[issue_id]

    async def _handle_failure(
        self, issue_id: str, attempt: Optional[RunAttempt], error: Optional[str] = None
    ) -> None:
        """Per SPEC.md Section 7.3: handle abnormal worker exit."""
        identifier = attempt.issue_identifier if attempt else "unknown"
        logger.info(
            f"Issue {identifier} failed: {error or attempt.error if attempt else 'unknown'}"
        )

        # Update totals
        # (Would add runtime seconds here)

        # Remove from running
        if issue_id in self.state.running:
            del self.state.running[issue_id]

        # Schedule retry with exponential backoff
        current_attempt = attempt.attempt if attempt and attempt.attempt else 0
        attempt_num = current_attempt + 1
        await self._schedule_retry(
            issue_id,
            identifier,
            attempt_num,
            error or (attempt.error if attempt else "unknown"),
        )

    async def _schedule_retry(
        self,
        issue_id: str,
        identifier: str,
        attempt_num: int,
        error: Optional[str],
        continuation: bool = False,
    ) -> None:
        """Per SPEC.md Section 8.4: schedule a retry with backoff."""
        # Cancel existing retry if any
        if issue_id in self.state.retry_attempts:
            del self.state.retry_attempts[issue_id]

        # Calculate delay
        if continuation:
            delay_ms = 1000  # Short fixed delay for continuation
        else:
            # Exponential backoff: min(10000 * 2^(attempt-1), max_retry_backoff_ms)
            delay_ms = min(
                10000 * (2 ** (attempt_num - 1)), self.config.agent_max_retry_backoff_ms
            )

        due_at_ms = int(time.time() * 1000) + delay_ms

        # Create retry entry
        retry = RetryEntry(
            issue_id=issue_id,
            identifier=identifier,
            attempt=attempt_num,
            due_at_ms=due_at_ms,
            error=error,
        )
        self.state.retry_attempts[issue_id] = retry

        # Schedule timer
        asyncio.create_task(self._fire_retry(issue_id, delay_ms / 1000))

    async def _fire_retry(self, issue_id: str, delay_seconds: float) -> None:
        """Fire a retry after the delay."""
        await asyncio.sleep(delay_seconds)

        retry = self.state.retry_attempts.get(issue_id)
        if not retry:
            return

        # Check if still eligible
        try:
            candidates = await self.tracker_facade.fetch_candidate_issues()
        except Exception as e:
            logger.warning(f"Failed to fetch candidates for retry: {e}")
            return

        # Find the specific issue
        found = None
        for issue in candidates:
            if issue.id == issue_id:
                found = issue
                break

        if not found:
            # Issue no longer active
            logger.info(
                f"Retry for {retry.identifier} - issue no longer candidate, releasing"
            )
            self._release_claim(issue_id)
            del self.state.retry_attempts[issue_id]
            return

        # Check slots
        if not self._can_dispatch(found):
            logger.info(
                f"Retry for {retry.identifier} - no slots available, requeueing"
            )
            # Would requeue - simplified here
            return

        # Re-dispatch
        logger.info(f"Retrying {retry.identifier} (attempt {retry.attempt})")
        await self._dispatch_issue(found)

        # Remove retry entry
        del self.state.retry_attempts[issue_id]

    async def _stop_and_release_issue(self, issue_id: str, reason: str) -> None:
        """Stop a running issue and release the claim."""
        logger.info(f"Stopping issue {issue_id}: {reason}")

        if issue_id in self.state.running:
            del self.state.running[issue_id]

        await self._release_issue(issue_id, reason)

    async def _release_issue(self, issue_id: str, reason: str) -> None:
        """Release a claimed issue."""
        self._release_claim(issue_id)

    def _release_claim(self, issue_id: str) -> None:
        """Release claim without stopping anything."""
        self.state.claimed.discard(issue_id)

    # Token accounting methods (per SPEC.md Section 13.5)

    def _extract_token_usage(self, update: dict) -> dict:
        """
        Extract token usage from event payload.

        Per SPEC.md Section 13.5: prefer absolute thread totals when available,
        such as total_token_usage or tokenUsage/total fields.
        """
        # Try different payload locations
        payloads = [
            update.get("usage"),
            update.get("payload"),
            update.get("params", {}).get("usage"),
            update.get("params", {}).get("tokenUsage"),
            update.get("tokenUsage"),
        ]

        # Try to find absolute token usage first
        for payload in payloads:
            if payload and isinstance(payload, dict):
                # Check for absolute total_token_usage
                usage = self._absolute_token_usage_from_payload(payload)
                if usage:
                    return usage

                # Check for turn/completed or turn_completed usage
                # Note: can be "method" or "event" field
                event_type = update.get("method", "") or update.get("event", "")
                if event_type in ["turn/completed", "turn_completed"]:
                    # Extract standard usage fields
                    if self._integer_token_map(payload):
                        return payload

        # Also try nested absolute paths
        nested_paths = [
            lambda: (
                update.get("params", {})
                .get("msg", {})
                .get("payload", {})
                .get("info", {})
                .get("total_token_usage")
            ),
            lambda: (
                update.get("params", {})
                .get("msg", {})
                .get("info", {})
                .get("total_token_usage")
            ),
        ]

        for path_fn in nested_paths:
            value = path_fn()
            if value and isinstance(value, dict) and self._integer_token_map(value):
                return value

        return {}

    def _absolute_token_usage_from_payload(self, payload: dict) -> Optional[dict]:
        """
        Extract absolute token usage from known paths.

        Looks for total_token_usage in common locations.
        """
        absolute_paths = [
            ["params", "msg", "payload", "info", "total_token_usage"],
            ["params", "msg", "info", "total_token_usage"],
            ["params", "tokenUsage", "total"],
            ["tokenUsage", "total"],
        ]

        for path in absolute_paths:
            value = payload
            try:
                for key in path:
                    value = value.get(key) if isinstance(value, dict) else None
                    if value is None:
                        break
                if value and isinstance(value, dict) and self._integer_token_map(value):
                    return value
            except (AttributeError, TypeError):
                continue

        return None

    def _extract_rate_limits(self, update: dict) -> Optional[dict]:
        """
        Extract rate limits from event payload.

        Per SPEC.md Section 13.5: track the latest rate-limit payload seen.
        """
        # Try different locations
        for key in ["rate_limits", "rateLimits"]:
            value = update.get(key)
            if value and self._is_rate_limits_map(value):
                return value

        # Check in payload
        payload = update.get("payload")
        if payload:
            if self._is_rate_limits_map(payload):
                return payload

            # Nested check
            for value in payload.values() if isinstance(payload, dict) else []:
                if self._is_rate_limits_map(value):
                    return value

        return None

    def _is_rate_limits_map(self, payload) -> bool:
        """
        Check if payload looks like a rate limits map.

        Should have limit_id/limit_name and buckets (primary/secondary/credits).
        """
        if not isinstance(payload, dict):
            return False

        # Check for limit identifier
        limit_id = (
            payload.get("limit_id")
            or payload.get("limitId")
            or payload.get("limit_name")
            or payload.get("limitName")
        )
        if not limit_id:
            return False

        # Check for buckets
        bucket_keys = [
            "primary",
            "secondary",
            "credits",
            "primary",
            "secondary",
            "credits",
        ]
        has_buckets = any(key in payload for key in bucket_keys)

        return has_buckets

    def _integer_token_map(self, payload: dict) -> bool:
        """
        Check if payload looks like a token usage map.

        Should contain integer token counts in common field names.
        """
        token_fields = [
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "prompt_tokens",
            "completion_tokens",
            "inputTokens",
            "outputTokens",
            "totalTokens",
            "promptTokens",
            "completionTokens",
            "INPUT_TOKENS",
            "OUTPUT_TOKENS",
            "TOTAL_TOKENS",
            "PROMPT_TOKENS",
            "COMPLETION_TOKENS",
            # Also support simple field names (as seen in some payloads)
            "input",
            "output",
            "total",
            "INPUT",
            "OUTPUT",
            "TOTAL",
        ]

        for field in token_fields:
            value = payload.get(field)
            if self._integer_like(value):
                return True

        return False

    def _integer_like(self, value) -> Optional[int]:
        """Extract integer value from various representations."""
        if isinstance(value, int) and value >= 0:
            return value

        if isinstance(value, str):
            try:
                num = int(value.strip())
                if num >= 0:
                    return num
            except ValueError:
                pass

        return None

    def _get_token_usage(self, usage: dict, token_type: str) -> Optional[int]:
        """
        Get token count for a specific type.

        Supports common field name variations.
        """
        field_mappings = {
            "input": [
                "input_tokens",
                "prompt_tokens",
                "input",
                "inputTokens",
                "promptTokens",
                "inputTokens",
                "INPUT_TOKENS",
                "PROMPT_TOKENS",
                "INPUT",
                # Also try completion tokens for input (some APIs use these)
                "completion_tokens",
                "completionTokens",
                "COMPLETION_TOKENS",
            ],
            "output": [
                "output_tokens",
                "completion_tokens",
                "output",
                "completion",
                "outputTokens",
                "completionTokens",
                "OUTPUT_TOKENS",
                "COMPLETION_TOKENS",
                "OUTPUT",
            ],
            "total": [
                "total_tokens",
                "total",
                "totalTokens",
                "totalTokens",
                "TOTAL_TOKENS",
                "TOTAL",
            ],
        }

        fields = field_mappings.get(token_type, [])

        for field in fields:
            value = usage.get(field)
            if self._integer_like(value) is not None:
                return self._integer_like(value)

        return None

    def _compute_token_delta(
        self,
        running_entry: RunningEntry,
        token_type: str,
        usage: dict,
        reported_key: str,
    ) -> dict:
        """
        Compute token delta relative to last reported value.

        Avoids double-counting by tracking last reported totals.
        """
        next_total = self._get_token_usage(usage, token_type)
        prev_reported = getattr(running_entry, reported_key, 0)

        delta = 0
        if next_total is not None and next_total >= prev_reported:
            delta = next_total - prev_reported

        reported = next_total if next_total is not None else prev_reported

        return {
            "delta": max(delta, 0),
            "reported": reported,
        }

    def _extract_token_delta(self, running_entry: RunningEntry, update: dict) -> dict:
        """
        Extract token delta from Codex update event.

        Returns dict with input/output/total deltas and reported values.
        """
        usage = self._extract_token_usage(update)

        input_result = self._compute_token_delta(
            running_entry, "input", usage, "codex_last_reported_input_tokens"
        )
        output_result = self._compute_token_delta(
            running_entry, "output", usage, "codex_last_reported_output_tokens"
        )
        total_result = self._compute_token_delta(
            running_entry, "total", usage, "codex_last_reported_total_tokens"
        )

        return {
            "input_tokens": input_result["delta"],
            "output_tokens": output_result["delta"],
            "total_tokens": total_result["delta"],
            "input_reported": input_result["reported"],
            "output_reported": output_result["reported"],
            "total_reported": total_result["reported"],
        }

    def _integrate_codex_update(
        self, running_entry: RunningEntry, update: dict
    ) -> None:
        """
        Process a Codex agent update event.

        Updates token counters and rate limits in the running entry
        and aggregates to orchestrator state.
        """
        # Extract and apply token delta
        token_delta = self._extract_token_delta(running_entry, update)
        self._apply_codex_token_delta(running_entry, token_delta)

        # Extract and apply rate limits
        rate_limits = self._extract_rate_limits(update)
        if rate_limits:
            self._apply_codex_rate_limits(rate_limits)

    def _apply_codex_token_delta(
        self, running_entry: RunningEntry, token_delta: dict
    ) -> None:
        """
        Apply token delta to running entry and state aggregates.

        Updates individual session totals and global aggregates.
        """
        # Update running entry totals
        running_entry.codex_input_tokens += token_delta.get("input_tokens", 0)
        running_entry.codex_output_tokens += token_delta.get("output_tokens", 0)
        running_entry.codex_total_tokens += token_delta.get("total_tokens", 0)

        # Update last reported values
        running_entry.codex_last_reported_input_tokens = token_delta.get(
            "input_reported", running_entry.codex_last_reported_input_tokens
        )
        running_entry.codex_last_reported_output_tokens = token_delta.get(
            "output_reported", running_entry.codex_last_reported_output_tokens
        )
        running_entry.codex_last_reported_total_tokens = token_delta.get(
            "total_reported", running_entry.codex_last_reported_total_tokens
        )

        # Update global aggregates
        self.state.codex_totals["input_tokens"] += token_delta.get("input_tokens", 0)
        self.state.codex_totals["output_tokens"] += token_delta.get("output_tokens", 0)
        self.state.codex_totals["total_tokens"] += token_delta.get("total_tokens", 0)

    def _apply_codex_rate_limits(self, rate_limits: dict) -> None:
        """
        Store the latest rate limits in orchestrator state.

        Per SPEC.md Section 13.5: track the latest rate-limit payload.
        """
        self.state.rate_limits = rate_limits

    def get_state_snapshot(self) -> dict:
        """
        Per SPEC.md Section 13.3: get runtime snapshot for observability.

        Returns snapshot containing:
            - running: list of running session rows with full info including turn_count
            - retrying: list of retry queue rows with due_in_ms
            - codex_totals: aggregated tokens and runtime seconds
            - rate_limits: latest coding-agent rate limit payload (if available)
            - polling: polling status (checking?, next_poll_in_ms, interval)
        """
        now = dt.datetime.now(dt.timezone.utc)
        now_ms = int(time.time() * 1000)

        # Build running sessions list with full information
        running = []
        for entry in self.state.running.values():
            runtime_seconds = self._compute_runtime_seconds(entry.started_at, now)

            running_entry = {
                "issue_id": entry.issue_id,
                "identifier": entry.issue_identifier,
                "state": entry.state,
                "worker_host": entry.worker_host,
                "workspace_path": entry.workspace_path,
                "session_id": entry.session_id,
                "codex_app_server_pid": entry.codex_app_server_pid,
                "codex_input_tokens": entry.codex_input_tokens,
                "codex_output_tokens": entry.codex_output_tokens,
                "codex_total_tokens": entry.codex_total_tokens,
                "turn_count": entry.turn_count,
                "started_at": entry.started_at,
                "last_codex_timestamp": entry.last_event_at,
                "last_codex_message": entry.last_event,
                "last_codex_event": entry.last_event,
                "runtime_seconds": runtime_seconds,
            }
            running.append(running_entry)

        # Build retry queue list with due_in_ms
        retrying = []
        for retry in self.state.retry_attempts.values():
            due_in_ms = max(0, retry.due_at_ms - now_ms)

            retry_entry = {
                "issue_id": retry.issue_id,
                "attempt": retry.attempt,
                "due_in_ms": due_in_ms,
                "identifier": retry.identifier,
                "error": retry.error,
                "worker_host": retry.worker_host,
                "workspace_path": retry.workspace_path,
            }
            retrying.append(retry_entry)

        # Build polling status
        polling = {
            "checking?": self._poll_check_in_progress,
            "next_poll_in_ms": self._compute_next_poll_in_ms(
                self._next_poll_due_at_ms, now_ms
            ),
            "poll_interval_ms": self.config.polling_interval_ms,
        }

        # Add migration status
        migration_status = self.tracker_facade.get_migration_status()

        return {
            "running": running,
            "retrying": retrying,
            "codex_totals": self.state.codex_totals,
            "rate_limits": self.state.rate_limits,
            "polling": polling,
            "migration": migration_status,
        }

    def _compute_runtime_seconds(self, started_at: str, now: dt.datetime) -> float:
        """
        Compute runtime seconds for a session.

        Args:
            started_at: Session start time (ISO 8601 string)
            now: Current time

        Returns:
            Runtime seconds as float
        """
        try:
            if isinstance(started_at, str):
                start_time = dt.datetime.fromisoformat(
                    started_at.replace("Z", "+00:00")
                ).replace(tzinfo=dt.timezone.utc)
                return (now - start_time).total_seconds()
        except (ValueError, TypeError):
            pass
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
