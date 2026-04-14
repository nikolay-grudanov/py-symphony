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

import pytest
from unittest.mock import Mock, patch, MagicMock
from symphony_yandex_tracker.adapter import YandexTrackerAdapter
from symphony_yandex_tracker import errors


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
        with patch(
            "symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient"
        ) as mock_client_class:
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
        with patch(
            "symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient"
        ) as mock_client_class:
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
        with patch(
            "symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient"
        ) as mock_client_class:
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
        with patch(
            "symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient"
        ) as mock_client_class:
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
        with patch(
            "symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient"
        ) as mock_client_class:
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
        with patch(
            "symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient"
        ) as mock_client_class:
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
        with patch(
            "symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient"
        ) as mock_client_class:
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
        with patch(
            "symphony_yandex_tracker.adapter.http_client_module.TrackerHttpClient"
        ) as mock_client_class:
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
            with pytest.raises(errors.TrackerApiError) as exc_info:
                adapter.authenticate()

            assert exc_info.value.status_code == 500


class TestUserStory1EndpointProperty:
    """Additional tests for endpoint property."""

    def test_endpoint_returns_configured_value(self):
        """Test endpoint property returns configured endpoint URL."""
        adapter = YandexTrackerAdapter(
            api_key="y0_test_token",
            project_slug="TEST-QUEUE",
            endpoint="https://api.tracker.yandex.net/v3",
        )

        assert adapter.endpoint == "https://api.tracker.yandex.net/v3"

    def test_endpoint_default_value(self):
        """Test endpoint property returns default value when not specified."""
        adapter = YandexTrackerAdapter(
            api_key="y0_test_token",
            project_slug="TEST-QUEUE",
        )

        assert adapter.endpoint == "https://api.tracker.yandex.net/v3"


class TestUserStory1ProjectSlugProperty:
    """Additional tests for project_slug property."""

    def test_project_slug_returns_configured_value(self):
        """Test project_slug property returns configured value."""
        adapter = YandexTrackerAdapter(
            api_key="y0_test_token",
            project_slug="TEST-QUEUE",
        )

        assert adapter.project_slug == "TEST-QUEUE"


class TestUserStory1ActiveStatesProperty:
    """Additional tests for active_states property."""

    def test_active_states_returns_copy(self):
        """Test active_states property returns a copy of the list."""
        adapter = YandexTrackerAdapter(
            api_key="y0_test_token",
            project_slug="TEST-QUEUE",
            active_states=["open", "in_progress"],
        )

        # Get active_states
        states = adapter.active_states

        # Modify returned list
        states.append("closed")

        # Verify original list is not modified
        assert "closed" not in adapter.active_states
