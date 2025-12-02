"""
Subscription service for managing subscriptions via Chargebee integration.

This service handles database operations and business logic, while delegating
Chargebee API calls to the SubscriptionClient.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.clients.subscription_client import get_subscription_client
from app.models.accounts import Account
from app.models.subscriptions import Subscription

logger = logging.getLogger(__name__)


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
        account_id: str,
        plan_id: str,
        customer_email: str,
        customer_first_name: Optional[str] = None,
        customer_last_name: Optional[str] = None,
    ) -> Subscription:
        """
        Create a new subscription for a account via Chargebee.

        Args:
            account_id: ID of the account
            plan_id: Chargebee plan ID
            customer_email: Customer email address
            customer_first_name: Customer first name (optional)
            customer_last_name: Customer last name (optional)

        Returns:
            Created Subscription instance

        Raises:
            ValueError: If account not found or subscription creation fails
        """
        # Verify account exists
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise ValueError(f"Account with ID {account_id} not found")

        # Check if subscription already exists for this account
        existing = self.db.query(Subscription).filter(Subscription.account_id == account_id).first()
        if existing:
            raise ValueError(f"Subscription already exists for account {account_id}")

        try:
            # Use subscription client for Chargebee operations
            subscription_client = get_subscription_client()

            # Create customer in Chargebee
            customer = subscription_client.create_customer(
                email=customer_email,
                first_name=customer_first_name,
                last_name=customer_last_name,
            )

            # Create subscription in Chargebee
            cb_subscription = subscription_client.create_subscription(
                plan_id=plan_id,
                customer_id=customer.id,  # type: ignore[attr-defined]
            )

            # Create subscription record in database
            subscription = Subscription(
                id=str(cb_subscription.id),  # type: ignore[attr-defined]
                account_id=account_id,
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
                subscription_metadata=(
                    json.dumps(cb_subscription.to_json())  # type: ignore[attr-defined]
                    if hasattr(cb_subscription, "to_json")
                    else None
                ),
            )

            self.db.add(subscription)
            self.db.commit()
            self.db.refresh(subscription)

            logger.info(f"Created subscription {subscription.id} for account {account_id}")
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

    def get_subscription_by_account(self, account_id: str) -> Optional[Subscription]:
        """
        Get subscription for a specific account.

        Args:
            account_id: ID of the account

        Returns:
            Subscription instance if found, None otherwise
        """
        return self.db.query(Subscription).filter(Subscription.account_id == account_id).first()

    def get_subscriptions_by_user(self, user_id: str) -> List[Subscription]:
        """
        Get all subscriptions for a user (through their accounts).

        Args:
            user_id: ID of the user

        Returns:
            List of Subscription instances
        """
        return (
            self.db.query(Subscription)
            .join(Account, Subscription.account_id == Account.id)
            .filter(Account.user_id == user_id)
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
            # Use subscription client for Chargebee operations
            subscription_client = get_subscription_client()

            if not plan_id:
                return subscription

            # Update subscription in Chargebee
            cb_subscription = subscription_client.update_subscription(
                chargebee_subscription_id=str(subscription.chargebee_subscription_id),
                plan_id=plan_id,
            )

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
            subscription.subscription_metadata = (  # type: ignore[attr-defined,assignment]
                json.dumps(cb_subscription.to_json())  # type: ignore[attr-defined]
                if hasattr(cb_subscription, "to_json")
                else None
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
            # Use subscription client for Chargebee operations
            subscription_client = get_subscription_client()

            # Cancel subscription in Chargebee
            cb_subscription = subscription_client.cancel_subscription(
                chargebee_subscription_id=str(subscription.chargebee_subscription_id),
                cancel_reason=cancel_reason,
            )

            # Update local subscription record
            subscription.status = cb_subscription.status  # type: ignore[attr-defined]
            subscription.cancelled_at = datetime.utcnow()  # type: ignore[assignment]
            subscription.cancel_reason = cancel_reason  # type: ignore[assignment]
            subscription.subscription_metadata = (  # type: ignore[attr-defined,assignment]
                json.dumps(cb_subscription.to_json())  # type: ignore[attr-defined]
                if hasattr(cb_subscription, "to_json")
                else None
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
            # Use subscription client for Chargebee operations
            subscription_client = get_subscription_client()

            # Fetch subscription from Chargebee
            cb_subscription = subscription_client.get_subscription(chargebee_subscription_id)

            logger.info(f"Syncing subscription {cb_subscription} from Chargebee: {cb_subscription}")
            # Derive plan_id in a Product Catalog 2.0 friendly way
            plan_id = self._extract_plan_id_from_cb_subscription(cb_subscription)
            if not plan_id:
                raise ValueError("Chargebee subscription is missing plan_id / item_price_id")

            # Find or create local subscription record
            subscription = (
                self.db.query(Subscription)
                .filter(Subscription.chargebee_subscription_id == chargebee_subscription_id)
                .first()
            )

            if subscription:
                # Update existing record
                subscription.status = cb_subscription.status  # type: ignore[attr-defined]
                # For PC 2.0, plan_id may be on subscription_items instead of root
                subscription.plan_id = plan_id  # type: ignore[assignment]
                subscription.current_term_start = self._parse_datetime(  # type: ignore[attr-defined,assignment]
                    getattr(cb_subscription, "current_term_start", None)
                )
                subscription.current_term_end = self._parse_datetime(  # type: ignore[attr-defined,assignment]
                    getattr(cb_subscription, "current_term_end", None)
                )
                subscription.trial_end = self._parse_datetime(  # type: ignore[attr-defined,assignment]
                    getattr(cb_subscription, "trial_end", None)
                )
                # Best-effort serialization of full Chargebee payload for debugging/auditing.
                # We intentionally swallow serialization errors to avoid failing the sync.
                try:
                    if hasattr(cb_subscription, "to_json"):
                        subscription.subscription_metadata = json.dumps(
                            cb_subscription.to_json(), default=str
                        )  # type: ignore[attr-defined,assignment]
                    elif hasattr(cb_subscription, "__dict__"):
                        subscription.subscription_metadata = json.dumps(
                            vars(cb_subscription), default=str
                        )  # type: ignore[attr-defined,assignment]
                    else:
                        subscription.subscription_metadata = None  # type: ignore[attr-defined,assignment]
                except Exception as ser_err:
                    logger.warning(
                        "Failed to serialize Chargebee subscription metadata: %s",
                        ser_err,
                    )
                    subscription.subscription_metadata = None  # type: ignore[attr-defined,assignment]
            else:
                # Create new record (shouldn't happen often, but handle it)
                subscription = Subscription(
                    id=str(cb_subscription.id),  # type: ignore[attr-defined]
                    account_id="",  # Will need to be set manually
                    chargebee_subscription_id=cb_subscription.id,  # type: ignore[attr-defined]
                    chargebee_customer_id=getattr(cb_subscription, "customer_id", ""),  # type: ignore[attr-defined]
                    plan_id=plan_id,  # type: ignore[assignment]
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
                    subscription_metadata=None,
                )
                # Populate metadata in a best-effort way (same logic as above)
                try:
                    if hasattr(cb_subscription, "to_json"):
                        subscription.subscription_metadata = json.dumps(
                            cb_subscription.to_json(), default=str
                        )  # type: ignore[attr-defined,assignment]
                    elif hasattr(cb_subscription, "__dict__"):
                        subscription.subscription_metadata = json.dumps(
                            vars(cb_subscription), default=str
                        )  # type: ignore[attr-defined,assignment]
                except Exception as ser_err:
                    logger.warning(
                        "Failed to serialize Chargebee subscription metadata (new): %s",
                        ser_err,
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

    def _extract_plan_id_from_cb_subscription(self, cb_subscription: object) -> Optional[str]:
        """
        Extract a plan_id / item_price_id from a Chargebee subscription object.

        Supports both Product Catalog 1.0 (subscription.plan_id)
        and Product Catalog 2.0 (subscription.subscription_items[0].item_price_id).
        """
        # Direct plan_id (PC 1.0 or some PC 2.0 setups)
        direct_plan_id = getattr(cb_subscription, "plan_id", None)
        if direct_plan_id:
            return str(direct_plan_id)

        # PC 2.0: subscription_items
        items = getattr(cb_subscription, "subscription_items", None)
        if items and isinstance(items, (list, tuple)):
            first = items[0]
            item_price_id = getattr(first, "item_price_id", None)
            if item_price_id:
                return str(item_price_id)

        # Fallback: nothing found
        return None

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
