"""
Sophia AI MCP Server Template
Real MCP implementation with unified memory bus integration
No mock data, no demos - production ready
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4

import httpx
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import Field

# Import unified memory bus
from app.memory.bus import UnifiedMemoryBus
from app.observability.metrics import MetricsCollector
from app.observability.otel import trace_async

logger = logging.getLogger(__name__)

@dataclass
class MCPToolCall:
    """Standard MCP tool call structure"""
    tool: str
    params: Dict[str, Any]
    call_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)

@dataclass
class MCPToolResult:
    """Standard MCP tool result structure"""
    call_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    latency_ms: Optional[float] = None
    cache_hit: bool = False

class MCPServerBase(ABC):
    """
    Base class for all MCP servers in Sophia AI
    Integrates with unified memory bus and observability
    """

    def __init__(
        self,
        domain: str,
        capabilities: List[str],
        memory_bus: UnifiedMemoryBus,
        metrics: MetricsCollector
    ):
        self.domain = domain
        self.capabilities = capabilities
        self.memory_bus = memory_bus
        self.metrics = metrics
        self.tools: Dict[str, Callable] = {}
        self.app = FastAPI(title=f"Sophia AI {domain.title()} MCP Server")
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        """Setup CORS and other middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure properly for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """Setup FastAPI routes for MCP protocol"""

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "domain": self.domain,
                "capabilities": self.capabilities,
                "timestamp": datetime.utcnow().isoformat()
            }

        @self.app.get("/capabilities")
        async def get_capabilities():
            return {
                "domain": self.domain,
                "tools": list(self.tools.keys()),
                "capabilities": self.capabilities
            }

        @self.app.post("/tools/call")
        async def call_tool(tool_call: MCPToolCall):
            return await self.handle_tool_call(tool_call.tool, tool_call.params, tool_call.call_id)

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    if message.get("type") == "tool_call":
                        result = await self.handle_tool_call(
                            message["tool"],
                            message["params"],
                            message.get("call_id", str(uuid4()))
                        )
                        await websocket.send_text(json.dumps(asdict(result)))

            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.close()

    @trace_async("mcp_tool_call")
    async def handle_tool_call(self, tool: str, params: Dict[str, Any], call_id: str) -> MCPToolResult:
        """
        Handle MCP tool call with caching, metrics, and SLO tracking
        Target: P95 < 180ms, Cache hit rate > 97%
        """
        start_time = time.time()

        try:
            # Check if tool exists
            if tool not in self.tools:
                return MCPToolResult(
                    call_id=call_id,
                    success=False,
                    error=f"Tool '{tool}' not found in domain '{self.domain}'"
                )

            # Generate cache key
            cache_key = self._generate_cache_key(tool, params)

            # Check cache first (targeting 97% hit rate)
            cached_result = await self.memory_bus.get(cache_key)
            if cached_result:
                self.metrics.cache_hit(self.domain, tool)
                latency_ms = (time.time() - start_time) * 1000

                return MCPToolResult(
                    call_id=call_id,
                    success=True,
                    result=cached_result,
                    latency_ms=latency_ms,
                    cache_hit=True
                )

            # Execute tool
            tool_func = self.tools[tool]
            result = await tool_func(**params)

            # Cache result with appropriate TTL
            ttl = self._get_cache_ttl(tool, result)
            await self.memory_bus.set(cache_key, result, ttl=ttl)

            # Record metrics
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.tool_call_latency(self.domain, tool, latency_ms)
            self.metrics.cache_miss(self.domain, tool)

            # Check SLO compliance (P95 < 180ms)
            if latency_ms > 180:
                logger.warning(f"SLO violation: {tool} took {latency_ms}ms (>180ms)")
                self.metrics.slo_violation(self.domain, tool, latency_ms)

            return MCPToolResult(
                call_id=call_id,
                success=True,
                result=result,
                latency_ms=latency_ms,
                cache_hit=False
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Tool call failed: {tool} - {str(e)}")
            self.metrics.tool_call_error(self.domain, tool, str(e))

            return MCPToolResult(
                call_id=call_id,
                success=False,
                error=str(e),
                latency_ms=latency_ms
            )

    def _generate_cache_key(self, tool: str, params: Dict[str, Any]) -> str:
        """Generate deterministic cache key for tool call"""
        # Sort params for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hash(sorted_params)
        return f"{self.domain}:{tool}:{param_hash}"

    def _get_cache_ttl(self, tool: str, result: Any) -> int:
        """Get appropriate cache TTL based on tool and result characteristics"""
        # Default TTLs by tool type
        ttl_map = {
            "search": 300,      # 5 minutes for search results
            "get": 600,         # 10 minutes for entity fetches
            "list": 180,        # 3 minutes for list operations
            "analytics": 900,   # 15 minutes for analytics
            "health": 300,      # 5 minutes for health scores
        }

        # Determine tool type from name
        for tool_type, ttl in ttl_map.items():
            if tool_type in tool.lower():
                return ttl

        # Default TTL
        return 300

    def register_tool(self, name: str, func: Callable):
        """Register a tool function"""
        self.tools[name] = func
        logger.info(f"Registered tool '{name}' in domain '{self.domain}'")

    def mcp_tool(self, name: str):
        """Decorator to register MCP tools"""
        def decorator(func: Callable):
            self.register_tool(name, func)
            return func
        return decorator

    @abstractmethod
    async def initialize(self):
        """Initialize domain-specific resources"""

    @abstractmethod
    async def shutdown(self):
        """Cleanup domain-specific resources"""

class MCPServerManager:
    """
    Manages multiple MCP servers and provides unified access
    """

    def __init__(self, memory_bus: UnifiedMemoryBus, metrics: MetricsCollector):
        self.memory_bus = memory_bus
        self.metrics = metrics
        self.servers: Dict[str, MCPServerBase] = {}
        self.app = FastAPI(title="Sophia AI MCP Server Manager")
        self._setup_routes()

    def _setup_routes(self):
        """Setup unified routes for all MCP servers"""

        @self.app.get("/health")
        async def health_check():
            server_health = {}
            for domain, server in self.servers.items():
                try:
                    # Call server health endpoint
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"http://localhost:{server.port}/health")
                        server_health[domain] = response.json()
                except Exception as e:
                    server_health[domain] = {"status": "unhealthy", "error": str(e)}

            return {
                "status": "healthy" if all(h.get("status") == "healthy" for h in server_health.values()) else "degraded",
                "servers": server_health,
                "timestamp": datetime.utcnow().isoformat()
            }

        @self.app.get("/servers")
        async def list_servers():
            return {
                "servers": {
                    domain: {
                        "capabilities": server.capabilities,
                        "tools": list(server.tools.keys())
                    }
                    for domain, server in self.servers.items()
                }
            }

        @self.app.post("/tools/call/{domain}")
        async def call_domain_tool(domain: str, tool_call: MCPToolCall):
            if domain not in self.servers:
                raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")

            server = self.servers[domain]
            return await server.handle_tool_call(tool_call.tool, tool_call.params, tool_call.call_id)

    def register_server(self, server: MCPServerBase):
        """Register an MCP server"""
        self.servers[server.domain] = server
        logger.info(f"Registered MCP server for domain '{server.domain}'")

    async def start_all_servers(self):
        """Initialize and start all registered servers"""
        for domain, server in self.servers.items():
            try:
                await server.initialize()
                logger.info(f"Started MCP server for domain '{domain}'")
            except Exception as e:
                logger.error(f"Failed to start server for domain '{domain}': {e}")
                raise

    async def shutdown_all_servers(self):
        """Shutdown all registered servers"""
        for domain, server in self.servers.items():
            try:
                await server.shutdown()
                logger.info(f"Shutdown MCP server for domain '{domain}'")
            except Exception as e:
                logger.error(f"Failed to shutdown server for domain '{domain}': {e}")

class SophiaMCPServer(MCPServerBase):
    """
    Unified Sophia MCP Server
    Provides compatibility layer for main_unified.py
    """

    def __init__(self, memory_bus=None):
        # Initialize metrics collector
        from app.observability.metrics import MetricsCollector
        metrics = MetricsCollector()

        super().__init__(
            domain="sophia_unified",
            capabilities=["memory", "system", "utility"],
            memory_bus=memory_bus,
            metrics=metrics
        )

        self.request_count = 0
        self.error_count = 0
        self.start_time = datetime.utcnow()

    async def initialize(self):
        """Initialize unified MCP server"""
        logger.info("Initializing Sophia Unified MCP Server...")

        # Register core tools
        await self._register_core_tools()

        # Validate memory bus connection
        if self.memory_bus:
            try:
                # Test memory bus connection
                sophia_key = f"test_{uuid4().hex[:8]}"
                await self.memory_bus.set(sophia_key, {"test": True}, ttl=60)
                result = await self.memory_bus.get(sophia_key)
                if result:
                    logger.info("✅ Memory bus connection verified")
                else:
                    logger.warning("⚠️ Memory bus test failed")
            except Exception as e:
                logger.warning(f"⚠️ Memory bus connection issue: {e}")

        logger.info(f"✅ Unified MCP Server initialized with {len(self.tools)} tools")

    async def shutdown(self):
        """Cleanup unified MCP server"""
        logger.info("Shutting down unified MCP server...")
        # Cleanup logic here
        logger.info("✅ Unified MCP server shutdown complete")

    async def _register_core_tools(self):
        """Register core MCP tools"""

        @self.mcp_tool("memory.store")
        async def memory_store(key: str, value: Any, ttl: int = 3600) -> Dict[str, Any]:
            """Store data in unified memory system"""
            if not self.memory_bus:
                raise RuntimeError("Memory bus not available")

            await self.memory_bus.set(key, value, ttl=ttl)

            return {
                "stored": True,
                "key": key,
                "ttl": ttl,
                "timestamp": datetime.utcnow().isoformat()
            }

        @self.mcp_tool("memory.retrieve")
        async def memory_retrieve(key: str) -> Dict[str, Any]:
            """Retrieve data from unified memory system"""
            if not self.memory_bus:
                raise RuntimeError("Memory bus not available")

            value = await self.memory_bus.get(key)

            return {
                "found": value is not None,
                "key": key,
                "value": value,
                "timestamp": datetime.utcnow().isoformat()
            }

        @self.mcp_tool("memory.search")
        async def memory_search(query: str, limit: int = 10) -> Dict[str, Any]:
            """Search across unified memory system"""
            if not self.memory_bus:
                raise RuntimeError("Memory bus not available")

            results = await self.memory_bus.search(query, limit=limit)

            return {
                "query": query,
                "results": results,
                "count": len(results),
                "limit": limit,
                "timestamp": datetime.utcnow().isoformat()
            }

        @self.mcp_tool("system.status")
        async def system_status() -> Dict[str, Any]:
            """Get system status and metrics"""
            return {
                "status": "operational",
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
                "tools_available": len(self.tools),
                "requests_processed": self.request_count,
                "errors_encountered": self.error_count,
                "memory_bus_connected": self.memory_bus is not None,
                "timestamp": datetime.utcnow().isoformat()
            }

        @self.mcp_tool("system.metrics")
        async def system_metrics(component: Optional[str] = None) -> Dict[str, Any]:
            """Get detailed system metrics"""
            metrics = {
                "server": {
                    "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
                    "request_count": self.request_count,
                    "error_count": self.error_count,
                    "error_rate": self.error_count / max(self.request_count, 1),
                    "tools_registered": len(self.tools)
                }
            }

            if self.memory_bus and (not component or component == "memory"):
                try:
                    memory_metrics = await self.memory_bus.get_metrics()
                    metrics["memory"] = memory_metrics
                except Exception as e:
                    metrics["memory"] = {"error": str(e)}

            if component and component in metrics:
                return {component: metrics[component]}

            return metrics

        @self.mcp_tool("util.generate_id")
        async def generate_id(prefix: str = "id") -> Dict[str, Any]:
            """Generate unique identifier"""
            unique_id = f"{prefix}_{uuid4().hex[:8]}"

            return {
                "id": unique_id,
                "prefix": prefix,
                "timestamp": datetime.utcnow().isoformat()
            }

        @self.mcp_tool("util.timestamp")
        async def get_timestamp(format_type: str = "iso") -> Dict[str, Any]:
            """Get current timestamp"""
            now = datetime.utcnow()

            if format_type == 'iso':
                timestamp = now.isoformat()
            elif format_type == 'unix':
                timestamp = int(now.timestamp())
            elif format_type == 'readable':
                timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
            else:
                timestamp = now.isoformat()

            return {
                "timestamp": timestamp,
                "format": format_type,
                "timezone": "UTC"
            }

    async def call_tool(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Compatibility method for main_unified.py"""
        self.request_count += 1

        try:
            tool_name = request.get('tool')
            params = request.get('params', {})
            call_id = request.get('call_id', str(uuid4()))

            result = await self.handle_tool_call(tool_name, params, call_id)

            return {
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "execution_time": result.latency_ms / 1000 if result.latency_ms else 0,
                "cache_hit": result.cache_hit,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.error_count += 1
            logger.error(f"Tool call failed: {e}")

            return {
                "success": False,
                "error": str(e),
                "execution_time": 0,
                "cache_hit": False,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def list_tools(self) -> Dict[str, Any]:
        """List all available tools - compatibility method"""
        tools_list = []

        for tool_name in self.tools.keys():
            # Extract tool info from function
            func = self.tools[tool_name]

            tools_list.append({
                "name": tool_name,
                "description": func.__doc__ or f"{tool_name} tool",
                "category": tool_name.split('.')[0] if '.' in tool_name else "general"
            })

        return {
            "tools": tools_list,
            "total_count": len(tools_list),
            "categories": list(set(tool.get("category", "general") for tool in tools_list)),
            "server_info": {
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
                "total_requests": self.request_count,
                "total_errors": self.error_count,
                "error_rate": self.error_count / max(self.request_count, 1)
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """Health check - compatibility method"""
        health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "tools_count": len(self.tools),
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1)
        }

        # Check memory bus health
        if self.memory_bus:
            try:
                # Simple health check - try to get a test key
                sophia_result = await self.memory_bus.get("health_check_test")
                health["memory_bus"] = {
                    "status": "healthy",
                    "connected": True
                }
            except Exception as e:
                health["memory_bus"] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "connected": False
                }
                health["status"] = "degraded"
        else:
            health["memory_bus"] = {
                "status": "not_configured",
                "connected": False
            }

        return health


# Utility functions for MCP tool development
def validate_required_params(params: Dict[str, Any], required: List[str]) -> None:
    """Validate that required parameters are present"""
    missing = [param for param in required if param not in params]
    if missing:
        raise ValueError(f"Missing required parameters: {missing}")

def sanitize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize parameters for safe processing"""
    # Remove None values
    sanitized = {k: v for k, v in params.items() if v is not None}

    # Convert UUIDs to strings
    for key, value in sanitized.items():
        if isinstance(value, UUID):
            sanitized[key] = str(value)

    return sanitized

async def with_retry(func: Callable, max_retries: int = 3, delay: float = 1.0):
    """Execute function with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            wait_time = delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s")
            await asyncio.sleep(wait_time)

# Example usage and testing
if __name__ == "__main__":

    # This would be used by specific domain servers
    # See revenue_ops_gateway.py for concrete implementation

    async def sophia_server():
        from app.memory.bus import UnifiedMemoryBus
        from app.observability.metrics import MetricsCollector

        memory_bus = UnifiedMemoryBus()
        metrics = MetricsCollector()

        # Create test server
        class TestMCPServer(MCPServerBase):
            async def initialize(self):
                @self.mcp_tool("test.echo")
                async def echo(message: str) -> Dict[str, Any]:
                    return {"echo": message, "timestamp": datetime.utcnow().isoformat()}

            async def shutdown(self):
                pass

        server = TestMCPServer("test", ["echo"], memory_bus, metrics)
        await server.initialize()

        # Test tool call
        result = await server.handle_tool_call("test.echo", {"message": "Hello Sophia"}, "test-123")
        print(f"Test result: {result}")

    # Run test
    asyncio.run(sophia_server())
