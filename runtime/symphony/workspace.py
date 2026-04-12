"""Workspace management - per-issue directories and lifecycle hooks."""

import os
import re
import logging
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from .config import Config


logger = logging.getLogger(__name__)


# Safety: sanitize workspace key per SPEC.md Section 4.2
_SANITIZE_RE = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_workspace_key(identifier: str) -> str:
    """Sanitize issue identifier for use as directory name."""
    return _SANITIZE_RE.sub("_", identifier)


@dataclass
class Workspace:
    """Workspace for a single issue."""

    path: Path
    issue_identifier: str
    created_now: bool  # True if directory was just created


class WorkspaceManager:
    """Manages per-issue workspaces and their lifecycle."""

    def __init__(self, config: Config):
        self.config = config
        self._workspaces: dict[str, Path] = {}  # identifier -> path

    def get_workspace(self, issue_identifier: str) -> Optional[Path]:
        """Get existing workspace path for an issue."""
        return self._workspaces.get(issue_identifier)

    def ensure_workspace(self, issue_identifier: str) -> Workspace:
        """
        Ensure workspace exists for the issue.

        Algorithm from SPEC.md Section 9.2:
        1. Sanitize identifier to workspace_key
        2. Compute workspace path under workspace root
        3. Ensure directory exists
        4. Mark created_now=true only if created during this call
        5. If created_now=true, run after_create hook
        """
        # Step 1: sanitize
        workspace_key = sanitize_workspace_key(issue_identifier)

        # Step 2: compute path
        workspace_path = self.config.workspace_root / workspace_key

        # Validate safety invariant from SPEC.md Section 9.5
        workspace_path_abs = workspace_path.resolve()
        root_abs = self.config.workspace_root.resolve()
        if not str(workspace_path_abs).startswith(str(root_abs)):
            raise ValueError(
                f"Workspace path {workspace_path} would be outside workspace root {self.config.workspace_root}"
            )

        # Step 3: ensure directory exists
        created_now = False
        if not workspace_path.exists():
            workspace_path.mkdir(parents=True, exist_ok=True)
            created_now = True
            logger.info(f"Created workspace: {workspace_path}")

        # Track workspace
        self._workspaces[issue_identifier] = workspace_path

        # Step 5: run after_create hook if new
        if created_now and self.config.hooks_after_create:
            self._run_hook("after_create", workspace_path)

        return Workspace(
            path=workspace_path,
            issue_identifier=issue_identifier,
            created_now=created_now,
        )

    def cleanup_workspace(self, issue_identifier: str) -> None:
        """
        Clean up workspace for a terminal or non-active issue.

        Per SPEC.md Section 9.4, runs before_remove hook then removes directory.
        """
        workspace_path = self._workspaces.get(issue_identifier)
        if not workspace_path or not workspace_path.exists():
            return

        # Run before_remove hook
        if self.config.hooks_before_remove:
            self._run_hook("before_remove", workspace_path)

        # Remove directory
        try:
            shutil.rmtree(workspace_path)
            logger.info(f"Removed workspace: {workspace_path}")
            del self._workspaces[issue_identifier]
        except Exception as e:
            logger.error(f"Failed to remove workspace {workspace_path}: {e}")

    def run_before_run_hook(self, workspace_path: Path) -> bool:
        """Run before_run hook. Returns False on failure."""
        if not self.config.hooks_before_run:
            return True

        return self._run_hook("before_run", workspace_path, fatal=True)

    def run_after_run_hook(self, workspace_path: Path) -> None:
        """Run after_run hook. Failures are logged and ignored."""
        if self.config.hooks_after_run:
            self._run_hook("after_run", workspace_path, fatal=False)

    def _run_hook(
        self, hook_name: str, workspace_path: Path, fatal: bool = True
    ) -> bool:
        """Run a workspace hook script."""
        hook_script = getattr(self.config, f"hooks_{hook_name}")
        if not hook_script:
            return True

        timeout_ms = self.config.hooks_timeout_ms
        timeout_sec = timeout_ms / 1000

        logger.info(f"Running {hook_name} hook in {workspace_path}")

        try:
            result = subprocess.run(
                ["sh", "-lc", hook_script],
                cwd=workspace_path,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )

            if result.returncode != 0:
                logger.error(f"{hook_name} hook failed: {result.stderr}")
                if fatal:
                    return False
            else:
                logger.debug(f"{hook_name} hook output: {result.stdout}")

            return True

        except subprocess.TimeoutExpired:
            logger.error(f"{hook_name} hook timed out after {timeout_sec}s")
            if fatal:
                return False
        except Exception as e:
            logger.error(f"{hook_name} hook error: {e}")
            if fatal:
                return False

        return True

    def cleanup_terminal_issues(self, terminal_identifiers: list[str]) -> None:
        """Clean up workspaces for issues that are now terminal."""
        for identifier in terminal_identifiers:
            self.cleanup_workspace(identifier)
