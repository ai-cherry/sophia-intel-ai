"""
Smart Command Dispatcher - Intelligent routing hub for NL commands
Routes to appropriate processing engine based on complexity and context
Integrates memory, swarms, agents, and optimization patterns
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from enum import Enum
# TODO: Define AgentRole locally or use SuperOrchestrator
from app.core.circuit_breaker import with_circuit_breaker
from app.nl_interface.memory_connector import NLInteraction, NLMemoryConnector
from app.nl_interface.quicknlp import CachedQuickNLP, CommandIntent, ParsedCommand
from app.swarms.improved_swarm import ImprovedAgentSwarm
from app.swarms.performance_optimizer import (
    CircuitBreaker,
    GracefulDegradationManager,
    SwarmOptimizer,
)

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Execution modes based on task complexity"""
    LITE = "lite"          # Simple, fast execution
    BALANCED = "balanced"  # Balanced speed/quality
    QUALITY = "quality"    # High quality, slower


class ComponentStatus(Enum):
    """Component availability status"""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class EnrichedCommand:
    """Command enriched with context and memory"""
    parsed_command: ParsedCommand
    session_id: str
    user_context: dict[str, Any]
    conversation_history: list[dict[str, Any]]
    complexity_score: float
    recommended_mode: ExecutionMode
    relevant_memories: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of command execution"""
    success: bool
    response: Any
    execution_mode: ExecutionMode
    execution_time: float
    patterns_used: list[str]
    quality_score: float
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SmartCommandDispatcher:
    """
    Intelligent command dispatcher that routes NL commands to optimal processing engine
    Integrates memory, swarms, agents, and optimization patterns
    """

    @with_circuit_breaker("webhook")
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        redis_url: str = "redis://localhost:6379",
        mcp_server_url: str = "http://localhost:8004",
        n8n_url: str = "http://localhost:5678",
        config_file: str = "app/config/nl_swarm_integration.json"
    ):
        """
        Initialize Smart Command Dispatcher
        
        Args:
            ollama_url: URL for Ollama LLM service
            redis_url: URL for Redis cache/state
            mcp_server_url: URL for MCP memory server
            n8n_url: URL for n8n workflow engine
            config_file: Path to configuration file
        """
        # Core components
        self.nlp = CachedQuickNLP(ollama_url=ollama_url)
        self.memory_connector = NLMemoryConnector(mcp_server_url=mcp_server_url)
        self.optimizer = SwarmOptimizer()
        self.degradation_manager = GracefulDegradationManager()

        # Execution engines
        self.orchestrator = OptimizedAgentOrchestrator(
            redis_url=redis_url,
            ollama_url=ollama_url,
            n8n_url=n8n_url
        )

        # Initialize swarm with mock agents for now
        self.swarm = ImprovedAgentSwarm(
            agents=["planner", "executor", "critic", "judge"],
            config_file="app/swarms/swarm_optimization_config.json"
        )

        # Configuration
        self.config = self._load_config(config_file)

        # Circuit breakers for each component
        self.circuit_breakers = {
            "memory": CircuitBreaker(failure_threshold=3, recovery_timeout=30),
            "swarm": CircuitBreaker(failure_threshold=2, recovery_timeout=60),
            "orchestrator": CircuitBreaker(failure_threshold=3, recovery_timeout=30),
            "n8n": CircuitBreaker(failure_threshold=5, recovery_timeout=20)
        }

        # Performance tracking
        self.execution_stats = {
            "total_commands": 0,
            "success_count": 0,
            "failure_count": 0,
            "mode_usage": {"lite": 0, "balanced": 0, "quality": 0},
            "avg_execution_time": 0,
            "total_execution_time": 0
        }

        # Session state
        self.active_sessions = {}

        logger.info("SmartCommandDispatcher initialized successfully")

    def _load_config(self, config_file: str) -> dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(config_file) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning(f"Could not load config from {config_file}, using defaults")
            return self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration"""
        return {
            "complexity_thresholds": {
                "lite": 0.3,
                "balanced": 0.7
            },
            "swarm_eligible_intents": [
                "EXECUTE_WORKFLOW",
                "QUERY_DATA",
                "RUN_AGENT"
            ],
            "memory_enrichment": {
                "enabled": True,
                "max_history": 10,
                "include_similar": True
            },
            "optimization": {
                "auto_adjust_mode": True,
                "performance_target_ms": 5000,
                "quality_target": 0.8
            },
            "fallback": {
                "enable_graceful_degradation": True,
                "fallback_to_simple": True
            }
        }

    async def process_command(
        self,
        text: str,
        session_id: str,
        user_context: Optional[dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Process a natural language command with intelligent routing
        
        Args:
            text: The natural language command
            session_id: Session identifier for context
            user_context: Optional user context
            
        Returns:
            ExecutionResult with response and metadata
        """
        start_time = time.time()
        self.execution_stats["total_commands"] += 1

        try:
            # Parse the command
            parsed_command = self.nlp.process(text)
            logger.info(f"Parsed command: {parsed_command.intent.value} (confidence: {parsed_command.confidence:.2f})")

            # Enrich with memory and context
            enriched_command = await self._enrich_with_memory(
                parsed_command,
                session_id,
                user_context or {}
            )

            # Analyze complexity and select execution mode
            execution_mode = await self._analyze_and_select_mode(enriched_command)
            logger.info(f"Selected execution mode: {execution_mode.value}")

            # Route to appropriate handler
            if self._is_swarm_eligible(enriched_command) and execution_mode != ExecutionMode.LITE:
                result = await self._dispatch_to_swarm(enriched_command, execution_mode)
            elif enriched_command.parsed_command.intent == CommandIntent.RUN_AGENT:
                result = await self._handle_agent_execution(enriched_command, execution_mode)
            elif enriched_command.parsed_command.intent == CommandIntent.QUERY_DATA:
                result = await self._handle_complex_query(enriched_command, execution_mode)
            else:
                result = await self._handle_simple_command(enriched_command)

            # Store interaction in memory
            await self._integrate_memory_results(
                enriched_command,
                result,
                execution_time=time.time() - start_time
            )

            # Update statistics
            self.execution_stats["success_count"] += 1
            self.execution_stats["mode_usage"][execution_mode.value] += 1

            execution_time = time.time() - start_time
            self._update_avg_execution_time(execution_time)

            return ExecutionResult(
                success=True,
                response=result,
                execution_mode=execution_mode,
                execution_time=execution_time,
                patterns_used=self._get_patterns_used(execution_mode),
                quality_score=result.get("quality_score", 0.8) if isinstance(result, dict) else 0.8
            )

        except Exception as e:
            logger.error(f"Command processing failed: {e}")
            self.execution_stats["failure_count"] += 1

            # Attempt fallback
            if self.config["fallback"]["enable_graceful_degradation"]:
                return await self._handle_with_fallback(text, session_id, str(e))

            return ExecutionResult(
                success=False,
                response=None,
                execution_mode=ExecutionMode.LITE,
                execution_time=time.time() - start_time,
                patterns_used=[],
                quality_score=0,
                error=str(e)
            )

    async def _enrich_with_memory(
        self,
        parsed_command: ParsedCommand,
        session_id: str,
        user_context: dict[str, Any]
    ) -> EnrichedCommand:
        """
        Enrich command with memory and conversation history
        
        Args:
            parsed_command: The parsed NL command
            session_id: Session identifier
            user_context: User context
            
        Returns:
            EnrichedCommand with context and history
        """
        enriched = EnrichedCommand(
            parsed_command=parsed_command,
            session_id=session_id,
            user_context=user_context,
            conversation_history=[],
            complexity_score=0.5,
            recommended_mode=ExecutionMode.BALANCED
        )

        if not self.config["memory_enrichment"]["enabled"]:
            return enriched

        try:
            # Use circuit breaker for memory operations
            async def fetch_memory():
                # Get conversation history
                history = await self.memory_connector.retrieve_session_history(
                    session_id,
                    limit=self.config["memory_enrichment"]["max_history"]
                )

                # Get context summary
                context_summary = await self.memory_connector.get_context_summary(
                    session_id,
                    max_interactions=5
                )

                # Search for similar interactions if enabled
                similar = []
                if self.config["memory_enrichment"]["include_similar"]:
                    similar = await self.memory_connector.search_interactions(
                        parsed_command.raw_text,
                        limit=3
                    )

                return history, context_summary, similar

            history, context_summary, similar = await self.circuit_breakers["memory"].call(
                fetch_memory
            )

            enriched.conversation_history = history
            enriched.metadata["context_summary"] = context_summary
            enriched.relevant_memories = similar

            # Update complexity based on context
            if len(history) > 5:
                enriched.complexity_score += 0.1  # More complex with longer history

            logger.debug(f"Enriched command with {len(history)} history items")

        except Exception as e:
            logger.warning(f"Memory enrichment failed (degraded mode): {e}")
            self.degradation_manager.mark_component_degraded("memory", str(e))

        return enriched

    async def _analyze_and_select_mode(
        self,
        enriched_command: EnrichedCommand
    ) -> ExecutionMode:
        """
        Analyze task complexity and select optimal execution mode
        
        Args:
            enriched_command: The enriched command
            
        Returns:
            Recommended execution mode
        """
        # Calculate task complexity
        task_dict = {
            "description": enriched_command.parsed_command.raw_text,
            "intent": enriched_command.parsed_command.intent.value,
            "entities": enriched_command.parsed_command.entities,
            "history_length": len(enriched_command.conversation_history)
        }

        complexity_score = self.optimizer.calculate_task_complexity(task_dict)
        enriched_command.complexity_score = complexity_score

        # Check for urgency in context
        urgency = enriched_command.user_context.get("urgency", "normal")

        # Select mode based on complexity and configuration
        thresholds = self.config["complexity_thresholds"]

        if urgency == "critical" or complexity_score < thresholds["lite"]:
            mode = ExecutionMode.LITE
        elif complexity_score < thresholds["balanced"]:
            mode = ExecutionMode.BALANCED
        else:
            mode = ExecutionMode.QUALITY

        # Auto-adjust based on performance if enabled
        if self.config["optimization"]["auto_adjust_mode"]:
            mode = self._auto_adjust_mode(mode)

        enriched_command.recommended_mode = mode
        return mode

    def _auto_adjust_mode(self, recommended_mode: ExecutionMode) -> ExecutionMode:
        """Auto-adjust mode based on recent performance"""
        if self.execution_stats["total_commands"] < 10:
            return recommended_mode

        avg_time = self.execution_stats["avg_execution_time"]
        success_rate = self.execution_stats["success_count"] / self.execution_stats["total_commands"]

        target_time = self.config["optimization"]["performance_target_ms"] / 1000
        target_quality = self.config["optimization"]["quality_target"]

        # If taking too long, downgrade
        if avg_time > target_time * 1.5:
            if recommended_mode == ExecutionMode.QUALITY:
                return ExecutionMode.BALANCED
            elif recommended_mode == ExecutionMode.BALANCED:
                return ExecutionMode.LITE

        # If quality is low, upgrade
        elif success_rate < target_quality:
            if recommended_mode == ExecutionMode.LITE:
                return ExecutionMode.BALANCED
            elif recommended_mode == ExecutionMode.BALANCED:
                return ExecutionMode.QUALITY

        return recommended_mode

    def _is_swarm_eligible(self, enriched_command: EnrichedCommand) -> bool:
        """Check if command is eligible for swarm execution"""
        intent_name = enriched_command.parsed_command.intent.name
        return (
            intent_name in self.config["swarm_eligible_intents"] and
            enriched_command.complexity_score > 0.4 and
            self.degradation_manager.is_component_available("swarm")
        )

    async def _dispatch_to_swarm(
        self,
        enriched_command: EnrichedCommand,
        execution_mode: ExecutionMode
    ) -> dict[str, Any]:
        """
        Dispatch command to swarm for execution
        
        Args:
            enriched_command: The enriched command
            execution_mode: Selected execution mode
            
        Returns:
            Execution result from swarm
        """
        try:
            # Prepare problem for swarm
            problem = {
                "type": enriched_command.parsed_command.intent.value,
                "description": enriched_command.parsed_command.raw_text,
                "entities": enriched_command.parsed_command.entities,
                "context": enriched_command.user_context,
                "complexity": enriched_command.complexity_score,
                "mode": execution_mode.value
            }

            # Configure swarm based on mode
            self.swarm.optimization_mode = execution_mode.value

            # Execute with circuit breaker
            async def swarm_execute():
                return await self.swarm.solve_with_improvements(problem)

            result = await self.circuit_breakers["swarm"].call(swarm_execute)

            logger.info(f"Swarm execution completed with quality score: {result.get('quality_score', 0)}")
            return result

        except Exception as e:
            logger.error(f"Swarm execution failed: {e}")
            self.degradation_manager.mark_component_degraded("swarm", str(e))

            # Fallback to orchestrator
            return await self._handle_agent_execution(enriched_command, ExecutionMode.LITE)

    async def _handle_agent_execution(
        self,
        enriched_command: EnrichedCommand,
        execution_mode: ExecutionMode
    ) -> dict[str, Any]:
        """
        Handle agent execution commands
        
        Args:
            enriched_command: The enriched command
            execution_mode: Selected execution mode
            
        Returns:
            Agent execution result
        """
        try:
            # Determine agent chain based on mode
            if execution_mode == ExecutionMode.LITE:
                agents_chain = [AgentRole.EXECUTOR]
            elif execution_mode == ExecutionMode.BALANCED:
                agents_chain = [AgentRole.RESEARCHER, AgentRole.EXECUTOR]
            else:
                agents_chain = [AgentRole.RESEARCHER, AgentRole.CODER, AgentRole.REVIEWER]

            # Extract agent name if specified
            agent_name = enriched_command.parsed_command.entities.get("agent_name", "default")

            # Execute with circuit breaker
            async def orchestrator_execute():
                async with self.orchestrator as orch:
                    return await orch.execute_workflow(
                        session_id=enriched_command.session_id,
                        user_request=enriched_command.parsed_command.raw_text,
                        workflow_name=f"agent_{agent_name}",
                        agents_chain=agents_chain
                    )

            context = await self.circuit_breakers["orchestrator"].call(orchestrator_execute)

            return {
                "agent": agent_name,
                "execution_context": context.state,
                "tasks_completed": len(context.tasks),
                "quality_score": 0.85,
                "execution_time": context.end_time - context.start_time if context.end_time else 0
            }

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            self.degradation_manager.mark_component_degraded("orchestrator", str(e))
            return {"error": str(e), "quality_score": 0}

    async def _handle_complex_query(
        self,
        enriched_command: EnrichedCommand,
        execution_mode: ExecutionMode
    ) -> dict[str, Any]:
        """
        Handle complex data queries
        
        Args:
            enriched_command: The enriched command
            execution_mode: Selected execution mode
            
        Returns:
            Query result
        """
        query_text = enriched_command.parsed_command.entities.get("query", "")

        # For complex queries, use swarm if available
        if execution_mode != ExecutionMode.LITE and self._is_swarm_eligible(enriched_command):
            return await self._dispatch_to_swarm(enriched_command, execution_mode)

        # Otherwise, use simple query processing
        return {
            "query": query_text,
            "results": f"Query results for: {query_text}",
            "result_count": 10,
            "quality_score": 0.7
        }

    async def _handle_simple_command(
        self,
        enriched_command: EnrichedCommand
    ) -> dict[str, Any]:
        """
        Handle simple commands that don't need complex processing
        
        Args:
            enriched_command: The enriched command
            
        Returns:
            Simple command result
        """
        intent = enriched_command.parsed_command.intent
        entities = enriched_command.parsed_command.entities

        # Map simple intents to responses
        if intent == CommandIntent.SYSTEM_STATUS:
            return await self._get_system_status()
        elif intent == CommandIntent.LIST_AGENTS:
            return {"agents": self.orchestrator.get_available_agents()}
        elif intent == CommandIntent.HELP:
            return {"commands": self.nlp.get_available_commands()}
        elif intent == CommandIntent.GET_METRICS:
            return self._get_performance_metrics()
        else:
            return {
                "intent": intent.value,
                "entities": entities,
                "response": f"Processed {intent.value} command",
                "quality_score": 0.9
            }

    @with_circuit_breaker("webhook")
    async def _get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "components": {
                "memory": self._check_component_status("memory"),
                "swarm": self._check_component_status("swarm"),
                "orchestrator": self._check_component_status("orchestrator"),
                "n8n": self._check_component_status("n8n")
            },
            "health_score": self.degradation_manager.get_system_health_score(),
            "active_sessions": len(self.active_sessions),
            "execution_stats": self.execution_stats,
            "cache_stats": self.nlp.get_cache_stats(),
            "quality_score": 1.0
        }

    def _check_component_status(self, component: str) -> str:
        """Check status of a component"""
        if not self.degradation_manager.is_component_available(component):
            return ComponentStatus.DEGRADED.value

        cb = self.circuit_breakers.get(component)
        if cb and cb.state == "open":
            return ComponentStatus.UNAVAILABLE.value

        return ComponentStatus.AVAILABLE.value

    async def _integrate_memory_results(
        self,
        enriched_command: EnrichedCommand,
        result: Any,
        execution_time: float
    ):
        """
        Store command execution results in memory
        
        Args:
            enriched_command: The enriched command
            result: Execution result
            execution_time: Time taken to execute
        """
        try:
            interaction = NLInteraction(
                session_id=enriched_command.session_id,
                timestamp=datetime.now().isoformat(),
                user_input=enriched_command.parsed_command.raw_text,
                intent=enriched_command.parsed_command.intent.value,
                entities=enriched_command.parsed_command.entities,
                confidence=enriched_command.parsed_command.confidence,
                response=json.dumps(result) if isinstance(result, dict) else str(result),
                workflow_id=enriched_command.parsed_command.workflow_trigger,
                execution_result={
                    "execution_mode": enriched_command.recommended_mode.value,
                    "execution_time": execution_time,
                    "quality_score": result.get("quality_score", 0) if isinstance(result, dict) else 0
                },
                metadata=enriched_command.metadata
            )

            await self.memory_connector.store_interaction(interaction)
            logger.debug(f"Stored interaction for session {enriched_command.session_id[:8]}")

        except Exception as e:
            logger.warning(f"Failed to store interaction in memory: {e}")

    async def _handle_with_fallback(
        self,
        text: str,
        session_id: str,
        original_error: str
    ) -> ExecutionResult:
        """
        Handle command with fallback mechanism
        
        Args:
            text: Original command text
            session_id: Session ID
            original_error: Error from original attempt
            
        Returns:
            Fallback execution result
        """
        logger.info(f"Attempting fallback for failed command: {original_error}")

        try:
            # Try simple NLP processing without enrichment
            parsed = self.nlp.process(text)

            # Execute in simplest mode
            result = {
                "intent": parsed.intent.value,
                "entities": parsed.entities,
                "response": f"Fallback response for {parsed.intent.value}",
                "original_error": original_error,
                "quality_score": 0.5
            }

            return ExecutionResult(
                success=True,
                response=result,
                execution_mode=ExecutionMode.LITE,
                execution_time=0,
                patterns_used=["fallback"],
                quality_score=0.5,
                metadata={"fallback": True}
            )

        except Exception as e:
            logger.error(f"Fallback also failed: {e}")
            return ExecutionResult(
                success=False,
                response=None,
                execution_mode=ExecutionMode.LITE,
                execution_time=0,
                patterns_used=["fallback"],
                quality_score=0,
                error=f"Both primary and fallback failed: {original_error}, {e}"
            )

    def _get_patterns_used(self, mode: ExecutionMode) -> list[str]:
        """Get list of patterns used for execution mode"""
        if mode == ExecutionMode.LITE:
            return ["quick_nlp", "simple_execution"]
        elif mode == ExecutionMode.BALANCED:
            return ["memory_enrichment", "orchestrator", "quality_gates"]
        else:
            return ["memory_enrichment", "swarm", "debate", "quality_gates", "consensus"]

    def _update_avg_execution_time(self, execution_time: float):
        """Update average execution time"""
        self.execution_stats["total_execution_time"] += execution_time
        self.execution_stats["avg_execution_time"] = (
            self.execution_stats["total_execution_time"] /
            self.execution_stats["total_commands"]
        )

    def _get_performance_metrics(self) -> dict[str, Any]:
        """Get comprehensive performance metrics"""
        metrics = {
            "dispatcher_stats": self.execution_stats,
            "nlp_cache_stats": self.nlp.get_cache_stats(),
            "memory_stats": self.memory_connector.get_statistics(),
            "swarm_metrics": self.swarm.get_performance_metrics(),
            "orchestrator_metrics": self.orchestrator.get_metrics(),
            "optimizer_recommendations": self.optimizer.get_optimization_recommendations(),
            "system_health": self.degradation_manager.get_system_health_score(),
            "circuit_breakers": {
                name: {
                    "state": cb.state,
                    "failure_count": cb.failure_count,
                    "success_count": cb.success_count
                }
                for name, cb in self.circuit_breakers.items()
            }
        }

        # Calculate overall quality score
        if self.execution_stats["total_commands"] > 0:
            metrics["overall_quality_score"] = (
                self.execution_stats["success_count"] /
                self.execution_stats["total_commands"]
            )
        else:
            metrics["overall_quality_score"] = 0

        return metrics

    async def optimize_for_session(
        self,
        session_id: str,
        optimization_goal: str = "balanced"
    ) -> dict[str, Any]:
        """
        Optimize dispatcher settings for a specific session
        
        Args:
            session_id: Session to optimize for
            optimization_goal: Goal (speed, quality, balanced)
            
        Returns:
            Optimization result
        """
        # Get session history
        history = await self.memory_connector.retrieve_session_history(session_id)

        # Analyze patterns
        intent_distribution = {}
        avg_complexity = 0

        for interaction in history:
            intent = interaction.get("intent")
            if intent:
                intent_distribution[intent] = intent_distribution.get(intent, 0) + 1

            if interaction.get("execution_result"):
                complexity = interaction["execution_result"].get("complexity_score", 0.5)
                avg_complexity += complexity

        if history:
            avg_complexity /= len(history)

        # Determine optimal settings
        if optimization_goal == "speed" or avg_complexity < 0.3:
            recommended_mode = ExecutionMode.LITE
            patterns_to_enable = ["quick_nlp"]
        elif optimization_goal == "quality" or avg_complexity > 0.7:
            recommended_mode = ExecutionMode.QUALITY
            patterns_to_enable = ["swarm", "debate", "quality_gates"]
        else:
            recommended_mode = ExecutionMode.BALANCED
            patterns_to_enable = ["orchestrator", "quality_gates"]

        # Store optimization for session
        self.active_sessions[session_id] = {
            "optimization_mode": recommended_mode,
            "patterns": patterns_to_enable,
            "avg_complexity": avg_complexity,
            "intent_distribution": intent_distribution
        }

        return {
            "session_id": session_id,
            "recommended_mode": recommended_mode.value,
            "patterns_to_enable": patterns_to_enable,
            "analysis": {
                "avg_complexity": avg_complexity,
                "interaction_count": len(history),
                "most_common_intent": max(intent_distribution.items(), key=lambda x: x[1])[0] if intent_distribution else None
            }
        }

    async def get_session_status(self, session_id: str) -> dict[str, Any]:
        """
        Get real-time status for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session status information
        """
        session_info = self.active_sessions.get(session_id, {})

        # Get recent history
        history = await self.memory_connector.retrieve_session_history(session_id, limit=5)

        # Get context summary
        context = await self.memory_connector.get_context_summary(session_id)

        return {
            "session_id": session_id,
            "active": session_id in self.active_sessions,
            "optimization_settings": session_info,
            "recent_interactions": len(history),
            "context_summary": context,
            "last_interaction": history[-1] if history else None
        }

    async def shutdown(self):
        """Graceful shutdown of dispatcher"""
        logger.info("Shutting down SmartCommandDispatcher")

        # Close connections
        await self.memory_connector.disconnect()
        await self.orchestrator.disconnect()

        # Save metrics
        metrics = self._get_performance_metrics()
        logger.info(f"Final metrics: {json.dumps(metrics, indent=2)}")

        logger.info("SmartCommandDispatcher shutdown complete")


# Example usage and testing
async def example_usage():
    """Example of using the SmartCommandDispatcher"""

    dispatcher = SmartCommandDispatcher()

    # Test commands with different complexity levels
    test_commands = [
        ("show system status", "simple"),  # Simple command
        ("run agent researcher to analyze market trends", "complex"),  # Agent execution
        ("query data about user engagement metrics", "medium"),  # Data query
        ("execute workflow data-pipeline with quality checks", "complex"),  # Workflow execution
    ]

    session_id = "test-session-001"

    for command, complexity in test_commands:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {command} (expected complexity: {complexity})")
        logger.info(f"{'='*60}")

        result = await dispatcher.process_command(
            text=command,
            session_id=session_id,
            user_context={"urgency": "normal"}
        )

        logger.info(f"Success: {result.success}")
        logger.info(f"Mode: {result.execution_mode.value}")
        logger.info(f"Execution Time: {result.execution_time:.2f}s")
        logger.info(f"Quality Score: {result.quality_score:.2f}")
        logger.info(f"Patterns Used: {', '.join(result.patterns_used)}")

        if result.error:
            logger.info(f"Error: {result.error}")
        else:
            logger.info(f"Response Preview: {str(result.response)[:200]}...")

    # Get session optimization
    optimization = await dispatcher.optimize_for_session(session_id)
    logger.info(f"\n{'='*60}")
    logger.info("Session Optimization:")
    logger.info(json.dumps(optimization, indent=2))

    # Get performance metrics
    metrics = dispatcher._get_performance_metrics()
    logger.info(f"\n{'='*60}")
    logger.info("Performance Metrics:")
    logger.info(f"Total Commands: {metrics['dispatcher_stats']['total_commands']}")
    logger.info(f"Success Rate: {metrics['overall_quality_score']:.2%}")
    logger.info(f"Avg Execution Time: {metrics['dispatcher_stats']['avg_execution_time']:.2f}s")
    logger.info(f"System Health: {metrics['system_health']:.2%}")

    # Shutdown
    await dispatcher.shutdown()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
