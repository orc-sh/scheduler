from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers import health_controller, project_controller, subscription_controller, webhook_controller
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
app.include_router(webhook_controller.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(subscription_controller.router, prefix="/api/subscriptions", tags=["Subscriptions"])

# Note: Authentication routes have been moved to the separate auth service
# running on port 8001. The scheduler service still uses the auth middleware
# for validating JWT tokens on protected routes.
