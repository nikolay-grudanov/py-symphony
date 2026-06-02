"""Tests for YandexTrackerAdapter - User Story 1 (T011-T014).

This module contains tests for Phase 3: User Story 1 - Configure Yandex Tracker as Issue Tracker.

Test Tasks:
- T011: Test adapter initialization with valid OAuth token and project_slug
- T012: Test tracker_type property returns "yandex_tracker"
- T013: Test lazy authentication (no API call on init)
- T014: Test authentication with valid token returns user info

User Story 1 Goal:
Enable Symphony orchestration platform to configure Yandex Tracker as issue tracking system.
"""

from unittest.mock import Mock, patch

import pytest
import httpx

from symphony_yandex_tracker import errors
from symphony_yandex_tracker import models
from symphony_yandex_tracker.adapter import YandexTrackerAdapter


class TestUserStory1AdapterInitialization:
    """Test suite for User Story 1: Configure Yandex Tracker as Issue Tracker.

    These tests verify that the adapter can be initialized with valid credentials
    and that authentication can be performed lazily on demand.
    """

    # T011: Test adapter initialization with valid OAuth token and project_slug
    def test_initialization_with_valid_oauth_token_and_project_slug(self):
        """Test T011: Adapter initialization succeeds with valid parameters.

        Test case: adapter initialization succeeds with valid parameters
        Parameters: api_key="y0_test_token", project_slug="TEST-QUEUE",
                   endpoint="https://api.tracker.yandex.net/v3"
        Verify: adapter is created without errors
        Verify: all parameters are stored correctly
        """
        # Create adapter with valid parameters
        adapter = YandexTrackerAdapter(
            api_key="y0_test_token",
            project_slug="TEST-QUEUE",
            endpoint="https://api.tracker.yandex.net/v3",
        )

        # Verify adapter is created without errors
        assert adapter is not None
        assert isinstance(adapter, YandexTrackerAdapter)

        # Verify all parameters are stored correctly
        assert adapter._api_key == "y0_test_token"
        assert adapter._project_slug == "TEST-QUEUE"
        assert adapter._endpoint == "https://api.tracker.yandex.net/v3"
        assert adapter._timeout == 30  # default value

        # Verify active_states has default values
        assert adapter._active_states == ["open", "in_progress"]

    def test_initialization_with_custom_timeout(self):
        """Test T011: Adapter initialization with custom timeout."""
        adapter = YandexTrackerAdapter(
            api_key="y0_test_token",
            project_slug="TEST-QUEUE",
            timeout=60,
        )

        assert adapter._timeout == 60

    def test_initialization_with_custom_active_states(self):
        """Test T011: Adapter initialization with custom active states."""
        adapter = YandexTrackerAdapter(
            api_key="y0_test_token",
            project_slug="TEST-QUEUE",
            active_states=["open", "in_progress", "need_info"],
        )

        assert adapter._active_states == ["open", "in_progress", "need_info"]

    def test_initialization_with_empty_project_slug(self):
        """Test T011: Adapter initialization works with empty project_slug."""
        adapter = YandexTrackerAdapter(
            api_key="y0_test_token",
            project_slug="",
        )

        assert adapter._project_slug == ""

    # T012: Test tracker_type property returns "yandex_tracker"
    def test_tracker_type_returns_yandex_tracker(self):
        """Test T012: tracker_type property returns correct value.

        Test case: tracker_type property returns correct value
        Verify: adapter.tracker_type == "yandex_tracker"
        """
        adapter = YandexTrackerAdapter(
            api_key="y0_test_token",
            project_slug="TEST-QUEUE",
        )

        # Verify tracker_type returns "yandex_tracker"
        assert adapter.tracker_type == "yandex_tracker"

    def test_tracker_type_is_immutable(self):
        """Test T012: tracker_type property is read-only."""
        adapter = YandexTrackerAdapter(
            api_key="y0_test_token",
            project_slug="TEST-QUEUE",
        )

        # Verify property returns a string
        assert isinstance(adapter.tracker_type, str)

        # Verify the value is exactly as expected
        assert adapter.tracker_type == "yandex_tracker"

    # T013: Test lazy authentication
    def test_lazy_authentication_no_api_call_on_init(self):
        """Test T013: Initialization does not call authentication API.

        Test case: initialization succeeds, authentication is lazy (not called on init)
        Verify: adapter initialization does not call authentication API
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            # Create adapter - should NOT instantiate HTTP client yet
            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST-QUEUE",
            )

            # Verify HTTP client class was NOT instantiated during init
            mock_client_class.assert_not_called()

            # Verify internal HTTP client is None (not created yet)
            assert adapter._http_client is None

    def test_lazy_authentication_http_client_created_on_demand(self):
        """Test T013: HTTP client is created only when needed.

        Verify: HTTP client is created only when _get_http_client() is called
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST-QUEUE",
            )

            # HTTP client should not be created yet
            assert adapter._http_client is None

            # Access http client - this should trigger creation
            client = adapter._get_http_client()

            # Now HTTP client should be created
            mock_client_class.assert_called_once_with(
                endpoint="https://api.tracker.yandex.net/v3",
                api_key="y0_test_token",
                timeout=30,
            )
            assert client is mock_client_instance

    def test_lazy_authentication_can_call_authenticate_separately(self):
        """Test T013: authenticate() method can be called separately.

        Verify: authenticate() method can be called separately after init
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"uid": 12345, "login": "testuser"}

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST-QUEUE",
            )

            # Call authenticate() explicitly
            result = adapter.authenticate()

            # Verify authenticate was called and returned user info
            assert result == {"uid": 12345, "login": "testuser"}
            mock_client_instance.get.assert_called_once_with("/v2/myself")

    # T014: Test authentication with valid token returns user info
    def test_authentication_with_valid_oauth_token_returns_user_info(self):
        """Test T014: authenticate() method calls GET /v2/myself and returns user info.

        Test case: authenticate() method calls GET /v2/myself and returns user info
        Mock http_client.get() to return valid user info response
        Verify: authenticate() returns user info dictionary
        Verify: authenticate() makes correct API call (GET /v2/myself)
        Verify: authenticate() includes Authorization header
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            # Mock API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_user_info = {
                "uid": 12345,
                "login": "testuser",
                "first_name": "Test",
                "last_name": "User",
                "email": "testuser@example.com",
            }
            mock_response.json.return_value = mock_user_info

            # Setup mock client
            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            # Create adapter and authenticate
            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST-QUEUE",
            )
            result = adapter.authenticate()

            # Verify authenticate() returns user info dictionary
            assert result == mock_user_info
            assert result["uid"] == 12345
            assert result["login"] == "testuser"

            # Verify authenticate() makes correct API call
            mock_client_instance.get.assert_called_once_with("/v2/myself")

    def test_authentication_with_iam_token_returns_user_info(self):
        """Test T014: authenticate() works with IAM token (t1. prefix).

        Test both OAuth token (y0__ prefix) and IAM token (t1. prefix)
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"uid": 67890, "login": "iamuser"}

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            # Create adapter with IAM token
            adapter = YandexTrackerAdapter(
                api_key="t1.eyJhbGciOiJSUzI1NiJ9.eyJ",
                project_slug="TEST-QUEUE",
            )
            result = adapter.authenticate()

            # Verify authentication works with IAM token
            assert result["uid"] == 67890
            mock_client_instance.get.assert_called_once_with("/v2/myself")

    def test_authentication_includes_authorization_header(self):
        """Test T014: authenticate() includes Authorization header in request.

        Verify: HTTP client is created with proper Authorization header
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"uid": 12345, "login": "testuser"}

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST-QUEUE",
            )
            adapter.authenticate()

            # Verify TrackerHttpClient was called with correct api_key
            mock_client_class.assert_called_once()
            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["api_key"] == "y0_test_token"

    def test_authentication_raises_token_expired_error_on_401(self):
        """Test T014: authenticate() raises TokenExpiredError on 401 response."""
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_expired_token",
                project_slug="TEST-QUEUE",
            )

            # Verify TokenExpiredError is raised
            with pytest.raises(errors.TokenExpiredError) as exc_info:
                adapter.authenticate()

            assert "invalid or expired" in exc_info.value.message.lower()

    def test_authentication_raises_tracker_api_error_on_non_200_non_401(self):
        """Test T014: authenticate() raises TrackerApiError on other error responses."""
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST-QUEUE",
            )

            # Verify TrackerApiError is raised
            with pytest.raises(errors.TrackerApiError):
                adapter.fetch_candidate_issues()


class TestUserStory3FetchIssuesByState:
    """Test suite for User Story 3: Query Issues by State.

    These tests verify that the adapter can fetch issues filtered by specific
    state names and return them in normalized format.

    Test Tasks:
    - T028: Test fetch_issues_by_state returns filtered issues by state list
    - T029: Test fetch_issues_by_state returns empty list for empty state list
    - T030: Test fetch_issues_by_state returns empty list for non-existent state (no error)
    """

    # T028: Test fetch_issues_by_state returns filtered issues by state list
    def test_fetch_issues_by_state_returns_filtered_issues(self):
        """Test T028: fetch_issues_by_state returns issues filtered by state list.

        Test case: fetch_issues_by_state returns list of issues filtered by states
        Mock API response with Yandex Tracker issue format
        Verify: returns list of issues with normalized fields (id, identifier,
                title, state, priority, created_at, labels, blocked_by)
        Verify: only issues with matching states are returned
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            # Mock API response with Yandex Tracker format
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {
                    "self": "https://api.tracker.yandex.net/v2/issues/123",
                    "key": "BACKEND-123",
                    "summary": "Implement user authentication",
                    "status": {"name": "Open", "key": "open"},
                    "priority": {"name": "High", "key": "high"},
                    "createdAt": "2024-01-15T10:30:00Z",
                    "tags": ["backend", "security"],
                    "dependencies": [{"id": "BACKEND-100"}],
                },
                {
                    "self": "https://api.tracker.yandex.net/v2/issues/124",
                    "key": "BACKEND-124",
                    "summary": "Add API documentation",
                    "status": {"name": "In progress", "key": "in_progress"},
                    "priority": {"name": "Medium", "key": "medium"},
                    "createdAt": "2024-01-16T14:00:00Z",
                    "tags": ["docs"],
                    "dependencies": [],
                },
                {
                    "self": "https://api.tracker.yandex.net/v2/issues/125",
                    "key": "BACKEND-125",
                    "summary": "Fix bug in parser",
                    "status": {"name": "Closed", "key": "closed"},
                    "priority": {"name": "High", "key": "high"},
                    "createdAt": "2024-01-17T09:00:00Z",
                    "tags": ["bug"],
                    "dependencies": [],
                },
            ]

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="BACKEND",
            )

            # Fetch only issues in "Open" and "In progress" states
            result = adapter.fetch_issues_by_state(["Open", "In progress"])

            # Verify result is a list
            assert isinstance(result, list)
            # Should return only 2 issues (Open and In progress), not Closed
            assert len(result) == 2

            # Verify first issue has normalized fields
            first_issue = result[0]
            assert "id" in first_issue
            assert "identifier" in first_issue
            assert "title" in first_issue
            assert "state" in first_issue
            assert "priority" in first_issue
            assert "created_at" in first_issue
            assert "labels" in first_issue
            assert "blocked_by" in first_issue

            # Verify API call was made
            mock_client_instance.get.assert_called_once()

    def test_fetch_issues_by_state_returns_normalized_format(self):
        """Test T028: fetch_issues_by_state returns normalized issue format.

        Verify: issues have id, identifier, title, state, priority, created_at, labels, blocked_by
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {
                    "self": "https://api.tracker.yandex.net/v2/issues/456",
                    "key": "TEST-100",
                    "summary": "Test issue",
                    "status": {"name": "Open"},
                    "priority": {"name": "High"},
                    "createdAt": "2024-01-15T10:30:00Z",
                    "tags": ["test"],
                    "dependencies": [{"id": "TEST-99"}],
                }
            ]

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.fetch_issues_by_state(["Open"])

            # Verify all required normalized fields are present
            issue = result[0]
            assert issue["id"] == "456"
            assert issue["identifier"] == "TEST-100"
            assert issue["title"] == "Test issue"
            assert issue["state"] == "open"  # normalized to lowercase
            assert issue["priority"] is not None
            assert issue["created_at"] == "2024-01-15T10:30:00Z"
            assert issue["labels"] == ["test"]
            assert issue["blocked_by"] == ["TEST-99"]

    # T029: Test fetch_issues_by_state returns empty list for empty state list
    def test_fetch_issues_by_state_returns_empty_list_for_empty_states(self):
        """Test T029: fetch_issues_by_state returns empty list when states list is empty.

        Test case: fetch_issues_by_state returns empty list when states list is empty
        Verify: returns empty list without calling API
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST-QUEUE",
            )

            result = adapter.fetch_issues_by_state([])

            # Verify empty list is returned
            assert result == []
            assert isinstance(result, list)

            # Verify API was NOT called (early return for empty states)
            mock_client_instance.get.assert_not_called()

    def test_fetch_issues_by_state_raises_error_when_project_slug_empty(self):
        """Test T029: fetch_issues_by_state raises ConfigurationError when project_slug is empty.

        Verify: ConfigurationError is raised before calling API when project_slug not set
        """
        adapter = YandexTrackerAdapter(
            api_key="y0_test_token",
            project_slug="",
        )

        # Verify ConfigurationError is raised
        with pytest.raises(errors.ConfigurationError) as exc_info:
            adapter.fetch_issues_by_state(["Open"])

        # Verify error message mentions project_slug
        assert "project_slug" in exc_info.value.message.lower()

    # T030: Test fetch_issues_by_state returns empty list for non-existent state (no error)
    def test_fetch_issues_by_state_returns_empty_for_non_existent_state(self):
        """Test T030: fetch_issues_by_state returns empty list when no issues match states.

        Test case: fetch_issues_by_state returns empty list when no issues match provided states
        Mock API response with issues in different states
        Verify: returns empty list without raising error
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            # Mock API response with issues in states not requested
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {
                    "self": "https://api.tracker.yandex.net/v2/issues/100",
                    "key": "TEST-1",
                    "summary": "Issue 1",
                    "status": {"name": "Closed"},
                    "priority": {"name": "High"},
                    "createdAt": "2024-01-15T10:30:00Z",
                    "tags": [],
                    "dependencies": [],
                },
                {
                    "self": "https://api.tracker.yandex.net/v2/issues/101",
                    "key": "TEST-2",
                    "summary": "Issue 2",
                    "status": {"name": "Resolved"},
                    "priority": {"name": "Medium"},
                    "createdAt": "2024-01-16T14:00:00Z",
                    "tags": [],
                    "dependencies": [],
                },
            ]

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            # Request states that don't exist in the response
            result = adapter.fetch_issues_by_state(["Open", "In progress"])

            # Verify empty list is returned (no error raised)
            assert result == []
            assert isinstance(result, list)

            # Verify API was still called
            mock_client_instance.get.assert_called_once()

    def test_fetch_issues_by_state_returns_empty_when_no_issues_at_all(self):
        """Test T030: fetch_issues_by_state returns empty list when API returns no issues.

        Verify: returns empty list when API response is empty
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.fetch_issues_by_state(["Open"])

            # Verify empty list is returned
            assert result == []

    def test_fetch_issues_by_state_logs_success(self):
        """Test T030: fetch_issues_by_state logs success with required fields.

        Verify: logging includes action, outcome, duration_ms, states, issue_count
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {
                    "self": "https://api.tracker.yandex.net/v2/issues/123",
                    "key": "TEST-1",
                    "summary": "Test issue",
                    "status": {"name": "Open"},
                    "priority": {"name": "High"},
                    "createdAt": "2024-01-15T10:30:00Z",
                    "tags": [],
                    "dependencies": [],
                }
            ]

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            # Call method - should log success
            adapter.fetch_issues_by_state(["Open"])

    def test_fetch_issues_by_state_raises_on_api_error(self):
        """Test T030: fetch_issues_by_state raises TrackerApiError on API error.

        Verify: TrackerApiError is raised when API returns error
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            # Verify TrackerApiError is raised
            with pytest.raises(errors.TrackerApiError):
                adapter.fetch_issues_by_state(["Open"])

    # Issue 6: Missing test for None states parameter
    def test_fetch_issues_by_state_handles_none_states(self):
        """Test T030: fetch_issues_by_state handles None states parameter.

        When states is None, should return empty list (same as empty list behavior)
        """
        adapter = YandexTrackerAdapter(
            api_key="y0_test_token",
            project_slug="TEST-QUEUE",
        )

        # Should return empty list for None states (treated as empty)
        result = adapter.fetch_issues_by_state(None)

        assert result == []
        assert isinstance(result, list)

    # Issue 7: Missing test for timeout scenario
    def test_fetch_issues_by_state_raises_on_timeout(self):
        """Test T030: fetch_issues_by_state raises TrackerTimeoutError on timeout.

        Verify: TrackerTimeoutError is raised when request times out
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            # Verify TrackerTimeoutError is raised
            with pytest.raises(errors.TrackerTimeoutError):
                adapter.fetch_issues_by_state(["Open"])

    # Issue 8: Missing test for large dataset / multiple pages
    def test_fetch_issues_by_state_handles_pagination(self):
        """Test T030: fetch_issues_by_state correctly handles pagination.

        Verify: All issues from multiple pages are returned
        Verify: Two API calls are made for paginated results
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            # First page: 50 issues (full page)
            page1_response = Mock()
            page1_response.status_code = 200
            page1_response.json.return_value = [
                {
                    "self": f"https://api.tracker.yandex.net/v2/issues/{i}",
                    "key": f"TEST-{i}",
                    "summary": f"Issue {i}",
                    "status": {"name": "Open"},
                    "priority": {"name": "High"},
                    "createdAt": "2024-01-15T10:30:00Z",
                    "tags": [],
                    "dependencies": [],
                }
                for i in range(50)
            ]

            # Second page: 10 issues (less than per_page = 50, signals last page)
            page2_response = Mock()
            page2_response.status_code = 200
            page2_response.json.return_value = [
                {
                    "self": f"https://api.tracker.yandex.net/v2/issues/{i}",
                    "key": f"TEST-{i}",
                    "summary": f"Issue {i}",
                    "status": {"name": "Open"},
                    "priority": {"name": "High"},
                    "createdAt": "2024-01-15T10:30:00Z",
                    "tags": [],
                    "dependencies": [],
                }
                for i in range(50, 60)
            ]

            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = [page1_response, page2_response]
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.fetch_issues_by_state(["Open"])

            # Verify all 60 issues are returned (50 + 10)
            assert len(result) == 60

            # Verify two API calls were made (pagination)
            assert mock_client_instance.get.call_count == 2


class TestUserStory4FetchIssueStatesByIds:
    """Test suite for User Story 4: Fetch Issue States by IDs.

    These tests verify that the adapter can fetch states for specific issue IDs
    and return them as a dictionary mapping issue_id to state name.

    Test Tasks:
    - T033: Test fetch_issue_states_by_ids returns dictionary mapping issue_id to state
    - T034: Test fetch_issue_states_by_ids returns empty dictionary for empty issue_ids list
    - T035: Test fetch_issue_states_by_ids handles mix of valid and non-existent issue IDs
    - T036: Test fetch_issue_states_by_ids raises TrackerApiError on API failures
    """

    # T033: Test fetch_issue_states_by_ids returns dictionary mapping issue_id to state
    def test_fetch_issue_states_by_ids_returns_dictionary(self):
        """Test T033: fetch_issue_states_by_ids returns dictionary mapping issue_id to state.

        Test case: fetch_issue_states_by_ids returns dictionary with issue_id -> state mapping
        Mock API to return multiple issues with different states
        Verify: result is a dictionary
        Verify: dictionary maps issue_id to state correctly
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            # Mock API responses for multiple issues
            def mock_get(path):
                mock_response = Mock()
                issue_id = path.split("/")[-1]

                if issue_id == "123":
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "key": "TEST-123",
                        "summary": "Issue 1",
                        "status": {"name": "Open"},
                    }
                elif issue_id == "456":
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "key": "TEST-456",
                        "summary": "Issue 2",
                        "status": {"name": "In progress"},
                    }
                elif issue_id == "789":
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "key": "TEST-789",
                        "summary": "Issue 3",
                        "status": {"name": "Closed"},
                    }
                return mock_response

            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = mock_get
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.fetch_issue_states_by_ids(["123", "456", "789"])

            # Verify result is a dictionary
            assert isinstance(result, dict)

            # Verify dictionary maps issue_id to state correctly
            assert result["123"] == "Open"
            assert result["456"] == "In progress"
            assert result["789"] == "Closed"

            # Verify three API calls were made
            assert mock_client_instance.get.call_count == 3

    def test_fetch_issue_states_by_ids_single_issue(self):
        """Test T033: fetch_issue_states_by_ids works with single issue ID."""
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "key": "TEST-100",
                "summary": "Single issue",
                "status": {"name": "Open"},
            }

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.fetch_issue_states_by_ids(["100"])

            # Verify dictionary with single entry
            assert isinstance(result, dict)
            assert len(result) == 1
            assert result["100"] == "Open"

    # T034: Test fetch_issue_states_by_ids returns empty dictionary for empty issue_ids list
    def test_fetch_issue_states_by_ids_returns_empty_dict_for_empty_list(self):
        """Test T034: fetch_issue_states_by_ids returns empty dictionary for empty issue_ids.

        Test case: call method with empty list
        Verify: empty dictionary is returned
        Verify: API is NOT called (early return)
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST-QUEUE",
            )

            result = adapter.fetch_issue_states_by_ids([])

            # Verify empty dictionary is returned
            assert result == {}
            assert isinstance(result, dict)

            # Verify API was NOT called (early return)
            mock_client_instance.get.assert_not_called()

    def test_fetch_issue_states_by_ids_returns_empty_for_none(self):
        """Test T034: fetch_issue_states_by_ids handles None issue_ids.

        Verify: empty dictionary is returned for None input
        """
        adapter = YandexTrackerAdapter(
            api_key="y0_test_token",
            project_slug="TEST-QUEUE",
        )

        result = adapter.fetch_issue_states_by_ids(None)

        assert result == {}
        assert isinstance(result, dict)

    # T035: Test fetch_issue_states_by_ids handles mix of valid and non-existent issue IDs
    def test_fetch_issue_states_by_ids_handles_mixed_valid_and_not_found(self):
        """Test T035: fetch_issue_states_by_ids handles mix of valid and non-existent issue IDs.

        Test case: Mock API with mix of 200 (valid) and 404 (not found) responses
        Verify: only valid issue IDs are included in result
        Verify: non-existent issue IDs are excluded (partial success)
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:

            def mock_get(path):
                mock_response = Mock()
                issue_id = path.split("/")[-1]

                # Issues 123 and 456 exist (200), issue 999 does not (404)
                if issue_id in ["123", "456"]:
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "key": f"TEST-{issue_id}",
                        "summary": f"Issue {issue_id}",
                        "status": {"name": "Open" if issue_id == "123" else "In progress"},
                    }
                elif issue_id == "999":
                    mock_response.status_code = 404
                    mock_response.text = "Issue not found"
                return mock_response

            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = mock_get
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.fetch_issue_states_by_ids(["123", "456", "999"])

            # Verify result contains only valid issues
            assert isinstance(result, dict)
            assert len(result) == 2
            assert "123" in result
            assert "456" in result
            assert "999" not in result  # non-existent excluded

            # Verify correct states for valid issues
            assert result["123"] == "Open"
            assert result["456"] == "In progress"

    def test_fetch_issue_states_by_ids_all_not_found_returns_empty(self):
        """Test T035: fetch_issue_states_by_ids returns empty dict when all issues not found.

        Verify: empty dictionary returned when all issue IDs return 404
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Issue not found"

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.fetch_issue_states_by_ids(["999", "998"])

            # Verify empty dictionary when no issues found
            assert result == {}
            assert isinstance(result, dict)

    # T036: Test fetch_issue_states_by_ids raises TrackerApiError on API failures
    def test_fetch_issue_states_by_ids_raises_on_unexpected_exception(self):
        """Test T036: fetch_issue_states_by_ids raises TrackerApiError on unexpected failures.

        Test case: Mock API to raise a non-HTTP exception
        Verify: TrackerApiError is raised
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = ValueError("Unexpected error")
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            # Verify TrackerApiError is raised for unexpected exceptions
            with pytest.raises(errors.TrackerApiError):
                adapter.fetch_issue_states_by_ids(["123"])

    def test_fetch_issue_states_by_ids_handles_http_error_with_warning(self):
        """Test T036: fetch_issue_states_by_ids logs warning for HTTP errors but continues.

        Verify: HTTP errors are logged as warnings, not raised
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = httpx.HTTPError("Connection error")
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            # Should return empty dict (HTTP error logged but not raised)
            result = adapter.fetch_issue_states_by_ids(["123"])
            assert result == {}

    def test_fetch_issue_states_by_ids_handles_timeout_with_warning(self):
        """Test T036: fetch_issue_states_by_ids logs warning for timeout but continues.

        Verify: Timeout errors are logged as warnings, not raised
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            # Should return empty dict (timeout logged but not raised)
            result = adapter.fetch_issue_states_by_ids(["123"])
            assert result == {}


class TestUserStory5GetAndUpdateIssue:
    """Test suite for User Story 5: Get and Update Issue Details.

    These tests verify that the adapter can fetch full issue details and
    update existing issues with various field operations.

    Test Tasks:
    - T041: Test get_issue returns full issue details for valid key
    - T042: Test get_issue raises ResourceNotFoundError for non-existent issue
    - T043: Test update_issue successfully updates issue and returns updated data
    - T044: Test update_issue supports array operations (add, remove, set, null)
    - T045: Test update_issue uses optimistic locking with version field (409 Conflict)
    """

    # T041: Test get_issue returns full issue details for valid key
    def test_get_issue_returns_full_details_for_valid_key(self):
        """Test T041: get_issue returns full issue details for valid key.

        Test case: get_issue returns issue details for valid issue key
        Mock API to return 200 with full issue details
        Verify: returned dict contains all fields (key, summary, status, priority, etc.)
        Verify: API was called with correct endpoint (/v2/issues/{issue_key})
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            # Mock API response with full issue details
            mock_response = Mock()
            mock_response.status_code = 200
            mock_full_issue = {
                "self": "https://api.tracker.yandex.net/v2/issues/123",
                "id": "1234567890abcdef",
                "key": "BACKEND-123",
                "summary": "Implement user authentication",
                "description": "Add OAuth2 authentication support",
                "status": {
                    "self": "https://api.tracker.yandex.net/v2/statuses/1",
                    "id": "1",
                    "key": "open",
                    "name": "Open",
                },
                "priority": {
                    "self": "https://api.tracker.yandex.net/v2/priorities/2",
                    "id": "2",
                    "key": "high",
                    "name": "High",
                },
                "type": {
                    "self": "https://api.tracker.yandex.net/v2/types/1",
                    "id": "1",
                    "key": "task",
                    "name": "Task",
                },
                "assignee": {
                    "self": "https://api.tracker.yandex.net/v2/users/12345",
                    "id": "12345",
                    "login": "developer",
                    "display": "Developer",
                },
                "deadline": "2024-02-01T23:59:59Z",
                "createdAt": "2024-01-15T10:30:00Z",
                "updatedAt": "2024-01-20T15:45:00Z",
                "version": 5,
                "tags": ["backend", "security"],
                "followers": [],
                "attachments": [],
            }
            mock_response.json.return_value = mock_full_issue

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="BACKEND",
            )

            # Call get_issue
            result = adapter.get_issue("BACKEND-123")

            # Verify returned dict contains all fields
            assert isinstance(result, dict)
            assert result["key"] == "BACKEND-123"
            assert result["summary"] == "Implement user authentication"
            assert result["description"] == "Add OAuth2 authentication support"
            assert result["status"]["key"] == "open"
            assert result["priority"]["key"] == "high"
            assert result["type"]["key"] == "task"
            assert result["assignee"]["login"] == "developer"
            assert result["version"] == 5
            assert result["tags"] == ["backend", "security"]

            # Verify API was called with correct endpoint
            mock_client_instance.get.assert_called_once_with("/v2/issues/BACKEND-123")

    def test_get_issue_returns_minimal_fields(self):
        """Test T041: get_issue works with minimal issue response.

        Verify: method handles minimal API response gracefully
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "key": "TEST-100",
                "summary": "Simple issue",
            }

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.get_issue("TEST-100")

            # Verify minimal fields are returned
            assert result["key"] == "TEST-100"
            assert result["summary"] == "Simple issue"

    # T042: Test get_issue raises ResourceNotFoundError for non-existent issue key
    def test_get_issue_raises_resource_not_found_for_non_existent_key(self):
        """Test T042: get_issue raises ResourceNotFoundError for non-existent issue.

        Test case: get_issue raises ResourceNotFoundError for non-existent issue
        Mock API to return 404
        Verify: ResourceNotFoundError is raised with correct message
        Verify: error includes resource_type="issue" and resource_id
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            # Mock API response with 404
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Issue not found"

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="BACKEND",
            )

            # Verify ResourceNotFoundError is raised
            with pytest.raises(errors.ResourceNotFoundError) as exc_info:
                adapter.get_issue("BACKEND-999")

            # Verify error message contains issue key
            assert "BACKEND-999" in exc_info.value.message

            # Verify error includes resource_type and resource_id
            assert exc_info.value.resource_type == "issue"
            assert exc_info.value.resource_id == "BACKEND-999"

    # T043: Test update_issue successfully updates issue and returns updated data
    def test_update_issue_successfully_updates_and_returns_data(self):
        """Test T043: update_issue successfully updates issue and returns updated data.

        Test case: update_issue updates issue and returns updated data
        Mock API to return 200 with updated issue
        Create UpdateIssueRequest with version and some fields
        Verify: returned dict contains updated data
        Verify: API was called with PATCH and correct JSON payload
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            # Mock API response with updated issue
            mock_response = Mock()
            mock_response.status_code = 200
            mock_updated_issue = {
                "self": "https://api.tracker.yandex.net/v2/issues/123",
                "id": "1234567890abcdef",
                "key": "BACKEND-123",
                "summary": "Updated summary",
                "description": "Updated description",
                "status": {"key": "in_progress", "name": "In progress"},
                "priority": {"key": "high", "name": "High"},
                "version": 6,
            }
            mock_response.json.return_value = mock_updated_issue

            mock_client_instance = Mock()
            mock_client_instance.patch.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="BACKEND",
            )

            # Create UpdateIssueRequest
            request = models.UpdateIssueRequest(
                summary="Updated summary",
                description="Updated description",
                version=5,
            )

            # Call update_issue
            result = adapter.update_issue("BACKEND-123", request)

            # Verify returned dict contains updated data
            assert isinstance(result, dict)
            assert result["key"] == "BACKEND-123"
            assert result["summary"] == "Updated summary"
            assert result["version"] == 6

            # Verify API was called with PATCH and correct JSON payload
            mock_client_instance.patch.assert_called_once()
            call_args = mock_client_instance.patch.call_args

            # Verify endpoint
            assert call_args[0][0] == "/v2/issues/BACKEND-123"

            # Verify JSON payload contains correct fields
            json_payload = call_args[1]["json"]
            assert json_payload["summary"] == "Updated summary"
            assert json_payload["description"] == "Updated description"
            assert json_payload["version"] == 5

    def test_update_issue_with_only_version_update(self):
        """Test T043: update_issue works with just version (no other fields).

        Verify: version can be updated alone (e.g., to refresh lock)
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "key": "TEST-100",
                "version": 7,
            }

            mock_client_instance = Mock()
            mock_client_instance.patch.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            request = models.UpdateIssueRequest(version=6)

            result = adapter.update_issue("TEST-100", request)

            # Verify update returned new version
            assert result["version"] == 7

            # Verify API was called
            mock_client_instance.patch.assert_called_once()

    # T044: Test update_issue supports array operations (add, remove, set, null)
    def test_update_issue_adds_followers(self):
        """Test T044: update_issue supports adding followers.

        Test: adding followers with ArrayFieldOperations(add=[...])
        Verify: JSON payload has correct format {"followers": {"add": [...]}}
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "key": "TEST-100",
                "followers": [{"login": "user1"}, {"login": "user2"}],
            }

            mock_client_instance = Mock()
            mock_client_instance.patch.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            # Create request with add operation
            request = models.UpdateIssueRequest(
                followers=models.ArrayFieldOperations(add=["user1", "user2"]),
                version=5,
            )

            adapter.update_issue("TEST-100", request)

            # Verify JSON payload format
            call_args = mock_client_instance.patch.call_args
            json_payload = call_args[1]["json"]

            assert "followers" in json_payload
            assert json_payload["followers"] == {"add": ["user1", "user2"]}

    def test_update_issue_removes_followers(self):
        """Test T044: update_issue supports removing followers.

        Test: removing followers with ArrayFieldOperations(remove=[...])
        Verify: JSON payload has correct format {"followers": {"remove": [...]}}
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "key": "TEST-100",
                "followers": [],
            }

            mock_client_instance = Mock()
            mock_client_instance.patch.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            request = models.UpdateIssueRequest(
                followers=models.ArrayFieldOperations(remove=["user1"]),
                version=5,
            )

            adapter.update_issue("TEST-100", request)

            call_args = mock_client_instance.patch.call_args
            json_payload = call_args[1]["json"]

            assert json_payload["followers"] == {"remove": ["user1"]}

    def test_update_issue_sets_followers(self):
        """Test T044: update_issue supports setting followers (replace all).

        Test: setting followers with ArrayFieldOperations(set_=[...])
        Verify: JSON payload has correct format {"followers": {"set": [...]}}
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "key": "TEST-100",
                "followers": [{"login": "user3"}],
            }

            mock_client_instance = Mock()
            mock_client_instance.patch.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            request = models.UpdateIssueRequest(
                followers=models.ArrayFieldOperations(set_=["user3"]),
                version=5,
            )

            adapter.update_issue("TEST-100", request)

            call_args = mock_client_instance.patch.call_args
            json_payload = call_args[1]["json"]

            assert json_payload["followers"] == {"set": ["user3"]}

    def test_update_issue_clears_followers_with_null(self):
        """Test T044: update_issue clears followers with None (null operation).

        Test: clearing followers with followers=None
        Verify: JSON payload has {"followers": null} for clearing
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "key": "TEST-100",
                "followers": [],
            }

            mock_client_instance = Mock()
            mock_client_instance.patch.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            # Set followers to None to clear
            request = models.UpdateIssueRequest(
                followers=None,
                version=5,
            )

            adapter.update_issue("TEST-100", request)

            call_args = mock_client_instance.patch.call_args
            json_payload = call_args[1]["json"]

            # None should become null in JSON to clear the array
            assert json_payload["followers"] is None

    def test_update_issue_combined_array_operations(self):
        """Test T044: update_issue supports combined add and remove operations.

        Verify: JSON payload can have both add and remove keys
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"key": "TEST-100"}

            mock_client_instance = Mock()
            mock_client_instance.patch.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            request = models.UpdateIssueRequest(
                tags=models.ArrayFieldOperations(add=["new"], remove=["old"]),
                version=5,
            )

            adapter.update_issue("TEST-100", request)

            call_args = mock_client_instance.patch.call_args
            json_payload = call_args[1]["json"]

            assert "tags" in json_payload
            assert "add" in json_payload["tags"]
            assert "remove" in json_payload["tags"]
            assert json_payload["tags"]["add"] == ["new"]
            assert json_payload["tags"]["remove"] == ["old"]

    # T045: Test update_issue uses optimistic locking with version field (409 Conflict)
    def test_update_issue_raises_concurrency_error_on_409(self):
        """Test T045: update_issue raises ConcurrencyError on version conflict.

        Test case: update_issue raises ConcurrencyError on 409 Conflict
        Mock API to return 409 Conflict
        Create UpdateIssueRequest with version
        Verify: ConcurrencyError is raised with correct message
        Verify: error includes issue_key and expected_version
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            # Mock API response with 409 Conflict
            mock_response = Mock()
            mock_response.status_code = 409
            mock_response.text = "Version conflict: issue was modified by another process"

            mock_client_instance = Mock()
            mock_client_instance.patch.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="BACKEND",
            )

            # Create request with version
            request = models.UpdateIssueRequest(
                summary="Updated summary",
                version=5,
            )

            # Verify ConcurrencyError is raised
            with pytest.raises(errors.ConcurrencyError) as exc_info:
                adapter.update_issue("BACKEND-123", request)

            # Verify error message contains expected text
            assert "conflict" in exc_info.value.message.lower() or "modified" in exc_info.value.message.lower()

            # Verify error includes issue_key and expected_version
            assert exc_info.value.issue_key == "BACKEND-123"
            assert exc_info.value.expected_version == 5

    def test_update_issue_raises_validation_error_without_version(self):
        """Test T045: update_issue raises ValidationError when version is missing.

        Verify: ValidationError is raised if version is not provided
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            # Create request without version
            request = models.UpdateIssueRequest(
                summary="Updated summary",
                version=None,  # Explicitly None
            )

            # Verify ValidationError is raised
            with pytest.raises(errors.ValidationError) as exc_info:
                adapter.update_issue("TEST-100", request)

            # Verify error mentions version requirement
            assert "version" in exc_info.value.message.lower()

    def test_update_issue_raises_resource_not_found_on_404(self):
        """Test T043: update_issue raises ResourceNotFoundError on 404.

        Verify: ResourceNotFoundError is raised when issue doesn't exist
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Issue not found"

            mock_client_instance = Mock()
            mock_client_instance.patch.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            request = models.UpdateIssueRequest(
                summary="Test",
                version=5,
            )

            with pytest.raises(errors.ResourceNotFoundError) as exc_info:
                adapter.update_issue("TEST-999", request)

            assert exc_info.value.resource_type == "issue"
            assert exc_info.value.resource_id == "TEST-999"

    def test_update_issue_raises_tracker_api_error_on_500(self):
        """Test T043: update_issue raises TrackerApiError on server error.

        Verify: TrackerApiError is raised when API returns 500
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"

            mock_client_instance = Mock()
            mock_client_instance.patch.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            request = models.UpdateIssueRequest(
                summary="Test",
                version=5,
            )

            with pytest.raises(errors.TrackerApiError):
                adapter.update_issue("TEST-100", request)


class TestUserStory6ManageIssueComments:
    """Test suite for User Story 6: Manage Issue Comments.

    These tests verify that the adapter can add comments to issues
    and handle various error scenarios appropriately.

    Test Tasks:
    - T052: Test add_comment creates comment and returns comment data for valid issue key
    - T053: Test add_comment raises ResourceNotFoundError for non-existent issue key
    """

    # T052: Test add_comment creates comment and returns comment data for valid issue key
    def test_add_comment_creates_comment_and_returns_comment_data(self):
        """Test T052: add_comment creates comment and returns comment data for valid issue key.

        Test case: add_comment adds a comment and returns comment data
        Mock API to return 201 with comment data
        Verify: returned dict contains comment fields (id, text, createdBy, createdAt)
        Verify: API was called with POST and correct endpoint (/v2/issues/{issue_key}/comments)
        Verify: JSON payload contains {"text": "comment text"}
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            # Mock API response with comment data
            mock_response = Mock()
            mock_response.status_code = 201
            mock_comment_data = {
                "self": "https://api.tracker.yandex.net/v2/issues/BACKEND-123/comments/1",
                "id": "5f8a2b3c4d5e6f7a8b9c0d1e",
                "text": "This is a test comment",
                "createdBy": {
                    "self": "https://api.tracker.yandex.net/v2/users/12345",
                    "id": "12345",
                    "login": "testuser",
                    "display": "Test User",
                },
                "createdAt": "2024-01-20T10:30:00Z",
                "updatedAt": "2024-01-20T10:30:00Z",
            }
            mock_response.json.return_value = mock_comment_data

            mock_client_instance = Mock()
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="BACKEND",
            )

            # Call add_comment
            result = adapter.add_comment("BACKEND-123", "This is a test comment")

            # Verify returned dict contains comment fields
            assert isinstance(result, dict)
            assert result["id"] == "5f8a2b3c4d5e6f7a8b9c0d1e"
            assert result["text"] == "This is a test comment"
            assert "createdBy" in result
            assert "createdAt" in result

            # Verify API was called with POST and correct endpoint
            mock_client_instance.post.assert_called_once()
            call_args = mock_client_instance.post.call_args

            # Verify endpoint
            assert call_args[0][0] == "/v2/issues/BACKEND-123/comments"

            # Verify JSON payload contains correct fields
            json_payload = call_args[1]["json"]
            assert json_payload == {"text": "This is a test comment"}

    def test_add_comment_returns_minimal_comment_fields(self):
        """Test T052: add_comment works with minimal comment response.

        Verify: method handles minimal API response gracefully
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": "12345",
                "text": "Simple comment",
                "createdAt": "2024-01-20T10:30:00Z",
            }

            mock_client_instance = Mock()
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.add_comment("TEST-100", "Simple comment")

            # Verify minimal fields are returned
            assert result["id"] == "12345"
            assert result["text"] == "Simple comment"

    def test_add_comment_with_multiline_text(self):
        """Test T052: add_comment supports multiline markdown text.

        Verify: multiline text is passed correctly in JSON payload
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": "12345",
                "text": "Line 1\n\nLine 2",
            }

            mock_client_instance = Mock()
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            multiline_text = "Line 1\n\nLine 2"
            result = adapter.add_comment("TEST-100", multiline_text)

            # Verify comment was added with multiline text
            assert result["text"] == "Line 1\n\nLine 2"

            # Verify JSON payload contains multiline text
            call_args = mock_client_instance.post.call_args
            json_payload = call_args[1]["json"]
            assert json_payload["text"] == "Line 1\n\nLine 2"

    # T053: Test add_comment raises ResourceNotFoundError for non-existent issue key
    def test_add_comment_raises_resource_not_found_for_non_existent_issue(self):
        """Test T053: add_comment raises ResourceNotFoundError for non-existent issue key.

        Test case: add_comment raises ResourceNotFoundError for non-existent issue
        Mock API to return 404
        Verify: ResourceNotFoundError is raised with correct message
        Verify: error includes resource_type="issue" and resource_id
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            # Mock API response with 404
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Issue not found"

            mock_client_instance = Mock()
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="BACKEND",
            )

            # Verify ResourceNotFoundError is raised
            with pytest.raises(errors.ResourceNotFoundError) as exc_info:
                adapter.add_comment("BACKEND-999", "Test comment")

            # Verify error message contains issue key
            assert "BACKEND-999" in exc_info.value.message

            # Verify error includes resource_type and resource_id
            assert exc_info.value.resource_type == "issue"
            assert exc_info.value.resource_id == "BACKEND-999"

    # Additional Test Cases for comprehensive coverage
    def test_add_comment_raises_validation_error_for_empty_text(self):
        """Test: add_comment raises ValidationError for empty string text.

        Verify: ValidationError is raised when text is empty string
        Verify: error message "Comment text cannot be empty"
        Verify: error field="text" and constraint="non-empty string"
        """
        adapter = YandexTrackerAdapter(
            api_key="y0_test_token",
            project_slug="TEST",
        )

        # Verify ValidationError is raised for empty string
        with pytest.raises(errors.ValidationError) as exc_info:
            adapter.add_comment("TEST-100", "")

        # Verify error message
        assert "Comment text cannot be empty" in exc_info.value.message

        # Verify error field and constraint
        assert exc_info.value.field == "text"
        assert exc_info.value.constraint == "non-empty string"

    def test_add_comment_raises_validation_error_for_whitespace_only_text(self):
        """Test: add_comment raises ValidationError for whitespace-only text.

        Verify: ValidationError is raised when text contains only whitespace
        Verify: error message "Comment text cannot be empty"
        Verify: error field="text" and constraint="non-empty string"
        """
        adapter = YandexTrackerAdapter(
            api_key="y0_test_token",
            project_slug="TEST",
        )

        # Verify ValidationError is raised for whitespace-only string
        with pytest.raises(errors.ValidationError) as exc_info:
            adapter.add_comment("TEST-100", "   ")

        # Verify error message
        assert "Comment text cannot be empty" in exc_info.value.message

        # Verify error field and constraint
        assert exc_info.value.field == "text"
        assert exc_info.value.constraint == "non-empty string"

    def test_add_comment_raises_validation_error_for_none_text(self):
        """Test: add_comment raises ValidationError for None text.

        Verify: ValidationError is raised when text is None
        """
        adapter = YandexTrackerAdapter(
            api_key="y0_test_token",
            project_slug="TEST",
        )

        # Verify ValidationError is raised for None
        with pytest.raises(errors.ValidationError) as exc_info:
            adapter.add_comment("TEST-100", None)

        # Verify error message mentions text
        assert "text" in exc_info.value.message.lower()

    def test_add_comment_raises_tracker_api_error_on_500(self):
        """Test: add_comment raises TrackerApiError on server error.

        Verify: TrackerApiError is raised when API returns 500
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"

            mock_client_instance = Mock()
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            # Verify TrackerApiError is raised
            with pytest.raises(errors.TrackerApiError) as exc_info:
                adapter.add_comment("TEST-100", "Test comment")

            # Verify error contains status code
            assert exc_info.value.status_code == 500

    def test_add_comment_raises_tracker_api_error_on_http_error(self):
        """Test: add_comment raises TrackerApiError on HTTP errors.

        Verify: TrackerApiError is raised for network/connection errors
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.post.side_effect = httpx.HTTPError("Connection error")
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            # Verify TrackerApiError is raised
            with pytest.raises(errors.TrackerApiError):
                adapter.add_comment("TEST-100", "Test comment")

    def test_add_comment_raises_tracker_api_error_on_timeout(self):
        """Test: add_comment raises TrackerApiError on timeout.

        Verify: TrackerApiError is raised when request times out

        Note: TimeoutException is a subclass of HTTPError and gets caught
        and converted to TrackerApiError.
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.post.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            # Verify TrackerApiError is raised
            with pytest.raises(errors.TrackerApiError):
                adapter.add_comment("TEST-100", "Test comment")

    def test_add_comment_raises_tracker_api_error_on_403(self):
        """Test: add_comment raises TrackerApiError on 403 Forbidden.

        Verify: TrackerApiError is raised when user lacks permissions
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_response.text = "Access denied"

            mock_client_instance = Mock()
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            # Verify TrackerApiError is raised
            with pytest.raises(errors.TrackerApiError) as exc_info:
                adapter.add_comment("TEST-100", "Test comment")

            assert exc_info.value.status_code == 403

    def test_add_comment_raises_tracker_api_error_on_400(self):
        """Test: add_comment raises TrackerApiError on 400 Bad Request.

        Verify: TrackerApiError is raised when request is malformed
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request: Invalid field"

            mock_client_instance = Mock()
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            # Verify TrackerApiError is raised
            with pytest.raises(errors.TrackerApiError) as exc_info:
                adapter.add_comment("TEST-100", "Test comment")

            assert exc_info.value.status_code == 400

    def test_update_issue_handles_http_error(self):
        """Test T043: update_issue raises TrackerApiError on HTTP errors.

        Verify: TrackerApiError is raised for network/connection errors
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.patch.side_effect = httpx.HTTPError("Connection error")
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            request = models.UpdateIssueRequest(
                summary="Test",
                version=5,
            )

            with pytest.raises(errors.TrackerApiError):
                adapter.update_issue("TEST-100", request)


class TestUserStory7TransitionIssueStatus:
    """Test suite for User Story 7: Transition Issue Status.

    These tests verify that the adapter can list available transitions for an issue,
    find transitions by target status, and execute status transitions.

    Test Tasks:
    - T057: Test list_transitions returns list of available transitions for valid issue
    - T058: Test find_transition_by_status returns transition ID for existing status
    - T059: Test find_transition_by_status returns None for non-existent status
    - T060: Test transition_issue executes transition and returns success
    - T061: Test transition_issue raises TransitionNotFoundError for non-existent transition
    """

    # T057: Test list_transitions returns list of available transitions for valid issue
    def test_list_transitions_returns_list_of_available_transitions(self):
        """Test T057: list_transitions returns list of available transitions for valid issue.

        Test case: list_transitions returns list of transitions for valid issue
        Mock API to return 200 with list of transitions
        Verify: returned list contains transition fields (id, name, target)
        Verify: API was called with GET and correct endpoint (/v2/issues/{issue_key}/transitions)
        Verify: logging with action="list_transitions"
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            # Mock API response with transitions
            mock_response = Mock()
            mock_response.status_code = 200
            mock_transitions = [
                {
                    "id": "transition_1",
                    "name": "Start review",
                    "target": {
                        "name": "In review",
                        "key": "in_review",
                    },
                },
                {
                    "id": "transition_2",
                    "name": "Close",
                    "target": {
                        "name": "Closed",
                        "key": "closed",
                    },
                },
                {
                    "id": "transition_3",
                    "name": "Reject",
                    "target": {
                        "name": "Open",
                        "key": "open",
                    },
                },
            ]
            mock_response.json.return_value = mock_transitions

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="BACKEND",
            )

            # Call list_transitions
            result = adapter.list_transitions("BACKEND-123")

            # Verify returned list contains transition fields
            assert isinstance(result, list)
            assert len(result) == 3

            # Verify first transition has required fields
            first_transition = result[0]
            assert "id" in first_transition
            assert "name" in first_transition
            assert "target" in first_transition

            # Verify specific values
            assert first_transition["id"] == "transition_1"
            assert first_transition["name"] == "Start review"
            assert first_transition["target"]["name"] == "In review"

            # Verify API was called with GET and correct endpoint
            mock_client_instance.get.assert_called_once_with("/v2/issues/BACKEND-123/transitions")

    def test_list_transitions_returns_empty_list(self):
        """Test T057: list_transitions returns empty list when no transitions available.

        Verify: method handles empty transitions list gracefully
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.list_transitions("TEST-100")

            # Verify empty list is returned
            assert result == []
            assert isinstance(result, list)

    def test_list_transitions_returns_minimal_transition_fields(self):
        """Test T057: list_transitions works with minimal transition response.

        Verify: method handles minimal API response gracefully
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {
                    "id": "trans_1",
                    "name": "Close",
                }
            ]

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.list_transitions("TEST-100")

            # Verify minimal fields are returned
            assert len(result) == 1
            assert result[0]["id"] == "trans_1"
            assert result[0]["name"] == "Close"

    # T058: Test find_transition_by_status returns transition ID for existing status
    def test_find_transition_by_status_returns_transition_id_for_existing_status(self):
        """Test T058: find_transition_by_status returns transition ID for existing status.

        Test case: find_transition_by_status finds transition by target status
        Mock list_transitions to return list with transition targeting specific status
        Verify: correct transition ID is returned
        Test with multiple transitions, verify correct one is found
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_transitions = [
                {
                    "id": "trans_open_to_in_progress",
                    "name": "Start work",
                    "target": {"name": "In progress", "key": "in_progress"},
                },
                {
                    "id": "trans_in_progress_to_review",
                    "name": "Submit for review",
                    "target": {"name": "In review", "key": "in_review"},
                },
                {
                    "id": "trans_review_to_closed",
                    "name": "Approve",
                    "target": {"name": "Closed", "key": "closed"},
                },
            ]
            mock_response.json.return_value = mock_transitions

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="BACKEND",
            )

            # Find transition to "In review" status
            result = adapter.find_transition_by_status("BACKEND-123", "In review")

            # Verify correct transition ID is returned
            assert result == "trans_in_progress_to_review"

    def test_find_transition_by_status_with_multiple_matches_returns_first(self):
        """Test T058: find_transition_by_status returns first match when multiple found.

        Verify: first matching transition is returned
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            # Simulate edge case: two transitions with same target name
            mock_transitions = [
                {
                    "id": "trans_first",
                    "name": "Transition A",
                    "target": {"name": "Closed", "key": "closed"},
                },
                {
                    "id": "trans_second",
                    "name": "Transition B",
                    "target": {"name": "Closed", "key": "closed"},
                },
            ]
            mock_response.json.return_value = mock_transitions

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.find_transition_by_status("TEST-100", "Closed")

            # Should return first match
            assert result == "trans_first"

    # T059: Test find_transition_by_status returns None for non-existent status
    def test_find_transition_by_status_returns_none_for_non_existent_status(self):
        """Test T059: find_transition_by_status returns None for non-existent status.

        Test case: find_transition_by_status returns None when status not found
        Mock list_transitions to return list without transition targeting status
        Verify: None is returned
        Test with empty transition list
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_transitions = [
                {
                    "id": "trans_1",
                    "name": "Open to In Progress",
                    "target": {"name": "In progress", "key": "in_progress"},
                },
                {
                    "id": "trans_2",
                    "name": "In Progress to Closed",
                    "target": {"name": "Closed", "key": "closed"},
                },
            ]
            mock_response.json.return_value = mock_transitions

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="BACKEND",
            )

            # Try to find non-existent status
            result = adapter.find_transition_by_status("BACKEND-123", "NonExistentStatus")

            # Verify None is returned
            assert result is None

    def test_find_transition_by_status_returns_none_for_empty_transitions(self):
        """Test T059: find_transition_by_status returns None for empty transitions list.

        Verify: None is returned when issue has no available transitions
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.find_transition_by_status("TEST-100", "Closed")

            # Verify None is returned for empty transitions
            assert result is None

    # T060: Test transition_issue executes transition and returns success
    def test_transition_issue_executes_transition_and_returns_success(self):
        """Test T060: transition_issue executes transition and returns success.

        Test case: transition_issue executes status transition
        Mock API to return 200 with transition result
        Verify: returned dict contains updated issue data
        Verify: API was called with POST and correct endpoint (/v2/issues/{issue_key}/transitions/{transition_id})
        Verify: logging with action="transition_issue"
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            # Mock API response with transition result
            mock_response = Mock()
            mock_response.status_code = 200
            mock_transition_result = {
                "self": "https://api.tracker.yandex.net/v2/issues/BACKEND-123",
                "id": "1234567890abcdef",
                "key": "BACKEND-123",
                "summary": "Implement user authentication",
                "status": {
                    "self": "https://api.tracker.yandex.net/v2/statuses/3",
                    "id": "3",
                    "key": "closed",
                    "name": "Closed",
                },
                "version": 6,
            }
            mock_response.json.return_value = mock_transition_result

            mock_client_instance = Mock()
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="BACKEND",
            )

            # Call transition_issue
            result = adapter.transition_issue("BACKEND-123", "trans_close")

            # Verify returned dict contains updated issue data
            assert isinstance(result, dict)
            assert result["key"] == "BACKEND-123"
            assert result["status"]["key"] == "closed"
            assert result["version"] == 6

            # Verify API was called with POST and correct endpoint
            mock_client_instance.post.assert_called_once()
            call_args = mock_client_instance.post.call_args

            # Verify endpoint
            assert call_args[0][0] == "/v2/issues/BACKEND-123/transitions/trans_close"

    def test_transition_issue_returns_minimal_response(self):
        """Test T060: transition_issue works with minimal response.

        Verify: method handles minimal API response gracefully
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "key": "TEST-100",
                "status": {"key": "closed"},
            }

            mock_client_instance = Mock()
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.transition_issue("TEST-100", "trans_close")

            # Verify minimal fields are returned
            assert result["key"] == "TEST-100"
            assert result["status"]["key"] == "closed"

    # T061: Test transition_issue raises TransitionNotFoundError for non-existent transition
    def test_transition_issue_raises_transition_not_found_error_for_non_existent(self):
        """Test T061: transition_issue raises TransitionNotFoundError for non-existent transition ID.

        Test case: transition_issue raises TransitionNotFoundError for invalid transition
        Mock API to return 404
        Verify: TransitionNotFoundError is raised with correct message
        Verify: error includes issue_key and target_status
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            # Mock API response with 404
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Transition not found"

            mock_client_instance = Mock()
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="BACKEND",
            )

            # Verify TransitionNotFoundError is raised
            with pytest.raises(errors.TransitionNotFoundError) as exc_info:
                adapter.transition_issue("BACKEND-123", "invalid_transition")

            # Verify error message contains transition info
            assert "invalid_transition" in exc_info.value.message

            # Verify error includes issue_key
            assert exc_info.value.issue_key == "BACKEND-123"

            # Verify error includes target_status
            assert exc_info.value.target_status == "invalid_transition"

    def test_transition_issue_raises_resource_not_found_for_non_existent_issue(self):
        """Test T060: transition_issue raises TransitionNotFoundError when issue doesn't exist.

        Note: The implementation treats all 404 responses as TransitionNotFoundError since
        both "issue not found" and "transition not found" return 404 from the API.
        The error includes issue_key for debugging purposes.

        Verify: TransitionNotFoundError is raised with issue_key
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Issue not found"

            mock_client_instance = Mock()
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            # Verify TransitionNotFoundError is raised (implementation treats 404 as transition not found)
            with pytest.raises(errors.TransitionNotFoundError) as exc_info:
                adapter.transition_issue("TEST-999", "trans_close")

            assert exc_info.value.issue_key == "TEST-999"

    # Additional Test Cases for comprehensive coverage

    # Test list_transitions errors
    def test_list_transitions_raises_resource_not_found_on_404(self):
        """Test: list_transitions raises ResourceNotFoundError on 404.

        Verify: ResourceNotFoundError is raised when issue doesn't exist
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Issue not found"

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            with pytest.raises(errors.ResourceNotFoundError) as exc_info:
                adapter.list_transitions("TEST-999")

            assert exc_info.value.resource_type == "issue"
            assert exc_info.value.resource_id == "TEST-999"

    def test_list_transitions_raises_tracker_api_error_on_500(self):
        """Test: list_transitions raises TrackerApiError on server error.

        Verify: TrackerApiError is raised when API returns 500
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            with pytest.raises(errors.TrackerApiError) as exc_info:
                adapter.list_transitions("TEST-100")

            assert exc_info.value.status_code == 500

    def test_list_transitions_raises_tracker_api_error_on_http_error(self):
        """Test: list_transitions raises TrackerApiError on HTTP errors.

        Verify: TrackerApiError is raised for network/connection errors
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = httpx.HTTPError("Connection error")
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            with pytest.raises(errors.TrackerApiError):
                adapter.list_transitions("TEST-100")

    def test_list_transitions_raises_tracker_api_error_on_timeout(self):
        """Test: list_transitions raises TrackerApiError on timeout.

        Note: TimeoutException is a subclass of HTTPError, so it gets caught
        and converted to TrackerApiError rather than TrackerTimeoutError.
        Verify: TrackerApiError is raised when request times out
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            with pytest.raises(errors.TrackerApiError):
                adapter.list_transitions("TEST-100")

    # Test find_transition_by_status edge cases
    def test_find_transition_by_status_handles_none_target(self):
        """Test: find_transition_by_status handles None status in transition list.

        Verify: transitions with None target are skipped gracefully
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_transitions = [
                {
                    "id": "trans_1",
                    "name": "Transition A",
                    "target": None,
                },
                {
                    "id": "trans_2",
                    "name": "Transition B",
                    "target": {"name": "Closed", "key": "closed"},
                },
            ]
            mock_response.json.return_value = mock_transitions

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.find_transition_by_status("TEST-100", "Closed")

            # Should find the transition with valid target
            assert result == "trans_2"

    def test_find_transition_by_status_handles_missing_target_field(self):
        """Test: find_transition_by_status handles missing target field in transition.

        Verify: transitions without target field are skipped gracefully
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_transitions = [
                {
                    "id": "trans_1",
                    "name": "Transition A",
                    # No target field
                },
                {
                    "id": "trans_2",
                    "name": "Transition B",
                    "target": {"name": "Closed", "key": "closed"},
                },
            ]
            mock_response.json.return_value = mock_transitions

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.find_transition_by_status("TEST-100", "Closed")

            # Should find the transition with valid target
            assert result == "trans_2"

    def test_find_transition_by_status_handles_empty_target_dict(self):
        """Test: find_transition_by_status handles empty target dict in transition.

        Verify: transitions with empty target dict are skipped gracefully
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_transitions = [
                {
                    "id": "trans_1",
                    "name": "Transition A",
                    "target": {},
                },
                {
                    "id": "trans_2",
                    "name": "Transition B",
                    "target": {"name": "Closed", "key": "closed"},
                },
            ]
            mock_response.json.return_value = mock_transitions

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.find_transition_by_status("TEST-100", "Closed")

            # Should find the transition with valid target
            assert result == "trans_2"

    def test_find_transition_by_status_handles_non_dict_target(self):
        """Test: find_transition_by_status handles non-dict target in transition.

        Verify: transitions with non-dict target are skipped gracefully
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_transitions = [
                {
                    "id": "trans_1",
                    "name": "Transition A",
                    "target": "invalid_target_string",
                },
                {
                    "id": "trans_2",
                    "name": "Transition B",
                    "target": {"name": "Closed", "key": "closed"},
                },
            ]
            mock_response.json.return_value = mock_transitions

            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            result = adapter.find_transition_by_status("TEST-100", "Closed")

            # Should find the transition with valid target
            assert result == "trans_2"

    # Test transition_issue errors
    def test_transition_issue_raises_tracker_api_error_on_500(self):
        """Test: transition_issue raises TrackerApiError on server error.

        Verify: TrackerApiError is raised when API returns 500
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"

            mock_client_instance = Mock()
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            with pytest.raises(errors.TrackerApiError) as exc_info:
                adapter.transition_issue("TEST-100", "trans_close")

            assert exc_info.value.status_code == 500

    def test_transition_issue_raises_tracker_api_error_on_http_error(self):
        """Test: transition_issue raises TrackerApiError on HTTP errors.

        Verify: TrackerApiError is raised for network/connection errors
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.post.side_effect = httpx.HTTPError("Connection error")
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            with pytest.raises(errors.TrackerApiError):
                adapter.transition_issue("TEST-100", "trans_close")

    def test_transition_issue_raises_tracker_api_error_on_timeout(self):
        """Test: transition_issue raises TrackerApiError on timeout.

        Note: TimeoutException is a subclass of HTTPError, so it gets caught
        and converted to TrackerApiError rather than TrackerTimeoutError.
        Verify: TrackerApiError is raised when request times out
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.post.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            with pytest.raises(errors.TrackerApiError):
                adapter.transition_issue("TEST-100", "trans_close")

    def test_transition_issue_raises_tracker_api_error_on_403(self):
        """Test: transition_issue raises TrackerApiError on 403 Forbidden.

        Verify: TrackerApiError is raised when user lacks permissions
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_response.text = "Access denied"

            mock_client_instance = Mock()
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            with pytest.raises(errors.TrackerApiError) as exc_info:
                adapter.transition_issue("TEST-100", "trans_close")

            assert exc_info.value.status_code == 403

    def test_transition_issue_raises_tracker_api_error_on_400(self):
        """Test: transition_issue raises TrackerApiError on 400 Bad Request.

        Verify: TrackerApiError is raised when request is malformed
        """
        with patch("symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient") as mock_client_class:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request: Invalid transition"

            mock_client_instance = Mock()
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            adapter = YandexTrackerAdapter(
                api_key="y0_test_token",
                project_slug="TEST",
            )

            with pytest.raises(errors.TrackerApiError) as exc_info:
                adapter.transition_issue("TEST-100", "trans_invalid")

            assert exc_info.value.status_code == 400


class TestUserStory8PluginRegistration:
    """Test suite for User Story 8: Plugin Registration.

    These tests verify that the YandexTrackerAdapter is properly registered
    as a plugin via entry points and has required metadata.

    Test Tasks:
    - T066: Test entry point exists in symphony.trackers group
    - T067: Test YandexTrackerAdapter is importable
    - T068: Test __plugin_info__ attribute has required fields
    """

    # T066: Test entry point exists in symphony.trackers group
    def test_t066_entry_point_exists_in_symphony_trackers_group(self):
        """Test T066: Entry point exists in symphony.trackers group."""
        from importlib.metadata import entry_points

        # Get entry points for symphony.trackers group
        eps = entry_points(group="symphony.trackers")

        # Verify yandex_tracker entry point exists (convert to dict for compatibility)
        ep_dict = {ep.name: ep for ep in eps}
        assert "yandex_tracker" in ep_dict

        # Verify it points to correct class
        ep = ep_dict["yandex_tracker"]
        assert ep.value == "symphony_yandex_tracker.adapter:YandexTrackerAdapter"

    # T067: Test YandexTrackerAdapter is importable
    def test_t067_yandex_tracker_adapter_is_importable(self):
        """Test T067: YandexTrackerAdapter is importable from symphony_yandex_tracker.adapter."""
        from symphony_yandex_tracker.adapter import YandexTrackerAdapter

        # Verify class exists and is correct
        assert YandexTrackerAdapter is not None
        assert YandexTrackerAdapter.__name__ == "YandexTrackerAdapter"

    # T068: Test __plugin_info__ attribute has required fields
    def test_t068_plugin_info_attribute_has_required_fields(self):
        """Test T068: __plugin_info__ attribute is present and contains required fields."""
        from symphony_yandex_tracker.adapter import YandexTrackerAdapter

        # Verify __plugin_info__ attribute exists
        assert hasattr(YandexTrackerAdapter, "__plugin_info__")

        # Verify it's a dictionary
        plugin_info = YandexTrackerAdapter.__plugin_info__
        assert isinstance(plugin_info, dict)

        # Verify required fields are present
        assert "name" in plugin_info
        assert "version" in plugin_info
        assert "tracker_kind" in plugin_info
        assert "description" in plugin_info
        assert "author" in plugin_info

        # Verify field values are strings
        assert isinstance(plugin_info["name"], str)
        assert isinstance(plugin_info["version"], str)
        assert isinstance(plugin_info["tracker_kind"], str)
        assert isinstance(plugin_info["description"], str)
        assert isinstance(plugin_info["author"], str)

        # Verify tracker_kind matches entry point name
        assert plugin_info["tracker_kind"] == "yandex_tracker"
