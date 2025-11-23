"""
User model for authentication and context management.

This is a plain Python class (not a database model) since user data
is stored in Supabase, not in the local database.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class User:
    """
    Plain Python class representing an authenticated user.

    This class is initialized from JWT token payload during authentication
    and stored in request context for use throughout the application.
    """

    id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    aud: Optional[str] = None
    session_id: Optional[str] = None
    app_metadata: Optional[Dict[str, Any]] = None
    user_metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    email_confirmed_at: Optional[datetime] = None
    phone_confirmed_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    last_sign_in_at: Optional[datetime] = None

    @classmethod
    def from_jwt_payload(cls, payload: Dict[str, Any]) -> "User":
        """
        Create a User instance from decoded JWT token payload.

        Args:
            payload: Decoded JWT token payload from Supabase

        Returns:
            User instance with populated fields
        """

        # Parse datetime strings if present
        def parse_datetime(value: Optional[Any]) -> Optional[datetime]:
            if value is None:
                return None
            if isinstance(value, datetime):
                return value
            if isinstance(value, (int, float)):
                return datetime.fromtimestamp(value)
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    return None
            return None

        return cls(
            id=payload.get("sub"),
            email=payload.get("email"),
            phone=payload.get("phone"),
            role=payload.get("role"),
            aud=payload.get("aud"),
            session_id=payload.get("session_id"),
            app_metadata=payload.get("app_metadata", {}),
            user_metadata=payload.get("user_metadata", {}),
            created_at=parse_datetime(payload.get("created_at")),
            updated_at=parse_datetime(payload.get("updated_at")),
            email_confirmed_at=parse_datetime(payload.get("email_confirmed_at")),
            phone_confirmed_at=parse_datetime(payload.get("phone_confirmed_at")),
            confirmed_at=parse_datetime(payload.get("confirmed_at")),
            last_sign_in_at=parse_datetime(payload.get("last_sign_in_at")),
        )

    @classmethod
    def from_supabase_user(cls, user_data: Dict[str, Any]) -> "User":
        """
        Create a User instance from Supabase user object.

        Args:
            user_data: User data from Supabase API response

        Returns:
            User instance with populated fields
        """

        def parse_datetime(value: Optional[str]) -> Optional[datetime]:
            if value is None:
                return None
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return None

        return cls(
            id=user_data.get("id"),
            email=user_data.get("email"),
            phone=user_data.get("phone"),
            role=user_data.get("role"),
            aud=user_data.get("aud"),
            session_id=None,  # Not typically in user object
            app_metadata=user_data.get("app_metadata", {}),
            user_metadata=user_data.get("user_metadata", {}),
            created_at=parse_datetime(user_data.get("created_at")),
            updated_at=parse_datetime(user_data.get("updated_at")),
            email_confirmed_at=parse_datetime(user_data.get("email_confirmed_at")),
            phone_confirmed_at=parse_datetime(user_data.get("phone_confirmed_at")),
            confirmed_at=parse_datetime(user_data.get("confirmed_at")),
            last_sign_in_at=parse_datetime(user_data.get("last_sign_in_at")),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert User instance to dictionary.

        Returns:
            Dictionary representation of the user
        """

        def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
            return dt.isoformat() if dt else None

        return {
            "id": self.id,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "aud": self.aud,
            "session_id": self.session_id,
            "app_metadata": self.app_metadata,
            "user_metadata": self.user_metadata,
            "created_at": serialize_datetime(self.created_at),
            "updated_at": serialize_datetime(self.updated_at),
            "email_confirmed_at": serialize_datetime(self.email_confirmed_at),
            "phone_confirmed_at": serialize_datetime(self.phone_confirmed_at),
            "confirmed_at": serialize_datetime(self.confirmed_at),
            "last_sign_in_at": serialize_datetime(self.last_sign_in_at),
        }

    def __repr__(self) -> str:
        """String representation of User."""
        return f"User(id='{self.id}', email='{self.email}', role='{self.role}')"

    def has_role(self, role: str) -> bool:
        """
        Check if user has a specific role.

        Args:
            role: Role name to check

        Returns:
            True if user has the role, False otherwise
        """
        return self.role == role

    def is_email_confirmed(self) -> bool:
        """Check if user's email is confirmed."""
        return self.email_confirmed_at is not None

    def is_phone_confirmed(self) -> bool:
        """Check if user's phone is confirmed."""
        return self.phone_confirmed_at is not None

    @property
    def name(self) -> str:
        """
        Get user's display name.

        Returns name from user_metadata if available, otherwise falls back to:
        1. Full name from user_metadata
        2. Email (username part)
        3. User ID

        Returns:
            User's display name
        """
        # Try to get name from user_metadata
        if self.user_metadata:
            # Check for various name fields
            if "name" in self.user_metadata:
                return self.user_metadata["name"]
            if "full_name" in self.user_metadata:
                return self.user_metadata["full_name"]
            if "display_name" in self.user_metadata:
                return self.user_metadata["display_name"]

        # Fall back to email username
        if self.email:
            return self.email.split("@")[0]

        # Last resort: use ID
        return self.id

    @property
    def tier(self) -> str:
        """
        Get user's subscription tier.

        Returns:
            'pro' or 'free' (defaults to 'free')
        """
        from app.utils.cron_validator import get_user_tier

        return get_user_tier(self)
