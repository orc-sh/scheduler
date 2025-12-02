"""
Route configuration for the Scheduler API.

This module centralizes all route registrations for better organization.
"""

from fastapi import FastAPI

from app.controllers import (
    account_controller,
    health_controller,
    notification_controller,
    scheduler_controller,
    subscription_controller,
    url_controller,
    url_receiver_controller,
    user_controller,
)


def router(app: FastAPI) -> None:
    """
    Register all application routes with their prefixes and tags.

    Args:
        app: FastAPI application instance
    """
    # Include each router with a specific prefix and tags for better organization
    app.include_router(health_controller.router, prefix="", tags=["Health"])
    app.include_router(account_controller.router, prefix="/api/accounts", tags=["Accounts"])
    app.include_router(url_controller.router, prefix="/api/urls", tags=["URLs"])
    app.include_router(scheduler_controller.router, prefix="/api/schedules", tags=["Schedules"])
    app.include_router(url_receiver_controller.router, prefix="/webhooks", tags=["URL Receiver"])
    app.include_router(notification_controller.router, prefix="/api/notifications", tags=["Notifications"])
    app.include_router(subscription_controller.router, prefix="/api/subscriptions", tags=["Subscriptions"])
    app.include_router(user_controller.router, prefix="/api/user", tags=["User"])
