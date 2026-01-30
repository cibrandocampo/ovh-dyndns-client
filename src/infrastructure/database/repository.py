from datetime import datetime, timezone
from typing import List, Optional

from pydantic import IPvAnyAddress, SecretStr
from sqlalchemy.orm import Session

from domain.hostconfig import HostConfig
from application.ports import IpStateStore, HostsRepository
from .models import Host, State, History, User, Settings
from .database import get_db_session


class SqliteRepository(IpStateStore, HostsRepository):
    """SQLite-based implementation of IpStateStore and HostsRepository."""

    # IpStateStore implementation

    def get_ip(self) -> Optional[IPvAnyAddress]:
        """Get the stored IP address from the database."""
        with get_db_session() as db:
            state = db.query(State).filter(State.id == 1).first()
            if state and state.current_ip:
                return IPvAnyAddress(state.current_ip)
            return None

    def set_ip(self, ip: IPvAnyAddress) -> None:
        """Store the current IP address in the database."""
        with get_db_session() as db:
            state = db.query(State).filter(State.id == 1).first()
            ip_str = str(ip)
            now = datetime.now(timezone.utc)

            if state:
                old_ip = state.current_ip
                state.current_ip = ip_str
                state.last_check = now
            else:
                old_ip = None
                state = State(id=1, current_ip=ip_str, last_check=now)
                db.add(state)

            # Log IP change in history
            if old_ip != ip_str:
                history = History(
                    ip=ip_str,
                    action="ip_changed",
                    details=f"IP changed from {old_ip} to {ip_str}"
                )
                db.add(history)

    # HostsRepository implementation

    def get_hosts(self) -> List[HostConfig]:
        """Get all hosts from the database as HostConfig objects."""
        with get_db_session() as db:
            hosts = db.query(Host).all()
            return [
                HostConfig(
                    hostname=host.hostname,
                    username=host.username,
                    password=SecretStr(host.password)
                )
                for host in hosts
            ]

    # Extended methods for API

    def get_all_hosts(self) -> List[dict]:
        """Get all hosts with full details for API."""
        with get_db_session() as db:
            hosts = db.query(Host).all()
            return [
                {
                    "id": host.id,
                    "hostname": host.hostname,
                    "username": host.username,
                    "last_update": host.last_update.isoformat() if host.last_update else None,
                    "last_status": host.last_status,
                    "last_error": host.last_error,
                    "created_at": host.created_at.isoformat() if host.created_at else None
                }
                for host in hosts
            ]

    def get_host_by_id(self, host_id: int) -> Optional[dict]:
        """Get a single host by ID."""
        with get_db_session() as db:
            host = db.query(Host).filter(Host.id == host_id).first()
            if not host:
                return None
            return {
                "id": host.id,
                "hostname": host.hostname,
                "username": host.username,
                "last_update": host.last_update.isoformat() if host.last_update else None,
                "last_status": host.last_status,
                "last_error": host.last_error,
                "created_at": host.created_at.isoformat() if host.created_at else None
            }

    def create_host(self, hostname: str, username: str, password: str) -> dict:
        """Create a new host."""
        with get_db_session() as db:
            host = Host(
                hostname=hostname,
                username=username,
                password=password
            )
            db.add(host)
            db.flush()

            history = History(
                action="host_created",
                hostname=hostname,
                details=f"Host {hostname} created"
            )
            db.add(history)

            return {
                "id": host.id,
                "hostname": host.hostname,
                "username": host.username,
                "last_update": None,
                "last_status": None,
                "last_error": None,
                "created_at": host.created_at.isoformat() if host.created_at else None
            }

    def update_host(self, host_id: int, hostname: str = None, username: str = None, password: str = None) -> Optional[dict]:
        """Update an existing host."""
        with get_db_session() as db:
            host = db.query(Host).filter(Host.id == host_id).first()
            if not host:
                return None

            if hostname is not None:
                host.hostname = hostname
            if username is not None:
                host.username = username
            if password is not None:
                host.password = password

            history = History(
                action="host_updated",
                hostname=host.hostname,
                details=f"Host {host.hostname} updated"
            )
            db.add(history)

            return {
                "id": host.id,
                "hostname": host.hostname,
                "username": host.username,
                "last_update": host.last_update.isoformat() if host.last_update else None,
                "last_status": host.last_status,
                "last_error": host.last_error,
                "created_at": host.created_at.isoformat() if host.created_at else None
            }

    def delete_host(self, host_id: int) -> bool:
        """Delete a host by ID."""
        with get_db_session() as db:
            host = db.query(Host).filter(Host.id == host_id).first()
            if not host:
                return False

            hostname = host.hostname
            db.delete(host)

            history = History(
                action="host_deleted",
                hostname=hostname,
                details=f"Host {hostname} deleted"
            )
            db.add(history)

            return True

    def update_host_status(self, hostname: str, success: bool, error: str = None) -> None:
        """Update the status of a host after a DNS update attempt."""
        with get_db_session() as db:
            host = db.query(Host).filter(Host.hostname == hostname).first()
            if host:
                host.last_update = datetime.now(timezone.utc)
                host.last_status = success
                host.last_error = error

                action = "host_updated" if success else "host_failed"
                history = History(
                    action=action,
                    hostname=hostname,
                    details=error if error else "DNS update successful"
                )
                db.add(history)

    # State methods

    def get_state(self) -> dict:
        """Get the current state (IP and last check time)."""
        with get_db_session() as db:
            state = db.query(State).filter(State.id == 1).first()
            if state:
                return {
                    "current_ip": state.current_ip,
                    "last_check": state.last_check.isoformat() if state.last_check else None
                }
            return {"current_ip": None, "last_check": None}

    # History methods

    def get_history(self, limit: int = 50, offset: int = 0) -> List[dict]:
        """Get history entries with pagination."""
        with get_db_session() as db:
            entries = db.query(History).order_by(
                History.timestamp.desc()
            ).offset(offset).limit(limit).all()

            return [
                {
                    "id": entry.id,
                    "ip": entry.ip,
                    "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                    "action": entry.action,
                    "hostname": entry.hostname,
                    "details": entry.details
                }
                for entry in entries
            ]

    def get_history_count(self) -> int:
        """Get total count of history entries."""
        with get_db_session() as db:
            return db.query(History).count()

    # User methods

    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Get a user by username."""
        with get_db_session() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return None
            return {
                "id": user.id,
                "username": user.username,
                "password_hash": user.password_hash,
                "must_change_password": user.must_change_password
            }

    def create_user(self, username: str, password_hash: str) -> dict:
        """Create a new user."""
        with get_db_session() as db:
            user = User(username=username, password_hash=password_hash)
            db.add(user)
            db.flush()
            return {
                "id": user.id,
                "username": user.username,
                "password_hash": user.password_hash,
                "must_change_password": user.must_change_password
            }

    def user_exists(self, username: str) -> bool:
        """Check if a user exists."""
        with get_db_session() as db:
            return db.query(User).filter(User.username == username).first() is not None

    def get_user_must_change_password(self, username: str) -> bool:
        """Check if user must change password."""
        with get_db_session() as db:
            user = db.query(User).filter(User.username == username).first()
            return user.must_change_password if user else False

    def update_user_password(self, username: str, password_hash: str) -> bool:
        """Update user password and mark as changed."""
        with get_db_session() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return False
            user.password_hash = password_hash
            user.must_change_password = False
            return True

    # Settings methods

    def get_settings(self) -> dict:
        """Get application settings."""
        with get_db_session() as db:
            settings = db.query(Settings).filter(Settings.id == 1).first()
            if settings:
                return {
                    "update_interval": settings.update_interval,
                    "logger_level": settings.logger_level
                }
            return {"update_interval": 300, "logger_level": "INFO"}

    def update_settings(self, update_interval: int = None, logger_level: str = None) -> dict:
        """Update application settings."""
        with get_db_session() as db:
            settings = db.query(Settings).filter(Settings.id == 1).first()
            if not settings:
                settings = Settings(id=1)
                db.add(settings)

            if update_interval is not None:
                settings.update_interval = update_interval
            if logger_level is not None:
                settings.logger_level = logger_level

            history = History(
                action="settings_updated",
                details=f"Settings updated: interval={settings.update_interval}, level={settings.logger_level}"
            )
            db.add(history)

            return {
                "update_interval": settings.update_interval,
                "logger_level": settings.logger_level
            }

    def init_default_settings(self) -> None:
        """Initialize default settings if they don't exist."""
        with get_db_session() as db:
            settings = db.query(Settings).filter(Settings.id == 1).first()
            if not settings:
                settings = Settings(id=1, update_interval=300, logger_level="INFO")
                db.add(settings)
