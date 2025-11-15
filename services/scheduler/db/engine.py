import os
from sqlalchemy import create_engine, MetaData
from databases import Database
from config.environment import init

# Initialize environment variables
init()

# Retrieve the DATABASE_URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./test.db"

# Create engine and metadata
database = Database(DATABASE_URL)
engine = create_engine(DATABASE_URL, echo=True)
metadata = MetaData()