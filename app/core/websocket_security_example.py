"""
WebSocket Security Implementation Example
Demonstrates how to use the comprehensive WebSocket security system
"""

import asyncio
import logging
from typing import Optional

from fastapi import FastAPI, Query

from .secure_websocket_factory import SecureWebSocketFactory, create_websocket_routes
from .websocket_security_config import SecurityConfig, get_config

logger = logging.getLogger(__name__)

# Example FastAPI application with secure WebSocket implementation
app = FastAPI(title="Secure WebSocket Demo")

# Global WebSocket manager (will be initialized on startup)
ws_manager = None


@app.on_event("startup")
async def startup_event():
    """Initialize secure WebSocket manager on startup"""
    global ws_manager

    # Get environment from env vars or default to development
    import os

    environment = os.getenv("ENVIRONMENT", "development")

    # Create secure WebSocket manager
    ws_manager = await SecureWebSocketFactory.create_manager(environment=environment)

    # Store in app state for access in routes
    app.state.ws_manager = ws_manager

    # Log security recommendations
    recommendations = SecureWebSocketFactory.get_security_recommendations(environment)
    logger.info(f"Security recommendations: {recommendations}")

    logger.info(f"Secure WebSocket server started for {environment} environment")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global ws_manager
    if ws_manager:
        # Close all connections gracefully
        for client_id in list(ws_manager.connections.keys()):
            await ws_manager.disconnect(client_id)


# WebSocket endpoint with comprehensive security
@app.websocket("/ws/{client_id}/{session_id}")
async def websocket_endpoint(
    websocket,
    client_id: str,
    session_id: str,
    token: Optional[str] = Query(None, description="JWT authentication token for secure access"),
):
    """
    Secure WebSocket endpoint with:
    - JWT authentication
    - Rate limiting
    - Input validation
    - Threat detection
    - Audit logging
    - Tenant isolation
    """
    if not ws_manager:
        await websocket.close(code=1011, reason="Server not initialized")
        return

    await ws_manager.websocket_endpoint(websocket, client_id, session_id, token)


# Security monitoring endpoints
@app.get("/ws/security/status")
async def get_security_status():
    """Get comprehensive security status"""
    if not ws_manager:
        return {"error": "WebSocket manager not initialized"}

    return await ws_manager.get_security_status()


@app.get("/ws/metrics")
async def get_websocket_metrics():
    """Get WebSocket performance and security metrics"""
    if not ws_manager:
        return {"error": "WebSocket manager not initialized"}

    return ws_manager.get_metrics()


@app.post("/ws/security/emergency-lockdown")
async def emergency_security_lockdown(duration_minutes: int = 15):
    """
    Emergency security lockdown - disconnects anonymous users and applies strict limits
    Use in case of detected attacks or security incidents
    """
    if not ws_manager:
        return {"error": "WebSocket manager not initialized"}

    await ws_manager.emergency_security_lockdown(duration_minutes)
    return {
        "status": "emergency_lockdown_activated",
        "duration_minutes": duration_minutes,
        "message": "All anonymous connections terminated, emergency rate limits applied",
    }


@app.get("/ws/audit/export")
async def export_audit_logs(hours: int = 24):
    """Export security audit logs for compliance"""
    if not ws_manager:
        return {"error": "WebSocket manager not initialized"}

    return await ws_manager.audit_log_export(hours)


# Pay Ready specific secure endpoint
@app.websocket("/ws/pay-ready/{client_id}/{session_id}")
async def pay_ready_websocket(
    websocket,
    client_id: str,
    session_id: str,
    token: str = Query(..., description="JWT token required for Pay Ready access"),
):
    """
    Pay Ready specific WebSocket with maximum security:
    - Mandatory authentication
    - Strict tenant isolation
    - Enhanced audit logging
    - Business cycle aware rate limiting
    """
    # Create Pay Ready optimized manager if needed
    pay_ready_manager = await SecureWebSocketFactory.create_pay_ready_manager()
    await pay_ready_manager.websocket_endpoint(websocket, client_id, session_id, token)


# Example client usage demonstration
async def example_client_usage():
    """Example of how a client would connect securely"""
    import json

    import websockets

    # Example JWT token (in real usage, obtain from auth service)
    jwt_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

    # Connect with authentication
    uri = f"ws://localhost:8000/ws/client123/session456?token={jwt_token}"

    try:
        async with websockets.connect(uri) as websocket:
            # Send authenticated message
            message = {
                "type": "subscribe",
                "channel": "sophia_pay_ready",
                "timestamp": "2024-01-01T00:00:00Z",
            }
            await websocket.send(json.dumps(message))

            # Receive response
            response = await websocket.recv()
            print(f"Server response: {response}")

            # Send heartbeat to maintain session
            heartbeat = {"type": "heartbeat"}
            await websocket.send(json.dumps(heartbeat))

            # Handle real-time updates
            while True:
                try:
                    update = await websocket.recv()
                    data = json.loads(update)
                    print(f"Real-time update: {data}")
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed by server")
                    break

    except Exception as e:
        print(f"Connection error: {e}")


# Security configuration examples
def get_example_configurations():
    """Get example security configurations for different scenarios"""

    # Development configuration
    dev_config = SecurityConfig(
        secret_key="dev-key-not-secure",
        require_authentication=False,  # Relaxed for testing
        enable_rate_limiting=True,
        ddos_threshold_rps=1000,
        enable_threat_detection=True,
        audit_retention_days=7,
    )

    # Production configuration
    prod_config = SecurityConfig(
        secret_key="your-production-secret-key-32-chars-min",
        require_authentication=True,
        enable_rate_limiting=True,
        enable_ddos_protection=True,
        ddos_threshold_rps=100,
        enable_threat_detection=True,
        session_timeout_minutes=30,
        audit_retention_days=90,
        pay_ready_strict_isolation=True,
    )

    return {"development": dev_config, "production": prod_config}


if __name__ == "__main__":
    # Example of running the secure WebSocket server
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run server with security enabled
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
