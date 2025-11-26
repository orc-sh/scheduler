from pydantic import BaseModel, EmailStr


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""

    refresh_token: str


class EmailPasswordLoginRequest(BaseModel):
    """Email/password login request"""

    email: EmailStr
    password: str


class EmailPasswordRegisterRequest(BaseModel):
    """Email/password registration request"""

    firstname: str
    lastname: str
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    """Forgot password request"""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request"""

    password: str
    token: str

