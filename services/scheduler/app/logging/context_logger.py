"""
Context-aware logger that injects the current request UUID into log messages.

This module provides a `get_logger` helper that behaves like `logging.getLogger`,
but prefixes all log messages with the UUID stored in `request_context`.
"""

import logging
from typing import Any, MutableMapping, Optional

from app.context.request_context import get_request_uuid


def _format_with_request_id(message: str) -> str:
    """
    Prefix the log message with the current request UUID, if available.

    Example:
        "[request_id=123e4567-e89b-12d3-a456-426614174000] original message"
    """
    request_id = get_request_uuid()
    if request_id is None:
        return message
    return f"[request_id={request_id}] {message}"


class ContextLogger(logging.LoggerAdapter):
    """
    LoggerAdapter that prefixes log messages with the request UUID from context.

    Usage:
        from app.logging.context_logger import get_logger

        logger = get_logger(__name__)
        logger.info("Something happened")
        # -> "[request_id=...uuid...] Something happened"
    """

    def process(
        self,
        msg: Any,
        kwargs: MutableMapping[str, Any],
    ) -> tuple[Any, MutableMapping[str, Any]]:
        # Only alter string messages; leave others untouched.
        if isinstance(msg, str):
            msg = _format_with_request_id(msg)
        return msg, kwargs


def get_logger(name: Optional[str] = None) -> ContextLogger:
    """
    Return a ContextLogger that automatically prefixes messages with request UUID.

    Args:
        name: Logger name, typically `__name__`.
    """
    base_logger = logging.getLogger(name)
    return ContextLogger(base_logger, {})
