"""Internal Jira REST API tracker adapter.

This module contains the full Jira tracker implementation.
The runtime/tracker/jira.py module re-exports this for backwards compatibility.
This allows the plugin to import from runtime.tracker.base without circular imports.
"""

import base64
from typing import Any, Dict, List, Optional

import requests

from .base import TrackerClient
from .factory import (
    TrackerAPIError,
    TrackerApiRequestError,
    TrackerApiStatusError,
    TrackerApiRateLimitError,
    TrackerApiTimeoutError,
    TrackerApiResourceNotFoundError,
)
from .normalization import NormalizationUtils


# Default configuration
DEFAULT_TIMEOUT = 30
MAX_RESULTS = 50

# Default active states for candidate issues
DEFAULT_ACTIVE_STATES = ["To Do", "In Progress"]


class JiraTracker(TrackerClient):
    """Jira issue tracker adapter.

    Implements the TrackerClient interface for Jira's REST API.
    Supports Jira Cloud with Basic Authentication.
    """

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        project_key: str = "",
        username: str = "",
        timeout: int = DEFAULT_TIMEOUT,
        active_states: Optional[List[str]] = None,
    ):
        """Initialize Jira tracker adapter.

        Args:
            api_key: Jira API token (or password for basic auth)
            endpoint: Jira instance URL (e.g., https://company.atlassian.net)
            project_key: Project key for filtering issues
            username: Username/email for basic authentication
            timeout: Request timeout in seconds (default: 30)
            active_states: Optional list of active states for candidate issues
        """
        self._api_key = api_key
        self._endpoint = endpoint.rstrip("/")
        self._project_key = project_key
        self._username = username
        self._timeout = timeout
        self._active_states = active_states or DEFAULT_ACTIVE_STATES
        self._session = None
        self._user = None

    @property
    def tracker_kind(self) -> str:
        """Return the tracker kind identifier."""
        return "jira"

    def _get_auth_header(self) -> str:
        """Generate Basic Auth header.

        Returns:
            Basic Auth header value (base64 encoded credentials)
        """
        credentials = f"{self._username}:{self._api_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """Execute HTTP request with error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API endpoint path
            data: Optional request body (JSON)
            params: Optional query parameters

        Returns:
            Response object

        Raises:
            TrackerApiRateLimitError: On rate limiting (429)
            TrackerApiStatusError: On unauthorized (401), forbidden (403), or other HTTP errors
            TrackerApiTimeoutError: On request timeout
            TrackerApiRequestError: On network/transport errors
        """
        url = f"{self._endpoint}{path}"
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self._timeout,
            )

            # Handle rate limiting (429)
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise TrackerApiRateLimitError(
                    f"Jira API rate limit exceeded. Retry after {retry_after} seconds"
                )

            # Handle unauthorized (401)
            if response.status_code == 401:
                raise TrackerApiStatusError(
                    "Invalid Jira credentials (401 Unauthorized)"
                )

            # Handle forbidden (403)
            if response.status_code == 403:
                raise TrackerApiStatusError(
                    f"Jira API access forbidden (403): {response.text[:200]}"
                )

            # Handle not found (404)
            if response.status_code == 404:
                raise TrackerApiResourceNotFoundError(f"Resource not found: {path}")

            # Handle other client errors (400-499)
            if 400 <= response.status_code < 500:
                error_msg = self._parse_error_response(response)
                raise TrackerApiStatusError(
                    f"Jira API error {response.status_code}: {error_msg}"
                )

            # Handle server errors (500+)
            if response.status_code >= 500:
                raise TrackerApiStatusError(
                    f"Jira server error {response.status_code}: {response.text[:200]}"
                )

            return response

        except requests.exceptions.Timeout as e:
            raise TrackerApiTimeoutError(
                f"Request timeout after {self._timeout}s: {e}"
            ) from e
        except requests.exceptions.ConnectionError as e:
            raise TrackerApiRequestError(f"Connection failed: {e}") from e
        except requests.exceptions.RequestException as e:
            raise TrackerApiRequestError(f"Request failed: {e}") from e

    def _parse_error_response(self, response: requests.Response) -> str:
        """Parse Jira ErrorCollection response.

        Args:
            response: Response object with JSON error body

        Returns:
            Parsed error message string
        """
        try:
            data = response.json()
            if "errorMessages" in data and data["errorMessages"]:
                return "; ".join(data["errorMessages"])
            if "errors" in data and data["errors"]:
                errors = [f"{k}: {v}" for k, v in data["errors"].items()]
                return "; ".join(errors)
        except Exception:
            pass
        return response.text[:500]

    @staticmethod
    def text_to_adf(text: str) -> Dict[str, Any]:
        """Convert plain text to Atlassian Document Format (ADF).

        Args:
            text: Plain text string

        Returns:
            ADF document structure
        """
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text}],
                }
            ],
        }

    def authenticate(self) -> Dict[str, Any]:
        """Validate credentials with Jira API.

        Calls GET /rest/api/3/myself to validate credentials
        and retrieve user information.

        Returns:
            User information dictionary

        Raises:
            TrackerApiStatusError: If credentials are invalid
        """
        response = self._request("GET", "/rest/api/3/myself")
        self._user = response.json()
        return self._user

    def fetch_issues(self, query: str) -> List[Dict[str, Any]]:
        """Fetch issues using JQL with pagination.

        Uses offset-based pagination via startAt/maxResults.
        Handles the 'total' field correctly (it's total matching issues, not per-page).

        Args:
            query: JQL query string

        Returns:
            List of issue dictionaries

        Raises:
            TrackerApiStatusError: On API errors
        """
        all_issues = []
        start_at = 0

        while True:
            response = self._request(
                "POST",
                "/rest/api/3/search/jql",
                data={
                    "jql": query,
                    "startAt": start_at,
                    "maxResults": MAX_RESULTS,
                    "fields": [
                        "key",
                        "summary",
                        "status",
                        "priority",
                        "created",
                        "updated",
                        "labels",
                        "assignee",
                        "description",
                        "components",
                    ],
                },
            )

            data = response.json()
            issues = data.get("issues", [])
            all_issues.extend(issues)

            total = data.get("total", 0)
            # Check if we've fetched all available issues
            if start_at + len(issues) >= total:
                break

            start_at += MAX_RESULTS

        return all_issues

    def get_issue(self, issue_id: str) -> Dict[str, Any]:
        """Get full issue details.

        Args:
            issue_id: Issue key (e.g., 'PROJ-123')

        Returns:
            Full issue dictionary with fields

        Raises:
            TrackerApiResourceNotFoundError: If issue not found
            TrackerApiStatusError: On other API errors
        """
        response = self._request(
            "GET",
            f"/rest/api/3/issue/{issue_id}",
            params={
                "fields": "summary,status,priority,assignee,labels,description,components,created,updated"
            },
        )
        return response.json()

    def update_issue(self, issue_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update issue fields.

        Args:
            issue_id: Issue key (e.g., 'PROJ-123')
            fields: Dictionary of fields to update

        Returns:
            Updated issue dictionary

        Raises:
            TrackerApiResourceNotFoundError: If issue not found
            TrackerApiStatusError: On other API errors
        """
        response = self._request(
            "PUT",
            f"/rest/api/3/issue/{issue_id}",
            data={"fields": fields},
        )
        # Handle 204 No Content response
        if response.status_code == 204:
            return {"success": True}
        return response.json()

    def add_comment(self, issue_id: str, body: str) -> Dict[str, Any]:
        """Add comment to issue.

        Converts plain text body to ADF format automatically.

        Args:
            issue_id: Issue key (e.g., 'PROJ-123')
            body: Comment text (plain text, will be converted to ADF)

        Returns:
            Created comment dictionary

        Raises:
            TrackerApiResourceNotFoundError: If issue not found
            TrackerApiStatusError: On other API errors
        """
        adf_body = self.text_to_adf(body)

        response = self._request(
            "POST",
            f"/rest/api/3/issue/{issue_id}/comment",
            data={"body": adf_body},
        )
        return response.json()

    def list_transitions(self, issue_id: str) -> List[Dict[str, Any]]:
        """Get available transitions for issue.

        Args:
            issue_id: Issue key (e.g., 'PROJ-123')

        Returns:
            List of transition dictionaries with id, name, and to fields

        Raises:
            TrackerApiResourceNotFoundError: If issue not found
            TrackerApiStatusError: On other API errors
        """
        response = self._request(
            "GET",
            f"/rest/api/3/issue/{issue_id}/transitions",
        )
        data = response.json()
        return data.get("transitions", [])

    def transition_issue(self, issue_id: str, transition_id: str) -> Dict[str, Any]:
        """Transition issue to new status.

        Args:
            issue_id: Issue key (e.g., 'PROJ-123')
            transition_id: Transition ID to execute

        Returns:
            Updated issue dictionary

        Raises:
            TrackerApiResourceNotFoundError: If issue not found
            TrackerApiStatusError: On other API errors
        """
        response = self._request(
            "POST",
            f"/rest/api/3/issue/{issue_id}/transitions",
            data={"transition": {"id": transition_id}},
        )
        # Handle 204 No Content response
        if response.status_code == 204:
            return {"success": True}
        return response.json()

    def fetch_candidate_issues(self) -> List[Dict[str, Any]]:
        """Fetch active issues from Jira.

        Fetches issues in active states (default: ["To Do", "In Progress"])
        that are candidates for dispatch.

        Returns:
            List of issue dictionaries with keys: id, identifier, title,
            state, priority, created_at, labels, blocked_by

        Raises:
            TrackerAPIError: If project_key is not configured
            TrackerApiStatusError: On API errors
        """
        if not self._project_key:
            raise TrackerAPIError("Jira tracker requires project_key to be configured")

        # Build JQL for active states
        states = ", ".join([f'"{s}"' for s in self._active_states])
        jql = f"project = {self._project_key} AND status IN ({states}) ORDER BY created DESC"

        issues = self.fetch_issues(jql)

        # Normalize to standard format
        return [self._normalize_jira_issue(issue) for issue in issues]

    def fetch_issues_by_states(self, state_names: List[str]) -> List[Dict[str, Any]]:
        """Fetch issues matching the specified states.

        Args:
            state_names: List of state names to filter by (e.g., ['To Do', 'In Progress'])

        Returns:
            List of issue dictionaries in the specified states

        Raises:
            TrackerAPIError: If project_key is not configured
            TrackerApiStatusError: On API errors
        """
        if not self._project_key:
            raise TrackerAPIError("Jira tracker requires project_key to be configured")

        if not state_names:
            return []

        # Build JQL with state filter
        states = ", ".join([f'"{s}"' for s in state_names])
        jql = f"project = {self._project_key} AND status IN ({states}) ORDER BY created DESC"

        issues = self.fetch_issues(jql)

        # Normalize to standard format
        return [self._normalize_jira_issue(issue) for issue in issues]

    def fetch_issue_states_by_ids(self, issue_ids: List[str]) -> Dict[str, str]:
        """Fetch current states for specific issues.

        Note:
            This method does not require project_key as it uses direct key lookup
            via JQL 'key IN (...)' which is more efficient than filtering by project.

        Args:
            issue_ids: List of issue keys to fetch states for
                      (e.g., ['PROJ-123', 'PROJ-456'])

        Returns:
            Dictionary mapping issue_key -> state_name

        Raises:
            TrackerApiStatusError: On API errors
        """
        if not issue_ids:
            return {}

        # Build JQL to fetch specific issues
        keys = ", ".join([f'"{k}"' for k in issue_ids])
        jql = f"key IN ({keys})"

        issues = self.fetch_issues(jql)

        # Map key to state name
        result = {}
        for issue in issues:
            key = issue.get("key")
            if key:
                status = issue.get("fields", {}).get("status", {})
                state_name = status.get("name", "") if status else ""
                result[key] = state_name

        return result

    def _normalize_jira_issue(self, raw_issue: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a Jira issue to the standard format.

        Extracts and transforms Jira-specific fields into the common format
        used by the TrackerClient interface.

        Args:
            raw_issue: Raw issue data from Jira REST API

        Returns:
            Normalized issue dictionary
        """
        fields = raw_issue.get("fields", {})

        # Extract labels
        labels = []
        raw_labels = fields.get("labels", [])
        if raw_labels:
            labels = [label.lower() for label in raw_labels]

        # Extract status/state
        status = fields.get("status", {})
        state = status.get("name", "").lower() if status else ""

        # Extract priority using NormalizationUtils
        raw_priority = fields.get("priority")
        if raw_priority:
            # Priority can be a string or an object with id/name
            if isinstance(raw_priority, dict):
                raw_priority = raw_priority.get("name")
        priority = NormalizationUtils._normalize_priority(raw_priority)

        # Extract assignee (blocked_by - issues that block this one)
        # Note: Jira doesn't have direct "blocked by" relationship,
        # this would require querying issue links
        blocked_by = []

        # Extract created/updated dates
        created_at = fields.get("created")
        updated_at = fields.get("updated")

        # Build normalized issue
        normalized = {
            "id": raw_issue.get("id", ""),
            "identifier": raw_issue.get("key", ""),
            "title": fields.get("summary", ""),
            "state": state,
            "priority": priority,
            "created_at": created_at,
            "updated_at": updated_at,
            "labels": labels,
            "blocked_by": blocked_by,
        }

        return NormalizationUtils.normalize_issue(normalized)

    def find_transition_by_status(self, issue_id: str, target_status: str) -> str:
        """Find transition ID for target status name.

        Args:
            issue_id: Issue key (e.g., 'PROJ-123')
            target_status: Target status name (e.g., 'Done')

        Returns:
            Transition ID

        Raises:
            TrackerAPIError: If no transition found for target status
        """
        transitions = self.list_transitions(issue_id)

        for transition in transitions:
            # Match by transition name or target status name
            transition_name = transition.get("name", "").lower()
            to_status = transition.get("to", {}).get("name", "").lower()
            target_lower = target_status.lower()

            if transition_name == target_lower or to_status == target_lower:
                transition_id = transition.get("id")
                if transition_id:
                    return transition_id

        available = [t.get("name") for t in transitions]
        raise TrackerAPIError(
            f"No transition found for status '{target_status}'. "
            f"Available transitions: {available}"
        )

    def move_to_status(self, issue_id: str, target_status: str) -> Dict[str, Any]:
        """Move issue to target status.

        Convenience method that finds the transition ID and executes it.

        Args:
            issue_id: Issue key (e.g., 'PROJ-123')
            target_status: Target status name (e.g., 'Done')

        Returns:
            Updated issue dictionary
        """
        transition_id = self.find_transition_by_status(issue_id, target_status)
        return self.transition_issue(issue_id, transition_id)
