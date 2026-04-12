"""File watcher for dynamic reload."""

import time
from pathlib import Path


class WorkflowWatcher:
    """Watches WORKFLOW.md for changes."""
    
    def __init__(self, path: str, callback):
        self._path = Path(path)
        self._callback = callback
        self._last_mtime: float = 0
    
    def start(self):
        """Start watching."""
        # TODO: Implement - see SPEC.md Section 6.2
        pass
    
    def stop(self):
        """Stop watching."""
        pass
