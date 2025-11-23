"""
Subscription model for managing project subscriptions via Chargebee.
"""

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Index, String, Text
from sqlalchemy.sql import func

from .base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    chargebee_subscription_id = Column(String(255), nullable=False, unique=True)
    chargebee_customer_id = Column(String(255), nullable=False)
    plan_id = Column(String(100), nullable=False)  # Chargebee plan ID
    status = Column(String(50), nullable=False)  # active, cancelled, past_due, etc.
    current_term_start = Column(TIMESTAMP, nullable=True)
    current_term_end = Column(TIMESTAMP, nullable=True)
    trial_end = Column(TIMESTAMP, nullable=True)
    cancelled_at = Column(TIMESTAMP, nullable=True)
    cancel_reason = Column(String(255), nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string for additional data
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        Index("idx_subscriptions_project_id", "project_id"),
        Index("idx_subscriptions_chargebee_id", "chargebee_subscription_id"),
        Index("idx_subscriptions_status", "status"),
    )
