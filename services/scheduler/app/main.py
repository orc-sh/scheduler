from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.celery import scheduler
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
from app.middleware import get_account_middleware, get_auth_middleware
from config.environment import get_frontend_url, init

# Initialize environment variables FIRST before importing modules that need them
init()

# Configure Celery to autodiscover tasks
scheduler.autodiscover_tasks(["app.tasks"], force=True)

# Create the FastAPI application
app = FastAPI(title="Scheduler API", version="1.0.0")

# Initialize middleware instances
auth_middleware = get_auth_middleware()
account_middleware = get_account_middleware()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        get_frontend_url(),
        "http://localhost:3000",
        "http://localhost:8001",  # Auth service
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_and_account_context_middleware(request: Request, call_next):
    """
    Global middleware to:
    1. Authenticate the request and set the current user in context
    2. Resolve and set the current account in context
    """
    # Exact paths that should be accessible without auth
    # (health checks, docs, schema, webhooks, external callbacks, etc.)
    public_paths = {
        "/health",
        "/health/",
        "/health/detailed",
        "/metrics",
        "/openapi.json",
        "/docs",
        "/docs/",
        "/redoc",
        "/redoc/",
        # Chargebee / external billing callbacks (no user JWT available)
        "/api/subscriptions/callback",
    }

    # Prefixes for public routes (e.g. incoming webhooks / public URL receivers)
    public_prefixes = [
        "/api/webhooks/",
    ]

    path = request.url.path

    # Allow unauthenticated access to public paths, public prefixes, and CORS preflight requests
    if (
        path in public_paths
        or any(path.startswith(prefix) for prefix in public_prefixes)
        or request.method == "OPTIONS"
    ):
        return await call_next(request)

    # Run auth middleware to populate user context / request.state.user
    await auth_middleware(request)

    # Run account middleware to populate account context / request.state.account
    await account_middleware(request)

    # Proceed with the request
    response = await call_next(request)
    return response


# Include each router with a specific prefix and tags for better organization
app.include_router(health_controller.router, prefix="", tags=["Health"])
app.include_router(account_controller.router, prefix="/api/accounts", tags=["Accounts"])
app.include_router(url_controller.router, prefix="/api/urls", tags=["URLs"])
app.include_router(scheduler_controller.router, prefix="/api/schedules", tags=["Schedules"])
app.include_router(url_receiver_controller.router, prefix="/api/webhooks", tags=["URL Receiver"])
app.include_router(notification_controller.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(subscription_controller.router, prefix="/api/subscriptions", tags=["Subscriptions"])
app.include_router(user_controller.router, prefix="/api/user", tags=["User"])
