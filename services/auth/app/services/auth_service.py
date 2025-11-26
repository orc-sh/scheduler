from typing import Dict, Optional, cast

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
            cast(dict, {"provider": provider, "options": {"redirect_to": redirect_to}})  # type: ignore
        )

        return response.url

    async def sign_up_with_email(self, email: str, password: str, firstname: str, lastname: str) -> Dict:
        """
        Sign up a new user using email and password.

        Args:
            email: User's email address
            password: User's password
            firstname: User's first name
            lastname: User's last name

        Returns:
            Dictionary containing access_token, refresh_token, expires_at and user info

        Raises:
            ValueError: If sign up fails
        """
        full_name = f"{firstname} {lastname}".strip()
        try:
            response = self.supabase.auth.sign_up(  # type: ignore[arg-type]
                {
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "full_name": full_name,
                            "first_name": firstname,
                            "last_name": lastname,
                        }
                    }
                }
            )
        except Exception as e:
            error_msg = str(e)
            if "already registered" in error_msg.lower() or "user already exists" in error_msg.lower():
                raise ValueError("A user with this email already exists. Please sign in instead.")
            raise ValueError(f"Failed to sign up user: {error_msg}")

        if not response.user:
            raise ValueError("Failed to sign up user: No user returned from Supabase")

        # If email confirmation is required, session might be None
        # In that case, we still return the user info but without tokens
        if not response.session:
            # Email confirmation required - user needs to confirm email before getting session
            return {
                "access_token": "",
                "refresh_token": "",
                "expires_at": 0,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "user_metadata": response.user.user_metadata,
                },
                "requires_email_confirmation": True,
            }

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

    async def sign_in_with_email(self, email: str, password: str) -> Dict:
        """
        Sign in a user using email and password.

        Args:
            email: User's email address
            password: User's password

        Returns:
            Dictionary containing access_token, refresh_token, expires_at and user info

        Raises:
            ValueError: If authentication fails
        """
        response = self.supabase.auth.sign_in_with_password(  # type: ignore[arg-type]
            {"email": email, "password": password}
        )

        if not response.session or not response.user:
            raise ValueError("Invalid email or password")

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

    async def exchange_code_for_session(self, code: str) -> Dict:
        """
        Exchange OAuth authorization code for session tokens

        Args:
            code: OAuth authorization code

        Returns:
            Dictionary containing access_token, refresh_token, and user info
        """
        response = self.supabase.auth.exchange_code_for_session(cast(dict, {"auth_code": code}))  # type: ignore

        if not response.session or not response.user:
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

    async def forgot_password(self, email: str) -> bool:
        """
        Send password reset email to user.

        Args:
            email: User's email address

        Returns:
            True if email was sent successfully

        Raises:
            ValueError: If email sending fails
        """
        try:
            redirect_to = f"{self.frontend_url}/reset-password"
            response = self.supabase.auth.reset_password_for_email(  # type: ignore[arg-type]
                email,
                {"redirect_to": redirect_to}
            )
            return True
        except Exception as e:
            error_msg = str(e)
            raise ValueError(f"Failed to send password reset email: {error_msg}")

    async def reset_password(self, password: str, token: str) -> bool:
        """
        Reset user password using reset token.

        Args:
            password: New password
            token: Password reset token from email (access_token from the reset URL)

        Returns:
            True if password was reset successfully

        Raises:
            ValueError: If password reset fails
        """
        try:
            # The token from Supabase password reset email is an access_token
            # Create a new Supabase client instance to avoid session conflicts
            supabase_client = create_client(get_supabase_url(), get_supabase_key())
            
            # Verify the token by getting the user
            try:
                user_response = supabase_client.auth.get_user(token)
                user = user_response.user  # type: ignore
                if not user:
                    raise ValueError("Invalid or expired reset token")
            except Exception as verify_error:
                raise ValueError(f"Invalid or expired reset token: {str(verify_error)}")
            
            # Set the session using the token as both access and refresh token
            # For password reset tokens, we can use the token as the access token
            supabase_client.auth.set_session(token, token)
            
            # Update password using the authenticated session
            response = supabase_client.auth.update_user(cast(dict, {"password": password}))  # type: ignore[arg-type]
            
            if not response.user:
                raise ValueError("Failed to update password")
            
            return True
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            error_msg = str(e)
            raise ValueError(f"Failed to reset password: {error_msg}")

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

            if not response.user:  # type: ignore
                return None

            user = response.user  # type: ignore
            return {
                "id": user.id,
                "email": user.email,
                "user_metadata": user.user_metadata,
                "created_at": user.created_at,
            }
        except Exception as e:
            print(f"Error getting user: {e}")
            return None


# Lazy singleton instance
_auth_service_instance: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get or create the singleton AuthService instance"""
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthService()
    return _auth_service_instance

