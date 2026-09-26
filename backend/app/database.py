"""SQLite database engine and session factory for the application."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # Required for SQLite when the same connection may be used across the
    # threads FastAPI uses to run sync path operations.
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def get_db():
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Called once at application startup."""
    # Imported here (not at module load time) so app.models registers its
    # tables on Base.metadata without creating a circular import with
    # app.database at import time.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)