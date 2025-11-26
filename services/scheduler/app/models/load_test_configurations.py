"""
Load test collection model for storing collections of webhooks.
"""

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class LoadTestConfiguration(Base):
    __tablename__ = "load_test_configurations"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    webhooks = relationship(
        "Webhook",
        foreign_keys="Webhook.load_test_configuration_id",
        back_populates="load_test_configuration",
        cascade="all, delete-orphan",
    )
    runs = relationship("LoadTestRun", back_populates="configuration", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_load_test_configs_project_id", "project_id"),
        Index("idx_load_test_configs_created_at", "created_at"),
    )
