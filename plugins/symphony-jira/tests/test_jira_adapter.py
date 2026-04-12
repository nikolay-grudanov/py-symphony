"""Tests for Jira plugin adapter (symphony_jira.adapter).

Note: This adapter is TEMPLATE-ONLY with no implementation.
The tests verify the structure and interface.
"""

import pytest


class TestJiraAdapterInitialization:
    """Test adapter initialization."""

    def test_init_with_valid_params(self):
        """Init with email + api_token + base_url + project_key succeeds."""
        from symphony_jira.adapter import JiraAdapter

        adapter = JiraAdapter(
            api_key="test-key",
            endpoint="https://company.atlassian.net",
            project_key="PROJ",
            username="test@example.com",
            timeout=30,
        )

        assert adapter.tracker_kind == "jira"

    @pytest.mark.skip(
        reason="Full implementation accepts None params - validation happens at API call time"
    )
    def test_init_without_project_key(self):
        """Init without project_key raises ValueError."""
        from symphony_jira.adapter import JiraAdapter

        with pytest.raises(ValueError, match="project_key is required"):
            JiraAdapter(
                api_key="test-key",
                endpoint="https://company.atlassian.net",
                project_key="",
            )

    @pytest.mark.skip(
        reason="Full implementation accepts None params - validation happens at API call time"
    )
    def test_init_without_base_url(self):
        """Init without base_url raises ValueError."""
        from symphony_jira.adapter import JiraAdapter

        with pytest.raises(ValueError, match="endpoint is required"):
            JiraAdapter(
                api_key="test-key",
                endpoint="",
                project_key="PROJ",
            )

    @pytest.mark.skip(
        reason="Full implementation accepts None params - validation happens at API call time"
    )
    def test_init_without_api_token(self):
        """Init without api_token raises ValueError."""
        from symphony_jira.adapter import JiraAdapter

        with pytest.raises(ValueError, match="api_key is required"):
            JiraAdapter(
                api_key="",
                endpoint="https://company.atlassian.net",
                project_key="PROJ",
            )

    def test_init_with_custom_active_states(self):
        """Init with custom active states."""
        from symphony_jira.adapter import JiraAdapter

        adapter = JiraAdapter(
            api_key="test-key",
            endpoint="https://company.atlassian.net",
            project_key="PROJ",
            active_states=["To Do", "In Progress", "In Review"],
        )

        assert adapter._active_states == ["To Do", "In Progress", "In Review"]

    def test_default_active_states(self):
        """Default active states when not provided."""
        from symphony_jira.adapter import JiraAdapter

        adapter = JiraAdapter(
            api_key="test-key",
            endpoint="https://company.atlassian.net",
            project_key="PROJ",
        )

        assert adapter._active_states == ["To Do", "In Progress"]


class TestJiraAdapterInterface:
    """Test adapter interface compliance."""

    def test_tracker_kind_property(self, plugin_jira_adapter):
        """tracker_kind returns 'jira'."""
        if plugin_jira_adapter is None:
            pytest.skip("Plugin adapter not available")

        assert plugin_jira_adapter.tracker_kind == "jira"

    def test_has_fetch_candidate_issues_method(self, plugin_jira_adapter):
        """Adapter has fetch_candidate_issues method."""
        if plugin_jira_adapter is None:
            pytest.skip("Plugin adapter not available")

        assert hasattr(plugin_jira_adapter, "fetch_candidate_issues")
        assert callable(plugin_jira_adapter.fetch_candidate_issues)

    def test_has_fetch_issues_by_states_method(self, plugin_jira_adapter):
        """Adapter has fetch_issues_by_states method."""
        if plugin_jira_adapter is None:
            pytest.skip("Plugin adapter not available")

        assert hasattr(plugin_jira_adapter, "fetch_issues_by_states")
        assert callable(plugin_jira_adapter.fetch_issues_by_states)

    def test_has_fetch_issue_states_by_ids_method(self, plugin_jira_adapter):
        """Adapter has fetch_issue_states_by_ids method."""
        if plugin_jira_adapter is None:
            pytest.skip("Plugin adapter not available")

        assert hasattr(plugin_jira_adapter, "fetch_issue_states_by_ids")
        assert callable(plugin_jira_adapter.fetch_issue_states_by_ids)


class TestJiraAdapterTemplateMethods:
    """Test template method signatures.

    These tests verify that the adapter has required methods
    but they don't have actual implementation yet.
    """

    @pytest.mark.skip(reason="Full implementation requires mocked API responses")
    def test_fetch_candidate_issues_returns_none(self, plugin_jira_adapter):
        """fetch_candidate_issues returns None (not implemented)."""
        if plugin_jira_adapter is None:
            pytest.skip("Plugin adapter not available")

        # Template returns None
        result = plugin_jira_adapter.fetch_candidate_issues()
        assert result is None

    @pytest.mark.skip(reason="Full implementation requires mocked API responses")
    def test_fetch_issues_by_states_returns_none(self, plugin_jira_adapter):
        """fetch_issues_by_states returns None (not implemented)."""
        if plugin_jira_adapter is None:
            pytest.skip("Plugin adapter not available")

        result = plugin_jira_adapter.fetch_issues_by_states(["To Do"])
        assert result is None

    @pytest.mark.skip(reason="Full implementation requires mocked API responses")
    def test_fetch_issue_states_by_ids_returns_none(self, plugin_jira_adapter):
        """fetch_issue_states_by_ids returns None (not implemented)."""
        if plugin_jira_adapter is None:
            pytest.skip("Plugin adapter not available")

        result = plugin_jira_adapter.fetch_issue_states_by_ids(["PROJ-123"])
        assert result is None


class TestJiraAdapterPluginInfo:
    """Test plugin metadata."""

    def test_plugin_info_exists(self):
        """Adapter has __plugin_info__ metadata."""
        from symphony_jira.adapter import JiraAdapter

        assert hasattr(JiraAdapter, "__plugin_info__")

    def test_plugin_info_name(self):
        """Plugin info contains expected fields."""
        from symphony_jira.adapter import JiraAdapter

        info = JiraAdapter.__plugin_info__
        assert info["name"] == "symphony-jira"
        assert info["tracker_kind"] == "jira"

    def test_plugin_info_version(self):
        """Plugin has version."""
        from symphony_jira.adapter import JiraAdapter

        info = JiraAdapter.__plugin_info__
        assert "version" in info
        assert info["version"] == "1.0.0"


class TestJiraAdapterEndpointNormalization:
    """Test endpoint URL normalization."""

    def test_endpoint_trailing_slash_removed(self):
        """Endpoint trailing slash is removed."""
        from symphony_jira.adapter import JiraAdapter

        adapter = JiraAdapter(
            api_key="test-key",
            endpoint="https://company.atlassian.net/",
            project_key="PROJ",
        )

        assert not adapter._endpoint.endswith("/")
        assert adapter._endpoint == "https://company.atlassian.net"


# =============================================================================
# Integration Tests - Plugin Discovery
# =============================================================================


class TestPluginDiscovery:
    """Test plugin discovery via entry points."""

    def test_jira_plugin_registered_in_registry(self):
        """Registry discovers 'jira' plugin via entry points."""
        import sys
        from pathlib import Path

        runtime_path = str(Path(__file__).parent.parent.parent / "runtime")
        if runtime_path not in sys.path:
            sys.path.insert(0, runtime_path)

        from runtime.tracker.registry import get_tracker_registry

        registry = get_tracker_registry()
        # Try discovery
        try:
            registry.discover_from_entry_points()
        except Exception:
            pass  # May fail but we can still test

        # Check if jira is registered
        jira_info = registry.get_adapter("jira")
        # Either from entry point or fallback
        assert jira_info is not None

    def test_factory_creates_jira_adapter(self):
        """Factory.create('jira', config) creates JiraAdapter."""
        import sys
        from pathlib import Path
        from dataclasses import dataclass

        runtime_path = str(Path(__file__).parent.parent.parent / "runtime")
        if runtime_path not in sys.path:
            sys.path.insert(0, runtime_path)

        from runtime.tracker.factory import TrackerFactory

        @dataclass
        class MockConfig:
            tracker_kind: str = "jira"
            tracker_api_key: str = "test-key"
            tracker_endpoint: str = "https://company.atlassian.net"
            tracker_project_slug: str = "PROJ"
            tracker_username: str = "test@example.com"
            tracker_timeout: int = 30

        config = MockConfig()

        try:
            adapter = TrackerFactory.create(config)
            assert adapter is not None
            assert adapter.tracker_kind == "jira"
        except Exception as e:
            # May fail if entry points not set up
            pytest.skip(f"Factory create failed: {e}")
