"""Workflow loader - parses WORKFLOW.md."""

from typing import Tuple, Dict, Any
import yaml


def load_workflow(workflow_path: str) -> Tuple[Dict[str, Any], str]:
    """
    Load and parse workflow file.
    
    Returns (config, prompt_template).
    """
    # TODO: Implement - see SPEC.md Section 5.2
    with open(workflow_path, 'r') as f:
        content = f.read()
    
    # TODO: Parse YAML front matter + Markdown body
    return {}, ""
