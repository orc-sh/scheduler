"""
Account context management using contextvars for thread-safe access.

This module provides thread-safe context storage for the current account.
The account context is set during middleware and can be accessed
throughout the application request lifecycle.
"""

from contextvars import ContextVar
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.models.accounts import Account

# Thread-safe context variable for storing the current account
_current_account: ContextVar[Optional["Account"]] = ContextVar("current_account", default=None)


def set_current_account_context(account: Optional["Account"]) -> None:
    """
    Set the current account in the context.

    This should be called by the account middleware after
    successfully identifying or creating the account.

    Args:
        account: Account instance to store in context, or None to clear

    Example:
        ```python
        # In middleware
        account = account_service.get_or_create_account_by_name(user_id, account_name, user)
        set_current_account_context(account)
        ```
    """
    _current_account.set(account)


def get_current_account_context() -> "Account":
    """
    Get the current account from the context.

    Returns:
        Current Account instance, or None if not set

    Example:
        ```python
        # In any part of the application
        account = get_current_account_context()
        if account:
            print(f"Current account: {account.name}")
        ```
    """
    account = _current_account.get()
    if account is None:
        raise RuntimeError("No account found in context. Ensure the account middleware has been applied.")
    return account


def clear_current_account_context() -> None:
    """
    Clear the current account from the context.

    This can be used to explicitly clear the account context,
    though it typically clears automatically after the request completes.
    """
    _current_account.set(None)


def require_current_account_context() -> "Account":
    """
    Get the current account from the context, raising an exception if not set.

    Returns:
        Current Account instance

    Raises:
        RuntimeError: If no account is set in the context

    Example:
        ```python
        # In a function that requires a account
        try:
            account = require_current_account_context()
            print(f"Processing request for account {account.name}")
        except RuntimeError:
            # Handle missing account
            pass
        ```
    """
    account = _current_account.get()
    if account is None:
        raise RuntimeError("No account found in context. Ensure the account middleware has been applied.")
    return account
