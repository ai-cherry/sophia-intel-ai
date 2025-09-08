# pydocstyle: ignore=D202,D400,D401
"""
Sophia AI Orchestrator Service
Cloud-first + AI-agent-first orchestration with performance patterns.
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager
from typing import Any

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import common patterns
from services.common import (
    BULKHEADS,
    AdaptiveCircuitBreaker,
    CircuitBreakerConfig,
    FourTierCacheManager,
    HedgedRequestManager,
    PredictivePrefetcher,
    ResponseFactory,
    ServiceResponse,
    instrument_service,
)

from .routing import ml_route_task


# Configuration
class OrchestratorConfig:
    """Orchestrator configuration"""

    # Service endpoints
    NEURAL_ENGINE_URL = os.getenv("NEURAL_ENGINE_URL", "http://neural-engine:8001")
    ENHANCED_SEARCH_URL = os.getenv("ENHANCED_SEARCH_URL", "http://enhanced-search:8004")
    CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://chat-service:8003")

    # Performance settings
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "100"))
    DEFAULT_TIMEOUT = float(os.getenv("DEFAULT_TIMEOUT", "30.0"))
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes

    # Circuit breaker settings
    CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5"))
    CIRCUIT_BREAKER_TIMEOUT = float(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60.0"))


# Request/Response models
class OrchestrationRequest(BaseModel):
    """Standard orchestration request"""

    task_type: str = Field(..., description="Type of task to orchestrate")
    payload: dict[str, Any] = Field(..., description="Task payload")
    priority: str = Field(default="normal", description="Task priority")
    timeout: float | None = Field(default=None, description="Request timeout")
    agent_preferences: dict[str, Any] | None = Field(
        default=None, description="Agent-specific preferences"
    )


class SwarmCoordinationRequest(BaseModel):
    """Swarm coordination request"""

    agents: list[str] = Field(..., description="List of agents to coordinate")
    workflow: dict[str, Any] = Field(..., description="Workflow definition")
    parallel: bool = Field(default=True, description="Execute agents in parallel")


# Global components
cache_manager = FourTierCacheManager()
hedged_manager = HedgedRequestManager()
prefetcher = PredictivePrefetcher()

# Circuit breakers for each service
circuit_breakers = {
    "neural-engine": AdaptiveCircuitBreaker(
        CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0)
    ),
    "enhanced-search": AdaptiveCircuitBreaker(
        CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30.0)
    ),
    "chat-service": AdaptiveCircuitBreaker(
        CircuitBreakerConfig(failure_threshold=5, recovery_timeout=45.0)
    ),
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    print("🚀 Starting Sophia AI Orchestrator")

    # Initialize cache connections
    await cache_manager.initialize()

    # Health check all services
    await perform_startup_health_checks()
    app.state.http_client = httpx.AsyncClient(timeout=OrchestratorConfig.DEFAULT_TIMEOUT)
    orchestrator.http_client = app.state.http_client

    try:
        yield
    finally:
        # Shutdown
        print("🛑 Shutting down Sophia AI Orchestrator")
        await app.state.http_client.aclose()
        await cache_manager.cleanup()


# FastAPI app
app = FastAPI(
    title="Sophia AI Orchestrator",
    description="Cloud-first + AI-agent-first orchestration service",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Core orchestration logic
class SophiaOrchestrator:
    """Main orchestrator class with performance patterns"""

    def __init__(self):
        self.http_client: httpx.AsyncClient | None = None
        self.active_tasks = {}
        self.performance_metrics = {}

    @instrument_service("orchestrator")
    async def orchestrate_task(self, request: OrchestrationRequest) -> ServiceResponse:
        """Main orchestration entry point"""
        start_time = time.time()

        try:
            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_result = await cache_manager.get(cache_key)

            if cached_result:
                return ServiceResponse.success_response(
                    data=cached_result,
                    service_name="orchestrator",
                    confidence=0.9,  # Slightly lower for cached results
                    duration_ms=(time.time() - start_time) * 1000,
                )

            # Route to appropriate handler
            result = await self._route_task(request)

            # Cache successful results
            if result.success:
                await cache_manager.set(cache_key, result.data, ttl=OrchestratorConfig.CACHE_TTL)

            # Record access pattern for prefetching
            prefetcher.record_access(cache_key, request.task_type)

            # Trigger predictive prefetching
            await prefetcher.prefetch_likely_next(cache_key, self._prefetch_handler)

            result.duration_ms = (time.time() - start_time) * 1000
            return result

        except Exception as e:
            return ServiceResponse.error_response(
                error=str(e),
                service_name="orchestrator",
                duration_ms=(time.time() - start_time) * 1000,
            )

    async def _route_task(self, request: OrchestrationRequest) -> ServiceResponse:
        """Route task to appropriate service with resilience patterns"""

        if request.task_type == "swarm_coordination":
            return await self._handle_swarm_coordination(request)

        target = await ml_route_task(request)
        if target == "enhanced-search":
            return await self._handle_search_task(request)
        if target == "chat-service":
            return await self._handle_chat_task(request)
        if target == "neural-engine":
            return await self._handle_inference_task(request)

        return ServiceResponse.error_response(
            error=f"Unknown task type: {request.task_type}", service_name="orchestrator"
        )

    async def _handle_search_task(self, request: OrchestrationRequest) -> ServiceResponse:
        """Handle search tasks with hedged requests"""

        # Primary search function
        async def primary_search():
            return await self._call_service_with_circuit_breaker(
                "enhanced-search",
                f"{OrchestratorConfig.ENHANCED_SEARCH_URL}/search",
                request.payload,
            )

        # Backup search functions (simplified search)
        async def backup_search():
            # Fallback to direct API calls if enhanced search fails
            return await self._fallback_search(request.payload.get("query", ""))

        # Use hedged requests for better latency
        try:
            result = await hedged_manager.hedged_request(
                primary_search, [backup_search], hedge_delay_ms=100  # Start backup after 100ms
            )
            return result
        except Exception as e:
            return ServiceResponse.error_response(
                error=f"All search attempts failed: {e!s}", service_name="orchestrator"
            )

    async def _handle_inference_task(self, request: OrchestrationRequest) -> ServiceResponse:
        """Handle neural inference tasks with bulkhead isolation"""

        # Use bulkhead to prevent inference overload
        async with BULKHEADS["neural_inference"]:
            return await self._call_service_with_circuit_breaker(
                "neural-engine",
                f"{OrchestratorConfig.NEURAL_ENGINE_URL}/api/v1/inference",
                request.payload,
            )

    async def _handle_chat_task(self, request: OrchestrationRequest) -> ServiceResponse:
        """Handle chat tasks with real-time optimization"""

        return await self._call_service_with_circuit_breaker(
            "chat-service", f"{OrchestratorConfig.CHAT_SERVICE_URL}/chat", request.payload
        )

    async def _handle_swarm_coordination(self, request: OrchestrationRequest) -> ServiceResponse:
        """Handle swarm coordination with parallel execution"""

        workflow = request.payload.get("workflow", {})
        agents = request.payload.get("agents", [])
        parallel = request.payload.get("parallel", True)

        if parallel:
            return await self._execute_parallel_swarm(agents, workflow)
        return await self._execute_sequential_swarm(agents, workflow)

    async def _execute_parallel_swarm(
        self, agents: list[str], workflow: dict[str, Any]
    ) -> ServiceResponse:
        """Execute swarm agents in parallel"""

        tasks = []
        for agent in agents:
            task = asyncio.create_task(self._execute_agent(agent, workflow))
            tasks.append(task)

        # Wait for all agents to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        successful_results = []
        errors = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(f"Agent {agents[i]}: {result!s}")
            elif isinstance(result, ServiceResponse) and result.success:
                successful_results.append(result.data)
            else:
                errors.append(f"Agent {agents[i]}: Failed")

        # Determine overall success
        if successful_results:
            confidence = len(successful_results) / len(agents)
            return ServiceResponse.success_response(
                data={"results": successful_results, "errors": errors, "success_rate": confidence},
                service_name="orchestrator",
                confidence=confidence,
            )
        return ServiceResponse.error_response(
            error=f"All agents failed: {errors}", service_name="orchestrator"
        )

    async def _execute_sequential_swarm(
        self, agents: list[str], workflow: dict[str, Any]
    ) -> ServiceResponse:
        """Execute swarm agents sequentially with context passing"""

        context = workflow.copy()
        results = []

        for agent in agents:
            try:
                result = await self._execute_agent(agent, context)
                if result.success:
                    results.append(result.data)
                    # Pass result to next agent
                    context["previous_result"] = result.data
                else:
                    return ServiceResponse.error_response(
                        error=f"Agent {agent} failed: {result.error}", service_name="orchestrator"
                    )
            except Exception as e:
                return ServiceResponse.error_response(
                    error=f"Agent {agent} exception: {e!s}", service_name="orchestrator"
                )

        return ServiceResponse.success_response(
            data={"results": results, "final_context": context},
            service_name="orchestrator",
            confidence=1.0,
        )

    async def _execute_agent(self, agent: str, context: dict[str, Any]) -> ServiceResponse:
        """Execute individual agent with context"""

        # Route to appropriate service based on agent type
        if agent == "search":
            return await self._call_service_with_circuit_breaker(
                "enhanced-search", f"{OrchestratorConfig.ENHANCED_SEARCH_URL}/search", context
            )
        if agent == "neural":
            return await self._call_service_with_circuit_breaker(
                "neural-engine", f"{OrchestratorConfig.NEURAL_ENGINE_URL}/api/v1/inference", context
            )
        if agent == "chat":
            return await self._call_service_with_circuit_breaker(
                "chat-service", f"{OrchestratorConfig.CHAT_SERVICE_URL}/chat", context
            )
        return ServiceResponse.error_response(
            error=f"Unknown agent type: {agent}", service_name="orchestrator"
        )

    async def _call_service_with_circuit_breaker(
        self, service_name: str, url: str, payload: dict[str, Any]
    ) -> ServiceResponse:
        """Call service with circuit breaker protection"""

        circuit_breaker = circuit_breakers.get(service_name)
        if not circuit_breaker:
            return ServiceResponse.error_response(
                error=f"No circuit breaker configured for {service_name}",
                service_name="orchestrator",
            )

        async def service_call():
            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

        try:
            result_data = await circuit_breaker.call(service_call)
            return ServiceResponse.success_response(
                data=result_data, service_name="orchestrator", sources=[service_name]
            )
        except Exception as e:
            return ServiceResponse.error_response(
                error=f"Service {service_name} failed: {e!s}", service_name="orchestrator"
            )

    async def _fallback_search(self, query: str) -> ServiceResponse:
        """Fallback search implementation"""
        # Simple fallback that could call APIs directly
        return ServiceResponse.partial_response(
            data={"results": [], "fallback": True},
            service_name="orchestrator",
            confidence=0.3,
            error="Using fallback search due to service unavailability",
        )

    def _generate_cache_key(self, request: OrchestrationRequest) -> str:
        """Generate cache key for request"""
        import hashlib
        import json

        # Create deterministic key from request
        key_data = {"task_type": request.task_type, "payload": request.payload}
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def _prefetch_handler(self, key: str):
        """Handle predictive prefetching."""
        # Implement prefetching logic based on access patterns


# Global orchestrator instance
orchestrator = SophiaOrchestrator()


# API endpoints
@app.post("/orchestrate", response_model=dict[str, Any])
@instrument_service("orchestrator")
async def orchestrate_endpoint(request: OrchestrationRequest) -> dict[str, Any]:
    """Handle orchestration requests."""
    result = await orchestrator.orchestrate_task(request)
    return result.to_dict()


@app.post("/swarm", response_model=dict[str, Any])
@instrument_service("orchestrator")
async def swarm_coordination_endpoint(request: SwarmCoordinationRequest) -> dict[str, Any]:
    """Coordinate swarm requests."""
    orchestration_request = OrchestrationRequest(
        task_type="swarm_coordination",
        payload={
            "agents": request.agents,
            "workflow": request.workflow,
            "parallel": request.parallel,
        },
    )

    result = await orchestrator.orchestrate_task(orchestration_request)
    return result.to_dict()


@app.get("/health")
async def health_check():
    """Return orchestrator health status."""
    return ResponseFactory.create_health_response(
        service_name="orchestrator",
        status="healthy",
        dependencies={
            "neural-engine": "unknown",
            "enhanced-search": "unknown",
            "chat-service": "unknown",
        },
        resource_usage={"cpu_percent": 0.0, "memory_percent": 0.0},
        uptime_seconds=time.time(),
    ).to_dict()


@app.get("/metrics")
async def metrics_endpoint():
    """Return monitoring metrics."""
    return {
        "active_tasks": len(orchestrator.active_tasks),
        "circuit_breaker_states": {name: cb.state.value for name, cb in circuit_breakers.items()},
        "cache_stats": await cache_manager.get_stats(),
        "performance_metrics": orchestrator.performance_metrics,
    }


async def perform_startup_health_checks():
    """Perform health checks on startup."""
    print("🔍 Performing startup health checks...")

    services = [
        ("neural-engine", f"{OrchestratorConfig.NEURAL_ENGINE_URL}/health"),
        ("enhanced-search", f"{OrchestratorConfig.ENHANCED_SEARCH_URL}/health"),
        ("chat-service", f"{OrchestratorConfig.CHAT_SERVICE_URL}/health"),
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        for service_name, health_url in services:
            try:
                response = await client.get(health_url)
                if response.status_code == 200:
                    print(f"✅ {service_name}: healthy")
                else:
                    print(f"⚠️ {service_name}: degraded (HTTP {response.status_code})")
            except Exception as e:
                print(f"❌ {service_name}: unhealthy ({e!s})")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="${BIND_IP}",
        port=8002,
        reload=False,
        workers=1,
        loop="uvloop",
        http="httptools",
    )
