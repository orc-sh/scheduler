from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers import (
    health_controller,
    project_controller,
    scheduler_controller,
    subscription_controller,
    url_controller,
    url_receiver_controller,
)
from config.environment import get_frontend_url, init

# Initialize environment variables FIRST before importing modules that need them
init()

# Create the FastAPI application
app = FastAPI(title="Scheduler API", version="1.0.0")

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

# Include each router with a specific prefix and tags for better organization
app.include_router(health_controller.router, prefix="", tags=["Health"])
app.include_router(project_controller.router, prefix="/api/projects", tags=["Projects"])

# Include scheduler controller FIRST (with specific routes like GET /api/schedules, POST /api/schedules, etc.)
# This ensures scheduler CRUD operations are matched before the catch-all URL receiver
app.include_router(scheduler_controller.router, prefix="/api/schedules", tags=["Schedules"])

# Include URL receiver endpoint AFTER scheduler controller
# This catches /api/webhooks/{unique_identifier} for base64 tokens (not UUIDs)
# The URL receiver validates that the identifier is NOT a UUID before processing
# (no auth required, public endpoint)
# Note: URL receiver still uses /api/webhooks prefix to maintain backward compatibility
app.include_router(url_receiver_controller.router, prefix="/api/webhooks", tags=["URL Receiver"])
app.include_router(subscription_controller.router, prefix="/api/subscriptions", tags=["Subscriptions"])
app.include_router(url_controller.router, prefix="/api/urls", tags=["URLs"])

# Note: Authentication routes have been moved to the separate auth service
# running on port 8001. The scheduler service still uses the auth middleware
# for validating JWT tokens on protected routes.
