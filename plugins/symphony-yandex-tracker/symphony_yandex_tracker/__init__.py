"""Yandex Tracker adapter for Symphony orchestration platform."""

from symphony_yandex_tracker.adapter import YandexTrackerAdapter
from symphony_yandex_tracker.errors import (
    ConcurrencyError,
    ConfigurationError,
    ResourceNotFoundError,
    TokenExpiredError,
    TrackerApiError,
    TrackerError,
    TrackerTimeoutError,
    TransitionNotFoundError,
    ValidationError,
)
from symphony_yandex_tracker.http_client import TrackerHttpClient
from symphony_yandex_tracker.logger import get_logger
from symphony_yandex_tracker.models import ArrayFieldOperations, UpdateIssueRequest

# Alias for backward compatibility
HttpClient = TrackerHttpClient

__all__ = [
    "YandexTrackerAdapter",
    "TrackerError",
    "TrackerApiError",
    "TrackerTimeoutError",
    "TokenExpiredError",
    "ResourceNotFoundError",
    "TransitionNotFoundError",
    "ValidationError",
    "ConcurrencyError",
    "ConfigurationError",
    "UpdateIssueRequest",
    "ArrayFieldOperations",
    "get_logger",
    "HttpClient",
    "TrackerHttpClient",
]
