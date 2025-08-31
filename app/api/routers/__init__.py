"""
API Routers for Sophia Intel AI
Modular organization of API endpoints.
"""

from .teams import router as teams_router
from .workflows import router as workflows_router
from .memory import router as memory_router
from .search import router as search_router
from .indexing import router as indexing_router
from .health import router as health_router

__all__ = [
    "teams_router",
    "workflows_router", 
    "memory_router",
    "search_router",
    "indexing_router",
    "health_router"
]