"""Tracker registry for pluggable adapter architecture."""

from typing import Dict, List, Optional, Type

from .base import TrackerClient


class TrackerRegistry:
    """Singleton registry for tracker adapters.

    Provides registration and lookup for tracker adapter classes.
    Allows runtime registration of new tracker types without modifying core code.
    """

    def __init__(self) -> None:
        self._adapters: Dict[str, Type[TrackerClient]] = {}

    def register(self, kind: str, adapter_class: Type[TrackerClient]) -> None:
        """Register a tracker adapter class.

        Args:
            kind: Tracker kind identifier (e.g., 'linear', 'jira')
            adapter_class: TrackerClient subclass to register

        Raises:
            TypeError: If adapter_class is not a TrackerClient subclass
        """
        if not issubclass(adapter_class, TrackerClient):
            raise TypeError(f"{adapter_class.__name__} must inherit from TrackerClient")
        self._adapters[kind.lower()] = adapter_class

    def get_adapter(self, kind: str) -> Optional[Type[TrackerClient]]:
        """Get a registered tracker adapter class.

        Args:
            kind: Tracker kind identifier

        Returns:
            TrackerClient subclass or None if not registered
        """
        return self._adapters.get(kind.lower())

    def list_adapters(self) -> List[str]:
        """List all registered tracker kinds.

        Returns:
            List of registered tracker kind identifiers
        """
        return list(self._adapters.keys())

    def is_registered(self, kind: str) -> bool:
        """Check if a tracker kind is registered.

        Args:
            kind: Tracker kind identifier

        Returns:
            True if the tracker kind is registered, False otherwise
        """
        return kind.lower() in self._adapters


# Global registry instance
_registry = TrackerRegistry()


def register_tracker(kind: str, adapter_class: Type[TrackerClient]) -> None:
    """Register a tracker adapter class with the global registry.

    Args:
        kind: Tracker kind identifier (e.g., 'linear', 'jira')
        adapter_class: TrackerClient subclass to register
    """
    _registry.register(kind, adapter_class)


def get_tracker_registry() -> TrackerRegistry:
    """Get the global tracker registry instance.

    Returns:
        The global TrackerRegistry instance
    """
    return _registry
