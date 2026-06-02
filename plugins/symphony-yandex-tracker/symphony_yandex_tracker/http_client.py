"""HTTP client for Yandex Tracker API.

This module provides an httpx-based HTTP client with connection pooling
and default timeout configuration for communicating with Yandex Tracker API v3.

Classes:
    TrackerHttpClient: HTTP client for Yandex Tracker API.
"""

from typing import Any

import httpx

DEFAULT_TIMEOUT: float = 30.0
"""Default timeout for API requests in seconds."""


class TrackerHttpClient:
    """HTTP client for Yandex Tracker API.

    This client wraps httpx with connection pooling and default timeout configuration.
    It provides a simplified interface for making authenticated API requests
    to Yandex Tracker API v3.

    Attributes:
        client: The underlying httpx.Client instance.
        endpoint: Base API endpoint URL.
        api_key: Authentication token.
        timeout: Request timeout in seconds.

    Example:
        >>> client = TrackerHttpClient(
        ...     endpoint="https://api.tracker.yandex.net/v3",
        ...     api_key="y0__...",
        ...     timeout=30.0
        ... )
        >>> response = client.get("/v2/myself")
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        timeout: float = DEFAULT_TIMEOUT,
        token_type: str = "oauth",
    ) -> None:
        """Initialize TrackerHttpClient.

        Args:
            endpoint: Base API endpoint URL (e.g., "https://api.tracker.yandex.net/v3").
            api_key: OAuth or IAM token for authentication.
            timeout: Request timeout in seconds. Defaults to 30 seconds.
            token_type: Token type ("oauth" for OAuth tokens, "iam" for IAM tokens).
                Defaults to "oauth".
        """
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._token_type = token_type

        # Configure httpx client with connection pooling
        # Limits are set for reasonable concurrent usage
        self.client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30.0,
            ),
            headers=self._build_headers(),
        )

    def _build_headers(self) -> dict[str, str]:
        """Build default headers for API requests.

        Uses the token type to determine the correct Authorization header format:
        - OAuth tokens (y0__ prefix): "Authorization: OAuth <token>"
        - IAM tokens (t1. prefix): "Authorization: Bearer <token>"

        Returns:
            Dictionary of default headers including Authorization.
        """
        if self._token_type == "iam":
            auth_header = f"Bearer {self.api_key}"
        else:
            # Default to OAuth for unknown token types (T017)
            auth_header = f"OAuth {self.api_key}"

        return {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get_full_url(self, path: str) -> str:
        """Get full URL for the given path.

        Args:
            path: API endpoint path (e.g., "/v2/myself").

        Returns:
            Full URL including endpoint.
        """
        return f"{self.endpoint}{path}"

    def get(self, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
        """Perform GET request.

        Args:
            path: API endpoint path.
            params: Query parameters.

        Returns:
            HTTP response object.
        """
        url = self._get_full_url(path)
        return self.client.get(url, params=params)

    def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Perform POST request.

        Args:
            path: API endpoint path.
            json: JSON request body.
            params: Query parameters.

        Returns:
            HTTP response object.
        """
        url = self._get_full_url(path)
        return self.client.post(url, json=json, params=params)

    def patch(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Perform PATCH request.

        Args:
            path: API endpoint path.
            json: JSON request body.
            params: Query parameters.

        Returns:
            HTTP response object.
        """
        url = self._get_full_url(path)
        return self.client.patch(url, json=json, params=params)

    def put(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Perform PUT request.

        Args:
            path: API endpoint path.
            json: JSON request body.
            params: Query parameters.

        Returns:
            HTTP response object.
        """
        url = self._get_full_url(path)
        return self.client.put(url, json=json, params=params)

    def delete(self, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
        """Perform DELETE request.

        Args:
            path: API endpoint path.
            params: Query parameters.

        Returns:
            HTTP response object.
        """
        url = self._get_full_url(path)
        return self.client.delete(url, params=params)

    def close(self) -> None:
        """Close the HTTP client and release resources.

        Should be called when the client is no longer needed.
        """
        self.client.close()

    def __enter__(self) -> "TrackerHttpClient":
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
