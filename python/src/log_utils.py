"""Logging utilities."""

import logging
from typing import Any
from contextvars import ContextVar

request_id: ContextVar[str] = ContextVar("request_id")


class ContextualLogger:
    """Logger that includes context information."""

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _format_message(self, message: str) -> str:
        try:
            ctx_id = request_id.get()
            return f"[RequestID: {ctx_id}] {message}"
        except LookupError:
            return message

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.info(self._format_message(message), *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.error(self._format_message(message), *args, **kwargs)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.debug(self._format_message(message), *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._logger.warning(self._format_message(message), *args, **kwargs)


def get_logger(name: str) -> ContextualLogger:
    """Get a contextual logger instance."""
    return ContextualLogger(logging.getLogger(name))
