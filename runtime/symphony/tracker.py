"""Issue tracker adapters - Abstract base + Linear implementation."""

import abc
import logging
from dataclasses import dataclass
from typing import Optional

import aiohttp

from .config import Config


logger = logging.getLogger(__name__)


# Domain models from SPEC.md Section 4.1.1
@dataclass
class Issue:
    """Normalized issue record."""

    id: str  # Linear internal UUID
    identifier: str  # Human ticket key (e.g., MT-123)
    title: str
    description: Optional[str]
    priority: Optional[int]  # Lower numbers = higher priority
    state: str
    branch_name: Optional[str]
    url: Optional[str]
    labels: list[str]  # Lowercase
    blocked_by: list[dict]  # [{id, identifier, state}]
    created_at: Optional[str]
    updated_at: Optional[str]


# Custom exceptions from SPEC.md Section 11.4
class TrackerError(Exception):
    """Base tracker error."""

    pass


class UnsupportedTrackerKind(TrackerError):
    """Unsupported tracker kind."""

    pass


class MissingTrackerApiKey(TrackerError):
    """Missing tracker API key."""

    pass


class MissingTrackerProjectSlug(TrackerError):
    """Missing tracker project slug."""

    pass


class LinearApiRequest(TrackerError):
    """Transport failures."""

    pass


class LinearApiStatus(TrackerError):
    """Non-200 HTTP response."""

    pass


class LinearGraphQLErrors(TrackerError):
    """GraphQL errors in response."""

    pass


class LinearUnknownPayload(TrackerError):
    """Malformed response payload."""

    pass


class LinearMissingEndCursor(TrackerError):
    """Pagination integrity error."""

    pass


class Tracker(abc.ABC):
    """Abstract base class for issue trackers."""

    @abc.abstractmethod
    async def fetch_candidate_issues(self) -> list[Issue]:
        """Fetch issues in active states for the configured project."""
        pass

    @abc.abstractmethod
    async def fetch_issues_by_states(self, states: list[str]) -> list[Issue]:
        """Fetch issues in specified states (for startup cleanup)."""
        pass

    @abc.abstractmethod
    async def fetch_issue_states(self, issue_ids: list[str]) -> dict[str, str]:
        """Fetch current states for specific issue IDs (for reconciliation)."""
        pass


class LinearTracker(Tracker):
    """Linear issue tracker adapter.

    Implements tracker adapter layer from SPEC.md Section 11.
    Uses GraphQL API with pagination support.
    """

    # GraphQL queries from SPEC.md Section 11.2
    CANDIDATE_QUERY = """
    query GetCandidates($projectSlug: String!, $states: [String!]!, $first: Int, $after: String) {
        issues(filter: { project: { slugId: { eq: $projectSlug } }, state: { name: { in: $states } } }, first: $first, after: $after) {
            nodes {
                id
                identifier
                title
                description
                priority
                state { name }
                branchName
                url
                labels(first: 20) { nodes { name } }
                createdAt
                updatedAt
            }
            pageInfo { hasNextPage endCursor }
        }
    }
    """

    STATE_QUERY = """
    query GetIssueStates($ids: [ID!]!) {
        nodes(ids: $ids) {
            ... on Issue {
                id
                state { name }
            }
        }
    }
    """

    RELATIONS_QUERY = """
    query GetIssueRelations($issueIds: [ID!]!) {
        nodes(ids: $issueIds) {
            ... on Issue {
                id
                blockedBy(first: 20) {
                    nodes {
                        id
                        identifier
                        state { name }
                    }
                }
            }
        }
    }
    """

    # Default pagination settings from SPEC.md
    DEFAULT_PAGE_SIZE = 50

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        project_slug: str,
        active_states: list[str],
        terminal_states: list[str],
    ):
        """Initialize Linear tracker adapter.

        Args:
            endpoint: GraphQL API endpoint URL
            api_key: Linear API key for authentication
            project_slug: Linear project slug ID for filtering
            active_states: List of active issue states
            terminal_states: List of terminal issue states
        """
        if not api_key:
            raise MissingTrackerApiKey("Linear API key is required")
        if not project_slug:
            raise MissingTrackerProjectSlug("Linear project slug is required")

        self.endpoint = endpoint
        self.api_key = api_key
        self.project_slug = project_slug
        self.active_states = active_states
        self.terminal_states = terminal_states
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _graphql_request(
        self,
        query: str,
        variables: dict,
    ) -> dict:
        """Execute GraphQL request with error handling.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Parsed response data

        Raises:
            LinearApiRequest: On transport failures
            LinearApiStatus: On non-200 HTTP response
            LinearGraphQLErrors: On GraphQL errors in response
        """
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            session = await self._get_session()
            async with session.post(
                self.endpoint,
                json={"query": query, "variables": variables},
                headers=headers,
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(
                        "Linear API error: status=%d body=%s",
                        resp.status,
                        error_text,
                    )
                    raise LinearApiStatus(
                        f"Linear API error: {resp.status} - {error_text}"
                    )

                data = await resp.json()

                if "errors" in data:
                    error_msg = str(data["errors"])
                    logger.error("GraphQL errors: %s", error_msg)
                    raise LinearGraphQLErrors(f"GraphQL errors: {error_msg}")

                return data.get("data", {})

        except aiohttp.ClientError as e:
            logger.error("Linear API transport error: %s", e)
            raise LinearApiRequest(f"Transport error: {e}") from e

    async def fetch_issue_relations(
        self, issue_ids: list[str]
    ) -> dict[str, list[dict]]:
        """Fetch blocked-by relations for multiple issues.

        Args:
            issue_ids: List of issue IDs to fetch relations for

        Returns:
            Dict mapping issue ID to list of blocker dicts with {id, identifier, state}
        """
        if not issue_ids:
            return {}

        try:
            data = await self._graphql_request(
                self.RELATIONS_QUERY, {"issueIds": issue_ids}
            )
        except (LinearApiRequest, LinearApiStatus, LinearGraphQLErrors) as e:
            logger.warning("Failed to fetch issue relations: %s", e)
            return {}

        result: dict[str, list[dict]] = {}
        nodes = data.get("nodes", [])

        for node in nodes:
            if node:
                issue_id = node.get("id", "")
                blocked_by_data = node.get("blockedBy", {}).get("nodes", [])

                blockers: list[dict] = []
                for blocker in blocked_by_data:
                    if blocker:
                        blocker_state = ""
                        if blocker.get("state"):
                            blocker_state = blocker["state"].get("name", "")

                        blockers.append(
                            {
                                "id": blocker.get("id", ""),
                                "identifier": blocker.get("identifier", ""),
                                "state": blocker_state,
                            }
                        )

                result[issue_id] = blockers

        logger.debug("Fetched relations for %d issues", len(result))
        return result

    async def fetch_candidate_issues(self) -> list[Issue]:
        """Fetch issues in active states with pagination.

        Returns:
            List of normalized Issue objects in active states

        Raises:
            LinearApiRequest: On transport failures
            LinearApiStatus: On non-200 HTTP response
            LinearGraphQLErrors: On GraphQL errors
            LinearMissingEndCursor: On pagination integrity error
        """
        all_issues: list[Issue] = []
        cursor: Optional[str] = None
        has_next_page = True

        while has_next_page:
            variables = {
                "projectSlug": self.project_slug,
                "states": self.active_states,
                "first": self.DEFAULT_PAGE_SIZE,
                "after": cursor,
            }

            data = await self._graphql_request(self.CANDIDATE_QUERY, variables)

            issues_data = data.get("issues", {})
            nodes = issues_data.get("nodes", [])
            page_info = issues_data.get("pageInfo", {})

            for node in nodes:
                issue = self._normalize_issue(node)
                if issue:
                    all_issues.append(issue)

            has_next_page = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")

            if has_next_page and not cursor:
                logger.error(
                    "Pagination integrity error: hasNextPage=true but no endCursor"
                )
                raise LinearMissingEndCursor("Missing endCursor in paginated response")

        # Fetch blocked-by relations in a separate query
        if all_issues:
            issue_ids = [issue.id for issue in all_issues]
            relations = await self.fetch_issue_relations(issue_ids)

            # Merge relations into issues
            for issue in all_issues:
                issue.blocked_by = relations.get(issue.id, [])

        logger.info(
            "Fetched %d candidate issues from project %s",
            len(all_issues),
            self.project_slug,
        )
        return all_issues

    async def fetch_issues_by_states(self, states: list[str]) -> list[Issue]:
        """Fetch issues in specified states (for startup cleanup).

        Args:
            states: List of state names to filter by

        Returns:
            List of normalized Issue objects in specified states
        """
        if not states:
            return []

        all_issues: list[Issue] = []
        cursor: Optional[str] = None
        has_next_page = True

        while has_next_page:
            variables = {
                "projectSlug": self.project_slug,
                "states": states,
                "first": self.DEFAULT_PAGE_SIZE,
                "after": cursor,
            }

            data = await self._graphql_request(self.CANDIDATE_QUERY, variables)

            issues_data = data.get("issues", {})
            nodes = issues_data.get("nodes", [])
            page_info = issues_data.get("pageInfo", {})

            for node in nodes:
                issue = self._normalize_issue(node)
                if issue:
                    all_issues.append(issue)

            has_next_page = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")

        logger.info(
            "Fetched %d issues in states %s from project %s",
            len(all_issues),
            states,
            self.project_slug,
        )
        return all_issues

    async def fetch_issue_states(self, issue_ids: list[str]) -> dict[str, str]:
        """Fetch current states for specific issue IDs.

        Used for active-run reconciliation.

        Args:
            issue_ids: List of issue IDs to fetch states for

        Returns:
            Dict mapping issue ID to state name

        Raises:
            LinearApiRequest: On transport failures
            LinearApiStatus: On non-200 HTTP response
            LinearGraphQLErrors: On GraphQL errors
        """
        if not issue_ids:
            return {}

        data = await self._graphql_request(self.STATE_QUERY, {"ids": issue_ids})

        result: dict[str, str] = {}
        nodes = data.get("nodes", [])

        for node in nodes:
            if node and "state" in node:
                result[node["id"]] = node["state"]["name"]

        logger.debug("Fetched states for %d issues", len(result))
        return result

    def _normalize_issue(
        self, node: Optional[dict], blocked_by: Optional[list[dict]] = None
    ) -> Optional[Issue]:
        """Normalize Linear issue to domain model.

        Implements normalization rules from SPEC.md Section 11.3:
        - labels -> lowercase strings
        - blocked_by -> derived from inverse relations
        - priority -> integer only (non-integers become null)
        - created_at/updated_at -> parse ISO-8601 timestamps

        Args:
            node: Raw issue data from Linear API
            blocked_by: Optional list of blocker dicts with {id, identifier, state}

        Returns:
            Normalized Issue or None if node is invalid
        """
        if not node:
            return None

        # Parse labels (lowercase per SPEC.md Section 11.3)
        labels: list[str] = []
        for label in node.get("labels", {}).get("nodes", []):
            if label and label.get("name"):
                labels.append(label["name"].lower())

        # Parse priority (integer only per SPEC.md Section 11.3)
        priority = node.get("priority")
        if priority is not None and not isinstance(priority, int):
            priority = None

        # Parse state
        state = ""
        if node.get("state"):
            state = node["state"].get("name", "")

        return Issue(
            id=node.get("id", ""),
            identifier=node.get("identifier", ""),
            title=node.get("title", ""),
            description=node.get("description"),
            priority=priority,
            state=state,
            branch_name=node.get("branchName"),
            url=node.get("url"),
            labels=labels,
            blocked_by=blocked_by or [],
            created_at=node.get("createdAt"),
            updated_at=node.get("updatedAt"),
        )


def create_tracker(config: Config) -> Tracker:
    """Factory function to create tracker from config.

    Args:
        config: Typed configuration object

    Returns:
        Tracker instance for the configured kind

    Raises:
        UnsupportedTrackerKind: If tracker kind is not supported
    """
    kind = config.tracker_kind

    if kind == "linear":
        return LinearTracker(
            endpoint=config.tracker_endpoint,
            api_key=config.tracker_api_key or "",
            project_slug=config.tracker_project_slug or "",
            active_states=config.tracker_active_states,
            terminal_states=config.tracker_terminal_states,
        )
    else:
        raise UnsupportedTrackerKind(f"Unsupported tracker kind: {kind}")
