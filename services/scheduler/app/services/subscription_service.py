"""
Subscription service for managing subscriptions via Chargebee integration.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

import chargebee
from sqlalchemy.orm import Session

from app.models.projects import Project
from app.models.subscriptions import Subscription
from config.environment import get_chargebee_api_key, get_chargebee_site

logger = logging.getLogger(__name__)


def _init_chargebee():
    """Initialize Chargebee configuration (lazy initialization)."""
    try:
        chargebee.configure(get_chargebee_api_key(), get_chargebee_site())
    except ValueError:
        # Configuration not set, will fail when actually using Chargebee
        pass


class SubscriptionService:
    """Service class for subscription-related operations with Chargebee integration"""

    def __init__(self, db: Session):
        """
        Initialize the subscription service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_subscription(
        self,
        project_id: str,
        plan_id: str,
        customer_email: str,
        customer_first_name: Optional[str] = None,
        customer_last_name: Optional[str] = None,
    ) -> Subscription:
        """
        Create a new subscription for a project via Chargebee.

        Args:
            project_id: ID of the project
            plan_id: Chargebee plan ID
            customer_email: Customer email address
            customer_first_name: Customer first name (optional)
            customer_last_name: Customer last name (optional)

        Returns:
            Created Subscription instance

        Raises:
            ValueError: If project not found or subscription creation fails
        """
        # Verify project exists
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")

        # Check if subscription already exists for this project
        existing = self.db.query(Subscription).filter(Subscription.project_id == project_id).first()
        if existing:
            raise ValueError(f"Subscription already exists for project {project_id}")

        try:
            # Initialize Chargebee if not already done
            _init_chargebee()

            # Create customer in Chargebee
            customer_result = chargebee.Customer.create(
                {
                    "email": customer_email,
                    "first_name": customer_first_name or "",
                    "last_name": customer_last_name or "",
                }
            )
            customer = customer_result.customer  # type: ignore[attr-defined]
            if not customer:
                raise ValueError("Failed to create customer in Chargebee")

            # Create subscription in Chargebee
            subscription_result = chargebee.Subscription.create(
                {
                    "plan_id": plan_id,
                    "customer": {"id": customer.id},  # type: ignore[attr-defined]
                }
            )
            cb_subscription = subscription_result.subscription  # type: ignore[attr-defined]
            if not cb_subscription:
                raise ValueError("Failed to create subscription in Chargebee")

            # Create subscription record in database
            subscription = Subscription(
                id=str(cb_subscription.id),  # type: ignore[attr-defined]
                project_id=project_id,
                chargebee_subscription_id=cb_subscription.id,  # type: ignore[attr-defined]
                chargebee_customer_id=customer.id,  # type: ignore[attr-defined]
                plan_id=plan_id,
                status=cb_subscription.status,  # type: ignore[attr-defined]
                current_term_start=self._parse_datetime(  # type: ignore[attr-defined]
                    getattr(cb_subscription, "current_term_start", None)
                ),
                current_term_end=self._parse_datetime(  # type: ignore[attr-defined]
                    getattr(cb_subscription, "current_term_end", None)
                ),
                trial_end=self._parse_datetime(  # type: ignore[attr-defined]
                    getattr(cb_subscription, "trial_end", None)
                ),
                metadata=(
                    json.dumps(vars(cb_subscription))  # type: ignore[attr-defined]
                    if hasattr(cb_subscription, "__dict__")
                    else None
                ),
            )

            self.db.add(subscription)
            self.db.commit()
            self.db.refresh(subscription)

            logger.info(f"Created subscription {subscription.id} for project {project_id}")
            return subscription

        except Exception as e:
            logger.error(f"Failed to create subscription: {str(e)}")
            self.db.rollback()
            raise ValueError(f"Failed to create subscription: {str(e)}")

    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """
        Get a specific subscription by ID.

        Args:
            subscription_id: ID of the subscription to retrieve

        Returns:
            Subscription instance if found, None otherwise
        """
        return self.db.query(Subscription).filter(Subscription.id == subscription_id).first()

    def get_subscription_by_project(self, project_id: str) -> Optional[Subscription]:
        """
        Get subscription for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            Subscription instance if found, None otherwise
        """
        return self.db.query(Subscription).filter(Subscription.project_id == project_id).first()

    def get_subscriptions_by_user(self, user_id: str) -> List[Subscription]:
        """
        Get all subscriptions for a user (through their projects).

        Args:
            user_id: ID of the user

        Returns:
            List of Subscription instances
        """
        return (
            self.db.query(Subscription)
            .join(Project, Subscription.project_id == Project.id)
            .filter(Project.user_id == user_id)
            .all()
        )

    def update_subscription(self, subscription_id: str, plan_id: Optional[str] = None) -> Optional[Subscription]:
        """
        Update a subscription (change plan, etc.) via Chargebee.

        Args:
            subscription_id: ID of the subscription to update
            plan_id: New plan ID (optional)

        Returns:
            Updated Subscription instance if found, None otherwise

        Raises:
            ValueError: If update fails
        """
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return None

        try:
            # Initialize Chargebee if not already done
            _init_chargebee()

            update_params = {}
            if plan_id:
                update_params["plan_id"] = plan_id

            if not update_params:
                return subscription

            # Update subscription in Chargebee
            result = chargebee.Subscription.update(subscription.chargebee_subscription_id, update_params)
            cb_subscription = result.subscription  # type: ignore[attr-defined]
            if not cb_subscription:
                raise ValueError("Failed to update subscription in Chargebee")

            # Update local subscription record
            subscription.plan_id = cb_subscription.plan_id  # type: ignore[attr-defined]
            subscription.status = cb_subscription.status  # type: ignore[attr-defined]
            subscription.current_term_start = self._parse_datetime(  # type: ignore[attr-defined,assignment]
                getattr(cb_subscription, "current_term_start", None)
            )
            subscription.current_term_end = self._parse_datetime(  # type: ignore[attr-defined,assignment]
                getattr(cb_subscription, "current_term_end", None)
            )
            subscription.trial_end = self._parse_datetime(  # type: ignore[attr-defined,assignment]
                getattr(cb_subscription, "trial_end", None)
            )
            subscription.metadata = (  # type: ignore[attr-defined,assignment]
                json.dumps(vars(cb_subscription)) if hasattr(cb_subscription, "__dict__") else None
            )

            self.db.commit()
            self.db.refresh(subscription)

            logger.info(f"Updated subscription {subscription_id}")
            return subscription

        except Exception as e:
            logger.error(f"Failed to update subscription: {str(e)}")
            self.db.rollback()
            raise ValueError(f"Failed to update subscription: {str(e)}")

    def cancel_subscription(self, subscription_id: str, cancel_reason: Optional[str] = None) -> Optional[Subscription]:
        """
        Cancel a subscription via Chargebee.

        Args:
            subscription_id: ID of the subscription to cancel
            cancel_reason: Reason for cancellation (optional)

        Returns:
            Updated Subscription instance if found, None otherwise

        Raises:
            ValueError: If cancellation fails
        """
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return None

        try:
            # Initialize Chargebee if not already done
            _init_chargebee()

            # Cancel subscription in Chargebee
            cancel_params = {}
            if cancel_reason:
                cancel_params["cancel_reason"] = cancel_reason

            result = chargebee.Subscription.cancel(subscription.chargebee_subscription_id, cancel_params)
            cb_subscription = result.subscription  # type: ignore[attr-defined]
            if not cb_subscription:
                raise ValueError("Failed to cancel subscription in Chargebee")

            # Update local subscription record
            subscription.status = cb_subscription.status  # type: ignore[attr-defined]
            subscription.cancelled_at = datetime.utcnow()  # type: ignore[assignment]
            subscription.cancel_reason = cancel_reason  # type: ignore[assignment]
            subscription.metadata = (  # type: ignore[attr-defined,assignment]
                json.dumps(vars(cb_subscription)) if hasattr(cb_subscription, "__dict__") else None
            )

            self.db.commit()
            self.db.refresh(subscription)

            logger.info(f"Cancelled subscription {subscription_id}")
            return subscription

        except Exception as e:
            logger.error(f"Failed to cancel subscription: {str(e)}")
            self.db.rollback()
            raise ValueError(f"Failed to cancel subscription: {str(e)}")

    def delete_subscription(self, subscription_id: str) -> bool:
        """
        Delete a subscription (only from local database, not from Chargebee).

        Note: This only removes the local record. The subscription in Chargebee
        should be cancelled first using cancel_subscription().

        Args:
            subscription_id: ID of the subscription to delete

        Returns:
            True if subscription was deleted, False if not found
        """
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return False

        self.db.delete(subscription)
        self.db.commit()
        return True

    def sync_subscription_from_chargebee(self, chargebee_subscription_id: str) -> Optional[Subscription]:
        """
        Sync subscription data from Chargebee to local database.

        Args:
            chargebee_subscription_id: Chargebee subscription ID

        Returns:
            Updated Subscription instance if found, None otherwise

        Raises:
            ValueError: If sync fails
        """
        try:
            # Initialize Chargebee if not already done
            _init_chargebee()

            # Fetch subscription from Chargebee
            result = chargebee.Subscription.retrieve(chargebee_subscription_id)
            cb_subscription = result.subscription  # type: ignore[attr-defined]
            if not cb_subscription:
                raise ValueError("Subscription not found in Chargebee")

            # Find or create local subscription record
            subscription = (
                self.db.query(Subscription)
                .filter(Subscription.chargebee_subscription_id == chargebee_subscription_id)
                .first()
            )

            if subscription:
                # Update existing record
                subscription.status = cb_subscription.status  # type: ignore[attr-defined]
                subscription.plan_id = cb_subscription.plan_id  # type: ignore[attr-defined]
                subscription.current_term_start = self._parse_datetime(  # type: ignore[attr-defined,assignment]
                    getattr(cb_subscription, "current_term_start", None)
                )
                subscription.current_term_end = self._parse_datetime(  # type: ignore[attr-defined,assignment]
                    getattr(cb_subscription, "current_term_end", None)
                )
                subscription.trial_end = self._parse_datetime(  # type: ignore[attr-defined,assignment]
                    getattr(cb_subscription, "trial_end", None)
                )
                subscription.metadata = (  # type: ignore[attr-defined,assignment]
                    json.dumps(vars(cb_subscription)) if hasattr(cb_subscription, "__dict__") else None
                )
            else:
                # Create new record (shouldn't happen often, but handle it)
                subscription = Subscription(
                    id=str(cb_subscription.id),  # type: ignore[attr-defined]
                    project_id="",  # Will need to be set manually
                    chargebee_subscription_id=cb_subscription.id,  # type: ignore[attr-defined]
                    chargebee_customer_id=getattr(cb_subscription, "customer_id", ""),  # type: ignore[attr-defined]
                    plan_id=cb_subscription.plan_id,  # type: ignore[attr-defined]
                    status=cb_subscription.status,  # type: ignore[attr-defined]
                    current_term_start=self._parse_datetime(  # type: ignore[attr-defined]
                        getattr(cb_subscription, "current_term_start", None)
                    ),
                    current_term_end=self._parse_datetime(  # type: ignore[attr-defined]
                        getattr(cb_subscription, "current_term_end", None)
                    ),
                    trial_end=self._parse_datetime(  # type: ignore[attr-defined]
                        getattr(cb_subscription, "trial_end", None)
                    ),
                    metadata=(
                        json.dumps(vars(cb_subscription))  # type: ignore[attr-defined]
                        if hasattr(cb_subscription, "__dict__")
                        else None
                    ),
                )
                self.db.add(subscription)

            self.db.commit()
            self.db.refresh(subscription)

            logger.info(f"Synced subscription {chargebee_subscription_id} from Chargebee")
            return subscription

        except Exception as e:
            logger.error(f"Failed to sync subscription from Chargebee: {str(e)}")
            self.db.rollback()
            raise ValueError(f"Failed to sync subscription: {str(e)}")

    def _parse_datetime(self, timestamp: Optional[int]) -> Optional[datetime]:
        """
        Parse Chargebee timestamp to datetime.

        Args:
            timestamp: Unix timestamp from Chargebee

        Returns:
            Datetime object or None
        """
        if timestamp is None:
            return None
        try:
            return datetime.fromtimestamp(timestamp)
        except (ValueError, TypeError):
            return None


def get_subscription_service(db: Session) -> SubscriptionService:
    """
    Factory function to create a SubscriptionService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        SubscriptionService instance
    """
    return SubscriptionService(db)
