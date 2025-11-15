from fastapi import FastAPI
from app.controllers import task_controller
from app.controllers import health_controller
from app.models.base import Base
from db.engine import engine
from app import tasks
from app.celery import scheduler

# Create tables if they do not exist
Base.metadata.create_all(bind=engine)

# Create the FastAPI application	
app = FastAPI()

# Include each router with a specific prefix and tags for better organization
app.include_router(health_controller.router, prefix="", tags=["Health"])
app.include_router(task_controller.router, prefix="/tasks", tags=["Tasks"])
