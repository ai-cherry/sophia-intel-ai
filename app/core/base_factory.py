"""
Base Agent Factory - Shared Foundation for Sophia and 
Provides common functionality for both domain factories:
- MCP server connectivity and management
- Model routing and fallback mechanisms
- Performance monitoring and metrics
- Cost tracking and optimization
- WebSocket real-time updates
"""
import contextlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4
import httpx
from fastapi import HTTPException, WebSocket
# Import MCP connection management
from app.mcp.connection_manager import (
    CircuitBreaker,
    CircuitBreakerConfig,
    Connection,
)
# Import monitoring and metrics (optional)
try:
    from app.core.monitoring import MetricsCollector, PerformanceTracker
except ImportError:
    MetricsCollector = None
    PerformanceTracker = None
logger = logging.getLogger(__name__)
# ==============================================================================
# BASE CONFIGURATION MODELS
# ==============================================================================
@dataclass
class ModelConfig:
    """Configuration for an LLM model"""
    provider: str
    model: str
    api_key: str
    endpoint: str
    virtual_key: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 60
    cost_per_1k_tokens: float = 0.0
    fallback_models: list[str] = field(default_factory=list)
@dataclass
class AgentConfig:
    """Base configuration for an agent"""
    id: str
    name: str
    role: str
    description: str
    model_config: ModelConfig
    capabilities: list[str]
    tools: list[str]
    personality_traits: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
@dataclass
class SwarmConfig:
    """Configuration for an agent swarm"""
    id: str
    name: str
    description: str
    agents: list[AgentConfig]
    execution_strategy: str
    coordination_model: str
    max_parallel: int = 5
    timeout: int = 300
class AgentStatus(str, Enum):
    """Agent operational status"""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"
# ==============================================================================
# MCP INTEGRATION MANAGER
# ==============================================================================
class MCPIntegrationManager:
    """
    Manages MCP server connections for agent factories
    Provides real file access and code intelligence
    """
    def __init__(self):
        self.connections: dict[str, Connection] = {}
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.health_status: dict[str, bool] = {}
        # MCP Server configurations
        self.mcp_configs = {
            "filesystem": {
                "port": 8001,
                "endpoint": "http://localhost:8001",
                "capabilities": [
                    "read_file",
                    "write_file",
                    "list_directory",
                    "search_files",
                ],
            },
            "git": {
                "port": 8002,
                "endpoint": "http://localhost:8002",
                "capabilities": ["git_status", "git_diff", "git_commit", "git_history"],
            },
            "code_intelligence": {
                "port": 8003,
                "endpoint": "http://localhost:8003",
                "capabilities": [
                    "semantic_search",
                    "dependency_analysis",
                    "symbol_lookup",
                ],
            },
            "memory": {
                "port": 8004,
                "endpoint": "http://localhost:8004",
                "capabilities": ["store_context", "retrieve_context", "search_memory"],
            },
        }
        logger.info("🔌 MCP Integration Manager initialized")
    async def connect_all(self) -> dict[str, bool]:
        """Connect to all MCP servers"""
        results = {}
        for server_name, config in self.mcp_configs.items():
            try:
                connection = await self._create_connection(server_name, config)
                self.connections[server_name] = connection
                self.health_status[server_name] = True
                results[server_name] = True
                logger.info(f"✅ Connected to MCP server: {server_name}")
            except Exception as e:
                logger.error(f"❌ Failed to connect to {server_name}: {e}")
                self.health_status[server_name] = False
                results[server_name] = False
        return results
    async def _create_connection(self, name: str, config: dict[str, Any]) -> Connection:
        """Create MCP server connection with circuit breaker"""
        # Initialize circuit breaker
        cb_config = CircuitBreakerConfig(
            failure_threshold=3, success_threshold=2, timeout=30, half_open_requests=2
        )
        self.circuit_breakers[name] = CircuitBreaker(name, cb_config)
        # Test connection
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{config['endpoint']}/health")
            if response.status_code != 200:
                raise ConnectionError(f"MCP server {name} health check failed")
        # Create connection object
        return Connection(
            id=f"mcp_{name}_{uuid4().hex[:8]}",
            server_name=name,
            endpoint=config["endpoint"],
            created_at=datetime.now(),
            last_used=datetime.now(),
            metadata={"capabilities": config["capabilities"]},
        )
    async def execute_mcp_operation(
        self, server: str, operation: str, params: dict[str, Any]
    ) -> Any:
        """Execute operation on MCP server with circuit breaker protection"""
        if server not in self.connections:
            raise ValueError(f"MCP server {server} not connected")
        if not self.health_status.get(server, False):
            raise ConnectionError(f"MCP server {server} is unhealthy")
        circuit_breaker = self.circuit_breakers[server]
        connection = self.connections[server]
        async def _execute():
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{connection.endpoint}/{operation}", json=params, timeout=30
                )
                if response.status_code == 200:
                    connection.last_used = datetime.now()
                    return response.json()
                else:
                    raise HTTPException(
                        status_code=response.status_code, detail=response.text
                    )
        return await circuit_breaker.async_call(_execute)
    def get_connection_status(self) -> dict[str, Any]:
        """Get status of all MCP connections"""
        return {
            "connections": {
                name: {
                    "connected": name in self.connections,
                    "healthy": self.health_status.get(name, False),
                    "circuit_breaker": (
                        self.circuit_breakers.get(name).state.value
                        if name in self.circuit_breakers
                        else None
                    ),
                    "last_used": (
                        self.connections[name].last_used.isoformat()
                        if name in self.connections
                        else None
                    ),
                }
                for name in self.mcp_configs
            },
            "summary": {
                "total": len(self.mcp_configs),
                "connected": len(self.connections),
                "healthy": sum(1 for h in self.health_status.values() if h),
            },
        }
# ==============================================================================
# MODEL ROUTER
# ==============================================================================
class ModelRouter:
    """
    Intelligent model routing with fallback and cost optimization
    """
    def __init__(self):
        self.model_configs: dict[str, ModelConfig] = self._initialize_models()
        self.usage_stats: dict[str, dict[str, Any]] = {}
        self.total_cost = 0.0
    def _initialize_models(self) -> dict[str, ModelConfig]:
        """Initialize all available models"""
        return {
            # Tier 1: Fast models
            "llama-4-scout": ModelConfig(
                provider="AIMLAPI",
                model="meta-llama/llama-4-scout",
                api_key=os.environ.get("AIMLAPI_API_KEY", ""),
                endpoint="https://api.aimlapi.com/v2/chat/completions",
                cost_per_1k_tokens=0.02,
                fallback_models=["llama-4-maverick", "gpt-4o-mini"],
            ),
            # Tier 2: Quality models
            "grok-code-fast": ModelConfig(
                provider="OpenRouter",
                model="x-ai/grok-code-fast-1",
                api_key=os.environ.get("OPENROUTER_API_KEY", ""),
                endpoint="https://openrouter.ai/api/v1/chat/completions",
                cost_per_1k_tokens=0.05,
                fallback_models=["gemini-2.0-flash", "gpt-4o"],
            ),
            "gemini-2.0-flash": ModelConfig(
                provider="OpenRouter",
                model="google/gemini-2.0-flash-exp",
                api_key=os.environ.get("OPENROUTER_API_KEY", ""),
                endpoint="https://openrouter.ai/api/v1/chat/completions",
                cost_per_1k_tokens=0.04,
                fallback_models=["grok-code-fast", "gpt-4o"],
            ),
            # Tier 3: Validation models
            "gpt-4o-mini": ModelConfig(
                provider="Portkey",
                model="gpt-4o-mini",
                api_key=os.environ.get("PORTKEY_API_KEY", ""),
                endpoint="https://api.portkey.ai/v1/chat/completions",
                virtual_key="openai-vk-190a60",
                cost_per_1k_tokens=0.03,
                fallback_models=["llama-4-maverick"],
            ),
            # Business models for Sophia
            "perplexity-sonar": ModelConfig(
                provider="Portkey",
                model="perplexity/llama-3.1-sonar-large-128k-online",
                api_key=os.environ.get("PORTKEY_API_KEY", ""),
                endpoint="https://api.portkey.ai/v1/chat/completions",
                virtual_key="perplexity-vk-56c172",
                cost_per_1k_tokens=0.06,
                fallback_models=["claude-3-5-sonnet"],
            ),
            "claude-3-5-sonnet": ModelConfig(
                provider="Portkey",
                model="anthropic/claude-3-5-sonnet-20241022",
                api_key=os.environ.get("PORTKEY_API_KEY", ""),
                endpoint="https://api.portkey.ai/v1/chat/completions",
                virtual_key="anthropic-vk-b42804",
                cost_per_1k_tokens=0.08,
                fallback_models=["gpt-4o"],
            ),
        }
    async def route_request(
        self, preferred_model: str, prompt: str, context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Route request to appropriate model with fallback"""
        if preferred_model not in self.model_configs:
            raise ValueError(f"Unknown model: {preferred_model}")
        config = self.model_configs[preferred_model]
        models_to_try = [preferred_model] + config.fallback_models
        for model_name in models_to_try:
            try:
                model_config = self.model_configs.get(model_name)
                if not model_config:
                    continue
                result = await self._call_model(model_config, prompt, context)
                # Track usage
                self._track_usage(
                    model_name, result.get("tokens", 0), model_config.cost_per_1k_tokens
                )
                return result
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}, trying fallback")
                continue
        raise HTTPException(status_code=503, detail="All models failed")
    async def _call_model(
        self, config: ModelConfig, prompt: str, context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Call specific model API"""
        headers = {"Content-Type": "application/json"}
        # Provider-specific headers
        if config.provider == "Portkey":
            headers.update(
                {
                    "x-portkey-api-key": config.api_key,
                    "x-portkey-virtual-key": config.virtual_key,
                    "x-portkey-provider": config.model.split("/")[0],
                }
            )
        elif config.provider == "OpenRouter":
            headers.update(
                {
                    "Authorization": f"Bearer {config.api_key}",
                    "HTTP-Referer": "https://sophia-intel-ai.com",
                    "X-Title": "Agent Factory",
                }
            )
        else:
            headers["Authorization"] = f"Bearer {config.api_key}"
        # Build request
        request_data = {
            "model": config.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
        }
        if context:
            request_data["context"] = context
        # Execute request
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.post(
                config.endpoint, headers=headers, json=request_data
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "content": data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", ""),
                    "tokens": data.get("usage", {}).get("total_tokens", 0),
                    "model_used": config.model,
                    "provider": config.provider,
                }
            else:
                raise HTTPException(
                    status_code=response.status_code, detail=response.text
                )
    def _track_usage(self, model: str, tokens: int, cost_per_1k: float):
        """Track model usage and costs"""
        if model not in self.usage_stats:
            self.usage_stats[model] = {"calls": 0, "total_tokens": 0, "total_cost": 0.0}
        stats = self.usage_stats[model]
        stats["calls"] += 1
        stats["total_tokens"] += tokens
        cost = (tokens / 1000) * cost_per_1k
        stats["total_cost"] += cost
        self.total_cost += cost
    def get_usage_report(self) -> dict[str, Any]:
        """Get model usage and cost report"""
        return {
            "models": self.usage_stats,
            "total_cost": round(self.total_cost, 4),
            "total_calls": sum(s["calls"] for s in self.usage_stats.values()),
            "total_tokens": sum(s["total_tokens"] for s in self.usage_stats.values()),
        }
# ==============================================================================
# BASE AGENT FACTORY
# ==============================================================================
class BaseAgentFactory:
    """
    Base factory class for both Sophia and  factories
    Provides shared functionality and infrastructure
    """
    def __init__(self, domain: str = "base"):
        self.domain = domain
        self.factory_id = f"{domain}_factory_{uuid4().hex[:8]}"
        # Core components
        self.mcp_manager = MCPIntegrationManager()
        self.model_router = ModelRouter()
        self.metrics_collector = MetricsCollector if MetricsCollector else None
        # Agent and swarm registries
        self.agents: dict[str, AgentConfig] = {}
        self.swarms: dict[str, SwarmConfig] = {}
        self.agent_status: dict[str, AgentStatus] = {}
        # Performance tracking
        self.performance_metrics: dict[str, Any] = {
            "agents_created": 0,
            "swarms_created": 0,
            "tasks_executed": 0,
            "total_execution_time": 0.0,
            "errors": 0,
            "success_rate": 1.0,
        }
        # WebSocket connections for real-time updates
        self.websocket_connections: set[WebSocket] = set()
        # Initialize timestamp
        self.initialized_at = datetime.now()
        logger.info(f"🏭 {domain.upper()} Base Factory initialized: {self.factory_id}")
    async def initialize(self) -> dict[str, Any]:
        """Initialize factory components"""
        initialization_results = {
            "factory_id": self.factory_id,
            "domain": self.domain,
            "timestamp": datetime.now().isoformat(),
        }
        # Connect to MCP servers
        mcp_results = await self.mcp_manager.connect_all()
        initialization_results["mcp_connections"] = mcp_results
        # Test model router
        model_count = len(self.model_router.model_configs)
        initialization_results["models_available"] = model_count
        # Set factory as ready
        initialization_results["status"] = "ready"
        logger.info(f"✅ {self.domain.upper()} Factory initialized successfully")
        return initialization_results
    async def create_agent(
        self,
        name: str,
        role: str,
        model: str,
        capabilities: list[str],
        tools: list[str] = None,
        personality: dict[str, Any] = None,
    ) -> str:
        """Create a new agent"""
        agent_id = f"{self.domain}_agent_{uuid4().hex[:8]}"
        # Get model configuration
        if model not in self.model_router.model_configs:
            raise ValueError(f"Unknown model: {model}")
        model_config = self.model_router.model_configs[model]
        # Create agent configuration
        agent_config = AgentConfig(
            id=agent_id,
            name=name,
            role=role,
            description=f"{name} - {role} agent for {self.domain}",
            model_config=model_config,
            capabilities=capabilities,
            tools=tools or [],
            personality_traits=personality or {},
        )
        # Register agent
        self.agents[agent_id] = agent_config
        self.agent_status[agent_id] = AgentStatus.IDLE
        # Update metrics
        self.performance_metrics["agents_created"] += 1
        # Broadcast to WebSockets
        await self._broadcast_update(
            {
                "event": "agent_created",
                "agent_id": agent_id,
                "name": name,
                "domain": self.domain,
            }
        )
        logger.info(f"🤖 Created agent: {name} ({agent_id})")
        return agent_id
    async def execute_task(
        self, agent_id: str, task: str, context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Execute task with an agent"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        agent = self.agents[agent_id]
        start_time = datetime.now()
        # Update agent status
        self.agent_status[agent_id] = AgentStatus.ACTIVE
        try:
            # Route to model
            result = await self.model_router.route_request(
                agent.model_config.model, task, context
            )
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            # Update metrics
            self.performance_metrics["tasks_executed"] += 1
            self.performance_metrics["total_execution_time"] += execution_time
            # Update agent status
            self.agent_status[agent_id] = AgentStatus.IDLE
            return {
                "success": True,
                "agent_id": agent_id,
                "agent_name": agent.name,
                "result": result["content"],
                "execution_time": execution_time,
                "model_used": result["model_used"],
                "tokens": result.get("tokens", 0),
            }
        except Exception as e:
            # Update error metrics
            self.performance_metrics["errors"] += 1
            self.performance_metrics["success_rate"] = self.performance_metrics[
                "tasks_executed"
            ] / (
                self.performance_metrics["tasks_executed"]
                + self.performance_metrics["errors"]
            )
            # Update agent status
            self.agent_status[agent_id] = AgentStatus.ERROR
            logger.error(f"Task execution failed for {agent_id}: {e}")
            return {
                "success": False,
                "agent_id": agent_id,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds(),
            }
    async def create_swarm(
        self,
        name: str,
        description: str,
        agent_ids: list[str],
        strategy: str = "parallel",
    ) -> str:
        """Create an agent swarm"""
        swarm_id = f"{self.domain}_swarm_{uuid4().hex[:8]}"
        # Validate agents exist
        for agent_id in agent_ids:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
        # Get agent configs
        swarm_agents = [self.agents[aid] for aid in agent_ids]
        # Create swarm configuration
        swarm_config = SwarmConfig(
            id=swarm_id,
            name=name,
            description=description,
            agents=swarm_agents,
            execution_strategy=strategy,
            coordination_model="autonomous" if strategy == "parallel" else "sequential",
        )
        # Register swarm
        self.swarms[swarm_id] = swarm_config
        # Update metrics
        self.performance_metrics["swarms_created"] += 1
        logger.info(
            f"🐝 Created swarm: {name} with {len(agent_ids)} agents ({swarm_id})"
        )
        return swarm_id
    async def _broadcast_update(self, message: dict[str, Any]):
        """Broadcast update to all connected WebSockets"""
        if not self.websocket_connections:
            return
        message_json = json.dumps(message)
        disconnected = set()
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message_json)
            except Exception:
                disconnected.add(websocket)
        # Remove disconnected websockets
        self.websocket_connections -= disconnected
    def get_factory_status(self) -> dict[str, Any]:
        """Get comprehensive factory status"""
        uptime = (datetime.now() - self.initialized_at).total_seconds()
        return {
            "factory_id": self.factory_id,
            "domain": self.domain,
            "uptime_seconds": uptime,
            "agents": {
                "total": len(self.agents),
                "by_status": {
                    status.value: sum(
                        1 for s in self.agent_status.values() if s == status
                    )
                    for status in AgentStatus
                },
            },
            "swarms": {
                "total": len(self.swarms),
                "total_agents_in_swarms": sum(
                    len(s.agents) for s in self.swarms.values()
                ),
            },
            "performance": self.performance_metrics,
            "mcp_status": self.mcp_manager.get_connection_status(),
            "model_usage": self.model_router.get_usage_report(),
            "websocket_connections": len(self.websocket_connections),
        }
    async def shutdown(self):
        """Gracefully shutdown factory"""
        logger.info(f"🔌 Shutting down {self.domain} factory...")
        # Close WebSocket connections
        for ws in self.websocket_connections:
            with contextlib.suppress(Exception):
                await ws.close()
        # Log final metrics
        logger.info(f"Final metrics: {self.performance_metrics}")
        logger.info(f"✅ {self.domain} factory shutdown complete")
# ==============================================================================
# FACTORY CREATION HELPERS
# ==============================================================================
def create_base_factory(domain: str = "base") -> BaseAgentFactory:
    """Create a base factory instance"""
    return BaseAgentFactory(domain)
async def initialize_factory(factory: BaseAgentFactory) -> dict[str, Any]:
    """Initialize a factory with all components"""
    return await factory.initialize()
# ==============================================================================
# END OF BASE FACTORY
# ==============================================================================
