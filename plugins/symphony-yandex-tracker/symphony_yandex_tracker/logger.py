"""Structured JSON logging for Yandex Tracker adapter.

This module provides JSON logging functionality with required context fields
as per FR-016, and sensitive information protection as per FR-017.

Classes:
    JsonFormatter: Custom logging formatter for structured JSON output.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging.

    This formatter outputs log records as JSON objects with required context fields:
    - issue_id: ID of the issue being operated on (if applicable)
    - action: Name of the operation (e.g., "authenticate", "fetch_issues")
    - outcome: Result of the operation ("success" or "error")
    - duration_ms: Duration of the operation in milliseconds (always ms)
    - error_message: Error message (only on errors)
    - stack_trace: Exception stack trace (only on errors)
    - timestamp: UTC timestamp in ISO 8601 format

    Note: duration_ms is always expected in milliseconds. The OperationTimer
    class handles conversion from seconds to milliseconds internally.

    Also includes standard logging fields: level, logger, message.

    Sensitive information protection (FR-017):
    - OAuth tokens (starting with "y0__") are masked
    - IAM tokens (starting with "t1.") are masked
    - Organization IDs are masked in headers

    Example:
        >>> import logging
        >>> logger = logging.getLogger("test")
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(JsonFormatter())
        >>> logger.addHandler(handler)
        >>> logger.info("Operation completed", extra={"action": "test", "outcome": "success"})
    """

    # Fields that are always included in the output
    REQUIRED_FIELDS = frozenset(
        [
            "timestamp",
            "level",
            "logger",
            "message",
            "issue_id",
            "action",
            "outcome",
            "duration_ms",
        ]
    )

    # Fields included only on errors
    ERROR_FIELDS = frozenset(["error_message", "stack_trace"])

    def __init__(self) -> None:
        """Initialize JsonFormatter."""
        super().__init__()
        # Use a dummy format - we handle formatting ourselves
        self._fmt = "%(message)s"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string.

        Args:
            record: Log record to format.

        Returns:
            JSON string representation of the log record.
        """
        # Build the log entry
        log_entry: dict[str, Any] = {}

        # Timestamp (UTC, ISO 8601)
        log_entry["timestamp"] = datetime.fromtimestamp(record.created, timezone.utc).isoformat()

        # Log level
        log_entry["level"] = record.levelname

        # Logger name
        log_entry["logger"] = record.name

        # Message
        # Handle both regular messages and extra fields
        log_entry["message"] = record.getMessage()

        # Extract custom fields from extra
        issue_id = getattr(record, "issue_id", None)
        action = getattr(record, "action", None)
        outcome = getattr(record, "outcome", None)
        duration_ms: float | None = getattr(record, "duration_ms", None)

        # duration_ms is always in milliseconds (from OperationTimer)
        if duration_ms is None:
            duration_ms = 0.0

        log_entry["issue_id"] = issue_id
        log_entry["action"] = action
        log_entry["outcome"] = outcome
        log_entry["duration_ms"] = round(duration_ms, 2) if duration_ms is not None else None

        # Error fields - only include on errors
        if record.levelno >= logging.ERROR:
            if record.exc_info:
                # Get exception info
                error_message = str(record.exc_info[1]) if record.exc_info[1] else ""
                stack_trace = self.formatException(record.exc_info)
            else:
                # Use message as error message
                error_message = record.getMessage()
                stack_trace = None

            log_entry["error_message"] = error_message
            if stack_trace:
                log_entry["stack_trace"] = stack_trace
        else:
            log_entry["error_message"] = None
            log_entry["stack_trace"] = None

        # Mask sensitive information
        log_entry = self._mask_sensitive_data(log_entry)

        return json.dumps(log_entry, ensure_ascii=False)

    def _mask_sensitive_data(self, log_entry: dict[str, Any]) -> dict[str, Any]:
        """Mask sensitive information in log entry.

        Masks OAuth tokens, IAM tokens, and organization IDs to prevent
        sensitive data leakage in logs (FR-017).

        Args:
            log_entry: Log entry dictionary.

        Returns:
            Log entry with sensitive data masked.
        """
        # Create a copy to avoid modifying the original
        masked = log_entry.copy()

        # Mask sensitive strings in message
        if masked.get("message"):
            masked["message"] = self._mask_token(masked["message"])

        # Mask error messages
        if masked.get("error_message"):
            masked["error_message"] = self._mask_token(masked["error_message"])

        # Mask tokens in any other string fields
        for key, value in masked.items():
            if isinstance(value, str):
                masked[key] = self._mask_token(value)

        return masked

    def _mask_token(self, text: str) -> str:
        """Mask OAuth and IAM tokens in text.

        Args:
            text: Text that may contain sensitive tokens.

        Returns:
            Text with tokens masked.
        """
        # Mask OAuth tokens (start with "y0__")
        if "y0__" in text:
            # Replace token after "y0__" with masked version
            parts = text.split("y0__")
            for i, part in enumerate(parts[1:], start=1):
                # Find the next space or end of token-like string
                # Tokens are typically alphanumeric with some special chars
                import re

                match = re.match(r"([A-Za-z0-9_-]+)", part)
                if match:
                    token_length = len(match.group(1))
                    if token_length > 4:
                        # Mask all but first 4 chars
                        masked_token = match.group(1)[:4] + "*" * (token_length - 4)
                        parts[i] = parts[i].replace(match.group(1), masked_token, 1)

            text = "y0__".join(parts)

        # Mask IAM tokens (start with "t1.")
        if "t1." in text:
            import re

            # Replace after "t1." until next space or end
            text = re.sub(
                r"(t1\.)([A-Za-z0-9_-]{10,})",
                lambda m: m.group(1) + m.group(2)[:4] + "*" * (len(m.group(2)) - 4),
                text,
            )

        # Mask organization IDs (common format: long numeric or alphanum strings)
        # Typically in headers like X-Org-ID or X-Cloud-Org-ID
        import re

        # Mask long alphanumeric strings that look like org IDs (20+ chars)
        text = re.sub(r"\b([A-Z0-9]{20,})\b", lambda m: m.group(1)[:8] + "*" * 12, text)

        return text


class OperationTimer:
    """Context manager for timing operations.

    Use this to measure and log operation duration.

    Example:
        >>> with OperationTimer() as timer:
        ...     do_some_work()
        >>> print(f"Duration: {timer.duration_ms}ms")
    """

    def __init__(self) -> None:
        """Initialize OperationTimer."""
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.duration_ms: float | None = None

    def __enter__(self) -> "OperationTimer":
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        """Stop timing."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000

    def get_duration_ms(self) -> float:
        """Get duration in milliseconds.

        Returns:
            Duration in milliseconds, or 0 if not finished.
        """
        return self.duration_ms if self.duration_ms is not None else 0.0


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger with JSON formatting.

    Args:
        name: Name of the logger.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Only add handler if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


def log_api_call(
    logger: logging.Logger,
    action: str,
    issue_id: str | None = None,
    outcome: str = "success",
    duration_ms: float | None = None,
    error_message: str | None = None,
    stack_trace: str | None = None,
) -> None:
    """Log an API call with structured context.

    Args:
        logger: Logger instance.
        action: Action name (e.g., "authenticate", "fetch_issues").
        issue_id: Issue ID if applicable.
        outcome: "success" or "error".
        duration_ms: Duration in milliseconds.
        error_message: Error message if outcome is "error".
        stack_trace: Stack trace if outcome is "error".
    """
    extra = {
        "action": action,
        "issue_id": issue_id,
        "outcome": outcome,
        "duration_ms": duration_ms,
        "error_message": error_message,
        "stack_trace": stack_trace,
    }

    if outcome == "success":
        logger.info(f"Action completed: {action}", extra=extra)
    else:
        logger.error(f"Action failed: {action}", extra=extra)
