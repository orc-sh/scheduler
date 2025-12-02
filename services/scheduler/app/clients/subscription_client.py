"""
Subscription client for communicating with Chargebee API.

This client handles all direct Chargebee API interactions, similar to how
AuthServiceClient handles communication with the auth service.
"""

import logging
from typing import Dict, Optional

from chargebee import Chargebee  # noqa: F401

from config.environment import get_chargebee_api_key, get_chargebee_site

logger = logging.getLogger(__name__)


class SubscriptionClient:
    """Client for communicating with Chargebee subscription API."""

    _instance = None

    def __init__(self) -> None:
        """Initialize the Chargebee client."""
        try:
            api_key = get_chargebee_api_key()
            site = get_chargebee_site()
            # Chargebee 3.x uses the Chargebee client class instead of module-level configure()
            self._client = Chargebee(api_key=api_key, site=site)
            logger.info("Chargebee client initialized successfully")
        except ValueError as e:
            self._client = None  # type: ignore[assignment]
            logger.warning(f"Chargebee configuration not set: {str(e)}")
            # Don't raise - will fail when actually using Chargebee

    def create_customer(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Dict:
        """
        Create a customer in Chargebee.

        Args:
            email: Customer email address
            first_name: Customer first name (optional)
            last_name: Customer last name (optional)

        Returns:
            Chargebee customer object

        Raises:
            ValueError: If customer creation fails
        """
        try:
            if not getattr(self, "_client", None):
                raise ValueError("Chargebee client is not configured")

            customer_result = self._client.Customer.create(  # type: ignore[union-attr]
                {
                    "email": email,
                    "first_name": first_name or "",
                    "last_name": last_name or "",
                }
            )
            customer = customer_result.customer  # type: ignore[attr-defined]
            if not customer:
                raise ValueError("Failed to create customer in Chargebee")
            return customer
        except Exception as e:
            logger.error(f"Failed to create customer in Chargebee: {str(e)}")
            raise ValueError(f"Failed to create customer in Chargebee: {str(e)}")

    def create_subscription(self, plan_id: str, customer_id: str) -> Dict:
        """
        Create a subscription in Chargebee using Product Catalog 2.0 format.

        Args:
            plan_id: Chargebee item price ID (plan_id) - used as item_price_id in Product Catalog 2.0
            customer_id: Chargebee customer ID

        Returns:
            Chargebee subscription object

        Raises:
            ValueError: If subscription creation fails
        """
        try:
            if not getattr(self, "_client", None):
                raise ValueError("Chargebee client is not configured")

            # Chargebee 3.x Product Catalog 2.0: use create_with_items with typed params
            params = self._client.Subscription.CreateWithItemsParams(  # type: ignore[union-attr]
                subscription_items=[
                    self._client.Subscription.CreateWithItemsSubscriptionItemParams(  # type: ignore[union-attr]
                        item_price_id=plan_id,
                        quantity=1,  # using int instead of str to match Chargebee API
                    )
                ]
            )
            subscription_result = self._client.Subscription.create_with_items(  # type: ignore[union-attr]
                customer_id, params
            )
            cb_subscription = subscription_result.subscription  # type: ignore[attr-defined]
            if not cb_subscription:
                raise ValueError("Failed to create subscription in Chargebee")
            return cb_subscription
        except Exception as e:
            logger.error(f"Failed to create subscription in Chargebee: {str(e)}")
            raise ValueError(f"Failed to create subscription in Chargebee: {str(e)}")

    def update_subscription(self, chargebee_subscription_id: str, plan_id: Optional[str] = None) -> Dict:
        """
        Update a subscription in Chargebee using Product Catalog 2.0 format.

        Args:
            chargebee_subscription_id: Chargebee subscription ID
            plan_id: New item price ID (plan_id) - used as item_price_id in Product Catalog 2.0 (optional)

        Returns:
            Updated Chargebee subscription object

        Raises:
            ValueError: If update fails
        """
        try:
            if not plan_id:
                raise ValueError("No update parameters provided")

            if not getattr(self, "_client", None):
                raise ValueError("Chargebee client is not configured")

            # Product Catalog 2.0 requires update_for_items with subscription_items
            # Replace the existing items with the new item_price_id
            result = self._client.Subscription.update_for_items(  # type: ignore[union-attr]
                chargebee_subscription_id,
                {
                    "subscription_items": [
                        {
                            "item_price_id": plan_id,
                            "quantity": 1,
                        }
                    ],
                    "replace_items_list": True,
                },
            )
            cb_subscription = result.subscription  # type: ignore[attr-defined]
            if not cb_subscription:
                raise ValueError("Failed to update subscription in Chargebee")
            return cb_subscription
        except Exception as e:
            logger.error(f"Failed to update subscription in Chargebee: {str(e)}")
            raise ValueError(f"Failed to update subscription in Chargebee: {str(e)}")

    def cancel_subscription(self, chargebee_subscription_id: str, cancel_reason: Optional[str] = None) -> Dict:
        """
        Cancel a subscription in Chargebee.

        Args:
            chargebee_subscription_id: Chargebee subscription ID
            cancel_reason: Reason for cancellation (optional)

        Returns:
            Cancelled Chargebee subscription object

        Raises:
            ValueError: If cancellation fails
        """
        try:
            if not getattr(self, "_client", None):
                raise ValueError("Chargebee client is not configured")

            cancel_params = {}
            if cancel_reason:
                cancel_params["cancel_reason"] = cancel_reason

            result = self._client.Subscription.cancel(  # type: ignore[union-attr]
                chargebee_subscription_id, cancel_params
            )
            cb_subscription = result.subscription  # type: ignore[attr-defined]
            if not cb_subscription:
                raise ValueError("Failed to cancel subscription in Chargebee")
            return cb_subscription
        except Exception as e:
            logger.error(f"Failed to cancel subscription in Chargebee: {str(e)}")
            raise ValueError(f"Failed to cancel subscription in Chargebee: {str(e)}")

    def get_subscription(self, chargebee_subscription_id: str) -> Dict:
        """
        Retrieve a subscription from Chargebee.

        Args:
            chargebee_subscription_id: Chargebee subscription ID

        Returns:
            Chargebee subscription object

        Raises:
            ValueError: If subscription not found or retrieval fails
        """
        try:
            if not getattr(self, "_client", None):
                raise ValueError("Chargebee client is not configured")

            result = self._client.Subscription.retrieve(chargebee_subscription_id)  # type: ignore[union-attr]
            cb_subscription = result.subscription  # type: ignore[attr-defined]
            if not cb_subscription:
                raise ValueError("Subscription not found in Chargebee")
            return cb_subscription
        except Exception as e:
            logger.error(f"Failed to retrieve subscription from Chargebee: {str(e)}")
            raise ValueError(f"Failed to retrieve subscription from Chargebee: {str(e)}")

    def sync_subscription(self, chargebee_subscription_id: str) -> Dict:
        """
        Sync subscription data from Chargebee.

        This is an alias for get_subscription for consistency.

        Args:
            chargebee_subscription_id: Chargebee subscription ID

        Returns:
            Chargebee subscription object
        """
        return self.get_subscription(chargebee_subscription_id)


# Singleton instance
_subscription_client_instance: Optional[SubscriptionClient] = None


def get_subscription_client() -> SubscriptionClient:
    """
    Get or create the singleton SubscriptionClient instance.

    Returns:
        SubscriptionClient instance
    """
    global _subscription_client_instance
    if _subscription_client_instance is None:
        _subscription_client_instance = SubscriptionClient()
    return _subscription_client_instance
