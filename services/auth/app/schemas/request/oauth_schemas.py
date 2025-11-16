from pydantic import BaseModel


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request with authorization code"""

    code: str

