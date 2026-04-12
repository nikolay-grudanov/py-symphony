"""Tracker facade for migration routing."""

import logging
from typing import List, Dict, Optional

from runtime.symphony.tracker import Issue, Tracker  # Old tracker
from runtime.tracker.compat import AsyncTrackerWrapper  # Compatibility wrapper
from runtime.tracker.factory import TrackerFactory  # New factory
from runtime.tracker.feature_flags import FeatureFlags  # Feature flags

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
            logger.info(
                f"TrackerFacade: fetched {len(result)} candidates from NEW tracker"
            )
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
