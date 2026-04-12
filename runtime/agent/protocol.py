"""JSON-RPC protocol client for Codex."""

import json
from typing import Dict, Any, Callable


class ProtocolClient:
    """JSON-RPC client for app-server."""
    
    def __init__(self, command: str, cwd: str):
        self._command = command
        self._cwd = cwd
        self._process = None
    
    def connect(self):
        """Connect to agent."""
        # TODO: Implement - see SPEC.md Section 10.1
        pass
    
    def initialize(self) -> Dict[str, Any]:
        """Send initialize request."""
        # TODO: Implement handshake - SPEC.md Section 10.2
        pass
    
    def start_thread(self) -> str:
        """Start thread, returns thread_id."""
        # TODO: Implement thread/start
        pass
    
    def start_turn(self, thread_id: str, prompt: str):
        """Start turn with prompt."""
        # TODO: Implement turn/start
        pass
    
    def read_events(self, callback: Callable):
        """Read events until completion."""
        # TODO: Implement - see SPEC.md Section 10.3
        pass
