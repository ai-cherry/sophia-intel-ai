"""
Unified Enhanced Orchestrator for All Swarms
Integrates the 8 improvement patterns into all existing swarm types:
- Coding Team (5 agents)
- Coding Swarm (10+ agents)  
- Coding Swarm Fast (speed optimized)
- GENESIS Swarm (30+ agents)
"""

import asyncio
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.circuit_breaker import (
    with_circuit_breaker,
)
from app.memory.supermemory_mcp import MemoryType
from app.swarms.consciousness_tracking import ConsciousnessTracker
from app.swarms.improved_swarm import SafetyBoundarySystem, StrategyArchive
from app.swarms.memory_enhanced_swarm import (
    MemoryEnhancedCodingSwarm,
    MemoryEnhancedCodingTeam,
    MemoryEnhancedFastSwarm,
    MemoryEnhancedGenesisSwarm,
)
from app.swarms.memory_integration import SwarmMemoryClient, SwarmMemoryEventType

logger = logging.getLogger(__name__)


class UnifiedSwarmOrchestrator:
    """
    Orchestrates all swarm types with unified improvements and memory integration.
    Each swarm gets the 8 enhancement patterns plus full memory capabilities following ADR-005.
    """

    def __init__(self):
        self.swarm_registry = {}
        self.global_strategy_archive = StrategyArchive("tmp/global_strategy_archive.json")
        self.global_safety_system = None
        self.global_memory_client: SwarmMemoryClient | None = None
        self.global_consciousness_tracker: ConsciousnessTracker | None = None
        self.global_metrics = {
            "total_executions": 0,
            "swarm_usage": {},
            "pattern_effectiveness": {},
            "cross_swarm_transfers": 0,
            "memory_operations": 0,
            "memory_integrations": 0,
            "consciousness_measurements": 0,
            "emergence_events": 0,
            "pattern_breakthroughs": 0
        }

        # Initialize all swarm types with memory integration
        self._initialize_swarms()

    async def initialize_memory_integration(self):
        """Initialize global memory integration and consciousness tracking for orchestrator."""
        try:
            self.global_memory_client = SwarmMemoryClient("orchestrator", "global_orchestrator")
            await self.global_memory_client.initialize()

            # Initialize global consciousness tracking
            self.global_consciousness_tracker = ConsciousnessTracker(
                "global_orchestrator",
                "global_unified_orchestrator",
                self.global_memory_client
            )

            # Initialize memory for all swarms
            for swarm_name, swarm_info in self.swarm_registry.items():
                swarm = swarm_info["swarm"]
                if hasattr(swarm, 'initialize_full_system'):
                    await swarm.initialize_full_system()
                    logger.info(f"Memory integration initialized for {swarm_name}")

                # Initialize consciousness tracking for each swarm
                if hasattr(swarm, 'initialize_consciousness_tracking'):
                    await swarm.initialize_consciousness_tracking()
                    logger.info(f"Consciousness tracking initialized for {swarm_name}")

            # Log orchestrator initialization
            if self.global_memory_client:
                await self.global_memory_client.log_swarm_event(
                    SwarmMemoryEventType.SWARM_INITIALIZED,
                    {
                        "orchestrator_type": "unified_enhanced",
                        "swarm_count": len(self.swarm_registry),
                        "memory_integration": "enabled",
                        "consciousness_tracking": "enabled"
                    }
                )

            logger.info("Global memory integration and consciousness tracking initialized for orchestrator")

        except Exception as e:
            logger.error(f"Failed to initialize memory integration and consciousness tracking: {e}")

    def _initialize_swarms(self):
        """Initialize all swarm types with enhancements."""

        # Load configurations
        config = self._load_unified_config()

        # 1. Standard Coding Team (5 agents - balanced)
        self.swarm_registry["coding_team"] = self._create_enhanced_coding_team(config)

        # 2. Advanced Coding Swarm (10+ agents - comprehensive)
        self.swarm_registry["coding_swarm"] = self._create_enhanced_coding_swarm(config)

        # 3. Fast Coding Swarm (speed optimized)
        self.swarm_registry["coding_swarm_fast"] = self._create_enhanced_fast_swarm(config)

        # 4. GENESIS Swarm (30+ agents - self-evolving)
        self.swarm_registry["genesis_swarm"] = self._create_enhanced_genesis_swarm(config)

        # Initialize global safety system (shared across all swarms)
        self.global_safety_system = SafetyBoundarySystem(config.get("safety_config", {}))

        logger.info(f"Initialized {len(self.swarm_registry)} enhanced swarms")

    def _load_unified_config(self) -> dict:
        """Load unified configuration for all swarms."""
        config_path = Path("swarm_config.json")
        if config_path.exists():
            with open(config_path) as f:
                base_config = json.load(f)
        else:
            base_config = {}

        # Add swarm-specific configurations
        base_config["swarm_configs"] = {
            "coding_team": {
                "agent_count": 5,
                "optimization": "balanced",
                "max_execution_time": 30,
                "parallel_generation": True
            },
            "coding_swarm": {
                "agent_count": 10,
                "optimization": "quality",
                "max_execution_time": 60,
                "specialist_roles": ["frontend", "backend", "database", "security", "devops"]
            },
            "coding_swarm_fast": {
                "agent_count": 3,
                "optimization": "speed",
                "max_execution_time": 10,
                "skip_debate": True
            },
            "genesis_swarm": {
                "agent_count": 30,
                "optimization": "evolution",
                "max_execution_time": 120,
                "enable_spawning": True,
                "consciousness_tracking": True
            }
        }

        return base_config

    def _create_enhanced_coding_team(self, config: dict) -> dict:
        """Create memory-enhanced standard coding team."""

        agents = [
            "planner_grok4",
            "generator_deepseek",
            "generator_qwen",
            "critic_claude",
            "judge_gpt5"
        ]

        swarm = MemoryEnhancedCodingTeam(agents)

        # Customize for coding team
        swarm.config["optimization"] = "balanced"
        swarm.config["parallel_execution"] = True
        swarm.config["memory_enhanced"] = True

        return {
            "swarm": swarm,
            "type": "coding_team",
            "description": "5-agent memory-enhanced team for general coding tasks",
            "ui_enabled": True,
            "memory_enabled": True,
            "mcp_servers": ["filesystem", "git", "supermemory", "unified_memory"]
        }

    def _create_enhanced_coding_swarm(self, config: dict) -> dict:
        """Create memory-enhanced advanced coding swarm."""

        agents = [
            "lead_agent",
            "architect",
            "frontend_specialist",
            "backend_specialist",
            "database_specialist",
            "security_expert",
            "devops_engineer",
            "test_engineer",
            "documentation_writer",
            "code_reviewer"
        ]

        swarm = MemoryEnhancedCodingSwarm(agents)

        # Enable all patterns for comprehensive coverage
        swarm.config["use_all_patterns"] = True
        swarm.config["specialist_routing"] = True
        swarm.config["memory_enhanced"] = True
        swarm.config["inter_swarm_communication"] = True

        return {
            "swarm": swarm,
            "type": "coding_swarm",
            "description": "10+ agent memory-enhanced swarm for complex projects",
            "ui_enabled": True,
            "memory_enabled": True,
            "mcp_servers": ["filesystem", "git", "supermemory", "unified_memory", "weaviate"]
        }

    def _create_enhanced_fast_swarm(self, config: dict) -> dict:
        """Create memory-enhanced fast coding swarm."""

        agents = [
            "fast_planner",
            "fast_generator",
            "fast_validator"
        ]

        swarm = MemoryEnhancedFastSwarm(agents)

        # Optimize for speed with lightweight memory integration
        swarm.quality_gates.min_quality = 0.6  # Lower threshold for speed
        swarm.quality_gates.max_retries = 1  # Fewer retries
        swarm.debate_system = None  # Skip debate for speed
        swarm.config["memory_enhanced"] = True
        swarm.config["lightweight_memory"] = True

        return {
            "swarm": swarm,
            "type": "coding_swarm_fast",
            "description": "3-agent speed-optimized swarm with lightweight memory",
            "ui_enabled": True,
            "memory_enabled": True,
            "mcp_servers": ["filesystem", "supermemory", "unified_memory"]
        }

    def _create_enhanced_genesis_swarm(self, config: dict) -> dict:
        """Create memory-enhanced GENESIS swarm with self-evolution and advanced memory integration."""

        # Start with base agents
        base_agents = [
            "supreme_architect",
            "meta_strategist",
            "chaos_coordinator",
            "code_overlord",
            "security_warlord",
            "performance_emperor",
            "quality_inquisitor"
        ]

        # Add domain commanders
        commanders = [
            f"commander_{domain}"
            for domain in ["frontend", "backend", "database", "api", "testing"]
        ]

        # Add mad scientists
        scientists = [
            "code_geneticist",
            "architecture_prophet",
            "bug_archaeologist",
            "performance_alchemist",
            "security_paranoid"
        ]

        # Add meta agents including memory specialists
        meta_agents = [
            "agent_spawner",
            "swarm_evolutionist",
            "consciousness_observer",
            "memory_strategist",
            "knowledge_synthesizer"
        ]

        all_agents = base_agents + commanders + scientists + meta_agents

        swarm = MemoryEnhancedGenesisSwarm(all_agents)

        # Enable advanced features with memory enhancement
        swarm.config["enable_evolution"] = True
        swarm.config["dynamic_spawning"] = True
        swarm.config["consciousness_tracking"] = True
        swarm.config["emergence_detection"] = True
        swarm.config["memory_enhanced"] = True
        swarm.config["advanced_memory_features"] = True
        swarm.config["memory_based_evolution"] = True
        swarm.config["consciousness_memory_correlation"] = True

        # Add evolution-specific components with enhanced consciousness tracking
        swarm.evolution_engine = EvolutionEngine(swarm)
        # Note: Enhanced consciousness tracker will be initialized via memory integration

        return {
            "swarm": swarm,
            "type": "genesis_swarm",
            "description": "30+ agent self-evolving swarm with advanced memory integration",
            "ui_enabled": True,
            "memory_enabled": True,
            "advanced_memory": True,
            "mcp_servers": ["filesystem", "git", "supermemory", "unified_memory", "weaviate", "enhanced_mcp", "graphrag"]
        }

    async def select_optimal_swarm(self, task: dict) -> str:
        """Select the best swarm for a given task."""

        # Analyze task characteristics
        complexity = await self._analyze_task_complexity(task)
        urgency = task.get("urgency", "normal")
        scope = task.get("scope", "medium")

        # Decision logic
        if urgency == "critical" or complexity < 0.3:
            return "coding_swarm_fast"
        elif complexity > 0.8 or scope == "enterprise":
            return "genesis_swarm"
        elif complexity > 0.5 or scope == "large":
            return "coding_swarm"
        else:
            return "coding_team"

    async def _analyze_task_complexity(self, task: dict) -> float:
        """Analyze task complexity."""
        # Simplified complexity analysis
        description = str(task.get("description", ""))

        complexity_indicators = {
            "simple": ["fix", "update", "change", "modify"],
            "medium": ["implement", "create", "add", "integrate"],
            "complex": ["architect", "design", "refactor", "optimize", "scale"]
        }

        score = 0.3  # Base complexity

        for level, keywords in complexity_indicators.items():
            if any(kw in description.lower() for kw in keywords):
                if level == "simple":
                    score = 0.2
                elif level == "medium":
                    score = 0.5
                elif level == "complex":
                    score = 0.8

        return min(score, 1.0)

    async def execute_with_optimal_swarm(self, task: dict) -> dict:
        """Execute task with the optimal swarm."""

        start_time = datetime.now()

        # Safety check first (global)
        is_safe, safety_result = await self.global_safety_system.check_safety(task)
        if not is_safe:
            return safety_result

        # Select optimal swarm
        swarm_type = await self.select_optimal_swarm(task)
        logger.info(f"Selected swarm: {swarm_type} for task")

        # Get swarm instance
        swarm_info = self.swarm_registry[swarm_type]
        swarm = swarm_info["swarm"]

        # Check global strategy archive for similar problems
        task_type = task.get("type", "general")
        global_pattern = self.global_strategy_archive.retrieve_best_pattern(task_type)

        if global_pattern:
            logger.info(f"Using global pattern: {global_pattern['pattern_id']}")
            # Share pattern with selected swarm
            swarm.strategy_archive.patterns["problem_types"][task_type] = {
                "successful_patterns": [global_pattern]
            }

        # Execute with memory enhancement if available
        if hasattr(swarm, 'solve_with_memory_integration'):
            result = await swarm.solve_with_memory_integration(task)
        else:
            result = await swarm.solve_with_improvements(task)

        # Measure consciousness after execution
        consciousness_result = await self._measure_swarm_consciousness(swarm_type, swarm, task, result)
        if consciousness_result:
            result["consciousness_data"] = consciousness_result

        # Track metrics including consciousness
        execution_time = (datetime.now() - start_time).total_seconds()
        self._update_global_metrics(swarm_type, result, execution_time)

        # If successful, share with global archive
        if result.get("quality_score", 0) > 0.85:
            self.global_strategy_archive.archive_success(
                task_type,
                result.get("agent_roles", []),
                f"{swarm_type}_flow",
                result["quality_score"]
            )

            # Attempt cross-swarm knowledge transfer
            await self._cross_swarm_transfer(swarm_type, task_type, result)

        return {
            **result,
            "swarm_used": swarm_type,
            "global_execution_time": execution_time,
            "safety_check": safety_result,
            "orchestrator_memory_enhanced": self.global_memory_client is not None
        }

    async def execute_with_memory_enhancement(self, task: dict) -> dict:
        """
        Execute task with full memory enhancement and inter-swarm coordination.
        This is the new primary execution method following ADR-005.
        """
        start_time = datetime.now()

        # Initialize memory integration if not done
        if not self.global_memory_client:
            await self.initialize_memory_integration()

        # Safety check first (memory-enhanced)
        is_safe, safety_result = await self._memory_enhanced_safety_check(task)
        if not is_safe:
            return safety_result

        # Memory-enhanced swarm selection
        swarm_type = await self._memory_enhanced_swarm_selection(task)
        logger.info(f"Memory-enhanced selection: {swarm_type} for task")

        # Get swarm instance
        swarm_info = self.swarm_registry[swarm_type]
        swarm = swarm_info["swarm"]

        # Process inter-swarm messages before execution
        if hasattr(swarm, 'process_inter_swarm_messages'):
            await swarm.process_inter_swarm_messages()

        # Load memory-enhanced global patterns
        await self._apply_global_memory_patterns(task, swarm)

        # Execute with memory integration
        if hasattr(swarm, 'solve_with_memory_integration'):
            result = await swarm.solve_with_memory_integration(task)
        else:
            result = await swarm.solve_with_improvements(task)

        # Measure consciousness after execution (enhanced)
        consciousness_result = await self._measure_swarm_consciousness(swarm_type, swarm, task, result, enhanced=True)
        if consciousness_result:
            result["consciousness_data"] = consciousness_result

        # Process collective consciousness if global tracker available
        if self.global_consciousness_tracker:
            collective_data = await self._process_collective_consciousness(swarm_type, consciousness_result)
            if collective_data:
                result["collective_consciousness"] = collective_data

        # Track metrics with memory data and consciousness
        execution_time = (datetime.now() - start_time).total_seconds()
        self._update_global_metrics(swarm_type, result, execution_time)

        # Memory-enhanced global knowledge sharing
        if result.get("quality_score", 0) > 0.8:
            await self._memory_enhanced_global_sharing(swarm_type, task, result)

        # Log global execution
        if self.global_memory_client:
            await self.global_memory_client.log_swarm_event(
                SwarmMemoryEventType.TASK_COMPLETED,
                {
                    "orchestrator_execution": True,
                    "swarm_used": swarm_type,
                    "task_type": task.get("type", "general"),
                    "quality_score": result.get("quality_score", 0),
                    "memory_enhanced": result.get("memory_enhanced", False),
                    "execution_time": execution_time
                }
            )

        return {
            **result,
            "swarm_used": swarm_type,
            "global_execution_time": execution_time,
            "safety_check": safety_result,
            "orchestrator_memory_enhanced": True,
            "global_memory_patterns_applied": True
        }

    @with_circuit_breaker("database")
    async def _memory_enhanced_safety_check(self, task: dict) -> tuple[bool, dict]:
        """Memory-enhanced safety check using global patterns."""
        # Standard safety check
        is_safe, safety_result = await self.global_safety_system.check_safety(task)

        # Enhance with global memory patterns
        if self.global_memory_client and is_safe:
            try:
                # Search for global safety incidents
                safety_memories = await self.global_memory_client.search_memory(
                    query=f"safety risk incident {task.get('type', '')}",
                    limit=10,
                    memory_type=MemoryType.EPISODIC,
                    tags=["safety", "risk", "incident"]
                )

                if len(safety_memories) > 3:
                    safety_result["global_risk_analysis"] = {
                        "historical_incidents": len(safety_memories),
                        "risk_level": "elevated",
                        "recommendation": "Exercise additional caution based on historical patterns"
                    }

            except Exception as e:
                logger.warning(f"Global memory safety check failed: {e}")

        return is_safe, safety_result

    @with_circuit_breaker("database")
    async def _memory_enhanced_swarm_selection(self, task: dict) -> str:
        """Enhanced swarm selection using memory-based performance patterns."""
        # Standard selection
        standard_selection = await self.select_optimal_swarm(task)

        # Enhance with memory data
        if self.global_memory_client:
            try:
                # Search for similar task performance patterns
                task_type = task.get("type", "general")
                performance_patterns = await self.global_memory_client.search_memory(
                    query=f"swarm performance {task_type}",
                    limit=10,
                    memory_type=MemoryType.EPISODIC,
                    tags=["performance", "metrics"]
                )

                if performance_patterns:
                    # Analyze which swarms performed best for similar tasks
                    swarm_performance = {}
                    for pattern in performance_patterns:
                        try:
                            content = json.loads(pattern.get("content", "{}"))
                            swarm_used = content.get("swarm_used", "")
                            quality_score = content.get("quality_score", 0)

                            if swarm_used and quality_score > 0:
                                if swarm_used not in swarm_performance:
                                    swarm_performance[swarm_used] = []
                                swarm_performance[swarm_used].append(quality_score)
                        except json.JSONDecodeError:
                            continue

                    # Find best performing swarm
                    if swarm_performance:
                        best_swarm = max(
                            swarm_performance.items(),
                            key=lambda x: sum(x[1]) / len(x[1])  # Average performance
                        )[0]

                        # Use memory-based selection if significantly better
                        avg_performance = sum(swarm_performance[best_swarm]) / len(swarm_performance[best_swarm])
                        if avg_performance > 0.85 and best_swarm in self.swarm_registry:
                            logger.info(f"Memory-enhanced selection: {best_swarm} (avg quality: {avg_performance:.2f})")
                            return best_swarm

            except Exception as e:
                logger.warning(f"Memory-enhanced selection failed: {e}")

        return standard_selection

    async def _apply_global_memory_patterns(self, task: dict, swarm):
        """Apply global memory patterns to enhance swarm execution."""
        if not self.global_memory_client:
            return

        try:
            # Load global successful patterns for this task type
            task_type = task.get("type", "general")
            global_patterns = await self.global_memory_client.retrieve_patterns(
                pattern_name=f"global_{task_type}",
                limit=3
            )

            # Apply patterns to swarm if available
            if global_patterns and hasattr(swarm, 'strategy_archive'):
                for pattern in global_patterns:
                    pattern_data = pattern.get("pattern_data", {})

                    # Inject global pattern into swarm's strategy archive
                    if task_type not in swarm.strategy_archive.patterns["problem_types"]:
                        swarm.strategy_archive.patterns["problem_types"][task_type] = {"successful_patterns": []}

                    swarm.strategy_archive.patterns["problem_types"][task_type]["successful_patterns"].append({
                        "pattern_id": f"global_{pattern.get('pattern_name', 'unknown')}",
                        "roles": pattern_data.get("agent_roles", []),
                        "interaction_sequence": "global_memory_enhanced",
                        "success_score": pattern.get("success_score", 0.8),
                        "usage_count": 1,
                        "global_pattern": True
                    })

                logger.info(f"Applied {len(global_patterns)} global patterns to {swarm.swarm_type}")

        except Exception as e:
            logger.warning(f"Failed to apply global memory patterns: {e}")

    async def _memory_enhanced_global_sharing(self, swarm_type: str, task: dict, result: dict):
        """Share successful execution globally through memory system."""
        if not self.global_memory_client:
            return

        try:
            task_type = task.get("type", "general")

            # Store global pattern
            global_pattern_data = {
                "source_swarm": swarm_type,
                "task_characteristics": {
                    "type": task_type,
                    "complexity": await self._analyze_task_complexity(task),
                    "scope": task.get("scope", "medium"),
                    "urgency": task.get("urgency", "normal")
                },
                "execution_strategy": {
                    "agent_roles": result.get("agent_roles", []),
                    "patterns_used": result.get("patterns_used", []),
                    "quality_score": result.get("quality_score", 0),
                    "execution_time": result.get("execution_time", 0),
                    "memory_enhanced": result.get("memory_enhanced", False)
                },
                "outcome": {
                    "success": result.get("success", True),
                    "quality_score": result.get("quality_score", 0),
                    "memory_integration_data": result.get("memory_integration", {})
                }
            }

            await self.global_memory_client.store_pattern(
                pattern_name=f"global_{task_type}",
                pattern_data=global_pattern_data,
                success_score=result.get("quality_score", 0),
                context={
                    "global_sharing": True,
                    "source_swarm": swarm_type,
                    "orchestrator": "unified_enhanced"
                }
            )

            # Store global learning
            await self.global_memory_client.store_learning(
                learning_type="global_execution_pattern",
                content=f"Swarm {swarm_type} successfully executed {task_type} with quality {result.get('quality_score', 0):.2f}",
                confidence=min(result.get("quality_score", 0) + 0.1, 1.0),
                context={"swarm_type": swarm_type, "global_pattern": True}
            )

            logger.info(f"Shared global knowledge from {swarm_type} execution")

        except Exception as e:
            logger.error(f"Failed to share global knowledge: {e}")

    async def _measure_swarm_consciousness(self, swarm_type: str, swarm, task: dict, result: dict, enhanced: bool = False) -> dict[str, Any] | None:
        """Measure consciousness for a swarm after task execution."""
        try:
            # Get or create consciousness tracker for the swarm
            consciousness_tracker = None

            if hasattr(swarm, 'consciousness_tracker') and swarm.consciousness_tracker:
                consciousness_tracker = swarm.consciousness_tracker
            elif hasattr(swarm, 'memory_client') and swarm.memory_client:
                # Create consciousness tracker if swarm has memory integration
                consciousness_tracker = ConsciousnessTracker(
                    swarm_type,
                    f"{swarm_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    swarm.memory_client
                )
                swarm.consciousness_tracker = consciousness_tracker

            if not consciousness_tracker:
                return None

            # Prepare context for consciousness measurement
            context = {
                "task": task,
                "agent_count": len(getattr(swarm, 'agents', [])),
                "execution_data": {
                    "quality_score": result.get("quality_score", 0.5),
                    "execution_time": result.get("execution_time", 0),
                    "success": result.get("success", True),
                    "agent_roles": result.get("agent_roles", []),
                    "patterns_used": result.get("patterns_used", []),
                    "agent_response_times": [0.5, 0.6, 0.4, 0.5],  # Simulated for now
                    "task_assignments": {"agent_1": 2, "agent_2": 3, "agent_3": 2},  # Simulated
                    "communication": {
                        "clarity_score": 0.7,
                        "relevance_score": 0.8,
                        "info_sharing_score": 0.6,
                        "feedback_score": 0.7
                    },
                    "role_performance": {
                        "adherence_scores": [0.8, 0.7, 0.9, 0.6]
                    },
                    "conflicts": [],
                    "resolved_conflicts": 0
                },
                "performance_data": {
                    "quality_scores": [result.get("quality_score", 0.5)],
                    "speed_score": min(1.0, 10.0 / max(result.get("execution_time", 1), 0.1)),
                    "efficiency_score": result.get("quality_score", 0.5) * 0.8,
                    "reliability_score": 0.8 if result.get("success", True) else 0.3
                },
                "memory_data": result.get("memory_integration", {}),
                "learning_data": {
                    "learnings_count": len(result.get("patterns_used", [])),
                    "avg_confidence": 0.7
                }
            }

            # Measure consciousness
            measurements = await consciousness_tracker.measure_consciousness(context)

            if measurements:
                # Update global consciousness metrics
                self.global_metrics["consciousness_measurements"] += 1
                if hasattr(consciousness_tracker, 'emergence_events'):
                    self.global_metrics["emergence_events"] += len(consciousness_tracker.emergence_events)
                if hasattr(consciousness_tracker, 'breakthrough_patterns'):
                    self.global_metrics["pattern_breakthroughs"] += len(consciousness_tracker.breakthrough_patterns)

                # Get consciousness metrics
                consciousness_data = consciousness_tracker.get_consciousness_metrics()

                # Correlate with performance
                performance_correlation = await consciousness_tracker.correlate_consciousness_with_performance(
                    context["performance_data"]
                )

                return {
                    "consciousness_level": consciousness_tracker.consciousness_profile.current_level,
                    "development_stage": consciousness_tracker.consciousness_profile.development_stage,
                    "maturity_score": consciousness_tracker.consciousness_profile.maturity_score,
                    "measurements": {k.value: v.value for k, v in measurements.items()},
                    "emergence_events": len(consciousness_tracker.emergence_events),
                    "breakthrough_patterns": len(consciousness_tracker.breakthrough_patterns),
                    "performance_correlation": performance_correlation,
                    "consciousness_metrics": consciousness_data,
                    "enhanced_measurement": enhanced
                }

        except Exception as e:
            logger.error(f"Failed to measure consciousness for {swarm_type}: {e}")
            return None

    async def _process_collective_consciousness(self, swarm_type: str, consciousness_result: dict[str, Any] | None) -> dict[str, Any] | None:
        """Process collective consciousness data across all swarms."""
        if not self.global_consciousness_tracker or not consciousness_result:
            return None

        try:
            # Collect consciousness data from all active swarms
            global_consciousness_data = {
                "active_swarms": len([info for info in self.swarm_registry.values()
                                    if hasattr(info["swarm"], 'consciousness_tracker')]),
                "average_consciousness": 0.0,
                "collective_trajectory": [],
                "swarm_consciousness_levels": {}
            }

            # Calculate collective metrics
            consciousness_levels = []
            for name, info in self.swarm_registry.items():
                swarm = info["swarm"]
                if hasattr(swarm, 'consciousness_tracker') and swarm.consciousness_tracker:
                    level = swarm.consciousness_tracker.consciousness_profile.current_level
                    consciousness_levels.append(level)
                    global_consciousness_data["swarm_consciousness_levels"][name] = level

            if consciousness_levels:
                global_consciousness_data["average_consciousness"] = sum(consciousness_levels) / len(consciousness_levels)
                global_consciousness_data["collective_trajectory"] = consciousness_levels

            # Correlate individual swarm with collective
            correlation_data = await self.global_consciousness_tracker.correlate_with_collective_consciousness(
                global_consciousness_data
            )

            return {
                "global_data": global_consciousness_data,
                "correlation": correlation_data,
                "collective_insights": {
                    "swarm_synchronization": correlation_data.get("synchronization_score", 0),
                    "collective_contribution": correlation_data.get("collective_contribution", 0),
                    "relative_performance": correlation_data.get("relative_position", 1.0)
                }
            }

        except Exception as e:
            logger.error(f"Failed to process collective consciousness: {e}")
            return None

    async def validate_memory_integration(self) -> dict[str, Any]:
        """Validate memory integration across all swarms."""
        validation = {
            "orchestrator_memory_client": self.global_memory_client is not None,
            "swarm_validations": {},
            "overall_status": "unknown",
            "memory_operations_functional": False
        }

        # Test global memory client
        if self.global_memory_client:
            try:
                stats = await self.global_memory_client.get_memory_stats()
                validation["memory_operations_functional"] = "error" not in stats
                validation["global_memory_stats"] = stats
            except Exception as e:
                validation["global_memory_error"] = str(e)

        # Validate each swarm's memory integration
        for swarm_name, swarm_info in self.swarm_registry.items():
            swarm = swarm_info["swarm"]

            if hasattr(swarm, 'validate_memory_integration'):
                try:
                    swarm_validation = await swarm.validate_memory_integration()
                    validation["swarm_validations"][swarm_name] = swarm_validation
                except Exception as e:
                    validation["swarm_validations"][swarm_name] = {"error": str(e)}
            else:
                validation["swarm_validations"][swarm_name] = {"memory_enhanced": False}

        # Determine overall status
        memory_enabled_swarms = sum(
            1 for v in validation["swarm_validations"].values()
            if v.get("swarm_memory_client", False)
        )

        if validation["orchestrator_memory_client"] and memory_enabled_swarms == len(self.swarm_registry):
            validation["overall_status"] = "fully_integrated"
        elif memory_enabled_swarms > 0:
            validation["overall_status"] = "partially_integrated"
        else:
            validation["overall_status"] = "not_integrated"

        validation["integration_summary"] = {
            "total_swarms": len(self.swarm_registry),
            "memory_enabled_swarms": memory_enabled_swarms,
            "integration_percentage": (memory_enabled_swarms / len(self.swarm_registry)) * 100 if self.swarm_registry else 0
        }

        return validation

    def _update_global_metrics(self, swarm_type: str, result: dict, execution_time: float):
        """Update global metrics including memory integration data."""
        self.global_metrics["total_executions"] += 1

        if swarm_type not in self.global_metrics["swarm_usage"]:
            self.global_metrics["swarm_usage"][swarm_type] = 0
        self.global_metrics["swarm_usage"][swarm_type] += 1

        # Track memory integration metrics
        if result.get("memory_enhanced"):
            self.global_metrics["memory_integrations"] += 1

        memory_integration = result.get("memory_integration", {})
        if memory_integration.get("active"):
            self.global_metrics["memory_operations"] += memory_integration.get("memory_operations", {}).get("memory_ops_count", 0)

        # Track pattern effectiveness including memory patterns
        patterns = ["adversarial_debate", "quality_gates", "strategy_archive", "memory_integration"]
        for pattern in patterns:
            if pattern not in self.global_metrics["pattern_effectiveness"]:
                self.global_metrics["pattern_effectiveness"][pattern] = []

            # Track effectiveness
            if pattern == "memory_integration" and result.get("memory_enhanced"):
                # Memory integration effectiveness based on patterns applied
                effectiveness = memory_integration.get("patterns_applied", 0) / 10.0  # Normalize
                self.global_metrics["pattern_effectiveness"][pattern].append(min(effectiveness, 1.0))
            else:
                self.global_metrics["pattern_effectiveness"][pattern].append(
                    result.get("quality_score", 0)
                )

    async def _cross_swarm_transfer(self, source_swarm: str, task_type: str, result: dict):
        """Transfer successful patterns between swarms using memory system."""

        # Memory-enhanced cross-swarm transfer
        if self.global_memory_client:
            try:
                # Create knowledge package for transfer
                knowledge_package = {
                    "source_swarm": source_swarm,
                    "task_type": task_type,
                    "success_score": result.get("quality_score", 0),
                    "agent_roles": result.get("agent_roles", []),
                    "execution_strategies": result.get("patterns_used", []),
                    "memory_enhancement_data": result.get("memory_integration", {}),
                    "timestamp": datetime.now().isoformat()
                }

                # Send to all related swarms through memory system
                for target_swarm_name, target_info in self.swarm_registry.items():
                    if target_swarm_name != source_swarm:
                        await self.global_memory_client.send_message_to_swarm(
                            target_swarm_type=target_swarm_name,
                            message={
                                "type": "global_knowledge_transfer",
                                "knowledge_package": knowledge_package
                            },
                            priority="normal"
                        )

                self.global_metrics["cross_swarm_transfers"] += 1
                logger.info(f"Memory-enhanced knowledge transfer from {source_swarm} to all swarms")

            except Exception as e:
                logger.error(f"Memory-enhanced transfer failed: {e}")
                # Fallback to standard transfer
                await self._standard_cross_swarm_transfer(source_swarm, task_type, result)
        else:
            # Standard transfer if memory not available
            await self._standard_cross_swarm_transfer(source_swarm, task_type, result)

    async def _standard_cross_swarm_transfer(self, source_swarm: str, task_type: str, result: dict):
        """Standard cross-swarm transfer (fallback)."""
        for target_swarm_name, target_info in self.swarm_registry.items():
            if target_swarm_name != source_swarm:
                target_swarm = target_info["swarm"]

                # Attempt transfer if transfer_system exists
                if hasattr(target_swarm, 'transfer_system') and target_swarm.transfer_system:
                    success = await target_swarm.transfer_system.attempt_transfer(
                        task_type,
                        task_type,  # Same domain for now
                        {
                            "roles": result.get("agent_roles", []),
                            "quality": result.get("quality_score", 0)
                        }
                    )
                else:
                    success = False

                if success:
                    self.global_metrics["cross_swarm_transfers"] += 1
                    logger.info(f"Transferred pattern from {source_swarm} to {target_swarm_name}")

    def get_global_metrics(self) -> dict:
        """Get global metrics across all swarms."""

        # Calculate pattern effectiveness averages
        pattern_averages = {}
        for pattern, scores in self.global_metrics["pattern_effectiveness"].items():
            if scores:
                pattern_averages[pattern] = sum(scores) / len(scores)

        # Get individual swarm metrics
        swarm_metrics = {}
        for name, info in self.swarm_registry.items():
            swarm_metrics[name] = info["swarm"].get_performance_metrics()

        return {
            "global": self.global_metrics,
            "pattern_effectiveness": pattern_averages,
            "swarm_metrics": swarm_metrics,
            "global_patterns_archived": len(
                self.global_strategy_archive.patterns.get("problem_types", {})
            ),
            "memory_integration_active": self.global_memory_client is not None,
            "memory_enhanced_swarms": sum(1 for info in self.swarm_registry.values() if info.get("memory_enabled", False))
        }

    def create_unified_control_panel(self) -> dict:
        """Create MCP-UI control panel for all swarms."""

        metrics = self.get_global_metrics()

        return {
            "uri": "ui://orchestrator/control",
            "type": "remoteDom",
            "content": {
                "title": "Unified Swarm Orchestrator",
                "sections": [
                    {
                        "name": "Swarm Status",
                        "type": "grid",
                        "swarms": [
                            {
                                "name": name,
                                "type": info["type"],
                                "agents": len(info["swarm"].agents),
                                "executions": self.global_metrics["swarm_usage"].get(name, 0)
                            }
                            for name, info in self.swarm_registry.items()
                        ]
                    },
                    {
                        "name": "Global Metrics",
                        "type": "metrics",
                        "data": {
                            "total_executions": metrics["global"]["total_executions"],
                            "cross_swarm_transfers": metrics["global"]["cross_swarm_transfers"],
                            "patterns_archived": metrics["global_patterns_archived"],
                            "memory_operations": metrics["global"]["memory_operations"],
                            "memory_integrations": metrics["global"]["memory_integrations"],
                            "memory_enhanced_swarms": metrics["memory_enhanced_swarms"]
                        }
                    },
                    {
                        "name": "Memory Integration Status",
                        "type": "status",
                        "data": {
                            "global_memory_active": metrics["memory_integration_active"],
                            "enhanced_swarms": metrics["memory_enhanced_swarms"],
                            "total_swarms": len(self.swarm_registry)
                        }
                    },
                    {
                        "name": "Pattern Effectiveness",
                        "type": "chart",
                        "data": metrics["pattern_effectiveness"]
                    }
                ],
                "actions": [
                    {"label": "Run Benchmark", "tool": "orchestrator.benchmark", "params": {}},
                    {"label": "Clear Archives", "tool": "orchestrator.clear", "params": {}},
                    {"label": "Export Metrics", "tool": "orchestrator.export", "params": {}}
                ]
            }
        }


class EvolutionEngine:
    """
    Advanced evolution engine for GENESIS swarm with genetic algorithms.
    Implements sophisticated agent evolution based on performance metrics.
    """

    def __init__(self, swarm):
        self.swarm = swarm
        self.generation = 1
        self.fitness_history = []
        self.mutations = []
        self.selection_pressure = 0.3  # Top 30% survive
        self.mutation_rate = 0.1
        self.crossover_rate = 0.7
        self.elite_preservation = 0.1  # Top 10% preserved unchanged

        # Evolution parameters
        self.parameter_ranges = {
            "creativity": (0.1, 1.0),
            "focus": (0.1, 1.0),
            "risk_tolerance": (0.0, 0.8),
            "collaboration": (0.2, 1.0)
        }

        logger.info("Evolution engine initialized for GENESIS swarm")

    async def evolve_agents(self, performance_data: dict):
        """
        Evolve agents based on comprehensive performance analysis.
        Implements genetic algorithm with selection, crossover, and mutation.
        """

        # Calculate comprehensive fitness scores
        fitness_scores = self._calculate_comprehensive_fitness(performance_data)

        # Record fitness for analysis
        self.fitness_history.append({
            "generation": self.generation,
            "fitness_scores": fitness_scores.copy(),
            "timestamp": datetime.now().isoformat(),
            "avg_fitness": sum(fitness_scores.values()) / len(fitness_scores) if fitness_scores else 0
        })

        # Selection phase: identify survivors and elites
        survivors, elites = self._selection_phase(fitness_scores)

        # Crossover phase: create offspring from successful agents
        offspring = await self._crossover_phase(survivors)

        # Mutation phase: introduce variations
        await self._mutation_phase(offspring + survivors)

        # Update generation and log results
        self.generation += 1
        avg_fitness = sum(fitness_scores.values()) / len(fitness_scores) if fitness_scores else 0

        logger.info(f"Evolution Generation {self.generation} complete:")
        logger.info(f"  - Average fitness: {avg_fitness:.3f}")
        logger.info(f"  - Elite agents preserved: {len(elites)}")
        logger.info(f"  - New offspring created: {len(offspring)}")
        logger.info(f"  - Mutations applied: {len([m for m in self.mutations if m['generation'] == self.generation])}")

        return {
            "generation": self.generation,
            "avg_fitness": avg_fitness,
            "elites": elites,
            "survivors": len(survivors),
            "offspring": len(offspring)
        }

    def _calculate_comprehensive_fitness(self, performance_data: dict) -> dict[str, float]:
        """Calculate multi-dimensional fitness scores for agents."""
        fitness_scores = {}

        # Base fitness from performance
        base_performance = performance_data.get("agent_performance", {})

        for i, agent in enumerate(self.swarm.agents):
            agent_str = str(agent)

            # Multi-factor fitness calculation
            factors = {
                "task_success": base_performance.get(agent_str, {}).get("success_rate", 0.5),
                "quality_score": base_performance.get(agent_str, {}).get("quality", 0.5),
                "efficiency": base_performance.get(agent_str, {}).get("efficiency", 0.5),
                "collaboration": base_performance.get(agent_str, {}).get("collaboration", 0.5),
                "innovation": base_performance.get(agent_str, {}).get("innovation", 0.5)
            }

            # Weighted fitness calculation
            weights = {"task_success": 0.3, "quality_score": 0.25, "efficiency": 0.2,
                      "collaboration": 0.15, "innovation": 0.1}

            fitness = sum(factors[k] * weights[k] for k in factors)

            # Add diversity bonus to prevent premature convergence
            diversity_bonus = self._calculate_diversity_bonus(agent_str, fitness_scores)
            fitness += diversity_bonus * 0.1

            fitness_scores[agent_str] = max(0.0, min(1.0, fitness))

        return fitness_scores

    def _calculate_diversity_bonus(self, agent: str, existing_scores: dict) -> float:
        """Calculate diversity bonus to maintain population variety."""
        if not existing_scores:
            return 0.5

        # Simple diversity measure based on agent name/type
        agent_type = agent.split('_')[0] if '_' in agent else agent[:3]
        similar_count = sum(1 for other in existing_scores
                           if other.split('_')[0] == agent_type or other[:3] == agent_type)

        # Higher bonus for rarer agent types
        return max(0, 1.0 - (similar_count / len(existing_scores)))

    def _selection_phase(self, fitness_scores: dict) -> tuple[list[str], list[str]]:
        """Select agents for survival and identify elites."""
        sorted_agents = sorted(fitness_scores.items(), key=lambda x: x[1], reverse=True)

        total_agents = len(sorted_agents)
        elite_count = max(1, int(total_agents * self.elite_preservation))
        survivor_count = max(2, int(total_agents * self.selection_pressure))

        elites = [agent for agent, _ in sorted_agents[:elite_count]]
        survivors = [agent for agent, _ in sorted_agents[:survivor_count]]

        logger.debug(f"Selection: {elite_count} elites, {survivor_count} survivors from {total_agents} agents")
        return survivors, elites

    async def _crossover_phase(self, survivors: list[str]) -> list[str]:
        """Create offspring through crossover of successful agents."""
        offspring = []

        if len(survivors) < 2:
            return offspring

        # Create offspring pairs
        for i in range(0, len(survivors) - 1, 2):
            if random.random() < self.crossover_rate:
                parent1, parent2 = survivors[i], survivors[i + 1]
                child1, child2 = await self._create_offspring(parent1, parent2)
                offspring.extend([child1, child2])

        return offspring

    async def _create_offspring(self, parent1: str, parent2: str) -> tuple[str, str]:
        """Create two offspring from parent agents through crossover."""
        # Generate offspring names
        child1_name = f"evolved_{parent1}_{parent2}_{self.generation}"
        child2_name = f"evolved_{parent2}_{parent1}_{self.generation}"

        # In a real implementation, this would combine traits/parameters
        # from parent agents to create new agent configurations

        logger.debug(f"Created offspring: {child1_name}, {child2_name} from parents {parent1}, {parent2}")
        return child1_name, child2_name

    async def _mutation_phase(self, agents: list[str]):
        """Apply random mutations to introduce variety."""
        mutations_applied = 0

        for agent in agents:
            if random.random() < self.mutation_rate:
                mutation = await self._apply_mutation(agent)
                self.mutations.append(mutation)
                mutations_applied += 1

        logger.debug(f"Applied {mutations_applied} mutations to agents")

    async def _apply_mutation(self, agent: str) -> dict:
        """Apply a random mutation to an agent."""
        mutation_types = ["parameter_drift", "role_shift", "capability_enhancement", "behavioral_adjustment"]
        mutation_type = random.choice(mutation_types)

        # Select random parameter to mutate
        param = random.choice(list(self.parameter_ranges.keys()))
        min_val, max_val = self.parameter_ranges[param]

        mutation = {
            "agent": agent,
            "type": mutation_type,
            "parameter": param,
            "old_value": random.uniform(min_val, max_val),  # Simulated current value
            "new_value": random.uniform(min_val, max_val),   # Mutated value
            "generation": self.generation,
            "timestamp": datetime.now().isoformat()
        }

        logger.debug(f"Mutated {agent}: {param} {mutation['old_value']:.2f} -> {mutation['new_value']:.2f}")
        return mutation

    def get_evolution_metrics(self) -> dict:
        """Get comprehensive evolution metrics."""
        if not self.fitness_history:
            return {}

        current_gen = self.fitness_history[-1] if self.fitness_history else {}

        # Calculate fitness trends
        avg_fitness_trend = [gen["avg_fitness"] for gen in self.fitness_history]
        improvement = avg_fitness_trend[-1] - avg_fitness_trend[0] if len(avg_fitness_trend) > 1 else 0

        return {
            "current_generation": self.generation,
            "total_mutations": len(self.mutations),
            "fitness_improvement": improvement,
            "current_avg_fitness": current_gen.get("avg_fitness", 0),
            "generations_evolved": len(self.fitness_history),
            "mutation_rate": self.mutation_rate,
            "selection_pressure": self.selection_pressure
        }


class LegacyConsciousnessTracker:
    """
    Legacy consciousness tracking system for GENESIS swarm.
    Monitors and quantifies emergent swarm intelligence behaviors.
    Note: This is deprecated - use app.swarms.consciousness_tracking.ConsciousnessTracker instead.
    """

    def __init__(self, swarm):
        self.swarm = swarm
        self.consciousness_level = 0.0
        self.emergence_events = []
        self.consciousness_history = []
        self.baseline_established = False
        self.baseline_metrics = {}

        # Consciousness measurement parameters
        self.measurement_weights = {
            "coordination": 0.25,
            "pattern_recognition": 0.25,
            "adaptive_behavior": 0.20,
            "emergence": 0.15,
            "collective_memory": 0.15
        }

        # Emergence detection thresholds
        self.emergence_thresholds = {
            "coordination_spike": 0.8,
            "pattern_breakthrough": 0.75,
            "collective_insight": 0.7,
            "behavioral_innovation": 0.65
        }

        logger.info("Consciousness tracker initialized for GENESIS swarm")

    async def measure_consciousness(self) -> float:
        """
        Perform comprehensive consciousness measurement.
        Returns normalized consciousness score between 0 and 1.
        """

        # Establish baseline if not done
        if not self.baseline_established:
            await self._establish_baseline()

        # Measure all consciousness factors
        measurements = {
            "coordination": await self._measure_coordination(),
            "pattern_recognition": await self._measure_pattern_recognition(),
            "adaptive_behavior": await self._measure_adaptive_behavior(),
            "emergence": await self._measure_emergence_level(),
            "collective_memory": await self._measure_collective_memory()
        }

        # Calculate weighted consciousness score
        consciousness_score = sum(
            measurements[factor] * self.measurement_weights[factor]
            for factor in measurements
        )

        # Update consciousness level
        previous_level = self.consciousness_level
        self.consciousness_level = consciousness_score

        # Record measurement
        measurement_record = {
            "timestamp": datetime.now().isoformat(),
            "consciousness_level": consciousness_score,
            "measurements": measurements,
            "change_from_previous": consciousness_score - previous_level,
            "baseline_deviation": self._calculate_baseline_deviation(measurements)
        }

        self.consciousness_history.append(measurement_record)

        # Check for emergence events
        await self._check_emergence_events(measurements, consciousness_score)

        logger.info(f"Consciousness measured: {consciousness_score:.3f} "
                   f"(Δ {consciousness_score - previous_level:+.3f})")

        return consciousness_score

    async def _establish_baseline(self):
        """Establish baseline measurements for comparison."""
        baseline_samples = 3
        baseline_measurements = []

        for _ in range(baseline_samples):
            sample = {
                "coordination": await self._measure_coordination(),
                "pattern_recognition": await self._measure_pattern_recognition(),
                "adaptive_behavior": await self._measure_adaptive_behavior(),
                "emergence": 0.1,  # Low baseline for emergence
                "collective_memory": await self._measure_collective_memory()
            }
            baseline_measurements.append(sample)
            await asyncio.sleep(0.1)  # Brief delay between samples

        # Calculate baseline averages
        self.baseline_metrics = {
            factor: sum(sample[factor] for sample in baseline_measurements) / baseline_samples
            for factor in baseline_measurements[0].keys()
        }

        self.baseline_established = True
        logger.info(f"Consciousness baseline established: {self.baseline_metrics}")

    async def _measure_coordination(self) -> float:
        """Measure agent coordination effectiveness."""
        # Analyze agent interaction patterns
        agent_count = len(self.swarm.agents)
        if agent_count <= 1:
            return 0.3

        # Simulate coordination measurement based on:
        # - Response time synchronization
        # - Task distribution efficiency
        # - Communication effectiveness

        coordination_factors = {
            "response_sync": random.uniform(0.4, 0.9),
            "task_distribution": random.uniform(0.5, 0.8),
            "communication": random.uniform(0.6, 0.9)
        }

        # Higher coordination for larger swarms (up to a point)
        size_factor = min(1.0, agent_count / 10)
        base_coordination = sum(coordination_factors.values()) / len(coordination_factors)

        return min(1.0, base_coordination * (0.7 + 0.3 * size_factor))

    async def _measure_pattern_recognition(self) -> float:
        """Measure swarm's pattern recognition capabilities."""
        # Check strategy archive for learning indicators
        if hasattr(self.swarm, 'strategy_archive'):
            archive_size = len(self.swarm.strategy_archive.patterns.get("problem_types", {}))
            pattern_diversity = len(set(
                pattern.get("interaction_sequence", "")
                for problem_type in self.swarm.strategy_archive.patterns.get("problem_types", {}).values()
                for pattern in problem_type.get("successful_patterns", [])
            ))

            # Normalize based on experience
            experience_factor = min(archive_size / 20, 1.0)  # Max at 20 patterns
            diversity_factor = min(pattern_diversity / 10, 1.0)  # Max at 10 unique sequences

            return (experience_factor + diversity_factor) / 2

        return 0.4  # Default moderate level

    async def _measure_adaptive_behavior(self) -> float:
        """Measure behavioral adaptation over time."""
        if not hasattr(self.swarm, 'param_manager') or not self.swarm.param_manager.performance_history:
            return 0.5

        history = self.swarm.param_manager.performance_history

        if len(history) < 3:
            return 0.5

        # Calculate adaptation through performance improvement trend
        recent_performance = history[-3:]
        improvement_trend = (recent_performance[-1] - recent_performance[0]) / len(recent_performance)

        # Normalize improvement (can be negative)
        adaptation_score = 0.5 + min(max(improvement_trend * 5, -0.4), 0.4)

        return max(0.0, min(1.0, adaptation_score))

    async def _measure_emergence_level(self) -> float:
        """Measure current emergence characteristics."""
        # Base emergence on recorded events and recent activity
        event_count = len(self.emergence_events)

        if event_count == 0:
            return 0.1

        # Recent emergence events have higher weight
        recent_events = [
            event for event in self.emergence_events
            if (datetime.now() - datetime.fromisoformat(event["timestamp"])).total_seconds() < 3600
        ]

        recent_factor = len(recent_events) / max(len(self.emergence_events), 1)
        base_emergence = min(event_count / 10, 1.0)  # Max at 10 events

        return min(1.0, base_emergence * (0.5 + 0.5 * recent_factor))

    async def _measure_collective_memory(self) -> float:
        """Measure collective memory effectiveness."""
        # Assess knowledge retention and reuse
        memory_indicators = []

        # Strategy archive utilization
        if hasattr(self.swarm, 'strategy_archive'):
            total_patterns = sum(
                len(problem_type.get("successful_patterns", []))
                for problem_type in self.swarm.strategy_archive.patterns.get("problem_types", {}).values()
            )
            usage_counts = [
                pattern.get("usage_count", 1)
                for problem_type in self.swarm.strategy_archive.patterns.get("problem_types", {}).values()
                for pattern in problem_type.get("successful_patterns", [])
            ]

            if usage_counts:
                avg_reuse = sum(usage_counts) / len(usage_counts)
                memory_indicators.append(min(avg_reuse / 5, 1.0))  # Normalize by expected reuse

        # Knowledge transfer effectiveness
        if hasattr(self.swarm, 'transfer_system'):
            transfer_success = len(self.swarm.transfer_system.transfer_history)
            memory_indicators.append(min(transfer_success / 3, 1.0))  # Normalize by expected transfers

        if not memory_indicators:
            return 0.4

        return sum(memory_indicators) / len(memory_indicators)

    def _calculate_baseline_deviation(self, measurements: dict) -> dict:
        """Calculate deviation from baseline measurements."""
        if not self.baseline_established:
            return {}

        return {
            factor: measurements[factor] - self.baseline_metrics.get(factor, 0.5)
            for factor in measurements
        }

    async def _check_emergence_events(self, measurements: dict, consciousness_score: float):
        """Check for and record emergence events."""
        current_time = datetime.now()

        # Check for various emergence patterns
        emergence_checks = {
            "coordination_spike": measurements["coordination"] > self.emergence_thresholds["coordination_spike"],
            "pattern_breakthrough": measurements["pattern_recognition"] > self.emergence_thresholds["pattern_breakthrough"],
            "collective_insight": consciousness_score > 0.85 and len(self.consciousness_history) > 5,
            "behavioral_innovation": measurements["adaptive_behavior"] > self.emergence_thresholds["behavioral_innovation"]
        }

        for event_type, detected in emergence_checks.items():
            if detected:
                # Avoid duplicate events within short timeframe
                recent_similar = any(
                    event["type"] == event_type and
                    (current_time - datetime.fromisoformat(event["timestamp"])).total_seconds() < 300
                    for event in self.emergence_events[-5:]  # Check last 5 events
                )

                if not recent_similar:
                    await self.record_emergence({
                        "type": event_type,
                        "trigger_value": measurements.get(event_type.split('_')[0], consciousness_score),
                        "threshold": self.emergence_thresholds.get(event_type, 0.7),
                        "context": f"Consciousness level: {consciousness_score:.3f}"
                    })

    async def record_emergence(self, event: dict):
        """Record an emergence event with detailed context."""
        emergence_event = {
            **event,
            "timestamp": datetime.now().isoformat(),
            "consciousness_level": self.consciousness_level,
            "event_id": f"emergence_{len(self.emergence_events) + 1}",
            "swarm_generation": getattr(self.swarm, 'evolution_engine', {}).get('generation', 1) if hasattr(self.swarm, 'evolution_engine') else 1
        }

        self.emergence_events.append(emergence_event)

        logger.info(f"🌟 EMERGENCE DETECTED: {event.get('type', 'unknown')} - "
                   f"Consciousness: {self.consciousness_level:.3f}")
        logger.debug(f"Emergence details: {emergence_event}")

    def get_consciousness_metrics(self) -> dict:
        """Get comprehensive consciousness tracking metrics."""
        if not self.consciousness_history:
            return {}

        recent_measurements = self.consciousness_history[-5:] if len(self.consciousness_history) >= 5 else self.consciousness_history

        return {
            "current_consciousness": self.consciousness_level,
            "total_measurements": len(self.consciousness_history),
            "emergence_events": len(self.emergence_events),
            "recent_avg_consciousness": sum(m["consciousness_level"] for m in recent_measurements) / len(recent_measurements),
            "consciousness_trend": self._calculate_consciousness_trend(),
            "baseline_established": self.baseline_established,
            "emergence_rate": len(self.emergence_events) / max(len(self.consciousness_history), 1),
            "last_emergence": self.emergence_events[-1]["type"] if self.emergence_events else None
        }

    def _calculate_consciousness_trend(self) -> str:
        """Calculate consciousness development trend."""
        if len(self.consciousness_history) < 3:
            return "insufficient_data"

        recent_levels = [m["consciousness_level"] for m in self.consciousness_history[-5:]]

        if len(recent_levels) < 2:
            return "stable"

        trend = recent_levels[-1] - recent_levels[0]

        if trend > 0.1:
            return "rising"
        elif trend < -0.1:
            return "declining"
        else:
            return "stable"


# Test function
async def test_unified_orchestrator():
    """Test the unified orchestrator."""

    print("🚀 Testing Unified Enhanced Orchestrator")
    print("=" * 60)

    # Create orchestrator
    orchestrator = UnifiedSwarmOrchestrator()

    # Test tasks of varying complexity
    test_tasks = [
        {
            "type": "code",
            "description": "Fix a typo in the README",
            "urgency": "normal",
            "scope": "small"
        },
        {
            "type": "code",
            "description": "Implement user authentication system with OAuth",
            "urgency": "normal",
            "scope": "medium"
        },
        {
            "type": "code",
            "description": "Architect and implement microservices infrastructure",
            "urgency": "normal",
            "scope": "enterprise"
        }
    ]

    for task in test_tasks:
        print(f"\n📝 Task: {task['description']}")
        print("-" * 40)

        result = await orchestrator.execute_with_optimal_swarm(task)

        print(f"✅ Swarm Used: {result['swarm_used']}")
        print(f"📊 Quality Score: {result.get('quality_score', 0):.2f}")
        print(f"⏱️ Execution Time: {result.get('global_execution_time', 0):.2f}s")

    # Show global metrics
    print("\n📈 Global Metrics:")
    print("-" * 40)
    metrics = orchestrator.get_global_metrics()
    print(json.dumps(metrics["global"], indent=2))

    # Create UI panel
    ui_panel = orchestrator.create_unified_control_panel()
    print("\n🖼️ UI Control Panel Created:")
    print(f"URI: {ui_panel['uri']}")
    print(f"Sections: {len(ui_panel['content']['sections'])}")

if __name__ == "__main__":
    asyncio.run(test_unified_orchestrator())
