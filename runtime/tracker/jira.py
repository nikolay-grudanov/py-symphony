"""Jira REST API tracker adapter.

DEPRECATED: This is a deprecated wrapper for backwards compatibility.
Use symphony-jira plugin instead: pip install symphony-jira

This module re-exports the built-in JiraTracker for backwards compatibility.
For new installations, use the symphony-jira plugin package.
"""

# Re-export for backwards compatibility
# The actual implementation is in this module (not a wrapper anymore)
from runtime.tracker.jira_internal import JiraTracker

# Re-export requests for backwards compatibility (tests mock this module)
from runtime.tracker import jira_internal

requests = jira_internal.requests

__all__ = ["JiraTracker", "requests"]
