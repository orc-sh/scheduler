from sqlalchemy import JSON, TIMESTAMP, BigInteger, Boolean, Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class WebhookResult(Base):
    __tablename__ = "webhook_results"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    webhook_id = Column(String(36), ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False)
    job_execution_id = Column(String(36), ForeignKey("job_executions.id", ondelete="CASCADE"), nullable=False)
    triggered_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    request_url = Column(String(1024), nullable=False)
    request_method = Column(String(10), nullable=False)
    request_headers = Column(JSON, nullable=True)
    request_body = Column(Text, nullable=True)  # Changed from LONGTEXT for SQLite compatibility
    response_status = Column(Integer, nullable=True)
    response_headers = Column(JSON, nullable=True)
    response_body = Column(Text, nullable=True)  # Changed from LONGTEXT for SQLite compatibility
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    is_success = Column(Boolean, nullable=False, server_default="0")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    __table_args__ = (
        Index("idx_webhook_results_webhook_id", "webhook_id"),
        Index("idx_webhook_results_job_execution_id", "job_execution_id"),
    )
