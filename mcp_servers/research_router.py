"""
Research Router for Sophia MCP Server
Exports a FastAPI router for integration with the main app
"""

from fastapi import APIRouter
from .research_server import app as research_app

# Create router from the research app
router = APIRouter()

# Add all routes from the research app to the router
for route in research_app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        # Skip the root route to avoid conflicts
        if route.path != "/":
            router.routes.append(route)

# Add a healthz route that matches the expected format
@router.get("/healthz")
async def healthz():
    """Health check endpoint for research service"""
    return {
        "status": "ok",
        "service": "sophia-research-mcp",
        "version": "4.2.0"
    }

