"""Feature flags for tracker migration."""

import os
import logging

logger = logging.getLogger(__name__)


class FeatureFlags:
    """Feature flags for controlling tracker migration rollout.

    Flags can be set via environment variables:
    - SYMPHONY_TRACKER_MIGRATION_ENABLED: Enable new tracker (default: false)
    - SYMPHONY_TRACKER_AUTO_ROLLBACK_ENABLED: Enable auto-rollback on error (default: true)
    - SYMPHONY_TRACKER_ROLLBACK_MODE: Rollback mode 'auto' or 'manual' (default: auto)

    Example:
        export SYMPHONY_TRACKER_MIGRATION_ENABLED=true
        export SYMPHONY_TRACKER_AUTO_ROLLBACK_ENABLED=true
    """

    def __init__(
        self,
        migration_enabled: bool | None = None,
        auto_rollback_enabled: bool | None = None,
        rollback_mode: str | None = None,
    ):
        """Initialize feature flags.

        Args:
            migration_enabled: Enable new tracker (defaults to env var)
            auto_rollback_enabled: Enable auto-rollback (defaults to env var)
            rollback_mode: Rollback mode (defaults to env var)
        """
        # Get env values
        env_migration = os.getenv("SYMPHONY_TRACKER_MIGRATION_ENABLED")
        env_auto_rollback = os.getenv("SYMPHONY_TRACKER_AUTO_ROLLBACK_ENABLED")
        env_rollback_mode = os.getenv("SYMPHONY_TRACKER_ROLLBACK_MODE")

        # Apply precedence: explicit value > env var > default
        self.migration_enabled = self._parse_bool(
            migration_enabled, env_migration, False
        )

        self.auto_rollback_enabled = self._parse_bool(
            auto_rollback_enabled, env_auto_rollback, True
        )

        # Apply precedence: explicit value > env var > default
        self.rollback_mode = rollback_mode or env_rollback_mode or "auto"

        # Validate rollback mode
        if self.rollback_mode not in ["auto", "manual"]:
            logger.warning(
                f"Invalid rollback_mode '{self.rollback_mode}', using 'auto'"
            )
            self.rollback_mode = "auto"

        logger.info(
            f"FeatureFlags initialized: migration_enabled={self.migration_enabled}, "
            f"auto_rollback_enabled={self.auto_rollback_enabled}, "
            f"rollback_mode={self.rollback_mode}"
        )

    def _parse_bool(
        self, value: bool | None, env_value: str | None, default: bool
    ) -> bool:
        """Parse boolean value from parameter or environment.

        Args:
            value: Explicit value (takes precedence)
            env_value: Environment variable value as string
            default: Default value if both are None/empty

        Returns:
            Boolean value
        """
        # Explicit value takes precedence
        if value is not None:
            return value

        # Parse from environment
        if env_value is not None:
            env_lower = env_value.lower()
            if env_lower in ["true", "1", "yes", "on"]:
                return True
            elif env_lower in ["false", "0", "no", "off", ""]:
                return False
            else:
                logger.warning(
                    f"Cannot parse bool from '{env_value}', using default {default}"
                )
                return default

        # Fall back to default
        return default

    def enable_migration(self) -> None:
        """Enable migration at runtime."""
        logger.info("FeatureFlags: enabling migration")
        self.migration_enabled = True

    def disable_migration(self) -> None:
        """Disable migration at runtime (rollback)."""
        logger.warning("FeatureFlags: disabling migration (rollback)")
        self.migration_enabled = False

    def set_rollback_mode(self, mode: str) -> None:
        """Set rollback mode.

        Args:
            mode: Either 'auto' or 'manual'
        """
        if mode not in ["auto", "manual"]:
            raise ValueError(f"Invalid rollback mode: {mode}")

        logger.info(f"FeatureFlags: setting rollback_mode={mode}")
        self.rollback_mode = mode

    def to_dict(self) -> dict:
        """Convert feature flags to dict for observability.

        Returns:
            Dict with all flag values
        """
        return {
            "migration_enabled": self.migration_enabled,
            "auto_rollback_enabled": self.auto_rollback_enabled,
            "rollback_mode": self.rollback_mode,
        }


# Global instance for easy access
_flags = None


def get_feature_flags() -> FeatureFlags:
    """Get global feature flags instance.

    Creates instance if not already initialized.

    Returns:
        FeatureFlags instance
    """
    global _flags
    if _flags is None:
        _flags = FeatureFlags()
    return _flags


def reset_feature_flags() -> None:
    """Reset global feature flags (mainly for testing)."""
    global _flags
    _flags = None
