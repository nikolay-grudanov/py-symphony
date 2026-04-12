"""Tests for workflow loader."""

import pytest
import tempfile
from pathlib import Path
from symphony.workflow import WorkflowLoader, load_workflow


def test_load_workflow_with_front_matter():
    """Test loading workflow with YAML front matter."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("""---
tracker:
  kind: linear
  project_slug: test-project
---

You are working on {{issue.identifier}}
""")
        f.flush()

        wf = load_workflow(f.name)

        assert wf.config["tracker"]["kind"] == "linear"
        assert wf.config["tracker"]["project_slug"] == "test-project"
        assert wf.prompt_template == "You are working on {{issue.identifier}}"

        Path(f.name).unlink()


def test_load_workflow_without_front_matter():
    """Test loading workflow with only prompt (no front matter)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("Just a prompt without config")
        f.flush()

        wf = load_workflow(f.name)

        assert wf.config == {}
        assert wf.prompt_template == "Just a prompt without config"

        Path(f.name).unlink()


def test_load_workflow_file_not_found():
    """Test error when file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_workflow("/nonexistent/path.md")
