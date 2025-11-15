from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.middleware.auth_middleware import get_current_user
from app.services.auth_service import auth_service

router = APIRouter()


class OAuthProvider(BaseModel):
    """OAuth provider information"""

    name: str
    display_name: str


class OAuthURLResponse(BaseModel):
    """OAuth authorization URL response"""

    url: str
    provider: str


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request with authorization code"""

    code: str


class TokenResponse(BaseModel):
    """Authentication token response"""

    access_token: str
    refresh_token: str
    expires_at: int
    user: dict


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""

    refresh_token: str


class UserResponse(BaseModel):
    """User information response"""

    id: str
    email: str
    user_metadata: dict


@router.get("/oauth/providers", response_model=List[OAuthProvider])
async def get_oauth_providers():
    """
    Get list of available OAuth providers

    Returns:
        List of OAuth provider information
    """
    return [
        {"name": "google", "display_name": "Google"},
        {"name": "github", "display_name": "GitHub"},
    ]


@router.get("/oauth/{provider}", response_model=OAuthURLResponse)
async def initiate_oauth(provider: str):
    """
    Initiate OAuth flow for specified provider

    Args:
        provider: OAuth provider name (google, github)

    Returns:
        OAuth authorization URL to redirect user to

    Raises:
        HTTPException: If provider is not supported
    """
    supported_providers = ["google", "github"]

    if provider.lower() not in supported_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider}' not supported. Supported providers: {', '.join(supported_providers)}",
        )

    try:
        oauth_url = auth_service.get_oauth_url(provider.lower())
        return {"url": oauth_url, "provider": provider}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate OAuth flow: {str(e)}")


@router.post("/oauth/callback", response_model=TokenResponse)
async def oauth_callback(callback_request: OAuthCallbackRequest):
    """
    Handle OAuth callback and exchange code for tokens

    Args:
        callback_request: Contains authorization code from OAuth provider

    Returns:
        Access token, refresh token, and user information

    Raises:
        HTTPException: If code exchange fails
    """
    try:
        session_data = await auth_service.exchange_code_for_session(callback_request.code)
        return session_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to exchange code for session: {str(e)}")


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
        new_tokens = await auth_service.refresh_token(refresh_request.refresh_token)
        return new_tokens
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Failed to refresh token: {str(e)}")


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    """
    Sign out the current user

    Args:
        user: Current authenticated user (from dependency)

    Returns:
        Success message
    """
    # Extract token from request if needed
    success = await auth_service.sign_out("")

    if success:
        return {"message": "Successfully logged out"}
    else:
        raise HTTPException(status_code=500, detail="Failed to log out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(request: Request, user: dict = Depends(get_current_user)):
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

    user_info = await auth_service.get_user(token)

    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user_info
