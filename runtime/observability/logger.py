"""Structured logging.

Per SPEC.md Section 13.1:
- Required context fields for issue-related logs: issue_id, issue_identifier
- Required context for coding-agent session lifecycle logs: session_id
- Message formatting: stable key=value phrasing
- Include action outcome (completed, failed, retrying, etc.)
- Timestamps in ISO 8601 format
"""

import logging as stdlib_logging
import structlog
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def configure_structlog() -> None:
    """Configure structlog with required processors."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Configure structlog on module load
configure_structlog()


class Logger:
    """Structured logger with context-aware methods.

    This class provides both:
    1. Standard logging interface (debug, info, warning, error) for backward compatibility
    2. Structured methods per SPEC.md Section 13.1

    Per SPEC.md Section 13.1 logging conventions:
    - Issue-related logs include issue_id and issue_identifier
    - Session lifecycle logs include session_id
    - Messages use key=value phrasing
    - Include action outcomes: completed, failed, retrying, etc.
    """

    def __init__(self, name: str = None):
        """Initialize logger.

        Args:
            name: Logger name (defaults to root logger)
        """
        self._name = name
        self._struct_logger = structlog.get_logger()
        # Use standard logging for compatibility
        self._std_logger = stdlib_logging.getLogger(name or __name__)

    # Standard logging interface methods for backward compatibility
    def debug(self, message: str, **context: Any) -> None:
        """Log debug message."""
        self._log("debug", message, **context)

    def info(self, message: str, **context: Any) -> None:
        """Log info message."""
        self._log("info", message, **context)

    def warning(self, message: str, **context: Any) -> None:
        """Log warning message."""
        self._log("warning", message, **context)

    def error(self, message: str, **context: Any) -> None:
        """Log error message."""
        self._log("error", message, **context)

    def critical(self, message: str, **context: Any) -> None:
        """Log critical message."""
        self._log("critical", message, **context)

    def _log(
        self,
        level: str,
        message: str,
        **context: Any,
    ) -> None:
        """Log structured message with context.

        Args:
            level: Log level (debug, info, warning, error)
            message: Log message with key=value phrasing
            **context: Additional context fields
        """
        # Add timestamp in ISO 8601 format
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Log via structlog for structured output
        log_method = getattr(self._struct_logger, level, self._struct_logger.info)
        log_method(message, **context)

        # Also log via standard logger for compatibility
        std_method = getattr(self._std_logger, level, self._std_logger.info)
        std_method(message, **context)

    # Structured logging methods per SPEC.md Section 13.1
    def log_issue_event(
        self,
        level: str,
        action: str,
        issue_id: str,
        issue_identifier: str,
        outcome: Optional[str] = None,
        error: Optional[str] = None,
        **context: Any,
    ) -> None:
        """Log issue-related event.

        Per SPEC.md Section 13.1: issue_id and issue_identifier required.

        Args:
            level: Log level (debug, info, warning, error)
            action: Action being performed (dispatching, stopping, etc.)
            issue_id: The issue ID
            issue_identifier: Human-readable issue identifier
            outcome: Action outcome (completed, failed, retrying, etc.)
            error: Optional error message
            **context: Additional context fields
        """
        # Build message with key=value phrasing
        message_parts = [
            f"action={action}",
            f"issue_id={issue_id}",
            f"issue_identifier={issue_identifier}",
        ]

        if outcome:
            message_parts.append(f"outcome={outcome}")

        if error:
            message_parts.append(f"error={error}")

        message = " ".join(message_parts)

        self._log(
            level,
            message,
            issue_id=issue_id,
            issue_identifier=issue_identifier,
            action=action,
            outcome=outcome,
            error=error,
            **context,
        )

    def log_session_event(
        self,
        level: str,
        action: str,
        session_id: Optional[str] = None,
        issue_id: Optional[str] = None,
        issue_identifier: Optional[str] = None,
        outcome: Optional[str] = None,
        error: Optional[str] = None,
        **context: Any,
    ) -> None:
        """Log coding-agent session lifecycle event.

        Per SPEC.md Section 13.1: session_id required for session logs.

        Args:
            level: Log level
            action: Session action (starting, turn_completed, stopping, etc.)
            session_id: The session ID
            issue_id: Associated issue ID
            issue_identifier: Associated issue identifier
            outcome: Action outcome (completed, failed, retrying, etc.)
            error: Optional error message
            **context: Additional context
        """
        # Build message with key=value phrasing
        message_parts = [f"action={action}"]

        if session_id:
            message_parts.append(f"session_id={session_id}")

        if issue_id:
            message_parts.append(f"issue_id={issue_id}")

        if issue_identifier:
            message_parts.append(f"issue_identifier={issue_identifier}")

        if outcome:
            message_parts.append(f"outcome={outcome}")

        if error:
            message_parts.append(f"error={error}")

        message = " ".join(message_parts)

        self._log(
            level,
            message,
            session_id=session_id,
            issue_id=issue_id,
            issue_identifier=issue_identifier,
            action=action,
            outcome=outcome,
            error=error,
            **context,
        )

    def log_dispatch(
        self,
        level: str,
        issue_id: str,
        issue_identifier: str,
        worker_host: Optional[str] = None,
        **context: Any,
    ) -> None:
        """Log issue dispatch event."""
        message = f"action=dispatching issue_id={issue_id} issue_identifier={issue_identifier}"

        if worker_host:
            message += f" worker_host={worker_host}"

        self._log(
            level,
            message,
            issue_id=issue_id,
            issue_identifier=issue_identifier,
            action="dispatching",
            outcome="dispatched",
            worker_host=worker_host,
            **context,
        )

    def log_retry(
        self,
        level: str,
        issue_id: str,
        issue_identifier: str,
        attempt: int,
        error: Optional[str] = None,
        **context: Any,
    ) -> None:
        """Log retry scheduling event."""
        message = f"action=retrying issue_id={issue_id} issue_identifier={issue_identifier} attempt={attempt}"

        if error:
            message += f" error={error}"

        self._log(
            level,
            message,
            issue_id=issue_id,
            issue_identifier=issue_identifier,
            action="retrying",
            attempt=attempt,
            outcome="retrying",
            error=error,
            **context,
        )

    def log_startup(self, level: str = "info") -> None:
        """Log orchestrator startup."""
        self._log(level, "action=orchestrator_starting outcome=started")

    def log_shutdown(self, level: str = "info") -> None:
        """Log orchestrator shutdown."""
        self._log(level, "action=orchestrator_stopping outcome=stopped")

    def log_validation_failure(
        self,
        level: str,
        reason: str,
        **context: Any,
    ) -> None:
        """Log dispatch validation failure."""
        message = f"action=validating outcome=failed reason={reason}"
        self._log(
            level,
            message,
            action="validating",
            outcome="failed",
            reason=reason,
            **context,
        )

    def log_cleanup(
        self,
        level: str,
        issue_identifier: str,
        count: int,
        **context: Any,
    ) -> None:
        """Log workspace cleanup event."""
        message = f"action=cleanup issue_identifier={issue_identifier} count={count}"
        self._log(
            level,
            message,
            issue_identifier=issue_identifier,
            action="cleanup",
            count=count,
            **context,
        )

    def log_stall_detected(
        self,
        issue_id: str,
        issue_identifier: str,
        session_id: Optional[str],
        elapsed_ms: int,
        **context: Any,
    ) -> None:
        """Log stall detection event."""
        message = f"action=stall_detected issue_id={issue_id} issue_identifier={issue_identifier} elapsed_ms={elapsed_ms}"

        if session_id:
            message += f" session_id={session_id}"

        self._log(
            "warning",
            message,
            issue_id=issue_id,
            issue_identifier=issue_identifier,
            session_id=session_id,
            elapsed_ms=elapsed_ms,
            action="stall_detected",
            outcome="restarting",
            **context,
        )

    def log_state_change(
        self,
        level: str,
        issue_id: str,
        issue_identifier: str,
        old_state: str,
        new_state: str,
        reason: Optional[str] = None,
        **context: Any,
    ) -> None:
        """Log issue state change (became terminal, no longer active, etc.)."""
        message = f"action=state_change issue_id={issue_id} issue_identifier={issue_identifier} old_state={old_state} new_state={new_state}"

        if reason:
            message += f" reason={reason}"

        self._log(
            level,
            message,
            issue_id=issue_id,
            issue_identifier=issue_identifier,
            old_state=old_state,
            new_state=new_state,
            reason=reason,
            action="state_change",
            **context,
        )
