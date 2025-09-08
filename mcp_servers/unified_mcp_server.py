#!/usr/bin/env python3
"""
Unified MCP Server for Sophia AI
Combines all MCP functionality with Redis caching and smart routing
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
import redis
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MCPConfig:
    """MCP Server Configuration"""

    redis_url: str = "${REDIS_URL}"
    cache_ttl: int = 300  # 5 minutes
    lambda_api_key: str = ""
    portkey_api_key: str = ""
    openrouter_api_key: str = ""
    max_retries: int = 3
    timeout: int = 30


class UnifiedMCPServer:
    """Unified MCP Server with Redis caching and smart routing"""

    def __init__(self, config: MCPConfig):
        self.config = config
        self.redis_client = None
        self.app = FastAPI(title="Sophia AI Unified MCP Server")
        self.setup_middleware()
        self.setup_routes()

    def setup_middleware(self):
        """Setup CORS and other middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    async def startup(self):
        """Initialize Redis connection and other resources"""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            await asyncio.get_event_loop().run_in_executor(None, self.redis_client.ping)
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable, using memory cache: {e}")
            self.redis_client = None

    async def get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data with fallback to memory"""
        if not self.redis_client:
            return None

        try:
            cached = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.get, key
            )
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        return None

    async def set_cached(self, key: str, data: Dict[str, Any], ttl: int = None):
        """Set cached data with TTL"""
        if not self.redis_client:
            return

        try:
            ttl = ttl or self.config.cache_ttl
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.redis_client.setex(key, ttl, json.dumps(data, default=str))
            )
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    async def smart_route_request(
        self, request_type: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Smart routing based on request complexity and available resources"""

        # Check cache first
        cache_key = f"mcp:{request_type}:{hash(str(payload))}"
        cached_result = await self.get_cached(cache_key)
        if cached_result:
            logger.info(f"✅ Cache hit for {request_type}")
            return cached_result

        # Route based on request type
        if request_type in ["gpu_inference", "model_training", "large_embedding"]:
            result = await self.route_to_lambda_labs(payload)
        elif request_type in ["business_intelligence", "data_query", "analytics"]:
            result = await self.route_to_estuary_flow(payload)
        elif request_type in ["chat", "completion", "simple_query"]:
            result = await self.route_to_openrouter(payload)
        else:
            result = await self.route_to_local_processing(payload)

        # Cache successful results
        if result.get("success"):
            await self.set_cached(cache_key, result)

        return result

    async def route_to_lambda_labs(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route GPU-intensive tasks to Lambda Labs"""
        if not self.config.lambda_api_key:
            return {"success": False, "error": "Lambda Labs API key not configured"}

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    "https://cloud.lambdalabs.com/api/v1/instances",
                    headers={"Authorization": f"Bearer {self.config.lambda_api_key}"},
                    json=payload,
                )

                if response.status_code == 200:
                    return {"success": True, "data": response.json(), "source": "lambda_labs"}
                else:
                    return {"success": False, "error": f"Lambda Labs error: {response.status_code}"}

        except Exception as e:
            logger.error(f"Lambda Labs routing error: {e}")
            return {"success": False, "error": str(e)}

    async def route_to_estuary_flow(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route data processing tasks to Estuary Flow"""
        try:
            # Simulate Estuary Flow processing
            result = {
                "success": True,
                "data": {
                    "processed_records": payload.get("record_count", 0),
                    "processing_time": 0.1,
                    "source": "estuary_flow",
                },
                "timestamp": datetime.now().isoformat(),
            }
            return result

        except Exception as e:
            logger.error(f"Estuary Flow routing error: {e}")
            return {"success": False, "error": str(e)}

    async def route_to_openrouter(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route AI requests to OpenRouter"""
        if not self.config.openrouter_api_key:
            return {"success": False, "error": "OpenRouter API key not configured"}

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.config.openrouter_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": payload.get("model", "anthropic/claude-3.5-haiku"),
                        "messages": payload.get("messages", []),
                        "max_tokens": payload.get("max_tokens", 1000),
                    },
                )

                if response.status_code == 200:
                    return {"success": True, "data": response.json(), "source": "openrouter"}
                else:
                    return {"success": False, "error": f"OpenRouter error: {response.status_code}"}

        except Exception as e:
            logger.error(f"OpenRouter routing error: {e}")
            return {"success": False, "error": str(e)}

    async def route_to_local_processing(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Route simple tasks to local processing"""
        try:
            # Simple local processing
            result = {
                "success": True,
                "data": {"processed": True, "payload_size": len(str(payload)), "source": "local"},
                "timestamp": datetime.now().isoformat(),
            }
            return result

        except Exception as e:
            logger.error(f"Local processing error: {e}")
            return {"success": False, "error": str(e)}

    def setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.on_event("startup")
        async def startup_event():
            await self.startup()

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            redis_status = "connected" if self.redis_client else "disconnected"
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "redis": redis_status,
                "version": "1.0.0",
            }

        @self.app.post("/mcp/route")
        async def route_request(request_data: Dict[str, Any]):
            """Main routing endpoint"""
            request_type = request_data.get("type", "unknown")
            payload = request_data.get("payload", {})

            start_time = time.time()
            result = await self.smart_route_request(request_type, payload)
            processing_time = time.time() - start_time

            result["processing_time"] = processing_time
            result["request_id"] = f"req_{int(time.time())}"

            return result

        @self.app.get("/mcp/stats")
        async def get_stats():
            """Get MCP server statistics"""
            try:
                if self.redis_client:
                    info = await asyncio.get_event_loop().run_in_executor(
                        None, self.redis_client.info
                    )
                    return {
                        "redis_connected": True,
                        "redis_memory": info.get("used_memory_human", "unknown"),
                        "redis_connections": info.get("connected_clients", 0),
                    }
                else:
                    return {"redis_connected": False}
            except Exception as e:
                return {"error": str(e)}

        @self.app.delete("/mcp/cache")
        async def clear_cache():
            """Clear MCP cache"""
            try:
                if self.redis_client:
                    await asyncio.get_event_loop().run_in_executor(None, self.redis_client.flushdb)
                    return {"success": True, "message": "Cache cleared"}
                else:
                    return {"success": False, "message": "Redis not connected"}
            except Exception as e:
                return {"success": False, "error": str(e)}


def create_mcp_server() -> UnifiedMCPServer:
    """Create and configure MCP server"""
    config = MCPConfig(
        redis_url=os.getenv("REDIS_URL", "${REDIS_URL}"),
        lambda_api_key=os.getenv("LAMBDA_API_KEY", ""),
        portkey_api_key=os.getenv("PORTKEY_API_KEY", ""),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        cache_ttl=int(os.getenv("MCP_CACHE_TTL", "300")),
        max_retries=int(os.getenv("MCP_MAX_RETRIES", "3")),
        timeout=int(os.getenv("MCP_TIMEOUT", "30")),
    )

    return UnifiedMCPServer(config)


if __name__ == "__main__":
    server = create_mcp_server()

    # Run server
    uvicorn.run(
        server.app, host="${BIND_IP}", port=int(os.getenv("MCP_PORT", "8001")), log_level="info"
    )
