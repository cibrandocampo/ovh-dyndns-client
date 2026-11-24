import functools
import threading
import time

import uvicorn

from api.main import app, init_admin_user
from api.routers.settings import set_settings_change_callback
from api.routers.status import set_controller
from application.controller import UpdateDnsController
from infrastructure.clients.ipify_client import IpifyClient
from infrastructure.clients.ovh_client import OvhClient
from infrastructure.database import (
    SqliteRepository,
    has_encrypted_hosts,
    init_db,
    migrate_plaintext_passwords,
)
from infrastructure.logger import Logger
from infrastructure.secrets import (
    encryption_key_exists,
    get_or_create_encryption_key,
    get_or_create_jwt_secret,
)

# Initialize logger
logger = Logger.get_logger()


DEFAULT_UPDATE_INTERVAL = 300


class SchedulerThread(threading.Thread):
    """Background thread that runs the DNS update scheduler."""

    def __init__(self, controller, repository):
        super().__init__(daemon=True)
        self.controller = controller
        self.repository = repository
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()
        self._interval = DEFAULT_UPDATE_INTERVAL

    def _read_interval(self):
        """Refresh the interval from the database, keeping the last one on error."""
        try:
            interval = self.repository.get_settings().get("update_interval", DEFAULT_UPDATE_INTERVAL)
        except Exception:
            logger.exception("Could not read settings, keeping the current update interval")
            return
        if interval != self._interval:
            self._interval = interval
            logger.info(f"Update interval set to {interval} seconds")

    def run(self):
        logger.info("Scheduler thread started")

        while not self._stop_event.is_set():
            self._read_interval()

            try:
                logger.info("Executing DNS update controller")
                self.controller.handler()
                logger.info("DNS update completed successfully")
            except Exception:
                logger.exception("Controller execution failed")

            # Sleep until the interval elapses. A wake-up (settings change)
            # re-reads the interval and recomputes the deadline from the last
            # run, so a shorter interval applies right away.
            last_run = time.monotonic()
            while not self._stop_event.is_set():
                remaining = last_run + self._interval - time.monotonic()
                if remaining <= 0:
                    break
                if self._wake_event.wait(remaining):
                    self._wake_event.clear()
                    self._read_interval()

    def wake(self):
        """Re-read the interval now instead of after the current wait."""
        self._wake_event.set()

    def stop(self):
        self._stop_event.set()
        self._wake_event.set()


def on_settings_change(new_settings, scheduler=None):
    """Callback when settings are changed via API."""
    logger.info(f"Settings changed: {new_settings}")
    if scheduler is not None:
        scheduler.wake()


def launch_scheduler(controller, repository):
    """Start the scheduler thread, unless `DISABLE_SCHEDULER=1` is set.

    Returns the started thread, or `None` when the env var disables it.
    Extracted from `main()` so it can be unit-tested without booting the
    rest of the application.
    """
    import os

    if os.getenv("DISABLE_SCHEDULER") == "1":
        logger.info("Scheduler disabled (DISABLE_SCHEDULER=1)")
        return None
    scheduler = SchedulerThread(controller, repository)
    scheduler.start()
    logger.info("Scheduler thread launched")
    return scheduler


def main():
    """Main entry point of the application."""
    logger.info("Starting OVH DynDNS client")

    # Initialize database
    logger.info("Initializing database")
    init_db()

    # Auto-generate or load persisted JWT secret (fail-fast on its own only if
    # the data dir is unwritable — handled by raising from secrets module).
    get_or_create_jwt_secret()

    # Refuse to start if there are encrypted hosts in the DB but no key file:
    # generating a new key here would silently render every existing
    # ciphertext undecryptable.
    if has_encrypted_hosts() and not encryption_key_exists():
        raise RuntimeError(
            "Encryption key is missing but encrypted hosts found in database. "
            "Restore data/.encryption_key or set ENCRYPTION_KEY env var."
        )

    # Auto-generate or load the encryption key (only reached when the
    # consistency check above passes).
    get_or_create_encryption_key()

    # Idempotent: encrypt any host password still stored as plaintext from
    # pre-encryption deployments. No-op on fresh installs and on subsequent
    # boots once everything is already migrated.
    migrated = migrate_plaintext_passwords()
    if migrated:
        logger.info(f"Encrypted {migrated} legacy plaintext host password(s)")

    # Create admin user if needed
    init_admin_user()

    # Create repository
    repository = SqliteRepository()

    # Create dependencies
    ip_provider = IpifyClient()
    dns_updater = OvhClient()

    # Create controller with SQLite repository
    controller = UpdateDnsController(
        ip_provider=ip_provider, dns_updater=dns_updater, ip_state=repository, hosts_repo=repository, logger=logger
    )

    # Set controller for API status endpoint
    set_controller(controller)

    # Start the scheduler thread (unless `DISABLE_SCHEDULER=1`, e.g. during
    # screenshot capture where a fake-credential seed must not be clobbered
    # by an immediate OVH-update tick).
    scheduler = launch_scheduler(controller, repository)

    # Settings changes wake the scheduler so a new interval applies at once
    set_settings_change_callback(functools.partial(on_settings_change, scheduler=scheduler))

    import os

    api_port = int(os.getenv("API_PORT", "8000"))

    # Start FastAPI server
    logger.info(f"Starting API server on port {api_port}")
    log_config = Logger.get_uvicorn_log_config()
    uvicorn.run(app, host="0.0.0.0", port=api_port, log_config=log_config)


if __name__ == "__main__":
    main()
