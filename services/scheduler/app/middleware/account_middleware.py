"""
Account middleware for setting the current account in the request context.

This middleware fetches the user from the token (via auth middleware) and
gets or creates a account for that user, setting it in the thread context.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.context.account_context import set_current_account_context
from app.context.user_context import get_current_user_context
from app.middleware.auth_middleware import get_current_user
from app.models.accounts import Account
from app.models.user import User
from app.services.account_service import get_account_service
from db.client import client

logger = logging.getLogger(__name__)


async def get_current_account(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
    account_name: Optional[str] = Query(
        None,
        description="Account name to use. If not provided, uses default account or first available account.",
    ),
) -> Account:
    """
    Dependency function to get or create the current account for the user.

    This function:
    1. Gets the authenticated user from the token
    2. Gets or creates a account for that user
    3. Sets the account in the thread context
    4. Returns the account

    Args:
        request: FastAPI request object
        user: Current authenticated user (from auth middleware)
        db: Database session
        account_name: Optional account name from query parameter

    Returns:
        Account instance

    Raises:
        HTTPException: If user is not authenticated or account creation fails

    Example:
        ```python
        @router.get("/api/endpoint")
        async def my_endpoint(
            account: Account = Depends(get_current_account)
        ):
            # Account is automatically set in context
            account_id = account.id
        ```
    """
    try:
        # Get user from context (should already be set by auth middleware)
        current_user = get_current_user_context()
        if not current_user:
            # Fallback to user from dependency
            current_user = user

        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated",
            )

        # Get account service
        account_service = get_account_service(db)

        # Get or create account for the user
        account = account_service.get_or_create_account_by_name(
            user_id=current_user.id,
            account_name=current_user.name,
            user=current_user,
        )

        if not account:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get or create account",
            )

        # Set account in thread-safe context
        set_current_account_context(account)

        # Also add to request state for backwards compatibility
        request.state.account = account

        logger.debug(f"Account context set: {account.id} ({account.name}) for user {current_user.id}")
        return account

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in account middleware: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set account context: {str(e)}",
        )


class AccountMiddleware:
    """Middleware class for account context management."""

    def __init__(self):
        """
        Initialize the account middleware.
        """
        pass

    async def __call__(self, request: Request) -> Optional[Account]:
        """
        Process request to set account context.

        This can be used as FastAPI middleware or in route handlers.

        Args:
            request: FastAPI request object

        Returns:
            Account instance if found/created, None otherwise
        """
        try:
            # Get user from request state (set by auth middleware)
            user: Optional[User] = getattr(request.state, "user", None)
            if not user:
                # Try to get from context
                user = get_current_user_context()
                if not user:
                    logger.warning("No user found in request state or context")
                    return None

            # Get account name from query parameter or use default
            account_name = user.name

            # Get database session
            from db.client import client

            db_gen = client()
            db = next(db_gen, None)
            if not db:
                logger.error("Failed to get database session")
                return None

            try:
                # Get account service
                account_service = get_account_service(db)

                # Get or create account
                account = account_service.get_or_create_account_by_name(
                    user_id=user.id,
                    account_name=account_name,
                    user=user,
                )

                if account:
                    # Set account in thread-safe context
                    set_current_account_context(account)

                    # Also add to request state
                    request.state.account = account

                    logger.debug(f"Account context set: {account.id} ({account.name}) for user {user.id}")
                    return account
                else:
                    logger.warning(f"Failed to get or create account '{account_name}' for user {user.id}")
                    return None
            finally:
                try:
                    next(db_gen, None)  # Complete the generator to trigger cleanup
                except StopIteration:
                    pass
        except Exception as e:
            logger.error(f"Error in account middleware: {str(e)}")
            return None


# Singleton instance
_account_middleware_instance: Optional[AccountMiddleware] = None


def get_account_middleware() -> AccountMiddleware:
    """
    Get or create the singleton AccountMiddleware instance.

    Args:
        default_account_name: Default account name to use

    Returns:
        AccountMiddleware instance
    """
    global _account_middleware_instance
    if _account_middleware_instance is None:
        _account_middleware_instance = AccountMiddleware()
    return _account_middleware_instance
