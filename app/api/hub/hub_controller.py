import asyncio
from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.ai_logger import logger

router = APIRouter(tags=["hub"])
templates = Jinja2Templates(directory="app/templates")

# Service registry
SERVICE_MAP = {
    "streamlit": "http://localhost:8501",
    "monitoring": "http://localhost:8002",
    "mcp_memory": "http://localhost:8001",
    "mcp_review": "http://localhost:8003",
}


async def check_service_health(service_name: str, url: str, timeout: float = 2.0) -> dict:
    """Check health of a single service"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{url}/health" if service_name != "streamlit" else url)
            return {
                "status": "healthy" if response.status_code < 400 else "unhealthy",
                "latency": response.elapsed.total_seconds() * 1000,
                "status_code": response.status_code,
            }
    except Exception as e:
        return {"status": "down", "error": str(e), "latency": 0}


async def get_service_status() -> dict:
    """Get status of all services"""
    services = {
        "api": {"port": 8005, "url": "http://localhost:8005"},
        "streamlit": {"port": 8501, "url": "http://localhost:8501"},
        "monitoring": {"port": 8002, "url": "http://localhost:8002"},
        "mcp_memory": {"port": 8001, "url": "http://localhost:8001"},
        "mcp_review": {"port": 8003, "url": "http://localhost:8003"},
    }

    # Check all services in parallel
    tasks = []
    for name, info in services.items():
        tasks.append(check_service_health(name, info["url"]))

    results = await asyncio.gather(*tasks)

    # Combine results
    status = {}
    for (name, info), result in zip(services.items(), results, strict=False):
        status[name] = {"port": info["port"], **result}

    # Determine overall health
    healthy_count = sum(1 for s in status.values() if s.get("status") == "healthy")
    total_count = len(status)

    overall = (
        "healthy"
        if healthy_count == total_count
        else "degraded"
        if healthy_count > 0
        else "critical"
    )

    return {
        "services": status,
        "timestamp": datetime.now().isoformat(),
        "overall_health": overall,
        "healthy_count": healthy_count,
        "total_count": total_count,
    }


async def get_current_config() -> dict:
    """Get current configuration"""
    return {
        "models": {
            "available": [
                "openai/gpt-5",
                "anthropic/claude-sonnet-4",
                "google/gemini-2.5-pro",
                "google/gemini-2.5-flash",
                "x-ai/grok-code-fast-1",
                "deepseek/deepseek-chat-v3.1",
                "z-ai/glm-4.5-air",
            ],
            "default": "google/gemini-2.5-pro",
        },
        "budgets": {"daily_limit": 100.0, "warning_threshold": 0.8},
        "features": {
            "repository_access": True,
            "memory_persistence": True,
            "cost_tracking": True,
            "websockets": True,
        },
        "ports": SERVICE_MAP,
    }


@router.get("/", response_class=HTMLResponse)
async def hub_dashboard(request: Request):
    """Main hub dashboard"""
    try:
        context = {
            "request": request,
            "title": "Sophia Intel AI Hub",
            "version": "1.0.0",
            "services": await get_service_status(),
            "config": await get_current_config(),
        }
        return templates.TemplateResponse("hub.html", context)
    except Exception as e:
        # Return a basic HTML page if template fails
        return HTMLResponse(
            content=f"""
        <!DOCTYPE html>
        <html>
        <head><title>Hub Error</title></head>
        <body>
            <h1>Hub Loading Error</h1>
            <p>Error: {str(e)}</p>
            <p>Please ensure the hub.html template exists in app/templates/</p>
        </body>
        </html>
        """
        )


@router.get("/status")
async def service_status():
    """Service health status endpoint"""
    return await get_service_status()


@router.post("/proxy/{service}/{path:path}")
async def proxy_request(service: str, path: str, request: Request):
    """Generic reverse proxy for services"""
    if service not in SERVICE_MAP:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")

    base_url = SERVICE_MAP[service]
    target_url = f"{base_url}/{path}"

    try:
        # Forward the request
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get request body
            body = await request.body()

            # Forward headers (excluding hop-by-hop headers)
            headers = dict(request.headers)
            hop_by_hop = ["host", "connection", "keep-alive", "transfer-encoding", "upgrade"]
            headers = {k: v for k, v in headers.items() if k.lower() not in hop_by_hop}
            headers["X-Forwarded-For"] = "hub"
            headers["X-Forwarded-Host"] = "localhost:8005"

            # Make the request
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body if body else None,
                follow_redirects=True,
            )

            # Return the response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"Service '{service}' is unavailable")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail=f"Service '{service}' timeout")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")


@router.get("/config")
async def get_config():
    """Get current configuration"""
    return await get_current_config()


# WebSocket endpoint for real-time events
connected_clients = set()


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket for real-time hub events"""
    await websocket.accept()
    connected_clients.add(websocket)

    try:
        # Send initial status
        status = await get_service_status()
        await websocket.send_json(
            {"type": "status", "data": status, "timestamp": datetime.now().isoformat()}
        )

        # Keep connection alive and send periodic updates
        while True:
            await asyncio.sleep(5)
            status = await get_service_status()
            await websocket.send_json(
                {"type": "status_update", "data": status, "timestamp": datetime.now().isoformat()}
            )

    except Exception as e:
        logger.info(f"WebSocket error: {e}")
    finally:
        connected_clients.remove(websocket)
