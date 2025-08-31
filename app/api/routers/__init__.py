"""
API Routers for Sophia Intel AI
Modular organization of API endpoints.
"""

from .teams import router as teams_router
from .swarms import router as swarms_router

# Create placeholder routers for missing modules
from fastapi import APIRouter

workflows_router = APIRouter(prefix="/workflows", tags=["workflows"])
memory_router = APIRouter(prefix="/memory", tags=["memory"])
search_router = APIRouter(prefix="/search", tags=["search"])
indexing_router = APIRouter(prefix="/indexing", tags=["indexing"])
health_router = APIRouter(prefix="/health", tags=["health"])

__all__ = [
    "teams_router",
    "swarms_router",
    "workflows_router", 
    "memory_router",
    "search_router",
    "indexing_router",
    "health_router"
]