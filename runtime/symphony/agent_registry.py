"""Agent backend registry for pluggable backend architecture.

Provides registration and lookup for agent backend classes.
Supports plugin discovery via entry points, built-in fallback,
and manual registration.
"""

import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from .agent_backend import AgentBackend

logger = logging.getLogger(__name__)


# Error classes


class PluginDiscoveryError(Exception):
    """Raised when plugin discovery fails."""

    pass


class PluginValidationError(Exception):
    """Raised when a plugin fails validation."""

    pass


class AgentBackendNotRegisteredError(Exception):
    """Raised when requested agent backend is not found."""

    def __init__(self, kind: str):
        pip_hint = f"pip install symphony-{kind}"
        super().__init__(
            f"Agent backend '{kind}' is not registered. Install with: {pip_hint}"
        )


# Data classes


@dataclass
class BackendInfo:
    """Information about a registered agent backend.

    Attributes:
        kind: Backend kind identifier (e.g., 'codex', 'claude-code')
        backend_class: Backend class that inherits from AgentBackend
        source: Source of registration ('entry_point', 'builtin', 'manual')
        metadata: Optional metadata dictionary
        entry_point: Entry point object if from entry points, None otherwise
    """

    kind: str
    backend_class: Type[AgentBackend]
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    entry_point: Optional[Any] = None


# Registry class


class AgentBackendRegistry:
    """Thread-safe registry for agent backends.

    Provides registration and lookup for agent backend classes.
    Supports plugin discovery via entry points, built-in fallback,
    and manual registration.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._backends: Dict[str, BackendInfo] = {}
        self._discovered: bool = False
        self._builtin_registered: bool = False

    def discover_from_entry_points(self) -> None:
        """Discover and register agent backend plugins from entry points.

        Scans the 'symphony.agent_backends' entry points group and registers
        all discovered backends. Only discovers once (cached).

        Raises:
            PluginDiscoveryError: If discovery fails
        """
        with self._lock:
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
                        "importlib.metadata not available (Python < 3.8), "
                        "skipping plugin discovery"
                    )
                    self._discovered = True
                    return

                # Get entry points - handle different API versions
                try:
                    eps = entry_points(group="symphony.agent_backends")
                    # Python 3.10+ returns EntryPoints which is iterable
                    # Convert to list for consistent handling
                    eps = list(eps)
                except TypeError:
                    # Python < 3.10: entry_points() returns a dict
                    all_eps = entry_points()
                    eps = (
                        all_eps.get("symphony.agent_backends", [])
                        if hasattr(all_eps, "get")
                        else []
                    )

                for ep in eps:
                    try:
                        # Load the backend class
                        backend_class = ep.load()

                        # Validate it's an AgentBackend subclass
                        if not issubclass(backend_class, AgentBackend):
                            logger.warning(
                                f"Entry point '{ep.name}' does not export "
                                f"an AgentBackend subclass"
                            )
                            continue

                        # Extract metadata if available
                        metadata = self._extract_metadata(backend_class)

                        # Check for duplicate backend kind
                        kind_lower = ep.name.lower()
                        if kind_lower in self._backends:
                            logger.warning(
                                f"Duplicate backend kind '{kind_lower}' found in "
                                f"entry points. Overwriting existing backend."
                            )

                        # Register the backend
                        self._backends[kind_lower] = BackendInfo(
                            kind=kind_lower,
                            backend_class=backend_class,
                            source="entry_point",
                            metadata=metadata,
                            entry_point=ep,
                        )

                        logger.debug(f"Discovered agent backend: {ep.name}")

                    except Exception as e:
                        logger.warning(f"Failed to load agent backend '{ep.name}': {e}")
                        continue

                self._discovered = True

            except (ImportError, AttributeError, ValueError) as e:
                raise PluginDiscoveryError(
                    f"Failed to discover agent backend plugins: {e}"
                ) from e

    def _extract_metadata(self, backend_class: Type[AgentBackend]) -> Dict[str, Any]:
        """Extract metadata from backend class.

        Args:
            backend_class: Backend class to extract metadata from

        Returns:
            Metadata dictionary or empty dict
        """
        if hasattr(backend_class, "__plugin_info__"):
            return backend_class.__plugin_info__
        return {}

    def register_builtin_fallback(self) -> None:
        """Register built-in Codex backend as fallback.

        Called when no entry points are discovered. Registers
        Codex backend as the default built-in backend.
        """
        with self._lock:
            if self._builtin_registered:
                return

            try:
                from symphony_codex.backend import CodexBackend
            except ImportError:
                logger.debug(
                    "symphony-codex plugin not available, skipping builtin fallback"
                )
                # Mark as attempted even if failed - prevents infinite retry
                self._builtin_registered = True
                return

            self._backends["codex"] = BackendInfo(
                kind="codex",
                backend_class=CodexBackend,
                source="builtin",
                metadata={},
                entry_point=None,
            )

            self._builtin_registered = True
            logger.debug("Registered built-in Codex backend as fallback")

    def register_backend(
        self,
        kind: str,
        backend_class: Type[AgentBackend],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register an agent backend class.

        Manual registration takes precedence over entry points.
        Useful for testing or dynamic registration.

        Args:
            kind: Backend kind identifier (e.g., 'codex', 'claude-code')
            backend_class: AgentBackend subclass to register
            metadata: Optional metadata dictionary

        Raises:
            TypeError: If backend_class is not an AgentBackend subclass
            PluginValidationError: If kind is invalid
        """
        with self._lock:
            # Validate backend class
            if not issubclass(backend_class, AgentBackend):
                raise TypeError(
                    f"{backend_class.__name__} must inherit from AgentBackend"
                )

            # Validate kind
            if not kind or not isinstance(kind, str):
                raise PluginValidationError("Backend kind must be a non-empty string")

            # Register with manual source (highest priority)
            self._backends[kind.lower()] = BackendInfo(
                kind=kind.lower(),
                backend_class=backend_class,
                source="manual",
                metadata=metadata or {},
                entry_point=None,
            )

            logger.debug(f"Registered agent backend: {kind} (manual)")

    def get_backend(self, kind: str) -> Optional[BackendInfo]:
        """Get a registered backend info.

        Args:
            kind: Backend kind identifier

        Returns:
            BackendInfo or None if not registered
        """
        with self._lock:
            kind_lower = kind.lower()

            # Ensure discovery has run
            if not self._discovered:
                self.discover_from_entry_points()

            # If no backends discovered, register builtin fallback
            if not self._backends and not self._builtin_registered:
                self.register_builtin_fallback()

            return self._backends.get(kind_lower)

    def list_backends(self) -> Dict[str, BackendInfo]:
        """List all available agent backends.

        Returns:
            Dictionary mapping kind -> BackendInfo
        """
        with self._lock:
            # Ensure discovery has run
            if not self._discovered:
                self.discover_from_entry_points()

            # If no backends discovered, register builtin fallback
            if not self._backends and not self._builtin_registered:
                self.register_builtin_fallback()

            return dict(self._backends)

    def list_kinds(self) -> List[str]:
        """List all registered backend kinds.

        Returns:
            List of registered backend kind identifiers
        """
        with self._lock:
            # Ensure discovery has run
            if not self._discovered:
                self.discover_from_entry_points()

            # If no backends discovered, register builtin fallback
            if not self._backends and not self._builtin_registered:
                self.register_builtin_fallback()

            return list(self._backends.keys())

    def is_registered(self, kind: str) -> bool:
        """Check if a backend kind is registered.

        Args:
            kind: Backend kind identifier

        Returns:
            True if the backend kind is registered, False otherwise
        """
        return self.get_backend(kind) is not None


# Global registry instance
_registry = AgentBackendRegistry()


def register_backend(kind: str, backend_class: Type[AgentBackend]) -> None:
    """Register an agent backend class with the global registry.

    Args:
        kind: Backend kind identifier (e.g., 'codex', 'claude-code')
        backend_class: AgentBackend subclass to register
    """
    _registry.register_backend(kind, backend_class)


def get_backend(kind: str) -> Type[AgentBackend]:
    """Get an agent backend class by kind.

    Args:
        kind: Backend kind identifier

    Returns:
        AgentBackend subclass

    Raises:
        AgentBackendNotRegisteredError: If backend is not registered
    """
    backend_info = _registry.get_backend(kind)
    if backend_info is None:
        raise AgentBackendNotRegisteredError(kind)
    return backend_info.backend_class


def list_backends() -> List[str]:
    """List all registered agent backend kinds.

    Returns:
        List of registered backend kind identifiers
    """
    return _registry.list_kinds()


def discover_backends() -> None:
    """Trigger plugin discovery for agent backends."""
    _registry.discover_from_entry_points()


def get_backend_registry() -> AgentBackendRegistry:
    """Get the global backend registry instance.

    Returns:
        The global AgentBackendRegistry instance
    """
    return _registry
