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
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import logging

from app.swarms.improved_swarm import (
    ImprovedAgentSwarm,
    AdversarialDebateSystem,
    QualityGateSystem,
    StrategyArchive,
    SafetyBoundarySystem,
    DynamicRoleAssigner,
    ConsensusSystem,
    AdaptiveParameterManager,
    KnowledgeTransferSystem,
    MCPUIIntegration
)

logger = logging.getLogger(__name__)


class UnifiedSwarmOrchestrator:
    """
    Orchestrates all swarm types with unified improvements.
    Each swarm gets the 8 enhancement patterns while maintaining its unique characteristics.
    """
    
    def __init__(self):
        self.swarm_registry = {}
        self.global_strategy_archive = StrategyArchive("tmp/global_strategy_archive.json")
        self.global_safety_system = None
        self.global_metrics = {
            "total_executions": 0,
            "swarm_usage": {},
            "pattern_effectiveness": {},
            "cross_swarm_transfers": 0
        }
        
        # Initialize all swarm types
        self._initialize_swarms()
    
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
    
    def _load_unified_config(self) -> Dict:
        """Load unified configuration for all swarms."""
        config_path = Path("swarm_config.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
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
    
    def _create_enhanced_coding_team(self, config: Dict) -> Dict:
        """Create enhanced standard coding team."""
        
        agents = [
            "planner_grok4",
            "generator_deepseek",
            "generator_qwen",
            "critic_claude",
            "judge_gpt5"
        ]
        
        swarm = ImprovedAgentSwarm(agents, "swarm_config.json")
        
        # Customize for coding team
        swarm.config["optimization"] = "balanced"
        swarm.config["parallel_execution"] = True
        
        return {
            "swarm": swarm,
            "type": "coding_team",
            "description": "5-agent balanced team for general coding tasks",
            "ui_enabled": True,
            "mcp_servers": ["filesystem", "git", "supermemory"]
        }
    
    def _create_enhanced_coding_swarm(self, config: Dict) -> Dict:
        """Create enhanced advanced coding swarm."""
        
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
        
        swarm = ImprovedAgentSwarm(agents, "swarm_config.json")
        
        # Enable all patterns for comprehensive coverage
        swarm.config["use_all_patterns"] = True
        swarm.config["specialist_routing"] = True
        
        return {
            "swarm": swarm,
            "type": "coding_swarm",
            "description": "10+ agent swarm for complex projects",
            "ui_enabled": True,
            "mcp_servers": ["filesystem", "git", "supermemory", "enhanced_mcp"]
        }
    
    def _create_enhanced_fast_swarm(self, config: Dict) -> Dict:
        """Create enhanced fast coding swarm."""
        
        agents = [
            "fast_planner",
            "fast_generator",
            "fast_validator"
        ]
        
        swarm = ImprovedAgentSwarm(agents, "swarm_config.json")
        
        # Optimize for speed
        swarm.quality_gates.min_quality = 0.6  # Lower threshold for speed
        swarm.quality_gates.max_retries = 1  # Fewer retries
        swarm.debate_system = None  # Skip debate for speed
        
        return {
            "swarm": swarm,
            "type": "coding_swarm_fast",
            "description": "3-agent speed-optimized swarm",
            "ui_enabled": True,
            "mcp_servers": ["filesystem", "supermemory"]
        }
    
    def _create_enhanced_genesis_swarm(self, config: Dict) -> Dict:
        """Create enhanced GENESIS swarm with self-evolution."""
        
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
        
        # Add meta agents
        meta_agents = [
            "agent_spawner",
            "swarm_evolutionist",
            "consciousness_observer"
        ]
        
        all_agents = base_agents + commanders + scientists + meta_agents
        
        swarm = ImprovedAgentSwarm(all_agents, "swarm_config.json")
        
        # Enable advanced features
        swarm.config["enable_evolution"] = True
        swarm.config["dynamic_spawning"] = True
        swarm.config["consciousness_tracking"] = True
        swarm.config["emergence_detection"] = True
        
        # Add evolution-specific components
        swarm.evolution_engine = EvolutionEngine(swarm)
        swarm.consciousness_tracker = ConsciousnessTracker(swarm)
        
        return {
            "swarm": swarm,
            "type": "genesis_swarm",
            "description": "30+ agent self-evolving swarm",
            "ui_enabled": True,
            "mcp_servers": ["filesystem", "git", "supermemory", "enhanced_mcp", "graphrag"]
        }
    
    async def select_optimal_swarm(self, task: Dict) -> str:
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
    
    async def _analyze_task_complexity(self, task: Dict) -> float:
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
    
    async def execute_with_optimal_swarm(self, task: Dict) -> Dict:
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
        
        # Execute with selected swarm
        result = await swarm.solve_with_improvements(task)
        
        # Track metrics
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
            "safety_check": safety_result
        }
    
    def _update_global_metrics(self, swarm_type: str, result: Dict, execution_time: float):
        """Update global metrics."""
        self.global_metrics["total_executions"] += 1
        
        if swarm_type not in self.global_metrics["swarm_usage"]:
            self.global_metrics["swarm_usage"][swarm_type] = 0
        self.global_metrics["swarm_usage"][swarm_type] += 1
        
        # Track pattern effectiveness
        for pattern in ["adversarial_debate", "quality_gates", "strategy_archive"]:
            if pattern not in self.global_metrics["pattern_effectiveness"]:
                self.global_metrics["pattern_effectiveness"][pattern] = []
            
            # Simple effectiveness tracking
            self.global_metrics["pattern_effectiveness"][pattern].append(
                result.get("quality_score", 0)
            )
    
    async def _cross_swarm_transfer(self, source_swarm: str, task_type: str, result: Dict):
        """Transfer successful patterns between swarms."""
        
        # Transfer successful patterns to other swarms
        for target_swarm_name, target_info in self.swarm_registry.items():
            if target_swarm_name != source_swarm:
                target_swarm = target_info["swarm"]
                
                # Attempt transfer
                success = await target_swarm.transfer_system.attempt_transfer(
                    task_type,
                    task_type,  # Same domain for now
                    {
                        "roles": result.get("agent_roles", []),
                        "quality": result.get("quality_score", 0)
                    }
                )
                
                if success:
                    self.global_metrics["cross_swarm_transfers"] += 1
                    logger.info(f"Transferred pattern from {source_swarm} to {target_swarm_name}")
    
    def get_global_metrics(self) -> Dict:
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
            )
        }
    
    def create_unified_control_panel(self) -> Dict:
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
                            "patterns_archived": metrics["global_patterns_archived"]
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
    """Handles agent evolution for GENESIS swarm."""
    
    def __init__(self, swarm):
        self.swarm = swarm
        self.generation = 1
        self.fitness_history = []
        self.mutations = []
    
    async def evolve_agents(self, performance_data: Dict):
        """Evolve agents based on performance."""
        
        # Calculate fitness scores
        fitness_scores = self._calculate_fitness(performance_data)
        
        # Select top performers
        top_agents = self._select_top_performers(fitness_scores)
        
        # Apply mutations to underperformers
        for agent in self.swarm.agents:
            if agent not in top_agents:
                await self._mutate_agent(agent)
        
        self.generation += 1
        self.fitness_history.append(fitness_scores)
        
        logger.info(f"Evolution complete. Generation {self.generation}")
    
    def _calculate_fitness(self, performance_data):
        """Calculate fitness scores for agents."""
        # Simplified fitness calculation
        return {agent: 0.5 + (i * 0.1) for i, agent in enumerate(self.swarm.agents)}
    
    def _select_top_performers(self, fitness_scores):
        """Select top performing agents."""
        sorted_agents = sorted(fitness_scores.items(), key=lambda x: x[1], reverse=True)
        top_count = len(sorted_agents) // 3
        return [agent for agent, _ in sorted_agents[:top_count]]
    
    async def _mutate_agent(self, agent):
        """Apply mutations to an agent."""
        mutation = {
            "agent": str(agent),
            "type": "parameter_adjustment",
            "generation": self.generation,
            "timestamp": datetime.now().isoformat()
        }
        self.mutations.append(mutation)
        logger.debug(f"Mutated agent: {agent}")


class ConsciousnessTracker:
    """Tracks swarm consciousness for GENESIS swarm."""
    
    def __init__(self, swarm):
        self.swarm = swarm
        self.consciousness_level = 0.0
        self.emergence_events = []
    
    async def measure_consciousness(self) -> float:
        """Measure current consciousness level."""
        
        # Factors contributing to consciousness
        factors = {
            "agent_coordination": self._measure_coordination(),
            "pattern_recognition": self._measure_pattern_recognition(),
            "adaptive_behavior": self._measure_adaptation(),
            "emergence": self._detect_emergence()
        }
        
        # Calculate weighted consciousness level
        weights = {"agent_coordination": 0.3, "pattern_recognition": 0.3,
                  "adaptive_behavior": 0.2, "emergence": 0.2}
        
        self.consciousness_level = sum(
            factors[k] * weights[k] for k in factors
        )
        
        return self.consciousness_level
    
    def _measure_coordination(self):
        """Measure agent coordination level."""
        # Simplified measurement
        return 0.7
    
    def _measure_pattern_recognition(self):
        """Measure pattern recognition capability."""
        archive_size = len(self.swarm.strategy_archive.patterns.get("problem_types", {}))
        return min(archive_size / 10, 1.0)
    
    def _measure_adaptation(self):
        """Measure adaptive behavior."""
        if hasattr(self.swarm, "param_manager"):
            history = self.swarm.param_manager.performance_history
            if len(history) > 1:
                improvement = (history[-1] - history[0]) / len(history)
                return max(0, min(improvement * 10, 1.0))
        return 0.5
    
    def _detect_emergence(self):
        """Detect emergent behaviors."""
        # Simplified emergence detection
        if len(self.emergence_events) > 5:
            return 1.0
        return len(self.emergence_events) / 5
    
    def record_emergence(self, event: Dict):
        """Record an emergence event."""
        self.emergence_events.append({
            **event,
            "timestamp": datetime.now().isoformat(),
            "consciousness_level": self.consciousness_level
        })
        logger.info(f"Emergence detected: {event.get('type', 'unknown')}")


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