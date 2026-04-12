"""Tracker registry for pluggable adapter architecture."""

import logging
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from .base import TrackerClient

logger = logging.getLogger(__name__)


# Error classes


class PluginDiscoveryError(Exception):
    """Raised when plugin discovery fails."""

    pass


class PluginValidationError(Exception):
    """Raised when a plugin fails validation."""

    pass


class TrackerNotFoundError(Exception):
    """Raised when requested tracker is not found."""

    pass


# Data classes


@dataclass
class AdapterInfo:
    """Information about a registered tracker adapter.

    Attributes:
        kind: Tracker kind identifier (e.g., 'linear', 'jira')
        adapter_class: Adapter class that inherits from TrackerClient
        source: Source of registration ('entry_point', 'builtin', 'manual')
        metadata: Optional metadata dictionary
        entry_point: Entry point object if from entry points, None otherwise
    """

    kind: str
    adapter_class: Type[TrackerClient]
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    entry_point: Optional[Any] = None


# Registry class


class TrackerRegistry:
    """Singleton registry for tracker adapters.

    Provides registration and lookup for tracker adapter classes.
    Supports plugin discovery via entry points, built-in fallback,
    and manual registration.
    """

    def __init__(self) -> None:
        self._adapters: Dict[str, AdapterInfo] = {}
        self._discovered: bool = False
        self._builtin_registered: bool = False

    def discover_from_entry_points(self) -> None:
        """Discover and register tracker plugins from entry points.

        Scans the 'symphony.trackers' entry points group and registers
        all discovered adapters. Only discovers once (cached).

        Raises:
            PluginDiscoveryError: If discovery fails
        """
        if self._discovered:
            return

        try:
            # Use importlib.metadata for entry points discovery
            # Python 3.9+ has it built-in
            try:
                from importlib.metadata import entry_points
            except ImportError:
                # No fallback for very old Python - just skip discovery
                logger.warning(
                    "importlib.metadata not available (Python < 3.8), skipping plugin discovery"
                )
                self._discovered = True
                return

            # Get entry points - handle different API versions
            try:
                eps = entry_points(group="symphony.trackers")
                # Python 3.10+ returns EntryPoints which is iterable
                # Convert to list for consistent handling
                eps = list(eps)
            except TypeError:
                # Python < 3.10: entry_points() returns a dict
                all_eps = entry_points()
                eps = (
                    all_eps.get("symphony.trackers", [])
                    if hasattr(all_eps, "get")
                    else []
                )

            for ep in eps:
                try:
                    # Load the adapter class
                    adapter_class = ep.load()

                    # Validate it's a TrackerClient subclass
                    if not issubclass(adapter_class, TrackerClient):
                        logger.warning(
                            f"Entry point '{ep.name}' does not export a TrackerClient subclass"
                        )
                        continue

                    # Extract metadata if available
                    metadata = self._extract_metadata(adapter_class)

                    # Check for duplicate tracker kind
                    kind_lower = ep.name.lower()
                    if kind_lower in self._adapters:
                        logger.warning(
                            f"Duplicate tracker kind '{kind_lower}' found in entry points. "
                            f"Overwriting existing adapter."
                        )

                    # Register the adapter
                    self._adapters[kind_lower] = AdapterInfo(
                        kind=kind_lower,
                        adapter_class=adapter_class,
                        source="entry_point",
                        metadata=metadata,
                        entry_point=ep,
                    )

                    logger.debug(f"Discovered tracker adapter: {ep.name}")

                except Exception as e:
                    logger.warning(f"Failed to load tracker adapter '{ep.name}': {e}")
                    continue

            self._discovered = True

        except (ImportError, AttributeError, ValueError) as e:
            raise PluginDiscoveryError(
                f"Failed to discover tracker plugins: {e}"
            ) from e

    def _extract_metadata(self, adapter_class: Type[TrackerClient]) -> Dict[str, Any]:
        """Extract metadata from adapter class.

        Args:
            adapter_class: Adapter class to extract metadata from

        Returns:
            Metadata dictionary or empty dict
        """
        if hasattr(adapter_class, "__plugin_info__"):
            return adapter_class.__plugin_info__
        return {}

    def register_builtin_fallback(self) -> None:
        """Register built-in adapters as fallback.

        Called when no entry points are discovered. Registers
        Linear and Jira adapters with deprecation warnings.

        Note:
            Built-in adapters are deprecated and will be removed
            in a future version.
        """
        if self._builtin_registered:
            return

        # Import built-in adapters
        from .linear import LinearTracker
        from .jira import JiraTracker

        # Register with deprecation warnings
        warnings.warn(
            "Using built-in Linear/Jira adapters is deprecated. "
            "Install plugin packages: pip install symphony-linear symphony-jira",
            DeprecationWarning,
            stacklevel=2,
        )

        self._adapters["linear"] = AdapterInfo(
            kind="linear",
            adapter_class=LinearTracker,
            source="builtin",
            metadata={"deprecated": True},
            entry_point=None,
        )

        self._adapters["jira"] = AdapterInfo(
            kind="jira",
            adapter_class=JiraTracker,
            source="builtin",
            metadata={"deprecated": True},
            entry_point=None,
        )

        self._builtin_registered = True
        logger.debug("Registered built-in adapters as fallback")

    def register_tracker(
        self,
        kind: str,
        adapter_class: Type[TrackerClient],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a tracker adapter class.

        Manual registration takes precedence over entry points.
        Useful for testing or dynamic registration.

        Args:
            kind: Tracker kind identifier (e.g., 'linear', 'jira')
            adapter_class: TrackerClient subclass to register
            metadata: Optional metadata dictionary

        Raises:
            TypeError: If adapter_class is not a TrackerClient subclass
            PluginValidationError: If kind is invalid
        """
        # Validate adapter class
        if not issubclass(adapter_class, TrackerClient):
            raise TypeError(f"{adapter_class.__name__} must inherit from TrackerClient")

        # Validate kind
        if not kind or not isinstance(kind, str):
            raise PluginValidationError("Tracker kind must be a non-empty string")

        # Register with manual source (highest priority)
        self._adapters[kind.lower()] = AdapterInfo(
            kind=kind.lower(),
            adapter_class=adapter_class,
            source="manual",
            metadata=metadata or {},
            entry_point=None,
        )

        logger.debug(f"Registered tracker adapter: {kind} (manual)")

    def get_adapter(self, kind: str) -> Optional[AdapterInfo]:
        """Get a registered tracker adapter info.

        Args:
            kind: Tracker kind identifier

        Returns:
            AdapterInfo or None if not registered
        """
        kind_lower = kind.lower()

        # Ensure discovery has run
        if not self._discovered:
            self.discover_from_entry_points()

        # If no adapters discovered, register builtin fallback
        if not self._adapters and not self._builtin_registered:
            self.register_builtin_fallback()

        return self._adapters.get(kind_lower)

    def list_available(self) -> Dict[str, AdapterInfo]:
        """List all available tracker adapters.

        Returns:
            Dictionary mapping kind -> AdapterInfo
        """
        # Ensure discovery has run
        if not self._discovered:
            self.discover_from_entry_points()

        # If no adapters discovered, register builtin fallback
        if not self._adapters and not self._builtin_registered:
            self.register_builtin_fallback()

        return dict(self._adapters)

    def list_kinds(self) -> List[str]:
        """List all registered tracker kinds.

        Returns:
            List of registered tracker kind identifiers
        """
        # Ensure discovery has run
        if not self._discovered:
            self.discover_from_entry_points()

        # If no adapters discovered, register builtin fallback
        if not self._adapters and not self._builtin_registered:
            self.register_builtin_fallback()

        return list(self._adapters.keys())

    def is_registered(self, kind: str) -> bool:
        """Check if a tracker kind is registered.

        Args:
            kind: Tracker kind identifier

        Returns:
            True if the tracker kind is registered, False otherwise
        """
        return self.get_adapter(kind) is not None


# Global registry instance
_registry = TrackerRegistry()


def register_tracker(kind: str, adapter_class: Type[TrackerClient]) -> None:
    """Register a tracker adapter class with the global registry.

    Args:
        kind: Tracker kind identifier (e.g., 'linear', 'jira')
        adapter_class: TrackerClient subclass to register
    """
    _registry.register_tracker(kind, adapter_class)


def get_tracker_registry() -> TrackerRegistry:
    """Get the global tracker registry instance.

    Returns:
        The global TrackerRegistry instance
    """
    return _registry
