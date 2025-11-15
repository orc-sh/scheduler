from typing import Dict, Optional

from supabase import Client, create_client

from config.environment import get_frontend_url, get_supabase_key, get_supabase_url


class AuthService:
    """Service for handling Supabase authentication operations"""

    def __init__(self):
        """Initialize Supabase client"""
        self.supabase: Client = create_client(get_supabase_url(), get_supabase_key())
        self.frontend_url = get_frontend_url()

    def get_oauth_url(self, provider: str) -> str:
        """
        Generate OAuth URL for the specified provider

        Args:
            provider: OAuth provider name (google, github, etc.)

        Returns:
            OAuth authorization URL
        """
        redirect_to = f"{self.frontend_url}/auth/callback"

        response = self.supabase.auth.sign_in_with_oauth(
            {"provider": provider, "options": {"redirect_to": redirect_to}}
        )

        return response.url

    async def exchange_code_for_session(self, code: str) -> Dict:
        """
        Exchange OAuth authorization code for session tokens

        Args:
            code: OAuth authorization code

        Returns:
            Dictionary containing access_token, refresh_token, and user info
        """
        response = self.supabase.auth.exchange_code_for_session({"auth_code": code})

        if not response.session:
            raise ValueError("Failed to exchange code for session")

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "expires_at": response.session.expires_at,
            "user": {
                "id": response.user.id,
                "email": response.user.email,
                "user_metadata": response.user.user_metadata,
            },
        }

    async def refresh_token(self, refresh_token: str) -> Dict:
        """
        Refresh an expired access token

        Args:
            refresh_token: The refresh token

        Returns:
            Dictionary containing new access_token and refresh_token
        """
        response = self.supabase.auth.refresh_session(refresh_token)

        if not response.session:
            raise ValueError("Failed to refresh token")

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "expires_at": response.session.expires_at,
        }

    async def sign_out(self, access_token: str) -> bool:
        """
        Sign out user and revoke session

        Args:
            access_token: User's access token

        Returns:
            True if successful
        """
        try:
            self.supabase.auth.sign_out()
            return True
        except Exception as e:
            print(f"Error signing out: {e}")
            return False

    async def get_user(self, access_token: str) -> Optional[Dict]:
        """
        Get user information from access token

        Args:
            access_token: User's access token

        Returns:
            User information dictionary or None if invalid
        """
        try:
            # Set the session with the access token
            self.supabase.auth.set_session(access_token, "")
            response = self.supabase.auth.get_user(access_token)

            if response.user:
                return {
                    "id": response.user.id,
                    "email": response.user.email,
                    "user_metadata": response.user.user_metadata,
                    "created_at": response.user.created_at,
                }
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None


# Singleton instance
auth_service = AuthService()
