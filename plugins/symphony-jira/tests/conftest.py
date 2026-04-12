"""Pytest fixtures for Jira adapter tests."""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

# Add runtime to path for imports
RUNTIME_PATH = str(Path(__file__).parent.parent.parent / "runtime")
if RUNTIME_PATH not in sys.path:
    sys.path.insert(0, RUNTIME_PATH)


# =============================================================================
# Mock Data Fixtures
# =============================================================================


@pytest.fixture
def mock_jira_issue() -> Dict[str, Any]:
    """Standard Jira API response for a single issue."""
    return {
        "id": "12345",
        "key": "PROJ-100",
        "self": "https://company.atlassian.net/rest/api/3/issue/12345",
        "fields": {
            "summary": "Test issue title",
            "status": {
                "name": "To Do",
                "statusCategory": {"key": "new", "name": "To Do"},
            },
            "priority": {
                "name": "High",
                "id": "2",
            },
            "assignee": {
                "accountId": "user123",
                "displayName": "John Doe",
                "emailAddress": "john@example.com",
            },
            "labels": ["bug", "urgent"],
            "created": "2026-04-01T10:00:00.000Z",
            "updated": "2026-04-02T15:30:00.000Z",
            "components": [],
            "description": None,
        },
    }


@pytest.fixture
def mock_jira_issue_null_assignee() -> Dict[str, Any]:
    """Jira issue with null assignee."""
    return {
        "id": "12346",
        "key": "PROJ-101",
        "self": "https://company.atlassian.net/rest/api/3/issue/12346",
        "fields": {
            "summary": "Issue with no assignee",
            "status": {
                "name": "In Progress",
                "statusCategory": {"key": "indeterminate", "name": "In Progress"},
            },
            "priority": {"name": "Medium", "id": "3"},
            "assignee": None,
            "labels": [],
            "created": "2026-04-01T10:00:00.000Z",
            "updated": "2026-04-02T15:30:00.000Z",
            "components": [],
            "description": None,
        },
    }


@pytest.fixture
def mock_jira_issue_null_priority() -> Dict[str, Any]:
    """Jira issue with null priority."""
    return {
        "id": "12347",
        "key": "PROJ-102",
        "self": "https://company.atlassian.net/rest/api/3/issue/12347",
        "fields": {
            "summary": "Issue with no priority",
            "status": {
                "name": "To Do",
                "statusCategory": {"key": "new", "name": "To Do"},
            },
            "priority": None,
            "assignee": {
                "accountId": "user123",
                "displayName": "John Doe",
            },
            "labels": [],
            "created": "2026-04-01T10:00:00.000Z",
            "updated": "2026-04-02T15:30:00.000Z",
            "components": [],
            "description": None,
        },
    }


@pytest.fixture
def mock_jira_search_response() -> Dict[str, Any]:
    """Jira search API response."""
    return {
        "startAt": 0,
        "maxResults": 50,
        "total": 2,
        "issues": [
            {
                "id": "12345",
                "key": "PROJ-100",
                "fields": {
                    "summary": "First issue",
                    "status": {"name": "To Do"},
                    "priority": {"name": "High"},
                    "assignee": None,
                    "labels": ["bug"],
                    "created": "2026-04-01T10:00:00.000Z",
                    "updated": "2026-04-02T15:30:00.000Z",
                },
            },
            {
                "id": "12346",
                "key": "PROJ-101",
                "fields": {
                    "summary": "Second issue",
                    "status": {"name": "In Progress"},
                    "priority": {"name": "Medium"},
                    "assignee": {"accountId": "user1", "displayName": "Jane"},
                    "labels": ["feature"],
                    "created": "2026-04-01T11:00:00.000Z",
                    "updated": "2026-04-02T16:30:00.000Z",
                },
            },
        ],
    }


@pytest.fixture
def mock_jira_search_response_empty() -> Dict[str, Any]:
    """Jira search response with empty results."""
    return {
        "startAt": 0,
        "maxResults": 50,
        "total": 0,
        "issues": [],
    }


@pytest.fixture
def mock_jira_search_response_paginated() -> Dict[str, Any]:
    """Paginated Jira search response (page 1 of 2)."""
    return {
        "startAt": 0,
        "maxResults": 50,
        "total": 75,
        "issues": [
            {
                "id": f"{12340 + i}",
                "key": f"PROJ-{100 + i}",
                "fields": {
                    "summary": f"Issue {i}",
                    "status": {"name": "To Do"},
                    "priority": {"name": "Medium"},
                    "assignee": None,
                    "labels": [],
                    "created": "2026-04-01T10:00:00.000Z",
                    "updated": "2026-04-02T15:30:00.000Z",
                },
            }
            for i in range(50)
        ],
    }


@pytest.fixture
def mock_jira_transitions() -> Dict[str, Any]:
    """Jira transitions response."""
    return {
        "transitions": [
            {
                "id": "11",
                "name": "To Do",
                "to": {"name": "To Do"},
            },
            {
                "id": "21",
                "name": "In Progress",
                "to": {"name": "In Progress"},
            },
            {
                "id": "31",
                "name": "Done",
                "to": {"name": "Done"},
            },
        ]
    }


@pytest.fixture
def mock_jira_myself_response() -> Dict[str, Any]:
    """Jira /myself API response."""
    return {
        "accountId": "user123",
        "displayName": "Test User",
        "emailAddress": "test@example.com",
        "active": True,
    }


@pytest.fixture
def mock_jira_comment_response() -> Dict[str, Any]:
    """Jira comment creation response."""
    return {
        "id": "10000",
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Test comment"}]}
            ],
        },
        "created": "2026-04-02T10:00:00.000Z",
    }


# =============================================================================
# Mock Adapter Fixtures
# =============================================================================


@pytest.fixture
def jira_adapter():
    """Create a JiraTracker instance with mock configuration.

    Returns:
        Initialized adapter with test config.
    """
    from runtime.tracker.jira import JiraTracker

    return JiraTracker(
        api_key="test-api-key",
        endpoint="https://company.atlassian.net",
        project_key="PROJ",
        username="test@example.com",
        timeout=30,
        active_states=["To Do", "In Progress"],
    )


@pytest.fixture
def plugin_jira_adapter():
    """Create a plugin JiraAdapter instance (template).

    Returns:
        Initialized plugin adapter (template).
    """
    try:
        from symphony_jira.adapter import JiraAdapter

        return JiraAdapter(
            api_key="test-api-key",
            endpoint="https://company.atlassian.net",
            project_key="PROJ",
            username="test@example.com",
            timeout=30,
            active_states=["To Do", "In Progress"],
        )
    except ImportError:
        # If plugin import fails, skip
        pytest.skip("symphony-jira plugin not installed")


# =============================================================================
# Mock HTTP Response Fixtures
# =============================================================================


class MockResponse:
    """Mock HTTP response for requests library."""

    def __init__(
        self,
        json_data: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        text: str = "",
    ):
        self._json_data = json_data
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text

    def json(self) -> Any:
        return self._json_data

    def raise_for_status(self) -> None:
        if 400 <= self.status_code < 600:
            raise Exception(f"HTTP {self.status_code}: {self.text}")


@pytest.fixture
def mock_response_success(mock_jira_issue) -> MockResponse:
    """Successful mock response."""
    return MockResponse(json_data=mock_jira_issue, status_code=200)


@pytest.fixture
def mock_response_404() -> MockResponse:
    """404 Not Found response."""
    return MockResponse(
        json_data={"errorMessages": ["Issue Does Not Exist"], "errors": {}},
        status_code=404,
        text="Issue Does Not Exist",
    )


@pytest.fixture
def mock_response_401() -> MockResponse:
    """401 Unauthorized response."""
    return MockResponse(
        json_data={"errorMessages": ["Unauthorized"], "errors": {}},
        status_code=401,
        text="Unauthorized",
    )


@pytest.fixture
def mock_response_429() -> MockResponse:
    """429 Rate Limit response."""
    return MockResponse(
        json_data={"errorMessages": ["Rate limit exceeded"], "errors": {}},
        status_code=429,
        headers={"Retry-After": "5"},
        text="Rate limit exceeded",
    )


@pytest.fixture
def mock_response_204() -> MockResponse:
    """204 No Content response."""
    return MockResponse(json_data=None, status_code=204)


@pytest.fixture
def mock_response_201(mock_jira_comment_response) -> MockResponse:
    """201 Created response for comments."""
    return MockResponse(json_data=mock_jira_comment_response, status_code=201)
