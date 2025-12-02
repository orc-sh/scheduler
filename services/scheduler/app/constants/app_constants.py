"""
Application-wide constants (URLs, prefixes, etc.).
"""

import os

BACKEND_BASE_URL = os.getenv("BACKEND_URL", "").rstrip("/")
FRONTEND_BASE_URL = os.getenv("FRONTEND_URL", "").rstrip("/")
