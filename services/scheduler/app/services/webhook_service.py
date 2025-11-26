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
        collection_id: Optional[str] = None,
        url: str = "",
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        body_template: Optional[str] = None,
        content_type: str = "application/json",
        order: Optional[int] = None,
    ) -> Webhook:
        """
        Create a new webhook.

        Args:
            job_id: ID of the job this webhook belongs to (optional)
            collection_id: ID of the collection (optional)
            url: URL to send the webhook to
            method: HTTP method (default: POST)
            headers: HTTP headers to include (optional)
            query_params: Query parameters to include (optional)
            body_template: Template for the request body (optional)
            content_type: Content type of the request (default: application/json)
            order: Execution order for load test webhooks (optional)

        Returns:
            Created Webhook instance
        """
        # If order is not provided and this is for a collection, set it to the next available order
        if collection_id and order is None:
            max_order = (
                self.db.query(Webhook)
                .filter(Webhook.collection_id == collection_id)
                .order_by(Webhook.order.desc())
                .first()
            )
            order = (max_order.order + 1) if max_order and max_order.order is not None else 0

        webhook = Webhook(
            id=str(uuid.uuid4()),
            job_id=job_id,
            collection_id=collection_id,
            url=url,
            method=method,
            headers=headers,
            query_params=query_params,
            body_template=body_template,
            content_type=content_type,
            order=order,
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

    def get_webhooks_by_collection(self, collection_id: str) -> List[Webhook]:
        """
        Get all webhooks for a collection, ordered by execution order.

        Args:
            collection_id: ID of the collection

        Returns:
            List of Webhook instances ordered by execution order
        """
        return (
            self.db.query(Webhook)
            .filter(Webhook.collection_id == collection_id)
            .order_by(Webhook.order.asc().nulls_last())
            .all()
        )

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
        order: Optional[int] = None,
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
            order: New execution order (optional)

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
        if order is not None:
            webhook.order = order  # type: ignore[assignment]

        self.db.commit()
        self.db.refresh(webhook)
        return webhook

    def reorder_webhooks(self, collection_id: str, webhook_ids: List[str]) -> bool:
        """
        Reorder webhooks for a collection.

        Args:
            collection_id: ID of the collection
            webhook_ids: List of webhook IDs in desired order

        Returns:
            True if reordering was successful, False otherwise
        """
        # Verify all webhooks belong to the collection
        webhooks = (
            self.db.query(Webhook)
            .filter(
                Webhook.id.in_(webhook_ids),
                Webhook.collection_id == collection_id,
            )
            .all()
        )

        if len(webhooks) != len(webhook_ids):
            return False

        # Update order for each webhook
        for order, webhook_id in enumerate(webhook_ids):
            webhook = next((w for w in webhooks if w.id == webhook_id), None)
            if webhook:
                webhook.order = order  # type: ignore[assignment]

        self.db.commit()
        return True

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

    def create_webhook_for_collection(
        self,
        collection_id: str,
        url: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        body_template: Optional[str] = None,
        content_type: str = "application/json",
        order: Optional[int] = None,
    ) -> Webhook:
        """
        Convenience method to create a webhook for a collection.

        Args:
            collection_id: ID of the collection
            url: URL to send the webhook to
            method: HTTP method (default: POST)
            headers: HTTP headers to include (optional)
            query_params: Query parameters to include (optional)
            body_template: Template for the request body (optional)
            content_type: Content type of the request (default: application/json)
            order: Execution order (optional)

        Returns:
            Created Webhook instance
        """
        return self.create_webhook(
            collection_id=collection_id,
            url=url,
            method=method,
            headers=headers,
            query_params=query_params,
            body_template=body_template,
            content_type=content_type,
            order=order,
        )

    def update_webhook_for_collection(
        self,
        webhook_id: str,
        url: Optional[str] = None,
        method: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        body_template: Optional[str] = None,
        content_type: Optional[str] = None,
        order: Optional[int] = None,
    ) -> Optional[Webhook]:
        """
        Convenience method to update a webhook for a collection.

        Args:
            webhook_id: ID of the webhook to update
            url: New URL (optional)
            method: New HTTP method (optional)
            headers: New headers (optional)
            query_params: New query parameters (optional)
            body_template: New body template (optional)
            content_type: New content type (optional)
            order: New execution order (optional)

        Returns:
            Updated Webhook instance if found, None otherwise
        """
        return self.update_webhook(
            webhook_id=webhook_id,
            url=url,
            method=method,
            headers=headers,
            query_params=query_params,
            body_template=body_template,
            content_type=content_type,
            order=order,
        )

    def delete_webhook_for_collection(self, webhook_id: str) -> bool:
        """
        Convenience method to delete a webhook for a collection.

        Args:
            webhook_id: ID of the webhook to delete

        Returns:
            True if webhook was deleted, False if not found
        """
        return self.delete_webhook(webhook_id)

    def reorder_webhooks_for_collection(self, collection_id: str, webhook_ids: List[str]) -> bool:
        """
        Convenience method to reorder webhooks for a collection.

        Args:
            collection_id: ID of the collection
            webhook_ids: List of webhook IDs in desired order

        Returns:
            True if reordering was successful, False otherwise
        """
        return self.reorder_webhooks(collection_id, webhook_ids)


def get_webhook_service(db: Session) -> WebhookService:
    """
    Factory function to create a WebhookService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        WebhookService instance
    """
    return WebhookService(db)
