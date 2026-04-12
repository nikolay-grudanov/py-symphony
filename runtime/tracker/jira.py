"""Jira REST API tracker adapter."""

from typing import Any, Dict, List, Optional

from .base import TrackerClient


class JiraTracker(TrackerClient):
    """Jira issue tracker adapter.

    Implements the TrackerClient interface for Jira's REST API.
    Currently a stub - see integrations/jira-adapter-spec.md for reference.
    """

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        project_key: str = "",
        username: str = "",
    ):
        """Initialize Jira tracker adapter.

        Args:
            api_key: Jira API token (or password for basic auth)
            endpoint: Jira instance URL (e.g., https://company.atlassian.net)
            project_key: Project key for filtering issues
            username: Username for basic authentication
        """
        self._api_key = api_key
        self._endpoint = endpoint.rstrip("/")
        self._project_key = project_key
        self._username = username

    @property
    def tracker_kind(self) -> str:
        """Return the tracker kind identifier."""
        return "jira"

    def fetch_candidate_issues(self) -> List[Dict[str, Any]]:
        """Fetch active issues from Jira.

        Returns:
            List of issue dictionaries with keys: id, identifier, title,
            state, priority, created_at, labels, blocked_by

        TODO: Implement - see integrations/jira-adapter-spec.md for REST API details.
              Requires:
              - JIRA_API_TOKEN environment variable
              - tracker_endpoint (Jira instance URL)
              - tracker_username (email for Jira Cloud)
              - tracker_project_slug (project key)
        """
        # TODO: Implement Jira REST API calls
        # Expected JQL: project = KEY AND status IN ("To Do", "In Progress")
        # Endpoint: GET /rest/api/3/search?jql=...
        return []

    def fetch_issues_by_states(self, state_names: List[str]) -> List[Dict[str, Any]]:
        """Fetch issues matching the specified states.

        Args:
            state_names: List of state names to filter by

        Returns:
            List of issue dictionaries in the specified states.

        TODO: Implement - JQL query with status filter.
              Example: status IN ("To Do", "In Progress", "Done")
        """
        # TODO: Implement Jira JQL query with state filter
        return []

    def fetch_issue_states_by_ids(self, issue_ids: List[str]) -> Dict[str, str]:
        """Fetch states for specific issues.

        Args:
            issue_ids: List of issue keys to fetch states for
                      (e.g., ['PROJ-123', 'PROJ-456'])

        Returns:
            Dictionary mapping issue_key -> state_name

        TODO: Implement - batch fetch using issue keys.
              Can use: GET /rest/api/3/search with ids param
        """
        # TODO: Implement Jira batch state lookup
        return {}
