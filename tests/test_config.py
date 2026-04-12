"""Tests for config loader."""

import pytest
from pathlib import Path
from symphony.workflow import Workflow
from symphony.config import load_config, Config


def test_load_config_defaults():
    """Test config with minimal workflow."""
    workflow = Workflow(config={}, prompt_template="", file_path=Path("/test"))

    cfg = load_config(workflow)

    assert cfg.tracker_kind == "linear"
    assert cfg.tracker_endpoint == "https://api.linear.app/graphql"
    assert cfg.agent_max_concurrent_agents == 10
    assert cfg.codex_command == "codex app-server"
    assert cfg.polling_interval_ms == 30000


def test_load_config_from_workflow():
    """Test config from workflow values."""
    workflow = Workflow(
        config={
            "tracker": {
                "kind": "linear",
                "project_slug": "my-project",
                "api_key": "test-key",
            },
            "polling": {
                "interval_ms": 15000,
            },
            "agent": {
                "max_concurrent_agents": 5,
            },
            "workspace": {
                "root": "/tmp/test-workspaces",
            },
        },
        prompt_template="test",
        file_path=Path("/test"),
    )

    cfg = load_config(workflow)

    assert cfg.tracker_kind == "linear"
    assert cfg.tracker_project_slug == "my-project"
    assert cfg.tracker_api_key == "test-key"
    assert cfg.polling_interval_ms == 15000
    assert cfg.agent_max_concurrent_agents == 5
    assert cfg.workspace_root == Path("/tmp/test-workspaces")
