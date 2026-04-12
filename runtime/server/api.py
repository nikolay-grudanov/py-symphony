"""HTTP API server."""

import time
from datetime import datetime

from aiohttp import web


class APIServer:
    """REST API server."""

    def __init__(self, orchestrator):
        self._app = web.Application()
        self._setup_routes()
        self._orchestrator = orchestrator
        self._runner = None

    def _setup_routes(self):
        """Setup API routes."""
        self._app.router.add_get("/api/v1/state", self.get_state)
        self._app.router.add_get("/api/v1/{issue_identifier}", self.get_issue)
        self._app.router.add_post("/api/v1/refresh", self.post_refresh)

    async def get_state(self, request):
        """GET /api/v1/state - Return runtime state snapshot."""
        snapshot = self._orchestrator.get_state_snapshot()
        return web.json_response(snapshot)

    async def get_issue(self, request):
        """GET /api/v1/<issue_identifier> - Return issue-specific runtime details."""
        issue_identifier = request.match_info["issue_identifier"]

        # Check running issues
        for issue_id, metadata in self._orchestrator.state.running.items():
            if metadata.get("identifier") == issue_identifier:
                return web.json_response(
                    self._build_issue_response(
                        issue_identifier, issue_id, metadata, "running"
                    )
                )

        # Check retry attempts
        for issue_id, retry_entry in self._orchestrator.state.retry_attempts.items():
            if retry_entry.get("identifier") == issue_identifier:
                return web.json_response(
                    self._build_issue_response(
                        issue_identifier, issue_id, retry_entry, "retry"
                    )
                )

        # Check claimed issues
        if issue_identifier in self._orchestrator.state.claimed:
            return web.json_response(
                self._build_issue_response(
                    issue_identifier,
                    issue_identifier,
                    {"identifier": issue_identifier},
                    "claimed",
                )
            )

        # Check completed issues
        if issue_identifier in self._orchestrator.state.completed:
            return web.json_response(
                self._build_issue_response(
                    issue_identifier,
                    issue_identifier,
                    {"identifier": issue_identifier},
                    "completed",
                )
            )

        # Not found
        return web.json_response(
            {
                "error": {
                    "code": "issue_not_found",
                    "message": f"Issue '{issue_identifier}' not found",
                }
            },
            status=404,
        )

    def _build_issue_response(
        self, identifier: str, issue_id: str, metadata: dict, status: str
    ):
        """Build issue-specific response."""
        now = datetime.utcnow()

        # Get workspace path
        workspace_path = metadata.get("workspace_path", "")
        workspace = {"path": workspace_path} if workspace_path else {}

        # Get attempts info
        attempts = {"restart_count": 0, "current_retry_attempt": 0}
        if status == "running":
            attempts["restart_count"] = metadata.get("restart_count", 0)
        elif status == "retry":
            attempts["current_retry_attempt"] = metadata.get("attempt", 0)

        # Get running details if applicable
        running = {}
        if status == "running":
            running = {
                "worker_host": metadata.get("worker_host"),
                "session_id": metadata.get("session_id"),
                "codex_app_server_pid": metadata.get("codex_app_server_pid"),
                "turn_count": metadata.get("turn_count", 0),
                "started_at": metadata.get("started_at"),
                "last_codex_timestamp": metadata.get("last_codex_timestamp"),
            }

        # Get retry details if applicable
        retry = None
        if status == "retry":
            due_at_ms = metadata.get("due_at_ms")
            now_ms = int(time.time() * 1000)
            retry = {
                "attempt": metadata.get("attempt"),
                "due_in_ms": max(0, due_at_ms - now_ms) if due_at_ms else None,
                "error": metadata.get("error"),
            }

        # Get last error
        last_error = metadata.get("error")

        return {
            "issue_identifier": identifier,
            "issue_id": issue_id,
            "status": status,
            "workspace": workspace,
            "attempts": attempts,
            "running": running,
            "retry": retry,
            "logs": {},
            "recent_events": [],
            "last_error": last_error,
            "tracked": {},
        }

    async def post_refresh(self, request):
        """POST /api/v1/refresh - Queue immediate tracker poll + reconciliation."""
        now = datetime.utcnow()

        # For now, just record the request (scheduler not fully implemented)
        # In full implementation, this would trigger immediate poll + reconcile

        return web.json_response(
            {
                "queued": True,
                "coalesced": False,
                "requested_at": now.isoformat() + "Z",
                "operations": ["poll", "reconcile"],
            }
        )

    async def start(self, host: str, port: int):
        """Start server."""
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()

        site = web.TCPSite(self._runner, host, port)
        await site.start()

        return (host, port)
