from pydantic import BaseModel


class UserResponse(BaseModel):
    """User information response"""

    id: str
    email: str
    user_metadata: dict

