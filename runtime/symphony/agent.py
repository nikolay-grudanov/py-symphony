"""Agent runner - orchestration layer.

Per SPEC.md Section 10, this module implements the orchestration logic
for running agent sessions, delegating protocol-specific details to the
backend implementation (Codex, ClaudeCode, etc.).
"""

import logging
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Callable
from contextlib import asynccontextmanager

from .config import Config
from .tracker import Issue
from .workspace import Workspace, WorkspaceManager
from .agent_backend import AgentBackend, TurnResult


logger = logging.getLogger(__name__)


@dataclass
class AgentEvent:
    """Agent lifecycle event emitted to orchestrator.

    Per SPEC.md Section 10.4, these events track session progress.
    """

    event: str
    timestamp: str
    issue_id: str
    issue_identifier: str
    session_id: Optional[str] = None
    message: Optional[str] = None
    usage: Optional[dict] = None  # token counts
    turn_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class RunAttempt:
    """One execution attempt for one issue.

    Tracks the status of a single run through the agent.
    """

    issue_id: str
    issue_identifier: str
    attempt: Optional[int]  # None for first run, >=1 for retries
    workspace_path: Path
    status: str  # preparing, running, succeeded, failed, timed_out, stalled, cancelled
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    session_id: Optional[str] = None
    turn_count: int = 0
    usage: dict = field(default_factory=dict)


class AgentRunner:
    """Orchestrates agent sessions with backend abstraction.

    Per TASK-003, this class delegates protocol-specific logic to the
    backend implementation while maintaining orchestration responsibilities:
    - Managing workspace lifecycle hooks
    - Tracking session state and turn count
    - Handling attempt completion and retry logic
    """

    def __init__(
        self,
        config: Config,
        workspace_manager: WorkspaceManager,
        backend: AgentBackend,
    ) -> None:
        """Initialize agent runner with backend.

        Args:
            config: Application configuration
            workspace_manager: Workspace manager for lifecycle hooks
            backend: Agent backend implementation (CodexBackend, etc.)
        """
        self.config = config
        self.workspace_manager = workspace_manager
        self.backend = backend

        # Orchestrator state only
        self._event_callback: Optional[Callable[[AgentEvent], None]] = None
        self._current_issue: Optional[Issue] = None
        self._turn_count: int = 0
        self._session_id: Optional[str] = None

    async def run(
        self,
        issue: Issue,
        workspace: Workspace,
        prompt: str,
        attempt: Optional[int] = None,
        event_callback: Optional[Callable[[AgentEvent], None]] = None,
    ) -> RunAttempt:
        """Run agent on an issue in the workspace.

        Per SPEC.md Section 10.7, the run process is:
        1. Run before_run hook
        2. Start backend process
        3. Session handshake
        4. Run turns until completion or max_turns
        5. Run after_run hook
        6. Stop backend

        Args:
            issue: The issue to work on
            workspace: The workspace for this issue
            prompt: The initial prompt for the agent
            attempt: Attempt number (None for first run, >=1 for retries)
            event_callback: Callback for lifecycle events

        Returns:
            RunAttempt with final status and results
        """
        self._event_callback = event_callback
        self._current_issue = issue
        self._turn_count = 0
        self._session_id = None

        attempt_obj = RunAttempt(
            issue_id=issue.id,
            issue_identifier=issue.identifier,
            attempt=attempt,
            workspace_path=workspace.path,
            status="preparing",
            started_at=datetime.utcnow().isoformat() + "Z",
        )

        # Step 1: Run before_run hook
        if not self.workspace_manager.run_before_run_hook(workspace.path):
            attempt_obj.status = "failed"
            attempt_obj.error = "before_run hook failed"
            return attempt_obj

        # Step 2: Start backend process
        try:
            await self.backend.start(workspace.path)
        except Exception as e:
            attempt_obj.status = "failed"
            attempt_obj.error = f"Failed to start agent: {e}"
            return attempt_obj

        # Step 3: Session handshake
        try:
            session_id = await self.backend.run_session(
                issue, prompt, event_callback=event_callback
            )
            self._session_id = session_id
            attempt_obj.session_id = session_id
            attempt_obj.status = "running"

            # Emit session_started event
            if event_callback:
                event_callback(
                    AgentEvent(
                        event="session_started",
                        timestamp=datetime.utcnow().isoformat() + "Z",
                        issue_id=issue.id,
                        issue_identifier=issue.identifier,
                        session_id=session_id,
                    )
                )
        except Exception as e:
            attempt_obj.status = "failed"
            attempt_obj.error = f"Session handshake failed: {e}"
            await self.backend.stop()
            return attempt_obj

        # Step 4: Run turns until completion, max turns, or error
        try:
            final_status = await self._run_turn_loop(
                prompt, workspace.path, issue, attempt_obj
            )
            attempt_obj.status = final_status
        except Exception as e:
            attempt_obj.status = "failed"
            attempt_obj.error = str(e)
            logger.exception("Error during turn loop")

        # Step 5: Run after_run hook
        self.workspace_manager.run_after_run_hook(workspace.path)

        # Step 6: Stop backend
        await self.backend.stop()

        # Finalize attempt
        attempt_obj.completed_at = datetime.utcnow().isoformat() + "Z"
        attempt_obj.turn_count = self._turn_count

        return attempt_obj

    @asynccontextmanager
    async def session(
        self,
        issue: Issue,
        workspace: Workspace,
        prompt: str,
        attempt: Optional[int] = None,
    ):
        """Context manager for running an agent session.

        Handles backend startup/shutdown and lifecycle hooks automatically.

        Usage:
            async with runner.session(issue, workspace, prompt) as attempt:
                # Session is running
                pass
            # Backend is stopped
        """
        attempt_obj = RunAttempt(
            issue_id=issue.id,
            issue_identifier=issue.identifier,
            attempt=attempt,
            workspace_path=workspace.path,
            status="preparing",
            started_at=datetime.utcnow().isoformat() + "Z",
        )

        self._current_issue = issue
        self._turn_count = 0
        self._event_callback = None

        # Run before_run hook
        if not self.workspace_manager.run_before_run_hook(workspace.path):
            attempt_obj.status = "failed"
            attempt_obj.error = "before_run hook failed"
            yield attempt_obj
            return

        # Start backend
        try:
            await self.backend.start(workspace.path)
        except Exception as e:
            attempt_obj.status = "failed"
            attempt_obj.error = f"Failed to start agent: {e}"
            yield attempt_obj
            return

        # Session handshake
        try:
            session_id = await self.backend.run_session(
                issue, prompt, event_callback=self._event_callback
            )
            self._session_id = session_id
            attempt_obj.session_id = session_id
            attempt_obj.status = "running"
        except Exception as e:
            attempt_obj.status = "failed"
            attempt_obj.error = f"Session handshake failed: {e}"
            await self.backend.stop()
            yield attempt_obj
            return

        try:
            yield attempt_obj
        finally:
            self.workspace_manager.run_after_run_hook(workspace.path)
            await self.backend.stop()
            attempt_obj.completed_at = datetime.utcnow().isoformat() + "Z"
            attempt_obj.turn_count = self._turn_count

    async def _run_turn_loop(
        self,
        base_prompt: str,
        workspace_path: Path,
        issue: Issue,
        attempt: RunAttempt,
    ) -> str:
        """Run turns until completion, max turns, or error.

        Per SPEC.md Section 10.3, we continue issuing turn requests
        until the session signals completion or we hit the limit.
        """
        while self._turn_count < self.config.agent_max_turns:
            # Build continuation prompt for subsequent turns
            if self._turn_count == 1:
                prompt = base_prompt
            else:
                prompt = self._build_continuation_prompt(
                    base_prompt, attempt.attempt, self._turn_count
                )

            # Run turn via backend
            turn_result = await self.backend.run_turn(
                prompt, event_callback=self._event_callback
            )

            # Interpret TurnResult
            if turn_result.status == "completed":
                self._turn_count += 1
                continue
            elif turn_result.status == "failed":
                attempt.error = turn_result.error or "Turn failed"
                return "failed"
            else:
                return turn_result.status

        # Reached max turns
        if attempt.status == "running":
            if self._turn_count >= self.config.agent_max_turns:
                attempt.error = f"Max turns ({self.config.agent_max_turns}) reached"
                return "failed"
            else:
                return "succeeded"

        return attempt.status

    def _build_initial_prompt(self, issue: Issue, template_prompt: str) -> str:
        """Build the initial prompt combining issue info with template.

        Per SPEC.md Section 7, the prompt includes issue identifier, title,
        description, and the workflow template content.
        """
        issue_context = f"""## Issue: {issue.identifier}

**Title:** {issue.title}

**Description:**
{issue.description or "(No description)"}

---

"""
        return issue_context + template_prompt

    def _build_continuation_prompt(
        self,
        base_prompt: str,
        attempt: Optional[int],
        turn_count: int,
    ) -> str:
        """Build prompt for continuation turns.

        Per SPEC.md Section 7.1, includes guidance to continue working.
        """
        continuation = f"""## Continuation (turn {turn_count})

Continue working on the previous task. The issue context remains the same.

"""

        if attempt is not None:
            continuation += f"(Retry attempt {attempt})\n\n"

        return continuation + base_prompt
