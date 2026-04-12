"""Agent runner - wraps workspace + prompt + subprocess."""

from .protocol import ProtocolClient
from pathlib import Path


class AgentRunner:
    """Runs coding agent for an issue."""
    
    def __init__(self, workspace_path: Path, prompt: str):
        self._workspace_path = workspace_path
        self._prompt = prompt
        self._client: ProtocolClient = None
    
    def run(self) -> Dict[str, Any]:
        """Run agent, returns result."""
        # TODO: Implement - see SPEC.md Section 10.7
        pass
    
    def stop(self):
        """Stop agent."""
        pass
