"""
URL log model for storing incoming requests to URLs.
"""

from sqlalchemy import JSON, TIMESTAMP, Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class UrlLog(Base):
    __tablename__ = "url_logs"

    id = Column(String(36), primary_key=True)
    url_id = Column(String(36), ForeignKey("urls.id", ondelete="CASCADE"), nullable=False)
    method = Column(String(10), nullable=False)
    headers = Column(JSON, nullable=True)
    query_params = Column(JSON, nullable=True)
    body = Column(Text, nullable=True)
    response_status = Column(Integer, nullable=True)
    response_headers = Column(JSON, nullable=True)
    response_body = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(512), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    __table_args__ = (
        Index("idx_url_logs_url_id", "url_id"),
        Index("idx_url_logs_created_at", "created_at"),
    )
