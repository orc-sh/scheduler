"""
URL model for storing webhook-like URL endpoints.
"""

import secrets

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Index, String
from sqlalchemy.sql import func

from .base import Base


class Url(Base):
    __tablename__ = "urls"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    unique_identifier = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        Index("idx_urls_project_id", "project_id"),
        Index("idx_urls_unique_identifier", "unique_identifier"),
    )

    @staticmethod
    def generate_unique_identifier() -> str:
        """
        Generate a unique identifier for the URL.
        Uses URL-safe base64 encoding for a secure random string.

        Returns:
            A unique identifier string
        """
        return secrets.token_urlsafe(32)
