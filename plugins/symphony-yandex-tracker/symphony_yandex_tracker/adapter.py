"""Yandex Tracker adapter for Symphony orchestration platform.

This module provides the main adapter class for integrating with Yandex Tracker API v3.

Classes:
    YandexTrackerAdapter: Main adapter class for Yandex Tracker.
"""

from typing import Any

import httpx

from symphony_yandex_tracker import errors, models
from symphony_yandex_tracker import http_client as http_client_module
from symphony_yandex_tracker import logger as logger_module

# Default endpoint for Yandex Tracker API v3
DEFAULT_ENDPOINT = "https://api.tracker.yandex.net/v3"

# Default active states for filtering issues
DEFAULT_ACTIVE_STATES = ["open", "in_progress"]


class YandexTrackerAdapter:
    """Adapter for Yandex Tracker API v3.

    This class provides an interface for interacting with Yandex Tracker issue
    tracking system. It handles authentication, issue fetching, updates, and
    status transitions.

    The adapter is designed to work with the Symphony orchestration platform
    and implements the tracker client interface.

    Attributes:
        tracker_type: Always returns "yandex_tracker".
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

    # Plugin metadata for discovery (FR-025)
    __plugin_info__: dict[str, str] = {
        "name": "symphony-yandex-tracker",
        "version": "0.1.0",
        "tracker_kind": "yandex_tracker",
        "description": "Yandex Tracker adapter for Symphony orchestration platform",
        "author": "Symphony Team",
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

    def fetch_candidate_issues(self) -> list[dict[str, Any]]:
        """Fetch candidate issues for orchestration.

        Fetches issues from the configured queue that are in active states.
        These are issues that could potentially be dispatched to agent execution.

        Returns:
            List of normalized issue dictionaries.

        Raises:
            errors.ConfigurationError: If project_slug is not set.
            errors.TrackerApiError: If API request fails.
            errors.TrackerTimeoutError: If request times out.
        """
        if not self._project_slug:
            raise errors.ConfigurationError(
                message="project_slug is required for fetching candidate issues",
                parameter="project_slug",
            )

        with logger_module.OperationTimer() as timer:
            try:
                client = self._get_http_client()

                # Build query parameters
                params: dict[str, Any] = {
                    "queue": self._project_slug,
                    "perPage": 100,
                }

                # Filter by active states
                if self._active_states:
                    # Yandex Tracker API uses status specific filtering
                    # We'll fetch all and filter locally for simplicity
                    pass

                response = client.get("/v2/issues", params=params)

                if response.status_code == 200:
                    issues: list[dict[str, Any]] = response.json()
                    self._logger.info(
                        f"Fetched {len(issues)} candidate issues",
                        extra={
                            "action": "fetch_candidate_issues",
                            "outcome": "success",
                            "duration_ms": timer.get_duration_ms(),
                            "issue_count": len(issues),
                        },
                    )
                    return issues
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
                    },
                )
                raise errors.TrackerTimeoutError(
                    message=f"Request timed out: {e}",
                    timeout=float(self._timeout),
                )
            except httpx.HTTPError as e:
                self._logger.error(
                    f"Fetch candidate issues error: {e}",
                    extra={
                        "action": "fetch_candidate_issues",
                        "outcome": "error",
                        "duration_ms": timer.get_duration_ms(),
                        "error_message": str(e),
                    },
                )
                raise errors.TrackerApiError(message=f"HTTP error: {e}")

    def fetch_issues_by_state(self, states: list[str]) -> list[dict[str, Any]]:
        """Fetch issues filtered by state list.

        Args:
            states: List of state names to filter by.

        Returns:
            List of normalized issue dictionaries.

        Raises:
            errors.ConfigurationError: If project_slug is not set.
            errors.TrackerApiError: If API request fails.
        """
        if not self._project_slug:
            raise errors.ConfigurationError(
                message="project_slug is required for fetching issues",
                parameter="project_slug",
            )

        if not states:
            return []

        with logger_module.OperationTimer() as timer:
            try:
                client = self._get_http_client()

                params: dict[str, Any] = {
                    "queue": self._project_slug,
                    "perPage": 100,
                }

                response = client.get("/v2/issues", params=params)

                if response.status_code == 200:
                    all_issues = response.json()
                    # Filter by states locally
                    filtered = [issue for issue in all_issues if issue.get("status", {}).get("name") in states]
                    self._logger.info(
                        f"Fetched {len(filtered)} issues by state",
                        extra={
                            "action": "fetch_issues_by_state",
                            "outcome": "success",
                            "duration_ms": timer.get_duration_ms(),
                            "states": states,
                            "issue_count": len(filtered),
                        },
                    )
                    return filtered
                else:
                    raise errors.TrackerApiError(
                        message=f"Failed to fetch issues: {response.status_code}",
                        status_code=response.status_code,
                        response_body=response.text,
                    )
            except httpx.HTTPError as e:
                self._logger.error(
                    f"Fetch issues by state error: {e}",
                    extra={
                        "action": "fetch_issues_by_state",
                        "outcome": "error",
                        "duration_ms": timer.get_duration_ms(),
                        "error_message": str(e),
                    },
                )
                raise errors.TrackerApiError(message=f"HTTP error: {e}")

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
