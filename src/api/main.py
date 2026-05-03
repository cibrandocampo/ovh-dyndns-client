from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from infrastructure.database import SqliteRepository

from .auth import get_admin_credentials, hash_password

# Module-level limiter, defined BEFORE the router import below so that
# `routers/auth.py` can `from api.main import limiter` while this module
# is still mid-import. Counters live in-memory and reset on process
# restart; sufficient for a single-instance self-hosted service.
limiter = Limiter(key_func=get_remote_address)

# Routers must be imported AFTER `limiter` is defined — they reference it
# at module top level via `@limiter.limit(...)` decorators.
from .routers import auth_router, history_router, hosts_router, settings_router, status_router  # noqa: E402


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(title="OVH DynDNS Client", description="API for managing OVH DynDNS hosts", version="1.0.0")

    # Wire the rate limiter into the app: state.limiter is the convention slowapi
    # looks up from `Request.app.state.limiter`, and the exception handler turns
    # `RateLimitExceeded` into a clean HTTP 429 response with retry headers.
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
        print(
            f"Admin user '{username}' created with default password. User will be required to change it on first login."
        )
    else:
        print(f"Admin user '{username}' already exists.")

    # Initialize default settings
    repository.init_default_settings()


app = create_app()
