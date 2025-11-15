from typing import Optional

import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer

from config.environment import get_supabase_jwt_secret

security = HTTPBearer()


class AuthMiddleware:
    """Middleware for JWT token verification"""

    def __init__(self):
        self.jwt_secret = get_supabase_jwt_secret()

    def verify_token(self, token: str) -> dict:
        """
        Verify JWT token and extract user information

        Args:
            token: JWT token string

        Returns:
            Decoded token payload containing user info

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Decode and verify the JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"], audience="authenticated")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def __call__(self, request: Request) -> Optional[dict]:
        """
        Extract and verify token from request headers

        Args:
            request: FastAPI request object

        Returns:
            User information from token

        Raises:
            HTTPException: If authentication fails
        """
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            # Extract token from "Bearer <token>" format
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify token and extract user info
        user_info = self.verify_token(token)

        # Add user info to request state for use in route handlers
        request.state.user = user_info

        return user_info


# Singleton instance
auth_middleware = AuthMiddleware()


async def get_current_user(request: Request) -> dict:
    """
    Dependency function to get current authenticated user

    Args:
        request: FastAPI request object

    Returns:
        User information from token
    """
    return await auth_middleware(request)
