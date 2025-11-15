from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import tasks  # noqa: F401
from app.celery import scheduler  # noqa: F401
from app.controllers import auth_controller, health_controller, task_controller
from app.models.base import Base
from config.environment import get_frontend_url
from db.engine import engine

# Create tables if they do not exist
Base.metadata.create_all(bind=engine)

# Create the FastAPI application
app = FastAPI(title="Scheduler API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        get_frontend_url(),
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include each router with a specific prefix and tags for better organization
app.include_router(health_controller.router, prefix="", tags=["Health"])
app.include_router(auth_controller.router, prefix="/auth", tags=["Authentication"])
app.include_router(task_controller.router, prefix="/tasks", tags=["Tasks"])
