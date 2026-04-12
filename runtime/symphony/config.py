"""Configuration layer - typed getters for workflow config."""

import os
import os.path
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
from .workflow import Workflow


# Default values from SPEC.md
_DEFAULTS = {
    "tracker": {
        "kind": "linear",
        "endpoint": "https://api.linear.app/graphql",
        "active_states": ["Todo", "In Progress"],
        "terminal_states": ["Closed", "Cancelled", "Canceled", "Duplicate", "Done"],
    },
    "polling": {
        "interval_ms": 30000,
    },
    "workspace": {
        "root": None,  # Will use temp dir
    },
    "hooks": {
        "timeout_ms": 60000,
    },
    "agent": {
        "max_concurrent_agents": 10,
        "max_concurrent_agents_by_state": {},
        "max_retry_backoff_ms": 300000,
        "max_turns": 20,
    },
    "worker": {
        "ssh_hosts": [],
        "max_concurrent_agents_per_host": 3,
    },
    "codex": {
        "command": "codex app-server",
        "turn_timeout_ms": 3600000,
        "read_timeout_ms": 5000,
        "stall_timeout_ms": 300000,
    },
}


def _expand_path(value: Union[str, Path]) -> Path:
    """Expand ~ and environment variables in path."""
    if not isinstance(value, str):
        return value

    # Expand ~ to home directory
    if value.startswith("~"):
        value = os.path.expanduser(value)

    # Expand $VAR environment variables
    if "$" in value:
        value = os.path.expandvars(value)

    return Path(value)


def _resolve_env(value: Union[str, None]) -> Optional[str]:
    """Resolve $VAR_NAME to environment variable."""
    if isinstance(value, str) and value.startswith("$"):
        var_name = value[1:]
        env_value = os.environ.get(var_name, "")
        return env_value if env_value else None
    return value


@dataclass
class Config:
    """Typed configuration from workflow."""

    # Tracker
    tracker_kind: str
    tracker_endpoint: str
    tracker_api_key: Optional[str]
    tracker_project_slug: Optional[str]
    tracker_username: Optional[str]
    tracker_active_states: list[str]
    tracker_terminal_states: list[str]

    # Polling
    polling_interval_ms: int

    # Workspace
    workspace_root: Path

    # Hooks
    hooks_after_create: Optional[str]
    hooks_before_run: Optional[str]
    hooks_after_run: Optional[str]
    hooks_before_remove: Optional[str]
    hooks_timeout_ms: int

    # Agent
    agent_max_concurrent_agents: int
    agent_max_concurrent_agents_by_state: dict[str, int]
    agent_max_retry_backoff_ms: int
    agent_max_turns: int

    # Worker
    worker_ssh_hosts: list[str]
    worker_max_concurrent_agents_per_host: int

    # Codex
    codex_command: str
    codex_approval_policy: Optional[str]
    codex_thread_sandbox: Optional[str]
    codex_turn_sandbox_policy: Optional[dict]
    codex_turn_timeout_ms: int
    codex_read_timeout_ms: int
    codex_stall_timeout_ms: int

    # Server (optional)
    server_port: Optional[int] = None

    # Agent backend selection
    agent_backend: str = "codex"  # Default backend


def load_config(workflow: Workflow) -> Config:
    """Load typed config from workflow, applying defaults and env resolution."""
    cfg = workflow.config

    # Helper to get nested config with default
    def get(path: str, default=None):
        keys = path.split(".")
        val = cfg
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
        return val if val is not None else default

    # Helper to parse and validate per-state limits (SPEC.md Section 8.3)
    def parse_per_state_limits(limit_dict: dict) -> dict[str, int]:
        """Parse and validate per-state concurrency limits.

        Invalid entries (non-positive, non-numeric) are ignored.
        State keys are normalized to lowercase for consistent lookup.
        """
        if not isinstance(limit_dict, dict):
            return {}

        validated = {}
        for state_key, limit in limit_dict.items():
            # Validate limit is a positive integer
            if isinstance(limit, int) and limit > 0:
                # Normalize state key to lowercase
                normalized_key = str(state_key).lower()
                validated[normalized_key] = limit
        return validated

    # Tracker
    tracker_cfg = cfg.get("tracker", {})
    tracker_kind = get("tracker.kind", "linear")

    # Resolve API key based on tracker kind
    # Linear: LINEAR_API_KEY, Jira: JIRA_API_TOKEN
    if tracker_kind == "jira":
        api_key = _resolve_env(tracker_cfg.get("api_key")) or os.environ.get(
            "JIRA_API_TOKEN"
        )
    else:
        api_key = _resolve_env(tracker_cfg.get("api_key")) or os.environ.get(
            "LINEAR_API_KEY"
        )

    # Resolve username for Jira (optional, for basic auth)
    tracker_username = _resolve_env(tracker_cfg.get("username")) or os.environ.get(
        "JIRA_USERNAME"
    )

    # Workspace root
    workspace_root = get("workspace.root")
    if workspace_root:
        workspace_root = _expand_path(workspace_root)
    else:
        import tempfile

        workspace_root = Path(tempfile.gettempdir()) / "symphony_workspaces"

    # Parse per-state concurrency limits
    per_state_limits_raw = get("agent.max_concurrent_agents_by_state", {})
    per_state_limits = parse_per_state_limits(per_state_limits_raw)

    return Config(
        # Tracker
        tracker_kind=get("tracker.kind", "linear"),
        tracker_endpoint=get("tracker.endpoint", "https://api.linear.app/graphql"),
        tracker_api_key=api_key,
        tracker_project_slug=get("tracker.project_slug"),
        tracker_username=tracker_username,
        tracker_active_states=get("tracker.active_states", ["Todo", "In Progress"]),
        tracker_terminal_states=get(
            "tracker.terminal_states",
            ["Closed", "Cancelled", "Canceled", "Duplicate", "Done"],
        ),
        # Polling
        polling_interval_ms=get("polling.interval_ms", 30000),
        # Workspace
        workspace_root=workspace_root,
        # Hooks
        hooks_after_create=get("hooks.after_create"),
        hooks_before_run=get("hooks.before_run"),
        hooks_after_run=get("hooks.after_run"),
        hooks_before_remove=get("hooks.before_remove"),
        hooks_timeout_ms=get("hooks.timeout_ms", 60000),
        # Agent
        agent_max_concurrent_agents=get("agent.max_concurrent_agents", 10),
        agent_max_concurrent_agents_by_state=per_state_limits,
        agent_max_retry_backoff_ms=get("agent.max_retry_backoff_ms", 300000),
        agent_max_turns=get("agent.max_turns", 20),
        # Worker
        worker_ssh_hosts=get("worker.ssh_hosts", []),
        worker_max_concurrent_agents_per_host=get(
            "worker.max_concurrent_agents_per_host", 3
        ),
        # Codex
        codex_command=get("codex.command", "codex app-server"),
        codex_approval_policy=get("codex.approval_policy"),
        codex_thread_sandbox=get("codex.thread_sandbox"),
        codex_turn_sandbox_policy=get("codex.turn_sandbox_policy"),
        codex_turn_timeout_ms=get("codex.turn_timeout_ms", 3600000),
        codex_read_timeout_ms=get("codex.read_timeout_ms", 5000),
        codex_stall_timeout_ms=get("codex.stall_timeout_ms", 300000),
        # Server
        server_port=get("server.port"),
        # Agent backend
        agent_backend=get("agent_backend", "codex"),
    )
