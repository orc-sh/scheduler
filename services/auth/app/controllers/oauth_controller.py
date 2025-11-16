from typing import List

from fastapi import APIRouter, HTTPException

from app.schemas import OAuthCallbackRequest, OAuthProvider, OAuthURLResponse, TokenResponse
from app.services.auth_service import get_auth_service

router = APIRouter()


@router.get("/providers", response_model=List[OAuthProvider])
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


@router.get("/{provider}", response_model=OAuthURLResponse)
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
        oauth_url = get_auth_service().get_oauth_url(provider.lower())
        return {"url": oauth_url, "provider": provider}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate OAuth flow: {str(e)}")


@router.post("/callback", response_model=TokenResponse)
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
        session_data = await get_auth_service().exchange_code_for_session(callback_request.code)
        return session_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to exchange code for session: {str(e)}")

