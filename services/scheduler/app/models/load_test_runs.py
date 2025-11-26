"""
Load test run model for storing individual load test execution instances.
"""

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class LoadTestRun(Base):
    __tablename__ = "load_test_runs"

    id = Column(String(36), primary_key=True)
    collection_id = Column(String(36), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False)

    # Test status
    status = Column(String(50), nullable=False, default="pending")  # pending, running, completed, failed, cancelled

    # Load test execution parameters
    concurrent_users = Column(Integer, nullable=False, default=10)
    duration_seconds = Column(Integer, nullable=False, default=60)
    requests_per_second = Column(Integer, nullable=True)  # Optional rate limiting

    # Timestamps
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    collection = relationship("Collection", back_populates="runs")
    reports = relationship("LoadTestReport", back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_load_test_runs_collection_id", "collection_id"),
        Index("idx_load_test_runs_status", "status"),
        Index("idx_load_test_runs_created_at", "created_at"),
    )
