"""
Webhook service for managing CRUD operations on webhooks.
"""

import uuid
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.webhooks import Webhook


class WebhookService:
    """Service class for webhook-related operations"""

    def __init__(self, db: Session):
        """
        Initialize the webhook service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_webhook(
        self,
        job_id: Optional[str] = None,
        url: str = "",
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        body_template: Optional[str] = None,
        content_type: str = "application/json",
    ) -> Webhook:
        """
        Create a new webhook.

        Args:
            job_id: ID of the job this webhook belongs to (optional)
            url: URL to send the webhook to
            method: HTTP method (default: POST)
            headers: HTTP headers to include (optional)
            query_params: Query parameters to include (optional)
            body_template: Template for the request body (optional)
            content_type: Content type of the request (default: application/json)

        Returns:
            Created Webhook instance
        """
        webhook = Webhook(
            id=str(uuid.uuid4()),
            job_id=job_id,
            url=url,
            method=method,
            headers=headers,
            query_params=query_params,
            body_template=body_template,
            content_type=content_type,
        )
        self.db.add(webhook)
        self.db.commit()
        self.db.refresh(webhook)
        return webhook

    def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """
        Get a specific webhook by ID.

        Args:
            webhook_id: ID of the webhook to retrieve

        Returns:
            Webhook instance if found, None otherwise
        """
        return self.db.query(Webhook).filter(Webhook.id == webhook_id).first()

    def get_webhooks_by_job(self, job_id: str) -> List[Webhook]:
        """
        Get all webhooks for a job.

        Args:
            job_id: ID of the job

        Returns:
            List of Webhook instances
        """
        return self.db.query(Webhook).filter(Webhook.job_id == job_id).all()

    def get_all_webhooks(self, limit: Optional[int] = None, offset: int = 0) -> List[Webhook]:
        """
        Get all webhooks with optional pagination.

        Args:
            limit: Maximum number of webhooks to return (optional)
            offset: Number of webhooks to skip (default: 0)

        Returns:
            List of Webhook instances
        """
        query = self.db.query(Webhook)
        if limit is not None:
            query = query.limit(limit)
        if offset > 0:
            query = query.offset(offset)
        return query.all()

    def update_webhook(
        self,
        webhook_id: str,
        url: Optional[str] = None,
        method: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        body_template: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Optional[Webhook]:
        """
        Update a webhook's properties.

        Args:
            webhook_id: ID of the webhook to update
            url: New URL (optional)
            method: New HTTP method (optional)
            headers: New headers (optional)
            query_params: New query parameters (optional)
            body_template: New body template (optional)
            content_type: New content type (optional)

        Returns:
            Updated Webhook instance if found, None otherwise
        """
        webhook = self.get_webhook(webhook_id)
        if not webhook:
            return None

        # Update fields if provided
        if url is not None:
            webhook.url = url  # type: ignore[assignment]
        if method is not None:
            webhook.method = method  # type: ignore[assignment]
        if headers is not None:
            webhook.headers = headers  # type: ignore[assignment]
        if query_params is not None:
            webhook.query_params = query_params  # type: ignore[assignment]
        if body_template is not None:
            webhook.body_template = body_template  # type: ignore[assignment]
        if content_type is not None:
            webhook.content_type = content_type  # type: ignore[assignment]

        self.db.commit()
        self.db.refresh(webhook)
        return webhook

    def delete_webhook(self, webhook_id: str) -> bool:
        """
        Delete a webhook.

        Args:
            webhook_id: ID of the webhook to delete

        Returns:
            True if webhook was deleted, False if not found
        """
        webhook = self.get_webhook(webhook_id)
        if not webhook:
            return False

        self.db.delete(webhook)
        self.db.commit()
        return True


def get_webhook_service(db: Session) -> WebhookService:
    """
    Factory function to create a WebhookService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        WebhookService instance
    """
    return WebhookService(db)
