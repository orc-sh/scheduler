"""
User-specific test data factories.
"""

import uuid
from typing import Optional

from app.models.user import User


class UserFactory:
    """Factory for creating User test objects."""

    @staticmethod
    def create(
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        role: str = "user",
        phone: Optional[str] = None,
        **kwargs,
    ) -> User:
        """
        Create a User instance (not persisted).
        """
        uid = user_id or str(uuid.uuid4())
        return User(
            id=uid,
            email=email or f"user-{uid[:8]}@example.com",
            role=role,
            phone=phone,
            aud="authenticated",
            **kwargs,
        )

    @staticmethod
    def create_admin(
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        **kwargs,
    ) -> User:
        """
        Create an admin User instance (not persisted).
        """
        return UserFactory.create(user_id=user_id, email=email, role="admin", **kwargs)

    @staticmethod
    def create_batch(count: int = 3) -> list[User]:
        """
        Create multiple User instances (not persisted).
        """
        return [UserFactory.create() for _ in range(count)]
