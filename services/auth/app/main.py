from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.controllers import auth_controller, oauth_controller
from config.environment import get_frontend_url, init

# Initialize environment variables FIRST before importing modules that need them
init()

# Create the FastAPI application
app = FastAPI(title="Authentication Service API", version="1.0.0", port=8001)

# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        get_frontend_url(),
        "https://www.localhooks.com",
        "http://localhost:3000",  # Allow web service
        "http://localhost:8000", # Allow scheduler service
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
app.include_router(oauth_controller.router, prefix="/api/oauth", tags=["OAuth"])
app.include_router(auth_controller.router, prefix="/api/auth", tags=["Authentication"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth"}

