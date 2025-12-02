import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer

from app.context.user_context import set_current_user_context
from app.models.user import User
from app.utils.jwt_helper import validate_jwt_token
from config.environment import get_chargebee_jwt_client_secret

security = HTTPBearer()


class JwtMiddleware:
    """Middleware for JWT token verification"""

    def __init__(self):
        self.jwt_secret = get_chargebee_jwt_client_secret()

    def validate_token(self, token: str) -> dict:
        """Validate a JWT token and return its payload."""
        return validate_jwt_token(token, self.jwt_secret)

    async def __call__(self, request: Request, call_next):
        """Validate a JWT token and return its payload."""
        token = request.query_params.get("token")
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        try:
            payload = self.validate_token(token)
            user = User.from_jwt_payload(payload)
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user = User.from_jwt_payload(payload)
        set_current_user_context(user)
        return await call_next(request)


def get_jwt_middleware() -> JwtMiddleware:
    """Get the singleton instance of the JwtMiddleware"""
    return JwtMiddleware()
