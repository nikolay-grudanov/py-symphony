"""Normalization utilities for tracker data."""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional


class NormalizationUtils:
    """Utilities for normalizing tracker data to a common format.

    Provides static methods to normalize issue data from different
    trackers into a consistent format for Symphony.
    """

    @staticmethod
    def normalize_issue(raw_issue: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize an issue from any tracker to common format.

        Args:
            raw_issue: Raw issue data from tracker

        Returns:
            Normalized issue dictionary with standardized keys

        Raises:
            ValueError: If issue has neither 'id' nor 'identifier'
        """
        issue_id = raw_issue.get("id") or raw_issue.get("identifier")
        if not issue_id:
            raise ValueError("Issue must have either 'id' or 'identifier' field")

        return {
            "id": issue_id,
            "identifier": raw_issue.get("identifier") or issue_id,
            "title": raw_issue.get("title") or raw_issue.get("summary", ""),
            "state": NormalizationUtils.normalize_state(
                raw_issue.get("state") or raw_issue.get("status", "")
            ),
            "priority": NormalizationUtils._normalize_priority(
                raw_issue.get("priority")
            ),
            "created_at": NormalizationUtils._parse_timestamp(
                raw_issue.get("created_at") or raw_issue.get("createdAt")
            ),
            "labels": NormalizationUtils._normalize_labels(
                raw_issue.get("labels") or raw_issue.get("tags", [])
            ),
            "blocked_by": raw_issue.get("blocked_by") or raw_issue.get("blockedBy", []),
        }

    @staticmethod
    def _normalize_labels(labels: List[str]) -> List[str]:
        """Normalize labels to lowercase.

        Args:
            labels: List of label strings

        Returns:
            List of lowercase labels
        """
        if not labels:
            return []
        return [label.lower().strip() for label in labels if label]

    @staticmethod
    def _normalize_priority(priority: Any) -> Optional[int]:
        """Normalize priority to integer.

        Linear uses: 0=None, 1=Urgent, 2=High, 3=Medium, 4=Low
        Jira uses: Highest, High, Medium, Low, Lowest

        Args:
            priority: Priority value from tracker

        Returns:
            Integer priority (0-4) or None
        """
        if priority is None:
            return None

        # Already an integer
        if isinstance(priority, int):
            return priority if 0 <= priority <= 4 else None

        # String priority
        if isinstance(priority, str):
            priority_lower = priority.lower().strip()

            # Linear-style priorities
            linear_map = {
                "urgent": 1,
                "high": 2,
                "medium": 3,
                "low": 4,
            }
            if priority_lower in linear_map:
                return linear_map[priority_lower]

            # Jira-style priorities
            jira_map = {
                "highest": 1,
                "high": 2,
                "medium": 3,
                "low": 4,
                "lowest": 4,
            }
            if priority_lower in jira_map:
                return jira_map[priority_lower]

            # Try to parse as integer
            try:
                val = int(priority_lower)
                return val if 0 <= val <= 4 else None
            except ValueError:
                return None

        return None

    @staticmethod
    def _parse_timestamp(timestamp: Any) -> Optional[datetime]:
        """Parse timestamp to datetime (ISO-8601).

        Args:
            timestamp: Timestamp value from tracker

        Returns:
            Parsed datetime or None
        """
        if not timestamp:
            return None

        if isinstance(timestamp, datetime):
            return timestamp

        if isinstance(timestamp, str):
            # Try ISO-8601 formats
            timestamp = timestamp.strip()

            # Handle 'Z' suffix
            if timestamp.endswith("Z"):
                timestamp = timestamp[:-1] + "+00:00"

            # Handle '+00:00' suffix
            if timestamp.endswith("+00:00"):
                # Remove timezone for fromisoformat, then add it back
                timestamp = timestamp[:-6]

            try:
                return datetime.fromisoformat(timestamp)
            except ValueError:
                # Try other common formats
                formats = [
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d",
                ]
                for fmt in formats:
                    try:
                        return datetime.strptime(timestamp, fmt)
                    except ValueError:
                        continue

        return None

    @staticmethod
    def normalize_state(state: str) -> str:
        """Normalize state name to lowercase format.

        Args:
            state: State name from tracker (e.g., "In Progress", "DONE")

        Returns:
            Lowercase state name with whitespace trimmed (e.g., "in progress", "done")

        Note:
            This method is separated from normalize_issue() to allow:
            - Batch normalization of multiple states without full issue objects
            - Performance optimization when only state normalization is needed
            - Reusability in other normalization contexts

        Example:
            >>> NormalizationUtils.normalize_state("In Progress")
            'in progress'
            >>> NormalizationUtils.normalize_state("  DONE  ")
            'done'
        """
        return state.lower().strip() if state else ""
