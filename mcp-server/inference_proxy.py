"""
FastAPI inference proxy for SOPHIA Intel Lambda Labs GH200 servers
"""
from fastapi import FastAPI, Depends, HTTPException, Request, status
import httpx
import os
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
PRIMARY_URL = os.getenv("LAMBDA_PRIMARY_URL", "http://192.222.51.223:8000")
SECONDARY_URL = os.getenv("LAMBDA_SECONDARY_URL", "http://192.222.50.242:8000")
API_KEY = os.getenv("INFERENCE_API_KEY", "sophia-inference-key")

app = FastAPI(
    title="SOPHIA Intel Inference Proxy",
    description="Proxy for Lambda Labs GH200 inference servers",
    version="1.0.0"
)

def api_key_auth(request: Request):
    """Simple API key authentication"""
    provided = request.headers.get("X-API-Key")
    if provided != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid API key"
        )

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "OK",
        "service": "SOPHIA Intel Inference Proxy",
        "primary_server": PRIMARY_URL,
        "secondary_server": SECONDARY_URL
    }

@app.post("/infer", dependencies=[Depends(api_key_auth)])
async def infer(payload: Dict[str, Any]):
    """
    Inference endpoint with automatic failover
    Tries primary server first, falls back to secondary
    """
    try:
        # Try primary server first
        async with httpx.AsyncClient(timeout=30) as client:
            logger.info(f"Sending inference request to primary server: {PRIMARY_URL}")
            resp = await client.post(f"{PRIMARY_URL}/infer", json=payload)
            resp.raise_for_status()
            result = resp.json()
            result["server_used"] = "primary"
            return result
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.warning(f"Primary server failed: {e}, trying secondary server")
        
        try:
            # Fallback to secondary server
            async with httpx.AsyncClient(timeout=30) as client:
                logger.info(f"Sending inference request to secondary server: {SECONDARY_URL}")
                resp = await client.post(f"{SECONDARY_URL}/infer", json=payload)
                resp.raise_for_status()
                result = resp.json()
                result["server_used"] = "secondary"
                return result
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.error(f"Both servers failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Both inference servers are unavailable"
            )

@app.get("/servers/status")
async def server_status():
    """Check status of both inference servers"""
    status_info = {
        "primary": {"url": PRIMARY_URL, "status": "unknown"},
        "secondary": {"url": SECONDARY_URL, "status": "unknown"}
    }
    
    # Check primary server
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{PRIMARY_URL}/health")
            status_info["primary"]["status"] = "healthy" if resp.status_code == 200 else "unhealthy"
    except:
        status_info["primary"]["status"] = "unreachable"
    
    # Check secondary server
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{SECONDARY_URL}/health")
            status_info["secondary"]["status"] = "healthy" if resp.status_code == 200 else "unhealthy"
    except:
        status_info["secondary"]["status"] = "unreachable"
    
    return status_info

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))
