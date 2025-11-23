"""
Unit tests for WebhookService.

These tests verify the service layer logic for webhook CRUD operations
without making actual API requests.
"""

import pytest
from sqlalchemy.orm import Session

from app.services.webhook_service import WebhookService, get_webhook_service
from tests.factories import JobFactory, ProjectFactory, WebhookFactory


@pytest.mark.unit
class TestWebhookServiceCreate:
    """Tests for webhook creation."""

    def test_create_webhook_success(self, db_session: Session, test_user):
        """Test creating a webhook successfully."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        service = WebhookService(db_session)

        webhook = service.create_webhook(
            job_id=job.id,
            url="https://api.example.com/webhook",
            method="POST",
            headers={"Authorization": "Bearer token"},
            query_params={"key": "value"},
            body_template='{"event": "test"}',
            content_type="application/json",
        )

        assert webhook.id is not None
        assert webhook.job_id == job.id
        assert webhook.url == "https://api.example.com/webhook"
        assert webhook.method == "POST"
        assert webhook.headers == {"Authorization": "Bearer token"}
        assert webhook.query_params == {"key": "value"}
        assert webhook.body_template == '{"event": "test"}'
        assert webhook.content_type == "application/json"
        assert webhook.created_at is not None

    def test_create_webhook_generates_uuid(self, db_session: Session, test_user):
        """Test that webhook ID is auto-generated as UUID."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        service = WebhookService(db_session)

        webhook = service.create_webhook(
            job_id=job.id,
            url="https://api.example.com/webhook",
        )

        # Check UUID format
        assert len(webhook.id) == 36  # UUID format: 8-4-4-4-12
        assert webhook.id.count("-") == 4

    def test_create_webhook_minimal_fields(self, db_session: Session, test_user):
        """Test creating a webhook with minimal required fields."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        service = WebhookService(db_session)

        webhook = service.create_webhook(
            job_id=job.id,
            url="https://api.example.com/webhook",
        )

        assert webhook.id is not None
        assert webhook.job_id == job.id
        assert webhook.url == "https://api.example.com/webhook"
        assert webhook.method == "POST"  # Default
        assert webhook.content_type == "application/json"  # Default
        assert webhook.headers is None
        assert webhook.query_params is None
        assert webhook.body_template is None

    def test_create_webhook_with_headers(self, db_session: Session, test_user):
        """Test creating a webhook with custom headers."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        service = WebhookService(db_session)

        headers = {
            "Authorization": "Bearer token123",
            "X-Custom-Header": "custom-value",
        }
        webhook = service.create_webhook(
            job_id=job.id,
            url="https://api.example.com/webhook",
            headers=headers,
        )

        assert webhook.headers == headers

    def test_create_webhook_with_query_params(self, db_session: Session, test_user):
        """Test creating a webhook with query parameters."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        service = WebhookService(db_session)

        query_params = {"api_key": "12345", "format": "json"}
        webhook = service.create_webhook(
            job_id=job.id,
            url="https://api.example.com/webhook",
            query_params=query_params,
        )

        assert webhook.query_params == query_params

    def test_create_webhook_different_methods(self, db_session: Session, test_user):
        """Test creating webhooks with different HTTP methods."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        service = WebhookService(db_session)

        for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            webhook = service.create_webhook(
                job_id=job.id,
                url=f"https://api.example.com/{method.lower()}",
                method=method,
            )
            assert webhook.method == method


@pytest.mark.unit
class TestWebhookServiceGet:
    """Tests for retrieving webhooks."""

    def test_get_webhook_by_id_success(self, db_session: Session, test_user):
        """Test retrieving a specific webhook by ID."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        created_webhook = WebhookFactory.create(db_session, job.id, url="https://api.example.com/webhook")

        service = WebhookService(db_session)
        webhook = service.get_webhook(created_webhook.id)

        assert webhook is not None
        assert webhook.id == created_webhook.id
        assert webhook.url == "https://api.example.com/webhook"

    def test_get_webhook_not_found(self, db_session: Session):
        """Test retrieving a non-existent webhook returns None."""
        service = WebhookService(db_session)

        webhook = service.get_webhook("non-existent-id")

        assert webhook is None

    def test_get_webhooks_by_job_empty(self, db_session: Session, test_user):
        """Test retrieving webhooks when job has none."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        service = WebhookService(db_session)

        webhooks = service.get_webhooks_by_job(job.id)

        assert webhooks == []

    def test_get_webhooks_by_job_multiple(self, db_session: Session, test_user):
        """Test retrieving all webhooks for a job."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        WebhookFactory.create_batch(db_session, job.id, count=3)

        service = WebhookService(db_session)
        webhooks = service.get_webhooks_by_job(job.id)

        assert len(webhooks) == 3
        assert all(w.job_id == job.id for w in webhooks)

    def test_get_webhooks_by_job_filters_by_job(self, db_session: Session, test_user):
        """Test that get_webhooks_by_job only returns the specified job's webhooks."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job1 = JobFactory.create(db_session, project.id, "Job 1")
        job2 = JobFactory.create(db_session, project.id, "Job 2")

        WebhookFactory.create_batch(db_session, job1.id, count=2)
        WebhookFactory.create_batch(db_session, job2.id, count=3)

        service = WebhookService(db_session)
        webhooks = service.get_webhooks_by_job(job1.id)

        assert len(webhooks) == 2
        assert all(w.job_id == job1.id for w in webhooks)


@pytest.mark.unit
class TestWebhookServiceUpdate:
    """Tests for webhook updates."""

    def test_update_webhook_url(self, db_session: Session, test_user):
        """Test updating a webhook's URL."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        created_webhook = WebhookFactory.create(db_session, job.id, url="https://api.example.com/old")

        service = WebhookService(db_session)
        updated_webhook = service.update_webhook(created_webhook.id, url="https://api.example.com/new")

        assert updated_webhook is not None
        assert updated_webhook.id == created_webhook.id
        assert updated_webhook.url == "https://api.example.com/new"

    def test_update_webhook_method(self, db_session: Session, test_user):
        """Test updating a webhook's HTTP method."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        created_webhook = WebhookFactory.create(db_session, job.id, method="POST")

        service = WebhookService(db_session)
        updated_webhook = service.update_webhook(created_webhook.id, method="PUT")

        assert updated_webhook is not None
        assert updated_webhook.method == "PUT"

    def test_update_webhook_headers(self, db_session: Session, test_user):
        """Test updating a webhook's headers."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        created_webhook = WebhookFactory.create(db_session, job.id, headers={"Old": "Header"})

        new_headers = {"New": "Header", "Another": "Value"}
        service = WebhookService(db_session)
        updated_webhook = service.update_webhook(created_webhook.id, headers=new_headers)

        assert updated_webhook is not None
        assert updated_webhook.headers == new_headers

    def test_update_webhook_query_params(self, db_session: Session, test_user):
        """Test updating a webhook's query parameters."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        created_webhook = WebhookFactory.create(db_session, job.id, query_params={"old": "param"})

        new_params = {"new": "param", "another": "value"}
        service = WebhookService(db_session)
        updated_webhook = service.update_webhook(created_webhook.id, query_params=new_params)

        assert updated_webhook is not None
        assert updated_webhook.query_params == new_params

    def test_update_webhook_body_template(self, db_session: Session, test_user):
        """Test updating a webhook's body template."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        created_webhook = WebhookFactory.create(db_session, job.id, body_template='{"old": "template"}')

        service = WebhookService(db_session)
        updated_webhook = service.update_webhook(created_webhook.id, body_template='{"new": "template"}')

        assert updated_webhook is not None
        assert updated_webhook.body_template == '{"new": "template"}'

    def test_update_webhook_content_type(self, db_session: Session, test_user):
        """Test updating a webhook's content type."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        created_webhook = WebhookFactory.create(db_session, job.id, content_type="application/json")

        service = WebhookService(db_session)
        updated_webhook = service.update_webhook(created_webhook.id, content_type="application/xml")

        assert updated_webhook is not None
        assert updated_webhook.content_type == "application/xml"

    def test_update_webhook_multiple_fields(self, db_session: Session, test_user):
        """Test updating multiple webhook fields at once."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        created_webhook = WebhookFactory.create(db_session, job.id)

        service = WebhookService(db_session)
        updated_webhook = service.update_webhook(
            created_webhook.id,
            url="https://api.example.com/updated",
            method="PUT",
            content_type="application/xml",
        )

        assert updated_webhook is not None
        assert updated_webhook.url == "https://api.example.com/updated"
        assert updated_webhook.method == "PUT"
        assert updated_webhook.content_type == "application/xml"

    def test_update_webhook_not_found(self, db_session: Session):
        """Test updating a non-existent webhook returns None."""
        service = WebhookService(db_session)

        result = service.update_webhook("non-existent-id", url="https://new.url")

        assert result is None


@pytest.mark.unit
class TestWebhookServiceDelete:
    """Tests for webhook deletion."""

    def test_delete_webhook_success(self, db_session: Session, test_user):
        """Test deleting a webhook successfully."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        created_webhook = WebhookFactory.create(db_session, job.id)
        webhook_id = created_webhook.id

        service = WebhookService(db_session)
        result = service.delete_webhook(webhook_id)

        assert result is True

        # Verify it's gone
        deleted_webhook = service.get_webhook(webhook_id)
        assert deleted_webhook is None

    def test_delete_webhook_not_found(self, db_session: Session):
        """Test deleting a non-existent webhook returns False."""
        service = WebhookService(db_session)

        result = service.delete_webhook("non-existent-id")

        assert result is False


@pytest.mark.unit
class TestWebhookServiceGetAll:
    """Tests for get_all_webhooks method."""

    def test_get_all_webhooks_empty(self, db_session: Session):
        """Test retrieving webhooks when database is empty."""
        service = WebhookService(db_session)

        webhooks = service.get_all_webhooks()

        assert webhooks == []

    def test_get_all_webhooks_multiple(self, db_session: Session, test_user):
        """Test retrieving all webhooks without pagination."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        WebhookFactory.create_batch(db_session, job.id, count=5)

        service = WebhookService(db_session)
        webhooks = service.get_all_webhooks()

        assert len(webhooks) == 5

    def test_get_all_webhooks_with_limit(self, db_session: Session, test_user):
        """Test retrieving webhooks with limit."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        WebhookFactory.create_batch(db_session, job.id, count=10)

        service = WebhookService(db_session)
        webhooks = service.get_all_webhooks(limit=5)

        assert len(webhooks) == 5

    def test_get_all_webhooks_with_offset(self, db_session: Session, test_user):
        """Test retrieving webhooks with offset."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        created_webhooks = WebhookFactory.create_batch(db_session, job.id, count=10)

        service = WebhookService(db_session)
        webhooks = service.get_all_webhooks(offset=5)

        assert len(webhooks) == 5
        # Verify we got the last 5 webhooks
        webhook_ids = [w.id for w in webhooks]
        expected_ids = [w.id for w in created_webhooks[5:]]
        assert webhook_ids == expected_ids

    def test_get_all_webhooks_with_limit_and_offset(self, db_session: Session, test_user):
        """Test retrieving webhooks with both limit and offset."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job = JobFactory.create(db_session, project.id, "Test Job")
        WebhookFactory.create_batch(db_session, job.id, count=20)

        service = WebhookService(db_session)
        webhooks = service.get_all_webhooks(limit=5, offset=5)

        assert len(webhooks) == 5

    def test_get_all_webhooks_multiple_jobs(self, db_session: Session, test_user):
        """Test retrieving webhooks across multiple jobs."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        job1 = JobFactory.create(db_session, project.id, "Job 1")
        job2 = JobFactory.create(db_session, project.id, "Job 2")
        job3 = JobFactory.create(db_session, project.id, "Job 3")

        WebhookFactory.create_batch(db_session, job1.id, count=3)
        WebhookFactory.create_batch(db_session, job2.id, count=4)
        WebhookFactory.create_batch(db_session, job3.id, count=2)

        service = WebhookService(db_session)
        webhooks = service.get_all_webhooks()

        assert len(webhooks) == 9


@pytest.mark.unit
class TestWebhookServiceFactory:
    """Tests for the service factory function."""

    def test_get_webhook_service_returns_instance(self, db_session: Session):
        """Test that factory function returns WebhookService instance."""
        service = get_webhook_service(db_session)

        assert isinstance(service, WebhookService)
        assert service.db == db_session

    def test_get_webhook_service_creates_new_instances(self, db_session: Session):
        """Test that factory creates new instances each time."""
        service1 = get_webhook_service(db_session)
        service2 = get_webhook_service(db_session)

        # Should be different instances
        assert service1 is not service2
        # But should share the same db session
        assert service1.db is service2.db


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
