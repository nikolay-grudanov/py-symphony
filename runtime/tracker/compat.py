"""Compatibility layer for migrating from old to new tracker architecture."""

import asyncio
import logging
from typing import Any, Dict, List

from runtime.symphony.tracker import Issue  # Old Issue dataclass
from runtime.tracker.base import TrackerClient  # New base interface

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

    async def fetch_candidate_issues(self) -> List[Issue]:
        """Fetch candidate issues async wrapper.

        Returns:
            List of Issue objects (old dataclass format)
        """
        logger.debug("AsyncTrackerWrapper: fetch_candidate_issues")

        # Call sync method in thread pool
        result = await asyncio.to_thread(self._client.fetch_candidate_issues)

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

        result = await asyncio.to_thread(self._client.fetch_issues_by_states, states)

        return [self._dict_to_issue(issue_dict) for issue_dict in result]

    async def fetch_issue_states(self, issue_ids: List[str]) -> Dict[str, str]:
        """Fetch issue states async wrapper.

        Note: Method name differs from new API (fetch_issue_states vs fetch_issue_states_by_ids)

        Args:
            issue_ids: List of issue IDs

        Returns:
            Dict mapping issue_id -> state_name
        """
        logger.debug(
            f"AsyncTrackerWrapper: fetch_issue_states(issue_ids={len(issue_ids)})"
        )

        result = await asyncio.to_thread(
            self._client.fetch_issue_states_by_ids, issue_ids
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
