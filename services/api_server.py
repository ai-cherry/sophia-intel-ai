from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from services.api.speech_controller import router as speech_router
from services.orchestrator import Orchestrator
from services.common.env_schema import get_config

# Load configuration
config = get_config()

app = FastAPI(
    title="SOPHIA Intel API",
    description="AI Command Center with Orchestration and Voice Capabilities", 
    version="1.0.0"
)

# Configure CORS
cors_origins = config.CORS_ORIGINS.split(",") if hasattr(config, 'CORS_ORIGINS') else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(speech_router)

# Initialize orchestrator
orchestrator = Orchestrator()

REQS = Counter("api_requests_total", "API requests", ["route"])
LAT = Histogram("api_latency_seconds", "API latency", ["route"])


# Request models
class OrchestrationRequest(BaseModel):
    request_type: str = Field(
        ..., description="Type of request: code, chat, gpu, memory, health"
    )
    payload: Dict[str, Any] = Field(..., description="Request payload")
    timeout: Optional[int] = Field(
        default=300, description="Request timeout in seconds"
    )
    retries: Optional[int] = Field(default=3, description="Number of retry attempts")


@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "ok", 
        "environment": config.ENV,
        "features": {
            "voice": config.FEATURE_VOICE_ENABLED,
            "research": config.FEATURE_RESEARCH_ENABLED,
            "code": config.FEATURE_CODE_GENERATION,
            "memory": config.FEATURE_MEMORY_ENABLED
        },
        "orchestrator": orchestrator.get_stats()
    }


@app.get("/metrics")
def metrics():
    data = generate_latest()  # type: ignore
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.post("/api/orchestration")
async def orchestrate_request(request: OrchestrationRequest):
    """
    Main orchestration endpoint that routes requests to appropriate services.
    """
    REQS.labels(route="/api/orchestration").inc()

    with LAT.labels(route="/api/orchestration").time():
        try:
            result = await orchestrator.handle_request(
                request_type=request.request_type,
                payload=request.payload,
                timeout=request.timeout,
                retries=request.retries,
            )
            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/orchestration/stats")
async def get_orchestrator_stats():
    """Get orchestrator performance statistics."""
    return orchestrator.get_stats()


@app.get("/api/orchestration/health")
async def orchestration_health():
    """Get health status of all orchestrated services."""
    result = await orchestrator.handle_request(
        request_type="health", payload={}, timeout=30, retries=1
    )
    return result
