"""Workspace security - path validation."""

from pathlib import Path


def validate_workspace_path(workspace_path: Path, workspace_root: Path) -> bool:
    """
    Validate workspace path is inside workspace root.
    
    Returns True if valid.
    """
    # TODO: Implement 3 security invariants - SPEC.md Section 9.5
    pass


def sanitize_identifier(identifier: str) -> str:
    """Sanitize issue identifier for use in path."""
    # TODO: Implement - see SPEC.md Section 4.2
    pass
