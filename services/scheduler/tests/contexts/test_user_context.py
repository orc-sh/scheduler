"""
Tests for User context management.

These tests demonstrate how to work with the User class and context.
"""

from datetime import datetime

import pytest

from app.context.user_context import (
    clear_current_user_context,
    get_current_user_context,
    require_current_user_context,
    set_current_user_context,
)
from app.models.user import User


class TestUserModel:
    """Tests for the User dataclass."""

    def test_user_from_jwt_payload(self):
        """Test creating User from JWT payload."""
        jwt_payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "role": "user",
            "aud": "authenticated",
            "session_id": "session-456",
            "app_metadata": {"provider": "google"},
            "user_metadata": {"name": "Test User"},
        }

        user = User.from_jwt_payload(jwt_payload)

        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.role == "user"
        assert user.aud == "authenticated"
        assert user.session_id == "session-456"
        assert user.app_metadata == {"provider": "google"}
        assert user.user_metadata == {"name": "Test User"}

    def test_user_from_supabase_user(self):
        """Test creating User from Supabase user object."""
        supabase_user = {
            "id": "user-789",
            "email": "supabase@example.com",
            "phone": "+1234567890",
            "role": "admin",
            "created_at": "2024-01-01T00:00:00Z",
            "user_metadata": {"theme": "dark"},
        }

        user = User.from_supabase_user(supabase_user)

        assert user.id == "user-789"
        assert user.email == "supabase@example.com"
        assert user.phone == "+1234567890"
        assert user.role == "admin"
        assert user.user_metadata == {"theme": "dark"}

    def test_user_to_dict(self):
        """Test converting User to dictionary."""
        user = User(
            id="user-999",
            email="dict@example.com",
            role="user",
        )

        user_dict = user.to_dict()

        assert user_dict["id"] == "user-999"
        assert user_dict["email"] == "dict@example.com"
        assert user_dict["role"] == "user"

    def test_user_has_role(self):
        """Test role checking."""
        admin_user = User(id="admin-1", role="admin")
        regular_user = User(id="user-1", role="user")

        assert admin_user.has_role("admin") is True
        assert admin_user.has_role("user") is False
        assert regular_user.has_role("user") is True
        assert regular_user.has_role("admin") is False

    def test_user_is_email_confirmed(self):
        """Test email confirmation status."""
        confirmed_user = User(id="user-1", email="confirmed@example.com", email_confirmed_at=datetime.now())
        unconfirmed_user = User(id="user-2", email="unconfirmed@example.com", email_confirmed_at=None)

        assert confirmed_user.is_email_confirmed() is True
        assert unconfirmed_user.is_email_confirmed() is False


class TestUserContext:
    """Tests for user context management."""

    def setup_method(self):
        """Clear context before each test."""
        clear_current_user_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_current_user_context()

    def test_set_and_get_user_context(self):
        """Test setting and getting user from context."""
        user = User(id="context-1", email="context@example.com")

        # Initially, context should be empty
        assert get_current_user_context() is None

        # Set user in context
        set_current_user_context(user)

        # Get user from context
        retrieved_user = get_current_user_context()
        assert retrieved_user is not None
        assert retrieved_user.id == "context-1"
        assert retrieved_user.email == "context@example.com"

    def test_require_user_context_with_user(self):
        """Test requiring user when user is set."""
        user = User(id="required-1", email="required@example.com")
        set_current_user_context(user)

        # Should not raise exception
        retrieved_user = require_current_user_context()
        assert retrieved_user.id == "required-1"

    def test_require_user_context_without_user(self):
        """Test requiring user when user is not set."""
        # Context is empty (no user set)

        # Should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            require_current_user_context()

        assert "No user found in context" in str(exc_info.value)

    def test_clear_user_context(self):
        """Test clearing user from context."""
        user = User(id="clear-1", email="clear@example.com")

        # Set user
        set_current_user_context(user)
        assert get_current_user_context() is not None

        # Clear user
        clear_current_user_context()
        assert get_current_user_context() is None

    def test_context_isolation(self):
        """Test that setting user doesn't affect other contexts."""
        user1 = User(id="isolated-1", email="user1@example.com")
        user2 = User(id="isolated-2", email="user2@example.com")

        # Set first user
        set_current_user_context(user1)
        assert get_current_user_context().id == "isolated-1"

        # Set second user (overwrites first)
        set_current_user_context(user2)
        assert get_current_user_context().id == "isolated-2"


class TestUserIntegration:
    """Integration tests demonstrating real-world usage."""

    def setup_method(self):
        """Clear context before each test."""
        clear_current_user_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_current_user_context()

    def test_jwt_to_context_flow(self):
        """Test the complete flow: JWT -> User -> Context."""
        # Simulate JWT payload from authentication
        jwt_payload = {
            "sub": "flow-123",
            "email": "flow@example.com",
            "role": "admin",
            "aud": "authenticated",
            "user_metadata": {"preferences": {"theme": "dark"}},
        }

        # Create user from JWT (as middleware would do)
        user = User.from_jwt_payload(jwt_payload)

        # Set in context (as middleware would do)
        set_current_user_context(user)

        # Access from context (as application code would do)
        current_user = get_current_user_context()

        # Verify all data is preserved
        assert current_user.id == "flow-123"
        assert current_user.email == "flow@example.com"
        assert current_user.has_role("admin")
        assert current_user.user_metadata["preferences"]["theme"] == "dark"

    def test_service_layer_usage(self):
        """Test using user context in service layer."""

        # Simulate a service class
        class UserService:
            def get_user_email(self) -> str:
                user = require_current_user_context()
                return user.email

            def get_user_permissions(self) -> list:
                user = get_current_user_context()
                if user and user.has_role("admin"):
                    return ["read", "write", "delete"]
                return ["read"]

        # Set up user
        admin_user = User(id="service-1", email="admin@example.com", role="admin")
        set_current_user_context(admin_user)

        # Use service
        service = UserService()
        assert service.get_user_email() == "admin@example.com"
        assert "delete" in service.get_user_permissions()

    def test_utility_function_usage(self):
        """Test using user context in utility functions."""

        def audit_log(action: str) -> dict:
            """Example utility function that logs user actions."""
            user = get_current_user_context()
            return {
                "action": action,
                "user_id": user.id if user else None,
                "user_email": user.email if user else None,
            }

        # Without user
        log_entry = audit_log("test_action")
        assert log_entry["user_id"] is None

        # With user
        user = User(id="util-1", email="util@example.com")
        set_current_user_context(user)
        log_entry = audit_log("test_action")
        assert log_entry["user_id"] == "util-1"
        assert log_entry["user_email"] == "util@example.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
