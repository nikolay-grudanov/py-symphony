"""Tests for User Story 8 - Plugin Entry Point Registration.

This module contains tests to verify that the Yandex Tracker adapter
is properly registered as a plugin through entry points.

Test Tasks:
- T066: Verify entry point is registered in symphony.trackers group
- T067: Verify YandexTrackerAdapter can be imported from symphony_yandex_tracker.adapter
- T068: Verify __plugin_info__ attribute contains all required fields

Note: These tests follow TDD approach - they should fail until the plugin
is properly implemented and registered.
"""

import pytest
from importlib.metadata import entry_points


class TestPluginEntryPointRegistration:
    """Test suite for plugin entry point registration (US8)."""

    def test_t066_entry_point_exists_in_symphony_trackers_group(self):
        """T066: Verify entry point is registered in symphony.trackers group.

        This test checks that the yandex_tracker entry point is properly
        registered in the symphony.trackers group, which allows the plugin
        to be discovered by the Symphony orchestration platform.
        """
        # Get entry points for the 'symphony.trackers' group
        # In Python 3.12+, the API changed: entry_points() returns a SelectableGroups object
        # For compatibility, we try both approaches
        try:
            # Python 3.12+ approach
            eps = entry_points()
            tracker_eps = eps.select(group="symphony.trackers")
        except AttributeError:
            # Python 3.10-3.11 approach
            eps = entry_points()
            tracker_eps = eps.get("symphony.trackers", [])

        # Find the yandex_tracker entry point
        yandex_ep = None
        for ep in tracker_eps:
            if ep.name == "yandex_tracker":
                yandex_ep = ep
                break

        assert yandex_ep is not None, (
            "Entry point 'yandex_tracker' not found in 'symphony.trackers' group. "
            "The plugin must be properly registered via pyproject.toml entry-points."
        )

        # Verify the entry point resolves to the correct class
        assert (
            yandex_ep.value == "symphony_yandex_tracker.adapter:YandexTrackerAdapter"
        ), (
            f"Entry point value mismatch. Expected "
            f"'symphony_yandex_tracker.adapter:YandexTrackerAdapter', "
            f"got '{yandex_ep.value}'"
        )

    def test_t067_yandex_tracker_adapter_is_importable(self):
        """T067: Verify YandexTrackerAdapter is importable from symphony_yandex_tracker.adapter.

        This test ensures that the adapter class can be imported from the
        expected module path, which is required for the entry point to work.
        """
        from symphony_yandex_tracker.adapter import YandexTrackerAdapter

        # Verify it's actually a class
        assert isinstance(YandexTrackerAdapter, type), (
            "YandexTrackerAdapter should be a class, not a module or other object"
        )

        # Verify it has the expected interface (basic check)
        assert hasattr(YandexTrackerAdapter, "__init__"), (
            "YandexTrackerAdapter should have an __init__ method"
        )

    def test_t068_plugin_info_attribute_has_required_fields(self):
        """T068: Verify __plugin_info__ attribute is present and contains required fields.

        The __plugin_info__ attribute should contain:
        - name: Plugin name
        - version: Plugin version
        - tracker_kind: Type of tracker (e.g., 'yandex_tracker')
        - description: Plugin description
        - author: Plugin author
        """
        from symphony_yandex_tracker.adapter import YandexTrackerAdapter

        # Check __plugin_info__ attribute exists
        assert hasattr(YandexTrackerAdapter, "__plugin_info__"), (
            "YandexTrackerAdapter must have __plugin_info__ attribute for plugin discovery"
        )

        plugin_info = YandexTrackerAdapter.__plugin_info__

        # Verify it's a dictionary
        assert isinstance(plugin_info, dict), (
            f"__plugin_info__ should be a dict, got {type(plugin_info).__name__}"
        )

        # Required fields that must be present
        required_fields = ["name", "version", "tracker_kind", "description", "author"]

        for field in required_fields:
            assert field in plugin_info, (
                f"__plugin_info__ must contain '{field}' field. "
                f"Current fields: {list(plugin_info.keys())}"
            )

            # Verify the field is not empty
            assert plugin_info[field], f"__plugin_info__['{field}'] must not be empty"

        # Verify tracker_kind matches expected value
        assert plugin_info["tracker_kind"] == "yandex_tracker", (
            f"tracker_kind should be 'yandex_tracker', got '{plugin_info['tracker_kind']}'"
        )

        # Verify name is the expected plugin name
        assert plugin_info["name"] == "symphony-yandex-tracker", (
            f"name should be 'symphony-yandex-tracker', got '{plugin_info['name']}'"
        )
