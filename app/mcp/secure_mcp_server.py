"""
Advanced MCP Server with OAuth Resource Indicators (RFC 8707)
Implements June 2025 security specifications
"""

import asyncio
import hashlib
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx
import jwt
from aiobreaker import CircuitBreaker
from fastapi import Depends, FastAPI, HTTPException, WebSocket
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Security configuration
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24


@dataclass
class ResourceIndicator:
    """
    OAuth 2.0 Resource Indicator (RFC 8707)
    Prevents token mis-redemption attacks
    """
    resource: str  # Resource server identifier
    audience: str  # Intended audience
    scope: list[str]  # Allowed scopes
    issued_at: float
    expires_at: float
    jti: str  # JWT ID for tracking

    def is_valid(self) -> bool:
        """Check if resource indicator is still valid"""
        return time.time() < self.expires_at

    def validate_resource(self, requested_resource: str) -> bool:
        """Validate requested resource matches indicator"""
        return self.resource == requested_resource and self.is_valid()


class MCPSecurityManager:
    """
    Security manager for MCP with Resource Indicators
    """

    def __init__(self):
        self.resource_indicators: dict[str, ResourceIndicator] = {}
        self.revoked_tokens: set = set()
        self.circuit_breaker = CircuitBreaker(
            fail_max=5,
            reset_timeout=timedelta(seconds=60)
        )

    def generate_resource_indicator(
        self,
        resource: str,
        audience: str,
        scope: list[str],
        duration_hours: int = 1
    ) -> str:
        """
        Generate JWT with Resource Indicator
        """
        now = time.time()
        expires_at = now + (duration_hours * 3600)
        jti = hashlib.sha256(f"{resource}{audience}{now}".encode()).hexdigest()

        indicator = ResourceIndicator(
            resource=resource,
            audience=audience,
            scope=scope,
            issued_at=now,
            expires_at=expires_at,
            jti=jti
        )

        # Store indicator
        self.resource_indicators[jti] = indicator

        # Create JWT
        payload = {
            "resource": resource,
            "aud": audience,
            "scope": " ".join(scope),
            "iat": now,
            "exp": expires_at,
            "jti": jti
        }

        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token

    def validate_token(self, token: str, requested_resource: str) -> ResourceIndicator:
        """
        Validate JWT token with Resource Indicator
        """
        try:
            # Decode token
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            jti = payload.get("jti")

            # Check if token is revoked
            if jti in self.revoked_tokens:
                raise HTTPException(status_code=401, detail="Token has been revoked")

            # Get resource indicator
            indicator = self.resource_indicators.get(jti)
            if not indicator:
                raise HTTPException(status_code=401, detail="Invalid resource indicator")

            # Validate resource
            if not indicator.validate_resource(requested_resource):
                raise HTTPException(
                    status_code=403,
                    detail=f"Token not valid for resource: {requested_resource}"
                )

            return indicator

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    def revoke_token(self, jti: str):
        """Revoke a token by its JWT ID"""
        self.revoked_tokens.add(jti)
        if jti in self.resource_indicators:
            del self.resource_indicators[jti]


class SecureMCPServer:
    """
    Secure MCP Server with advanced authentication and circuit breakers
    """

    def __init__(self, server_id: str = "sophia-mcp-server"):
        self.server_id = server_id
        self.security_manager = MCPSecurityManager()
        self.app = FastAPI(title=f"Secure MCP Server - {server_id}")
        self.tools: dict[str, Callable] = {}
        self.health_metrics = {
            "requests_total": 0,
            "requests_failed": 0,
            "avg_latency_ms": 0.0,
            "circuit_breaker_trips": 0
        }

        # Circuit breakers for different operations
        self.llm_circuit_breaker = CircuitBreaker(
            fail_max=5,
            reset_timeout=timedelta(seconds=60)
        )
        self.db_circuit_breaker = CircuitBreaker(
            fail_max=3,
            reset_timeout=timedelta(seconds=30)
        )

        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes with security"""

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "server_id": self.server_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": self.health_metrics
            }

        @self.app.get("/metrics")
        async def metrics():
            """Prometheus-compatible metrics endpoint"""
            return {
                "mcp_requests_total": self.health_metrics["requests_total"],
                "mcp_requests_failed": self.health_metrics["requests_failed"],
                "mcp_latency_ms": self.health_metrics["avg_latency_ms"],
                "mcp_circuit_breaker_trips": self.health_metrics["circuit_breaker_trips"]
            }

        @self.app.post("/auth/token")
        async def generate_token(
            resource: str,
            audience: str,
            scope: list[str] = ["read", "write"]
        ):
            """Generate OAuth token with Resource Indicator"""
            token = self.security_manager.generate_resource_indicator(
                resource=resource,
                audience=audience,
                scope=scope
            )
            return {
                "access_token": token,
                "token_type": "bearer",
                "expires_in": 3600,
                "resource": resource,
                "scope": " ".join(scope)
            }

        @self.app.post("/tools/{tool_name}")
        async def execute_tool(
            tool_name: str,
            request: dict[str, Any],
            authorization: HTTPAuthorizationCredentials = Depends(HTTPBearer())
        ):
            """Execute MCP tool with security validation"""
            start_time = time.perf_counter()

            # Validate token with resource indicator
            resource = f"tool:{tool_name}"
            indicator = self.security_manager.validate_token(
                authorization.credentials,
                resource
            )

            # Check scope
            if "execute" not in indicator.scope and "write" not in indicator.scope:
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient scope for tool execution"
                )

            # Execute tool with circuit breaker
            try:
                if tool_name not in self.tools:
                    raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

                tool_func = self.tools[tool_name]

                # Apply circuit breaker based on tool type
                if "llm" in tool_name.lower():
                    result = await self.llm_circuit_breaker(tool_func)(request)
                elif "db" in tool_name.lower() or "memory" in tool_name.lower():
                    result = await self.db_circuit_breaker(tool_func)(request)
                else:
                    result = await tool_func(request)

                # Update metrics
                latency = (time.perf_counter() - start_time) * 1000
                self._update_metrics(latency, success=True)

                return {
                    "result": result,
                    "latency_ms": latency,
                    "resource": resource
                }

            except Exception as e:
                self._update_metrics(0, success=False)
                if "circuit breaker" in str(e).lower():
                    self.health_metrics["circuit_breaker_trips"] += 1
                raise HTTPException(status_code=503, detail=f"Tool execution failed: {str(e)}")

        @self.app.websocket("/ws/mcp")
        async def websocket_endpoint(
            websocket: WebSocket,
            token: str = None
        ):
            """WebSocket endpoint with auto-reconnection support"""
            if not token:
                await websocket.close(code=1008, reason="Missing authentication")
                return

            try:
                # Validate token
                indicator = self.security_manager.validate_token(token, "websocket:mcp")
                await websocket.accept()

                # Send authentication success
                await websocket.send_json({
                    "type": "auth_success",
                    "resource": indicator.resource,
                    "scope": indicator.scope
                })

                # Handle messages
                while True:
                    data = await websocket.receive_json()

                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif data.get("type") == "tool_execute":
                        # Execute tool through WebSocket
                        tool_name = data.get("tool")
                        params = data.get("params", {})

                        if tool_name in self.tools:
                            result = await self.tools[tool_name](params)
                            await websocket.send_json({
                                "type": "tool_result",
                                "tool": tool_name,
                                "result": result
                            })
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Tool {tool_name} not found"
                            })

            except Exception as e:
                await websocket.close(code=1011, reason=str(e))

    def register_tool(self, name: str, func: Callable):
        """Register a tool with the MCP server"""
        self.tools[name] = func

    def _update_metrics(self, latency: float, success: bool):
        """Update health metrics"""
        self.health_metrics["requests_total"] += 1
        if not success:
            self.health_metrics["requests_failed"] += 1

        if latency > 0:
            # Calculate running average
            total = self.health_metrics["requests_total"]
            avg = self.health_metrics["avg_latency_ms"]
            self.health_metrics["avg_latency_ms"] = (avg * (total - 1) + latency) / total


class MCPCloudIntegration:
    """
    Integration with cloud MCP servers (AWS, Google Cloud, Azure)
    """

    def __init__(self):
        self.providers = {
            "aws": {
                "endpoint": "https://mcp.amazonaws.com",
                "auth_endpoint": "https://auth.mcp.amazonaws.com/token"
            },
            "gcp": {
                "endpoint": "https://mcp.googleapis.com",
                "auth_endpoint": "https://oauth2.googleapis.com/token"
            },
            "azure": {
                "endpoint": "https://mcp.azure.com",
                "auth_endpoint": "https://login.microsoftonline.com/token"
            }
        }
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.tokens: dict[str, str] = {}

    async def authenticate(self, provider: str, credentials: dict[str, str]) -> str:
        """Authenticate with cloud MCP provider"""
        if provider not in self.providers:
            raise ValueError(f"Unknown provider: {provider}")

        config = self.providers[provider]

        # Request token with resource indicator
        response = await self.http_client.post(
            config["auth_endpoint"],
            json={
                **credentials,
                "resource": f"mcp:{provider}",
                "grant_type": "client_credentials"
            }
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            self.tokens[provider] = token
            return token
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Authentication failed for {provider}"
            )

    async def execute_cloud_tool(
        self,
        provider: str,
        tool: str,
        params: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute tool on cloud MCP server"""
        if provider not in self.tokens:
            raise HTTPException(status_code=401, detail=f"Not authenticated with {provider}")

        config = self.providers[provider]

        response = await self.http_client.post(
            f"{config['endpoint']}/tools/{tool}",
            headers={
                "Authorization": f"Bearer {self.tokens[provider]}",
                "X-Resource-Indicator": f"mcp:{provider}:tool:{tool}"
            },
            json=params
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Cloud tool execution failed: {response.text}"
            )


# Example secure tools
async def secure_code_generation(params: dict[str, Any]) -> str:
    """Secure code generation tool"""
    prompt = params.get("prompt", "")
    language = params.get("language", "python")

    # Simulate secure processing
    await asyncio.sleep(0.1)

    return f"# Secure {language} code\n# Generated from: {prompt[:50]}...\n\nprint('Hello, secure world!')"


async def secure_memory_search(params: dict[str, Any]) -> list[dict]:
    """Secure memory search with encryption"""
    query = params.get("query", "")

    # Simulate encrypted search
    await asyncio.sleep(0.05)

    return [
        {
            "id": hashlib.sha256(query.encode()).hexdigest()[:8],
            "content": f"Encrypted result for: {query}",
            "score": 0.95
        }
    ]


# Initialize and run secure MCP server
def create_secure_mcp_server() -> SecureMCPServer:
    """Create and configure secure MCP server"""
    server = SecureMCPServer("sophia-secure-mcp")

    # Register secure tools
    server.register_tool("code_generation", secure_code_generation)
    server.register_tool("memory_search", secure_memory_search)

    return server


if __name__ == "__main__":
    import uvicorn

    server = create_secure_mcp_server()
    print("🔒 Starting Secure MCP Server with OAuth Resource Indicators...")
    print("📊 Health endpoint: http://localhost:8006/health")
    print("🔑 Token endpoint: http://localhost:8006/auth/token")

    uvicorn.run(server.app, host="0.0.0.0", port=8006)
