"""
User dependencies for FastAPI dependency injection.

These dependencies allow accessing the current authenticated user
from the context without needing to pass the request object.
"""

from typing import Optional

from fastapi import HTTPException, status

from app.context.user_context import get_current_user_context, require_current_user_context
from app.models.user import User


def get_current_user_from_context() -> Optional[User]:
    """
    FastAPI dependency to get the current user from context.

    Returns:
        Current authenticated User instance, or None if not set

    Example:
        ```python
        from fastapi import APIRouter, Depends
        from app.dependencies import get_current_user_from_context
        from app.models.user import User

        router = APIRouter()

        @router.get("/profile")
        async def get_profile(user: User = Depends(get_current_user_from_context)):
            if user:
                return {"email": user.email}
            return {"message": "Not authenticated"}
        ```
    """
    return get_current_user_context()


def require_user_from_context() -> User:
    """
    FastAPI dependency to get the current user from context, with required authentication.

    Returns:
        Current authenticated User instance

    Raises:
        HTTPException: 401 if no user is in context

    Example:
        ```python
        from fastapi import APIRouter, Depends
        from app.dependencies import require_user_from_context
        from app.models.user import User

        router = APIRouter()

        @router.get("/")
        async def get_dashboard(user: User = Depends(require_user_from_context)):
            # This endpoint requires authentication
            return {"user_id": user.id, "email": user.email}
        ```
    """
    try:
        return require_current_user_context()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
