"""Tracker adapters."""

from .base import TrackerClient
from .registry import get_tracker_registry, register_tracker

# Factory and exceptions
from .factory import (
    TrackerFactory,
    # Factory errors
    TrackerFactoryError,
    TrackerNotRegisteredError,
    TrackerConfigError,
    # API errors
    TrackerAPIError,
    TrackerApiRequestError,
    TrackerApiStatusError,
    TrackerApiConflictError,
    TrackerApiResourceNotFoundError,
    TrackerApiTimeoutError,
    TrackerApiRateLimitError,
)

from .linear import LinearTracker
from .jira import JiraTracker

# Register built-in adapters
register_tracker("linear", LinearTracker)
register_tracker("jira", JiraTracker)

# Export core classes for external use
__all__ = [
    # Core classes
    "TrackerClient",
    "TrackerFactory",
    # Registry
    "get_tracker_registry",
    "register_tracker",
    # Trackers
    "LinearTracker",
    "JiraTracker",
    # Factory errors
    "TrackerFactoryError",
    "TrackerNotRegisteredError",
    "TrackerConfigError",
    # API errors
    "TrackerAPIError",
    "TrackerApiRequestError",
    "TrackerApiStatusError",
    "TrackerApiConflictError",
    "TrackerApiResourceNotFoundError",
    "TrackerApiTimeoutError",
    "TrackerApiRateLimitError",
]
