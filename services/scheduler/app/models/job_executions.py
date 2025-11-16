from sqlalchemy import TIMESTAMP, Column, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class JobExecution(Base):
    __tablename__ = "job_executions"

    id = Column(String(36), primary_key=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum("pending", "success", "failure", name="execution_status_enum"), nullable=False)
    started_at = Column(TIMESTAMP, nullable=True)
    finished_at = Column(TIMESTAMP, nullable=True)
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)  # Changed from MEDIUMTEXT for SQLite compatibility
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    __table_args__ = (
        Index("idx_job_executions_job_id", "job_id"),
        Index("idx_job_executions_created_at", "created_at"),
    )
