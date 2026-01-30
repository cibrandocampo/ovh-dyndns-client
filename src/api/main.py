import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from .routers import auth_router, hosts_router, status_router, history_router, settings_router
from .auth import hash_password, get_admin_credentials
from infrastructure.database import init_db, SqliteRepository


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="OVH DynDNS Client",
        description="API for managing OVH DynDNS hosts",
        version="1.0.0"
    )

    # Include routers
    application.include_router(auth_router)
    application.include_router(hosts_router)
    application.include_router(status_router)
    application.include_router(history_router)
    application.include_router(settings_router)

    # Mount static files
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        application.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @application.get("/", include_in_schema=False)
    async def root():
        """Serve the main frontend page."""
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "OVH DynDNS Client API", "docs": "/docs"}

    @application.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    return application


def init_admin_user():
    """Create admin user if it doesn't exist."""
    username, password = get_admin_credentials()

    repository = SqliteRepository()
    if not repository.user_exists(username):
        password_hash = hash_password(password)
        repository.create_user(username, password_hash)
        print(f"Admin user '{username}' created with default password. User will be required to change it on first login.")
    else:
        print(f"Admin user '{username}' already exists.")

    # Initialize default settings
    repository.init_default_settings()


app = create_app()
