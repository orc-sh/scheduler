import os

from dotenv import load_dotenv


# Load environment variables from the .env file
def init():
    load_dotenv()


def get_supabase_url() -> str:
    """Get Supabase project URL from environment"""
    url = os.getenv("SUPABASE_URL")
    if not url:
        raise ValueError("SUPABASE_URL environment variable is not set")
    return url


def get_supabase_key() -> str:
    """Get Supabase anon/public key from environment"""
    key = os.getenv("SUPABASE_KEY")
    if not key:
        raise ValueError("SUPABASE_KEY environment variable is not set")
    return key


def get_supabase_jwt_secret() -> str:
    """Get Supabase JWT secret for token verification"""
    secret = os.getenv("SUPABASE_JWT_SECRET")
    if not secret:
        raise ValueError("SUPABASE_JWT_SECRET environment variable is not set")
    return secret


def get_frontend_url() -> str:
    """Get frontend URL for CORS and redirects"""
    return os.getenv("FRONTEND_URL", "http://localhost:5173")
