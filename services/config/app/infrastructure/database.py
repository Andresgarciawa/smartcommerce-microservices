"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import os
from typing import Generator

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL_CONFIG",
    "postgresql://postgres:postgres@localhost:5432/config_db"
)

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=int(os.getenv("DB_POOL_SIZE", 20)),
    max_overflow=int(os.getenv("DB_POOL_MAX_OVERFLOW", 40)),
    pool_pre_ping=True,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    from app.infrastructure.models import Base
    Base.metadata.create_all(bind=engine)
