"""Workflow loader - reads and parses WORKFLOW.md files."""

import os
import re
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


@dataclass
class Workflow:
    """Parsed workflow definition."""

    config: dict
    prompt_template: str
    file_path: Path


class WorkflowLoader:
    """Loads and parses WORKFLOW.md files."""

    FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

    def load(self, path: str | Path) -> Workflow:
        """Load and parse a WORKFLOW.md file."""
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {path}")

        content = path.read_text(encoding="utf-8")

        # Parse front matter
        match = self.FRONT_MATTER_RE.match(content)
        if match:
            config = yaml.safe_load(match.group(1)) or {}
            prompt = content[match.end() :].strip()
        else:
            # No front matter - entire file is prompt
            config = {}
            prompt = content.strip()

        return Workflow(config=config, prompt_template=prompt, file_path=path)

    def watch(self, path: str | Path, callback) -> Observer:
        """Watch workflow file for changes and call callback on change."""
        path = Path(path)
        handler = _WorkflowChangeHandler(callback)
        observer = Observer()
        observer.schedule(handler, str(path.parent), recursive=False)
        observer.start()
        return observer


class _WorkflowChangeHandler(FileSystemEventHandler):
    """Handler for workflow file changes."""

    def __init__(self, callback):
        self.callback = callback

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            logger.info(f"Workflow file changed: {event.src_path}")
            self.callback()


# Convenience function
def load_workflow(path: str | Path) -> Workflow:
    """Load a WORKFLOW.md file."""
    return WorkflowLoader().load(path)
