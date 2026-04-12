"""Token accounting and metrics."""

from dataclasses import dataclass


@dataclass
class TokenTotals:
    """Token usage totals."""
    
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    seconds_running: float = 0.0


class Metrics:
    """Metrics collector."""
    
    def __init__(self):
        self._totals = TokenTotals()
    
    def add_tokens(self, input_delta: int, output_delta: int):
        """Add token deltas."""
        # TODO: Implement accounting - SPEC.md Section 13.5
        pass
    
    def get_totals(self) -> TokenTotals:
        """Get current totals."""
        return self._totals
