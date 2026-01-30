import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base

DEFAULT_DATABASE_PATH = "/app/data/dyndns.db"

_engine = None
_SessionLocal = None


def get_database_url() -> str:
    db_path = os.getenv("DATABASE_PATH", DEFAULT_DATABASE_PATH)
    return f"sqlite:///{db_path}"


def init_db() -> None:
    """Initialize the database engine and create tables if they don't exist."""
    global _engine, _SessionLocal

    database_url = get_database_url()

    # Ensure data directory exists
    db_path = os.getenv("DATABASE_PATH", DEFAULT_DATABASE_PATH)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    _engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False}
    )

    Base.metadata.create_all(bind=_engine)

    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_db() -> Session:
    """Get a database session. Must call init_db() first."""
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _SessionLocal()


@contextmanager
def get_db_session():
    """Context manager for database sessions with automatic cleanup."""
    db = get_db()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
