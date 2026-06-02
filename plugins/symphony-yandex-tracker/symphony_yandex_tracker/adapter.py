"""Yandex Tracker adapter for Symphony orchestration platform.

This module provides the main adapter class for integrating with Yandex Tracker API v3.

Classes:
    YandexTrackerAdapter: Main adapter class for Yandex Tracker.
"""

import sys
import traceback
from pathlib import Path
from typing import Any

import httpx

from symphony_yandex_tracker import errors, models
from symphony_yandex_tracker import http_client as http_client_module
from symphony_yandex_tracker import logger as logger_module

# Import normalization utilities from runtime (T026)
# Add project root to path if not already available
_project_root = Path(__file__).resolve().parents[3]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    from runtime.tracker.base import TrackerClient
    from runtime.tracker.normalization import NormalizationUtils
except ImportError:
    # Fallback: runtime module not available
    TrackerClient = object  # type: ignore[assignment, misc]
    NormalizationUtils = None  # type: ignore[assignment]

# Default endpoint for Yandex Tracker API v3
DEFAULT_ENDPOINT = "https://api.tracker.yandex.net/v3"

# Default active states for filtering issues
DEFAULT_ACTIVE_STATES = ["open", "in_progress"]


class YandexTrackerAdapter(TrackerClient):
    """Adapter for Yandex Tracker API v3.

    This class provides an interface for interacting with Yandex Tracker issue
    tracking system. It handles authentication, issue fetching, updates, and
    status transitions.

    The adapter is designed to work with the Symphony orchestration platform
    and implements the tracker client interface.

    Attributes:
        tracker_type: Always returns "yandex_tracker".
        tracker_kind: Always returns "yandex_tracker".
        endpoint: Base URL for Yandex Tracker API v3.
        api_key: OAuth or IAM token for authentication.
        timeout: Request timeout in seconds.
        active_states: List of state names for filtering active issues.
        project_slug: Queue key and organization ID for API requests.

    Example:
        >>> adapter = YandexTrackerAdapter(
        ...     api_key="y0__...",
        ...     endpoint="https://api.tracker.yandex.net/v3",
        ...     timeout=30,
        ...     active_states=["open", "in_progress"],
        ...     project_slug="MYQUEUE"
        ... )
        >>> user_info = adapter.authenticate()

    Args:
        api_key: OAuth token (starts with "y0__") or IAM token (starts with "t1.").
        endpoint: Yandex Tracker API v3 URL. Defaults to
            "https://api.tracker.yandex.net/v3".
        timeout: Request timeout in seconds. Defaults to 30.
        active_states: List of state names for filtering active issues.
            Defaults to ["open", "in_progress"].
        project_slug: Queue key AND organization ID. Used for X-Org-ID or
            X-Cloud-Org-ID headers. Must be non-empty for fetching candidate issues.
    """

    # Plugin metadata for discovery (FR-025, US8)
    __plugin_info__: dict[str, str] = {
        "name": "symphony-yandex-tracker",
        "version": "0.1.0",
        "tracker_kind": "yandex_tracker",
        "description": "Yandex Tracker integration adapter for Symphony orchestration platform",
        "author": "py-symphony team",
    }

    def __init__(
        self,
        api_key: str,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: float = 30.0,
        active_states: list[str] | None = None,
        project_slug: str = "",
    ) -> None:
        """Initialize YandexTrackerAdapter.

        Args:
            api_key: OAuth or IAM token for authentication.
            endpoint: API endpoint URL. Defaults to DEFAULT_ENDPOINT.
            timeout: Request timeout in seconds. Defaults to 30.
            active_states: List of active states. Defaults to DEFAULT_ACTIVE_STATES.
            project_slug: Queue key and organization ID.

        Raises:
            errors.ConfigurationError: If api_key is empty.
        """
        # Validate api_key is not empty (T015)
        if not api_key or not api_key.strip():
            raise errors.ConfigurationError(
                message="api_key cannot be empty",
                parameter="api_key",
            )

        self._api_key = api_key
        self._endpoint = endpoint
        self._timeout = timeout
        self._active_states = active_states or DEFAULT_ACTIVE_STATES.copy()
        self._project_slug = project_slug

        # HTTP client is lazily initialized
        self._http_client: http_client_module.TrackerHttpClient | None = None

        # Logger for structured logging
        self._logger = logger_module.get_logger("symphony_yandex_tracker")

        # Log initialization with action="initialize" (T015)
        self._logger.info(
            "YandexTrackerAdapter initialized",
            extra={
                "action": "initialize",
                "outcome": "success",
                "endpoint": self._endpoint,
                "timeout": self._timeout,
                "active_states": self._active_states,
                "project_slug": self._project_slug,
            },
        )

    @property
    def tracker_type(self) -> str:
        """Return the tracker type identifier.

        Returns:
            Always returns "yandex_tracker" (FR-003).
        """
        return "yandex_tracker"

    @property
    def tracker_kind(self) -> str:
        """Return the tracker kind identifier (TrackerClient interface).

        Returns:
            Always returns "yandex_tracker".
        """
        return "yandex_tracker"

    @property
    def endpoint(self) -> str:
        """Return the API endpoint URL.

        Returns:
            Yandex Tracker API v3 endpoint URL.
        """
        return self._endpoint

    @property
    def timeout(self) -> float:
        """Return the request timeout in seconds.

        Returns:
            Timeout value in seconds.
        """
        return self._timeout

    @property
    def active_states(self) -> list[str]:
        """Return the list of active states for filtering issues.

        Returns:
            List of active state names.
        """
        return self._active_states.copy()

    @property
    def project_slug(self) -> str:
        """Return the project/queue slug.

        Returns:
            Queue key and organization ID.
        """
        return self._project_slug

    def _get_http_client(self) -> http_client_module.TrackerHttpClient:
        """Get or create the HTTP client.

        Returns:
            Initialized HTTP client.

        Raises:
            errors.ConfigurationError: If project_slug is not set when required.
        """
        if self._http_client is None:
            # Detect token type (T017)
            token_type = self._detect_token_type(self._api_key)
            # Only pass token_type if it's not the default "oauth"
            # This maintains backward compatibility with existing code/tests
            client_kwargs: dict[str, Any] = {
                "endpoint": self._endpoint,
                "api_key": self._api_key,
                "timeout": self._timeout,
            }
            if token_type != "oauth":
                client_kwargs["token_type"] = token_type

            self._http_client = http_client_module.TrackerHttpClient(**client_kwargs)
        return self._http_client

    def authenticate(self) -> dict[str, Any]:
        """Authenticate with Yandex Tracker API.

        Validates the token by calling GET /v2/myself endpoint and returns
        user information if authentication is successful.

        Returns:
            Dictionary containing user information.

        Raises:
            errors.TrackerApiError: If API request fails.
            errors.TrackerTimeoutError: If request times out.
            errors.TokenExpiredError: If token is invalid or expired.
        """
        with logger_module.OperationTimer() as timer:
            try:
                client = self._get_http_client()
                response = client.get("/v2/myself")

                if response.status_code == 200:
                    self._logger.info(
                        "Authentication successful",
                        extra={
                            "action": "authenticate",
                            "outcome": "success",
                            "duration_ms": timer.get_duration_ms(),
                        },
                    )
                    return response.json()  # type: ignore[no-any-return]  # type: ignore[no-any-return]
                elif response.status_code == 401:
                    raise errors.TokenExpiredError(
                        message="Authentication failed: token is invalid or expired",
                        token_type=self._detect_token_type(self._api_key),
                    )
                else:
                    raise errors.TrackerApiError(
                        message=f"Authentication failed: {response.status_code}",
                        status_code=response.status_code,
                        response_body=response.text,
                    )
            except httpx.TimeoutException as e:
                self._logger.error(
                    f"Authentication timeout: {e}",
                    extra={
                        "action": "authenticate",
                        "outcome": "error",
                        "duration_ms": timer.get_duration_ms(),
                        "error_message": str(e),
                    },
                )
                raise errors.TrackerTimeoutError(
                    message=f"Request timed out: {e}",
                    timeout=float(self._timeout),
                    url=f"{self._endpoint}/v2/myself",
                )
            except httpx.HTTPError as e:
                self._logger.error(
                    f"Authentication error: {e}",
                    extra={
                        "action": "authenticate",
                        "outcome": "error",
                        "duration_ms": timer.get_duration_ms(),
                        "error_message": str(e),
                    },
                )
                raise errors.TrackerApiError(message=f"HTTP error: {e}")

    def _detect_token_type(self, token: str) -> str:
        """Detect the type of authentication token.

        Args:
            token: The token string.

        Returns:
            "oauth" for OAuth tokens (starts with "y0__"),
            "iam" for IAM tokens (starts with "t1.").
            Defaults to "oauth" for unrecognized tokens (T017).
        """
        if token.startswith("y0__"):
            return "oauth"
        elif token.startswith("t1."):
            return "iam"
        # Default to oauth for unrecognized tokens (T017)
        return "oauth"

    def fetch_candidate_issues(
        self,
        per_page: int = 50,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """Fetch candidate issues for orchestration.

        Fetches issues from the configured queue that are in active states.
        These are issues that could potentially be dispatched to agent execution.

        Args:
            per_page: Number of issues per page (default: 50).
            page: Page number to fetch (default: 1).

        Returns:
            List of normalized issue dictionaries with fields:
                - id: Issue internal ID
                - identifier: Issue key (e.g., "BACKEND-123")
                - title: Issue summary/title
                - state: Current status/state
                - priority: Priority level
                - created_at: Creation timestamp
                - labels: Issue tags/labels
                - blocked_by: List of blocking issues

        Raises:
            errors.ConfigurationError: If project_slug is not set (T024).
            errors.TrackerApiError: If API request fails.
            errors.TrackerTimeoutError: If request times out.
        """
        # T024: Validate project_slug is not empty
        if not self._project_slug:
            raise errors.ConfigurationError(
                message="project_slug is required for fetching candidate issues",
                parameter="project_slug",
            )

        with logger_module.OperationTimer() as timer:
            try:
                client = self._get_http_client()

                # T025: Build query parameters with pagination
                params: dict[str, Any] = {
                    "queue": self._project_slug,
                    "perPage": per_page,
                    "page": page,
                }

                # Filter by active states - Yandex Tracker API filter syntax
                if self._active_states:
                    # Use status filtering with "in" operator
                    # Format: status in (open, in_progress)
                    status_filter = ", ".join(self._active_states)
                    params["filter"] = f"status in ({status_filter})"

                response = client.get("/v2/issues", params=params)

                if response.status_code == 200:
                    raw_issues: list[dict[str, Any]] = response.json()

                    # T026: Normalize issues using runtime utilities
                    normalized_issues = self._normalize_issues(raw_issues)

                    self._logger.info(
                        f"Fetched {len(normalized_issues)} candidate issues",
                        extra={
                            "action": "fetch_candidate_issues",
                            "outcome": "success",
                            "duration_ms": timer.get_duration_ms(),
                            "issue_count": len(normalized_issues),
                            "project_slug": self._project_slug,
                            "per_page": per_page,
                            "page": page,
                        },
                    )
                    return normalized_issues
                else:
                    raise errors.TrackerApiError(
                        message=f"Failed to fetch issues: {response.status_code}",
                        status_code=response.status_code,
                        response_body=response.text,
                    )
            except httpx.TimeoutException as e:
                self._logger.error(
                    f"Fetch candidate issues timeout: {e}",
                    extra={
                        "action": "fetch_candidate_issues",
                        "outcome": "error",
                        "duration_ms": timer.get_duration_ms(),
                        "error_message": str(e),
                        "project_slug": self._project_slug,
                    },
                )
                raise errors.TrackerTimeoutError(
                    message=f"Request timed out: {e}",
                    timeout=float(self._timeout),
                    url=f"{self._endpoint}/v2/issues",
                )
            except httpx.HTTPError as e:
                self._logger.error(
                    f"Fetch candidate issues error: {e}",
                    extra={
                        "action": "fetch_candidate_issues",
                        "outcome": "error",
                        "duration_ms": timer.get_duration_ms(),
                        "error_message": str(e),
                        "project_slug": self._project_slug,
                    },
                )
                raise errors.TrackerApiError(message=f"HTTP error: {e}")

    def _normalize_issues(
        self,
        raw_issues: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Normalize raw Yandex Tracker issues to common format.

        Args:
            raw_issues: List of raw issue dictionaries from Yandex Tracker API.

        Returns:
            List of normalized issue dictionaries.

        Note:
            T026: Normalization maps Yandex Tracker fields to normalized format:
            - self -> id (extracted from URL)
            - key -> identifier
            - summary -> title
            - status -> state
            - priority -> priority
            - createdAt -> created_at
            - tags -> labels
            - dependencies -> blocked_by
        """
        if not raw_issues:
            return []

        # Use runtime normalization if available
        if NormalizationUtils is not None:
            try:
                return [NormalizationUtils.normalize_issue(self._normalize_yandex_issue(issue)) for issue in raw_issues]
            except (ImportError, AttributeError, ValueError) as e:
                # Issue #1 & #4: Log the fallback instead of silent pass
                self._logger.warning(
                    f"Runtime normalization failed ({e}), using internal normalization",
                    extra={"action": "normalize_issues", "outcome": "fallback"},
                )

        # Fallback: internal normalization
        normalized = []
        for issue in raw_issues:
            normalized_issue = self._normalize_yandex_issue(issue)
            # Skip empty issues (invalid issues without identifiers)
            if normalized_issue:
                normalized.append(normalized_issue)

        return normalized

    def _normalize_yandex_issue(self, raw_issue: dict[str, Any]) -> dict[str, Any]:
        """Normalize a single Yandex Tracker issue to common format.

        Args:
            raw_issue: Raw issue from Yandex Tracker API.

        Returns:
            Normalized issue dictionary.
        """
        # Extract ID from self URL
        issue_id = None
        self_url = raw_issue.get("self", "")
        if self_url:
            # Extract ID from URL like https://api.tracker.yandex.net/v2/issues/123
            parts = self_url.rstrip("/").split("/")
            if parts:
                issue_id = parts[-1]

        # Extract status name
        status = raw_issue.get("status", {})
        state = ""
        if isinstance(status, dict):
            state = status.get("name", "") or status.get("key", "")
        elif status:
            state = str(status)

        # Extract priority
        priority = raw_issue.get("priority", {})
        priority_value = None
        if isinstance(priority, dict):
            # Try key first, then name
            priority_key = priority.get("key") or priority.get("name")
            if priority_key:
                priority_map = {
                    "critical": 1,
                    "high": 2,
                    "medium": 3,
                    "low": 4,
                }
                priority_value = priority_map.get(str(priority_key).lower(), 3)
        elif priority:
            priority_value = priority

        # Extract labels/tags
        labels = raw_issue.get("tags", [])
        if not labels:
            labels = []

        # Extract blocked_by/dependencies
        blocked_by = raw_issue.get("dependencies", [])
        if not blocked_by:
            blocked_by = []
        # Extract just IDs from dependencies
        if blocked_by:
            blocked_by = [dep.get("id", "") for dep in blocked_by if dep.get("id")]

        # Issue #2: Validate that at least one identifier is present
        issue_id_value = issue_id or raw_issue.get("id")
        issue_key_value = raw_issue.get("key")
        if not (issue_id_value or issue_key_value):
            self._logger.warning(
                f"Issue missing all identifiers, skipping: {raw_issue}",
                extra={"action": "normalize_issue", "outcome": "skip"},
            )
            return {}  # Return empty dict for invalid issues

        return {
            "id": issue_id_value,
            "identifier": issue_key_value or "",
            "title": raw_issue.get("summary", ""),
            "state": state.lower().strip() if state else "",
            "priority": priority_value,
            "created_at": raw_issue.get("createdAt", ""),
            "labels": labels,
            "blocked_by": blocked_by,
        }

    def fetch_issues_by_state(self, states: list[str]) -> list[dict[str, Any]]:
        """Fetch issues filtered by state list.

        Args:
            states: List of state names to filter by.

        Returns:
            List of normalized issue dictionaries.

        Raises:
            errors.ConfigurationError: If project_slug is not set.
            errors.TrackerApiError: If API request fails.
            errors.TrackerTimeoutError: If request times out.
        """
        # T031: Validate project_slug is not empty
        if not self._project_slug:
            raise errors.ConfigurationError(
                message="project_slug is required for fetching issues",
                parameter="project_slug",
            )

        if not states:
            return []

        # Validate content of the list
        validated_states = []
        for state in states:
            if not isinstance(state, str):
                raise errors.ValidationError(
                    message=f"State must be string, got {type(state).__name__}",
                    field="states",
                    constraint="list of strings",
                )
            if not state.strip():
                # Skip empty strings with warning
                self._logger.warning(
                    "Skipping empty state in states list",
                    extra={"action": "fetch_issues_by_state", "outcome": "warning"},
                )
                continue
            validated_states.append(state.strip())

        if not validated_states:
            return []

        with logger_module.OperationTimer() as timer:
            try:
                client = self._get_http_client()

                # T031: Server-side filtering using API and pagination
                all_normalized_issues: list[dict[str, Any]] = []
                page = 1
                per_page = 50
                total_pages = 0  # Track total pages for logging

                while True:
                    total_pages += 1  # Increment at the beginning of each iteration
                    params: dict[str, Any] = {
                        "queue": self._project_slug,
                        "perPage": per_page,
                        "page": page,
                    }

                    # T031: Filter by states using API - use status filtering with "in" operator
                    # Format: status in (open, in_progress)
                    # Convert human-readable state names to API keys (lowercase, spaces to underscores)
                    status_keys = [state.lower().replace(" ", "_").replace("-", "_") for state in validated_states]
                    status_filter = ", ".join(status_keys)
                    params["filter"] = f"status in ({status_filter})"

                    response = client.get("/v2/issues", params=params)

                    if response.status_code != 200:
                        raise errors.TrackerApiError(
                            message=f"Failed to fetch issues: {response.status_code}",
                            status_code=response.status_code,
                            response_body=response.text,
                        )

                    raw_issues: list[dict[str, Any]] = response.json()

                    # T031: Normalize issues using runtime utilities
                    if raw_issues:
                        normalized_issues = self._normalize_issues(raw_issues)
                        all_normalized_issues.extend(normalized_issues)

                    # T031: Pagination - check if we got full page
                    if len(raw_issues) < per_page:
                        break
                    page += 1

                # T031: Client-side filtering to ensure exact state matching
                # (handles edge cases where API may return extra issues)
                state_names_lower = {s.lower() for s in validated_states}
                filtered_issues = [
                    issue for issue in all_normalized_issues if issue.get("state", "").lower() in state_names_lower
                ]

                # T031: Log successful fetch with structured logging
                self._logger.info(
                    f"Fetched {len(filtered_issues)} issues by state",
                    extra={
                        "action": "fetch_issues_by_state",
                        "outcome": "success",
                        "duration_ms": timer.get_duration_ms(),
                        "states": validated_states,
                        "issue_count": len(filtered_issues),
                        "project_slug": self._project_slug,
                        "per_page": per_page,
                        "page": total_pages,  # Use correct page count
                    },
                )
                return filtered_issues

            except httpx.TimeoutException as e:
                # T031: Handle timeout error with structured logging
                self._logger.error(
                    f"Fetch issues by state timeout: {e}",
                    extra={
                        "action": "fetch_issues_by_state",
                        "outcome": "error",
                        "duration_ms": timer.get_duration_ms(),
                        "error_message": str(e),
                        "stack_trace": traceback.format_exc(),
                        "project_slug": self._project_slug,
                        "states": validated_states,
                    },
                )
                raise errors.TrackerTimeoutError(
                    message=f"Request timed out: {e}",
                    timeout=float(self._timeout),
                    url=f"{self._endpoint}/v2/issues",
                )
            except httpx.HTTPError as e:
                # T031: Handle HTTP error with structured logging
                self._logger.error(
                    f"Fetch issues by state error: {e}",
                    extra={
                        "action": "fetch_issues_by_state",
                        "outcome": "error",
                        "duration_ms": timer.get_duration_ms(),
                        "error_message": str(e),
                        "stack_trace": traceback.format_exc(),
                        "project_slug": self._project_slug,
                        "states": validated_states,
                    },
                )
                raise errors.TrackerApiError(message=f"HTTP error: {e}")
            except Exception as e:
                self._logger.error(
                    f"Unexpected error fetching issues by state: {e}",
                    extra={
                        "action": "fetch_issues_by_state",
                        "outcome": "error",
                        "duration_ms": timer.get_duration_ms(),
                        "error_message": str(e),
                        "stack_trace": traceback.format_exc(),
                        "project_slug": self._project_slug,
                        "states": validated_states,
                    },
                )
                raise errors.TrackerApiError(message=f"Unexpected error: {e}")

    def fetch_issues_by_states(self, state_names: list[str]) -> list[dict[str, Any]]:
        """Fetch issues matching the specified states (TrackerClient interface).

        Delegates to fetch_issues_by_state for backward compatibility.

        Args:
            state_names: List of state names to filter by.

        Returns:
            List of normalized issue dictionaries.
        """
        return self.fetch_issues_by_state(state_names)

    def fetch_issue_states_by_ids(self, issue_ids: list[str]) -> dict[str, str]:
        """Fetch current states for specific issue IDs.

        Args:
            issue_ids: List of issue IDs to fetch states for.

        Returns:
            Dictionary mapping issue_id to current state name.

        Raises:
            errors.TrackerApiError: If API request fails.
        """
        if not issue_ids:
            return {}

        with logger_module.OperationTimer() as timer:
            try:
                client = self._get_http_client()
                result: dict[str, str] = {}

                for issue_id in issue_ids:
                    try:
                        response = client.get(f"/v2/issues/{issue_id}")
                        if response.status_code == 200:
                            issue = response.json()
                            state = issue.get("status", {}).get("name", "")
                            result[issue_id] = state
                        elif response.status_code == 404:
                            # Issue not found - skip it
                            pass
                        else:
                            # Log but continue with other issues
                            self._logger.warning(
                                f"Failed to fetch issue {issue_id}: {response.status_code}",
                                extra={
                                    "action": "fetch_issue_states_by_ids",
                                    "outcome": "error",
                                    "issue_id": issue_id,
                                },
                            )
                    except httpx.HTTPError as e:
                        self._logger.warning(
                            f"Error fetching issue {issue_id}: {e}",
                            extra={
                                "action": "fetch_issue_states_by_ids",
                                "outcome": "error",
                                "issue_id": issue_id,
                                "error_message": str(e),
                            },
                        )

                self._logger.info(
                    f"Fetched states for {len(result)} issues",
                    extra={
                        "action": "fetch_issue_states_by_ids",
                        "outcome": "success",
                        "duration_ms": timer.get_duration_ms(),
                        "issue_count": len(result),
                    },
                )
                return result
            except Exception as e:
                # Re-raise as TrackerApiError for other exceptions
                raise errors.TrackerApiError(message=f"Failed to fetch states: {e}")

    def get_issue(self, issue_key: str) -> dict[str, Any]:
        """Fetch full issue details.

        Args:
            issue_key: Issue key (e.g., "BACKEND-123").

        Returns:
            Dictionary containing full issue details.

        Raises:
            errors.ResourceNotFoundError: If issue does not exist.
            errors.TrackerApiError: If API request fails.
        """
        with logger_module.OperationTimer() as timer:
            try:
                client = self._get_http_client()
                response = client.get(f"/v2/issues/{issue_key}")

                if response.status_code == 200:
                    self._logger.info(
                        f"Fetched issue {issue_key}",
                        extra={
                            "action": "get_issue",
                            "outcome": "success",
                            "duration_ms": timer.get_duration_ms(),
                            "issue_id": issue_key,
                        },
                    )
                    return response.json()  # type: ignore[no-any-return]
                elif response.status_code == 404:
                    raise errors.ResourceNotFoundError(
                        message=f"Issue not found: {issue_key}",
                        resource_type="issue",
                        resource_id=issue_key,
                    )
                else:
                    raise errors.TrackerApiError(
                        message=f"Failed to fetch issue: {response.status_code}",
                        status_code=response.status_code,
                        response_body=response.text,
                    )
            except httpx.HTTPError as e:
                self._logger.error(
                    f"Get issue error: {e}",
                    extra={
                        "action": "get_issue",
                        "outcome": "error",
                        "duration_ms": timer.get_duration_ms(),
                        "error_message": str(e),
                    },
                )
                raise errors.TrackerApiError(message=f"HTTP error: {e}")

    def update_issue(
        self,
        issue_key: str,
        request: models.UpdateIssueRequest,
    ) -> dict[str, Any]:
        """Update an issue.

        Args:
            issue_key: Issue key (e.g., "BACKEND-123").
            request: UpdateIssueRequest with fields to update.

        Returns:
            Dictionary containing updated issue details.

        Raises:
            errors.ValidationError: If request validation fails.
            errors.ConcurrencyError: If version conflict (409).
            errors.ResourceNotFoundError: If issue does not exist.
            errors.TrackerApiError: If API request fails.
        """
        # Validate request
        validation_errors = request.validate()
        if validation_errors:
            raise errors.ValidationError(
                message=f"Invalid request: {', '.join(validation_errors)}",
            )

        with logger_module.OperationTimer() as timer:
            try:
                client = self._get_http_client()
                response = client.patch(
                    f"/v2/issues/{issue_key}",
                    json=request.to_dict(),
                )

                if response.status_code == 200:
                    self._logger.info(
                        f"Updated issue {issue_key}",
                        extra={
                            "action": "update_issue",
                            "outcome": "success",
                            "duration_ms": timer.get_duration_ms(),
                            "issue_id": issue_key,
                        },
                    )
                    return response.json()  # type: ignore[no-any-return]
                elif response.status_code == 404:
                    raise errors.ResourceNotFoundError(
                        message=f"Issue not found: {issue_key}",
                        resource_type="issue",
                        resource_id=issue_key,
                    )
                elif response.status_code == 409:
                    raise errors.ConcurrencyError(
                        message="Version conflict: issue was modified by another process",
                        issue_key=issue_key,
                        expected_version=request.version,
                    )
                else:
                    raise errors.TrackerApiError(
                        message=f"Failed to update issue: {response.status_code}",
                        status_code=response.status_code,
                        response_body=response.text,
                    )
            except httpx.HTTPError as e:
                self._logger.error(
                    f"Update issue error: {e}",
                    extra={
                        "action": "update_issue",
                        "outcome": "error",
                        "duration_ms": timer.get_duration_ms(),
                        "error_message": str(e),
                    },
                )
                raise errors.TrackerApiError(message=f"HTTP error: {e}")

    def add_comment(self, issue_key: str, text: str) -> dict[str, Any]:
        """Add a comment to an issue.

        Args:
            issue_key: Issue key (e.g., "BACKEND-123").
            text: Comment text (markdown).

        Returns:
            Dictionary containing created comment details.

        Raises:
            errors.ValidationError: If comment text is empty.
            errors.ResourceNotFoundError: If issue does not exist.
            errors.TrackerApiError: If API request fails.
        """
        if not text or not text.strip():
            raise errors.ValidationError(
                message="Comment text cannot be empty",
                field="text",
                constraint="non-empty string",
            )

        with logger_module.OperationTimer() as timer:
            try:
                client = self._get_http_client()
                response = client.post(
                    f"/v2/issues/{issue_key}/comments",
                    json={"text": text},
                )

                if response.status_code == 201:
                    self._logger.info(
                        f"Added comment to issue {issue_key}",
                        extra={
                            "action": "add_comment",
                            "outcome": "success",
                            "duration_ms": timer.get_duration_ms(),
                            "issue_id": issue_key,
                        },
                    )
                    return response.json()  # type: ignore[no-any-return]
                elif response.status_code == 404:
                    raise errors.ResourceNotFoundError(
                        message=f"Issue not found: {issue_key}",
                        resource_type="issue",
                        resource_id=issue_key,
                    )
                else:
                    raise errors.TrackerApiError(
                        message=f"Failed to add comment: {response.status_code}",
                        status_code=response.status_code,
                        response_body=response.text,
                    )
            except httpx.HTTPError as e:
                self._logger.error(
                    f"Add comment error: {e}",
                    extra={
                        "action": "add_comment",
                        "outcome": "error",
                        "duration_ms": timer.get_duration_ms(),
                        "error_message": str(e),
                    },
                )
                raise errors.TrackerApiError(message=f"HTTP error: {e}")

    def list_transitions(self, issue_key: str) -> list[dict[str, Any]]:
        """List available status transitions for an issue.

        Args:
            issue_key: Issue key (e.g., "BACKEND-123").

        Returns:
            List of transition dictionaries.

        Raises:
            errors.ResourceNotFoundError: If issue does not exist.
            errors.TrackerApiError: If API request fails.
        """
        with logger_module.OperationTimer() as timer:
            try:
                client = self._get_http_client()
                response = client.get(f"/v2/issues/{issue_key}/transitions")

                if response.status_code == 200:
                    transitions: list[dict[str, Any]] = response.json()
                    self._logger.info(
                        f"Listed {len(transitions)} transitions for issue {issue_key}",
                        extra={
                            "action": "list_transitions",
                            "outcome": "success",
                            "duration_ms": timer.get_duration_ms(),
                            "issue_id": issue_key,
                            "transition_count": len(transitions),
                        },
                    )
                    return transitions
                elif response.status_code == 404:
                    raise errors.ResourceNotFoundError(
                        message=f"Issue not found: {issue_key}",
                        resource_type="issue",
                        resource_id=issue_key,
                    )
                else:
                    raise errors.TrackerApiError(
                        message=f"Failed to list transitions: {response.status_code}",
                        status_code=response.status_code,
                        response_body=response.text,
                    )
            except httpx.HTTPError as e:
                self._logger.error(
                    f"List transitions error: {e}",
                    extra={
                        "action": "list_transitions",
                        "outcome": "error",
                        "duration_ms": timer.get_duration_ms(),
                        "error_message": str(e),
                    },
                )
                raise errors.TrackerApiError(message=f"HTTP error: {e}")

    def find_transition_by_status(
        self,
        issue_key: str,
        status_name: str,
    ) -> str | None:
        """Find transition ID by target status name.

        Args:
            issue_key: Issue key (e.g., "BACKEND-123").
            status_name: Target status name to find transition for.

        Returns:
            Transition ID if found, None otherwise.
        """
        transitions = self.list_transitions(issue_key)

        for transition in transitions:
            # Yandex Tracker transitions have target status info
            target = transition.get("target", {})
            target_status = target.get("name") if isinstance(target, dict) else None

            if target_status == status_name:
                return transition.get("id")

        return None

    def transition_issue(
        self,
        issue_key: str,
        transition_id: str,
    ) -> dict[str, Any]:
        """Execute a status transition on an issue.

        Args:
            issue_key: Issue key (e.g., "BACKEND-123").
            transition_id: Transition ID to execute.

        Returns:
            Dictionary containing transition result.

        Raises:
            errors.TransitionNotFoundError: If transition is not available.
            errors.ResourceNotFoundError: If issue does not exist.
            errors.TrackerApiError: If API request fails.
        """
        with logger_module.OperationTimer() as timer:
            try:
                client = self._get_http_client()
                response = client.post(f"/v2/issues/{issue_key}/transitions/{transition_id}")

                if response.status_code == 200:
                    self._logger.info(
                        f"Executed transition {transition_id} on issue {issue_key}",
                        extra={
                            "action": "transition_issue",
                            "outcome": "success",
                            "duration_ms": timer.get_duration_ms(),
                            "issue_id": issue_key,
                            "transition_id": transition_id,
                        },
                    )
                    return response.json()  # type: ignore[no-any-return]
                elif response.status_code == 404:
                    # Check if issue or transition not found
                    raise errors.TransitionNotFoundError(
                        message=f"Transition not found: {transition_id}",
                        issue_key=issue_key,
                        target_status=transition_id,
                    )
                else:
                    raise errors.TrackerApiError(
                        message=f"Failed to execute transition: {response.status_code}",
                        status_code=response.status_code,
                        response_body=response.text,
                    )
            except httpx.HTTPError as e:
                self._logger.error(
                    f"Transition issue error: {e}",
                    extra={
                        "action": "transition_issue",
                        "outcome": "error",
                        "duration_ms": timer.get_duration_ms(),
                        "error_message": str(e),
                    },
                )
                raise errors.TrackerApiError(message=f"HTTP error: {e}")

    def close(self) -> None:
        """Close the adapter and release resources.

        Should be called when the adapter is no longer needed.
        """
        if self._http_client is not None:
            self._http_client.close()
            self._http_client = None

    def __enter__(self) -> "YandexTrackerAdapter":
        """Enter context manager.

        Returns:
            Self.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit context manager."""
        self.close()
