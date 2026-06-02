"""Tests for JsonFormatter - Sensitive Information Protection (T079)."""

import json
import logging
import pytest

from symphony_yandex_tracker.logger import JsonFormatter, get_logger


class TestSensitiveDataMasking:
    """Test suite for sensitive data masking in JsonFormatter.

    Verifies that OAuth tokens, org IDs, query params, and authorization
    headers are properly masked in log output.
    """

    def _format_log(self, message: str, **extra_fields) -> dict:
        """Helper to format a log message and return parsed JSON."""
        # Create a logger and handler
        handler = logging.StreamHandler()
        formatter = JsonFormatter()
        handler.setFormatter(formatter)

        logger = logging.getLogger("test_masking")
        logger.handlers = []  # Clear existing handlers
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Add extra fields to record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None,
        )
        # Set extra fields
        for key, value in extra_fields.items():
            setattr(record, key, value)

        # Format using the formatter
        output = formatter.format(record)
        return json.loads(output)

    # T079a: OAuth token masking (show first 4 chars + ***)
    def test_oauth_token_masked(self):
        """Test T079a: OAuth token is masked, showing only first 4 chars."""
        result = self._format_log("Token: y0_abc123defgh456")

        # Should mask but keep first 4 chars visible
        assert "***" in result["message"]
        # First 4 chars should be visible
        assert "y0_ab" in result["message"]
        # Full token should NOT appear
        assert "abc123defgh456" not in result["message"]

    def test_oauth_token_in_url_masked(self):
        """Test OAuth token in URL is masked."""
        result = self._format_log("Request to https://api.example.com/oauth/y0_myToken123")

        assert "***" in result["message"]
        assert "y0_my" in result["message"]

    # T079b: Organization ID masking (show last 4 chars)
    def test_org_id_masked(self):
        """Test T079b: Org ID is masked, showing only last 4 chars."""
        # Long org ID (20+ chars)
        org_id = "123456789012345678901234567890"
        result = self._format_log(f"Org: {org_id}")

        # Last 4 chars should be visible
        assert "7890" in result["message"]
        # First chars should be masked
        assert "12345678" not in result["message"]

    def test_org_id_in_header_masked(self):
        """Test org ID in custom header is masked."""
        result = self._format_log("Header X-Org-ID: 1122334455667788990011")

        # Last 4 visible
        assert "0011" in result["message"]
        # Full not visible
        assert "2233445566778899" not in result["message"]

    # T079c: Query params token filtering
    def test_query_param_token_filtered(self):
        """Test T079c: Query param with token is filtered."""
        result = self._format_log("GET https://api.example.com?q=1&token=secret123")

        assert "token=***" in result["message"]
        assert "secret123" not in result["message"]

    def test_query_param_oauth_filtered(self):
        """Test oauth parameter in query string is filtered."""
        result = self._format_log("GET https://api.example.com?oauth=tokenvalue")

        assert "oauth=***" in result["message"]
        assert "tokenvalue" not in result["message"]

    def test_query_param_access_token_filtered(self):
        """Test access_token parameter is filtered."""
        result = self._format_log("POST /api?access_token=abc123")

        assert "access_token=***" in result["message"]
        assert "abc123" not in result["message"]

    def test_query_param_refresh_token_filtered(self):
        """Test refresh_token parameter is filtered."""
        result = self._format_log("/api?refresh_token=xyz789")

        assert "refresh_token=***" in result["message"]
        assert "xyz789" not in result["message"]

    # T079d: Authorization header filtering
    def test_authorization_header_masked(self):
        """Test T079d: Authorization header is masked."""
        result = self._format_log("Authorization: Bearer y0_abc123def")

        # Value should be masked (starts with ***)
        assert "***" in result["message"]
        # But first 4 chars of token after prefix visible
        assert "y0_ab" in result["message"]
        # Full token hidden
        assert "abc123def" not in result["message"]

    def test_authorization_without_bearer_masked(self):
        """Test Authorization without Bearer prefix is masked."""
        result = self._format_log('Auth: {"Authorization": "t1.iam.tokenvalue"}')

        assert "***" in result["message"]

    # Test IAM tokens (start with "t1.")
    def test_iam_token_masked(self):
        """Test IAM token starting with t1. is masked."""
        result = self._format_log("IAM: t1.iamtokenvalue1234567890")

        # Should show first 4 chars after prefix
        assert "t1.iam" in result["message"]
        assert "***" in result["message"]
        # Full token hidden
        assert "tokenvalue1234567890" not in result["message"]

    # Test combined scenarios
    def test_multiple_sensitive_fields_masked(self):
        """Test multiple sensitive fields are all masked."""
        org_id = "9988776655443322110000"
        result = self._format_log(
            f"Request to /api?token=abc123&id={org_id}&oauth=x",
            issue_id=org_id,
        )

        # Both token and org ID masked
        assert "***" in result["message"]
        assert "token=" in result["message"]  # key remains
        assert "oauth=" in result["message"]  # key remains
        assert "0000" in result["message"]  # org ID last 4

    def test_no_masking_for_normal_strings(self):
        """Test normal strings without sensitive data are unchanged."""
        result = self._format_log("Simple message without敏感数据")

        assert result["message"] == "Simple message without敏感数据"


class TestOperationTimer:
    """Test suite for OperationTimer."""

    def test_timer_records_duration_ms(self):
        """Test timer records duration in milliseconds."""
        from symphony_yandex_tracker.logger import OperationTimer
        import time

        with OperationTimer() as timer:
            time.sleep(0.01)  # 10ms

        assert timer.duration_ms is not None
        assert timer.duration_ms >= 10.0

    def test_get_duration_ms_returns_zero_when_not_stopped(self):
        """Test get_duration_ms returns 0 if timer not used."""
        from symphony_yandex_tracker.logger import OperationTimer

        timer = OperationTimer()
        assert timer.get_duration_ms() == 0.0


class TestJsonFormatterHelpers:
    """Test suite for JSON formatter helper methods."""

    def test_format_json(self):
        """Test formatter outputs valid JSON."""
        handler = logging.StreamHandler()
        formatter = JsonFormatter()
        handler.setFormatter(formatter)

        logger = logging.getLogger("test_structure")
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        setattr(record, "action", "test")
        setattr(record, "outcome", "success")

        output = formatter.format(record)
        result = json.loads(output)

        assert "timestamp" in result
        assert "level" in result
        assert "logger" in result
        assert "message" in result
        assert "issue_id" in result
        assert "action" in result
        assert "outcome" in result
        assert "duration_ms" in result