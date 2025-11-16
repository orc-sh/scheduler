from fastapi import APIRouter, Depends, HTTPException, Request

from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas import RefreshTokenRequest, TokenResponse, UserResponse
from app.services.auth_service import get_auth_service

router = APIRouter()


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(refresh_request: RefreshTokenRequest):
    """
    Refresh an expired access token

    Args:
        refresh_request: Contains refresh token

    Returns:
        New access token and refresh token

    Raises:
        HTTPException: If token refresh fails
    """
    try:
        new_tokens = await get_auth_service().refresh_token(refresh_request.refresh_token)
        return new_tokens
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Failed to refresh token: {str(e)}")


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)):
    """
    Sign out the current user

    Args:
        user: Current authenticated user (from dependency)

    Returns:
        Success message
    """
    # Extract token from request if needed
    success = await get_auth_service().sign_out("")

    if success:
        return {"message": "Successfully logged out"}
    else:
        raise HTTPException(status_code=500, detail="Failed to log out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(request: Request, user: User = Depends(get_current_user)):
    """
    Get current authenticated user's information

    Args:
        request: FastAPI request object
        user: Current authenticated user (from dependency)

    Returns:
        User information
    """
    # Extract token from request
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")

    user_info = await get_auth_service().get_user(token)

    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user_info

