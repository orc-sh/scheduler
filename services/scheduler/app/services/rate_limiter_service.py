"""
Rate limiter service for webhook execution based on subscription plan.

Uses Redis to track webhook execution counts per webhook ID with 24-hour expiration.
Rate limits:
- Free plan: 100 executions per day per webhook
- Pro plan: 1000 executions per day per webhook
"""

import os
from typing import Optional

import redis
from sqlalchemy.orm import Session

from app.logging.context_logger import get_logger
from app.models.accounts import Account
from app.models.jobs import Job
from app.models.subscriptions import Subscription
from app.models.webhooks import Webhook

logger = get_logger(__name__)

# Rate limits per plan (executions per day per webhook)
RATE_LIMITS = {
    "free": 100,
    "pro": 10,
}

# Creation limits per plan
# Free plan: unlimited URLs, 10 jobs/schedules
# Pro plan: 100 URLs, 100 jobs/schedules
URL_CREATION_LIMITS = {
    "free": 10,  # None means unlimited
    "pro": 10,
}

JOB_CREATION_LIMITS = {
    "free": 10,
    "pro": 100,
}

# Redis key expiration time (24 hours in seconds)
REDIS_TTL = 24 * 60 * 60  # 86400 seconds


class RateLimiterService:
    """Service for rate limiting webhook executions based on subscription plan"""

    def __init__(self):
        """Initialize Redis client"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Rate limiter service initialized with Redis connection")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for rate limiting: {e}")
            self.redis_client = None

    def _get_plan_type(self, plan_id: str) -> str:
        """
        Determine plan type from plan ID.

        Args:
            plan_id: Subscription plan ID

        Returns:
            Plan type: 'free' or 'pro'
        """
        if not plan_id:
            return "free"

        plan_lower = plan_id.lower()
        if plan_lower.startswith("pro"):
            return "pro"
        return "free"

    def _get_rate_limit(self, plan_id: Optional[str]) -> int:
        """
        Get rate limit for a plan.

        Args:
            plan_id: Subscription plan ID

        Returns:
            Rate limit (executions per day per webhook)
        """
        plan_type = self._get_plan_type(plan_id or "free")
        return RATE_LIMITS.get(plan_type, RATE_LIMITS["free"])

    def _get_redis_key(self, identifier: str, key_type: str = "webhook") -> str:
        """
        Generate Redis key for rate limiting.

        Args:
            identifier: Webhook ID or URL identifier
            key_type: Type of identifier ('webhook' or 'url')

        Returns:
            Redis key string
        """
        return f"rate_limit:{key_type}:{identifier}"

    def get_plan_for_account(self, db: Session, account_id: str) -> Optional[str]:
        """
        Get subscription plan ID for an account.

        Args:
            db: Database session
            account_id: Account ID

        Returns:
            Plan ID or None if not found
        """
        try:
            # Get account
            account = db.query(Account).filter(Account.id == account_id).first()
            if not account:
                logger.debug(f"Account {account_id} not found")
                return None

            # Get subscription
            subscription = db.query(Subscription).filter(Subscription.account_id == account_id).first()
            if not subscription:
                logger.debug(f"No subscription found for account {account_id}")
                return None

            plan_id = getattr(subscription, "plan_id", None)
            plan_id_str = str(plan_id) if plan_id else None
            logger.debug(f"Found plan_id {plan_id_str} for account {account_id}")
            return plan_id_str
        except Exception as e:
            logger.error(f"Error getting plan for account {account_id}: {e}")
            return None

    def get_plan_for_webhook(self, db: Session, webhook: Webhook) -> Optional[str]:
        """
        Get subscription plan ID for a webhook.

        Args:
            db: Database session
            webhook: Webhook instance

        Returns:
            Plan ID or None if not found
        """
        try:
            if not webhook:
                return None

            # Access SQLAlchemy column value properly
            job_id = getattr(webhook, "job_id", None)
            if not job_id:
                logger.debug(f"Webhook {getattr(webhook, 'id', 'unknown')} has no job_id")
                return None

            # Get job
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.debug(f"Job {job_id} not found")
                return None

            account_id = getattr(job, "account_id", None)
            if not account_id:
                logger.debug(f"Job {job_id} has no account_id")
                return None

            # Get account
            account = db.query(Account).filter(Account.id == account_id).first()
            if not account:
                logger.debug(f"Account {account_id} not found")
                return None

            # Get subscription
            subscription = (
                db.query(Subscription).filter(Subscription.account_id == getattr(account, "id", None)).first()
            )
            if not subscription:
                logger.debug(f"No subscription found for account {getattr(account, 'id', 'unknown')}")
                return None

            plan_id = getattr(subscription, "plan_id", None)
            plan_id_str = str(plan_id) if plan_id else None
            logger.debug(f"Found plan_id {plan_id_str} for webhook {getattr(webhook, 'id', 'unknown')}")
            return plan_id_str
        except Exception as e:
            logger.error(f"Error getting plan for webhook {webhook.id if webhook else 'unknown'}: {e}")
            return None

    def check_rate_limit(self, db: Session, webhook: Webhook) -> tuple[bool, int, int]:
        """
        Check if webhook execution is within rate limit.

        Args:
            db: Database session
            webhook: Webhook instance

        Returns:
            Tuple of (is_allowed, current_count, limit)
            - is_allowed: True if execution is allowed, False if rate limited
            - current_count: Current number of executions today
            - limit: Maximum allowed executions per day
        """
        if not self.redis_client:
            # If Redis is not available, allow execution (fail open)
            logger.warning("Redis not available, allowing webhook execution without rate limiting")
            return True, 0, RATE_LIMITS["pro"]

        try:
            webhook_id = str(webhook.id)
            # Get plan for webhook
            plan_id = self.get_plan_for_webhook(db, webhook)
            plan_type = self._get_plan_type(plan_id or "free")
            limit = self._get_rate_limit(plan_id)

            # Get Redis key
            redis_key = self._get_redis_key(webhook_id, key_type="webhook")

            # Get current count
            current_count_str = self.redis_client.get(redis_key)
            current_count = int(current_count_str) if current_count_str and isinstance(current_count_str, str) else 0

            # Log rate limit check for debugging
            logger.info(
                f"Rate limit check for webhook {webhook_id}: {current_count}/{limit} "
                f"(plan_id: {plan_id}, plan_type: {plan_type})"
            )

            # Check if limit exceeded
            if current_count >= limit:
                logger.warning(
                    f"Rate limit exceeded for webhook {webhook_id}: {current_count}/{limit} "
                    f"(plan_id: {plan_id}, plan_type: {plan_type})"
                )
                return False, current_count, limit

            return True, current_count, limit
        except Exception as e:
            logger.error(f"Error checking rate limit for webhook {webhook.id if webhook else 'unknown'}: {e}")
            # Fail open - allow execution if rate limit check fails
            return True, 0, RATE_LIMITS["pro"]

    def check_rate_limit_for_url(self, db: Session, url_id: str, account_id: str) -> tuple[bool, int, int]:
        """
        Check if URL request is within rate limit.

        Args:
            db: Database session
            url_id: URL ID or unique identifier
            account_id: Account ID

        Returns:
            Tuple of (is_allowed, current_count, limit)
        """
        if not self.redis_client:
            logger.warning("Redis not available, allowing URL request without rate limiting")
            return True, 0, RATE_LIMITS["pro"]

        try:
            # Get plan for account
            plan_id = self.get_plan_for_account(db, account_id)
            plan_type = self._get_plan_type(plan_id or "free")
            limit = self._get_rate_limit(plan_id)

            # Get Redis key
            redis_key = self._get_redis_key(str(url_id), key_type="url")

            # Get current count
            current_count_str = self.redis_client.get(redis_key)
            current_count = int(current_count_str) if current_count_str and isinstance(current_count_str, str) else 0

            # Log rate limit check for debugging
            logger.info(
                f"Rate limit check for URL {url_id}: {current_count}/{limit} "
                f"(plan_id: {plan_id}, plan_type: {plan_type})"
            )

            # Check if limit exceeded
            if current_count >= limit:
                logger.warning(
                    f"Rate limit exceeded for URL {url_id}: {current_count}/{limit} "
                    f"(plan_id: {plan_id}, plan_type: {plan_type})"
                )
                return False, current_count, limit

            return True, current_count, limit
        except Exception as e:
            logger.error(f"Error checking rate limit for URL {url_id}: {e}")
            # Fail open - allow request if rate limit check fails
            return True, 0, RATE_LIMITS["pro"]

    def increment_rate_limit(self, identifier: str, key_type: str = "webhook") -> int:
        """
        Increment rate limit counter.

        Args:
            identifier: Webhook ID or URL identifier
            key_type: Type of identifier ('webhook' or 'url')

        Returns:
            New count after increment
        """
        if not self.redis_client:
            return 0

        try:
            redis_key = self._get_redis_key(str(identifier), key_type=key_type)

            # Increment counter (creates key if it doesn't exist)
            incr_result = self.redis_client.incr(redis_key)
            new_count = int(incr_result) if incr_result is not None else 0  # type: ignore[arg-type]

            # Set expiration if this is the first increment (key was just created)
            if new_count == 1:
                self.redis_client.expire(redis_key, REDIS_TTL)

            return new_count
        except Exception as e:
            logger.error(f"Error incrementing rate limit for {key_type} {identifier}: {e}")
            return 0

    def get_current_count(self, identifier: str, key_type: str = "webhook") -> int:
        """
        Get current count for webhook or URL.

        Args:
            identifier: Webhook ID or URL identifier
            key_type: Type of identifier ('webhook' or 'url')

        Returns:
            Current count
        """
        if not self.redis_client:
            return 0

        try:
            redis_key = self._get_redis_key(str(identifier), key_type=key_type)
            count_str = self.redis_client.get(redis_key)
            return int(count_str) if count_str and isinstance(count_str, str) else 0
        except Exception as e:
            logger.error(f"Error getting current count for {key_type} {identifier}: {e}")
            return 0

    def _count_urls_for_account(self, db: Session, account_id: str) -> int:
        """
        Count the number of URLs for an account.

        Args:
            db: Database session
            account_id: Account ID

        Returns:
            Number of URLs for the account
        """
        try:
            from app.models.urls import Url

            count = db.query(Url).filter(Url.account_id == account_id).count()
            return count
        except Exception as e:
            logger.error(f"Error counting URLs for account {account_id}: {e}")
            return 0

    def _count_jobs_for_account(self, db: Session, account_id: str) -> int:
        """
        Count the number of jobs/schedules for an account.

        Args:
            db: Database session
            account_id: Account ID

        Returns:
            Number of jobs for the account
        """
        try:
            count = db.query(Job).filter(Job.account_id == account_id).count()
            return count
        except Exception as e:
            logger.error(f"Error counting jobs for account {account_id}: {e}")
            return 0

    def can_create_url(self, db: Session, account_id: str) -> tuple[bool, int, Optional[int]]:
        """
        Check if account can create more URLs based on plan limits.

        Args:
            db: Database session
            account_id: Account ID

        Returns:
            Tuple of (can_create, current_count, limit)
            - can_create: True if can create more URLs, False if limit reached
            - current_count: Current number of URLs for the account
            - limit: Maximum allowed URLs (None for unlimited)
        """
        try:
            # Get plan for account
            plan_id = self.get_plan_for_account(db, account_id)
            plan_type = self._get_plan_type(plan_id or "free")
            limit = URL_CREATION_LIMITS.get(plan_type)

            # Count existing URLs
            current_count = self._count_urls_for_account(db, account_id)

            # If limit is None, it means unlimited (for free plan)
            if limit is None:
                logger.info(
                    f"URL creation check for account {account_id}: {current_count}/unlimited "
                    f"(plan_id: {plan_id}, plan_type: {plan_type})"
                )
                return True, current_count, None

            # Check if limit exceeded
            if current_count >= limit:
                logger.warning(
                    f"URL creation limit exceeded for account {account_id}: {current_count}/{limit} "
                    f"(plan_id: {plan_id}, plan_type: {plan_type})"
                )
                return False, current_count, limit

            logger.info(
                f"URL creation check for account {account_id}: {current_count}/{limit} "
                f"(plan_id: {plan_id}, plan_type: {plan_type})"
            )
            return True, current_count, limit
        except Exception as e:
            logger.error(f"Error checking URL creation limit for account {account_id}: {e}")
            # Fail open - allow creation if check fails
            return True, 0, None

    def can_create_job(self, db: Session, account_id: str) -> tuple[bool, int, int]:
        """
        Check if account can create more jobs/schedules based on plan limits.

        Args:
            db: Database session
            account_id: Account ID

        Returns:
            Tuple of (can_create, current_count, limit)
            - can_create: True if can create more jobs, False if limit reached
            - current_count: Current number of jobs for the account
            - limit: Maximum allowed jobs
        """
        try:
            # Get plan for account
            plan_id = self.get_plan_for_account(db, account_id)
            plan_type = self._get_plan_type(plan_id or "free")
            limit = JOB_CREATION_LIMITS.get(plan_type, JOB_CREATION_LIMITS["free"])

            # Count existing jobs
            current_count = self._count_jobs_for_account(db, account_id)

            # Check if limit exceeded
            if current_count >= limit:
                logger.warning(
                    f"Job creation limit exceeded for account {account_id}: {current_count}/{limit} "
                    f"(plan_id: {plan_id}, plan_type: {plan_type})"
                )
                return False, current_count, limit

            logger.info(
                f"Job creation check for account {account_id}: {current_count}/{limit} "
                f"(plan_id: {plan_id}, plan_type: {plan_type})"
            )
            return True, current_count, limit
        except Exception as e:
            logger.error(f"Error checking job creation limit for account {account_id}: {e}")
            # Fail open - allow creation if check fails
            return True, 0, JOB_CREATION_LIMITS["pro"]


# Singleton instance
_rate_limiter_service: Optional[RateLimiterService] = None


def get_rate_limiter_service() -> RateLimiterService:
    """
    Get or create rate limiter service instance.

    Returns:
        RateLimiterService instance
    """
    global _rate_limiter_service
    if _rate_limiter_service is None:
        _rate_limiter_service = RateLimiterService()
    return _rate_limiter_service
