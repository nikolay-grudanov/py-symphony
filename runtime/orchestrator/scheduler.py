"""Poll loop and scheduling."""

from .state import OrchestratorState


class Scheduler:
    """Scheduler for dispatching work."""
    
    def __init__(self, state: OrchestratorState):
        self._state = state
        self._running = False
    
    def start(self):
        """Start scheduler."""
        # TODO: Implement - see SPEC.md Section 8.1
        pass
    
    def stop(self):
        """Stop scheduler."""
        pass
    
    def tick(self):
        """Execute one poll tick."""
        # TODO: Validate → Fetch → Dispatch
        pass
