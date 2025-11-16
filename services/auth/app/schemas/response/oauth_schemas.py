from pydantic import BaseModel


class OAuthProvider(BaseModel):
    """OAuth provider information"""

    name: str
    display_name: str


class OAuthURLResponse(BaseModel):
    """OAuth authorization URL response"""

    url: str
    provider: str

