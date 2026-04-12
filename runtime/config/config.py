"""Configuration layer - typed getters for workflow config."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ServiceConfig:
    """Service configuration."""
    
    poll_interval_ms: int = 30000
    workspace_root: str = "/tmp/symphony_workspaces"
    max_concurrent_agents: int = 10
    # TODO: Add all config fields from SPEC.md Section 6


class Config:
    """Configuration manager."""
    
    def __init__(self):
        self._config: Optional[ServiceConfig] = None
    
    def get_poll_interval_ms(self) -> int:
        """Get poll interval in milliseconds."""
        # TODO: Implement
        return 30000
    
    def get_workspace_root(self) -> str:
        """Get workspace root directory."""
        # TODO: Implement
        return "/tmp/symphony_workspaces"
    
    def get_max_concurrent_agents(self) -> int:
        """Get max concurrent agents."""
        # TODO: Implement
        return 10
