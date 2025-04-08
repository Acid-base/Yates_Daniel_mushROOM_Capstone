"""Tests for logging utilities."""

import logging
from unittest.mock import Mock, patch
import pytest
from utils.logging import ContextualLogger, get_logger, request_id


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return Mock(spec=logging.Logger)


@pytest.fixture
def contextual_logger(mock_logger):
    """Create a contextual logger with a mock base logger."""
    return ContextualLogger(mock_logger)


def test_contextual_logger_with_request_id(contextual_logger):
    """Test logging with request ID in context."""
    token = request_id.set("test-request-id")
    try:
        contextual_logger.info("Test message")
        contextual_logger._logger.info.assert_called_once_with(
            "[RequestID: test-request-id] Test message"
        )
    finally:
        request_id.reset(token)


def test_contextual_logger_without_request_id(contextual_logger):
    """Test logging without request ID in context."""
    contextual_logger.info("Test message")
    contextual_logger._logger.info.assert_called_once_with("Test message")


def test_contextual_logger_error(contextual_logger):
    """Test error logging."""
    contextual_logger.error("Error message")
    contextual_logger._logger.error.assert_called_once_with("Error message")


def test_contextual_logger_debug(contextual_logger):
    """Test debug logging."""
    contextual_logger.debug("Debug message")
    contextual_logger._logger.debug.assert_called_once_with("Debug message")


def test_contextual_logger_with_args(contextual_logger):
    """Test logging with additional arguments."""
    contextual_logger.info("Test %s %d", "message", 123)
    contextual_logger._logger.info.assert_called_once_with("Test %s %d", "message", 123)


def test_contextual_logger_with_kwargs(contextual_logger):
    """Test logging with keyword arguments."""
    contextual_logger.info("Test message", extra={"key": "value"})
    contextual_logger._logger.info.assert_called_once_with(
        "Test message", extra={"key": "value"}
    )


def test_get_logger():
    """Test get_logger factory function."""
    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = Mock(spec=logging.Logger)
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test_module")

        mock_get_logger.assert_called_once_with("test_module")
        assert isinstance(logger, ContextualLogger)
        assert logger._logger == mock_logger


def test_nested_context():
    """Test nested request context handling."""
    outer_token = request_id.set("outer-request")
    try:
        logger = get_logger("test")
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock(spec=logging.Logger)
            mock_get_logger.return_value = mock_logger

            logger.info("Outer message")
            mock_logger.info.assert_called_with(
                "[RequestID: outer-request] Outer message"
            )

            inner_token = request_id.set("inner-request")
            try:
                logger.info("Inner message")
                mock_logger.info.assert_called_with(
                    "[RequestID: inner-request] Inner message"
                )
            finally:
                request_id.reset(inner_token)

            logger.info("Back to outer message")
            mock_logger.info.assert_called_with(
                "[RequestID: outer-request] Back to outer message"
            )
    finally:
        request_id.reset(outer_token)


def test_multiple_loggers_same_context():
    """Test multiple loggers using the same request context."""
    token = request_id.set("shared-request")
    try:
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger1 = Mock(spec=logging.Logger)
            mock_logger2 = Mock(spec=logging.Logger)
            mock_get_logger.side_effect = [mock_logger1, mock_logger2]

            logger1.info("Message from logger1")
            logger2.info("Message from logger2")

            mock_logger1.info.assert_called_with(
                "[RequestID: shared-request] Message from logger1"
            )
            mock_logger2.info.assert_called_with(
                "[RequestID: shared-request] Message from logger2"
            )
    finally:
        request_id.reset(token)
