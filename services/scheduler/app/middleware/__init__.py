# Middleware package

from app.middleware.account_middleware import AccountMiddleware, get_account_middleware, get_current_account
from app.middleware.auth_middleware import AuthMiddleware, get_auth_middleware, get_current_user
from app.middleware.middleware_wrapper import middleware_wrapper
from app.middleware.subscription_middleware import (
    SubscriptionMiddleware,
    get_all_subscriptions_for_user,
    get_subscription_for_user,
    get_subscription_middleware,
    require_active_subscription,
    require_plan,
    verify_subscription_status,
)

__all__ = [
    # Auth middleware
    "AuthMiddleware",
    "get_auth_middleware",
    "get_current_user",
    # Account middleware
    "AccountMiddleware",
    "get_account_middleware",
    "get_current_account",
    # Request context middleware
    "middleware_wrapper",
    # Subscription middleware
    "SubscriptionMiddleware",
    "get_subscription_middleware",
    "get_subscription_for_user",
    "get_all_subscriptions_for_user",
    "require_active_subscription",
    "require_plan",
    "verify_subscription_status",
]
