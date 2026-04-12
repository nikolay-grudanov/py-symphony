"""Comprehensive tests for the deprecated built-in Jira adapter (runtime/tracker/jira.py).

These tests verify the fully implemented JiraTracker adapter.
"""

import base64
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# Fixtures - Reusable mock data
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
            "priority": {"name": "High", "id": "2"},
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
            "status": {"name": "In Progress"},
            "priority": {"name": "Medium"},
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
            "status": {"name": "To Do"},
            "priority": None,
            "assignee": {"accountId": "user123", "displayName": "John Doe"},
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
    return {"startAt": 0, "maxResults": 50, "total": 0, "issues": []}


@pytest.fixture
def mock_jira_search_paginated_page1() -> Dict[str, Any]:
    """Paginated response - first page."""
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
def mock_jira_search_paginated_page2() -> Dict[str, Any]:
    """Paginated response - second page."""
    return {
        "startAt": 50,
        "maxResults": 50,
        "total": 75,
        "issues": [
            {
                "id": f"{12390 + i}",
                "key": f"PROJ-{150 + i}",
                "fields": {
                    "summary": f"Issue {50 + i}",
                    "status": {"name": "To Do"},
                    "priority": {"name": "Medium"},
                    "assignee": None,
                    "labels": [],
                    "created": "2026-04-01T10:00:00.000Z",
                    "updated": "2026-04-02T15:30:00.000Z",
                },
            }
            for i in range(25)
        ],
    }


@pytest.fixture
def mock_jira_transitions() -> Dict[str, Any]:
    """Jira transitions response."""
    return {
        "transitions": [
            {"id": "11", "name": "To Do", "to": {"name": "To Do"}},
            {"id": "21", "name": "In Progress", "to": {"name": "In Progress"}},
            {"id": "31", "name": "Done", "to": {"name": "Done"}},
        ]
    }


@pytest.fixture
def mock_jira_myself() -> Dict[str, Any]:
    """Jira /myself response."""
    return {
        "accountId": "user123",
        "displayName": "Test User",
        "emailAddress": "test@example.com",
        "active": True,
    }


@pytest.fixture
def mock_jira_comment_created() -> Dict[str, Any]:
    """Jira comment created response."""
    return {
        "id": "10000",
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Test comment"}],
                }
            ],
        },
    }


@pytest.fixture
def jira_tracker():
    """Create a JiraTracker instance with test config."""
    from runtime.tracker.jira import JiraTracker

    return JiraTracker(
        api_key="test-api-key",
        endpoint="https://company.atlassian.net",
        project_key="PROJ",
        username="test@example.com",
        timeout=30,
        active_states=["To Do", "In Progress"],
    )


# =============================================================================
# Mock Response Classes
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


# =============================================================================
# Test Class: Initialization
# =============================================================================


class TestJiraTrackerInitialization:
    """Test JiraTracker initialization."""

    def test_init_with_valid_params(self):
        """Init with required params succeeds."""
        from runtime.tracker.jira import JiraTracker

        tracker = JiraTracker(
            api_key="test-key",
            endpoint="https://company.atlassian.net",
            project_key="PROJ",
            username="test@example.com",
            timeout=30,
        )

        assert tracker._api_key == "test-key"
        assert tracker._endpoint == "https://company.atlassian.net"
        assert tracker._project_key == "PROJ"
        assert tracker._username == "test@example.com"

    def test_init_default_active_states(self):
        """Default active states when not provided."""
        from runtime.tracker.jira import JiraTracker

        tracker = JiraTracker(
            api_key="test-key",
            endpoint="https://company.atlassian.net",
        )

        assert tracker._active_states == ["To Do", "In Progress"]

    def test_init_custom_active_states(self):
        """Custom active states."""
        from runtime.tracker.jira import JiraTracker

        tracker = JiraTracker(
            api_key="test-key",
            endpoint="https://company.atlassian.net",
            active_states=["Open", "In Progress"],
        )

        assert tracker._active_states == ["Open", "In Progress"]

    def test_endpoint_trailing_slash_removed(self):
        """Endpoint trailing slash removed."""
        from runtime.tracker.jira import JiraTracker

        tracker = JiraTracker(
            api_key="test-key",
            endpoint="https://company.atlassian.net/",
        )

        assert not tracker._endpoint.endswith("/")


class TestJiraTrackerProperty:
    """Test tracker properties."""

    def test_tracker_kind(self, jira_tracker):
        """tracker_kind returns 'jira'."""
        assert jira_tracker.tracker_kind == "jira"

    def test_get_auth_header_format(self, jira_tracker):
        """Auth header is valid Basic auth format."""
        header = jira_tracker._get_auth_header()
        assert header.startswith("Basic ")

        # Decode and verify
        encoded = header.split(" ")[1]
        decoded = base64.b64decode(encoded).decode()
        assert decoded == f"test@example.com:test-api-key"


# =============================================================================
# Test Class: Get Issue
# =============================================================================


class TestGetIssue:
    """Test get_issue method."""

    @patch("runtime.tracker.jira.requests.request")
    def test_get_issue_success(self, mock_request, jira_tracker, mock_jira_issue):
        """Successful get_issue returns issue data."""
        mock_request.return_value = MockResponse(
            json_data=mock_jira_issue, status_code=200
        )

        result = jira_tracker.get_issue("PROJ-100")

        assert result["key"] == "PROJ-100"
        assert result["fields"]["summary"] == "Test issue title"
        mock_request.assert_called_once()

    @patch("runtime.tracker.jira.requests.request")
    def test_get_issue_with_null_assignee(
        self, mock_request, jira_tracker, mock_jira_issue_null_assignee
    ):
        """Issue with null assignee does not crash."""
        mock_request.return_value = MockResponse(
            json_data=mock_jira_issue_null_assignee, status_code=200
        )

        result = jira_tracker.get_issue("PROJ-101")

        assert result["key"] == "PROJ-101"

    @patch("runtime.tracker.jira.requests.request")
    def test_get_issue_with_null_priority(
        self, mock_request, jira_tracker, mock_jira_issue_null_priority
    ):
        """Issue with null priority does not crash."""
        mock_request.return_value = MockResponse(
            json_data=mock_jira_issue_null_priority, status_code=200
        )

        result = jira_tracker.get_issue("PROJ-102")

        assert result["key"] == "PROJ-102"

    @patch("runtime.tracker.jira.requests.request")
    def test_get_issue_404(self, mock_request, jira_tracker):
        """404 returns TrackerApiResourceNotFoundError."""
        from runtime.tracker.factory import TrackerApiResourceNotFoundError

        mock_request.return_value = MockResponse(
            json_data={"errorMessages": ["Issue Does Not Exist"], "errors": {}},
            status_code=404,
            text="Not Found",
        )

        with pytest.raises(TrackerApiResourceNotFoundError):
            jira_tracker.get_issue("PROJ-999")

    @patch("runtime.tracker.jira.requests.request")
    def test_get_issue_401(self, mock_request, jira_tracker):
        """401 returns TrackerApiStatusError."""
        from runtime.tracker.factory import TrackerApiStatusError

        mock_request.return_value = MockResponse(
            json_data={"errorMessages": ["Unauthorized"], "errors": {}},
            status_code=401,
            text="Unauthorized",
        )

        with pytest.raises(TrackerApiStatusError):
            jira_tracker.get_issue("PROJ-100")

    @patch("runtime.tracker.jira.requests.request")
    def test_get_issue_timeout(self, mock_request, jira_tracker):
        """Timeout raises TrackerApiTimeoutError."""
        import requests
        from runtime.tracker.factory import TrackerApiTimeoutError

        mock_request.side_effect = requests.exceptions.Timeout("Connection timeout")

        with pytest.raises(TrackerApiTimeoutError):
            jira_tracker.get_issue("PROJ-100")


# =============================================================================
# Test Class: Fetch Issues (JQL Search)
# =============================================================================


class TestFetchIssues:
    """Test fetch_issues method (JQL search)."""

    @patch("runtime.tracker.jira.requests.request")
    def test_get_issues_simple_jql(
        self, mock_request, jira_tracker, mock_jira_search_response
    ):
        """Simple JQL query returns issues."""
        mock_request.return_value = MockResponse(
            json_data=mock_jira_search_response, status_code=200
        )

        issues = jira_tracker.fetch_issues("project = PROJ")

        assert len(issues) == 2
        assert issues[0]["key"] == "PROJ-100"

    @patch("runtime.tracker.jira.requests.request")
    def test_get_issues_empty_result(
        self, mock_request, jira_tracker, mock_jira_search_response_empty
    ):
        """Empty result returns empty list."""
        mock_request.return_value = MockResponse(
            json_data=mock_jira_search_response_empty, status_code=200
        )

        issues = jira_tracker.fetch_issues("project = PROJ AND resolution = Unresolved")

        assert issues == []

    @patch("runtime.tracker.jira.requests.request")
    def test_get_issues_pagination(
        self,
        mock_request,
        jira_tracker,
        mock_jira_search_paginated_page1,
        mock_jira_search_paginated_page2,
    ):
        """Pagination: two requests for results > maxResults."""
        # First call returns page 1, second call returns page 2
        mock_request.side_effect = [
            MockResponse(json_data=mock_jira_search_paginated_page1, status_code=200),
            MockResponse(json_data=mock_jira_search_paginated_page2, status_code=200),
        ]

        issues = jira_tracker.fetch_issues("project = PROJ")

        # Should have all 75 issues (50 + 25)
        assert len(issues) == 75
        assert mock_request.call_count == 2

    @patch("runtime.tracker.jira.requests.request")
    def test_get_issues_jql_syntax_error(self, mock_request, jira_tracker):
        """JQL syntax error raises TrackerApiStatusError."""
        from runtime.tracker.factory import TrackerApiStatusError

        mock_request.return_value = MockResponse(
            json_data={
                "errorMessages": ["Expected 'AND', got 'InvalidToken'"],
                "errors": {"jql": "Invalid query"},
            },
            status_code=400,
            text="Bad Request",
        )

        with pytest.raises(TrackerApiStatusError):
            jira_tracker.fetch_issues("invalid jql query")


# =============================================================================
# Test Class: Deprecated Endpoint Check
# =============================================================================


class TestDeprecatedEndpoint:
    """CRITICAL: Check for deprecated /rest/api/3/search endpoint."""

    @patch("runtime.tracker.jira.requests.request")
    def test_uses_deprecated_endpoint(
        self, mock_request, jira_tracker, mock_jira_search_response
    ):
        """CRITICAL: Check adapter uses deprecated /rest/api/3/search endpoint.

        This is a bug! The /rest/api/3/search endpoint was deprecated in May 2025.
        We should use /rest/api/3/search/jql instead.
        """
        mock_request.return_value = MockResponse(
            json_data=mock_jira_search_response, status_code=200
        )

        # Call fetch_issues which internally uses search
        jira_tracker.fetch_issues("project = PROJ")

        # Check what endpoint was called
        call_args = mock_request.call_args
        url = call_args[1]["url"] if "url" in call_args[1] else call_args[0][1]

        # Check for deprecated EXACT endpoint: /rest/api/3/search (NOT /rest/api/3/search/jql)
        # The deprecated endpoint ends with /search, the new endpoint ends with /search/jql
        if url.endswith("/rest/api/3/search") or "/rest/api/3/search?" in url:
            pytest.fail(
                "BUG FOUND: Adapter uses deprecated /rest/api/3/search endpoint. "
                "This endpoint was deprecated in May 2025. "
                "Should use /rest/api/3/search/jql instead. "
                "Create bug ticket TASK-004-BUG-001."
            )


# =============================================================================
# Test Class: Transitions
# =============================================================================


class TestTransitions:
    """Test transition methods."""

    @patch("runtime.tracker.jira.requests.request")
    def test_list_transitions(self, mock_request, jira_tracker, mock_jira_transitions):
        """list_transitions returns transitions."""
        mock_request.return_value = MockResponse(
            json_data=mock_jira_transitions, status_code=200
        )

        transitions = jira_tracker.list_transitions("PROJ-100")

        assert len(transitions) == 3
        assert transitions[0]["name"] == "To Do"

    @patch("runtime.tracker.jira.requests.request")
    def test_transition_issue_204(self, mock_request, jira_tracker):
        """Transition with 204 No Content handled correctly."""
        from runtime.tracker.factory import TrackerApiStatusError

        # 204 returns empty response
        mock_request.return_value = MockResponse(json_data=None, status_code=204)

        result = jira_tracker.transition_issue("PROJ-100", "31")

        assert result == {"success": True}

    @patch("runtime.tracker.jira.requests.request")
    def test_transition_issue_invalid_id(self, mock_request, jira_tracker):
        """Invalid transition ID raises error."""
        from runtime.tracker.factory import TrackerApiStatusError

        mock_request.return_value = MockResponse(
            json_data={
                "errorMessages": ["Transition id '999' does not exist"],
                "errors": {},
            },
            status_code=400,
            text="Bad Request",
        )

        with pytest.raises(TrackerApiStatusError):
            jira_tracker.transition_issue("PROJ-100", "999")

    @patch("runtime.tracker.jira.requests.request")
    def test_find_transition_by_status(
        self, mock_request, jira_tracker, mock_jira_transitions
    ):
        """find_transition_by_status returns transition ID."""
        mock_request.return_value = MockResponse(
            json_data=mock_jira_transitions, status_code=200
        )

        transition_id = jira_tracker.find_transition_by_status("PROJ-100", "Done")

        assert transition_id == "31"


# =============================================================================
# Test Class: Add Comment
# =============================================================================


class TestAddComment:
    """Test add_comment method."""

    @patch("runtime.tracker.jira.requests.request")
    def test_add_comment_text_converts_to_adf(
        self, mock_request, jira_tracker, mock_jira_comment_created
    ):
        """Text comment converts to ADF format."""
        mock_request.return_value = MockResponse(
            json_data=mock_jira_comment_created, status_code=201
        )

        result = jira_tracker.add_comment("PROJ-100", "Test comment")

        assert result["id"] == "10000"
        # Verify ADF format was sent
        call_args = mock_request.call_args
        body = call_args[1]["json"]["body"]
        assert body["type"] == "doc"
        assert body["version"] == 1

    @patch("runtime.tracker.jira.requests.request")
    def test_add_comment_multiline_text(
        self, mock_request, jira_tracker, mock_jira_comment_created
    ):
        """Multiline text produces correct ADF."""
        mock_request.return_value = MockResponse(
            json_data=mock_jira_comment_created, status_code=201
        )

        result = jira_tracker.add_comment("PROJ-100", "Line 1\nLine 2\nLine 3")

        # Verify multiline is handled
        call_args = mock_request.call_args
        body = call_args[1]["json"]["body"]
        assert body["content"][0]["type"] == "paragraph"

    @patch("runtime.tracker.jira.requests.request")
    def test_add_comment_empty_string(self, mock_request, jira_tracker):
        """Empty string - adapter doesn't validate but API returns 400."""
        from runtime.tracker.factory import TrackerApiStatusError

        # Current behavior: adapter sends request, API returns 400
        mock_request.return_value = MockResponse(
            json_data={"errorMessages": ["Comment body is required"]},
            status_code=400,
            text="Bad Request",
        )
        # The adapter doesn't validate empty string - it makes request and API errors
        with pytest.raises(TrackerApiStatusError):
            jira_tracker.add_comment("PROJ-100", "")

    @patch("runtime.tracker.jira.requests.request")
    def test_add_comment_201(
        self, mock_request, jira_tracker, mock_jira_comment_created
    ):
        """201 response indicates success."""
        mock_request.return_value = MockResponse(
            json_data=mock_jira_comment_created, status_code=201
        )

        result = jira_tracker.add_comment("PROJ-100", "Test")

        assert "id" in result


class TestTextToADF:
    """Test text_to_adf static method."""

    def test_text_to_adf_simple(self, jira_tracker):
        """Simple text converts to ADF."""
        result = jira_tracker.text_to_adf("Hello world")

        assert result["type"] == "doc"
        assert result["version"] == 1
        assert result["content"][0]["type"] == "paragraph"
        assert result["content"][0]["content"][0]["text"] == "Hello world"

    def test_text_to_adf_empty(self, jira_tracker):
        """Empty text produces valid ADF."""
        result = jira_tracker.text_to_adf("")

        assert result["type"] == "doc"


# =============================================================================
# Test Class: Priority Normalization
# =============================================================================


class TestPriorityNormalization:
    """Test priority normalization using NormalizationUtils."""

    def test_priority_highest(self, jira_tracker, mock_jira_issue):
        """'Highest' priority normalizes to 1."""
        from runtime.tracker.normalization import NormalizationUtils

        mock_jira_issue["fields"]["priority"] = {"name": "Highest"}
        normalized = jira_tracker._normalize_jira_issue(mock_jira_issue)

        assert normalized["priority"] == 1

    def test_priority_high(self, jira_tracker, mock_jira_issue):
        """'High' priority normalizes to 2."""
        mock_jira_issue["fields"]["priority"] = {"name": "High"}
        normalized = jira_tracker._normalize_jira_issue(mock_jira_issue)

        assert normalized["priority"] == 2

    def test_priority_medium(self, jira_tracker, mock_jira_issue):
        """'Medium' priority normalizes to 3."""
        mock_jira_issue["fields"]["priority"] = {"name": "Medium"}
        normalized = jira_tracker._normalize_jira_issue(mock_jira_issue)

        assert normalized["priority"] == 3

    def test_priority_low(self, jira_tracker, mock_jira_issue):
        """'Low' priority normalizes to 4."""
        mock_jira_issue["fields"]["priority"] = {"name": "Low"}
        normalized = jira_tracker._normalize_jira_issue(mock_jira_issue)

        assert normalized["priority"] == 4

    def test_priority_lowest(self, jira_tracker, mock_jira_issue):
        """'Lowest' priority normalizes to 4."""
        mock_jira_issue["fields"]["priority"] = {"name": "Lowest"}
        normalized = jira_tracker._normalize_jira_issue(mock_jira_issue)

        assert normalized["priority"] == 4

    def test_priority_none(self, jira_tracker, mock_jira_issue):
        """None priority does not crash."""
        mock_jira_issue["fields"]["priority"] = None
        normalized = jira_tracker._normalize_jira_issue(mock_jira_issue)

        assert normalized["priority"] is None


# =============================================================================
# Test Class: Rate Limiting
# =============================================================================


class TestRateLimiting:
    """Test rate limit handling."""

    @patch("runtime.tracker.jira.requests.request")
    def test_rate_limit_429_with_retry_after(self, mock_request, jira_tracker):
        """429 with Retry-After raises with message."""
        from runtime.tracker.factory import TrackerApiRateLimitError

        mock_request.return_value = MockResponse(
            json_data={"errorMessages": ["Rate limit"]},
            status_code=429,
            headers={"Retry-After": "5"},
            text="Rate limit",
        )

        with pytest.raises(TrackerApiRateLimitError) as exc_info:
            jira_tracker.get_issue("PROJ-100")

        assert "5" in str(exc_info.value)

    @patch("runtime.tracker.jira.requests.request")
    def test_rate_limit_429_no_retry_after(self, mock_request, jira_tracker):
        """429 without Retry-After raises with default."""
        from runtime.tracker.factory import TrackerApiRateLimitError

        mock_request.return_value = MockResponse(
            json_data={"errorMessages": ["Rate limit"]},
            status_code=429,
            headers={},
            text="Rate limit",
        )

        with pytest.raises(TrackerApiRateLimitError) as exc_info:
            jira_tracker.get_issue("PROJ-100")

        # Should have default retry-after
        assert "60" in str(exc_info.value)

    @patch("runtime.tracker.jira.requests.request")
    def test_rate_limit_repeated(self, mock_request, jira_tracker):
        """429 three times raises TrackerError."""
        from runtime.tracker.factory import TrackerApiRateLimitError

        mock_request.return_value = MockResponse(
            json_data={"errorMessages": ["Rate limit"]},
            status_code=429,
            headers={"Retry-After": "1"},
            text="Rate limit",
        )

        # Note: This test shows current behavior doesn't have retry logic
        # It just raises on each 429
        with pytest.raises(TrackerApiRateLimitError):
            jira_tracker.get_issue("PROJ-100")


# =============================================================================
# Test Class: Candidate Issues
# =============================================================================


class TestCandidateIssues:
    """Test fetch_candidate_issues method."""

    @patch("runtime.tracker.jira.requests.request")
    def test_fetch_candidate_issues(
        self, mock_request, jira_tracker, mock_jira_search_response
    ):
        """fetch_candidate_issues returns normalized issues."""
        mock_request.return_value = MockResponse(
            json_data=mock_jira_search_response, status_code=200
        )

        issues = jira_tracker.fetch_candidate_issues()

        assert len(issues) == 2
        # Check normalization
        assert "id" in issues[0]
        assert "identifier" in issues[0]
        assert "title" in issues[0]

    @patch("runtime.tracker.jira.requests.request")
    def test_fetch_candidate_issues_no_project_key(self, mock_request):
        """No project_key raises TrackerAPIError."""
        from runtime.tracker.jira import JiraTracker
        from runtime.tracker.factory import TrackerAPIError

        tracker = JiraTracker(
            api_key="test-key",
            endpoint="https://company.atlassian.net",
            project_key="",  # No project key
        )

        with pytest.raises(TrackerAPIError):
            tracker.fetch_candidate_issues()


# =============================================================================
# Test Class: Fetch Issues By States
# =============================================================================


class TestFetchIssuesByStates:
    """Test fetch_issues_by_states method."""

    @patch("runtime.tracker.jira.requests.request")
    def test_fetch_issues_by_states(
        self, mock_request, jira_tracker, mock_jira_search_response
    ):
        """fetch_issues_by_states returns issues in specified states."""
        mock_request.return_value = MockResponse(
            json_data=mock_jira_search_response, status_code=200
        )

        issues = jira_tracker.fetch_issues_by_states(["To Do"])

        assert len(issues) == 2

    @patch("runtime.tracker.jira.requests.request")
    def test_fetch_issues_by_states_empty_list(self, mock_request, jira_tracker):
        """Empty state list returns empty list."""
        issues = jira_tracker.fetch_issues_by_states([])

        assert issues == []
        mock_request.assert_not_called()


# =============================================================================
# Test Class: Fetch Issue States By IDs
# =============================================================================


class TestFetchIssueStatesByIds:
    """Test fetch_issue_states_by_ids method."""

    @patch("runtime.tracker.jira.requests.request")
    def test_fetch_issue_states_by_ids(
        self, mock_request, jira_tracker, mock_jira_search_response
    ):
        """fetch_issue_states_by_ids returns state mapping."""
        mock_request.return_value = MockResponse(
            json_data=mock_jira_search_response, status_code=200
        )

        states = jira_tracker.fetch_issue_states_by_ids(["PROJ-100", "PROJ-101"])

        assert states["PROJ-100"] == "To Do"
        assert states["PROJ-101"] == "In Progress"

    @patch("runtime.tracker.jira.requests.request")
    def test_fetch_issue_states_by_ids_empty(self, mock_request, jira_tracker):
        """Empty ID list returns empty dict."""
        states = jira_tracker.fetch_issue_states_by_ids([])

        assert states == {}
        mock_request.assert_not_called()


# =============================================================================
# Test Class: Update Issue
# =============================================================================


class TestUpdateIssue:
    """Test update_issue method."""

    @patch("runtime.tracker.jira.requests.request")
    def test_update_issue(self, mock_request, jira_tracker):
        """Update issue fields."""
        mock_request.return_value = MockResponse(
            json_data={"fields": {"summary": "Updated"}}, status_code=200
        )

        result = jira_tracker.update_issue("PROJ-100", {"summary": "Updated title"})

        assert result is not None

    @patch("runtime.tracker.jira.requests.request")
    def test_update_issue_204(self, mock_request, jira_tracker):
        """204 response handled."""
        mock_request.return_value = MockResponse(json_data=None, status_code=204)

        result = jira_tracker.update_issue("PROJ-100", {"summary": "Updated"})

        assert result == {"success": True}


# =============================================================================
# Test Class: Authenticate
# =============================================================================


class TestAuthenticate:
    """Test authenticate method."""

    @patch("runtime.tracker.jira.requests.request")
    def test_authenticate(self, mock_request, jira_tracker, mock_jira_myself):
        """authenticate returns user info."""
        mock_request.return_value = MockResponse(
            json_data=mock_jira_myself, status_code=200
        )

        user = jira_tracker.authenticate()

        assert user["displayName"] == "Test User"
        assert jira_tracker._user is not None
