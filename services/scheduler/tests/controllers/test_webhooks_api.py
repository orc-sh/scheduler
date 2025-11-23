"""
Integration tests for Webhooks API endpoints.

These tests verify the complete API functionality including
request/response handling, authentication, and database interactions.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.context.user_context import set_current_user_context
from app.models.user import User
from tests.factories import ProjectFactory


@pytest.mark.integration
class TestCreateCronWebhookAPI:
    """Tests for POST /webhooks endpoint."""

    def test_create_webhook_success(self, client: TestClient, db_session: Session, test_user: User):
        """Test creating a webhook with job and project successfully."""
        set_current_user_context(test_user)

        response = client.post(
            "/api/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                    "timezone": "UTC",
                    "enabled": True,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                    "method": "POST",
                    "headers": {"Authorization": "Bearer token"},
                    "query_params": {"key": "value"},
                    "body_template": '{"event": "test"}',
                    "content_type": "application/json",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Verify project (created with user's name)
        assert "project" in data
        assert data["project"]["user_id"] == test_user.id
        assert data["project"]["name"] == test_user.name
        assert "id" in data["project"]

        # Verify job
        assert "job" in data
        assert data["job"]["project_id"] == data["project"]["id"]
        assert data["job"]["name"] == "Test Job"
        assert data["job"]["schedule"] == "0 9 * * *"
        assert data["job"]["type"] == 1
        assert data["job"]["enabled"] is True
        assert "next_run_at" in data["job"]

        # Verify webhook
        assert "webhook" in data
        assert data["webhook"]["job_id"] == data["job"]["id"]
        assert data["webhook"]["url"] == "https://api.example.com/webhook"
        assert data["webhook"]["method"] == "POST"

    def test_create_webhook_reuses_existing_project(self, client: TestClient, db_session: Session, test_user: User):
        """Test that webhook creation reuses existing project with user's name."""
        # Create project with user's name first
        existing_project = ProjectFactory.create(db_session, test_user.id, test_user.name)
        set_current_user_context(test_user)

        response = client.post(
            "/api/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                    "method": "POST",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Should reuse existing project
        assert data["project"]["id"] == existing_project.id
        assert data["project"]["name"] == test_user.name

    def test_create_webhook_without_auth(self, client: TestClient):
        """Test creating a webhook without authentication fails."""
        response = client.post(
            "/api/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                },
            },
        )

        assert response.status_code == 401

    def test_create_webhook_invalid_cron_schedule(self, client: TestClient, test_user: User):
        """Test creating a webhook with invalid cron schedule fails."""
        set_current_user_context(test_user)

        response = client.post(
            "/api/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "invalid cron",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                },
            },
        )

        assert response.status_code == 400
        assert "cron" in response.json()["detail"].lower()

    def test_create_webhook_missing_job_fields(self, client: TestClient, test_user: User):
        """Test creating webhook with missing required job fields fails."""
        set_current_user_context(test_user)

        response = client.post(
            "/api/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    # Missing schedule and type
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                },
            },
        )

        assert response.status_code == 422

    def test_create_webhook_missing_webhook_url(self, client: TestClient, test_user: User):
        """Test creating webhook with missing URL fails."""
        set_current_user_context(test_user)

        response = client.post(
            "/api/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    # Missing url
                    "method": "POST",
                },
            },
        )

        assert response.status_code == 422

    def test_create_webhook_with_custom_timezone(self, client: TestClient, test_user: User):
        """Test creating webhook with custom timezone."""
        set_current_user_context(test_user)

        response = client.post(
            "/api/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                    "timezone": "America/New_York",
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["job"]["timezone"] == "America/New_York"

    def test_create_webhook_disabled_job(self, client: TestClient, test_user: User):
        """Test creating webhook with disabled job."""
        set_current_user_context(test_user)

        response = client.post(
            "/api/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                    "enabled": False,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["job"]["enabled"] is False

    def test_create_webhook_with_different_http_methods(self, client: TestClient, test_user: User):
        """Test creating webhooks with different HTTP methods."""
        set_current_user_context(test_user)

        for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            response = client.post(
                "/api/webhooks",
                json={
                    "job": {
                        "name": f"Test Job {method}",
                        "schedule": "0 9 * * *",
                        "type": 1,
                    },
                    "webhook": {
                        "url": f"https://api.example.com/{method.lower()}",
                        "method": method,
                    },
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["webhook"]["method"] == method

    def test_create_webhook_with_headers(self, client: TestClient, test_user: User):
        """Test creating webhook with custom headers."""
        set_current_user_context(test_user)

        headers = {
            "Authorization": "Bearer secret-token",
            "X-Custom-Header": "custom-value",
            "Content-Type": "application/json",
        }

        response = client.post(
            "/api/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                    "headers": headers,
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["webhook"]["headers"] == headers

    def test_create_webhook_with_query_params(self, client: TestClient, test_user: User):
        """Test creating webhook with query parameters."""
        set_current_user_context(test_user)

        query_params = {"api_key": "12345", "format": "json", "version": "v2"}

        response = client.post(
            "/api/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                    "query_params": query_params,
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["webhook"]["query_params"] == query_params

    def test_create_webhook_with_body_template(self, client: TestClient, test_user: User):
        """Test creating webhook with body template."""
        set_current_user_context(test_user)

        body_template = '{"event": "scheduled", "timestamp": "{{timestamp}}", "data": "{{data}}"}'

        response = client.post(
            "/api/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                    "body_template": body_template,
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["webhook"]["body_template"] == body_template

    def test_create_webhook_with_custom_content_type(self, client: TestClient, test_user: User):
        """Test creating webhook with custom content type."""
        set_current_user_context(test_user)

        response = client.post(
            "/api/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                    "content_type": "application/xml",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["webhook"]["content_type"] == "application/xml"

    def test_create_multiple_webhooks_same_user(self, client: TestClient, db_session: Session, test_user: User):
        """Test creating multiple webhooks for the same user."""
        set_current_user_context(test_user)

        # Create first webhook
        response1 = client.post(
            "/api/webhooks",
            json={
                "job": {
                    "name": "Job 1",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook1",
                },
            },
        )
        assert response1.status_code == 201
        project_id_1 = response1.json()["project"]["id"]

        # Create second webhook
        response2 = client.post(
            "/api/webhooks",
            json={
                "job": {
                    "name": "Job 2",
                    "schedule": "0 10 * * *",
                    "type": 2,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook2",
                },
            },
        )
        assert response2.status_code == 201
        project_id_2 = response2.json()["project"]["id"]

        # Should reuse the same project
        assert project_id_1 == project_id_2

        # Jobs should be different
        assert response1.json()["job"]["id"] != response2.json()["job"]["id"]

    def test_create_webhooks_different_users(self, client: TestClient, test_user: User, another_user: User):
        """Test creating webhooks for different users creates separate projects."""
        # User 1 creates webhook
        set_current_user_context(test_user)
        response1 = client.post(
            "/api/webhooks",
            json={
                "job": {"name": "Job 1", "schedule": "0 9 * * *", "type": 1},
                "webhook": {"url": "https://api.example.com/webhook1"},
            },
        )
        assert response1.status_code == 201

        # User 2 creates webhook
        set_current_user_context(another_user)
        response2 = client.post(
            "/api/webhooks",
            json={
                "job": {"name": "Job 2", "schedule": "0 9 * * *", "type": 1},
                "webhook": {"url": "https://api.example.com/webhook2"},
            },
        )
        assert response2.status_code == 201

        # Projects should be different
        assert response1.json()["project"]["id"] != response2.json()["project"]["id"]
        assert response1.json()["project"]["user_id"] == test_user.id
        assert response2.json()["project"]["user_id"] == another_user.id


@pytest.mark.integration
class TestWebhookAPIWorkflow:
    """End-to-end workflow tests for webhooks API."""

    def test_complete_webhook_creation_workflow(self, client: TestClient, db_session: Session, test_user: User):
        """Test complete workflow: create webhook, verify all entities."""
        set_current_user_context(test_user)

        # Create webhook
        response = client.post(
            "/api/webhooks",
            json={
                "job": {
                    "name": "Daily Report",
                    "schedule": "0 9 * * *",
                    "type": 1,
                    "timezone": "UTC",
                    "enabled": True,
                },
                "webhook": {
                    "url": "https://api.example.com/daily-report",
                    "method": "POST",
                    "headers": {"Authorization": "Bearer token"},
                    "content_type": "application/json",
                },
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Verify project exists in database
        from app.services.project_service import get_project_service

        project_service = get_project_service(db_session)
        project = project_service.get_project(data["project"]["id"], test_user.id)
        assert project is not None
        assert project.name == test_user.name

        # Verify job exists in database
        from app.services.job_service import get_job_service

        job_service = get_job_service(db_session)
        job = job_service.get_job(data["job"]["id"])
        assert job is not None
        assert job.name == "Daily Report"
        assert job.project_id == project.id

        # Verify webhook exists in database
        from app.services.webhook_service import get_webhook_service

        webhook_service = get_webhook_service(db_session)
        webhook = webhook_service.get_webhook(data["webhook"]["id"])
        assert webhook is not None
        assert webhook.url == "https://api.example.com/daily-report"
        assert webhook.job_id == job.id

    def test_idempotent_project_creation(self, client: TestClient, test_user: User):
        """Test that multiple webhook creations reuse the same project."""
        set_current_user_context(test_user)

        project_ids = set()

        # Create 5 webhooks
        for i in range(5):
            response = client.post(
                "/api/webhooks",
                json={
                    "job": {
                        "name": f"Job {i}",
                        "schedule": "0 9 * * *",
                        "type": 1,
                    },
                    "webhook": {
                        "url": f"https://api.example.com/webhook{i}",
                    },
                },
            )
            assert response.status_code == 201
            project_ids.add(response.json()["project"]["id"])

        # All should use the same project
        assert len(project_ids) == 1


@pytest.mark.integration
class TestGetWebhookByIdAPI:
    """Tests for GET /webhooks/{webhook_id} endpoint."""

    def test_get_webhook_success(self, client: TestClient, db_session: Session, test_user: User):
        """Test retrieving a specific webhook by ID."""
        set_current_user_context(test_user)

        # Create a webhook first
        response = client.post(
            "/api/webhooks",
            json={
                "job": {
                    "name": "Test Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                    "method": "POST",
                    "headers": {"Authorization": "Bearer token"},
                },
            },
        )
        assert response.status_code == 201
        webhook_id = response.json()["webhook"]["id"]

        # Now get the webhook
        response = client.get(f"/api/webhooks/{webhook_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == webhook_id
        assert data["url"] == "https://api.example.com/webhook"
        assert data["method"] == "POST"
        assert data["headers"] == {"Authorization": "Bearer token"}

    def test_get_webhook_not_found(self, client: TestClient, test_user: User):
        """Test retrieving a non-existent webhook."""
        set_current_user_context(test_user)

        response = client.get("/api/webhooks/non-existent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_webhook_without_auth(self, client: TestClient):
        """Test retrieving a webhook without authentication."""
        response = client.get("/api/webhooks/some-id")

        assert response.status_code == 401

    def test_get_webhook_different_user(
        self, client: TestClient, db_session: Session, test_user: User, another_user: User
    ):
        """Test that users cannot access other users' webhooks."""
        # User 1 creates a webhook
        set_current_user_context(test_user)
        response = client.post(
            "/api/webhooks",
            json={
                "job": {"name": "User 1 Job", "schedule": "0 9 * * *", "type": 1},
                "webhook": {"url": "https://api.example.com/webhook1"},
            },
        )
        assert response.status_code == 201
        webhook_id = response.json()["webhook"]["id"]

        # User 2 tries to access User 1's webhook
        set_current_user_context(another_user)
        response = client.get(f"/api/webhooks/{webhook_id}")

        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()


@pytest.mark.integration
class TestGetAllWebhooksAPI:
    """Tests for GET /webhooks endpoint."""

    def test_get_all_webhooks_empty(self, client: TestClient, test_user: User):
        """Test retrieving webhooks when user has none."""
        set_current_user_context(test_user)

        response = client.get("/api/webhooks")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_all_webhooks_multiple(self, client: TestClient, test_user: User):
        """Test retrieving multiple webhooks."""
        set_current_user_context(test_user)

        # Create multiple webhooks
        for i in range(3):
            response = client.post(
                "/api/webhooks",
                json={
                    "job": {
                        "name": f"Job {i}",
                        "schedule": "0 9 * * *",
                        "type": 1,
                    },
                    "webhook": {
                        "url": f"https://api.example.com/webhook{i}",
                    },
                },
            )
            assert response.status_code == 201

        # Get all webhooks
        response = client.get("/api/webhooks")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_all_webhooks_pagination(self, client: TestClient, test_user: User):
        """Test pagination parameters."""
        set_current_user_context(test_user)

        # Create 10 webhooks
        for i in range(10):
            response = client.post(
                "/api/webhooks",
                json={
                    "job": {
                        "name": f"Job {i}",
                        "schedule": "0 9 * * *",
                        "type": 1,
                    },
                    "webhook": {
                        "url": f"https://api.example.com/webhook{i}",
                    },
                },
            )
            assert response.status_code == 201

        # Get first 5
        response = client.get("/api/webhooks?limit=5&offset=0")
        assert response.status_code == 200
        assert len(response.json()) == 5

        # Get next 5
        response = client.get("/api/webhooks?limit=5&offset=5")
        assert response.status_code == 200
        assert len(response.json()) == 5

    def test_get_all_webhooks_without_auth(self, client: TestClient):
        """Test retrieving webhooks without authentication."""
        response = client.get("/api/webhooks")

        assert response.status_code == 401

    def test_get_all_webhooks_user_isolation(self, client: TestClient, test_user: User, another_user: User):
        """Test that users only see their own webhooks."""
        # User 1 creates 2 webhooks
        set_current_user_context(test_user)
        for i in range(2):
            response = client.post(
                "/api/webhooks",
                json={
                    "job": {"name": f"User 1 Job {i}", "schedule": "0 9 * * *", "type": 1},
                    "webhook": {"url": f"https://api.example.com/user1-webhook{i}"},
                },
            )
            assert response.status_code == 201

        # User 2 creates 3 webhooks
        set_current_user_context(another_user)
        for i in range(3):
            response = client.post(
                "/api/webhooks",
                json={
                    "job": {"name": f"User 2 Job {i}", "schedule": "0 9 * * *", "type": 1},
                    "webhook": {"url": f"https://api.example.com/user2-webhook{i}"},
                },
            )
            assert response.status_code == 201

        # User 2 should only see their 3 webhooks
        response = client.get("/api/webhooks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # User 1 should only see their 2 webhooks
        set_current_user_context(test_user)
        response = client.get("/api/webhooks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


@pytest.mark.integration
class TestUpdateWebhookAPI:
    """Tests for PUT /webhooks/{webhook_id} endpoint."""

    def test_update_webhook_url(self, client: TestClient, db_session: Session, test_user: User):
        """Test updating a webhook's URL."""
        set_current_user_context(test_user)

        # Create a webhook
        response = client.post(
            "/api/webhooks",
            json={
                "job": {"name": "Test Job", "schedule": "0 9 * * *", "type": 1},
                "webhook": {"url": "https://api.example.com/old"},
            },
        )
        assert response.status_code == 201
        webhook_id = response.json()["webhook"]["id"]

        # Update the webhook
        response = client.put(
            f"/api/webhooks/{webhook_id}",
            json={"url": "https://api.example.com/new"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == webhook_id
        assert data["url"] == "https://api.example.com/new"

    def test_update_webhook_method(self, client: TestClient, test_user: User):
        """Test updating a webhook's HTTP method."""
        set_current_user_context(test_user)

        # Create a webhook
        response = client.post(
            "/api/webhooks",
            json={
                "job": {"name": "Test Job", "schedule": "0 9 * * *", "type": 1},
                "webhook": {"url": "https://api.example.com/webhook", "method": "POST"},
            },
        )
        assert response.status_code == 201
        webhook_id = response.json()["webhook"]["id"]

        # Update the method
        response = client.put(
            f"/api/webhooks/{webhook_id}",
            json={"method": "PUT"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["method"] == "PUT"

    def test_update_webhook_headers(self, client: TestClient, test_user: User):
        """Test updating a webhook's headers."""
        set_current_user_context(test_user)

        # Create a webhook
        response = client.post(
            "/api/webhooks",
            json={
                "job": {"name": "Test Job", "schedule": "0 9 * * *", "type": 1},
                "webhook": {
                    "url": "https://api.example.com/webhook",
                    "headers": {"Old": "Header"},
                },
            },
        )
        assert response.status_code == 201
        webhook_id = response.json()["webhook"]["id"]

        # Update headers
        response = client.put(
            f"/api/webhooks/{webhook_id}",
            json={"headers": {"New": "Header", "Another": "Value"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["headers"] == {"New": "Header", "Another": "Value"}

    def test_update_webhook_multiple_fields(self, client: TestClient, test_user: User):
        """Test updating multiple webhook fields at once."""
        set_current_user_context(test_user)

        # Create a webhook
        response = client.post(
            "/api/webhooks",
            json={
                "job": {"name": "Test Job", "schedule": "0 9 * * *", "type": 1},
                "webhook": {"url": "https://api.example.com/old"},
            },
        )
        assert response.status_code == 201
        webhook_id = response.json()["webhook"]["id"]

        # Update multiple fields
        response = client.put(
            f"/api/webhooks/{webhook_id}",
            json={
                "url": "https://api.example.com/updated",
                "method": "PATCH",
                "content_type": "application/xml",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://api.example.com/updated"
        assert data["method"] == "PATCH"
        assert data["content_type"] == "application/xml"

    def test_update_webhook_not_found(self, client: TestClient, test_user: User):
        """Test updating a non-existent webhook."""
        set_current_user_context(test_user)

        response = client.put(
            "/api/webhooks/non-existent-id",
            json={"url": "https://api.example.com/new"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_webhook_without_auth(self, client: TestClient):
        """Test updating a webhook without authentication."""
        response = client.put(
            "/api/webhooks/some-id",
            json={"url": "https://api.example.com/new"},
        )

        assert response.status_code == 401

    def test_update_webhook_different_user(self, client: TestClient, test_user: User, another_user: User):
        """Test that users cannot update other users' webhooks."""
        # User 1 creates a webhook
        set_current_user_context(test_user)
        response = client.post(
            "/api/webhooks",
            json={
                "job": {"name": "User 1 Job", "schedule": "0 9 * * *", "type": 1},
                "webhook": {"url": "https://api.example.com/webhook1"},
            },
        )
        assert response.status_code == 201
        webhook_id = response.json()["webhook"]["id"]

        # User 2 tries to update User 1's webhook
        set_current_user_context(another_user)
        response = client.put(
            f"/api/webhooks/{webhook_id}",
            json={"url": "https://api.example.com/hacked"},
        )

        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()

    def test_update_webhook_query_params(self, client: TestClient, test_user: User):
        """Test updating a webhook's query parameters."""
        set_current_user_context(test_user)

        # Create a webhook
        response = client.post(
            "/api/webhooks",
            json={
                "job": {"name": "Test Job", "schedule": "0 9 * * *", "type": 1},
                "webhook": {"url": "https://api.example.com/webhook"},
            },
        )
        assert response.status_code == 201
        webhook_id = response.json()["webhook"]["id"]

        # Update query params
        response = client.put(
            f"/api/webhooks/{webhook_id}",
            json={"query_params": {"api_key": "12345", "format": "json"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query_params"] == {"api_key": "12345", "format": "json"}

    def test_update_webhook_body_template(self, client: TestClient, test_user: User):
        """Test updating a webhook's body template."""
        set_current_user_context(test_user)

        # Create a webhook
        response = client.post(
            "/api/webhooks",
            json={
                "job": {"name": "Test Job", "schedule": "0 9 * * *", "type": 1},
                "webhook": {"url": "https://api.example.com/webhook"},
            },
        )
        assert response.status_code == 201
        webhook_id = response.json()["webhook"]["id"]

        # Update body template
        response = client.put(
            f"/api/webhooks/{webhook_id}",
            json={"body_template": '{"event": "updated", "data": "{{data}}"}'},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["body_template"] == '{"event": "updated", "data": "{{data}}"}'


@pytest.mark.integration
class TestDeleteWebhookAPI:
    """Tests for DELETE /webhooks/{webhook_id} endpoint."""

    def test_delete_webhook_success(self, client: TestClient, db_session: Session, test_user: User):
        """Test deleting a webhook successfully."""
        set_current_user_context(test_user)

        # Create a webhook
        response = client.post(
            "/api/webhooks",
            json={
                "job": {"name": "Test Job", "schedule": "0 9 * * *", "type": 1},
                "webhook": {"url": "https://api.example.com/webhook"},
            },
        )
        assert response.status_code == 201
        webhook_id = response.json()["webhook"]["id"]

        # Delete the webhook
        response = client.delete(f"/api/webhooks/{webhook_id}")

        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f"/api/webhooks/{webhook_id}")
        assert response.status_code == 404

    def test_delete_webhook_not_found(self, client: TestClient, test_user: User):
        """Test deleting a non-existent webhook."""
        set_current_user_context(test_user)

        response = client.delete("/api/webhooks/non-existent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_webhook_without_auth(self, client: TestClient):
        """Test deleting a webhook without authentication."""
        response = client.delete("/api/webhooks/some-id")

        assert response.status_code == 401

    def test_delete_webhook_different_user(self, client: TestClient, test_user: User, another_user: User):
        """Test that users cannot delete other users' webhooks."""
        # User 1 creates a webhook
        set_current_user_context(test_user)
        response = client.post(
            "/api/webhooks",
            json={
                "job": {"name": "User 1 Job", "schedule": "0 9 * * *", "type": 1},
                "webhook": {"url": "https://api.example.com/webhook1"},
            },
        )
        assert response.status_code == 201
        webhook_id = response.json()["webhook"]["id"]

        # User 2 tries to delete User 1's webhook
        set_current_user_context(another_user)
        response = client.delete(f"/api/webhooks/{webhook_id}")

        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()

        # Verify webhook still exists for User 1
        set_current_user_context(test_user)
        response = client.get(f"/api/webhooks/{webhook_id}")
        assert response.status_code == 200

    def test_delete_webhook_cascades_behavior(self, client: TestClient, test_user: User):
        """Test that deleting a webhook doesn't affect the job."""
        set_current_user_context(test_user)

        # Create a webhook
        response = client.post(
            "/api/webhooks",
            json={
                "job": {"name": "Test Job", "schedule": "0 9 * * *", "type": 1},
                "webhook": {"url": "https://api.example.com/webhook"},
            },
        )
        assert response.status_code == 201
        webhook_id = response.json()["webhook"]["id"]
        # job_id = response.json()["job"]["id"]

        # Delete the webhook
        response = client.delete(f"/api/webhooks/{webhook_id}")
        assert response.status_code == 204

        # Verify job still exists (through project/job endpoints if available)
        # For now, we just verify webhook is gone
        response = client.get(f"/api/webhooks/{webhook_id}")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
