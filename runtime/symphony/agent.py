"""Agent runner - Codex app-server integration.

Per SPEC.md Section 10, this module implements the protocol for communicating
with Codex app-server over stdio using JSON-RPC-like messages.
"""

import asyncio
import json
import logging
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Callable, Awaitable
from contextlib import asynccontextmanager

from .config import Config
from .tracker import Issue
from .workspace import Workspace, WorkspaceManager


logger = logging.getLogger(__name__)


# Protocol constants from SPEC.md Section 10.2
PROTOCOL_VERSION = "1.0"


class ProtocolError(Exception):
    """Error during protocol communication."""

    pass


class ProtocolTimeout(ProtocolError):
    """Protocol operation timed out."""

    pass


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
    """Runs Codex app-server for an issue in a workspace.

    Implements the JSON-RPC-like protocol over stdio as described in
    SPEC.md Section 10.
    """

    def __init__(self, config: Config, workspace_manager: WorkspaceManager):
        """Initialize agent runner.

        Args:
            config: Application configuration
            workspace_manager: Workspace manager for lifecycle hooks
        """
        self.config = config
        self.workspace_manager = workspace_manager

        # Process state
        self._process: Optional[subprocess.Popen] = None
        self._stdin_writer: Optional[asyncio.StreamWriter] = None
        self._stdout_reader: Optional[asyncio.StreamReader] = None
        self._read_task: Optional[asyncio.Task] = None

        # Protocol state
        self._request_id: int = 0
        self._pending_requests: dict[int, asyncio.Future] = {}
        self._message_handler: Optional[Callable[[dict], None]] = None
        self._event_callback: Optional[Callable[[AgentEvent], None]] = None

        # Session state
        self._session_id: Optional[str] = None
        self._thread_id: Optional[str] = None
        self._turn_id: Optional[str] = None
        self._turn_count: int = 0

        # Issue context
        self._current_issue: Optional[Issue] = None

        # State flags for turn loop control
        self._input_required: bool = False

    async def run(
        self,
        issue: Issue,
        workspace: Workspace,
        prompt: str,
        attempt: Optional[int] = None,
        event_callback: Optional[Callable[[AgentEvent], None]] = None,
    ) -> RunAttempt:
        """Run Codex on an issue in the workspace.

        Per SPEC.md Section 10.7, the run process is:
        1. Create/reuse workspace (already done by WorkspaceManager)
        2. Build prompt from workflow template
        3. Start app-server session
        4. Forward app-server events to orchestrator via callback
        5. On any error, fail the worker attempt

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
        self._input_required = False

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

        # Step 2: Start app-server process
        try:
            await self._start_process(workspace.path)
        except Exception as e:
            attempt_obj.status = "failed"
            attempt_obj.error = f"Failed to start Codex: {e}"
            return attempt_obj

        # Step 3: Session handshake (initialize -> initialized -> thread/start)
        try:
            session_id = await self._session_handshake(issue, workspace.path, prompt)
            self._session_id = session_id
            attempt_obj.session_id = session_id
            attempt_obj.status = "running"

            # Emit session_started event
            if self._event_callback:
                self._event_callback(
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
            await self._stop_process()
            return attempt_obj

        # Step 4: Run turns until completion or max_turns
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

        # Step 6: Stop app-server
        await self._stop_process()

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

        Handles process startup/shutdown automatically.

        Usage:
            async with runner.session(issue, workspace, prompt) as attempt:
                # Session is running
                pass
            # Process is stopped
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

        # Start process
        try:
            await self._start_process(workspace.path)
        except Exception as e:
            attempt_obj.status = "failed"
            attempt_obj.error = f"Failed to start Codex: {e}"
            yield attempt_obj
            return

        # Session handshake
        try:
            session_id = await self._session_handshake(issue, workspace.path, prompt)
            self._session_id = session_id
            attempt_obj.session_id = session_id
            attempt_obj.status = "running"
        except Exception as e:
            attempt_obj.status = "failed"
            attempt_obj.error = f"Session handshake failed: {e}"
            await self._stop_process()
            yield attempt_obj
            return

        try:
            yield attempt_obj
        finally:
            self.workspace_manager.run_after_run_hook(workspace.path)
            await self._stop_process()
            attempt_obj.completed_at = datetime.utcnow().isoformat() + "Z"
            attempt_obj.turn_count = self._turn_count

    async def _start_process(self, workspace_path: Path) -> None:
        """Start Codex app-server process.

        Per SPEC.md Section 10.1, we launch via 'bash -lc' in the workspace directory.
        """
        cmd = self.config.codex_command
        logger.info(f"Starting Codex: {cmd} in {workspace_path}")

        self._process = subprocess.Popen(
            ["bash", "-lc", cmd],
            cwd=workspace_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        # Create async streams from the pipes
        loop = asyncio.get_event_loop()

        # stdin as async writer
        self._stdin_writer = asyncio.StreamWriter(
            self._process.stdin,
            protocol=asyncio.streams.FlowControlMixin,
            loop=loop,
        )

        # stdout as async reader
        self._stdout_reader = asyncio.StreamReader(loop=loop)
        protocol = asyncio.StreamReaderProtocol(self._stdout_reader, loop=loop)
        transport, _ = loop.run_until_complete(
            loop.connect_read_pipe(lambda: protocol, self._process.stdout)
        )

        # Start background task to read messages
        self._read_task = asyncio.create_task(self._read_messages())

    async def _stop_process(self) -> None:
        """Stop Codex app-server process gracefully."""
        logger.info("Stopping Codex process")

        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
            self._read_task = None

        if self._stdin_writer:
            self._stdin_writer.close()
            self._stdin_writer = None

        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, self._process.wait),
                    timeout=5,
                )
            except asyncio.TimeoutError:
                logger.warning("Codex process did not terminate, killing")
                self._process.kill()
                self._process.wait()

            self._process = None

        self._stdout_reader = None

    async def _session_handshake(
        self, issue: Issue, workspace_path: Path, initial_prompt: str
    ) -> str:
        """Perform session handshake per SPEC.md Section 10.2.

        Sequence:
        1. initialize request (with client info)
        2. initialized notification (no response)
        3. thread/start request (creates thread)
        4. turn/start request (first turn with issue)
        """
        # Step 1: initialize
        resp = await self._send_request(
            "initialize",
            {
                "clientInfo": {"name": "symphony", "version": "1.0.0"},
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {
                    "tools": True,
                    "streaming": True,
                },
            },
        )

        result = resp.get("result", {})
        server_info = result.get("serverInfo", {})
        logger.info(
            f"Codex server: {server_info.get('name')} {server_info.get('version')}"
        )

        # Step 2: initialized notification (no response)
        await self._send_notification("initialized", {})

        # Step 3: thread/start
        thread_resp = await self._send_request(
            "thread/start",
            {
                "approvalPolicy": self.config.codex_approval_policy or "on-failure",
                "sandbox": self.config.codex_thread_sandbox or "workspace-write",
                "cwd": str(workspace_path.resolve()),
            },
        )

        thread_data = thread_resp.get("result", {}).get("thread", {})
        self._thread_id = thread_data.get("id")
        logger.info(f"Thread started: {self._thread_id}")

        # Step 4: turn/start (first turn with issue info)
        turn_resp = await self._send_request(
            "turn/start",
            {
                "threadId": self._thread_id,
                "input": [
                    {
                        "type": "text",
                        "text": self._build_initial_prompt(issue, initial_prompt),
                    }
                ],
                "cwd": str(workspace_path.resolve()),
                "title": f"{issue.identifier}: {issue.title}",
                "approvalPolicy": self.config.codex_approval_policy or "on-failure",
                "sandboxPolicy": self.config.codex_turn_sandbox_policy,
            },
        )

        turn_data = turn_resp.get("result", {}).get("turn", {})
        self._turn_id = turn_data.get("id")
        self._turn_count = 1

        session_id = f"{self._thread_id}/{self._turn_id}"
        logger.info(f"First turn started: {session_id}")

        return session_id

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

    async def _run_turn_loop(
        self,
        base_prompt: str,
        workspace_path: Path,
        issue: Issue,
        attempt: RunAttempt,
    ) -> str:
        """Run turns until completion, max turns, or error.

        Per SPEC.md Section 10.3, we continue issuing turn/start requests
        until the session signals completion or we hit the limit.
        """
        while self._turn_count < self.config.agent_max_turns:
            # Check if we need to continue (issue still active)
            # For now, always continue until max turns or explicit completion

            # Build continuation prompt for subsequent turns
            if self._turn_count == 1:
                prompt = base_prompt
            else:
                prompt = self._build_continuation_prompt(
                    base_prompt, attempt.attempt, self._turn_count
                )

            # Run the turn
            turn_result = await self._run_turn(
                prompt,
                workspace_path,
                issue,
            )

            if turn_result == "completed":
                # Session indicates work is done
                self._turn_count += 1
                continue
            elif turn_result == "failed":
                attempt.error = "Turn failed"
                return "failed"
            else:
                # Other status (cancelled, timeout, stalled)
                return turn_result

        # Reached max turns
        if attempt.status == "running":
            if self._turn_count >= self.config.agent_max_turns:
                attempt.error = f"Max turns ({self.config.agent_max_turns}) reached"
                return "failed"
            else:
                return "succeeded"

        return attempt.status

    async def _run_turn(
        self,
        prompt: str,
        workspace_path: Path,
        issue: Issue,
    ) -> str:
        """Run a single turn and wait for completion.

        Sends turn/start request and processes events until completion
        or error.
        """
        # Start new turn
        turn_resp = await self._send_request(
            "turn/start",
            {
                "threadId": self._thread_id,
                "input": [{"type": "text", "text": prompt}],
                "cwd": str(workspace_path.resolve()),
                "title": f"{issue.identifier}: turn {self._turn_count + 1}",
                "approvalPolicy": self.config.codex_approval_policy or "on-failure",
                "sandboxPolicy": self.config.codex_turn_sandbox_policy,
            },
        )

        turn_data = turn_resp.get("result", {}).get("turn", {})
        self._turn_id = turn_data.get("id")

        # Wait for turn completion (handled by message reader)
        # We track completion via the event callback mechanism
        completion_event = await self._wait_for_turn_completion()

        if completion_event:
            if completion_event.event == "turn_completed":
                return "completed"
            elif completion_event.event == "turn_failed":
                return "failed"
            elif completion_event.event == "turn_input_required":
                # Per SPEC.md Section 10.5: fail immediately on input required
                logger.error("User input required - failing run attempt")
                return "failed"

        return "completed"

    async def _wait_for_turn_completion(self) -> Optional[AgentEvent]:
        """Wait for turn completion event.

        Uses a future that gets set when we receive turn/completed
        or turn/failed message. Also checks for input_required flag.
        """
        loop = asyncio.get_event_loop()
        completion_future: asyncio.Future = loop.create_future()

        def completion_handler(event: AgentEvent):
            if not completion_future.done():
                completion_future.set_result(event)

        # Register temporary handler
        old_callback = self._event_callback
        self._event_callback = completion_handler

        try:
            # Wait for completion with timeout
            # Also periodically check for input_required flag
            timeout_secs = self.config.codex_turn_timeout_ms / 1000

            while not completion_future.done():
                # Check if input required was triggered
                if self._input_required:
                    logger.warning(
                        "User input required during turn, failing immediately"
                    )
                    return AgentEvent(
                        event="turn_input_required",
                        timestamp=datetime.utcnow().isoformat() + "Z",
                        issue_id=self._current_issue.id if self._current_issue else "",
                        issue_identifier=self._current_issue.identifier
                        if self._current_issue
                        else "",
                        session_id=self._session_id,
                        turn_id=self._turn_id,
                        error="User input required",
                    )

                # Wait with short interval for responsive check
                result = await asyncio.wait_for(
                    completion_future,
                    timeout=min(1.0, timeout_secs),  # Check every second
                )
                return result

            return await completion_future
        except asyncio.TimeoutError:
            logger.warning("Turn completion timeout")
            return None
        finally:
            self._event_callback = old_callback
            # Reset input_required flag after wait
            self._input_required = False

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

    # Protocol methods

    async def _send_request(self, method: str, params: dict) -> dict:
        """Send JSON-RPC request and wait for response.

        Per SPEC.md Section 10.2, we use request/response pattern
        with numeric IDs for correlation.
        """
        if not self._stdin_writer:
            raise ProtocolError("Process not started")

        request_id = self._request_id
        self._request_id += 1

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        logger.debug(f">>> {json.dumps(request)}")

        # Write request
        self._stdin_writer.write(json.dumps(request).encode() + b"\n")
        await self._stdin_writer.drain()

        # Create future for response
        loop = asyncio.get_event_loop()
        response_future: asyncio.Future = loop.create_future()
        self._pending_requests[request_id] = response_future

        try:
            # Wait for response with timeout
            response = await asyncio.wait_for(
                response_future,
                timeout=self.config.codex_turn_timeout_ms / 1000,
            )

            # Handle error responses
            if "error" in response:
                raise ProtocolError(f"Request {method} failed: {response['error']}")

            return response

        except asyncio.TimeoutError:
            raise ProtocolTimeout(f"Request {method} timed out")
        finally:
            self._pending_requests.pop(request_id, None)

    async def _send_notification(self, method: str, params: dict) -> None:
        """Send JSON-RPC notification (no response expected)."""
        if not self._stdin_writer:
            raise ProtocolError("Process not started")

        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        logger.debug(f">>> (notification) {json.dumps(notification)}")

        self._stdin_writer.write(json.dumps(notification).encode() + b"\n")
        await self._stdin_writer.drain()

    async def _read_messages(self) -> None:
        """Read and process protocol messages from stdout.

        Per SPEC.md Section 10.4, handles:
        - Response to requests (matching by ID)
        - Notifications (turn/completed, turn/failed, etc.)
        """
        if not self._stdout_reader:
            return

        buffer = b""

        try:
            while True:
                try:
                    line = await asyncio.wait_for(
                        self._stdout_reader.readline(),
                        timeout=self.config.codex_read_timeout_ms / 1000,
                    )
                except asyncio.TimeoutError:
                    # Check if process is still alive
                    if self._process and self._process.poll() is not None:
                        logger.warning("Codex process exited")
                        break
                    continue

                if not line:
                    # EOF
                    break

                buffer += line
                if line.strip() == b"":
                    continue

                try:
                    msg = json.loads(buffer.decode("utf-8"))
                    buffer = b""
                    self._handle_message(msg)
                except json.JSONDecodeError:
                    # Incomplete JSON, continue buffering
                    continue

        except asyncio.CancelledError:
            logger.debug("Message reader cancelled")
        except Exception as e:
            logger.error(f"Error reading messages: {e}")

    def _handle_message(self, msg: dict) -> None:
        """Handle incoming protocol message.

        Per SPEC.md Section 10.4:
        - Response: has "id" field, matches to pending request
        - Notification: no "id" field, handle based on method
        """
        logger.debug(f"<<< {json.dumps(msg)}")

        # Check if it's a response
        msg_id = msg.get("id")
        if msg_id is not None:
            # It's a response to a previous request
            future = self._pending_requests.get(msg_id)
            if future and not future.done():
                future.set_result(msg)
            return

        # It's a notification
        method = msg.get("method", "")
        params = msg.get("params", {})

        if method == "turn/completed":
            self._handle_turn_completed(params)
        elif method == "turn/failed":
            self._handle_turn_failed(params)
        elif method == "turn/cancelled":
            self._handle_turn_cancelled(params)
        elif method == "tool/useStarted":
            self._handle_tool_started(params)
        elif method == "tool/useCompleted":
            self._handle_tool_completed(params)
        elif method == "tool/useFailed":
            self._handle_tool_failed(params)
        elif method == "message":
            self._handle_message_event(params)
        elif method == "error":
            logger.error(f"Protocol error from Codex: {params}")
        elif method in (
            "turn/inputRequired",
            "item/tool/requestUserInput",
            "input_required",
        ):
            self._handle_input_required(params)

    def _handle_turn_completed(self, params: dict) -> None:
        """Handle turn/completed notification."""
        usage = params.get("usage", {})
        message = params.get("message", "")

        if self._event_callback:
            self._event_callback(
                AgentEvent(
                    event="turn_completed",
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    issue_id=self._current_issue.id if self._current_issue else "",
                    issue_identifier=self._current_issue.identifier
                    if self._current_issue
                    else "",
                    session_id=self._session_id,
                    turn_id=self._turn_id,
                    usage=usage,
                    message=message,
                )
            )

        logger.info(f"Turn completed: {self._turn_id}, usage: {usage}")

    def _handle_turn_failed(self, params: dict) -> None:
        """Handle turn/failed notification."""
        error = params.get("error", "Unknown error")

        if self._event_callback:
            self._event_callback(
                AgentEvent(
                    event="turn_failed",
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    issue_id=self._current_issue.id if self._current_issue else "",
                    issue_identifier=self._current_issue.identifier
                    if self._current_issue
                    else "",
                    session_id=self._session_id,
                    turn_id=self._turn_id,
                    error=error,
                )
            )

        logger.error(f"Turn failed: {self._turn_id}, error: {error}")

    def _handle_turn_cancelled(self, params: dict) -> None:
        """Handle turn/cancelled notification."""
        reason = params.get("reason", "")

        if self._event_callback:
            self._event_callback(
                AgentEvent(
                    event="turn_cancelled",
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    issue_id=self._current_issue.id if self._current_issue else "",
                    issue_identifier=self._current_issue.identifier
                    if self._current_issue
                    else "",
                    session_id=self._session_id,
                    turn_id=self._turn_id,
                    message=reason,
                )
            )

        logger.warning(f"Turn cancelled: {self._turn_id}, reason: {reason}")

    def _handle_tool_started(self, params: dict) -> None:
        """Handle tool/useStarted notification."""
        tool_name = params.get("tool", "unknown")
        logger.debug(f"Tool started: {tool_name}")

    def _handle_tool_completed(self, params: dict) -> None:
        """Handle tool/useCompleted notification."""
        tool_name = params.get("tool", "unknown")
        logger.debug(f"Tool completed: {tool_name}")

    def _handle_tool_failed(self, params: dict) -> None:
        """Handle tool/useFailed notification."""
        tool_name = params.get("tool", "unknown")
        error = params.get("error", "Unknown error")
        logger.warning(f"Tool failed: {tool_name}, error: {error}")

    def _handle_message_event(self, params: dict) -> None:
        """Handle message notification (streaming output)."""
        content = params.get("content", "")
        message_type = params.get("type", "text")

        logger.debug(f"Message ({message_type}): {content[:100]}...")

    def _handle_input_required(self, params: dict) -> None:
        """Handle user input request notification.

        Per SPEC.md Section 10.5, if the agent requests user input,
        we must fail the run attempt immediately.
        """
        # Set flag to signal input required
        self._input_required = True

        # Extract input details for logging
        input_type = params.get("type", "unknown")
        input_prompt = params.get("prompt", params.get("message", ""))

        logger.warning(
            f"User input requested: type={input_type}, prompt={input_prompt[:100]}..."
        )

        # Emit error event via callback
        if self._event_callback:
            self._event_callback(
                AgentEvent(
                    event="turn_input_required",
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    issue_id=self._current_issue.id if self._current_issue else "",
                    issue_identifier=self._current_issue.identifier
                    if self._current_issue
                    else "",
                    session_id=self._session_id,
                    turn_id=self._turn_id,
                    error=f"User input required: {input_type}",
                )
            )
