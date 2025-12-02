"""
Request context management for storing and accessing a UUID in a thread-safe manner.

This module provides a ContextVar for storing a request-specific UUID,
allowing access throughout the request lifecycle. Useful for tracing, logging, etc.
"""

from contextvars import ContextVar
from typing import Optional
from uuid import UUID

# Thread-safe context variable for storing the current request UUID
_current_uuid: ContextVar[Optional[UUID]] = ContextVar("current_uuid", default=None)


def set_request_uuid(uuid: Optional[UUID]) -> None:
    """
    Set the current request UUID in context.

    Args:
        uuid: The UUID to associate with the current request, or None to clear.
    """
    _current_uuid.set(uuid)


def get_request_uuid() -> Optional[UUID]:
    """
    Retrieve the current request UUID from context.

    Returns:
        The UUID associated with the current request, or None if not set.
    """
    return _current_uuid.get()


def clear_request_uuid() -> None:
    """
    Clear the current request UUID from context.
    """
    _current_uuid.set(None)
