from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.celery import scheduler
from app.controllers import (
    health_controller,
    notification_controller,
    project_controller,
    scheduler_controller,
    subscription_controller,
    url_controller,
    url_receiver_controller,
)
from config.environment import get_frontend_url, init

# Initialize environment variables FIRST before importing modules that need them
init()

# Configure Celery to autodiscover tasks
scheduler.autodiscover_tasks(["app.tasks"], force=True)

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
app.include_router(url_controller.router, prefix="/api/urls", tags=["URLs"])
app.include_router(scheduler_controller.router, prefix="/api/schedules", tags=["Schedules"])
app.include_router(url_receiver_controller.router, prefix="/api/webhooks", tags=["URL Receiver"])
app.include_router(notification_controller.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(subscription_controller.router, prefix="/api/subscriptions", tags=["Subscriptions"])
