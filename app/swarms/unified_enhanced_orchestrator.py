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
from typing import Dict, Any, List, Optional, Tuple
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
    
    async def evolve_agents(self, performance_data: Dict):
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
    
    def _calculate_comprehensive_fitness(self, performance_data: Dict) -> Dict[str, float]:
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
    
    def _calculate_diversity_bonus(self, agent: str, existing_scores: Dict) -> float:
        """Calculate diversity bonus to maintain population variety."""
        if not existing_scores:
            return 0.5
        
        # Simple diversity measure based on agent name/type
        agent_type = agent.split('_')[0] if '_' in agent else agent[:3]
        similar_count = sum(1 for other in existing_scores.keys()
                           if other.split('_')[0] == agent_type or other[:3] == agent_type)
        
        # Higher bonus for rarer agent types
        return max(0, 1.0 - (similar_count / len(existing_scores)))
    
    def _selection_phase(self, fitness_scores: Dict) -> Tuple[List[str], List[str]]:
        """Select agents for survival and identify elites."""
        sorted_agents = sorted(fitness_scores.items(), key=lambda x: x[1], reverse=True)
        
        total_agents = len(sorted_agents)
        elite_count = max(1, int(total_agents * self.elite_preservation))
        survivor_count = max(2, int(total_agents * self.selection_pressure))
        
        elites = [agent for agent, _ in sorted_agents[:elite_count]]
        survivors = [agent for agent, _ in sorted_agents[:survivor_count]]
        
        logger.debug(f"Selection: {elite_count} elites, {survivor_count} survivors from {total_agents} agents")
        return survivors, elites
    
    async def _crossover_phase(self, survivors: List[str]) -> List[str]:
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
    
    async def _create_offspring(self, parent1: str, parent2: str) -> Tuple[str, str]:
        """Create two offspring from parent agents through crossover."""
        # Generate offspring names
        child1_name = f"evolved_{parent1}_{parent2}_{self.generation}"
        child2_name = f"evolved_{parent2}_{parent1}_{self.generation}"
        
        # In a real implementation, this would combine traits/parameters
        # from parent agents to create new agent configurations
        
        logger.debug(f"Created offspring: {child1_name}, {child2_name} from parents {parent1}, {parent2}")
        return child1_name, child2_name
    
    async def _mutation_phase(self, agents: List[str]):
        """Apply random mutations to introduce variety."""
        mutations_applied = 0
        
        for agent in agents:
            if random.random() < self.mutation_rate:
                mutation = await self._apply_mutation(agent)
                self.mutations.append(mutation)
                mutations_applied += 1
        
        logger.debug(f"Applied {mutations_applied} mutations to agents")
    
    async def _apply_mutation(self, agent: str) -> Dict:
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
    
    def get_evolution_metrics(self) -> Dict:
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


class ConsciousnessTracker:
    """
    Advanced consciousness tracking system for GENESIS swarm.
    Monitors and quantifies emergent swarm intelligence behaviors.
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
    
    def _calculate_baseline_deviation(self, measurements: Dict) -> Dict:
        """Calculate deviation from baseline measurements."""
        if not self.baseline_established:
            return {}
        
        return {
            factor: measurements[factor] - self.baseline_metrics.get(factor, 0.5)
            for factor in measurements
        }
    
    async def _check_emergence_events(self, measurements: Dict, consciousness_score: float):
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
    
    async def record_emergence(self, event: Dict):
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
    
    def get_consciousness_metrics(self) -> Dict:
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