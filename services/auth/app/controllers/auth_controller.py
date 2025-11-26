from fastapi import APIRouter, Depends, HTTPException, Request

from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas import (
    EmailPasswordLoginRequest,
    EmailPasswordRegisterRequest,
    ForgotPasswordRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import get_auth_service

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login_with_email_password(login_request: EmailPasswordLoginRequest):
    """
    Authenticate a user using email and password.

    Args:
        login_request: Contains email and password

    Returns:
        Access token, refresh token, and user information

    Raises:
        HTTPException: If authentication fails
    """
    try:
        session_data = await get_auth_service().sign_in_with_email(
            email=login_request.email,
            password=login_request.password,
        )
        return session_data
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid email or password: {str(e)}")


@router.post("/register", response_model=TokenResponse)
async def register_with_email_password(register_request: EmailPasswordRegisterRequest):
    """
    Register a new user using email and password.

    Args:
        register_request: Contains firstname, lastname, email and password

    Returns:
        Access token, refresh token, and user information

    Raises:
        HTTPException: If registration fails
    """
    try:
        session_data = await get_auth_service().sign_up_with_email(
            email=register_request.email,
            password=register_request.password,
            firstname=register_request.firstname,
            lastname=register_request.lastname,
        )
        return session_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to register user: {str(e)}")


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


@router.post("/forgot-password")
async def forgot_password(forgot_request: ForgotPasswordRequest):
    """
    Send password reset email to user.

    Args:
        forgot_request: Contains email address

    Returns:
        Success message

    Raises:
        HTTPException: If email sending fails
    """
    try:
        await get_auth_service().forgot_password(forgot_request.email)
        return {"message": "Password reset email sent. Please check your inbox."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset-password")
async def reset_password(reset_request: ResetPasswordRequest):
    """
    Reset user password using reset token.

    Args:
        reset_request: Contains new password and reset token

    Returns:
        Success message

    Raises:
        HTTPException: If password reset fails
    """
    try:
        await get_auth_service().reset_password(
            password=reset_request.password,
            token=reset_request.token,
        )
        return {"message": "Password reset successfully. You can now sign in with your new password."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

