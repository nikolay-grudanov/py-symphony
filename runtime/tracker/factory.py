"""Tracker factory for creating adapter instances."""

import os
from typing import Any, Dict, Optional, Type

from .base import TrackerClient
from .registry import get_tracker_registry


class TrackerFactoryError(Exception):
    """Exception raised for tracker factory errors."""

    pass


class TrackerNotRegisteredError(TrackerFactoryError):
    """Exception raised when tracker kind is not registered."""

    pass


class TrackerConfigError(TrackerFactoryError):
    """Exception raised when tracker configuration is invalid."""

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


class TrackerFactory:
    """Factory for creating tracker adapter instances.

    Creates tracker adapters based on configuration, handling
    validation and instantiation.
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
        """
        kind = config.tracker_kind
        registry = get_tracker_registry()

        # Get adapter class
        adapter_class = registry.get_adapter(kind)
        if adapter_class is None:
            available = registry.list_adapters()
            raise TrackerNotRegisteredError(
                f"Tracker kind '{kind}' is not registered. "
                f"Available trackers: {available}"
            )

        # Validate configuration
        TrackerFactory._validate_config(kind, config)

        # Instantiate adapter
        return TrackerFactory._instantiate_adapter(adapter_class, config)

    @staticmethod
    def _validate_config(kind: str, config: Any) -> None:
        """Validate tracker configuration.

        Args:
            kind: Tracker kind identifier
            config: Configuration object

        Raises:
            TrackerConfigError: If configuration is invalid
        """
        if kind == "linear":
            TrackerFactory._validate_linear_config(config)
        elif kind == "jira":
            TrackerFactory._validate_jira_config(config)
        # Add other trackers here

    @staticmethod
    def _validate_linear_config(config: Any) -> None:
        """Validate Linear tracker configuration.

        Args:
            config: Configuration object

        Raises:
            TrackerConfigError: If configuration is invalid
        """
        # Check API key (required)
        api_key = config.tracker_api_key
        if not api_key:
            raise TrackerConfigError(
                "Linear tracker requires 'tracker_api_key' in config or "
                "LINEAR_API_KEY environment variable"
            )

        # Check project slug (required)
        project_slug = config.tracker_project_slug
        if not project_slug:
            raise TrackerConfigError(
                "Linear tracker requires 'tracker_project_slug' in config"
            )

    @staticmethod
    def _validate_jira_config(config: Any) -> None:
        """Validate Jira tracker configuration.

        Args:
            config: Configuration object

        Raises:
            TrackerConfigError: If configuration is invalid
        """
        # Check API token
        api_key = config.tracker_api_key
        if not api_key:
            raise TrackerConfigError(
                "Jira tracker requires 'tracker_api_key' in config or "
                "JIRA_API_TOKEN environment variable"
            )

        # Check endpoint
        endpoint = config.tracker_endpoint
        if not endpoint:
            raise TrackerConfigError(
                "Jira tracker requires 'tracker_endpoint' in config"
            )

        # Check username for basic auth
        username = config.tracker_username
        if not username:
            raise TrackerConfigError(
                "Jira tracker requires 'tracker_username' in config for basic auth"
            )

    @staticmethod
    def _instantiate_adapter(
        adapter_class: Type[TrackerClient], config: Any
    ) -> TrackerClient:
        """Instantiate a tracker adapter with configuration.

        Args:
            adapter_class: TrackerClient subclass to instantiate
            config: Configuration object

        Returns:
            TrackerClient instance
        """
        kind = config.tracker_kind

        if kind == "linear":
            return adapter_class(
                api_key=config.tracker_api_key,
                project_slug=config.tracker_project_slug,
            )
        elif kind == "jira":
            return adapter_class(
                api_key=config.tracker_api_key,
                endpoint=config.tracker_endpoint,
                project_key=config.tracker_project_slug or "",
                username=config.tracker_username or "",
            )
        else:
            # Fallback for unknown trackers - pass all config as kwargs
            return adapter_class(
                api_key=config.tracker_api_key,
                endpoint=config.tracker_endpoint,
                project_slug=config.tracker_project_slug,
                username=config.tracker_username,
            )
