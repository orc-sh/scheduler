from fastapi import FastAPI

from app.celery import scheduler
from app.middleware.cors_middleware import cors
from app.middleware.middleware_wrapper import middleware_wrapper
from app.routes import router
from config.environment import init

# Initialize environment variables FIRST before importing modules that need them
init()

# Configure Celery to autodiscover tasks
scheduler.autodiscover_tasks(["app.tasks"], force=True)

# Create the FastAPI application
app = FastAPI(title="Scheduler API", version="1.0.0")

# CORS
cors(app)

# middlewares
http_middleware = app.middleware("http")
http_middleware(middleware_wrapper)

# routes
router(app)
