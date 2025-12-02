"""
Account service for managing CRUD operations on accounts.
"""

import logging
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.accounts import Account

logger = logging.getLogger(__name__)


class AccountService:
    """Service class for account-related operations"""

    def __init__(self, db: Session):
        """
        Initialize the account service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_account(self, user_id: str, name: str, user=None) -> Account:
        """
        Create a new account for a user.
        Automatically creates a free tier subscription for the account.

        Uses a database transaction to ensure atomicity - if subscription creation
        fails for any reason, the account creation will be rolled back automatically.

        Args:
            user_id: ID of the user creating the account
            name: Name of the account
            user: User instance (optional, needed for subscription creation)

        Returns:
            Created Account instance

        Raises:
            Exception: If subscription creation fails, the entire transaction is
                rolled back and the original exception is re-raised.
        """
        account = Account(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
        )
        self.db.add(account)
        # Flush to make account visible in the transaction without committing
        # This allows the subscription service to see the account in the same session
        self.db.flush()
        self.db.refresh(account)

        # Automatically create a free tier subscription for the new account
        if user:
            try:
                from app.services.subscription_service import get_subscription_service

                subscription_service = get_subscription_service(self.db)

                # Get user email for subscription
                customer_email = user.email or f"{user_id}@example.com"
                customer_first_name = None
                customer_last_name = None

                # Try to extract name from user metadata
                if user.user_metadata:
                    if "name" in user.user_metadata:
                        name_parts = str(user.user_metadata["name"]).split(" ", 1)
                        customer_first_name = name_parts[0] if len(name_parts) > 0 else None
                        customer_last_name = name_parts[1] if len(name_parts) > 1 else None
                    elif "full_name" in user.user_metadata:
                        name_parts = str(user.user_metadata["full_name"]).split(" ", 1)
                        customer_first_name = name_parts[0] if len(name_parts) > 0 else None
                        customer_last_name = name_parts[1] if len(name_parts) > 1 else None

                # Create subscription with free plan
                # This will commit both account and subscription in the same transaction
                # since they share the same database session
                subscription_service.create_subscription(
                    account_id=str(account.id),
                    plan_id="free-plan-INR-Monthly",
                    customer_email=customer_email,
                    customer_first_name=customer_first_name,
                    customer_last_name=customer_last_name,
                )
                # Refresh account after successful commit
                self.db.refresh(account)
                logger.info(f"Created free tier subscription for account {account.id}")
            except Exception as e:
                # Rollback the entire transaction if subscription creation fails
                # This will automatically rollback the account since they're in the same transaction
                logger.error(f"Failed to create subscription for account {account.id}: {str(e)}")
                logger.info("Rolling back transaction - account creation will be undone")
                self.db.rollback()
                # Re-raise the original exception to notify the caller
                raise
        else:
            # If no user provided, commit the account creation
            self.db.commit()
            self.db.refresh(account)

        return account

    def get_account(self, account_id: str, user_id: str) -> Optional[Account]:
        """
        Get a specific account by ID for a user.

        Args:
            account_id: ID of the account to retrieve
            user_id: ID of the user (for authorization)

        Returns:
            Account instance if found and owned by user, None otherwise
        """
        return self.db.query(Account).filter(Account.id == account_id, Account.user_id == user_id).first()

    def get_accounts(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Account]:
        """
        Get all accounts for a user with pagination.

        Args:
            user_id: ID of the user
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of Account instances
        """
        return self.db.query(Account).filter(Account.user_id == user_id).offset(skip).limit(limit).all()

    def get_accounts_paginated(self, user_id: str, page: int = 1, page_size: int = 10) -> tuple[List[Account], dict]:
        """
        Get all accounts for a user with page-based pagination and metadata.

        Args:
            user_id: ID of the user
            page: Page number (1-indexed)
            page_size: Number of records per page

        Returns:
            Tuple of (List of Account instances, pagination metadata dict)
        """
        # Ensure page is at least 1
        page = max(1, page)
        page_size = max(1, min(page_size, 100))  # Cap at 100 items per page

        # Get total count
        total_entries = self.count_accounts(user_id)

        # Calculate total pages
        total_pages = (total_entries + page_size - 1) // page_size if total_entries > 0 else 1

        # Ensure page doesn't exceed total pages
        page = min(page, total_pages)

        # Calculate offset
        skip = (page - 1) * page_size

        # Get accounts for current page
        accounts = self.db.query(Account).filter(Account.user_id == user_id).offset(skip).limit(page_size).all()

        # Build pagination metadata
        has_next = page < total_pages
        has_previous = page > 1

        pagination_metadata = {
            "current_page": page,
            "total_pages": total_pages,
            "total_entries": total_entries,
            "page_size": page_size,
            "has_next": has_next,
            "has_previous": has_previous,
            "next_page": page + 1 if has_next else None,
            "previous_page": page - 1 if has_previous else None,
        }

        return accounts, pagination_metadata

    def update_account(self, account_id: str, user_id: str, name: str) -> Optional[Account]:
        """
        Update a account's name.

        Args:
            account_id: ID of the account to update
            user_id: ID of the user (for authorization)
            name: New name for the account

        Returns:
            Updated Account instance if found and owned by user, None otherwise
        """
        account = self.get_account(account_id, user_id)
        if not account:
            return None

        account.name = name  # type: ignore[assignment]
        self.db.commit()
        self.db.refresh(account)
        return account

    def delete_account(self, account_id: str, user_id: str) -> bool:
        """
        Delete an account and automatically cancel/delete all associated subscriptions.

        Uses a database transaction to ensure atomicity - if subscription deletion
        fails for any reason, the account deletion will be rolled back automatically.

        The process:
        1. Cancel subscription in Chargebee (external API call, best effort)
        2. Delete subscription and account in a single transaction
        3. Commit atomically

        Args:
            account_id: ID of the account to delete
            user_id: ID of the user (for authorization)

        Returns:
            True if account was deleted, False if not found or not owned by user

        Raises:
            Exception: If subscription or account deletion fails, the entire transaction
                is rolled back and the exception is re-raised.
        """
        account = self.get_account(account_id, user_id)
        if not account:
            return False

        try:
            # Get subscription service to handle subscription operations
            from app.services.subscription_service import get_subscription_service

            subscription_service = get_subscription_service(self.db)

            # Get subscription for this account
            subscription = subscription_service.get_subscription_by_account(account_id)

            if subscription:
                # Cancel subscription in Chargebee first (to stop billing)
                # This is an external API call that commits separately
                # If it fails, we'll still proceed with deletion but log a warning
                try:
                    subscription_service.cancel_subscription(
                        subscription_id=str(subscription.id), cancel_reason="Account deleted"
                    )
                    logger.info(f"Cancelled subscription {subscription.id} in Chargebee for account {account_id}")
                    # Re-fetch subscription after cancellation (it may have been updated)
                    subscription = subscription_service.get_subscription_by_account(account_id)
                except Exception as cancel_error:
                    # Log warning but continue with deletion - subscription may already be cancelled
                    # or Chargebee cancellation may fail, but we still want to clean up locally
                    logger.warning(f"Failed to cancel subscription {subscription.id} in Chargebee: {str(cancel_error)}")
                    # Subscription still exists locally, proceed with deletion

            # Start transaction for atomic deletion
            # Delete subscription from local database (if it exists)
            if subscription:
                self.db.delete(subscription)
                logger.info(f"Marked subscription {subscription.id} for deletion from database")

            # Delete the account
            self.db.delete(account)
            logger.info(f"Marked account {account_id} for deletion")

            # Commit the entire transaction atomically (both subscription and account deletion)
            self.db.commit()
            logger.info(f"Successfully deleted account {account_id} and its subscriptions")
            return True

        except Exception as e:
            # Rollback the entire transaction if anything fails
            logger.error(f"Failed to delete account {account_id} or its subscriptions: {str(e)}")
            logger.info("Rolling back transaction - account deletion will be undone")
            self.db.rollback()
            # Re-raise the exception to notify the caller
            raise

    def count_accounts(self, user_id: str) -> int:
        """
        Count the total number of accounts for a user.

        Args:
            user_id: ID of the user

        Returns:
            Total count of accounts
        """
        return self.db.query(Account).filter(Account.user_id == user_id).count()

    def get_or_create_account_by_name(
        self, user_id: str, account_name: str, user=None, default_plan_id: str = "free-plan"
    ) -> Account:
        """
        Get an existing account by name or create it if it doesn't exist.
        Automatically creates a free tier subscription for new accounts via create_account.

        Args:
            user_id: ID of the user
            account_name: Name of the account to find or create
            user: User instance (optional, needed for subscription creation)
            default_plan_id: Default plan ID for new subscriptions (default: "free-plan")
                Note: This parameter is kept for backward compatibility but subscriptions
                are now always created with "free-plan" via create_account.

        Returns:
            Account instance (either existing or newly created)
        """
        # Try to find existing account
        account = self.db.query(Account).filter(Account.user_id == user_id, Account.name == account_name).first()

        # If not found, create new account (which will automatically create subscription)
        if not account:
            account = self.create_account(user_id, account_name, user=user)

        return account


def get_account_service(db: Session) -> AccountService:
    """
    Factory function to create a AccountService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        AccountService instance
    """
    return AccountService(db)
