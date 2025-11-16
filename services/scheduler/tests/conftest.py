"""
Pytest configuration and fixtures for the scheduler service tests.

This module provides shared fixtures for database, API client, authentication,
and test data generation.
"""

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.context.user_context import clear_current_user_context, set_current_user_context
from app.main import app
from app.models.base import Base
from app.models.user import User
from db.client import client as get_db

# Test database configuration
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    """
    Create a test database engine.

    Uses SQLite in-memory database for fast, isolated tests.
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create a session factory for the test database."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session(test_engine, test_session_factory) -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.

    This fixture:
    1. Creates all tables before the test
    2. Yields a database session
    3. Rolls back changes after the test
    4. Drops all tables for a clean slate

    Yields:
        Database session for testing
    """
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create a new session
    session = test_session_factory()

    try:
        yield session
    finally:
        session.rollback()
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with database dependency override.

    Args:
        db_session: Test database session

    Yields:
        TestClient for making API requests
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user() -> User:
    """
    Create a test user for authentication.

    Returns:
        User instance with test data
    """
    return User(
        id="test-user-123",
        email="test@example.com",
        role="user",
        aud="authenticated",
    )


@pytest.fixture(scope="function")
def another_user() -> User:
    """
    Create another test user for multi-user scenarios.

    Returns:
        User instance with different test data
    """
    return User(
        id="another-user-456",
        email="another@example.com",
        role="user",
        aud="authenticated",
    )


@pytest.fixture(scope="function")
def admin_user() -> User:
    """
    Create an admin test user.

    Returns:
        User instance with admin role
    """
    return User(
        id="admin-user-789",
        email="admin@example.com",
        role="admin",
        aud="authenticated",
    )


@pytest.fixture(scope="function", autouse=True)
def clear_user_context():
    """
    Automatically clear user context before and after each test.

    This prevents context pollution between tests.
    """
    clear_current_user_context()
    yield
    clear_current_user_context()


@pytest.fixture(scope="function")
def authenticated_client(client: TestClient, test_user: User) -> TestClient:
    """
    Create an authenticated test client.

    This fixture sets up the user context so that endpoints requiring
    authentication will work.

    Args:
        client: FastAPI test client
        test_user: Test user to authenticate as

    Returns:
        TestClient with user context set
    """
    set_current_user_context(test_user)
    return client


@pytest.fixture(scope="function")
def auth_headers() -> dict:
    """
    Create authentication headers for API requests.

    Returns:
        Dictionary with Authorization header
    """
    return {
        "Authorization": "Bearer test-token-12345",
        "Content-Type": "application/json",
    }


# Environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """
    Set up test environment variables.

    This runs once per test session.
    """
    # Set test environment variables
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL

    yield

    # Cleanup after all tests
    pass


# Marker configurations
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
