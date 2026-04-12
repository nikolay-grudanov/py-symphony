"""Linear GraphQL tracker adapter.

DEPRECATED: This is a deprecated wrapper for backwards compatibility.
Use symphony-linear plugin instead: pip install symphony-linear

This module re-exports the built-in LinearTracker for backwards compatibility.
For new installations, use the symphony-linear plugin package.
"""

# Re-export for backwards compatibility
# The actual implementation is in this module (not a wrapper anymore)
from runtime.tracker.linear_internal import LinearTracker

# Re-export requests for backwards compatibility (tests mock this module)
from runtime.tracker import linear_internal

requests = linear_internal.requests

__all__ = ["LinearTracker", "requests"]
