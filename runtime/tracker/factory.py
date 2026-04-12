"""Tracker factory for creating adapter instances."""

import logging
import warnings
from typing import Any, Dict, Type

from .base import TrackerClient
from .registry import get_tracker_registry, AdapterInfo

logger = logging.getLogger(__name__)


# Error classes


class TrackerFactoryError(Exception):
    """Exception raised for tracker factory errors."""

    pass


class TrackerNotRegisteredError(TrackerFactoryError):
    """Exception raised when tracker kind is not registered."""

    pass


class TrackerConfigError(TrackerFactoryError):
    """Exception raised when tracker configuration is invalid."""

    pass


class TrackerDependencyError(TrackerFactoryError):
    """Exception raised when adapter dependencies are missing."""

    pass


class TrackerAPIError(TrackerFactoryError):
    """Base exception for tracker API errors."""

    pass


class TrackerApiRequestError(TrackerAPIError):
    """Exception raised for tracker API transport failures."""

    pass


class TrackerApiStatusError(TrackerAPIError):
    """Exception raised for non-200 HTTP responses."""

    pass


class TrackerApiConflictError(TrackerAPIError):
    """Exception raised for API conflicts (409)."""

    pass


class TrackerApiResourceNotFoundError(TrackerAPIError):
    """Exception raised when resource not found (404)."""

    pass


class TrackerApiTimeoutError(TrackerAPIError):
    """Exception raised for API timeouts."""

    pass


class TrackerApiRateLimitError(TrackerAPIError):
    """Exception raised for rate limit errors (429)."""

    pass


# Factory class


class TrackerFactory:
    """Factory for creating tracker adapter instances.

    Creates tracker adapters based on configuration, handling
    plugin discovery and generic instantiation.
    """

    @staticmethod
    def create(config: Any) -> TrackerClient:
        """Create a tracker adapter instance from configuration.

        Args:
            config: Configuration object with tracker settings

        Returns:
            TrackerClient instance

        Raises:
            TrackerNotRegisteredError: If tracker kind is not registered
            TrackerConfigError: If configuration is invalid
            TrackerDependencyError: If adapter dependencies are missing
        """
        kind = config.tracker_kind
        registry = get_tracker_registry()

        # Get adapter info from registry
        adapter_info = registry.get_adapter(kind)
        if adapter_info is None:
            available = list(registry.list_available().keys())
            raise TrackerNotRegisteredError(
                f"Tracker kind '{kind}' is not registered. "
                f"Available trackers: {', '.join(available)}\n"
                f"To install a tracker plugin, run: pip install symphony-{kind}\n"
                f"For custom trackers, see: https://docs.symphony.dev/plugins/trackers"
            )

        adapter_class = adapter_info.adapter_class

        # Check for deprecation warnings
        if adapter_info.metadata.get("deprecated"):
            warnings.warn(
                f"Using built-in '{kind}' adapter is deprecated. "
                f"Install plugin package: pip install symphony-{kind}",
                DeprecationWarning,
                stacklevel=2,
            )

        # Build config dictionary for adapter
        config_dict = TrackerFactory._build_config_dict(config, kind)

        # Instantiate adapter (adapter validates its own config)
        try:
            return adapter_class(**config_dict)
        except (TypeError, ValueError) as e:
            raise TrackerConfigError(
                f"Failed to instantiate '{kind}' adapter configuration: {e}"
            ) from e
        except Exception as e:
            # Don't wrap API-related exceptions
            if isinstance(
                e, (TrackerAPIError, TrackerApiRequestError, TrackerApiStatusError)
            ):
                raise
            raise TrackerConfigError(
                f"Failed to instantiate '{kind}' adapter: {e}"
            ) from e

    @staticmethod
    def _build_config_dict(config: Any, kind: str) -> Dict[str, Any]:
        """Build configuration dictionary for adapter instantiation.

        Maps global config keys to adapter-specific keys.
        Different tracker kinds may need different parameter names.

        Args:
            config: Configuration object
            kind: Tracker kind identifier

        Returns:
            Configuration dictionary for adapter constructor
        """
        # Base config that all adapters can use
        config_dict: Dict[str, Any] = {
            "api_key": getattr(config, "tracker_api_key", None),
            "endpoint": getattr(config, "tracker_endpoint", None),
            "username": getattr(config, "tracker_username", None),
            "timeout": getattr(config, "tracker_timeout", 30),
            "active_states": getattr(config, "tracker_active_states", None),
        }

        # Tracker-specific mappings
        if kind == "linear":
            config_dict["project_slug"] = getattr(config, "tracker_project_slug", None)
        elif kind == "jira":
            config_dict["project_key"] = getattr(config, "tracker_project_slug", None)
        else:
            # Generic: try common parameter names
            config_dict["project_slug"] = getattr(config, "tracker_project_slug", None)
            config_dict["project_key"] = getattr(config, "tracker_project_slug", None)

        # Remove None values
        config_dict = {k: v for k, v in config_dict.items() if v is not None}

        # Validate required parameters
        TrackerFactory._validate_config(kind, config_dict)

        return config_dict

    @staticmethod
    def _validate_config(kind: str, config_dict: Dict[str, Any]) -> None:
        """Validate required configuration parameters.

        Args:
            kind: Tracker kind identifier
            config_dict: Configuration dictionary

        Raises:
            TrackerConfigError: If required parameters are missing
        """
        if kind == "linear":
            missing = []
            if "api_key" not in config_dict:
                missing.append("api_key")
            if "project_slug" not in config_dict:
                missing.append("project_slug")
            if missing:
                raise TrackerConfigError(
                    f"Linear adapter requires missing configuration parameters: {', '.join(missing)}. "
                    f"Please provide tracker_api_key and tracker_project_slug in configuration."
                )
        elif kind == "jira":
            missing = []
            if "api_key" not in config_dict:
                missing.append("api_key")
            if "endpoint" not in config_dict:
                missing.append("endpoint")
            if missing:
                raise TrackerConfigError(
                    f"Jira adapter requires missing configuration parameters: {', '.join(missing)}. "
                    f"Please provide tracker_api_key and tracker_endpoint in configuration."
                )
