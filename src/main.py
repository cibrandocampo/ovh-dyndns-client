import threading
import time
import uvicorn

from infrastructure.database import init_db, SqliteRepository
from infrastructure.logger import Logger
from infrastructure.clients.ipify_client import IpifyClient
from infrastructure.clients.ovh_client import OvhClient
from application.controller import UpdateDnsController
from api.main import app, init_admin_user
from api.routers.status import set_controller
from api.routers.settings import set_settings_change_callback

# Initialize logger
logger = Logger.get_logger()


class SchedulerThread(threading.Thread):
    """Background thread that runs the DNS update scheduler."""

    def __init__(self, controller, repository):
        super().__init__(daemon=True)
        self.controller = controller
        self.repository = repository
        self._stop_event = threading.Event()
        self._interval = None

    def run(self):
        logger.info("Scheduler thread started")

        while not self._stop_event.is_set():
            # Get current interval from database
            settings = self.repository.get_settings()
            interval = settings.get("update_interval", 300)

            if self._interval != interval:
                self._interval = interval
                logger.info(f"Update interval set to {interval} seconds")

            try:
                logger.info("Executing DNS update controller")
                self.controller.handler()
                logger.info("DNS update completed successfully")
            except RuntimeError as e:
                logger.error(f"Controller execution failed: {e}")

            # Wait for the interval, but check for stop event periodically
            for _ in range(interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)

    def stop(self):
        self._stop_event.set()


def on_settings_change(new_settings):
    """Callback when settings are changed via API."""
    logger.info(f"Settings changed: {new_settings}")


def main():
    """Main entry point of the application."""
    logger.info("Starting OVH DynDNS client")

    # Initialize database
    logger.info("Initializing database")
    init_db()

    # Create admin user if needed
    init_admin_user()

    # Create repository
    repository = SqliteRepository()

    # Create dependencies
    ip_provider = IpifyClient()
    dns_updater = OvhClient()

    # Create controller with SQLite repository
    controller = UpdateDnsController(
        ip_provider=ip_provider,
        dns_updater=dns_updater,
        ip_state=repository,
        hosts_repo=repository,
        logger=logger
    )

    # Set controller for API status endpoint
    set_controller(controller)

    # Set settings change callback
    set_settings_change_callback(on_settings_change)

    # Start scheduler in background thread
    scheduler = SchedulerThread(controller, repository)
    scheduler.start()
    logger.info("Scheduler thread launched")

    # Get API port from environment
    import os
    api_port = int(os.getenv("API_PORT", "8000"))

    # Start FastAPI server
    logger.info(f"Starting API server on port {api_port}")
    uvicorn.run(app, host="0.0.0.0", port=api_port, log_level="info")


if __name__ == "__main__":
    main()
