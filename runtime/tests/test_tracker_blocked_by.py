"""Tests for blocked_by relation fetching in Linear tracker."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from symphony.tracker import LinearTracker, Issue


class MockLinearTracker(LinearTracker):
    """Test subclass that allows overriding _graphql_request easily.

    Note: _graphql_request returns data.get('data', {}) from the raw API response,
    so mock responses should contain the extracted data (e.g., {"nodes": [...]}),
    NOT the wrapped response (e.g., {"data": {"nodes": [...]}}).
    """

    def __init__(self, mock_responses=None):
        super().__init__(
            endpoint="https://api.linear.app/graphql",
            api_key="test_key",
            project_slug="test-project",
            active_states=["Todo", "In Progress"],
            terminal_states=["Done", "Cancelled"],
        )
        self._mock_responses = mock_responses or []
        self._call_count = 0

    async def _graphql_request(self, query, variables):
        if self._mock_responses:
            response = self._mock_responses[
                self._call_count % len(self._mock_responses)
            ]
            self._call_count += 1
            return response
        return {"nodes": []}


class TestFetchIssueRelations:
    """Tests for fetch_issue_relations method."""

    def test_fetch_issue_relations_returns_blockers(self):
        """Test that relations query returns blocker data with correct structure."""
        # This is what _graphql_request returns after data.get('data', {})
        mock_response = {
            "nodes": [
                {
                    "id": "issue-1",
                    "blockedBy": {
                        "nodes": [
                            {
                                "id": "blocker-1",
                                "identifier": "PROJ-100",
                                "state": {"name": "In Progress"},
                            }
                        ]
                    },
                }
            ]
        }

        tracker = MockLinearTracker([mock_response])

        result = asyncio.run(tracker.fetch_issue_relations(["issue-1"]))

        assert "issue-1" in result
        assert len(result["issue-1"]) == 1
        assert result["issue-1"][0]["id"] == "blocker-1"
        assert result["issue-1"][0]["identifier"] == "PROJ-100"
        assert result["issue-1"][0]["state"] == "In Progress"

    def test_fetch_issue_relations_empty_list_when_no_blockers(self):
        """Test that empty list is returned when no blockers exist."""
        mock_response = {"nodes": [{"id": "issue-1", "blockedBy": {"nodes": []}}]}

        tracker = MockLinearTracker([mock_response])

        result = asyncio.run(tracker.fetch_issue_relations(["issue-1"]))

        assert "issue-1" in result
        assert result["issue-1"] == []

    def test_fetch_issue_relations_multiple_blockers(self):
        """Test that multiple blockers are returned correctly."""
        mock_response = {
            "nodes": [
                {
                    "id": "issue-1",
                    "blockedBy": {
                        "nodes": [
                            {
                                "id": "blocker-1",
                                "identifier": "PROJ-100",
                                "state": {"name": "In Progress"},
                            },
                            {
                                "id": "blocker-2",
                                "identifier": "PROJ-101",
                                "state": {"name": "Todo"},
                            },
                        ]
                    },
                }
            ]
        }

        tracker = MockLinearTracker([mock_response])

        result = asyncio.run(tracker.fetch_issue_relations(["issue-1"]))

        assert len(result["issue-1"]) == 2
        assert result["issue-1"][0]["identifier"] == "PROJ-100"
        assert result["issue-1"][1]["identifier"] == "PROJ-101"


class TestFetchIssueRelationsErrors:
    """Tests for error handling in fetch_issue_relations."""

    def test_fetch_issue_relations_api_failure_returns_empty_dict(self):
        """Test that API request failure returns empty dict (no crash)."""
        from symphony.tracker import LinearApiRequest

        class FailingTracker(LinearTracker):
            async def _graphql_request(self, query, variables):
                raise LinearApiRequest("Network error")

        tracker = FailingTracker(
            endpoint="https://api.linear.app/graphql",
            api_key="test_key",
            project_slug="test-project",
            active_states=["Todo", "In Progress"],
            terminal_states=["Done", "Cancelled"],
        )

        result = asyncio.run(tracker.fetch_issue_relations(["issue-1"]))

        assert result == {}

    def test_fetch_issue_relations_status_error_returns_empty_dict(self):
        """Test that non-200 HTTP response returns empty dict."""
        from symphony.tracker import LinearApiStatus

        class FailingTracker(LinearTracker):
            async def _graphql_request(self, query, variables):
                raise LinearApiStatus("Status 500")

        tracker = FailingTracker(
            endpoint="https://api.linear.app/graphql",
            api_key="test_key",
            project_slug="test-project",
            active_states=["Todo", "In Progress"],
            terminal_states=["Done", "Cancelled"],
        )

        result = asyncio.run(tracker.fetch_issue_relations(["issue-1"]))

        assert result == {}

    def test_fetch_issue_relations_graphql_error_returns_empty_dict(self):
        """Test that GraphQL errors return empty dict."""
        from symphony.tracker import LinearGraphQLErrors

        class FailingTracker(LinearTracker):
            async def _graphql_request(self, query, variables):
                raise LinearGraphQLErrors("GraphQL error")

        tracker = FailingTracker(
            endpoint="https://api.linear.app/graphql",
            api_key="test_key",
            project_slug="test-project",
            active_states=["Todo", "In Progress"],
            terminal_states=["Done", "Cancelled"],
        )

        result = asyncio.run(tracker.fetch_issue_relations(["issue-1"]))

        assert result == {}

    def test_fetch_issue_relations_empty_issue_ids_returns_empty_dict(self):
        """Test that empty issue_ids returns empty dict."""
        tracker = MockLinearTracker()

        result = asyncio.run(tracker.fetch_issue_relations([]))

        assert result == {}

    def test_fetch_issue_relations_handles_missing_nodes(self):
        """Test that missing nodes in response are handled gracefully."""
        mock_response = {}

        tracker = MockLinearTracker([mock_response])

        result = asyncio.run(tracker.fetch_issue_relations(["issue-1"]))

        assert result == {}

    def test_fetch_issue_relations_status_error_returns_empty_dict(self):
        """Test that non-200 HTTP response returns empty dict."""
        from symphony.tracker import LinearApiStatus

        class FailingTracker(MockLinearTracker):
            async def _graphql_request(self, query, variables):
                raise LinearApiStatus("Status 500")

        tracker = FailingTracker()

        result = asyncio.run(tracker.fetch_issue_relations(["issue-1"]))

        assert result == {}

    def test_fetch_issue_relations_graphql_error_returns_empty_dict(self):
        """Test that GraphQL errors return empty dict."""
        from symphony.tracker import LinearGraphQLErrors

        class FailingTracker(MockLinearTracker):
            async def _graphql_request(self, query, variables):
                raise LinearGraphQLErrors("GraphQL error")

        tracker = FailingTracker()

        result = asyncio.run(tracker.fetch_issue_relations(["issue-1"]))

        assert result == {}

    def test_fetch_issue_relations_empty_issue_ids_returns_empty_dict(self):
        """Test that empty issue_ids returns empty dict."""
        tracker = MockLinearTracker()

        result = asyncio.run(tracker.fetch_issue_relations([]))

        assert result == {}

    def test_fetch_issue_relations_handles_missing_nodes(self):
        """Test that missing nodes in response are handled gracefully."""
        mock_response = {}

        tracker = MockLinearTracker([mock_response])

        result = asyncio.run(tracker.fetch_issue_relations(["issue-1"]))

        assert result == {}


class TestFetchCandidateIssuesBlockedBy:
    """Tests for blocked_by population in fetch_candidate_issues."""

    def test_fetch_candidate_issues_populates_blocked_by(self):
        """Test that after fetching candidates, issues have blocked_by field populated."""
        # This is what _graphql_request returns after data.get('data', {})
        candidate_response = {
            "issues": {
                "nodes": [
                    {
                        "id": "issue-1",
                        "identifier": "PROJ-1",
                        "title": "Test issue",
                        "description": None,
                        "priority": 1,
                        "state": {"name": "In Progress"},
                        "branchName": "feature/test",
                        "url": "https://linear.app/PROJ-1",
                        "labels": {"nodes": []},
                        "createdAt": "2024-01-01T00:00:00Z",
                        "updatedAt": "2024-01-01T00:00:00Z",
                    }
                ],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }

        relations_response = {
            "nodes": [
                {
                    "id": "issue-1",
                    "blockedBy": {
                        "nodes": [
                            {
                                "id": "blocker-1",
                                "identifier": "PROJ-100",
                                "state": {"name": "In Progress"},
                            }
                        ]
                    },
                }
            ]
        }

        tracker = MockLinearTracker([candidate_response, relations_response])

        issues = asyncio.run(tracker.fetch_candidate_issues())

        assert len(issues) == 1
        assert issues[0].id == "issue-1"
        assert len(issues[0].blocked_by) == 1
        assert issues[0].blocked_by[0]["id"] == "blocker-1"
        assert issues[0].blocked_by[0]["identifier"] == "PROJ-100"

    def test_fetch_candidate_issues_no_blockers_empty_list(self):
        """Test that issues without blockers have empty list."""
        candidate_response = {
            "issues": {
                "nodes": [
                    {
                        "id": "issue-1",
                        "identifier": "PROJ-1",
                        "title": "Test issue",
                        "description": None,
                        "priority": 1,
                        "state": {"name": "Todo"},
                        "branchName": None,
                        "url": "https://linear.app/PROJ-1",
                        "labels": {"nodes": []},
                        "createdAt": "2024-01-01T00:00:00Z",
                        "updatedAt": "2024-01-01T00:00:00Z",
                    }
                ],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }

        relations_response = {"nodes": [{"id": "issue-1", "blockedBy": {"nodes": []}}]}

        tracker = MockLinearTracker([candidate_response, relations_response])

        issues = asyncio.run(tracker.fetch_candidate_issues())

        assert len(issues) == 1
        assert issues[0].blocked_by == []

    def test_fetch_candidate_issues_no_issues_returns_empty_list(self):
        """Test that when no issues, blocked_by query is not called."""
        candidate_response = {
            "data": {
                "issues": {
                    "nodes": [],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        }

        tracker = MockLinearTracker([candidate_response])

        issues = asyncio.run(tracker.fetch_candidate_issues())

        assert issues == []


class TestNormalizeIssueBlockedBy:
    """Tests for _normalize_issue blocked_by parameter handling."""

    @pytest.fixture
    def tracker(self):
        """Create tracker instance."""
        tracker = LinearTracker(
            endpoint="https://api.linear.app/graphql",
            api_key="test_key",
            project_slug="test-project",
            active_states=["Todo", "In Progress"],
            terminal_states=["Done", "Cancelled"],
        )
        return tracker

    def test_normalize_issue_accepts_blocked_by_parameter(self, tracker):
        """Test that blocked_by is correctly passed through normalization."""
        node = {
            "id": "issue-1",
            "identifier": "PROJ-1",
            "title": "Test issue",
            "description": None,
            "priority": 1,
            "state": {"name": "In Progress"},
            "branchName": "feature/test",
            "url": "https://linear.app/PROJ-1",
            "labels": {"nodes": []},
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z",
        }

        blocked_by = [
            {"id": "blocker-1", "identifier": "PROJ-100", "state": "In Progress"},
            {"id": "blocker-2", "identifier": "PROJ-101", "state": "Todo"},
        ]

        issue = tracker._normalize_issue(node, blocked_by=blocked_by)

        assert issue is not None
        assert issue.id == "issue-1"
        assert len(issue.blocked_by) == 2
        assert issue.blocked_by[0]["id"] == "blocker-1"
        assert issue.blocked_by[1]["identifier"] == "PROJ-101"

    def test_normalize_issue_default_blocked_by_empty_list(self, tracker):
        """Test that blocked_by defaults to empty list when not provided."""
        node = {
            "id": "issue-1",
            "identifier": "PROJ-1",
            "title": "Test issue",
            "description": None,
            "priority": 1,
            "state": {"name": "In Progress"},
            "branchName": "feature/test",
            "url": "https://linear.app/PROJ-1",
            "labels": {"nodes": []},
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z",
        }

        issue = tracker._normalize_issue(node)

        assert issue is not None
        assert issue.blocked_by == []

    def test_normalize_issue_accepts_none_blocked_by(self, tracker):
        """Test that blocked_by can be explicitly None."""
        node = {
            "id": "issue-1",
            "identifier": "PROJ-1",
            "title": "Test issue",
            "description": None,
            "priority": 1,
            "state": {"name": "In Progress"},
            "branchName": "feature/test",
            "url": "https://linear.app/PROJ-1",
            "labels": {"nodes": []},
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z",
        }

        issue = tracker._normalize_issue(node, blocked_by=None)

        assert issue is not None
        assert issue.blocked_by == []
