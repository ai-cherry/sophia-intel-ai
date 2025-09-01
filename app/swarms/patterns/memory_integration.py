"""
Memory Integration Pattern for Swarm Systems
Implements ADR-005 memory integration as a composable swarm pattern.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import logging

from .base import SwarmPattern, PatternConfig, PatternResult
from ..memory_integration import SwarmMemoryClient, SwarmMemoryEventType
from app.memory.supermemory_mcp import MemoryType
from app.core.circuit_breaker import with_circuit_breaker, get_llm_circuit_breaker, get_weaviate_circuit_breaker, get_redis_circuit_breaker, get_webhook_circuit_breaker

logger = logging.getLogger(__name__)


@dataclass
class MemoryIntegrationConfig(PatternConfig):
    """Configuration for memory integration pattern."""
    
    # Memory storage settings
    auto_store_patterns: bool = True
    auto_store_learnings: bool = True
    auto_store_metrics: bool = True
    
    # Context loading settings
    load_context_on_init: bool = True
    max_context_patterns: int = 5
    max_context_learnings: int = 10
    max_context_history: int = 20
    
    # Inter-swarm communication settings
    enable_inter_swarm_comm: bool = True
    message_priority_default: str = "normal"
    
    # Memory persistence thresholds
    min_quality_for_pattern_storage: float = 0.8
    min_confidence_for_learning: float = 0.7
    
    # Performance settings
    memory_operation_timeout: float = 5.0
    batch_memory_operations: bool = True
    max_batch_size: int = 10


class MemoryIntegrationPattern(SwarmPattern):
    """
    Memory integration pattern that provides persistent memory capabilities
    to swarm orchestrators following ADR-005 architecture.
    """
    
    def __init__(self, config: Optional[MemoryIntegrationConfig] = None):
        super().__init__(config or MemoryIntegrationConfig())
        self.memory_client: Optional[SwarmMemoryClient] = None
        self.swarm_context: Dict[str, Any] = {}
        self.memory_operations_log: List[Dict] = []
        
    async def initialize(self) -> None:
        """Initialize memory integration pattern - public interface."""
        await self._setup()
        return None  # Explicit return for proper async/await behavior
        
    async def _setup(self) -> None:
        """Initialize memory integration pattern."""
        # Memory client will be initialized when swarm info is available
        logger.info("Memory integration pattern initialized")
        
    async def cleanup(self) -> None:
        """Cleanup memory integration pattern - public interface."""
        await self._teardown()
        return None  # Explicit return for proper async/await behavior
        
    async def _teardown(self) -> None:
        """Cleanup memory integration pattern."""
        if self.memory_client:
            await self.memory_client.close()
            self.memory_client = None
            
    async def execute(self, context: Dict[str, Any], agents: List[Any]) -> PatternResult:
        """
        Execute memory integration for swarm workflow.
        
        Args:
            context: Execution context including swarm_info, task, etc.
            agents: List of swarm agents
            
        Returns:
            PatternResult with memory integration data
        """
        start_time = datetime.now()
        
        try:
            # Initialize memory client if not done
            await self._ensure_memory_client(context)
            
            # Load relevant context
            if self.config.load_context_on_init:
                await self._load_swarm_context(context)
            
            # Store task initiation
            task = context.get("task", {})
            if task:
                await self._store_task_initiation(task, agents)
            
            # Apply memory-enhanced execution
            result = await self._execute_with_memory(context, agents)
            
            # Store execution results
            await self._store_execution_results(context, result)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return PatternResult(
                success=True,
                data={
                    "memory_client_active": self.memory_client is not None,
                    "context_loaded": bool(self.swarm_context),
                    "memory_operations": len(self.memory_operations_log),
                    "execution_result": result
                },
                pattern_name="memory_integration",
                execution_time=execution_time,
                metrics={
                    "memory_ops_count": len(self.memory_operations_log),
                    "context_patterns_loaded": len(self.swarm_context.get("patterns", [])),
                    "context_learnings_loaded": len(self.swarm_context.get("learnings", []))
                }
            )
            
        except Exception as e:
            logger.error(f"Memory integration execution failed: {e}")
            return PatternResult(
                success=False,
                error=str(e),
                pattern_name="memory_integration"
            )
    
    async def _ensure_memory_client(self, context: Dict[str, Any]):
        """Ensure memory client is initialized with swarm information."""
        if self.memory_client:
            return
            
        # Extract swarm information from context
        swarm_info = context.get("swarm_info", {})
        swarm_type = swarm_info.get("type", "unknown_swarm")
        swarm_id = swarm_info.get("id", f"{swarm_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Initialize memory client
        self.memory_client = SwarmMemoryClient(swarm_type, swarm_id)
        await self.memory_client.initialize()
        
        logger.info(f"Memory client initialized for {swarm_type}:{swarm_id}")
    
    async def _load_swarm_context(self, context: Dict[str, Any]):
        """Load relevant context from memory system."""
        if not self.memory_client:
            return
            
        try:
            # Load swarm context
            self.swarm_context = await self.memory_client.load_swarm_context()
            
            # Apply context to execution if available
            if self.swarm_context.get("patterns"):
                context["memory_patterns"] = self.swarm_context["patterns"][:self.config.max_context_patterns]
            
            if self.swarm_context.get("learnings"):
                context["memory_learnings"] = self.swarm_context["learnings"][:self.config.max_context_learnings]
            
            logger.info(f"Loaded swarm context: {len(self.swarm_context.get('patterns', []))} patterns, "
                       f"{len(self.swarm_context.get('learnings', []))} learnings")
                       
        except Exception as e:
            logger.error(f"Failed to load swarm context: {e}")
    
    async def _store_task_initiation(self, task: Dict[str, Any], agents: List[Any]):
        """Store task initiation event."""
        if not self.memory_client:
            return
            
        try:
            await self.memory_client.log_swarm_event(
                SwarmMemoryEventType.TASK_STARTED,
                {
                    "task_type": task.get("type", "unknown"),
                    "task_description": str(task.get("description", ""))[:200],
                    "agent_count": len(agents),
                    "agents": [str(agent) for agent in agents[:10]]  # Limit for storage
                }
            )
            
            self._log_memory_operation("task_initiation", "success")
            
        except Exception as e:
            logger.error(f"Failed to store task initiation: {e}")
            self._log_memory_operation("task_initiation", "failed", str(e))
    
    async def _execute_with_memory(self, context: Dict[str, Any], agents: List[Any]) -> Dict[str, Any]:
        """Execute with memory-enhanced capabilities."""
        
        # Apply memory context to enhance execution
        enhanced_context = context.copy()
        
        # Add relevant patterns to context
        if "memory_patterns" in context:
            enhanced_context["suggested_patterns"] = [
                p for p in context["memory_patterns"]
                if p.get("success_score", 0) > self.config.min_quality_for_pattern_storage
            ]
        
        # Add relevant learnings to context
        if "memory_learnings" in context:
            enhanced_context["relevant_learnings"] = [
                l for l in context["memory_learnings"]
                if l.get("confidence", 0) > self.config.min_confidence_for_learning
            ]
        
        # Execute with enhanced context
        result = {
            "enhanced_context_applied": True,
            "memory_patterns_available": len(enhanced_context.get("suggested_patterns", [])),
            "memory_learnings_available": len(enhanced_context.get("relevant_learnings", [])),
            "execution_timestamp": datetime.now().isoformat()
        }
        
        return result
    
    async def _store_execution_results(self, context: Dict[str, Any], result: Dict[str, Any]):
        """Store execution results and outcomes."""
        if not self.memory_client:
            return
            
        try:
            task = context.get("task", {})
            quality_score = result.get("quality_score", 0.5)
            
            # Log task completion
            await self.memory_client.log_swarm_event(
                SwarmMemoryEventType.TASK_COMPLETED,
                {
                    "task_type": task.get("type", "unknown"),
                    "success": result.get("success", False),
                    "quality_score": quality_score,
                    "execution_time": result.get("execution_time", 0),
                    "patterns_used": result.get("patterns_used", []),
                    "result_summary": str(result).get("summary", str(result))[:300]
                }
            )
            
            # Store successful patterns if quality threshold met
            if (self.config.auto_store_patterns and 
                quality_score >= self.config.min_quality_for_pattern_storage):
                
                await self._store_successful_pattern(context, result)
            
            # Store learnings if available
            if self.config.auto_store_learnings and "learnings" in result:
                await self._store_learnings(result["learnings"])
            
            # Store performance metrics
            if self.config.auto_store_metrics and "metrics" in result:
                await self.memory_client.store_performance_metrics(
                    result["metrics"],
                    execution_context=context
                )
            
            self._log_memory_operation("execution_results", "success")
            
        except Exception as e:
            logger.error(f"Failed to store execution results: {e}")
            self._log_memory_operation("execution_results", "failed", str(e))
    
    async def _store_successful_pattern(self, context: Dict[str, Any], result: Dict[str, Any]):
        """Store successful execution pattern."""
        if not self.memory_client:
            return
            
        task = context.get("task", {})
        task_type = task.get("type", "general")
        
        pattern_data = {
            "task_characteristics": {
                "type": task_type,
                "complexity": task.get("complexity", 0.5),
                "scope": task.get("scope", "medium"),
                "urgency": task.get("urgency", "normal")
            },
            "execution_strategy": {
                "agent_roles": result.get("agent_roles", []),
                "patterns_used": result.get("patterns_used", []),
                "quality_gates_passed": result.get("quality_gates_passed", []),
                "consensus_method": result.get("consensus_method", "")
            },
            "outcome": {
                "quality_score": result.get("quality_score", 0),
                "execution_time": result.get("execution_time", 0),
                "success_factors": result.get("success_factors", [])
            }
        }
        
        await self.memory_client.store_pattern(
            pattern_name=f"execution_strategy_{task_type}",
            pattern_data=pattern_data,
            success_score=result.get("quality_score", 0),
            context={"task_context": task}
        )
        
        logger.info(f"Stored successful pattern for {task_type} (score: {result.get('quality_score', 0):.2f})")
    
    async def _store_learnings(self, learnings: List[Dict[str, Any]]):
        """Store learnings from execution."""
        if not self.memory_client:
            return
            
        for learning in learnings:
            learning_type = learning.get("type", "general")
            content = learning.get("content", "")
            confidence = learning.get("confidence", 0.5)
            
            if confidence >= self.config.min_confidence_for_learning:
                await self.memory_client.store_learning(
                    learning_type=learning_type,
                    content=content,
                    confidence=confidence,
                    context=learning.get("context", {})
                )
    
    def _log_memory_operation(self, operation: str, status: str, error: Optional[str] = None):
        """Log memory operation for tracking."""
        self.memory_operations_log.append({
            "operation": operation,
            "status": status,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
    
    # ============================================
    # Inter-Swarm Communication Methods
    # ============================================
    
    async def send_knowledge_to_swarm(
        self,
        target_swarm_type: str,
        knowledge: Dict[str, Any],
        priority: str = "normal"
    ):
        """Send knowledge or insights to another swarm."""
        if not self.memory_client or not self.config.enable_inter_swarm_comm:
            return
            
        try:
            await self.memory_client.send_message_to_swarm(
                target_swarm_type=target_swarm_type,
                message={
                    "type": "knowledge_transfer",
                    "knowledge": knowledge,
                    "from_swarm": self.memory_client.swarm_type
                },
                priority=priority
            )
            
            logger.info(f"Sent knowledge to {target_swarm_type}: {knowledge.get('type', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Failed to send knowledge to {target_swarm_type}: {e}")
    
    async def receive_inter_swarm_messages(self) -> List[Dict[str, Any]]:
        """Receive and process messages from other swarms."""
        if not self.memory_client or not self.config.enable_inter_swarm_comm:
            return []
            
        try:
            messages = await self.memory_client.get_messages_for_swarm(limit=20)
            
            # Process knowledge transfer messages
            knowledge_messages = [
                msg for msg in messages
                if msg.get("message", {}).get("type") == "knowledge_transfer"
            ]
            
            if knowledge_messages:
                logger.info(f"Received {len(knowledge_messages)} knowledge transfer messages")
            
            return knowledge_messages
            
        except Exception as e:
            logger.error(f"Failed to receive inter-swarm messages: {e}")
            return []
    
    # ============================================
    # Memory-Enhanced Decision Making
    # ============================================
    
    @with_circuit_breaker("database")
    async def enhance_decision_with_memory(
        self,
        decision_context: Dict[str, Any],
        available_options: List[Any]
    ) -> Dict[str, Any]:
        """
        Enhance decision making with memory-based insights.
        
        Args:
            decision_context: Context for the decision
            available_options: Available options to choose from
            
        Returns:
            Enhanced decision data with memory insights
        """
        if not self.memory_client:
            return {"options": available_options, "memory_enhanced": False}
        
        # Search for similar past decisions
        decision_type = decision_context.get("type", "general")
        similar_decisions = await self.memory_client.search_memory(
            query=f"decision {decision_type}",
            limit=5,
            memory_type=MemoryType.SEMANTIC,
            tags=["decision"]
        )
        
        # Get relevant learnings
        relevant_learnings = await self.memory_client.retrieve_learnings(
            learning_type="decision_making",
            limit=3
        )
        
        # Analyze patterns in past decisions
        decision_patterns = self._analyze_decision_patterns(similar_decisions)
        
        enhanced_decision = {
            "options": available_options,
            "memory_enhanced": True,
            "insights": {
                "similar_past_decisions": len(similar_decisions),
                "relevant_learnings": len(relevant_learnings),
                "decision_patterns": decision_patterns,
                "recommendations": self._generate_recommendations(
                    decision_patterns, relevant_learnings, available_options
                )
            }
        }
        
        return enhanced_decision
    
    def _analyze_decision_patterns(self, similar_decisions: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in past decisions."""
        if not similar_decisions:
            return {}
        
        # Extract decision patterns
        patterns = {
            "common_factors": [],
            "success_indicators": [],
            "failure_indicators": []
        }
        
        for decision in similar_decisions:
            try:
                content = json.loads(decision.get("content", "{}"))
                
                # Extract common factors
                if "factors" in content:
                    patterns["common_factors"].extend(content["factors"])
                
                # Extract success/failure indicators
                if content.get("outcome") == "success":
                    patterns["success_indicators"].extend(content.get("indicators", []))
                elif content.get("outcome") == "failure":
                    patterns["failure_indicators"].extend(content.get("indicators", []))
                    
            except json.JSONDecodeError:
                continue
        
        return patterns
    
    def _generate_recommendations(
        self,
        decision_patterns: Dict[str, Any],
        learnings: List[Dict],
        options: List[Any]
    ) -> List[str]:
        """Generate recommendations based on memory analysis."""
        recommendations = []
        
        # Recommendations based on success indicators
        success_indicators = decision_patterns.get("success_indicators", [])
        if success_indicators:
            recommendations.append(
                f"Past successes indicate: {', '.join(success_indicators[:3])}"
            )
        
        # Recommendations based on learnings
        high_confidence_learnings = [
            l for l in learnings if l.get("confidence", 0) > 0.8
        ]
        if high_confidence_learnings:
            recommendations.append(
                f"High-confidence learning: {high_confidence_learnings[0].get('content', '')[:100]}"
            )
        
        # General recommendation
        if len(options) > 1:
            recommendations.append(
                f"Consider {len(options)} available options against {len(success_indicators)} success patterns"
            )
        
        return recommendations[:3]  # Limit to top 3 recommendations
    
    # ============================================
    # Memory-Based Learning
    # ============================================
    
    async def capture_learning_from_execution(
        self,
        execution_result: Dict[str, Any],
        context: Dict[str, Any]
    ):
        """
        Capture and store learnings from execution.
        
        Args:
            execution_result: Result of swarm execution
            context: Execution context
        """
        if not self.memory_client or not self.config.auto_store_learnings:
            return
        
        # Extract learnings from execution
        learnings = []
        
        # Quality-based learnings
        quality_score = execution_result.get("quality_score", 0)
        if quality_score > 0.9:
            learnings.append({
                "type": "high_quality_execution",
                "content": f"Achieved exceptional quality ({quality_score:.2f}) using: {execution_result.get('success_factors', [])}",
                "confidence": 0.9,
                "context": {"quality_score": quality_score}
            })
        elif quality_score < 0.5:
            learnings.append({
                "type": "quality_improvement",
                "content": f"Low quality execution ({quality_score:.2f}). Issues: {execution_result.get('issues', [])}",
                "confidence": 0.8,
                "context": {"quality_score": quality_score}
            })
        
        # Performance learnings
        execution_time = execution_result.get("execution_time", 0)
        if execution_time > 0:
            if execution_time < 5.0:  # Fast execution
                learnings.append({
                    "type": "performance_optimization",
                    "content": f"Fast execution achieved in {execution_time:.1f}s using efficient patterns",
                    "confidence": 0.7,
                    "context": {"execution_time": execution_time}
                })
            elif execution_time > 60.0:  # Slow execution
                learnings.append({
                    "type": "performance_issue",
                    "content": f"Slow execution ({execution_time:.1f}s) may indicate optimization opportunities",
                    "confidence": 0.6,
                    "context": {"execution_time": execution_time}
                })
        
        # Store learnings
        for learning in learnings:
            await self._store_learnings([learning])
        
        if learnings:
            logger.info(f"Captured {len(learnings)} learnings from execution")
    
    # ============================================
    # Utility Methods
    # ============================================
    
    def get_memory_integration_metrics(self) -> Dict[str, Any]:
        """Get metrics specific to memory integration."""
        return {
            "memory_client_active": self.memory_client is not None,
            "operations_logged": len(self.memory_operations_log),
            "context_loaded": bool(self.swarm_context),
            "successful_operations": len([
                op for op in self.memory_operations_log 
                if op.get("status") == "success"
            ]),
            "failed_operations": len([
                op for op in self.memory_operations_log 
                if op.get("status") == "failed"
            ]),
            "last_operation": self.memory_operations_log[-1] if self.memory_operations_log else None
        }
    
    async def validate_memory_integration(self) -> Dict[str, Any]:
        """Validate memory integration is working correctly."""
        validation = {
            "memory_client_initialized": self.memory_client is not None,
            "mcp_server_accessible": False,
            "memory_operations_functional": False,
            "context_loading_functional": False
        }
        
        if self.memory_client:
            try:
                # Test MCP server connectivity
                stats = await self.memory_client.get_memory_stats()
                validation["mcp_server_accessible"] = "error" not in stats
                
                # Test memory operations
                test_entry = await self.memory_client.store_memory(
                    topic="Memory Integration Test",
                    content="Test memory operation for validation",
                    memory_type=MemoryType.EPISODIC,
                    tags=["test", "validation"]
                )
                validation["memory_operations_functional"] = "error" not in test_entry
                
                # Test context loading
                test_context = await self.memory_client.load_swarm_context()
                validation["context_loading_functional"] = isinstance(test_context, dict)
                
            except Exception as e:
                logger.error(f"Memory integration validation failed: {e}")
                validation["validation_error"] = str(e)
        
        return validation


# ============================================
# Memory-Enhanced Strategy Archive
# ============================================

class MemoryEnhancedStrategyArchive:
    """
    Memory-enhanced strategy archive that uses unified memory system
    instead of local files for pattern storage and retrieval.
    """
    
    def __init__(self, swarm_type: str, memory_client: SwarmMemoryClient):
        self.swarm_type = swarm_type
        self.memory_client = memory_client
        
    async def archive_success(
        self,
        problem_type: str,
        roles: List[str],
        interaction_sequence: str,
        quality_score: float,
        additional_context: Optional[Dict[str, Any]] = None
    ):
        """Archive successful pattern in unified memory system."""
        if quality_score < 0.8:
            return  # Only archive high-quality solutions
        
        pattern_data = {
            "problem_type": problem_type,
            "roles": roles,
            "interaction_sequence": interaction_sequence,
            "quality_score": quality_score,
            "usage_count": 1,
            "swarm_type": self.swarm_type,
            "additional_context": additional_context or {}
        }
        
        await self.memory_client.store_pattern(
            pattern_name=f"strategy_{problem_type}",
            pattern_data=pattern_data,
            success_score=quality_score,
            context=additional_context
        )
        
        logger.info(f"Archived successful strategy for {problem_type} (score: {quality_score:.2f})")
    
    async def retrieve_best_pattern(self, problem_type: str) -> Optional[Dict[str, Any]]:
        """Retrieve best pattern for problem type from memory."""
        patterns = await self.memory_client.retrieve_patterns(
            pattern_name=f"strategy_{problem_type}",
            limit=1
        )
        
        if patterns:
            # Update usage count by storing learning about pattern reuse
            best_pattern = patterns[0]
            await self.memory_client.store_learning(
                learning_type="pattern_reuse",
                content=f"Reused successful pattern for {problem_type}",
                confidence=0.9,
                context={"pattern_id": best_pattern.get("pattern_name", "")}
            )
            
            return best_pattern.get("pattern_data", {})
        
        return None