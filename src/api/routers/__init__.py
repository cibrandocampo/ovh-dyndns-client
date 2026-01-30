from .auth import router as auth_router
from .hosts import router as hosts_router
from .status import router as status_router
from .history import router as history_router
from .settings import router as settings_router

__all__ = ["auth_router", "hosts_router", "status_router", "history_router", "settings_router"]
