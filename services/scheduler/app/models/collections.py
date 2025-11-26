"""
Collection model for storing collections of webhooks for load testing.
"""

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Collection(Base):
    __tablename__ = "collections"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=True)  # Nullable for blank names
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    webhooks = relationship(
        "Webhook", foreign_keys="Webhook.collection_id", back_populates="collection", cascade="all, delete-orphan"
    )
    runs = relationship("LoadTestRun", back_populates="collection", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_collections_project_id", "project_id"),
        Index("idx_collections_created_at", "created_at"),
    )
