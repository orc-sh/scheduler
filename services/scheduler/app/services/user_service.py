"""
User service for managing user account operations.
"""

from sqlalchemy.orm import Session

from app.logging.context_logger import get_logger
from app.models.accounts import Account
from app.services.account_service import get_account_service
from app.services.subscription_service import get_subscription_service

logger = get_logger(__name__)


class UserService:
    """Service class for user-related operations"""

    def __init__(self, db: Session):
        """
        Initialize the user service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def delete_user_account(self, user_id: str) -> bool:
        """
        Delete a user account and all associated data.

        This method:
        1. Gets all accounts for the user
        2. Cancels all subscriptions in Chargebee
        3. Deletes all accounts (which cascades to delete jobs, webhooks, urls, subscriptions, etc.)

        Args:
            user_id: ID of the user to delete

        Returns:
            True if account was deleted successfully, False otherwise

        Raises:
            ValueError: If deletion fails
        """
        try:
            account_service = get_account_service(self.db)
            subscription_service = get_subscription_service(self.db)

            # Get all accounts for the user
            accounts = self.db.query(Account).filter(Account.user_id == user_id).all()

            if not accounts:
                logger.info(f"No accounts found for user {user_id}, account deletion complete")
                return True

            # Cancel all subscriptions before deleting accounts
            for account in accounts:
                try:
                    subscription = subscription_service.get_subscription_by_account(account_id=str(account.id))
                    if subscription:
                        # Cancel subscription in Chargebee
                        try:
                            subscription_service.cancel_subscription(
                                subscription_id=subscription.id,
                                cancel_reason="Account deletion",
                            )
                            logger.info(f"Cancelled subscription {subscription.id} for account {account.id}")
                        except Exception as e:
                            logger.warning(f"Failed to cancel subscription {subscription.id}: {str(e)}")
                            # Continue with deletion even if cancellation fails
                except Exception as e:
                    logger.warning(f"Error processing subscription for account {account.id}: {str(e)}")

            # Delete all accounts (cascade will handle related data)
            deleted_count = 0
            for account in accounts:
                try:
                    deleted = account_service.delete_account(account_id=str(account.id), user_id=user_id)
                    if deleted:
                        deleted_count += 1
                        logger.info(f"Deleted account {account.id} for user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to delete account {account.id}: {str(e)}")
                    # Continue with other accounts

            if deleted_count != len(accounts):
                logger.warning(f"Only deleted {deleted_count} out of {len(accounts)} accounts for user {user_id}")

            self.db.commit()
            logger.info(f"Successfully deleted account for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete user account {user_id}: {str(e)}")
            self.db.rollback()
            raise ValueError(f"Failed to delete user account: {str(e)}")


def get_user_service(db: Session) -> UserService:
    """
    Factory function to create a UserService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        UserService instance
    """
    return UserService(db)
