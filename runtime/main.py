"""Symphony Service - CLI entry point."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from runtime.symphony.workflow import load_workflow
from runtime.symphony.config import load_config
from runtime.symphony.tracker import create_tracker
from runtime.symphony.workspace import WorkspaceManager
from runtime.symphony.agent import AgentRunner
from runtime.symphony.orchestrator import Orchestrator

from runtime.tracker.facade import create_facade
from runtime.tracker.feature_flags import get_feature_flags


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Symphony - Orchestrate coding agents to get project work done.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "workflow",
        nargs="?",
        default="./WORKFLOW.md",
        help="Path to WORKFLOW.md file (default: ./WORKFLOW.md)",
    )

    parser.add_argument(
        "--logs-root",
        help="Directory for log files (default: ./log)",
        default=None,
    )

    parser.add_argument(
        "--port",
        type=int,
        help="Port for optional HTTP server (default: disabled)",
        default=None,
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (debug) logging",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    return parser.parse_args()


async def run_symphony(
    workflow_path: str, logs_root: str | None, port: int | None
) -> int:
    """Run the Symphony orchestrator."""
    # Load workflow
    workflow = load_workflow(workflow_path)
    logging.info(f"Loaded workflow from {workflow_path}")

    # Load config
    config = load_config(workflow)
    logging.info(
        f"Config loaded: tracker={config.tracker_kind}, project={config.tracker_project_slug}"
    )

    # Create components
    # Create old tracker (for fallback)
    old_tracker = None
    try:
        old_tracker = create_tracker(config.tracker_kind, config)
    except Exception as e:
        logging.warning(f"Failed to create old tracker: {e}")

    # Get feature flags
    feature_flags = get_feature_flags()

    # Create facade with both trackers
    tracker_facade = create_facade(
        old_tracker=old_tracker,
        config=config,
        feature_flags=feature_flags,
    )

    workspace_manager = WorkspaceManager(config)
    agent_runner = AgentRunner(config)

    # Create and start orchestrator
    orchestrator = Orchestrator(
        config=config,
        tracker_facade=tracker_facade,
        workspace_manager=workspace_manager,
        agent_runner=agent_runner,
    )

    try:
        await orchestrator.start()
        logging.info("Orchestrator running, press Ctrl+C to stop")

        # Wait for interrupt
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        await orchestrator.stop()

    return 0


def main() -> int:
    """Main entry point."""
    args = parse_args()
    setup_logging(args.verbose)

    # Validate workflow path
    workflow_path = Path(args.workflow)
    if not workflow_path.exists():
        logging.error(f"Workflow file not found: {workflow_path}")
        return 1

    # Run async main
    try:
        return asyncio.run(run_symphony(args.workflow, args.logs_root, args.port))
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
