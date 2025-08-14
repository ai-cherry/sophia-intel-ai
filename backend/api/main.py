"""
Main API server for Sophia Intelligence services
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

# Import routers
from backend.api.swarm_chat import router as swarm_chat_router

# Import any existing routers
try:
    from apps.api.routers.sales_router import router as sales_router
    has_sales_router = True
except ImportError:
    has_sales_router = False

# Create FastAPI application
app = FastAPI(
    title="Sophia Intelligence API",
    description="API server for Sophia Intelligence services including Swarm chat interface",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(swarm_chat_router)

# Add sales router if available
if has_sales_router:
    app.include_router(sales_router)


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint that returns API information"""
    return {
        "name": "Sophia Intelligence API",
        "version": "1.0.0",
        "services": {
            "swarm_chat": "/swarm-chat",
            "sales_router": "/sales" if has_sales_router else "not available"
        }
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8001, reload=True)
