"""Data models for Yandex Tracker adapter.

This module contains data classes and types for representing Yandex Tracker
entities and API request/response structures.

Classes:
    UpdateIssueRequest: Dataclass for PATCH /issues/{key} operations.
    ArrayFieldOperations: Container for array field operations (add, remove, set).
"""

from dataclasses import dataclass
from typing import Any


class ArrayFieldOperations:
    """Container for array field operations.

    Represents the structure used by Yandex Tracker API for array field updates.
    Each operation (add, remove, set) is optional, and the entire operations
    dict can be None to represent a "null" operation (clear the array).

    Attributes:
        add: List of items to append to the array.
        remove: List of items to remove from the array.
        set_: List of items to replace the array with entirely.
    """

    def __init__(
        self,
        add: list[str] | None = None,
        remove: list[str] | None = None,
        set_: list[str] | None = None,
    ) -> None:
        """Initialize ArrayFieldOperations.

        Args:
            add: List of items to append to the array.
            remove: List of items to remove from the array.
            set_: List of items to replace the array with entirely.
        """
        self.add = add
        self.remove = remove
        self.set = set_

    def to_dict(self) -> dict[str, Any] | None:
        """Convert operations to dictionary for API request.

        Returns:
            Dictionary with operations, or None if no operations specified.
        """
        result: dict[str, Any] = {}
        if self.add is not None:
            result["add"] = self.add
        if self.remove is not None:
            result["remove"] = self.remove
        if self.set is not None:
            result["set"] = self.set

        return result if result else None


@dataclass
class UpdateIssueRequest:
    """Request dataclass for updating a Yandex Tracker issue.

    This class represents a PATCH request to the Yandex Tracker API v3 endpoint
    /v2/issues/{key}. It supports all documented API fields including:
    - Basic fields: summary, description, status, priority, type, assignee, deadline
    - Array operations: followers, attachments, tags
    - Custom fields: extKey1, extKey2, etc.
    - System fields: version for optimistic locking

    For array fields, use the ArrayFieldOperations class to specify operations
    like add, remove, set. To clear an array entirely, use None.

    Example:
        >>> # Update summary and add followers
        >>> request = UpdateIssueRequest(
        ...     summary="New summary",
        ...     followers=ArrayFieldOperations(add=["user1", "user2"]),
        ...     version=5
        ... )
        >>>
        >>> # Remove tags and add new ones
        >>> request = UpdateIssueRequest(
        ...     tags=ArrayFieldOperations(remove=["old"], add=["new"]),
        ...     version=5
        ... )
        >>>
        >>> # Clear followers (null operation)
        >>> request = UpdateIssueRequest(
        ...     followers=None,
        ...     version=5
        ... )

    Attributes:
        summary: Issue title/summary.
        description: Detailed issue description (markdown).
        status: Status name.
        priority: Priority name (e.g., 'low', 'normal', 'high', 'critical').
        type: Issue type name (e.g., 'task', 'bug', 'story').
        assignee: Assigned user login or ID.
        deadline: Deadline timestamp (ISO 8601).
        createdAt: Creation timestamp (ISO 8601) - read-only in PATCH.
        updatedAt: Last update timestamp (ISO 8601) - read-only in PATCH.
        followers: Array operations for followers (user logins/IDs).
        attachments: Array operations for attachments (attachment IDs).
        tags: Array operations for tags (tag names).
        extKey1: Custom field value (extKey format from Yandex Tracker).
        extKey2: Custom field value (extKey format from Yandex Tracker).
        extKey3: Custom field value (extKey format from Yandex Tracker).
        extKey4: Custom field value (extKey format from Yandex Tracker).
        extKey5: Custom field value (extKey format from Yandex Tracker).
        id: Issue UUID (read-only, ignored in PATCH).
        key: Issue key (read-only, ignored in PATCH).
        queue: Queue key (read-only, ignored in PATCH).
        version: Optimistic locking version (required for PATCH operations).
    """

    # Basic fields (optional)
    summary: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    type: str | None = None
    assignee: str | None = None
    deadline: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None

    # Array operations
    followers: ArrayFieldOperations | None = None
    attachments: ArrayFieldOperations | None = None
    tags: ArrayFieldOperations | None = None

    # Custom fields (extKey format)
    extKey1: Any = None
    extKey2: Any = None
    extKey3: Any = None
    extKey4: Any = None
    extKey5: Any = None

    # System fields (for context, read-only in PATCH)
    id: str | None = None
    key: str | None = None
    queue: str | None = None

    # Optimistic locking (required for PATCH)
    version: int | None = None

    def validate(self) -> list[str]:
        """Validate the request structure before sending to API.

        Checks for required fields and logical consistency.

        Returns:
            List of validation error messages. Empty if valid.
        """
        errors: list[str] = []

        # Version is required for PATCH operations
        if self.version is None:
            errors.append("version is required for update operations")

        # Validate array operations
        for field_name in ["followers", "attachments", "tags"]:
            operations = getattr(self, field_name)
            if operations is not None and not isinstance(operations, ArrayFieldOperations):
                errors.append(f"{field_name} must be ArrayFieldOperations or None, got {type(operations).__name__}")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Convert request to dictionary for API request.

        Converts all fields to the format expected by Yandex Tracker API v3.
        Arrays are converted to the {add:[], remove:[], set:[]} format.

        Returns:
            Dictionary suitable for PATCH request body.
        """
        result: dict[str, Any] = {}

        # Basic fields - only include if not None
        basic_fields = [
            "summary",
            "description",
            "status",
            "priority",
            "type",
            "assignee",
            "deadline",
            "createdAt",
            "updatedAt",
        ]
        for field_name in basic_fields:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value

        # System fields - only include if not None
        if self.id is not None:
            result["id"] = self.id
        if self.key is not None:
            result["key"] = self.key
        if self.queue is not None:
            result["queue"] = self.queue

        # Version is required
        if self.version is not None:
            result["version"] = self.version

        # Array operations - convert to API format
        array_fields = ["followers", "attachments", "tags"]
        for field_name in array_fields:
            operations = getattr(self, field_name)
            if operations is None:
                # None means "null" operation - clear the array
                result[field_name] = None
            elif isinstance(operations, ArrayFieldOperations):
                ops_dict = operations.to_dict()
                if ops_dict is not None:
                    result[field_name] = ops_dict

        # Custom fields (extKey) - only include if not None
        custom_fields = ["extKey1", "extKey2", "extKey3", "extKey4", "extKey5"]
        for field_name in custom_fields:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value

        return result


@dataclass
class Issue:
    """Yandex Tracker issue entity.

    Represents a work item in Yandex Tracker. This is the raw API response format
    before normalization to the standard Symphony format.

    Note: This is a placeholder for future Phase 3+ implementation.
    The adapter will return normalized issues via runtime/tracker/normalization.py.

    Attributes:
        id: Internal issue UUID.
        key: Unique issue identifier (e.g., "BACKEND-123").
        summary: Issue title.
        description: Detailed issue description (markdown).
        status: Status object with id and name.
        priority: Priority object with id and key.
        type: Issue type object.
        assignee: Assigned user object (optional).
        deadline: Deadline timestamp (ISO 8601).
        createdAt: Creation timestamp (ISO 8601).
        updatedAt: Last update timestamp (ISO 8601).
        version: Optimistic locking version.
    """

    id: str | None = None
    key: str | None = None
    summary: str | None = None
    description: str | None = None
    status: dict[str, Any] | None = None
    priority: dict[str, Any] | None = None
    type: dict[str, Any] | None = None
    assignee: dict[str, Any] | None = None
    deadline: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None
    version: int | None = None


@dataclass
class Transition:
    """Yandex Tracker status transition.

    Represents an available status transition for an issue in the workflow.

    Attributes:
        id: Transition unique identifier.
        name: Human-readable transition name.
        target_status: Target status name after transition execution.
    """

    id: str | None = None
    name: str | None = None
    target_status: str | None = None


@dataclass
class Comment:
    """Yandex Tracker issue comment.

    Represents a comment posted to an issue.

    Attributes:
        id: Comment unique identifier.
        text: Comment body (markdown).
        created_by: User object who posted the comment.
        created_at: Creation timestamp (ISO 8601).
        updated_at: Last update timestamp (ISO 8601).
    """

    id: str | None = None
    text: str | None = None
    created_by: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class Queue:
    """Yandex Tracker queue.

    Represents a queue (project) in Yandex Tracker.

    Attributes:
        key: Unique queue identifier (e.g., "BACKEND").
        name: Human-readable queue name.
    """

    key: str | None = None
    name: str | None = None
