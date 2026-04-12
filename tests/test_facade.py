"""Tests for tracker facade."""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock

from runtime.symphony.tracker import Issue, Tracker
from runtime.tracker.compat import AsyncTrackerWrapper
from runtime.tracker.facade import TrackerFacade, create_facade
from runtime.tracker.feature_flags import FeatureFlags


@pytest.fixture
def mock_old_tracker():
    """Mock old tracker."""
    tracker = MagicMock(spec=Tracker)
    tracker.fetch_candidate_issues = AsyncMock(
        return_value=[
            Issue(
                id="old-1",
                identifier="OLD-1",
                title="Old Issue",
                description="Old description",
                priority=1,
                state="Todo",
                branch_name="old-branch",
                url="https://example.com/old-1",
                labels=[],
                blocked_by=[],
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            )
        ]
    )
    tracker.fetch_issues_by_states = AsyncMock(return_value=[])
    tracker.fetch_issue_states = AsyncMock(return_value={})
    return tracker


@pytest.fixture
def mock_new_tracker():
    """Mock new tracker wrapper."""
    wrapper = MagicMock(spec=AsyncTrackerWrapper)
    wrapper.fetch_candidate_issues = AsyncMock(
        return_value=[
            Issue(
                id="new-1",
                identifier="NEW-1",
                title="New Issue",
                description="New description",
                priority=1,
                state="Todo",
                branch_name="new-branch",
                url="https://example.com/new-1",
                labels=[],
                blocked_by=[],
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
            )
        ]
    )
    wrapper.fetch_issues_by_states = AsyncMock(return_value=[])
    wrapper.fetch_issue_states = AsyncMock(return_value={})
    return wrapper


@pytest.fixture
def mock_config():
    """Mock configuration."""
    config = MagicMock()
    config.tracker_kind = "linear"
    config.tracker_api_key = "test-key"
    config.tracker_project_slug = "test-project"
    config.tracker_endpoint = "https://api.linear.app/graphql"
    return config


def test_facade_uses_old_tracker_when_disabled(mock_old_tracker, mock_new_tracker):
    """Test facade routes to old tracker when migration disabled."""
    flags = FeatureFlags(migration_enabled=False)
    facade = TrackerFacade(
        old_tracker=mock_old_tracker,
        new_tracker_wrapper=mock_new_tracker,
        feature_flags=flags,
    )

    result = asyncio.run(facade.fetch_candidate_issues())

    assert len(result) == 1
    assert result[0].identifier == "OLD-1"
    mock_old_tracker.fetch_candidate_issues.assert_called_once()
    mock_new_tracker.fetch_candidate_issues.assert_not_called()


def test_facade_uses_new_tracker_when_enabled(mock_old_tracker, mock_new_tracker):
    """Test facade routes to new tracker when migration enabled."""
    flags = FeatureFlags(migration_enabled=True)
    facade = TrackerFacade(
        old_tracker=mock_old_tracker,
        new_tracker_wrapper=mock_new_tracker,
        feature_flags=flags,
    )

    result = asyncio.run(facade.fetch_candidate_issues())

    assert len(result) == 1
    assert result[0].identifier == "NEW-1"
    mock_new_tracker.fetch_candidate_issues.assert_called_once()
    mock_old_tracker.fetch_candidate_issues.assert_not_called()


def test_facade_auto_rollback_on_error(mock_old_tracker, mock_new_tracker):
    """Test facade auto-rolls back to old tracker on error."""
    flags = FeatureFlags(migration_enabled=True, auto_rollback_enabled=True)
    facade = TrackerFacade(
        old_tracker=mock_old_tracker,
        new_tracker_wrapper=mock_new_tracker,
        feature_flags=flags,
    )

    # Make new tracker fail
    mock_new_tracker.fetch_candidate_issues.side_effect = Exception(
        "New tracker failed"
    )

    # Should fall back to old tracker
    result = asyncio.run(facade.fetch_candidate_issues())

    assert len(result) == 1
    assert result[0].identifier == "OLD-1"
    assert not facade._using_new_tracker  # Should have switched back


def test_facade_runtime_switch_to_new(mock_old_tracker, mock_new_tracker):
    """Test runtime switch to new tracker."""
    flags = FeatureFlags(migration_enabled=True)
    facade = TrackerFacade(
        old_tracker=mock_old_tracker,
        new_tracker_wrapper=mock_new_tracker,
        feature_flags=flags,
    )

    # Start with old
    facade._using_new_tracker = False

    # Switch to new
    asyncio.run(facade.switch_to_new_tracker())
    assert facade._using_new_tracker

    result = asyncio.run(facade.fetch_candidate_issues())
    assert result[0].identifier == "NEW-1"


def test_facade_runtime_switch_to_old(mock_old_tracker, mock_new_tracker):
    """Test runtime switch to old tracker (rollback)."""
    flags = FeatureFlags(migration_enabled=True)
    facade = TrackerFacade(
        old_tracker=mock_old_tracker,
        new_tracker_wrapper=mock_new_tracker,
        feature_flags=flags,
    )

    # Start with new
    facade._using_new_tracker = True

    # Switch to old
    asyncio.run(facade.switch_to_old_tracker())
    assert not facade._using_new_tracker

    result = asyncio.run(facade.fetch_candidate_issues())
    assert result[0].identifier == "OLD-1"


def test_facade_migration_status(mock_old_tracker, mock_new_tracker):
    """Test migration status reporting."""
    flags = FeatureFlags(migration_enabled=True)
    facade = TrackerFacade(
        old_tracker=mock_old_tracker,
        new_tracker_wrapper=mock_new_tracker,
        feature_flags=flags,
    )

    status = facade.get_migration_status()

    assert status["using_new_tracker"] == True
    assert status["migration_enabled"] == True
    assert status["old_tracker_present"] == True
    assert status["new_tracker_present"] == True


def test_facade_migration_status_old_only(mock_old_tracker):
    """Test migration status with only old tracker."""
    flags = FeatureFlags(migration_enabled=False)
    facade = TrackerFacade(
        old_tracker=mock_old_tracker,
        new_tracker_wrapper=None,
        feature_flags=flags,
    )

    status = facade.get_migration_status()

    assert status["using_new_tracker"] == False
    assert status["migration_enabled"] == False
    assert status["old_tracker_present"] == True
    assert status["new_tracker_present"] == False


def test_facade_switch_to_new_without_new_tracker():
    """Test switching to new tracker when it's not initialized."""
    facade = TrackerFacade(
        old_tracker=None,
        new_tracker_wrapper=None,
        feature_flags=FeatureFlags(),
    )

    with pytest.raises(
        RuntimeError, match="Cannot switch: new tracker not initialized"
    ):
        asyncio.run(facade.switch_to_new_tracker())


def test_facade_switch_to_old_without_old_tracker():
    """Test switching to old tracker when it's not initialized."""
    facade = TrackerFacade(
        old_tracker=None,
        new_tracker_wrapper=None,
        feature_flags=FeatureFlags(),
    )

    with pytest.raises(
        RuntimeError, match="Cannot switch: old tracker not initialized"
    ):
        asyncio.run(facade.switch_to_old_tracker())


def test_facade_fetch_issues_by_states_routing(mock_old_tracker, mock_new_tracker):
    """Test fetch_issues_by_states routes correctly."""
    flags = FeatureFlags(migration_enabled=True)
    facade = TrackerFacade(
        old_tracker=mock_old_tracker,
        new_tracker_wrapper=mock_new_tracker,
        feature_flags=flags,
    )

    # Test with new tracker enabled
    states = ["Done", "Cancelled"]
    asyncio.run(facade.fetch_issues_by_states(states))
    mock_new_tracker.fetch_issues_by_states.assert_called_once_with(states)

    # Test with old tracker
    facade._using_new_tracker = False
    asyncio.run(facade.fetch_issues_by_states(states))
    mock_old_tracker.fetch_issues_by_states.assert_called_once_with(states)


def test_facade_fetch_issue_states_routing(mock_old_tracker, mock_new_tracker):
    """Test fetch_issue_states routes correctly."""
    flags = FeatureFlags(migration_enabled=True)
    facade = TrackerFacade(
        old_tracker=mock_old_tracker,
        new_tracker_wrapper=mock_new_tracker,
        feature_flags=flags,
    )

    # Test with new tracker enabled
    issue_ids = ["issue-1", "issue-2"]
    asyncio.run(facade.fetch_issue_states(issue_ids))
    mock_new_tracker.fetch_issue_states.assert_called_once_with(issue_ids)

    # Test with old tracker
    facade._using_new_tracker = False
    asyncio.run(facade.fetch_issue_states(issue_ids))
    mock_old_tracker.fetch_issue_states.assert_called_once_with(issue_ids)


def test_facade_no_auto_rollback_when_disabled(mock_old_tracker, mock_new_tracker):
    """Test facade doesn't auto-rollback when disabled."""
    flags = FeatureFlags(migration_enabled=True, auto_rollback_enabled=False)
    facade = TrackerFacade(
        old_tracker=mock_old_tracker,
        new_tracker_wrapper=mock_new_tracker,
        feature_flags=flags,
    )

    # Make new tracker fail
    mock_new_tracker.fetch_candidate_issues.side_effect = Exception(
        "New tracker failed"
    )

    # Should raise error instead of rolling back
    with pytest.raises(Exception, match="New tracker failed"):
        asyncio.run(facade.fetch_candidate_issues())

    # Should still be using new tracker
    assert facade._using_new_tracker
