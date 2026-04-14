"""Error classes for Yandex Tracker adapter.

This module defines the error class hierarchy for the Yandex Tracker adapter.
All errors inherit from the base TrackerError class.

Classes:
    TrackerError: Base exception for all tracker-related errors.
    TrackerApiError: API request/response errors.
    TimeoutError: Request timeout errors.
    TokenExpiredError: Authentication token expiration errors.
    ResourceNotFoundError: Resource not found errors.
    TransitionNotFoundError: Status transition not found errors.
    ValidationError: Data validation errors.
    ConcurrencyError: Optimistic locking/concurrency errors.
    ConfigurationError: Configuration/initialization errors.
"""

from typing import Any


class TrackerError(Exception):
    """Base exception for all tracker-related errors.

    This is the root class for all exceptions raised by the Yandex Tracker adapter.
    All other error classes inherit from this base class.

    Attributes:
        message: Human-readable error message.
        details: Additional error context (optional).
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize TrackerError.

        Args:
            message: Human-readable error message.
            details: Additional error context dictionary.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        """Return string representation of the error."""
        return f"{self.__class__.__name__}(message={self.message!r}, details={self.details!r})"


class TrackerApiError(TrackerError):
    """API request or response error.

    Raised when the Yandex Tracker API returns an error response or when
    a network/protocol error occurs during API communication.

    Attributes:
        status_code: HTTP status code (if available).
        response_body: Raw API response body (if available).
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize TrackerApiError.

        Args:
            message: Human-readable error message.
            status_code: HTTP status code from API response.
            response_body: Raw API response body.
            details: Additional error context dictionary.
        """
        super().__init__(message, details)
        self.status_code = status_code
        self.response_body = response_body

    def __repr__(self) -> str:
        """Return string representation of the error."""
        return (
            f"TrackerApiError(message={self.message!r}, "
            f"status_code={self.status_code!r}, response_body={self.response_body!r})"
        )


class TimeoutError(TrackerError):
    """Request timeout error.

    Raised when a request to the Yandex Tracker API exceeds the configured
    timeout threshold.

    Attributes:
        timeout: Timeout value in seconds.
        url: Request URL that timed out.
    """

    def __init__(
        self,
        message: str,
        timeout: float | None = None,
        url: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize TimeoutError.

        Args:
            message: Human-readable error message.
            timeout: Configured timeout value in seconds.
            url: Request URL that timed out.
            details: Additional error context dictionary.
        """
        super().__init__(message, details)
        self.timeout = timeout
        self.url = url

    def __repr__(self) -> str:
        """Return string representation of the error."""
        return f"TimeoutError(message={self.message!r}, timeout={self.timeout!r}, url={self.url!r})"


class TokenExpiredError(TrackerError):
    """Authentication token expiration error.

    Raised when the OAuth or IAM token has expired and needs to be refreshed.
    The adapter should typically trigger re-authentication when this error occurs.

    Attributes:
        token_type: Type of token that expired ('oauth' or 'iam').
    """

    def __init__(
        self,
        message: str,
        token_type: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize TokenExpiredError.

        Args:
            message: Human-readable error message.
            token_type: Type of token that expired ('oauth' or 'iam').
            details: Additional error context dictionary.
        """
        super().__init__(message, details)
        self.token_type = token_type

    def __repr__(self) -> str:
        """Return string representation of the error."""
        return f"TokenExpiredError(message={self.message!r}, token_type={self.token_type!r})"


class ResourceNotFoundError(TrackerError):
    """Resource not found error.

    Raised when the requested resource (issue, queue, user) does not exist
    in Yandex Tracker.

    Attributes:
        resource_type: Type of resource (e.g., 'issue', 'queue', 'user').
        resource_id: ID or key of the resource that was not found.
    """

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ResourceNotFoundError.

        Args:
            message: Human-readable error message.
            resource_type: Type of resource that was not found.
            resource_id: ID or key of the resource.
            details: Additional error context dictionary.
        """
        super().__init__(message, details)
        self.resource_type = resource_type
        self.resource_id = resource_id

    def __repr__(self) -> str:
        """Return string representation of the error."""
        return (
            f"ResourceNotFoundError(message={self.message!r}, "
            f"resource_type={self.resource_type!r}, resource_id={self.resource_id!r})"
        )


class TransitionNotFoundError(TrackerError):
    """Status transition not found error.

    Raised when a requested status transition is not available for an issue.
    This typically occurs when the workflow doesn't allow the requested transition.

    Attributes:
        issue_key: Key of the issue.
        target_status: Target status that was requested.
        available_transitions: List of available transition names.
    """

    def __init__(
        self,
        message: str,
        issue_key: str | None = None,
        target_status: str | None = None,
        available_transitions: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize TransitionNotFoundError.

        Args:
            message: Human-readable error message.
            issue_key: Key of the issue.
            target_status: Target status name that was requested.
            available_transitions: List of available transition names.
            details: Additional error context dictionary.
        """
        super().__init__(message, details)
        self.issue_key = issue_key
        self.target_status = target_status
        self.available_transitions = available_transitions or []

    def __repr__(self) -> str:
        """Return string representation of the error."""
        return (
            f"TransitionNotFoundError(message={self.message!r}, "
            f"issue_key={self.issue_key!r}, target_status={self.target_status!r})"
        )


class ValidationError(TrackerError):
    """Data validation error.

    Raised when request data fails validation before being sent to the API.

    Attributes:
        field: Name of the field that failed validation.
        value: Value that failed validation.
        constraint: Validation constraint that was violated.
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        constraint: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ValidationError.

        Args:
            message: Human-readable error message.
            field: Name of the field that failed validation.
            value: Value that failed validation.
            constraint: Description of the violated constraint.
            details: Additional error context dictionary.
        """
        super().__init__(message, details)
        self.field = field
        self.value = value
        self.constraint = constraint

    def __repr__(self) -> str:
        """Return string representation of the error."""
        return (
            f"ValidationError(message={self.message!r}, field={self.field!r}, "
            f"value={self.value!r}, constraint={self.constraint!r})"
        )


class ConcurrencyError(TrackerError):
    """Optimistic locking/concurrency error.

    Raised when a concurrent modification conflict is detected (e.g., HTTP 409 Conflict).
    This typically happens when the version field is stale.

    Attributes:
        issue_key: Key of the issue with the conflict.
        current_version: Current version of the resource.
        expected_version: Version that was provided in the request.
    """

    def __init__(
        self,
        message: str,
        issue_key: str | None = None,
        current_version: int | None = None,
        expected_version: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ConcurrencyError.

        Args:
            message: Human-readable error message.
            issue_key: Key of the issue with the conflict.
            current_version: Current version of the resource on the server.
            expected_version: Version that was provided in the request.
            details: Additional error context dictionary.
        """
        super().__init__(message, details)
        self.issue_key = issue_key
        self.current_version = current_version
        self.expected_version = expected_version

    def __repr__(self) -> str:
        """Return string representation of the error."""
        return (
            f"ConcurrencyError(message={self.message!r}, issue_key={self.issue_key!r}, "
            f"current_version={self.current_version!r}, expected_version={self.expected_version!r})"
        )


class ConfigurationError(TrackerError):
    """Configuration or initialization error.

    Raised when adapter configuration is invalid or missing required parameters.

    Attributes:
        parameter: Name of the invalid or missing parameter.
    """

    def __init__(
        self,
        message: str,
        parameter: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ConfigurationError.

        Args:
            message: Human-readable error message.
            parameter: Name of the invalid or missing parameter.
            details: Additional error context dictionary.
        """
        super().__init__(message, details)
        self.parameter = parameter

    def __repr__(self) -> str:
        """Return string representation of the error."""
        return f"ConfigurationError(message={self.message!r}, parameter={self.parameter!r})"
