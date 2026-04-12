# Tracker Migration Implementation Plan

**Document Version**: 1.0
**Last Updated**: April 12, 2026
**Author**: Symphony Development Team
**Status**: Draft

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites Checklist](#prerequisites-checklist)
3. [Phase 1: Compatibility Layer](#phase-1-compatibility-layer-2-3-hours)
4. [Phase 2: TrackerFacade](#phase-2-trackerfacade-1-2-hours)
5. [Phase 3: Feature Flags System](#phase-3-feature-flags-system-1-hour)
6. [Phase 4: Orchestrator Integration](#phase-4-orchestrator-integration-1-2-hours)
7. [Phase 5: Testing & Verification](#phase-5-testing--verification-3-4-hours)
8. [Migration Day Checklist](#migration-day-checklist)
9. [Rollback Procedures](#rollback-procedures)
10. [Verification Commands](#verification-commands)

---

## Overview

### Purpose

This document provides a step-by-step guide for migrating the Orchestrator from the old monolithic tracker architecture to the new pluggable tracker architecture. The migration will be performed using the **Strangler Fig pattern** combined with **Feature Flags** to ensure gradual rollout and quick rollback capability.

### Risk Level

**MEDIUM-HIGH**

Justification:
- Core system component (tracker) being replaced
- Risk of breaking issue tracking and workflow orchestration
- Mitigated by gradual rollout and auto-rollback features
- Reversible at any point during migration

### Estimated Total Time

**8-12 hours** (excluding code review and final approval)

### Migration Pattern

**Strangler Fig + Feature Flags**

- **Strangler Fig**: Gradually replace old tracker with new tracker through a facade
- **Feature Flags**: Control rollout percentage and enable instant rollback
- **Compatibility Layer**: Maintain old API while using new implementation
- **Auto-Rollback**: Automatically revert to old tracker on errors

---

## Prerequisites Checklist

Complete ALL items before starting the migration:

- [ ] **Verify current codebase state** (git status clean)
  ```bash
  git status
  # Should show no uncommitted changes
  ```

- [ ] **Create feature branch**
  ```bash
  git checkout -b feature/tracker-migration
  ```

- [ ] **Backup current configuration**
  ```bash
  cp WORKFLOW.md WORKFLOW.md.backup
  cp config/symphony.yaml config/symphony.yaml.backup
  ```

- [ ] **Verify test infrastructure is working**
  ```bash
  make test
  # Or: pytest runtime/tests/ -v
  ```

- [ ] **Review migration strategy document**
  ```bash
  cat docs/tracker-migration-strategy.md
  # Ensure you understand the strategy and risks
  ```

- [ ] **Prepare rollback procedures**
  - Verify rollback procedures are documented in strategy document
  - Test rollback in staging environment (if available)

- [ ] **Notify team members about migration window**
  - Send notification to team
  - Schedule maintenance window if needed

---

## Phase 1: Compatibility Layer (2-3 hours)

**Goal**: Create a compatibility layer that makes the new synchronous tracker client compatible with the old asynchronous API.

### Task 1.1: Create `runtime/tracker/compat.py`

**File Location**: `runtime/tracker/compat.py`

**Description**: Implement AsyncTrackerWrapper class that wraps the new sync TrackerClient and provides async methods expected by the Orchestrator.

**Code to create**:

```python
"""Compatibility layer for migrating from old to new tracker architecture."""

import asyncio
import logging
from dataclasses import asdict, replace
from typing import Any, Dict, List, Optional

from symphony.tracker import Issue  # Old Issue dataclass
from tracker.base import TrackerClient  # New base interface

logger = logging.getLogger(__name__)


class AsyncTrackerWrapper:
    """Wrapper to make new sync TrackerClient compatible with old async API.

    The new TrackerClient uses synchronous methods, but the old Orchestrator
    expects async methods. This wrapper provides async wrappers around the
    sync methods using asyncio.to_thread().
    """

    def __init__(self, tracker_client: TrackerClient):
        """Initialize with a new tracker client instance.

        Args:
            tracker_client: New TrackerClient instance (sync methods)
        """
        self._client = tracker_client
        self._executor = None

    async def fetch_candidate_issues(self) -> List[Issue]:
        """Fetch candidate issues async wrapper.

        Returns:
            List of Issue objects (old dataclass format)
        """
        logger.debug("AsyncTrackerWrapper: fetch_candidate_issues")

        # Call sync method in thread pool
        result = await asyncio.to_thread(
            self._client.fetch_candidate_issues
        )

        # Convert dict issues to Issue dataclass
        return [self._dict_to_issue(issue_dict) for issue_dict in result]

    async def fetch_issues_by_states(self, states: List[str]) -> List[Issue]:
        """Fetch issues by states async wrapper.

        Args:
            states: List of state names

        Returns:
            List of Issue objects (old dataclass format)
        """
        logger.debug(f"AsyncTrackerWrapper: fetch_issues_by_states(states={states})")

        result = await asyncio.to_thread(
            self._client.fetch_issues_by_states,
            states
        )

        return [self._dict_to_issue(issue_dict) for issue_dict in result]

    async def fetch_issue_states(self, issue_ids: List[str]) -> Dict[str, str]:
        """Fetch issue states async wrapper.

        Note: Method name differs from new API (fetch_issue_states vs fetch_issue_states_by_ids)

        Args:
            issue_ids: List of issue IDs

        Returns:
            Dict mapping issue_id -> state_name
        """
        logger.debug(f"AsyncTrackerWrapper: fetch_issue_states(issue_ids={len(issue_ids)})")

        result = await asyncio.to_thread(
            self._client.fetch_issue_states_by_ids,
            issue_ids
        )

        return result

    def _dict_to_issue(self, issue_dict: Dict[str, Any]) -> Issue:
        """Convert dict issue to old Issue dataclass.

        Args:
            issue_dict: Issue dictionary from new tracker

        Returns:
            Issue dataclass (old format)
        """
        # Extract fields with proper defaults
        return Issue(
            id=issue_dict.get("id", ""),
            identifier=issue_dict.get("identifier", ""),
            title=issue_dict.get("title", ""),
            description=issue_dict.get("description"),
            priority=issue_dict.get("priority"),
            state=issue_dict.get("state", ""),
            branch_name=issue_dict.get("branch_name"),
            url=issue_dict.get("url"),
            labels=issue_dict.get("labels", []),
            blocked_by=issue_dict.get("blocked_by", []),
            created_at=issue_dict.get("created_at"),
            updated_at=issue_dict.get("updated_at"),
        )
```

### Task 1.2: Create `runtime/tests/test_compat.py`

**File Location**: `runtime/tests/test_compat.py`

**Description**: Unit tests for AsyncTrackerWrapper and IssueWrapper.

**Code to create**:

```python
"""Tests for compatibility layer."""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock

from symphony.tracker import Issue
from tracker.compat import AsyncTrackerWrapper
from tracker.base import TrackerClient


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


@pytest.mark.asyncio
async def test_fetch_candidate_issues(async_wrapper, mock_new_tracker):
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
    result = await async_wrapper.fetch_candidate_issues()

    # Verify result is Issue dataclass
    assert len(result) == 1
    assert isinstance(result[0], Issue)
    assert result[0].identifier == "TEST-1"
    assert result[0].title == "Test Issue"


@pytest.mark.asyncio
async def test_fetch_issues_by_states(async_wrapper, mock_new_tracker):
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

    result = await async_wrapper.fetch_issues_by_states(states)

    assert len(result) == 1
    assert result[0].state == "Done"
    mock_new_tracker.fetch_issues_by_states.assert_called_once_with(states)


@pytest.mark.asyncio
async def test_fetch_issue_states(async_wrapper, mock_new_tracker):
    """Test fetching issue states."""
    issue_ids = ["issue-1", "issue-2"]

    mock_new_tracker.fetch_issue_states_by_ids.return_value = {
        "issue-1": "In Progress",
        "issue-2": "Todo",
    }

    result = await async_wrapper.fetch_issue_states(issue_ids)

    assert result["issue-1"] == "In Progress"
    assert result["issue-2"] == "Todo"
    mock_new_tracker.fetch_issue_states_by_ids.assert_called_once_with(issue_ids)


@pytest.mark.asyncio
async def test_dict_to_issue_conversion(async_wrapper):
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
```

### Acceptance Criteria

- [ ] All unit tests pass: `pytest runtime/tests/test_compat.py -v`
- [ ] AsyncTrackerWrapper successfully wraps sync TrackerClient
- [ ] All old API methods work (fetch_candidate_issues, fetch_issues_by_states, fetch_issue_states)
- [ ] Dict issues are correctly converted to Issue dataclass
- [ ] All optional fields handle None gracefully

### Rollback Procedures

If issues arise during this phase:

1. Delete compatibility layer:
   ```bash
   rm runtime/tracker/compat.py
   rm runtime/tests/test_compat.py
   ```

2. Verify tests still pass with old implementation:
   ```bash
   pytest runtime/tests/ -v
   ```

### Estimated Time

**2-3 hours**

---

## Phase 2: TrackerFacade (1-2 hours)

**Goal**: Create a facade that routes between old and new tracker based on feature flags, with auto-rollback capability.

### Task 2.1: Create `runtime/tracker/facade.py`

**File Location**: `runtime/tracker/facade.py`

**Description**: Implement TrackerFacade that routes to old or new tracker based on feature flag configuration.

**Code to create**:

```python
"""Tracker facade for migration routing."""

import logging
from typing import List, Dict, Optional

from symphony.tracker import Issue, Tracker  # Old tracker
from tracker.compat import AsyncTrackerWrapper  # Compatibility wrapper
from tracker.factory import TrackerFactory  # New factory
from tracker.feature_flags import FeatureFlags  # Feature flags

logger = logging.getLogger(__name__)


class TrackerFacade:
    """Facade for routing between old and new tracker during migration.

    This facade implements the old Tracker API interface and routes
    calls to either the old tracker or the new tracker based on
    feature flag configuration. This enables gradual rollout and
    quick rollback if needed.
    """

    def __init__(
        self,
        old_tracker: Optional[Tracker],
        new_tracker_wrapper: Optional[AsyncTrackerWrapper],
        feature_flags: FeatureFlags,
    ):
        """Initialize facade with both trackers.

        Args:
            old_tracker: Old Tracker instance (can be None if not using)
            new_tracker_wrapper: New tracker wrapped in AsyncTrackerWrapper
            feature_flags: Feature flag configuration
        """
        self._old_tracker = old_tracker
        self._new_tracker = new_tracker_wrapper
        self._feature_flags = feature_flags

        # Track which tracker is being used
        self._using_new_tracker = feature_flags.migration_enabled

        logger.info(
            f"TrackerFacade initialized: using_new={self._using_new_tracker}, "
            f"old_tracker={'present' if old_tracker else 'none'}, "
            f"new_tracker={'present' if new_tracker_wrapper else 'none'}"
        )

    async def fetch_candidate_issues(self) -> List[Issue]:
        """Fetch candidate issues using appropriate tracker.

        Routes to old or new tracker based on feature flag.

        Returns:
            List of Issue objects
        """
        if self._using_new_tracker:
            return await self._fetch_candidate_issues_new()
        else:
            return await self._fetch_candidate_issues_old()

    async def _fetch_candidate_issues_new(self) -> List[Issue]:
        """Fetch from new tracker (via wrapper)."""
        logger.debug("TrackerFacade: fetching candidates from NEW tracker")

        try:
            result = await self._new_tracker.fetch_candidate_issues()
            logger.info(f"TrackerFacade: fetched {len(result)} candidates from NEW tracker")
            return result
        except Exception as e:
            logger.error(f"TrackerFacade: NEW tracker error: {e}")
            if self._feature_flags.auto_rollback_enabled:
                logger.warning("TrackerFacade: Auto-rolling back to OLD tracker")
                self._using_new_tracker = False
                return await self._fetch_candidate_issues_old()
            raise

    async def _fetch_candidate_issues_old(self) -> List[Issue]:
        """Fetch from old tracker."""
        logger.debug("TrackerFacade: fetching candidates from OLD tracker")
        result = await self._old_tracker.fetch_candidate_issues()
        logger.info(f"TrackerFacade: fetched {len(result)} candidates from OLD tracker")
        return result

    async def fetch_issues_by_states(self, states: List[str]) -> List[Issue]:
        """Fetch issues by states using appropriate tracker."""
        if self._using_new_tracker:
            return await self._new_tracker.fetch_issues_by_states(states)
        else:
            return await self._old_tracker.fetch_issues_by_states(states)

    async def fetch_issue_states(self, issue_ids: List[str]) -> Dict[str, str]:
        """Fetch issue states using appropriate tracker."""
        if self._using_new_tracker:
            return await self._new_tracker.fetch_issue_states(issue_ids)
        else:
            return await self._old_tracker.fetch_issue_states(issue_ids)

    def get_migration_status(self) -> Dict[str, any]:
        """Get current migration status for observability.

        Returns:
            Dict with migration status info
        """
        return {
            "using_new_tracker": self._using_new_tracker,
            "migration_enabled": self._feature_flags.migration_enabled,
            "auto_rollback_enabled": self._feature_flags.auto_rollback_enabled,
            "rollback_mode": self._feature_flags.rollback_mode,
            "old_tracker_present": self._old_tracker is not None,
            "new_tracker_present": self._new_tracker is not None,
        }

    async def switch_to_new_tracker(self) -> None:
        """Switch to using new tracker.

        Can be used for runtime migration without restart.
        """
        if self._new_tracker is None:
            raise RuntimeError("Cannot switch: new tracker not initialized")

        logger.info("TrackerFacade: switching to NEW tracker")
        self._using_new_tracker = True

    async def switch_to_old_tracker(self) -> None:
        """Switch to using old tracker.

        Can be used for runtime rollback.
        """
        if self._old_tracker is None:
            raise RuntimeError("Cannot switch: old tracker not initialized")

        logger.warning("TrackerFacade: switching to OLD tracker (rollback)")
        self._using_new_tracker = False


def create_facade(
    old_tracker: Optional[Tracker],
    config,
    feature_flags: Optional[FeatureFlags] = None,
) -> TrackerFacade:
    """Create tracker facade with appropriate configuration.

    Args:
        old_tracker: Old Tracker instance (optional)
        config: Configuration object
        feature_flags: Feature flags (will create default if None)

    Returns:
        Configured TrackerFacade instance
    """
    if feature_flags is None:
        feature_flags = FeatureFlags()

    # Create new tracker if migration is enabled
    new_tracker_wrapper = None
    if feature_flags.migration_enabled:
        try:
            # Create new tracker using factory
            new_tracker = TrackerFactory.create(config)
            # Wrap in async wrapper
            new_tracker_wrapper = AsyncTrackerWrapper(new_tracker)
            logger.info("TrackerFacade: new tracker created successfully")
        except Exception as e:
            logger.error(f"TrackerFacade: failed to create new tracker: {e}")
            # Disable migration if new tracker creation fails
            feature_flags.migration_enabled = False

    return TrackerFacade(
        old_tracker=old_tracker,
        new_tracker_wrapper=new_tracker_wrapper,
        feature_flags=feature_flags,
    )
```

### Task 2.2: Create `runtime/tests/test_facade.py`

**File Location**: `runtime/tests/test_facade.py`

**Description**: Integration tests for TrackerFacade including routing logic and auto-rollback.

**Code to create**:

```python
"""Tests for tracker facade."""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock

from symphony.tracker import Issue, Tracker
from tracker.compat import AsyncTrackerWrapper
from tracker.facade import TrackerFacade, create_facade
from tracker.feature_flags import FeatureFlags


@pytest.fixture
def mock_old_tracker():
    """Mock old tracker."""
    tracker = MagicMock(spec=Tracker)
    tracker.fetch_candidate_issues = AsyncMock(return_value=[
        Issue(id="old-1", identifier="OLD-1", title="Old Issue", state="Todo",
              labels=[], blocked_by=[])
    ])
    tracker.fetch_issues_by_states = AsyncMock(return_value=[])
    tracker.fetch_issue_states = AsyncMock(return_value={})
    return tracker


@pytest.fixture
def mock_new_tracker():
    """Mock new tracker wrapper."""
    wrapper = MagicMock(spec=AsyncTrackerWrapper)
    wrapper.fetch_candidate_issues = AsyncMock(return_value=[
        Issue(id="new-1", identifier="NEW-1", title="New Issue", state="Todo",
              labels=[], blocked_by=[])
    ])
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


@pytest.mark.asyncio
async def test_facade_uses_old_tracker_when_disabled(mock_old_tracker, mock_new_tracker):
    """Test facade routes to old tracker when migration disabled."""
    flags = FeatureFlags(migration_enabled=False)
    facade = TrackerFacade(
        old_tracker=mock_old_tracker,
        new_tracker_wrapper=mock_new_tracker,
        feature_flags=flags,
    )

    result = await facade.fetch_candidate_issues()

    assert len(result) == 1
    assert result[0].identifier == "OLD-1"
    mock_old_tracker.fetch_candidate_issues.assert_called_once()
    mock_new_tracker.fetch_candidate_issues.assert_not_called()


@pytest.mark.asyncio
async def test_facade_uses_new_tracker_when_enabled(mock_old_tracker, mock_new_tracker):
    """Test facade routes to new tracker when migration enabled."""
    flags = FeatureFlags(migration_enabled=True)
    facade = TrackerFacade(
        old_tracker=mock_old_tracker,
        new_tracker_wrapper=mock_new_tracker,
        feature_flags=flags,
    )

    result = await facade.fetch_candidate_issues()

    assert len(result) == 1
    assert result[0].identifier == "NEW-1"
    mock_new_tracker.fetch_candidate_issues.assert_called_once()
    mock_old_tracker.fetch_candidate_issues.assert_not_called()


@pytest.mark.asyncio
async def test_facade_auto_rollback_on_error(mock_old_tracker, mock_new_tracker):
    """Test facade auto-rolls back to old tracker on error."""
    flags = FeatureFlags(migration_enabled=True, auto_rollback_enabled=True)
    facade = TrackerFacade(
        old_tracker=mock_old_tracker,
        new_tracker_wrapper=mock_new_tracker,
        feature_flags=flags,
    )

    # Make new tracker fail
    mock_new_tracker.fetch_candidate_issues.side_effect = Exception("New tracker failed")

    # Should fall back to old tracker
    result = await facade.fetch_candidate_issues()

    assert len(result) == 1
    assert result[0].identifier == "OLD-1"
    assert not facade._using_new_tracker  # Should have switched back


@pytest.mark.asyncio
async def test_facade_runtime_switch_to_new(mock_old_tracker, mock_new_tracker):
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
    await facade.switch_to_new_tracker()
    assert facade._using_new_tracker

    result = await facade.fetch_candidate_issues()
    assert result[0].identifier == "NEW-1"


@pytest.mark.asyncio
async def test_facade_runtime_switch_to_old(mock_old_tracker, mock_new_tracker):
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
    await facade.switch_to_old_tracker()
    assert not facade._using_new_tracker

    result = await facade.fetch_candidate_issues()
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
```

### Acceptance Criteria

- [ ] All tests pass: `pytest runtime/tests/test_facade.py -v`
- [ ] TrackerFacade correctly routes based on feature flags
- [ ] Auto-rollback works on new tracker errors
- [ ] Runtime switch to new/old tracker works
- [ ] Migration status is correctly reported

### Rollback Procedures

If issues arise during this phase:

1. Delete facade:
   ```bash
   rm runtime/tracker/facade.py
   rm runtime/tests/test_facade.py
   ```

2. Revert any changes to imports in other files

### Estimated Time

**1-2 hours**

---

## Phase 3: Feature Flags System (1 hour)

**Goal**: Implement feature flag system to control migration rollout.

### Task 3.1: Create `runtime/tracker/feature_flags.py`

**File Location**: `runtime/tracker/feature_flags.py`

**Description**: Implement feature flag system with environment variables.

**Code to create**:

```python
"""Feature flags for tracker migration."""

import os
import logging

logger = logging.getLogger(__name__)


class FeatureFlags:
    """Feature flags for controlling tracker migration rollout.

    Flags can be set via environment variables:
    - SYMPHONY_TRACKER_MIGRATION_ENABLED: Enable new tracker (default: false)
    - SYMPHONY_TRACKER_AUTO_ROLLBACK_ENABLED: Enable auto-rollback on error (default: true)
    - SYMPHONY_TRACKER_ROLLBACK_MODE: Rollback mode 'auto' or 'manual' (default: auto)

    Example:
        export SYMPHONY_TRACKER_MIGRATION_ENABLED=true
        export SYMPHONY_TRACKER_AUTO_ROLLBACK_ENABLED=true
    """

    def __init__(
        self,
        migration_enabled: Optional[bool] = None,
        auto_rollback_enabled: Optional[bool] = None,
        rollback_mode: Optional[str] = None,
    ):
        """Initialize feature flags.

        Args:
            migration_enabled: Enable new tracker (defaults to env var)
            auto_rollback_enabled: Enable auto-rollback (defaults to env var)
            rollback_mode: Rollback mode (defaults to env var)
        """
        self.migration_enabled = self._parse_bool(
            migration_enabled,
            os.getenv("SYMPHONY_TRACKER_MIGRATION_ENABLED", "false").lower(),
            False
        )

        self.auto_rollback_enabled = self._parse_bool(
            auto_rollback_enabled,
            os.getenv("SYMPHONY_TRACKER_AUTO_ROLLBACK_ENABLED", "true").lower(),
            True
        )

        self.rollback_mode = rollback_mode or os.getenv(
            "SYMPHONY_TRACKER_ROLLBACK_MODE", "auto"
        )

        # Validate rollback mode
        if self.rollback_mode not in ["auto", "manual"]:
            logger.warning(
                f"Invalid rollback_mode '{self.rollback_mode}', using 'auto'"
            )
            self.rollback_mode = "auto"

        logger.info(
            f"FeatureFlags initialized: migration_enabled={self.migration_enabled}, "
            f"auto_rollback_enabled={self.auto_rollback_enabled}, "
            f"rollback_mode={self.rollback_mode}"
        )

    def _parse_bool(
        self,
        value: Optional[bool],
        env_value: str,
        default: bool
    ) -> bool:
        """Parse boolean value from parameter or environment.

        Args:
            value: Explicit value (takes precedence)
            env_value: Environment variable value as string
            default: Default value if both are None/empty

        Returns:
            Boolean value
        """
        if value is not None:
            return value

        if env_value in ["true", "1", "yes", "on"]:
            return True
        elif env_value in ["false", "0", "no", "off", ""]:
            return False
        else:
            logger.warning(f"Cannot parse bool from '{env_value}', using default {default}")
            return default

    def enable_migration(self) -> None:
        """Enable migration at runtime."""
        logger.info("FeatureFlags: enabling migration")
        self.migration_enabled = True

    def disable_migration(self) -> None:
        """Disable migration at runtime (rollback)."""
        logger.warning("FeatureFlags: disabling migration (rollback)")
        self.migration_enabled = False

    def set_rollback_mode(self, mode: str) -> None:
        """Set rollback mode.

        Args:
            mode: Either 'auto' or 'manual'
        """
        if mode not in ["auto", "manual"]:
            raise ValueError(f"Invalid rollback mode: {mode}")

        logger.info(f"FeatureFlags: setting rollback_mode={mode}")
        self.rollback_mode = mode

    def to_dict(self) -> dict:
        """Convert feature flags to dict for observability.

        Returns:
            Dict with all flag values
        """
        return {
            "migration_enabled": self.migration_enabled,
            "auto_rollback_enabled": self.auto_rollback_enabled,
            "rollback_mode": self.rollback_mode,
        }


# Global instance for easy access
_flags: Optional[FeatureFlags] = None


def get_feature_flags() -> FeatureFlags:
    """Get global feature flags instance.

    Creates instance if not already initialized.

    Returns:
        FeatureFlags instance
    """
    global _flags
    if _flags is None:
        _flags = FeatureFlags()
    return _flags


def reset_feature_flags() -> None:
    """Reset global feature flags (mainly for testing)."""
    global _flags
    _flags = None
```

### Task 3.2: Create `runtime/tests/test_feature_flags.py`

**File Location**: `runtime/tests/test_feature_flags.py`

**Description**: Unit tests for feature flags system.

**Code to create**:

```python
"""Tests for feature flags."""

import os
import pytest

from tracker.feature_flags import FeatureFlags, get_feature_flags, reset_feature_flags


def test_feature_flags_defaults():
    """Test default feature flag values."""
    # Clear environment
    os.environ.pop("SYMPHONY_TRACKER_MIGRATION_ENABLED", None)
    os.environ.pop("SYMPHONY_TRACKER_AUTO_ROLLBACK_ENABLED", None)
    os.environ.pop("SYMPHONY_TRACKER_ROLLBACK_MODE", None)

    flags = FeatureFlags()

    assert flags.migration_enabled == False  # Default
    assert flags.auto_rollback_enabled == True  # Default
    assert flags.rollback_mode == "auto"


def test_feature_flags_from_env():
    """Test feature flags from environment variables."""
    os.environ["SYMPHONY_TRACKER_MIGRATION_ENABLED"] = "true"
    os.environ["SYMPHONY_TRACKER_AUTO_ROLLBACK_ENABLED"] = "false"
    os.environ["SYMPHONY_TRACKER_ROLLBACK_MODE"] = "manual"

    try:
        flags = FeatureFlags()

        assert flags.migration_enabled == True
        assert flags.auto_rollback_enabled == False
        assert flags.rollback_mode == "manual"
    finally:
        os.environ.pop("SYMPHONY_TRACKER_MIGRATION_ENABLED", None)
        os.environ.pop("SYMPHONY_TRACKER_AUTO_ROLLBACK_ENABLED", None)
        os.environ.pop("SYMPHONY_TRACKER_ROLLBACK_MODE", None)


def test_feature_flags_explicit_values():
    """Test explicit values override environment."""
    os.environ["SYMPHONY_TRACKER_MIGRATION_ENABLED"] = "true"

    try:
        flags = FeatureFlags(migration_enabled=False)

        assert flags.migration_enabled == False  # Explicit wins
    finally:
        os.environ.pop("SYMPHONY_TRACKER_MIGRATION_ENABLED", None)


def test_feature_flags_bool_parsing():
    """Test boolean parsing from environment."""
    test_cases = [
        ("true", True),
        ("false", False),
        ("1", True),
        ("0", False),
        ("yes", True),
        ("no", False),
        ("on", True),
        ("off", False),
    ]

    for env_value, expected in test_cases:
        os.environ["SYMPHONY_TRACKER_MIGRATION_ENABLED"] = env_value
        try:
            flags = FeatureFlags()
            assert flags.migration_enabled == expected
        finally:
            os.environ.pop("SYMPHONY_TRACKER_MIGRATION_ENABLED", None)


def test_feature_flags_invalid_bool():
    """Test invalid boolean values use default."""
    os.environ["SYMPHONY_TRACKER_MIGRATION_ENABLED"] = "invalid"

    try:
        flags = FeatureFlags()
        assert flags.migration_enabled == False  # Default used
    finally:
        os.environ.pop("SYMPHONY_TRACKER_MIGRATION_ENABLED", None)


def test_feature_flags_invalid_rollback_mode():
    """Test invalid rollback mode uses default."""
    os.environ["SYMPHONY_TRACKER_ROLLBACK_MODE"] = "invalid"

    try:
        flags = FeatureFlags()
        assert flags.rollback_mode == "auto"  # Default used
    finally:
        os.environ.pop("SYMPHONY_TRACKER_ROLLBACK_MODE", None)


def test_feature_flags_runtime_enable():
    """Test runtime enable migration."""
    flags = FeatureFlags(migration_enabled=False)
    assert flags.migration_enabled == False

    flags.enable_migration()
    assert flags.migration_enabled == True


def test_feature_flags_runtime_disable():
    """Test runtime disable migration."""
    flags = FeatureFlags(migration_enabled=True)
    assert flags.migration_enabled == True

    flags.disable_migration()
    assert flags.migration_enabled == False


def test_feature_flags_set_rollback_mode():
    """Test setting rollback mode."""
    flags = FeatureFlags()
    assert flags.rollback_mode == "auto"

    flags.set_rollback_mode("manual")
    assert flags.rollback_mode == "manual"

    flags.set_rollback_mode("auto")
    assert flags.rollback_mode == "auto"


def test_feature_flags_invalid_rollback_mode_raises():
    """Test invalid rollback mode raises error."""
    flags = FeatureFlags()

    with pytest.raises(ValueError, match="Invalid rollback mode"):
        flags.set_rollback_mode("invalid")


def test_feature_flags_to_dict():
    """Test converting feature flags to dict."""
    flags = FeatureFlags(
        migration_enabled=True,
        auto_rollback_enabled=False,
        rollback_mode="manual"
    )

    result = flags.to_dict()

    assert result == {
        "migration_enabled": True,
        "auto_rollback_enabled": False,
        "rollback_mode": "manual",
    }


def test_global_feature_flags():
    """Test global feature flags instance."""
    reset_feature_flags()

    flags1 = get_feature_flags()
    flags2 = get_feature_flags()

    assert flags1 is flags2  # Same instance


def test_reset_feature_flags():
    """Test resetting global feature flags."""
    flags1 = get_feature_flags()
    flags1.migration_enabled = True

    reset_feature_flags()

    flags2 = get_feature_flags()
    assert flags2.migration_enabled == False  # New instance
    assert flags1 is not flags2
```

### Acceptance Criteria

- [ ] All tests pass: `pytest runtime/tests/test_feature_flags.py -v`
- [ ] Feature flags read from environment variables
- [ ] Explicit values override environment
- [ ] Runtime enable/disable works
- [ ] Invalid values use defaults with warnings

### Rollback Procedures

If issues arise during this phase:

1. Delete feature flags:
   ```bash
   rm runtime/tracker/feature_flags.py
   rm runtime/tests/test_feature_flags.py
   ```

2. Remove any references to feature flags from other files

### Estimated Time

**1 hour**

---

## Phase 4: Orchestrator Integration (1-2 hours)

**Goal**: Integrate the new tracker facade into the Orchestrator.

### Task 4.1: Modify `runtime/symphony/orchestrator.py`

**File Location**: `runtime/symphony/orchestrator.py`

**Description**: Update Orchestrator to use TrackerFacade instead of direct Tracker instance.

#### Step 4.1.a: Update imports (around line 12)

**BEFORE:**
```python
from .tracker import Issue, Tracker
```

**AFTER:**
```python
from .tracker import Issue  # Keep Issue for now
# from .tracker import Tracker  # Remove old Tracker import
from ..tracker.facade import TrackerFacade, create_facade  # New facade
from ..tracker.feature_flags import get_feature_flags  # Feature flags
```

#### Step 4.1.b: Update `__init__` signature (around line 103)

**BEFORE:**
```python
def __init__(
    self,
    config: Config,
    tracker: Tracker,
    workspace_manager: WorkspaceManager,
    agent_runner: AgentRunner,
):
    self.config = config
    self.tracker = tracker
```

**AFTER:**
```python
def __init__(
    self,
    config: Config,
    tracker_facade: TrackerFacade,  # Changed from tracker: Tracker
    workspace_manager: WorkspaceManager,
    agent_runner: AgentRunner,
):
    self.config = config
    self.tracker_facade = tracker_facade  # Changed from self.tracker
```

#### Step 4.1.c: Update all tracker method calls to use facade

Replace all occurrences of `self.tracker` with `self.tracker_facade`:

**Line 194:**
```python
# BEFORE:
candidates = await self.tracker.fetch_candidate_issues()

# AFTER:
candidates = await self.tracker_facade.fetch_candidate_issues()
```

**Line 218:**
```python
# BEFORE:
terminal_issues = await self.tracker.fetch_issues_by_states(...)

# AFTER:
terminal_issues = await self.tracker_facade.fetch_issues_by_states(...)
```

**Line 247:**
```python
# BEFORE:
current_states = await self.tracker.fetch_issue_states(running_ids)

# AFTER:
current_states = await self.tracker_facade.fetch_issue_states(running_ids)
```

**Line 766:**
```python
# BEFORE:
candidates = await self.tracker.fetch_candidate_issues()

# AFTER:
candidates = await self.tracker_facade.fetch_candidate_issues()
```

#### Step 4.1.d: Add migration status to `get_state_snapshot` (around line 1238)

**BEFORE return statement:**
```python
migration_status = self.tracker_facade.get_migration_status()

# Then update return dict:
return {
    "running": running,
    "retrying": retrying,
    "codex_totals": self.state.codex_totals,
    "rate_limits": self.state.rate_limits,
    "polling": polling,
    "migration": migration_status,  # Add this
}
```

### Task 4.2: Modify main entry point to create facade

**File Location**: `runtime/main.py` (or wherever Orchestrator is instantiated)

**Description**: Update main entry point to create tracker facade.

**BEFORE:**
```python
from symphony.tracker import create_tracker
tracker = create_tracker(config)
orchestrator = Orchestrator(
    config=config,
    tracker=tracker,
    workspace_manager=workspace_manager,
    agent_runner=agent_runner,
)
```

**AFTER:**
```python
from symphony.tracker import create_tracker, Tracker  # Old tracker for backup
from tracker.facade import create_facade
from tracker.feature_flags import get_feature_flags

# Create old tracker (for fallback)
old_tracker = None
try:
    old_tracker = create_tracker(config)
except Exception as e:
    logger.warning(f"Failed to create old tracker: {e}")

# Get feature flags
feature_flags = get_feature_flags()

# Create facade with both trackers
tracker_facade = create_facade(
    old_tracker=old_tracker,
    config=config,
    feature_flags=feature_flags,
)

orchestrator = Orchestrator(
    config=config,
    tracker_facade=tracker_facade,
    workspace_manager=workspace_manager,
    agent_runner=agent_runner,
)
```

### Acceptance Criteria

- [ ] Orchestrator compiles without errors
- [ ] All tests pass: `pytest runtime/tests/test_orchestrator.py -v`
- [ ] Migration status appears in state snapshot
- [ ] Both old and new tracker paths work

### Rollback Procedures

If issues arise during this phase:

1. Revert orchestrator.py changes:
   ```bash
   git checkout runtime/symphony/orchestrator.py
   ```

2. Revert main.py changes:
   ```bash
   git checkout runtime/main.py
   ```

3. Verify system still works with old tracker:
   ```bash
   make test
   ```

### Estimated Time

**1-2 hours**

---

## Phase 5: Testing & Verification (3-4 hours)

**Goal**: Comprehensive testing of the migration.

### Task 5.1: Run all unit tests

```bash
pytest runtime/tests/ -v --cov=runtime/tracker --cov=runtime/symphony
```

**Expected**: All tests pass, coverage >90%

### Task 5.2: Run integration tests with old tracker

```bash
export SYMPHONY_TRACKER_MIGRATION_ENABLED=false
pytest runtime/tests/test_integration.py -v
```

**Expected**: All tests pass with old tracker

### Task 5.3: Run integration tests with new tracker

```bash
export SYMPHONY_TRACKER_MIGRATION_ENABLED=true
pytest runtime/tests/test_integration.py -v
```

**Expected**: All tests pass with new tracker

### Task 5.4: End-to-end test

```bash
# Start with old tracker
export SYMPHONY_TRACKER_MIGRATION_ENABLED=false
./bin/symphony WORKFLOW.md

# Stop and start with new tracker
export SYMPHONY_TRACKER_MIGRATION_ENABLED=true
./bin/symphony WORKFLOW.md
```

**Expected**: Both trackers work correctly in end-to-end scenario

### Task 5.5: Performance test

Compare performance of old vs new tracker:

```bash
# Test old tracker performance
export SYMPHONY_TRACKER_MIGRATION_ENABLED=false
./bin/symphony WORKFLOW.md
# Measure: request latency, memory usage, CPU usage

# Test new tracker performance
export SYMPHONY_TRACKER_MIGRATION_ENABLED=true
./bin/symphony WORKFLOW.md
# Measure: request latency, memory usage, CPU usage
```

**Expected**: Performance is comparable (within 10%)

### Task 5.6: Rollback test

```bash
# Start with new tracker
export SYMPHONY_TRACKER_MIGRATION_ENABLED=true
export SYMPHONY_TRACKER_AUTO_ROLLBACK_ENABLED=true

# Simulate error (modify code to throw exception)
# Verify auto-rollback to old tracker works
```

**Expected**: Auto-rollback triggers correctly, system continues with old tracker

### Acceptance Criteria

- [ ] All unit tests pass (>90% coverage)
- [ ] Integration tests pass for both old and new tracker
- [ ] End-to-end test succeeds with both trackers
- [ ] Performance is comparable (within 10%)
- [ ] Auto-rollback works correctly

### Estimated Time

**3-4 hours**

---

## Migration Day Checklist

### Pre-Migration

Complete ALL items before deploying:

- [ ] Review all phases completed
  - Phase 1: Compatibility Layer ✅
  - Phase 2: TrackerFacade ✅
  - Phase 3: Feature Flags ✅
  - Phase 4: Orchestrator Integration ✅
  - Phase 5: Testing ✅

- [ ] All tests passing
  ```bash
  pytest runtime/tests/ -v
  ```

- [ ] Rollback procedures documented and tested
  - Automatic rollback tested ✅
  - Manual rollback documented ✅
  - Code rollback documented ✅

- [ ] Team notified of migration window
  - Email sent to team
  - Calendar invite created
  - On-call engineer assigned

- [ ] Monitoring dashboards ready
  - Prometheus metrics configured
  - Grafana dashboards updated
  - Alert thresholds set

- [ ] Backup current configuration
  ```bash
  cp WORKFLOW.md WORKFLOW.md.pre-migration
  cp config/symphony.yaml config/symphony.yaml.pre-migration
  ```

### During Migration

Follow these steps in order:

1. **Deploy code changes**
   ```bash
   git pull origin feature/tracker-migration
   # Or merge to main branch
   ```

2. **Start with migration disabled**
   ```bash
   export SYMPHONY_TRACKER_MIGRATION_ENABLED=false
   ./bin/symphony WORKFLOW.md &
   echo $! > orchestrator.pid
   ```

3. **Verify system works with old tracker**
   ```bash
   # Check logs
   tail -f /var/log/symphony/orchestrator.log

   # Check metrics
   curl http://localhost:8080/api/status
   ```

4. **Enable 5% rollout**
   ```bash
   # Stop orchestrator
   kill $(cat orchestrator.pid)

   # Enable migration
   export SYMPHONY_TRACKER_MIGRATION_ENABLED=true

   # Start orchestrator
   ./bin/symphony WORKFLOW.md &
   echo $! > orchestrator.pid
   ```

5. **Monitor logs for errors**
   ```bash
   grep "ERROR" /var/log/symphony/orchestrator.log
   grep "TrackerFacade" /var/log/symphony/orchestrator.log
   ```

6. **Check migration status in observability**
   ```bash
   curl http://localhost:8080/api/status | jq .migration
   ```

7. **Gradually increase rollout**
   - 10% → 25% → 50% → 100%
   - Wait at least 30 minutes between each step
   - Monitor metrics and logs at each step

### Post-Migration

Verify success after full rollout:

- [ ] All metrics green
  - Error rate < 0.1%
  - Latency within 10% of baseline
  - No 5xx errors

- [ ] No errors in logs
  ```bash
  grep "ERROR" /var/log/symphony/orchestrator.log | tail -100
  ```

- [ ] Auto-rollback not triggered
  - Check logs for "Auto-rolling back"
  - Should see "fetched from NEW tracker" messages

- [ ] Performance acceptable
  - Compare to baseline measurements
  - Should be within 10%

- [ ] Team notified of success
  - Send success email
  - Update status page
  - Close migration ticket

### Rollback Conditions

Rollback immediately if ANY of these conditions occur:

- [ ] Error rate > 5%
- [ ] Latency increase > 50%
- [ ] Auto-rollback triggered
- [ ] Team decision to rollback

---

## Rollback Procedures

### Automatic Rollback

**How it works:**
- Feature flag `SYMPHONY_TRACKER_AUTO_ROLLBACK_ENABLED` controls auto-rollback
- When new tracker throws error, facade automatically switches to old tracker
- No code changes required
- System continues operating with old tracker

**Enable auto-rollback:**
```bash
export SYMPHONY_TRACKER_AUTO_ROLLBACK_ENABLED=true
```

**Verify auto-rollback:**
```bash
# Check logs for rollback message
grep "Auto-rolling back" /var/log/symphony/orchestrator.log

# Check migration status
curl http://localhost:8080/api/status | jq .migration
# Should show "using_new_tracker": false
```

### Manual Rollback

**Step 1: Stop orchestrator**
```bash
kill $(cat orchestrator.pid)
```

**Step 2: Set environment variable**
```bash
export SYMPHONY_TRACKER_MIGRATION_ENABLED=false
```

**Step 3: Start orchestrator**
```bash
./bin/symphony WORKFLOW.md &
echo $! > orchestrator.pid
```

**Step 4: Verify rollback**
```bash
# Check logs
tail -f /var/log/symphony/orchestrator.log
# Should see "fetching from OLD tracker"

# Check status
curl http://localhost:8080/api/status | jq .migration
# Should show "using_new_tracker": false
```

### Code Rollback

**Option 1: Revert migration commit**
```bash
# Find migration commit
git log --oneline | grep tracker-migration

# Revert commit
git revert <migration-commit-hash>

# Deploy
git push origin main
```

**Option 2: Checkout previous commit**
```bash
# Checkout pre-migration commit
git checkout <pre-migration-commit-hash>

# Deploy
git push -f origin main  # Force push (DANGEROUS!)
```

**Option 3: Restore from backup**
```bash
# Restore configuration
cp WORKFLOW.md.pre-migration WORKFLOW.md
cp config/symphony.yaml.pre-migration config/symphony.yaml

# Restart
./bin/symphony WORKFLOW.md &
echo $! > orchestrator.pid
```

### Rollback Verification

After rollback, verify system is working:

- [ ] Old tracker works correctly
  ```bash
  # Check logs
  tail -f /var/log/symphony/orchestrator.log

  # Should see "fetching from OLD tracker"
  ```

- [ ] No errors in logs
  ```bash
  grep "ERROR" /var/log/symphony/orchestrator.log | tail -50
  ```

- [ ] Metrics back to baseline
  ```bash
  # Check error rate
  curl http://localhost:8080/api/metrics | grep error_rate

  # Check latency
  curl http://localhost:8080/api/metrics | grep latency
  ```

- [ ] Team notified of rollback
  - Send rollback email
  - Update status page
  - Create incident ticket

---

## Verification Commands

### Unit Tests

Run all unit tests for new components:

```bash
# Test compatibility layer
pytest runtime/tests/test_compat.py -v

# Test facade
pytest runtime/tests/test_facade.py -v

# Test feature flags
pytest runtime/tests/test_feature_flags.py -v

# Test orchestrator
pytest runtime/tests/test_orchestrator.py -v
```

### Integration Tests

Run integration tests with both trackers:

```bash
# Old tracker
export SYMPHONY_TRACKER_MIGRATION_ENABLED=false
pytest runtime/tests/test_integration.py -v

# New tracker
export SYMPHONY_TRACKER_MIGRATION_ENABLED=true
pytest runtime/tests/test_integration.py -v
```

### End-to-End

Run full end-to-end test:

```bash
# Start orchestrator
./bin/symphony WORKFLOW.md

# Monitor logs
tail -f /var/log/symphony/orchestrator.log

# Check status
curl http://localhost:8080/api/status
```

### Migration Status

Check current migration status:

```bash
# Via orchestrator API
curl http://localhost:8080/api/status | jq .migration

# Expected output:
# {
#   "using_new_tracker": true,
#   "migration_enabled": true,
#   "auto_rollback_enabled": true,
#   "rollback_mode": "auto",
#   "old_tracker_present": true,
#   "new_tracker_present": true
# }
```

### Logs

Check migration-related logs:

```bash
# Check migration logs
grep "TrackerFacade" /var/log/symphony/orchestrator.log

# Check for errors
grep "ERROR" /var/log/symphony/orchestrator.log | tail -50

# Check for rollback
grep "Auto-rolling back" /var/log/symphony/orchestrator.log

# Check which tracker is being used
grep "fetching from" /var/log/symphony/orchestrator.log | tail -20
```

### Performance Monitoring

Monitor performance metrics:

```bash
# Check latency
curl http://localhost:8080/api/metrics | grep tracker_latency

# Check error rate
curl http://localhost:8080/api/metrics | grep tracker_error_rate

# Check request count
curl http://localhost:8080/api/metrics | grep tracker_requests_total
```

### Health Checks

Verify system health:

```bash
# Overall health
curl http://localhost:8080/api/health

# Tracker health
curl http://localhost:8080/api/tracker/health

# Expected output:
# {
#   "status": "healthy",
#   "tracker": "linear",
#   "version": "2.0.0"
# }
```

---

## Summary

**Total Estimated Time**: 8-12 hours

**Risk Level**: MEDIUM-HIGH (managed with gradual rollout and quick rollback)

**Success Criteria**:
- [ ] All phases completed
- [ ] All tests passing
- [ ] Migration status shows new tracker active
- [ ] Metrics within acceptable range
- [ ] Zero downtime or <5 minutes if rollback needed

**Key Benefits**:
1. **Gradual rollout**: Can enable migration at different percentages
2. **Quick rollback**: Can switch back to old tracker in <5 minutes
3. **Zero downtime**: No system restart required for rollback
4. **Observability**: Full visibility into migration status and metrics
5. **Safe migration**: Auto-rollback protects against unexpected errors

**Next Steps**:
1. Review this plan with the team
2. Schedule migration window
3. Complete all phases in sequence
4. Execute migration day checklist
5. Monitor and verify success
6. Update documentation if needed

---

**Document History**:

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | April 12, 2026 | Symphony Team | Initial version |
