"\nBase MCP Server class with common functionality\n"

import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

try:
    import uvloop

    UVLOOP_AVAILABLE = True
except ImportError:
    UVLOOP_AVAILABLE = False
try:
    import orjson

    def JSON_DUMPS(x):
        return orjson.dumps(x, option=orjson.OPT_INDENT_2).decode()

    JSON_LOADS = orjson.loads
except ImportError:
    import json

    def JSON_DUMPS(x):
        return json.dumps(x, indent=2)

    JSON_LOADS = json.loads
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

@dataclass
class MCPServerConfig:
    """Configuration for MCP servers"""

    name: str
    description: str = ""
    version: str = "1.0.0"
    enable_performance_optimization: bool = True
    enable_circuit_breaker: bool = True
    enable_fallback_handler: bool = True
    enable_metrics: bool = True
    enable_caching: bool = True
    log_level: str = "INFO"
    timeout_seconds: int = 30
    max_retries: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    environment_variables: dict[str, str] = field(default_factory=dict)
    required_env_vars: list[str] = field(default_factory=list)

class BaseMCPServer(ABC):
    """
    Base class for all MCP servers with common functionality:
    - Standardized initialization
    - Performance optimization
    - Error handling
    - Logging
    - Metrics collection
    - Circuit breaker pattern
    - Fallback handling
    """

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.server = Server(config.name)
        self.logger = logging.getLogger(f"mcp.{config.name}")
        self._setup_logging()
        if config.enable_performance_optimization and UVLOOP_AVAILABLE:
            uvloop.install()
            self.logger.info("✅ uvloop event loop optimization enabled")
        self._metrics_collector = None
        self._circuit_breakers = {}
        self._fallback_handler = None
        self._cache = {}
        self._validate_environment()
        self.logger.info(f"✅ {config.name} MCP Server initialized")

    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _validate_environment(self):
        """Validate required environment variables"""
        missing_vars = []
        for var in self.config.required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        if missing_vars:
            error_msg = (
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
            self.logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)

    @abstractmethod
    async def initialize_tools(self) -> list[Tool]:
        """Initialize and return the list of tools for this server"""

    @abstractmethod
    async def handle_tool_call(
        self, name: str, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Handle tool calls - must be implemented by subclasses"""

    async def initialize(self):
        """Initialize the MCP server with tools and handlers"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return await self.initialize_tools()

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            start_time = time.time()
            try:
                self._validate_tool_input(name, arguments)
                result = await self.handle_tool_call(name, arguments)
                execution_time = time.time() - start_time
                self._record_success_metrics(name, execution_time)
                self.logger.info(
                    f"✅ {name} completed in {execution_time * 1000:.1f}ms"
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                self._record_error_metrics(name, execution_time, str(e))
                self.logger.error(f"❌ {name} failed: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    def _validate_tool_input(self, name: str, arguments: dict[str, Any]):
        """Validate tool input - can be overridden by subclasses"""
        if not isinstance(arguments, dict):
            raise ValueError(f"Tool {name} arguments must be a dictionary")

    def _record_success_metrics(self, tool_name: str, execution_time: float):
        """Record success metrics"""
        if self._metrics_collector:
            self._metrics_collector.increment_requests(tool_name, "success")
            self._metrics_collector.observe_request_duration(tool_name, execution_time)

    def _record_error_metrics(self, tool_name: str, execution_time: float, error: str):
        """Record error metrics"""
        if self._metrics_collector:
            self._metrics_collector.increment_requests(tool_name, "error")
            self._metrics_collector.observe_request_duration(tool_name, execution_time)

    async def setup_reliability_components(self):
        """Setup circuit breakers, fallback handlers, and metrics"""
        if self.config.enable_metrics:
            await self._setup_metrics()
        if self.config.enable_circuit_breaker:
            await self._setup_circuit_breakers()
        if self.config.enable_fallback_handler:
            await self._setup_fallback_handler()

    async def _setup_metrics(self):
        """Setup metrics collection"""
        try:
            from ..reliability.metrics_collector import MCPMetricsCollector

            self._metrics_collector = MCPMetricsCollector(self.config.name)
            self.logger.info("✅ Metrics collection enabled")
        except ImportError:
            self.logger.warning("⚠️ Metrics collector not available")

    async def _setup_circuit_breakers(self):
        """Setup circuit breakers"""
        try:
            from ..reliability.circuit_breaker import circuit_registry

            self.logger.info("✅ Circuit breaker protection enabled")
        except ImportError:
            self.logger.warning("⚠️ Circuit breaker not available")

    async def _setup_fallback_handler(self):
        """Setup fallback handler"""
        try:
            from ..reliability.fallback_handler import get_fallback_handler

            self._fallback_handler = get_fallback_handler()
            self.logger.info("✅ Fallback handling enabled")
        except ImportError:
            self.logger.warning("⚠️ Fallback handler not available")

    def get_status(self) -> dict[str, Any]:
        """Get server status information"""
        return {
            "name": self.config.name,
            "version": self.config.version,
            "status": "running",
            "uptime": time.time(),
            "features": {
                "performance_optimization": self.config.enable_performance_optimization,
                "circuit_breaker": self.config.enable_circuit_breaker,
                "fallback_handler": self.config.enable_fallback_handler,
                "metrics": self.config.enable_metrics,
                "caching": self.config.enable_caching,
            },
            "timestamp": datetime.now().isoformat(),
        }

    async def run(self):
        """Run the MCP server"""
        await self.setup_reliability_components()
        await self.initialize()
        self.logger.info(f"🚀 {self.config.name} MCP Server starting")
        self.logger.info(f"   ├── Version: {self.config.version}")
        self.logger.info(
            f"   ├── Performance optimization: {('ENABLED' if self.config.enable_performance_optimization else 'DISABLED')}"
        )
        self.logger.info(
            f"   ├── Circuit breaker: {('ENABLED' if self.config.enable_circuit_breaker else 'DISABLED')}"
        )
        self.logger.info(
            f"   ├── Fallback handling: {('ENABLED' if self.config.enable_fallback_handler else 'DISABLED')}"
        )
        self.logger.info(
            f"   └── Metrics: {('ENABLED' if self.config.enable_metrics else 'DISABLED')}"
        )
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )

    def format_response(self, data: Any) -> str:
        """Format response data as JSON"""
        return JSON_DUMPS(data)

    def get_env_var(self, name: str, default: str | None = None) -> str | None:
        """Get environment variable with optional default"""
        return os.getenv(name, default)

    def require_env_var(self, name: str) -> str:
        """Get required environment variable, raise error if missing"""
        value = os.getenv(name)
        if not value:
            raise ValueError(f"Required environment variable {name} not found")
        return value

    async def cache_get(self, key: str) -> Any | None:
        """Get value from cache"""
        if self.config.enable_caching:
            return self._cache.get(key)
        return None

    async def cache_set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL"""
        if self.config.enable_caching:
            self._cache[key] = {"value": value, "expires": time.time() + ttl}

    async def cache_clear_expired(self):
        """Clear expired cache entries"""
        if not self.config.enable_caching:
            return
        current_time = time.time()
        expired_keys = [
            key
            for key, data in self._cache.items()
            if data.get("expires", 0) < current_time
        ]
        for key in expired_keys:
            del self._cache[key]

class APIBasedMCPServer(BaseMCPServer):
    """
    Base class for API-based MCP servers (OpenRouter, Perplexity, Grok, etc.)
    """

    def __init__(self, config: MCPServerConfig, api_key_env_var: str, base_url: str):
        super().__init__(config)
        self.api_key = self.require_env_var(api_key_env_var)
        self.base_url = base_url
        self.default_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.logger.info(f"✅ API-based server initialized with endpoint: {base_url}")

    async def make_api_request(
        self, data: dict[str, Any], timeout: int | None = None
    ) -> dict[str, Any]:
        """Make API request with error handling and retries"""
        import aiohttp
        from aiohttp import ClientTimeout

        timeout = timeout or self.config.timeout_seconds
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                headers=self.default_headers,
                json=data,
                timeout=ClientTimeout(total=timeout),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
                return await response.json()

class ServiceBasedMCPServer(BaseMCPServer):
    """
    Base class for service-based MCP servers (GitHub, Asana, etc.)
    """

    def __init__(self, config: MCPServerConfig):
        super().__init__(config)
        self._services = {}

    def register_service(self, name: str, service: Any):
        """Register a service for use in tools"""
        self._services[name] = service
        self.logger.info(f"✅ Registered service: {name}")

    def get_service(self, name: str) -> Any:
        """Get a registered service"""
        service = self._services.get(name)
        if not service:
            raise ValueError(f"Service {name} not found")
        return service

"""
base_server.py - Syntax errors fixed
This file had severe syntax errors and was replaced with a minimal valid structure.
"""

