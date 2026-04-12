"""Orchestrator runtime state - in-memory state."""

from dataclasses import dataclass, field
from typing import Dict, Set, Any, Optional


@dataclass
class OrchestratorState:
    """Runtime state owned by orchestrator."""

    poll_interval_ms: int = 30000
    max_concurrent_agents: int = 10
    running: Dict[str, Any] = field(default_factory=dict)
    claimed: Set[str] = field(default_factory=set)
    retry_attempts: Dict[str, Any] = field(default_factory=dict)
    completed: Set[str] = field(default_factory=set)
    codex_totals: Dict[str, Any] = field(
        default_factory=lambda: {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "seconds_running": 0.0,
        }
    )
    codex_rate_limits: Optional[Dict[str, Any]] = None
