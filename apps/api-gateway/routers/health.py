"""Health check router"""
from fastapi import APIRouter
from core.env_schema import validate_environment

router = APIRouter()
config = validate_environment()

@router.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "service": "sophia-api-gateway",
        "status": "healthy",
        "version": "1.0.0",
        "environment": config.env,
        "features": ["orchestration", "speech", "health"]
    }
