#!/usr/bin/env python3
"""Seed the dev database with realistic fixtures for screenshots and demo.

Refuses to overwrite an existing dataset unless ``--reset`` is passed,
which wipes hosts/history/state/settings/users in dependency-safe order
before seeding. Persisted secrets under ``data/`` (``.jwt_secret``,
``.encryption_key``) are NOT touched.

Run inside the dev container after the ``../scripts:/scripts:ro`` mount
is in place::

    python /scripts/seed.py --reset
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# When invoked as `python /scripts/seed.py` inside the dev container, /app
# is already on PYTHONPATH (set by the compose env). We insert it again so
# the script also works when imported directly by the unit tests, which do
# not pre-set the variable.
sys.path.insert(0, str(Path("/app")))

from api.auth import hash_password  # noqa: E402
from infrastructure.database import SqliteRepository, init_db  # noqa: E402
from infrastructure.database.database import get_db_session  # noqa: E402
from infrastructure.database.models import History, Host, Settings, State, User  # noqa: E402

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
PUBLIC_IP = "1.2.3.4"

# (hostname, username, password, last_status, last_error, age_minutes)
HOSTS: list[tuple] = [
    ("home.example.com", "ovh-user-home", "ovh-pass-1", True, None, 5),
    ("vpn.example.com", "ovh-user-vpn", "ovh-pass-2", True, None, 10),
    ("files.example.com", "ovh-user-files", "ovh-pass-3", True, None, 60),
    (
        "nas.example.com",
        "ovh-user-nas",
        "ovh-pass-4",
        False,
        "Authentication failed - check username/password",
        30,
    ),
    ("media.example.com", "ovh-user-media", "ovh-pass-5", None, None, None),
]

# Synthetic past events to fill the history pages. Mix of ip_changed,
# host_updated (success), host_failed, host_created/deleted, settings.
# (action, hostname, ip, details, age_hours)
HISTORY_EVENTS: list[tuple] = [
    ("ip_changed", None, "192.168.0.10", "IP changed from None to 192.168.0.10", 168),
    ("host_updated", "home.example.com", None, "DNS update successful", 167),
    ("host_failed", "nas.example.com", None, "HTTP 401: Unauthorized", 165),
    ("host_updated", "vpn.example.com", None, "DNS update successful", 100),
    ("settings_updated", None, None, "Settings updated: interval=300, level=INFO", 90),
    ("ip_changed", None, "10.20.30.40", "IP changed from 192.168.0.10 to 10.20.30.40", 80),
    ("host_updated", "home.example.com", None, "DNS update successful", 79),
    ("host_updated", "files.example.com", None, "DNS update successful", 78),
    (
        "host_failed",
        "nas.example.com",
        None,
        "Hostname not found - check DynHost configuration in OVH",
        75,
    ),
    ("ip_changed", None, "203.0.113.42", "IP changed from 10.20.30.40 to 203.0.113.42", 50),
    ("host_updated", "home.example.com", None, "DNS update successful", 49),
    ("host_updated", "vpn.example.com", None, "DNS update successful", 48),
    ("host_updated", "files.example.com", None, "DNS update successful", 47),
    ("host_failed", "nas.example.com", None, "Authentication failed - check username/password", 46),
    ("host_created", "files.example.com", None, "Host files.example.com created", 30),
    ("host_deleted", "old-server.example.com", None, "Host old-server.example.com deleted", 25),
    ("ip_changed", None, PUBLIC_IP, f"IP changed from 203.0.113.42 to {PUBLIC_IP}", 1),
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _has_data() -> bool:
    """True when any of hosts/history/state/users already has at least one row."""
    with get_db_session() as db:
        return any(db.query(model).first() is not None for model in (Host, History, State, User))


def _wipe() -> None:
    """Delete every domain row in dependency-safe order. Persisted secrets stay."""
    with get_db_session() as db:
        db.query(History).delete()
        db.query(Host).delete()
        db.query(State).delete()
        db.query(Settings).delete()
        db.query(User).delete()


def _seed_admin() -> None:
    with get_db_session() as db:
        db.add(
            User(
                username=ADMIN_USERNAME,
                password_hash=hash_password(ADMIN_PASSWORD),
                must_change_password=False,
            )
        )


def _seed_hosts(now: datetime, repo: SqliteRepository) -> None:
    for hostname, username, password, status, error, age in HOSTS:
        repo.create_host(hostname, username, password)
        if status is not None:
            repo.update_host_status(hostname, status, error)
            # `update_host_status` sets last_update=now(); override to a
            # controlled past timestamp so the dashboard shows realistic
            # "X minutes ago" wording.
            with get_db_session() as db:
                row = db.query(Host).filter_by(hostname=hostname).first()
                row.last_update = now - timedelta(minutes=age)


def _seed_history(now: datetime) -> None:
    with get_db_session() as db:
        for action, hostname, ip, details, age in HISTORY_EVENTS:
            db.add(
                History(
                    action=action,
                    hostname=hostname,
                    ip=ip,
                    details=details,
                    timestamp=now - timedelta(hours=age),
                )
            )


def _refresh_state_last_check(now: datetime) -> None:
    """Bring `state.last_check` forward to now so the dashboard shows a recent check."""
    with get_db_session() as db:
        row = db.query(State).filter_by(id=1).first()
        if row:
            row.last_check = now


def seed(reset: bool = False) -> None:
    """Populate the database with the demo fixture set."""
    init_db()

    if _has_data():
        if not reset:
            print(
                "Refusing to seed: database already contains data. "
                "Re-run with --reset to wipe and re-seed, or remove "
                "data/dyndns.db first.",
                file=sys.stderr,
            )
            sys.exit(1)
        _wipe()

    repo = SqliteRepository()
    now = _utcnow()

    _seed_admin()
    repo.init_default_settings()
    repo.set_ip(PUBLIC_IP)  # writes State row + a "ip_changed" history entry
    _seed_hosts(now, repo)  # 5 host_created + 4 host_updated/host_failed entries
    _seed_history(now)  # synthetic past events
    _refresh_state_last_check(now)

    print(
        f"Seeded: 1 admin, {len(HOSTS)} hosts, "
        f"{len(HISTORY_EVENTS)} synthetic history events (plus the rows "
        f"emitted by repo calls), public IP {PUBLIC_IP}."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed the dev database with demo fixtures (5 hosts, mixed health, ~25 history rows)."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Wipe existing hosts/history/state/settings/users before seeding.",
    )
    seed(reset=parser.parse_args().reset)


if __name__ == "__main__":
    main()
