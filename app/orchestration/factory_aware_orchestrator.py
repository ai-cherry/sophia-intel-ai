"""Factory-Aware Orchestrator: Unified AI orchestration with agent factory integration.

This module provides the central orchestration layer that makes Sophia and Artemis
fully aware of their agent factory capabilities, enabling dynamic agent spawning,
real-time activity broadcasting, and continuous learning.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

import redis.asyncio as redis
from fastapi import WebSocket

# Artemis import removed
from app.core.circuit_breaker import with_circuit_breaker
from app.memory.unified_memory_router import UnifiedMemoryRouter
from app.sophia.agent_factory import SophiaBusinessAgentFactory

logger = logging.getLogger(__name__)


class RequestType(Enum):
    """Types of requests the orchestrator can handle."""

    BUSINESS_ANALYSIS = "business_analysis"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DATA_VISUALIZATION = "data_visualization"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    HYBRID = "hybrid"


class AgentActivity(Enum):
    """Types of agent activities for broadcasting."""

    SPAWNED = "agent_spawned"
    TASK_ASSIGNED = "task_assigned"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETE = "execution_complete"
    COLLABORATION_STARTED = "collaboration_started"
    LEARNING_TRIGGERED = "learning_triggered"


@dataclass
class OrchestratorRequest:
    """Request to the factory-aware orchestrator."""

    id: str
    type: RequestType
    content: str
    context: dict[str, Any]
    user_id: str
    session_id: str
    timestamp: datetime = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow()
        if not self.id:
            self.id = str(uuid4())


@dataclass
class AgentSpawnEvent:
    """Event broadcast when agents are spawned."""

    factory: str  # 'sophia' or 'artemis'
    agents: list[str]  # Agent IDs
    purpose: str
    complexity: str
    estimated_cost: float
    timestamp: datetime = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


@dataclass
class ExecutionEvent:
    """Event broadcast during execution."""

    event_type: AgentActivity
    agent_id: str
    task_id: str
    status: str
    details: dict[str, Any]
    metrics: dict[str, float]
    timestamp: datetime = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


class EventBroadcaster:
    """Broadcasts events to connected WebSocket clients."""

    def __init__(self):
        self.connections: set[WebSocket] = set()
        self.redis_client = None
        self.event_queue = asyncio.Queue()
        self.broadcast_task = None

    async def initialize(self):
        """Initialize the event broadcaster."""
        try:
            self.redis_client = await redis.from_url(
                "redis://localhost:6379", decode_responses=True
            )
            self.broadcast_task = asyncio.create_task(self._broadcast_loop())
            logger.info("EventBroadcaster initialized")
        except Exception as e:
            logger.error(f"Failed to initialize EventBroadcaster: {e}")

    async def add_connection(self, websocket: WebSocket):
        """Add a WebSocket connection."""
        await websocket.accept()
        self.connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.connections)}")

    async def remove_connection(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.connections.discard(websocket)
        logger.info(
            f"WebSocket disconnected. Total connections: {len(self.connections)}"
        )

    async def publish(self, event_type: str, data: dict[str, Any]):
        """Publish an event to all connected clients."""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Add to queue for broadcasting
        await self.event_queue.put(event)

        # Also publish to Redis for persistence
        if self.redis_client:
            await self.redis_client.publish(
                f"orchestrator:{event_type}", json.dumps(event)
            )

    async def _broadcast_loop(self):
        """Continuously broadcast events from the queue."""
        while True:
            try:
                event = await self.event_queue.get()

                # Broadcast to all connected WebSockets
                disconnected = set()
                for websocket in self.connections:
                    try:
                        await websocket.send_json(event)
                    except Exception:
                        disconnected.add(websocket)

                # Remove disconnected clients
                self.connections -= disconnected

            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(1)


class ComplexityAnalyzer:
    """Analyzes request complexity for agent selection."""

    @staticmethod
    def analyze(request: OrchestratorRequest) -> dict[str, Any]:
        """Analyze the complexity of a request."""
        len(request.content)
        word_count = len(request.content.split())

        # Determine complexity based on various factors
        complexity_score = 0.0

        # Length-based complexity
        if word_count > 500:
            complexity_score += 0.3
        elif word_count > 200:
            complexity_score += 0.2
        elif word_count > 50:
            complexity_score += 0.1

        # Type-based complexity
        complex_types = {
            RequestType.SECURITY_AUDIT: 0.4,
            RequestType.PERFORMANCE_OPTIMIZATION: 0.3,
            RequestType.CODE_GENERATION: 0.3,
            RequestType.HYBRID: 0.5,
        }
        complexity_score += complex_types.get(request.type, 0.1)

        # Context-based complexity
        if request.context.get("multi_source", False):
            complexity_score += 0.2
        if request.context.get("real_time", False):
            complexity_score += 0.1
        if request.context.get("critical", False):
            complexity_score += 0.3

        # Normalize score
        complexity_score = min(1.0, complexity_score)

        # Determine category
        if complexity_score >= 0.7:
            category = "high"
            recommended_agents = 3
        elif complexity_score >= 0.4:
            category = "medium"
            recommended_agents = 2
        else:
            category = "low"
            recommended_agents = 1

        return {
            "score": complexity_score,
            "category": category,
            "recommended_agents": recommended_agents,
            "estimated_tokens": word_count * 4,  # Rough estimate
            "estimated_time": complexity_score * 30,  # Seconds
        }


class FactoryAwareOrchestrator:
    """Main orchestrator with full factory awareness and event broadcasting."""

    def __init__(self):
        self.sophia_factory = SophiaBusinessAgentFactory()
        self.artemis_factory = None  # ArtemisAgentFactory removed
        self.event_broadcaster = EventBroadcaster()
        self.memory_router = UnifiedMemoryRouter()
        self.complexity_analyzer = ComplexityAnalyzer()

        # Active executions tracking
        self.active_executions: dict[str, dict[str, Any]] = {}
        self.agent_performance: dict[str, list[float]] = {}

        # Learning components (will be expanded)
        self.execution_patterns: list[dict[str, Any]] = []
        self.optimization_suggestions: list[dict[str, Any]] = []

        logger.info(
            "FactoryAwareOrchestrator initialized with full factory integration"
        )

    async def initialize(self):
        """Initialize the orchestrator and its components."""
        await self.event_broadcaster.initialize()
        logger.info("FactoryAwareOrchestrator fully initialized")

    @with_circuit_breaker("orchestrator")
    async def process_request(self, request: OrchestratorRequest) -> dict[str, Any]:
        """Process a request with full factory awareness and broadcasting."""
        try:
            # Analyze complexity
            complexity = self.complexity_analyzer.analyze(request)

            # Broadcast request received
            await self.event_broadcaster.publish(
                "request_received",
                {
                    "request_id": request.id,
                    "type": request.type.value,
                    "complexity": complexity,
                    "user_id": request.user_id,
                },
            )

            # Determine which factory to use
            factory_type = self._determine_factory(request)

            # Spawn appropriate agents
            if factory_type == "sophia":
                agents = await self._spawn_sophia_agents(request, complexity)
            elif factory_type == "artemis":
                agents = await self._spawn_artemis_agents(request, complexity)
            else:  # hybrid
                agents = await self._spawn_hybrid_agents(request, complexity)

            # Broadcast agent spawn event
            spawn_event = AgentSpawnEvent(
                factory=factory_type,
                agents=[a["id"] for a in agents],
                purpose=request.type.value,
                complexity=complexity["category"],
                estimated_cost=self._estimate_cost(agents, complexity),
            )

            await self.event_broadcaster.publish("agents_spawned", spawn_event.__dict__)

            # Execute with real-time streaming
            result = await self._execute_with_streaming(agents, request)

            # Store execution for learning
            await self._store_execution(request, agents, result)

            # Trigger learning if appropriate
            if self._should_trigger_learning():
                asyncio.create_task(self._trigger_learning())

            return {
                "request_id": request.id,
                "result": result,
                "agents_used": agents,
                "complexity": complexity,
                "factory": factory_type,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error processing request {request.id}: {e}")
            await self.event_broadcaster.publish(
                "error", {"request_id": request.id, "error": str(e)}
            )
            raise

    def _determine_factory(self, request: OrchestratorRequest) -> str:
        """Determine which factory to use based on request type."""
        business_types = {RequestType.BUSINESS_ANALYSIS, RequestType.DATA_VISUALIZATION}
        technical_types = {
            RequestType.CODE_GENERATION,
            RequestType.CODE_REVIEW,
            RequestType.SECURITY_AUDIT,
            RequestType.PERFORMANCE_OPTIMIZATION,
        }

        if request.type in business_types:
            return "sophia"
        elif request.type in technical_types:
            return "artemis"
        else:
            return "hybrid"

    async def _spawn_sophia_agents(
        self, request: OrchestratorRequest, complexity: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Spawn Sophia business agents."""
        agents = []
        num_agents = complexity["recommended_agents"]

        # Select appropriate agent templates based on request type
        if request.type == RequestType.BUSINESS_ANALYSIS:
            template_ids = ["sales_pipeline_analyst", "revenue_forecaster"]
        elif request.type == RequestType.DATA_VISUALIZATION:
            template_ids = ["market_research_specialist"]
        else:
            template_ids = ["client_success_manager"]

        # Create agents
        for i in range(min(num_agents, len(template_ids))):
            agent_id = await self.sophia_factory.create_business_agent(
                template_ids[i], custom_config={"request_context": request.context}
            )
            agents.append(
                {"id": agent_id, "template": template_ids[i], "factory": "sophia"}
            )

        return agents

    async def _spawn_artemis_agents(
        self, request: OrchestratorRequest, complexity: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Spawn Artemis technical agents."""
        agents = []
        num_agents = complexity["recommended_agents"]

        # Select appropriate agent templates based on request type
        if request.type == RequestType.CODE_REVIEW:
            template_names = ["code_reviewer", "security_auditor"]
        elif request.type == RequestType.CODE_GENERATION:
            template_names = ["code_refactoring_specialist"]
        elif request.type == RequestType.SECURITY_AUDIT:
            template_names = ["security_auditor", "vulnerability_scanner"]
        else:
            template_names = ["performance_optimizer"]

        # Create agents
        for i in range(min(num_agents, len(template_names))):
            agent_id = await self.artemis_factory.create_technical_agent(
                template_names[i], custom_config={"request_context": request.context}
            )
            agents.append(
                {"id": agent_id, "template": template_names[i], "factory": "artemis"}
            )

        return agents

    async def _spawn_hybrid_agents(
        self, request: OrchestratorRequest, complexity: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Spawn both Sophia and Artemis agents for hybrid requests."""
        sophia_agents = await self._spawn_sophia_agents(
            request, {**complexity, "recommended_agents": 1}
        )
        artemis_agents = await self._spawn_artemis_agents(
            request, {**complexity, "recommended_agents": 1}
        )
        return sophia_agents + artemis_agents

    async def _execute_with_streaming(
        self, agents: list[dict[str, Any]], request: OrchestratorRequest
    ) -> dict[str, Any]:
        """Execute request with real-time streaming updates."""
        execution_id = str(uuid4())
        self.active_executions[execution_id] = {
            "request_id": request.id,
            "agents": agents,
            "started": datetime.utcnow(),
            "status": "running",
        }

        # Broadcast execution start
        await self.event_broadcaster.publish(
            "execution_started",
            {"execution_id": execution_id, "request_id": request.id, "agents": agents},
        )

        try:
            # Simulate execution with streaming updates
            # In production, this would call actual agent execution
            results = {}
            for agent in agents:
                # Broadcast agent task assignment
                await self.event_broadcaster.publish(
                    "task_assigned",
                    {
                        "agent_id": agent["id"],
                        "task": request.content[:100],  # Truncated for brevity
                        "execution_id": execution_id,
                    },
                )

                # Simulate processing
                await asyncio.sleep(1)  # Replace with actual agent execution

                # Store result
                results[agent["id"]] = {
                    "response": f"Processed by {agent['template']}",
                    "confidence": 0.85,
                    "tokens_used": 150,
                }

                # Broadcast completion
                await self.event_broadcaster.publish(
                    "agent_complete",
                    {
                        "agent_id": agent["id"],
                        "execution_id": execution_id,
                        "success": True,
                    },
                )

            # Synthesize results
            final_result = {
                "execution_id": execution_id,
                "synthesized_response": "Combined analysis from all agents",
                "individual_results": results,
                "total_tokens": sum(r["tokens_used"] for r in results.values()),
                "execution_time": (
                    datetime.utcnow() - self.active_executions[execution_id]["started"]
                ).total_seconds(),
            }

            # Update execution status
            self.active_executions[execution_id]["status"] = "complete"
            self.active_executions[execution_id]["result"] = final_result

            # Broadcast execution complete
            await self.event_broadcaster.publish(
                "execution_complete",
                {
                    "execution_id": execution_id,
                    "request_id": request.id,
                    "success": True,
                    "execution_time": final_result["execution_time"],
                },
            )

            return final_result

        except Exception as e:
            self.active_executions[execution_id]["status"] = "failed"
            self.active_executions[execution_id]["error"] = str(e)
            raise

    def _estimate_cost(
        self, agents: list[dict[str, Any]], complexity: dict[str, Any]
    ) -> float:
        """Estimate the cost of execution."""
        # Simple cost estimation model
        base_cost_per_agent = 0.01  # $0.01 per agent
        complexity_multiplier = {"low": 1.0, "medium": 2.0, "high": 3.5}

        num_agents = len(agents)
        multiplier = complexity_multiplier[complexity["category"]]

        return num_agents * base_cost_per_agent * multiplier

    async def _store_execution(
        self,
        request: OrchestratorRequest,
        agents: list[dict[str, Any]],
        result: dict[str, Any],
    ):
        """Store execution for learning and analysis."""
        execution_data = {
            "request": {
                "id": request.id,
                "type": request.type.value,
                "content": request.content,
                "context": request.context,
            },
            "agents": agents,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Store in memory system
        await self.memory_router.store(
            key=f"execution:{request.id}",
            value=execution_data,
            domain="SHARED",
            tier="L2",  # Warm storage
        )

        # Add to patterns for learning
        self.execution_patterns.append(execution_data)

        # Keep only recent patterns (last 100)
        if len(self.execution_patterns) > 100:
            self.execution_patterns = self.execution_patterns[-100:]

    def _should_trigger_learning(self) -> bool:
        """Determine if learning should be triggered."""
        # Trigger learning every 10 executions
        return len(self.execution_patterns) % 10 == 0

    async def _trigger_learning(self):
        """Trigger learning process (placeholder for learning system)."""
        await self.event_broadcaster.publish(
            "learning_triggered",
            {
                "pattern_count": len(self.execution_patterns),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # In production, this would trigger actual learning
        logger.info("Learning process triggered")

    async def get_active_executions(self) -> list[dict[str, Any]]:
        """Get list of active executions."""
        return [
            {**exec_data, "execution_id": exec_id}
            for exec_id, exec_data in self.active_executions.items()
            if exec_data["status"] == "running"
        ]

    async def get_agent_performance(self, agent_id: str) -> dict[str, Any]:
        """Get performance metrics for a specific agent."""
        if agent_id not in self.agent_performance:
            return {"agent_id": agent_id, "metrics": [], "average_score": 0.0}

        scores = self.agent_performance[agent_id]
        return {
            "agent_id": agent_id,
            "metrics": scores,
            "average_score": sum(scores) / len(scores) if scores else 0.0,
            "total_executions": len(scores),
        }


# Global orchestrator instance
_orchestrator = None


def get_orchestrator() -> FactoryAwareOrchestrator:
    """Get or create the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = FactoryAwareOrchestrator()
    return _orchestrator
