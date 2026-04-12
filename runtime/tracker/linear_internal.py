"""Linear GraphQL tracker adapter.

This module contains the full Linear tracker implementation.
The runtime/tracker/linear.py module re-exports this for backwards compatibility.
This allows the plugin to import from runtime.tracker.base without circular imports.
"""

from typing import Any, Dict, List, Optional

import requests

from .base import TrackerClient
from .factory import (
    TrackerAPIError,
    TrackerApiRequestError,
    TrackerApiStatusError,
    TrackerApiRateLimitError,
    TrackerApiTimeoutError,
)
from .normalization import NormalizationUtils


# Default active states for candidate issues
DEFAULT_ACTIVE_STATES = ["Todo", "In Progress"]

# Linear GraphQL API endpoint
LINEAR_ENDPOINT = "https://api.linear.app/graphql"

# Page size for pagination
ISSUE_PAGE_SIZE = 50
RELATION_PAGE_SIZE = 50

# Request timeout
DEFAULT_TIMEOUT_SECONDS = 30


class LinearTracker(TrackerClient):
    """Linear issue tracker adapter.

    Implements the TrackerClient interface for Linear's GraphQL API.
    """

    def __init__(
        self,
        api_key: str,
        project_slug: Optional[str] = None,
        active_states: Optional[List[str]] = None,
        endpoint: str = LINEAR_ENDPOINT,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ):
        """Initialize Linear tracker adapter.

        Args:
            api_key: Linear API key
            project_slug: Optional project identifier for filtering
            active_states: Optional list of active states for candidate issues
            endpoint: Linear GraphQL API endpoint (default: https://api.linear.app/graphql)
            timeout_seconds: Request timeout in seconds (default: 30)
        """
        self._api_key = api_key
        self._project_slug = project_slug
        self._active_states = active_states or DEFAULT_ACTIVE_STATES
        self._endpoint = endpoint
        self._timeout_seconds = timeout_seconds

    @property
    def tracker_kind(self) -> str:
        """Return the tracker kind identifier."""
        return "linear"

    def _graphql_query(
        self,
        query: str,
        variables: Dict[str, Any],
        operation_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a GraphQL query against Linear API.

        Args:
            query: GraphQL query string
            variables: Query variables
            operation_name: Optional operation name

        Returns:
            GraphQL response data

        Raises:
            TrackerApiRequestError: On network/transport errors
            TrackerApiStatusError: On non-200 HTTP responses
            TrackerApiRateLimitError: On rate limiting (429)
            TrackerApiTimeoutError: On request timeout
            TrackerAPIError: On other API errors
        """
        payload: Dict[str, Any] = {"query": query, "variables": variables}
        if operation_name:
            payload["operationName"] = operation_name

        headers = {
            "Authorization": self._api_key,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self._endpoint,
                json=payload,
                headers=headers,
                timeout=self._timeout_seconds,
            )

            if response.status_code == 429:
                raise TrackerApiRateLimitError("Linear API rate limit exceeded (429)")

            if response.status_code != 200:
                body = response.text
                raise TrackerApiStatusError(
                    f"Linear API returned status {response.status_code}: {body[:500]}"
                )

            data = response.json()

            # Check for GraphQL errors
            if "errors" in data:
                error_messages = [
                    err.get("message", "Unknown error") for err in data["errors"]
                ]
                raise TrackerAPIError(
                    f"Linear GraphQL errors: {'; '.join(error_messages)}"
                )

            return data

        except requests.exceptions.Timeout as e:
            raise TrackerApiTimeoutError(f"Linear API timeout: {e}") from e
        except requests.exceptions.RequestException as e:
            raise TrackerApiRequestError(f"Linear API request failed: {e}") from e

    def _normalize_linear_issue(self, raw_issue: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a Linear issue to the standard format.

        Extracts and transforms Linear-specific fields into the common format.

        Args:
            raw_issue: Raw issue data from Linear GraphQL

        Returns:
            Normalized issue dictionary
        """
        # Extract labels from nested structure
        labels = []
        if raw_issue.get("labels") and raw_issue["labels"].get("nodes"):
            labels = [
                label.get("name", "").lower()
                for label in raw_issue["labels"]["nodes"]
                if label.get("name")
            ]

        # Extract blockers from inverseRelations (type: "blocks")
        blocked_by = []
        if raw_issue.get("inverseRelations") and raw_issue["inverseRelations"].get(
            "nodes"
        ):
            for relation in raw_issue["inverseRelations"]["nodes"]:
                if relation.get("type", "").lower() == "blocks" and relation.get(
                    "issue"
                ):
                    blocker = relation["issue"]
                    blocked_by.append(
                        {
                            "id": blocker.get("id", ""),
                            "identifier": blocker.get("identifier", ""),
                            "state": blocker.get("state", {}).get("name", "").lower()
                            if blocker.get("state")
                            else "",
                        }
                    )

        # Build normalized issue with Linear-specific structure
        normalized = {
            "id": raw_issue.get("id", ""),
            "identifier": raw_issue.get("identifier", ""),
            "title": raw_issue.get("title", ""),
            "state": raw_issue.get("state", {}).get("name", "").lower()
            if raw_issue.get("state")
            else "",
            "priority": raw_issue.get("priority"),
            "created_at": raw_issue.get("createdAt"),
            "updated_at": raw_issue.get("updatedAt"),
            "labels": labels,
            "blocked_by": blocked_by,
        }

        # Use NormalizationUtils for final processing
        return NormalizationUtils.normalize_issue(normalized)

    def _fetch_issues_by_states_page(
        self,
        state_names: List[str],
        after_cursor: Optional[str] = None,
    ) -> tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Fetch a single page of issues by states.

        Args:
            state_names: List of state names to filter by
            after_cursor: Optional pagination cursor

        Returns:
            Tuple of (issues list, page_info dict or None if no more pages)
        """
        query = """
        query SymphonyLinearPoll($projectSlug: String!, $stateNames: [String!]!, $first: Int!, $relationFirst: Int!, $after: String) {
          issues(filter: {project: {slugId: {eq: $projectSlug}}, state: {name: {in: $stateNames}}}, first: $first, after: $after) {
            nodes {
              id
              identifier
              title
              description
              priority
              state {
                name
              }
              branchName
              url
              assignee {
                id
              }
              labels {
                nodes {
                  name
                }
              }
              inverseRelations(first: $relationFirst) {
                nodes {
                  type
                  issue {
                    id
                    identifier
                    state {
                      name
                    }
                  }
                }
              }
              createdAt
              updatedAt
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
        """

        variables = {
            "projectSlug": self._project_slug,
            "stateNames": state_names,
            "first": ISSUE_PAGE_SIZE,
            "relationFirst": RELATION_PAGE_SIZE,
            "after": after_cursor,
        }

        response = self._graphql_query(query, variables, "SymphonyLinearPoll")

        if "data" not in response or "issues" not in response.get("data", {}):
            raise TrackerAPIError("Invalid response structure from Linear API")

        issues_data = response["data"]["issues"]
        nodes = issues_data.get("nodes", [])
        page_info = issues_data.get("pageInfo", {})

        # Normalize each issue
        issues = [self._normalize_linear_issue(issue) for issue in nodes]

        # Determine if there are more pages
        if page_info.get("hasNextPage") and page_info.get("endCursor"):
            return issues, page_info
        else:
            return issues, None

    def fetch_issues_by_states(self, state_names: List[str]) -> List[Dict[str, Any]]:
        """Fetch issues matching the specified states.

        Args:
            state_names: List of state names to filter by

        Returns:
            List of issue dictionaries in the specified states.

        Raises:
            TrackerConfigError: If project_slug is not configured
            TrackerAPIError: On API errors
        """
        if not self._project_slug:
            raise TrackerAPIError(
                "Linear tracker requires project_slug to be configured"
            )

        if not state_names:
            return []

        # Normalize state names
        normalized_states = list(set(state_names))

        all_issues = []
        cursor = None

        # Paginate through all results
        while True:
            issues, page_info = self._fetch_issues_by_states_page(
                normalized_states, cursor
            )
            all_issues.extend(issues)

            if page_info is None:
                break

            cursor = page_info.get("endCursor")

        return all_issues

    def fetch_issue_states_by_ids(self, issue_ids: List[str]) -> Dict[str, str]:
        """Fetch states for specific issues.

        Args:
            issue_ids: List of issue identifiers to fetch states for

        Returns:
            Dictionary mapping issue_id -> state_name

        Raises:
            TrackerConfigError: If project_slug is not configured
            TrackerAPIError: On API errors
        """
        if not self._project_slug:
            raise TrackerAPIError(
                "Linear tracker requires project_slug to be configured"
            )

        if not issue_ids:
            return {}

        # Deduplicate issue IDs
        unique_ids = list(set(issue_ids))

        query = """
        query SymphonyLinearIssuesById($ids: [ID!]!, $first: Int!, $relationFirst: Int!) {
          issues(filter: {id: {in: $ids}}, first: $first) {
            nodes {
              id
              identifier
              title
              state {
                name
              }
              priority
              createdAt
              updatedAt
              labels {
                nodes {
                  name
                }
              }
              inverseRelations(first: $relationFirst) {
                nodes {
                  type
                  issue {
                    id
                    identifier
                    state {
                      name
                    }
                  }
                }
              }
            }
          }
        }
        """

        # Linear API has a limit on IDs per query, so batch if needed
        result: Dict[str, str] = {}

        # Process in batches
        for i in range(0, len(unique_ids), ISSUE_PAGE_SIZE):
            batch_ids = unique_ids[i : i + ISSUE_PAGE_SIZE]

            variables = {
                "ids": batch_ids,
                "first": len(batch_ids),
                "relationFirst": RELATION_PAGE_SIZE,
            }

            response = self._graphql_query(query, variables, "SymphonyLinearIssuesById")

            if "data" not in response or "issues" not in response.get("data", {}):
                continue

            nodes = response["data"]["issues"].get("nodes", [])

            for issue in nodes:
                issue_id = issue.get("id")
                if issue_id:
                    state_name = ""
                    if issue.get("state") and issue["state"].get("name"):
                        state_name = issue["state"]["name"].lower()
                    result[issue_id] = state_name

        return result

    def fetch_candidate_issues(self) -> List[Dict[str, Any]]:
        """Fetch active issues from Linear.

        Fetches issues in active states (default: ["Todo", "In Progress"])
        that are candidates for dispatch.

        Returns:
            List of issue dictionaries with keys: id, identifier, title,
            state, priority, created_at, labels, blocked_by

        Raises:
            TrackerConfigError: If project_slug is not configured
            TrackerAPIError: On API errors
        """
        if not self._project_slug:
            raise TrackerAPIError(
                "Linear tracker requires project_slug to be configured"
            )

        return self.fetch_issues_by_states(self._active_states)
