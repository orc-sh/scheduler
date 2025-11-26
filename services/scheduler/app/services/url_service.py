"""
URL service for managing CRUD operations on URLs and URL logs.
"""

import uuid
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.url_logs import UrlLog
from app.models.urls import Url


class UrlService:
    """Service class for URL-related operations"""

    def __init__(self, db: Session):
        """
        Initialize the URL service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_url(self, project_id: str) -> Url:
        """
        Create a new URL for a project.

        Args:
            project_id: ID of the project this URL belongs to

        Returns:
            Created Url instance
        """
        url = Url(
            id=str(uuid.uuid4()),
            project_id=project_id,
            unique_identifier=Url.generate_unique_identifier(),
        )
        self.db.add(url)
        self.db.commit()
        self.db.refresh(url)
        return url

    def get_url(self, url_id: str) -> Optional[Url]:
        """
        Get a specific URL by ID.

        Args:
            url_id: ID of the URL to retrieve

        Returns:
            Url instance if found, None otherwise
        """
        return self.db.query(Url).filter(Url.id == url_id).first()

    def get_url_by_identifier(self, unique_identifier: str) -> Optional[Url]:
        """
        Get a URL by its unique identifier.

        Args:
            unique_identifier: Unique identifier of the URL

        Returns:
            Url instance if found, None otherwise
        """
        return self.db.query(Url).filter(Url.unique_identifier == unique_identifier).first()

    def get_urls_by_project(self, project_id: str) -> List[Url]:
        """
        Get all URLs for a project.

        Args:
            project_id: ID of the project

        Returns:
            List of Url instances
        """
        return self.db.query(Url).filter(Url.project_id == project_id).all()

    def get_all_urls(self, limit: Optional[int] = None, offset: int = 0) -> List[Url]:
        """
        Get all URLs with optional pagination.

        Args:
            limit: Maximum number of URLs to return (optional)
            offset: Number of URLs to skip (default: 0)

        Returns:
            List of Url instances
        """
        query = self.db.query(Url)
        if limit is not None:
            query = query.limit(limit)
        if offset > 0:
            query = query.offset(offset)
        return query.all()

    def update_url(self, url_id: str, project_id: Optional[str] = None) -> Optional[Url]:
        """
        Update a URL's properties.

        Args:
            url_id: ID of the URL to update
            project_id: New project ID (optional)

        Returns:
            Updated Url instance if found, None otherwise
        """
        url = self.get_url(url_id)
        if not url:
            return None

        if project_id is not None:
            url.project_id = project_id  # type: ignore[assignment]

        self.db.commit()
        self.db.refresh(url)
        return url

    def delete_url(self, url_id: str) -> bool:
        """
        Delete a URL.

        Args:
            url_id: ID of the URL to delete

        Returns:
            True if URL was deleted, False if not found
        """
        url = self.get_url(url_id)
        if not url:
            return False

        self.db.delete(url)
        self.db.commit()
        return True

    def create_url_log(
        self,
        url_id: str,
        method: str,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        response_status: Optional[int] = None,
        response_headers: Optional[Dict[str, str]] = None,
        response_body: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UrlLog:
        """
        Create a new URL log entry.

        Args:
            url_id: ID of the URL this log belongs to
            method: HTTP method
            headers: Request headers (optional)
            query_params: Query parameters (optional)
            body: Request body (optional)
            response_status: Response status code (optional)
            response_headers: Response headers (optional)
            response_body: Response body (optional)
            ip_address: IP address of the requester (optional)
            user_agent: User agent of the requester (optional)

        Returns:
            Created UrlLog instance
        """
        url_log = UrlLog(
            id=str(uuid.uuid4()),
            url_id=url_id,
            method=method,
            headers=headers,
            query_params=query_params,
            body=body,
            response_status=response_status,
            response_headers=response_headers,
            response_body=response_body,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(url_log)
        self.db.commit()
        self.db.refresh(url_log)
        return url_log

    def get_url_logs(
        self, url_id: str, limit: Optional[int] = None, offset: int = 0, order_by_desc: bool = True
    ) -> List[UrlLog]:
        """
        Get all logs for a URL.

        Args:
            url_id: ID of the URL
            limit: Maximum number of logs to return (optional)
            offset: Number of logs to skip (default: 0)
            order_by_desc: Order by created_at descending (default: True)

        Returns:
            List of UrlLog instances
        """
        query = self.db.query(UrlLog).filter(UrlLog.url_id == url_id)
        if order_by_desc:
            query = query.order_by(UrlLog.created_at.desc())
        else:
            query = query.order_by(UrlLog.created_at.asc())
        if limit is not None:
            query = query.limit(limit)
        if offset > 0:
            query = query.offset(offset)
        return query.all()

    def get_url_log(self, log_id: str) -> Optional[UrlLog]:
        """
        Get a specific URL log by ID.

        Args:
            log_id: ID of the log to retrieve

        Returns:
            UrlLog instance if found, None otherwise
        """
        return self.db.query(UrlLog).filter(UrlLog.id == log_id).first()

    def count_url_logs(self, url_id: str) -> int:
        """
        Count the total number of logs for a URL.

        Args:
            url_id: ID of the URL

        Returns:
            Total count of logs
        """
        return self.db.query(UrlLog).filter(UrlLog.url_id == url_id).count()


def get_url_service(db: Session) -> "UrlService":
    """
    Factory function to create a UrlService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        UrlService instance
    """
    return UrlService(db)
