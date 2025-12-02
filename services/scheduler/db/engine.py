import logging
import os

from databases import Database
from sqlalchemy import MetaData, create_engine

from app.context.request_context import get_request_uuid
from config.environment import init

# Initialize environment variables
init()


class SQLAlchemyContextFilter(logging.Filter):
    """
    Logging filter that adds request UUID to SQLAlchemy log records.

    This filter modifies the log record's message to include the request UUID
    from context, ensuring SQL queries and engine events are traceable.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request UUID prefix to the log message."""
        request_id = get_request_uuid()
        if request_id is not None:
            # Modify the message to include request ID
            record.msg = f"[request_id={request_id}] {record.msg}"
        return True


# Configure SQLAlchemy loggers to use context filter
# This ensures SQL queries and engine events include the request UUID
_context_filter = SQLAlchemyContextFilter()

# Apply filter to common SQLAlchemy logger names
# Note: filters are NOT inherited, so we attach to both base and child loggers.
_sqlalchemy_logger_names = [
    "sqlalchemy",
    "sqlalchemy.engine",
    "sqlalchemy.engine.Engine",
    "sqlalchemy.pool",
    "sqlalchemy.orm",
]

for logger_name in _sqlalchemy_logger_names:
    logger = logging.getLogger(logger_name)
    logger.addFilter(_context_filter)
    # Don't override existing level if it was already more verbose
    if logger.level == logging.NOTSET:
        logger.setLevel(logging.INFO)

# Retrieve the DATABASE_URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./test.db"

# Create engine and metadata
database = Database(DATABASE_URL)
engine = create_engine(DATABASE_URL, echo=True)
metadata = MetaData()
