from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Authentication token response"""

    access_token: str
    refresh_token: str
    expires_at: int
    user: dict

