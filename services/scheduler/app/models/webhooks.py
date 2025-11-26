from sqlalchemy import JSON, TIMESTAMP, Column, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(String(36), primary_key=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True)  # Nullable for load tests
    collection_id = Column(
        String(36), ForeignKey("collections.id", ondelete="CASCADE"), nullable=True
    )  # Nullable for scheduled jobs
    url = Column(String(1024), nullable=False)
    method = Column(
        Enum("GET", "POST", "PUT", "PATCH", "DELETE", name="http_method_enum"), nullable=False, server_default="POST"
    )
    headers = Column(JSON, nullable=True)
    query_params = Column(JSON, nullable=True)
    body_template = Column(Text, nullable=True)
    content_type = Column(String(100), server_default="application/json")
    order = Column(Integer, nullable=True)  # Execution order for load test webhooks
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    collection = relationship("Collection", foreign_keys=[collection_id], back_populates="webhooks")

    __table_args__ = (
        Index("idx_webhooks_job_id", "job_id"),
        Index("idx_webhooks_collection_id", "collection_id"),
    )
