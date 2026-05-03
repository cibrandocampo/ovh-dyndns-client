import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, Host

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

    _engine = create_engine(database_url, connect_args={"check_same_thread": False})

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


def has_encrypted_hosts() -> bool:
    """True if any row in `hosts` carries the encrypted-password marker.

    Used at startup to fail-fast when the encryption key is missing but
    the database still holds Fernet ciphertext from a previous boot.
    """
    from infrastructure.crypto import ENCRYPTED_PREFIX

    with get_db_session() as db:
        return db.query(Host).filter(Host.password.like(f"{ENCRYPTED_PREFIX}%")).first() is not None


def migrate_plaintext_passwords() -> int:
    """Encrypt any host password still stored as plaintext.

    Idempotent: rows already prefixed with `enc:v1:` are skipped, so it is
    safe to call on every boot. Intended to run after `init_db()` and
    before any code that reads `Host.password`.

    Returns the number of rows migrated.
    """
    from infrastructure.crypto import encrypt_password, is_encrypted

    migrated = 0
    with get_db_session() as db:
        hosts = db.query(Host).all()
        for host in hosts:
            if not is_encrypted(host.password):
                host.password = encrypt_password(host.password)
                migrated += 1
    return migrated
