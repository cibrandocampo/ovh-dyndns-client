from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    must_change_password = Column(Boolean, default=True)


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, default=1)
    update_interval = Column(Integer, default=300)
    logger_level = Column(String, default="INFO")


class Host(Base):
    __tablename__ = "hosts"

    id = Column(Integer, primary_key=True)
    hostname = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    last_update = Column(DateTime, nullable=True)
    last_status = Column(Boolean, nullable=True)
    last_error = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class State(Base):
    __tablename__ = "state"

    id = Column(Integer, primary_key=True, default=1)
    current_ip = Column(String, nullable=True)
    last_check = Column(DateTime, nullable=True)


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True)
    ip = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    action = Column(String)
    hostname = Column(String, nullable=True)
    details = Column(String, nullable=True)
