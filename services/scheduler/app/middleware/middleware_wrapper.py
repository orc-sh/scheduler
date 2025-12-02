"""
Request context middleware that combines auth and account middleware.

This middleware handles:
1. Public path exclusions (health checks, docs, webhooks, etc.)
2. Generation and storage of a per-request UUID in context
3. Authentication via auth middleware
4. Account context resolution via account middleware
"""

from uuid import uuid4

from fastapi import Request

from app.context.request_context import clear_request_uuid, set_request_uuid
from app.middleware.account_middleware import get_account_middleware
from app.middleware.auth_middleware import get_auth_middleware
from app.middleware.jwt_middleware import get_jwt_middleware

# Initialize middleware instances
auth_middleware = get_auth_middleware()
account_middleware = get_account_middleware()
jwt_middleware = get_jwt_middleware()


async def middleware_wrapper(request: Request, call_next):
    """
    Global middleware to:
    1. Generate and store a per-request UUID in the context
    2. Authenticate the request and set the current user in context
    3. Resolve and set the current account in context
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
    }

    # Prefixes for public routes (e.g. incoming webhooks / public URL receivers)
    public_prefixes = [
        "/webhooks/",
    ]

    path = request.url.path

    # Generate and set a request UUID for all requests (public or authenticated)
    request_id = uuid4()
    set_request_uuid(request_id)
    # Optionally expose on request.state for debugging / external logging
    request.state.request_id = str(request_id)

    try:
        # Special case: protect Chargebee callback with JWT middleware instead of full auth/account
        if path.startswith("/api/subscriptions/callback"):
            return await jwt_middleware(request, call_next)

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
    finally:
        # Ensure the request UUID is cleared after the request completes
        clear_request_uuid()
