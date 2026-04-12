"""Base tracker interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class TrackerClient(ABC):
    """Base tracker client interface.

    Defines the contract for all issue tracker adapters.
    Each adapter must implement these methods to integrate with Symphony.
    """

    @property
    @abstractmethod
    def tracker_kind(self) -> str:
        """Return the tracker kind identifier (e.g., 'linear', 'jira')."""
        raise NotImplementedError

    @abstractmethod
    def fetch_candidate_issues(self) -> List[Dict[str, Any]]:
        """Fetch issues in active states that are candidates for dispatch.

        Returns:
            List of issue dictionaries with keys: id, identifier, title,
            state, priority, created_at, labels, blocked_by
        """
        pass

    @abstractmethod
    def fetch_issues_by_states(self, state_names: List[str]) -> List[Dict[str, Any]]:
        """Fetch issues matching the specified states.

        Args:
            state_names: List of state names to filter by (e.g., ['Todo', 'In Progress'])

        Returns:
            List of issue dictionaries in the specified states.
        """
        pass

    @abstractmethod
    def fetch_issue_states_by_ids(self, issue_ids: List[str]) -> Dict[str, str]:
        """Fetch current states for specific issues.

        Args:
            issue_ids: List of issue identifiers to fetch states for

        Returns:
            Dictionary mapping issue_id -> state_name
        """
        pass
