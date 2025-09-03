"""
SuperOrchestrator - The ONE orchestrator to rule them all.
All other orchestrators will be deleted. This is the future.
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import WebSocket

from app.core.orchestrator_enhancements import (
    NaturalLanguageController,
    RealTimeMonitor,
    RegisteredSystem,
    SystemStatus,
    SystemType,
    UniversalRegistry,
)
from app.core.orchestrator_personality import orchestrator_personality, smart_suggestions
from app.embeddings.agno_embedding_service import AgnoEmbeddingService

# LLM will be injected or use portkey
from app.memory.unified_memory_store import UnifiedMemoryStore


class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class SystemState:
    """Real-time system state"""
    active_agents: int = 0
    memory_usage_mb: float = 0
    task_queue_size: int = 0
    avg_response_time_ms: float = 0
    health_score: float = 100.0
    last_optimization: datetime = None
    ai_insights: list[str] = None


class EmbeddedMemoryManager:
    """Memory management embedded in orchestrator"""

    def __init__(self):
        self.store = UnifiedMemoryStore(agent_id="super_orchestrator")
        self.cache = {}

    async def remember(self, key: str, value: Any, ttl: int = 3600):
        self.cache[key] = value
        await self.store.add_memory(key, value, ttl=ttl)

    async def recall(self, key: str) -> Any:
        if key in self.cache:
            return self.cache[key]
        return await self.store.get_memory(key)

    async def search(self, query: str, limit: int = 10):
        return await self.store.search_memories(query, limit=limit)


class EmbeddedStateManager:
    """State management embedded in orchestrator"""

    def __init__(self):
        self.state = SystemState()
        self.history = []

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        self.history.append({
            "timestamp": datetime.now(),
            "state": self.state.__dict__.copy()
        })

    def get_state(self) -> SystemState:
        return self.state

    def get_history(self, limit: int = 100):
        return self.history[-limit:]


class EmbeddedTaskManager:
    """Task management embedded in orchestrator"""

    def __init__(self):
        self.queue = asyncio.PriorityQueue()
        self.active_tasks = {}
        self.completed_tasks = []

    async def add_task(self, task: dict, priority: TaskPriority = TaskPriority.NORMAL):
        task_id = f"task_{datetime.now().timestamp()}"
        task["id"] = task_id
        task["created_at"] = datetime.now()
        await self.queue.put((priority.value, task))
        return task_id

    async def get_next_task(self) -> dict | None:
        try:
            priority, task = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            self.active_tasks[task["id"]] = task
            return task
        except asyncio.TimeoutError:
            return None

    def complete_task(self, task_id: str, result: Any = None):
        if task_id in self.active_tasks:
            task = self.active_tasks.pop(task_id)
            task["completed_at"] = datetime.now()
            task["result"] = result
            self.completed_tasks.append(task)
            return True
        return False


class AISystemMonitor:
    """AI-powered system monitoring"""

    def __init__(self, llm: Any | None = None):
        self.llm = llm
        self.metrics_history = []
        self.insights = []

    async def analyze_system(self, state: SystemState) -> dict:
        """AI analyzes system state and provides insights"""

        prompt = f"""
        Analyze this system state and provide insights:
        
        Active Agents: {state.active_agents}
        Memory Usage: {state.memory_usage_mb}MB
        Task Queue: {state.task_queue_size} tasks
        Avg Response Time: {state.avg_response_time_ms}ms
        Health Score: {state.health_score}
        
        Provide:
        1. Health assessment
        2. Performance bottlenecks
        3. Optimization suggestions
        4. Predictions for next hour
        
        Format as JSON.
        """

        response = await self.llm.ainvoke(prompt)
        insights = json.loads(response.content)

        self.insights.append({
            "timestamp": datetime.now(),
            "insights": insights
        })

        return insights

    async def auto_optimize(self, metrics: dict) -> list[str]:
        """AI suggests and applies optimizations"""

        optimizations = []

        # High memory usage
        if metrics.get("memory_usage_mb", 0) > 1000:
            optimizations.append("cache_cleanup")

        # Slow response times
        if metrics.get("avg_response_time_ms", 0) > 500:
            optimizations.append("enable_caching")
            optimizations.append("increase_workers")

        # Large task queue
        if metrics.get("task_queue_size", 0) > 100:
            optimizations.append("scale_workers")
            optimizations.append("prioritize_tasks")

        return optimizations


class SuperOrchestrator:
    """
    The ONE orchestrator to rule them all.
    Everything is embedded, AI-powered, and exceptional.
    """

    def __init__(self):
        # Embedded Managers (not separate files!)
        self.memory = EmbeddedMemoryManager()
        self.state = EmbeddedStateManager()
        self.tasks = EmbeddedTaskManager()

        # AI Brain (uses Portkey or injected LLM)
        self.llm = None  # Will be set via dependency injection
        self.ai_monitor = AISystemMonitor(None)  # Will use portkey directly
        self.embedding_service = AgnoEmbeddingService()

        # Personality System - Hell yeah, let's do this!
        self.personality = orchestrator_personality
        self.suggestions = smart_suggestions

        # UNIVERSAL CONTROL SYSTEM - This is the KEY!
        self.registry = UniversalRegistry()  # Tracks ALL AI systems
        self.nl_controller = NaturalLanguageController(self.registry)
        self.monitor = RealTimeMonitor(self.registry)

        # Micro-swarm registry (extends the integration plan)
        self.micro_swarms: dict[str, Any] = {}
        self.swarm_configs = {}

        # WebSocket connections for real-time UI
        self.connections: list[WebSocket] = []

        # Background tasks
        self.monitoring_task = None
        self.optimization_task = None

        # Auto-register self as the master orchestrator
        # Will be done in initialize()

    async def _register_self(self):
        """Register the orchestrator itself as a system"""
        master = RegisteredSystem(
            id="orchestrator_master",
            name="SuperOrchestrator",
            type=SystemType.SERVICE,
            status=SystemStatus.ACTIVE,
            capabilities=["orchestrate", "monitor", "optimize", "personality", "natural_language"],
            metadata={"role": "master", "personality": True}
        )
        await self.registry.register(master)

    async def initialize(self):
        """Initialize the orchestrator"""
        # Register self
        await self._register_self()
        
        # Start background monitoring
        self.monitoring_task = asyncio.create_task(self._monitor_loop())
        self.optimization_task = asyncio.create_task(self._optimization_loop())

        # Initialize state
        self.state.update(
            health_score=100.0,
            last_optimization=datetime.now()
        )

        return {"status": "initialized", "timestamp": datetime.now()}

    async def shutdown(self):
        """Graceful shutdown"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.optimization_task:
            self.optimization_task.cancel()

        # Close WebSocket connections
        for ws in self.connections:
            await ws.close()

    async def process_request(self, request: dict) -> dict:
        """
        Main entry point for ALL orchestration requests.
        This replaces all other orchestrators.
        """

        request_type = request.get("type")

        # Add to task queue
        task_id = await self.tasks.add_task(
            request,
            priority=self._determine_priority(request)
        )

        # Process based on type
        if request_type == "chat":
            response = await self._handle_chat(request)
        elif request_type == "command":
            response = await self._handle_command(request)
        elif request_type == "query":
            response = await self._handle_query(request)
        elif request_type == "agent":
            response = await self._handle_agent_request(request)
        else:
            response = await self._handle_generic(request)

        # Complete task
        self.tasks.complete_task(task_id, response)

        # Update metrics
        await self._update_metrics(request, response)

        return response

    async def _handle_chat(self, request: dict) -> dict:
        """Handle chat interactions with AI"""

        user_message = request.get("message")
        context = await self.memory.search(user_message, limit=5)

        # Check if this command needs pushback
        risk_analysis = self.personality.analyze_command_risk(user_message)
        if risk_analysis["should_pushback"]:
            pushback_response = self.personality.generate_response(
                "processing", command=user_message
            )
            return {
                "type": "chat_response",
                "message": pushback_response,
                "needs_confirmation": True,
                "timestamp": datetime.now()
            }

        # Get personality-infused greeting if appropriate
        if any(word in user_message.lower() for word in ["hi", "hello", "hey", "sup"]):
            greeting = self.personality.generate_response("greeting")
            return {
                "type": "chat_response",
                "message": greeting,
                "timestamp": datetime.now()
            }

        # Build prompt with context and personality
        prompt = f"""
        You are the SuperOrchestrator AI assistant with a specific personality:
        - Be enthusiastic and energetic
        - Use occasional mild profanity for emphasis (hell, damn, shit)
        - Be smart and insightful
        - Push back on risky or unclear requests
        
        Context from memory:
        {json.dumps(context, indent=2)}
        
        User: {user_message}
        
        Provide a helpful response with personality.
        """

        response = await self.llm.ainvoke(prompt)

        # Store in memory for future context
        await self.memory.remember(
            f"chat_{datetime.now().timestamp()}",
            {
                "user": user_message,
                "assistant": response.content
            }
        )

        return {
            "type": "chat_response",
            "message": response.content,
            "timestamp": datetime.now()
        }

    async def _handle_command(self, request: dict) -> dict:
        """Execute system commands"""

        command = request.get("command")
        params = request.get("params", {})
        
        # Track command for smart suggestions
        self.suggestions.track_command(command, success=True)

        # Command routing (replaces multiple orchestrators)
        commands = {
            "deploy": self._deploy_agent,
            "scale": self._scale_system,
            "optimize": self._optimize_system,
            "analyze": self._analyze_performance,
            "heal": self._self_heal
        }

        handler = commands.get(command, self._unknown_command)
        result = await handler(params)

        return {
            "type": "command_response",
            "command": command,
            "result": result,
            "timestamp": datetime.now()
        }

    async def _handle_query(self, request: dict) -> dict:
        """Handle data queries"""

        query_type = request.get("query_type")

        if query_type == "metrics":
            return await self._get_metrics()
        elif query_type == "state":
            return {"state": self.state.get_state().__dict__}
        elif query_type == "tasks":
            return {
                "active": list(self.tasks.active_tasks.values()),
                "completed": self.tasks.completed_tasks[-10:]
            }
        elif query_type == "insights":
            return {"insights": self.ai_monitor.insights[-5:]}
        else:
            return {"error": "Unknown query type"}

    async def _handle_agent_request(self, request: dict) -> dict:
        """Handle agent-related requests"""

        action = request.get("action")
        agent_config = request.get("config", {})

        # This replaces separate agent orchestrators
        if action == "create":
            return await self._create_agent(agent_config)
        elif action == "destroy":
            return await self._destroy_agent(agent_config.get("agent_id"))
        elif action == "status":
            return await self._get_agent_status(agent_config.get("agent_id"))
        else:
            return {"error": "Unknown agent action"}

    async def _handle_generic(self, request: dict) -> dict:
        """Use AI to handle unknown request types"""

        prompt = f"""
        Handle this orchestration request:
        {json.dumps(request, indent=2)}
        
        Determine the appropriate action and response.
        Format response as JSON.
        """

        response = await self.llm.ainvoke(prompt)
        return json.loads(response.content)

    def _determine_priority(self, request: dict) -> TaskPriority:
        """AI determines task priority"""

        # Critical keywords
        if any(word in str(request).lower() for word in ["critical", "urgent", "emergency"]):
            return TaskPriority.CRITICAL

        # High priority types
        if request.get("type") in ["deploy", "scale", "heal"]:
            return TaskPriority.HIGH

        # Default
        return TaskPriority.NORMAL

    async def _monitor_loop(self):
        """Continuous monitoring loop"""

        while True:
            try:
                # Collect metrics
                metrics = await self._collect_metrics()

                # AI analysis
                insights = await self.ai_monitor.analyze_system(self.state.get_state())

                # Update state
                self.state.update(
                    ai_insights=insights.get("insights", []),
                    health_score=insights.get("health_score", 100)
                )

                # Broadcast to UI
                await self._broadcast_update({
                    "type": "monitoring_update",
                    "metrics": metrics,
                    "insights": insights,
                    "state": self.state.get_state().__dict__
                })

                await asyncio.sleep(30)  # Monitor every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                # Self-healing
                await self._self_heal({"error": str(e)})

    async def _optimization_loop(self):
        """Continuous optimization loop"""

        while True:
            try:
                # Get current metrics
                metrics = await self._collect_metrics()

                # AI optimization suggestions
                optimizations = await self.ai_monitor.auto_optimize(metrics)

                # Apply optimizations
                for optimization in optimizations:
                    await self._apply_optimization(optimization)

                # Update state
                self.state.update(last_optimization=datetime.now())

                await asyncio.sleep(300)  # Optimize every 5 minutes

            except asyncio.CancelledError:
                break
            except Exception:
                pass  # Silent fail for optimization

    async def _collect_metrics(self) -> dict:
        """Collect system metrics"""

        import psutil

        metrics = {
            "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024,
            "cpu_percent": psutil.cpu_percent(interval=1),
            "active_agents": self.state.get_state().active_agents,
            "task_queue_size": self.tasks.queue.qsize(),
            "active_tasks": len(self.tasks.active_tasks),
            "completed_tasks": len(self.tasks.completed_tasks),
            "health_score": self.state.get_state().health_score,
            "active_systems": len(self.registry.get_active_systems()),
            "error_count": sum(1 for s in self.registry.systems.values() if s.status == SystemStatus.ERROR),
            "cost_today": self._calculate_cost(),
            "idle_systems": sum(1 for s in self.registry.systems.values() if s.status == SystemStatus.IDLE)
        }
        
        return metrics

    async def _update_metrics(self, request: dict, response: dict):
        """Update performance metrics"""

        # Calculate response time (simplified)
        response_time = 100  # Placeholder

        current_avg = self.state.get_state().avg_response_time_ms
        new_avg = (current_avg * 0.9) + (response_time * 0.1)  # Weighted average

        self.state.update(avg_response_time_ms=new_avg)

    async def _broadcast_update(self, update: dict):
        """Broadcast updates to all connected UIs"""

        for ws in self.connections[:]:
            try:
                await ws.send_json(update)
            except:
                self.connections.remove(ws)

    # Command Handlers

    async def _deploy_agent(self, params: dict) -> dict:
        """Deploy a new agent"""
        agent_id = f"agent_{datetime.now().timestamp()}"
        self.state.update(active_agents=self.state.get_state().active_agents + 1)
        return {"agent_id": agent_id, "status": "deployed"}

    async def _scale_system(self, params: dict) -> dict:
        """Scale the system"""
        scale_factor = params.get("factor", 2)
        return {"status": "scaled", "factor": scale_factor}

    async def _optimize_system(self, params: dict) -> dict:
        """Optimize the system"""
        optimizations = await self.ai_monitor.auto_optimize(await self._collect_metrics())
        for opt in optimizations:
            await self._apply_optimization(opt)
        return {"optimizations_applied": optimizations}

    async def _analyze_performance(self, params: dict) -> dict:
        """Analyze system performance with personality"""
        metrics = await self._collect_metrics()
        insights = await self.ai_monitor.analyze_system(self.state.get_state())
        
        # Get personality-infused analysis
        personality_response = self.personality.generate_response(
            "analysis", 
            data={
                "health_score": metrics.get("health_score", 0),
                "active_systems": metrics.get("active_systems", 0),
                "cost": metrics.get("cost_today", 0),
                "recommendations": insights.get("optimization_suggestions", [])
            }
        )
        
        return {
            "metrics": metrics, 
            "insights": insights,
            "personality_analysis": personality_response
        }

    async def _self_heal(self, params: dict) -> dict:
        """Self-healing functionality with personality"""
        issue = params.get("error", "Unknown issue")
        
        # Get personality response for error
        error_response = self.personality.generate_response(
            "error",
            data={"error": issue}
        )

        # AI determines healing action
        prompt = f"Determine healing action for: {issue}"
        response = await self.llm.ainvoke(prompt)

        return {
            "healing_action": response.content,
            "personality_message": error_response
        }

    async def _apply_optimization(self, optimization: str):
        """Apply a specific optimization"""

        optimizations = {
            "cache_cleanup": self._cleanup_cache,
            "enable_caching": self._enable_caching,
            "increase_workers": self._increase_workers,
            "scale_workers": self._scale_workers,
            "prioritize_tasks": self._prioritize_tasks
        }

        handler = optimizations.get(optimization)
        if handler:
            await handler()

    async def _cleanup_cache(self):
        """Clean up memory cache"""
        self.memory.cache.clear()

    async def _enable_caching(self):
        """Enable aggressive caching"""
        pass  # Implement caching logic

    async def _increase_workers(self):
        """Increase worker count"""
        pass  # Implement worker scaling

    async def _scale_workers(self):
        """Scale workers based on load"""
        pass  # Implement dynamic scaling

    async def _prioritize_tasks(self):
        """Re-prioritize task queue"""
        pass  # Implement task prioritization

    async def _create_agent(self, config: dict) -> dict:
        """Create a new agent"""
        agent_id = f"agent_{datetime.now().timestamp()}"
        # Agent creation logic here
        return {"agent_id": agent_id, "status": "created"}

    async def _destroy_agent(self, agent_id: str) -> dict:
        """Destroy an agent"""
        # Agent destruction logic here
        self.state.update(active_agents=max(0, self.state.get_state().active_agents - 1))
        return {"agent_id": agent_id, "status": "destroyed"}

    async def _get_agent_status(self, agent_id: str) -> dict:
        """Get agent status"""
        # Agent status logic here
        return {"agent_id": agent_id, "status": "active"}

    async def _unknown_command(self, params: dict) -> dict:
        """Handle unknown commands with AI"""
        return {"error": "Unknown command", "params": params}

    async def _get_metrics(self) -> dict:
        """Get current metrics"""
        return await self._collect_metrics()
    
    def _calculate_cost(self) -> float:
        """Calculate current operational cost"""
        # Basic cost calculation based on active systems
        active_systems = len(self.registry.get_active_systems())
        # Rough estimate: $0.001 per active system per hour
        base_cost = active_systems * 0.001
        
        # Add cost for different system types
        swarm_cost = len(self.registry.get_by_type(SystemType.SWARM)) * 0.005
        mcp_cost = len(self.registry.get_by_type(SystemType.MCP_SERVER)) * 0.002
        
        return base_cost + swarm_cost + mcp_cost
    
    async def process_natural_language(self, command: str) -> dict:
        """Process natural language commands with personality"""
        # Get contextual suggestions
        current_context = {
            "error_count": sum(1 for s in self.registry.systems.values() if s.status == SystemStatus.ERROR),
            "cost_today": self._calculate_cost(),
            "idle_systems": sum(1 for s in self.registry.systems.values() if s.status == SystemStatus.IDLE)
        }
        suggestions = self.suggestions.get_contextual_suggestions(current_context)
        
        # Process the command
        result = await self.nl_controller.process_command(command)
        
        # Track for learning
        self.suggestions.track_command(command, result.get("success", True))
        
        # Add personality and suggestions to response
        result["suggestions"] = suggestions
        result["personality_active"] = True
        
        return result

    # WebSocket Support

    async def connect_websocket(self, websocket: WebSocket):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.connections.append(websocket)

        # Send initial state
        await websocket.send_json({
            "type": "initial_state",
            "state": self.state.get_state().__dict__,
            "metrics": await self._collect_metrics()
        })

    async def disconnect_websocket(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        if websocket in self.connections:
            self.connections.remove(websocket)


# Singleton instance
_orchestrator = None

def get_orchestrator() -> SuperOrchestrator:
    """Get the singleton orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SuperOrchestrator()
    return _orchestrator
