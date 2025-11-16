from pydantic import BaseModel


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""

    refresh_token: str

