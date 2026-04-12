"""Tests for compatibility layer."""

import asyncio
import pytest
from unittest.mock import MagicMock

from runtime.symphony.tracker import Issue
from runtime.tracker.compat import AsyncTrackerWrapper
from runtime.tracker.base import TrackerClient


@pytest.fixture
def mock_new_tracker():
    """Mock new tracker client."""
    tracker = MagicMock(spec=TrackerClient)
    tracker.tracker_kind = "linear"
    return tracker


@pytest.fixture
def async_wrapper(mock_new_tracker):
    """Async wrapper instance."""
    return AsyncTrackerWrapper(mock_new_tracker)


def test_fetch_candidate_issues(async_wrapper, mock_new_tracker):
    """Test fetching candidate issues."""
    # Mock new tracker response (dict format)
    mock_new_tracker.fetch_candidate_issues.return_value = [
        {
            "id": "issue-1",
            "identifier": "TEST-1",
            "title": "Test Issue",
            "description": "Test description",
            "priority": 1,
            "state": "Todo",
            "branch_name": "branch-1",
            "url": "https://example.com/issue-1",
            "labels": ["bug"],
            "blocked_by": [],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
    ]

    # Call async wrapper
    result = asyncio.run(async_wrapper.fetch_candidate_issues())

    # Verify result is Issue dataclass
    assert len(result) == 1
    assert isinstance(result[0], Issue)
    assert result[0].identifier == "TEST-1"
    assert result[0].title == "Test Issue"


def test_fetch_issues_by_states(async_wrapper, mock_new_tracker):
    """Test fetching issues by states."""
    states = ["Done", "Cancelled"]

    mock_new_tracker.fetch_issues_by_states.return_value = [
        {
            "id": "issue-2",
            "identifier": "TEST-2",
            "title": "Done Issue",
            "state": "Done",
            "labels": [],
            "blocked_by": [],
        }
    ]

    result = asyncio.run(async_wrapper.fetch_issues_by_states(states))

    assert len(result) == 1
    assert result[0].state == "Done"
    mock_new_tracker.fetch_issues_by_states.assert_called_once_with(states)


def test_fetch_issue_states(async_wrapper, mock_new_tracker):
    """Test fetching issue states."""
    issue_ids = ["issue-1", "issue-2"]

    mock_new_tracker.fetch_issue_states_by_ids.return_value = {
        "issue-1": "In Progress",
        "issue-2": "Todo",
    }

    result = asyncio.run(async_wrapper.fetch_issue_states(issue_ids))

    assert result["issue-1"] == "In Progress"
    assert result["issue-2"] == "Todo"
    mock_new_tracker.fetch_issue_states_by_ids.assert_called_once_with(issue_ids)


def test_dict_to_issue_conversion(async_wrapper):
    """Test dict to Issue dataclass conversion."""
    issue_dict = {
        "id": "test-id",
        "identifier": "TEST-123",
        "title": "Test Title",
        "description": "Test Description",
        "priority": 2,
        "state": "In Progress",
        "branch_name": "test-branch",
        "url": "https://example.com/test",
        "labels": ["feature", "enhancement"],
        "blocked_by": [{"id": "blocker-1", "identifier": "BLOCKER-1", "state": "Todo"}],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
    }

    issue = async_wrapper._dict_to_issue(issue_dict)

    assert isinstance(issue, Issue)
    assert issue.id == "test-id"
    assert issue.identifier == "TEST-123"
    assert issue.title == "Test Title"
    assert issue.description == "Test Description"
    assert issue.priority == 2
    assert issue.state == "In Progress"
    assert issue.branch_name == "test-branch"
    assert issue.url == "https://example.com/test"
    assert issue.labels == ["feature", "enhancement"]
    assert len(issue.blocked_by) == 1
    assert issue.blocked_by[0]["identifier"] == "BLOCKER-1"


def test_dict_to_issue_with_missing_fields(async_wrapper):
    """Test dict to Issue conversion with missing optional fields."""
    issue_dict = {
        "id": "test-id",
        "identifier": "TEST-123",
        "title": "Test Title",
        "state": "Todo",
        "labels": [],
        "blocked_by": [],
    }

    issue = async_wrapper._dict_to_issue(issue_dict)

    assert issue.id == "test-id"
    assert issue.description is None
    assert issue.priority is None
    assert issue.branch_name is None
    assert issue.url is None


def test_fetch_candidate_issues_empty(async_wrapper, mock_new_tracker):
    """Test fetching candidate issues with empty result."""
    mock_new_tracker.fetch_candidate_issues.return_value = []

    result = asyncio.run(async_wrapper.fetch_candidate_issues())

    assert result == []
    assert len(result) == 0


def test_fetch_issues_by_states_empty(async_wrapper, mock_new_tracker):
    """Test fetching issues by states with empty result."""
    states = ["Done"]
    mock_new_tracker.fetch_issues_by_states.return_value = []

    result = asyncio.run(async_wrapper.fetch_issues_by_states(states))

    assert result == []


def test_fetch_issue_states_empty(async_wrapper, mock_new_tracker):
    """Test fetching issue states with empty result."""
    issue_ids = []
    mock_new_tracker.fetch_issue_states_by_ids.return_value = {}

    result = asyncio.run(async_wrapper.fetch_issue_states(issue_ids))

    assert result == {}


def test_dict_to_issue_minimal(async_wrapper):
    """Test dict to Issue conversion with minimal required fields."""
    issue_dict = {
        "id": "minimal-id",
        "identifier": "MINIMAL-1",
        "title": "Minimal Issue",
        "state": "Todo",
        "labels": [],
        "blocked_by": [],
    }

    issue = async_wrapper._dict_to_issue(issue_dict)

    assert issue.id == "minimal-id"
    assert issue.identifier == "MINIMAL-1"
    assert issue.title == "Minimal Issue"
    assert issue.state == "Todo"
    assert issue.labels == []
    assert issue.blocked_by == []
