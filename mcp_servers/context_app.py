"""
Standalone Context Server App for Deployment
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .context_server import router
from .common.metrics import init_metrics, register_healthz_if_missing

# Create FastAPI app
app = FastAPI(
    title="SOPHIA Context Server v4.2",
    description="Code indexing and RAG service",
    version="4.2.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the context router
app.include_router(router, prefix="", tags=["Context"])

# v4.2 platform invariants
register_healthz_if_missing(app, "sophia-context-mcp", "4.2.0")
init_metrics(app, "sophia-context-mcp", "4.2.0")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SOPHIA Context Server v4.2",
        "version": "4.2.0",
        "status": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

