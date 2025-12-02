"""
CORS middleware configuration for the Scheduler API.

This module centralizes CORS setup so it can be reused and kept
separate from application bootstrap logic.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.environment import get_frontend_url


def cors(app: FastAPI) -> None:
    """
    Configure CORS middleware on the given FastAPI app.

    Args:
        app: FastAPI application instance.
    """

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list([get_frontend_url(), "http://localhost:3000", "http://localhost:8001"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
