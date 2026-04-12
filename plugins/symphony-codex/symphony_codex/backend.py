"""Codex agent backend implementation.

This module implements the AgentBackend interface for Codex app-server,
using JSON-RPC protocol over stdio.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from runtime.symphony.agent_backend import AgentBackend, TurnResult
from runtime.symphony.agent import AgentEvent
from runtime.symphony.tracker import Issue
from runtime.symphony.config import Config


logger = logging.getLogger(__name__)

# Protocol constants from SPEC.md Section 10.2
PROTOCOL_VERSION = "1.0"


class ProtocolError(Exception):
    """Error during protocol communication."""

    pass


class ProtocolTimeout(ProtocolError):
    """Protocol operation timed out."""

    pass


class CodexBackend(AgentBackend):
    """Codex agent backend implementation.

    Implements the AgentBackend interface for Codex app-server,
    using JSON-RPC protocol over stdio.
    """

    def __init__(self, config: Config) -> None:
        """Initialize Codex backend with configuration.

        Args:
            config: Symphony configuration object with Codex-specific settings
        """
        self.config = config

        # Process state
        self._process: Optional[asyncio.subprocess.Process] = None
        self._stdin_writer: Optional[asyncio.StreamWriter] = None
        self._stdout_reader: Optional[asyncio.StreamReader] = None
        self._read_task: Optional[asyncio.Task] = None

        # Protocol state
        self._request_id: int = 0
        self._pending_requests: dict[int, asyncio.Future] = {}

        # Session state
        self._session_id: Optional[str] = None
        self._thread_id: Optional[str] = None
        self._turn_id: Optional[str] = None
        self._turn_count: int = 0

        # Issue context
        self._current_issue: Optional[Issue] = None

        # Event callback (NOT stored between calls)
        self._event_callback: Optional[Callable[[AgentEvent], None]] = None

        # State flags for turn loop control
        self._input_required: bool = False

        # Workspace path for current session
        self._workspace_path: Optional[Path] = None

    async def start(self, workspace_path: Path) -> None:
        """Запустить процесс/сессию агента.

        Args:
            workspace_path: Путь к workspace директории

        Raises:
            RuntimeError: Если процесс не может быть запущен
        """
        cmd = self.config.codex_command
        logger.info(f"Starting Codex: {cmd} in {workspace_path}")

        self._workspace_path = workspace_path
        self._process = await asyncio.create_subprocess_exec(
            "bash",
            "-lc",
            cmd,
            cwd=workspace_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self._stdin_writer = self._process.stdin
        self._stdout_reader = self._process.stdout

        # Start background task to read messages
        self._read_task = asyncio.create_task(self._read_messages())

    async def run_session(
        self,
        issue: Issue,
        prompt: str,
        event_callback: Optional[Callable[[AgentEvent], None]] = None,
    ) -> str:
        """Выполнить сессию, вернуть session_id.

        Per SPEC.md Section 10.2, performs the protocol handshake sequence:
        initialize -> initialized -> thread/start -> turn/start

        Args:
            issue: Объект Issue из трекера
            prompt: Initial prompt для сессии
            event_callback: Optional callback for events (NOT stored in backend)

        Returns:
            session_id: Уникальный идентификатор сессии

        Raises:
            ProtocolError: Если handshake не удался
        """
        # Временно сохранить callback для этого вызова
        self._event_callback = event_callback
        self._current_issue = issue
        self._turn_count = 0
        self._session_id = None

        if not self._workspace_path:
            raise ProtocolError("Backend not started - call start() first")

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
        logger.info(f"Codex server: {server_info.get('name')} {server_info.get('version')}")

        # Step 2: initialized notification (no response)
        await self._send_notification("initialized", {})

        # Step 3: thread/start
        thread_resp = await self._send_request(
            "thread/start",
            {
                "approvalPolicy": self.config.codex_approval_policy or "on-failure",
                "sandbox": self.config.codex_thread_sandbox or "workspace-write",
                "cwd": str(self._workspace_path.resolve()),
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
                        "text": self._build_initial_prompt(issue, prompt),
                    }
                ],
                "cwd": str(self._workspace_path.resolve()),
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

        return session_id

    async def run_turn(
        self, prompt: str, event_callback: Optional[Callable[[AgentEvent], None]] = None
    ) -> TurnResult:
        """Выполнить один turn, вернуть статус.

        Per SPEC.md Section 10.3, executes a single turn and waits
        for completion, returning TurnResult with status and usage metrics.

        Args:
            prompt: Prompt для этого turn
            event_callback: Optional callback for events (NOT stored in backend)

        Returns:
            TurnResult: Статус, usage и error (если есть)

        Raises:
            ProtocolError: Если запрос turn/start не удался
            TimeoutError: Если turn не завершился за отведённое время
        """
        # Временно сохранить callback для этого вызова
        self._event_callback = event_callback

        if not self._workspace_path or not self._thread_id or not self._current_issue:
            return TurnResult(
                status="failed",
                usage={},
                error="Session not initialized - call run_session() first",
            )

        # Start new turn
        turn_resp = await self._send_request(
            "turn/start",
            {
                "threadId": self._thread_id,
                "input": [{"type": "text", "text": prompt}],
                "cwd": str(self._workspace_path.resolve()),
                "title": f"{self._current_issue.identifier}: turn {self._turn_count + 1}",
                "approvalPolicy": self.config.codex_approval_policy or "on-failure",
                "sandboxPolicy": self.config.codex_turn_sandbox_policy,
            },
        )

        turn_data = turn_resp.get("result", {}).get("turn", {})
        self._turn_id = turn_data.get("id")
        self._turn_count += 1

        # Wait for turn completion (handled by message reader)
        completion_event = await self._wait_for_turn_completion()

        if completion_event:
            if completion_event.event == "turn_completed":
                return TurnResult(
                    status="completed", usage=completion_event.usage or {}, error=None
                )
            elif completion_event.event == "turn_failed":
                return TurnResult(
                    status="failed", usage={}, error=completion_event.error or "Turn failed"
                )
            elif completion_event.event == "turn_input_required":
                # Per SPEC.md Section 10.5: fail immediately on input required
                logger.error("User input required - failing run attempt")
                return TurnResult(status="failed", usage={}, error="User input required")

        return TurnResult(status="completed", usage={}, error=None)

    async def stop(self) -> None:
        """Остановить процесс.

        Gracefully shuts down the agent process and cleans up resources.
        Performs:
        - Cancels pending read tasks
        - Closes stdin writer
        - Terminates process with timeout
        - Falls back to kill if necessary
        """
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
                    self._process.wait(),
                    timeout=5,
                )
            except asyncio.TimeoutError:
                logger.warning("Codex process did not terminate, killing")
                self._process.kill()
                await self._process.wait()

            self._process = None

        self._stdout_reader = None
        self._workspace_path = None

    # === Private methods ===

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
                    if self._process and self._process.returncode is not None:
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
                    issue_identifier=self._current_issue.identifier if self._current_issue else "",
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
                    issue_identifier=self._current_issue.identifier if self._current_issue else "",
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
                    issue_identifier=self._current_issue.identifier if self._current_issue else "",
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

        logger.warning(f"User input requested: type={input_type}, prompt={input_prompt[:100]}...")

        # Emit error event via callback
        if self._event_callback:
            self._event_callback(
                AgentEvent(
                    event="turn_input_required",
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    issue_id=self._current_issue.id if self._current_issue else "",
                    issue_identifier=self._current_issue.identifier if self._current_issue else "",
                    session_id=self._session_id,
                    turn_id=self._turn_id,
                    error=f"User input required: {input_type}",
                )
            )

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
        response_future: asyncio.Future = asyncio.get_event_loop().create_future()
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

    # === Helper methods ===

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
                    logger.warning("User input required during turn, failing immediately")
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
