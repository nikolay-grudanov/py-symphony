"""Tests for feature flags."""

import os
import pytest

from runtime.tracker.feature_flags import (
    FeatureFlags,
    get_feature_flags,
    reset_feature_flags,
)


def test_feature_flags_defaults():
    """Test default feature flag values."""
    # Clear environment
    os.environ.pop("SYMPHONY_TRACKER_MIGRATION_ENABLED", None)
    os.environ.pop("SYMPHONY_TRACKER_AUTO_ROLLBACK_ENABLED", None)
    os.environ.pop("SYMPHONY_TRACKER_ROLLBACK_MODE", None)

    flags = FeatureFlags()

    assert flags.migration_enabled == False  # Default
    assert flags.auto_rollback_enabled == True  # Default
    assert flags.rollback_mode == "auto"


def test_feature_flags_from_env():
    """Test feature flags from environment variables."""
    os.environ["SYMPHONY_TRACKER_MIGRATION_ENABLED"] = "true"
    os.environ["SYMPHONY_TRACKER_AUTO_ROLLBACK_ENABLED"] = "false"
    os.environ["SYMPHONY_TRACKER_ROLLBACK_MODE"] = "manual"

    try:
        flags = FeatureFlags()

        assert flags.migration_enabled == True
        assert flags.auto_rollback_enabled == False
        assert flags.rollback_mode == "manual"
    finally:
        os.environ.pop("SYMPHONY_TRACKER_MIGRATION_ENABLED", None)
        os.environ.pop("SYMPHONY_TRACKER_AUTO_ROLLBACK_ENABLED", None)
        os.environ.pop("SYMPHONY_TRACKER_ROLLBACK_MODE", None)


def test_feature_flags_explicit_values():
    """Test explicit values override environment."""
    os.environ["SYMPHONY_TRACKER_MIGRATION_ENABLED"] = "true"

    try:
        flags = FeatureFlags(migration_enabled=False)

        assert flags.migration_enabled == False  # Explicit wins
    finally:
        os.environ.pop("SYMPHONY_TRACKER_MIGRATION_ENABLED", None)


def test_feature_flags_bool_parsing():
    """Test boolean parsing from environment."""
    test_cases = [
        ("true", True),
        ("false", False),
        ("1", True),
        ("0", False),
        ("yes", True),
        ("no", False),
        ("on", True),
        ("off", False),
    ]

    for env_value, expected in test_cases:
        os.environ["SYMPHONY_TRACKER_MIGRATION_ENABLED"] = env_value
        try:
            flags = FeatureFlags()
            assert flags.migration_enabled == expected
        finally:
            os.environ.pop("SYMPHONY_TRACKER_MIGRATION_ENABLED", None)


def test_feature_flags_invalid_bool():
    """Test invalid boolean values use default."""
    os.environ["SYMPHONY_TRACKER_MIGRATION_ENABLED"] = "invalid"

    try:
        flags = FeatureFlags()
        assert flags.migration_enabled == False  # Default used
    finally:
        os.environ.pop("SYMPHONY_TRACKER_MIGRATION_ENABLED", None)


def test_feature_flags_invalid_rollback_mode():
    """Test invalid rollback mode uses default."""
    os.environ["SYMPHONY_TRACKER_ROLLBACK_MODE"] = "invalid"

    try:
        flags = FeatureFlags()
        assert flags.rollback_mode == "auto"  # Default used
    finally:
        os.environ.pop("SYMPHONY_TRACKER_ROLLBACK_MODE", None)


def test_feature_flags_runtime_enable():
    """Test runtime enable migration."""
    flags = FeatureFlags(migration_enabled=False)
    assert flags.migration_enabled == False

    flags.enable_migration()
    assert flags.migration_enabled == True


def test_feature_flags_runtime_disable():
    """Test runtime disable migration."""
    flags = FeatureFlags(migration_enabled=True)
    assert flags.migration_enabled == True

    flags.disable_migration()
    assert flags.migration_enabled == False


def test_feature_flags_set_rollback_mode():
    """Test setting rollback mode."""
    flags = FeatureFlags()
    assert flags.rollback_mode == "auto"

    flags.set_rollback_mode("manual")
    assert flags.rollback_mode == "manual"

    flags.set_rollback_mode("auto")
    assert flags.rollback_mode == "auto"


def test_feature_flags_invalid_rollback_mode_raises():
    """Test invalid rollback mode raises error."""
    flags = FeatureFlags()

    with pytest.raises(ValueError, match="Invalid rollback mode"):
        flags.set_rollback_mode("invalid")


def test_feature_flags_to_dict():
    """Test converting feature flags to dict."""
    flags = FeatureFlags(
        migration_enabled=True, auto_rollback_enabled=False, rollback_mode="manual"
    )

    result = flags.to_dict()

    assert result == {
        "migration_enabled": True,
        "auto_rollback_enabled": False,
        "rollback_mode": "manual",
    }


def test_global_feature_flags():
    """Test global feature flags instance."""
    reset_feature_flags()

    flags1 = get_feature_flags()
    flags2 = get_feature_flags()

    assert flags1 is flags2  # Same instance


def test_reset_feature_flags():
    """Test resetting global feature flags."""
    flags1 = get_feature_flags()
    flags1.migration_enabled = True

    reset_feature_flags()

    flags2 = get_feature_flags()
    assert flags2.migration_enabled == False  # New instance
    assert flags1 is not flags2
