
"""
Experimental Evolution Engine for Swarm Learning and Adaptation - ADR-002 Implementation
An experimental genetic algorithm system for autonomous swarm evolution with safety boundaries.

⚠️ EXPERIMENTAL FEATURE ⚠️
This is an experimental system for swarm evolution. It must be explicitly enabled and comes
with safety controls, but should be used with caution in production environments.

Key Features:
- Experimental genetic algorithm approach with safety controls
- Optional activation via configuration (disabled by default)
- Pattern-based evolution with breakthrough identification  
- Memory integration for historical learning
- Fallback mechanisms for poor performance
- Multi-population evolution for different swarm types
- Real-time adaptation capabilities (experimental)
"""

import asyncio
import json
import random
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import numpy as np
from copy import deepcopy

from app.swarms.memory_integration import SwarmMemoryClient, SwarmMemoryEventType
from app.memory.supermemory_mcp import MemoryType

logger = logging.getLogger(__name__)


class ExperimentalMode(Enum):
    """Experimental evolution modes for different levels of exploration."""
    DISABLED = "disabled"           # No evolution (safe default)
    OBSERVE_ONLY = "observe_only"   # Monitor patterns but don't evolve
    CAUTIOUS = "cautious"          # Very safe evolution with tight bounds
    EXPERIMENTAL = "experimental"   # Balanced experimental evolution
    AGGRESSIVE = "aggressive"      # More exploratory (requires explicit enable)


@dataclass
class ExperimentalSafetyBounds:
    """Safety boundaries for experimental evolution parameters."""
    min_mutation_rate: float = 0.01
    max_mutation_rate: float = 0.15
    min_selection_pressure: float = 0.1
    max_selection_pressure: float = 0.5
    min_crossover_rate: float = 0.3
    max_crossover_rate: float = 0.8
    max_population_changes: int = 3  # Max agents to change per generation
    performance_degradation_threshold: float = 0.1  # Rollback threshold


@dataclass 
class ExperimentalEvolutionConfig:
    """Configuration for the experimental evolution engine."""
    # Core experimental settings
    mode: ExperimentalMode = ExperimentalMode.DISABLED  # Disabled by default
    enabled: bool = False  # Must be explicitly enabled
    experimental_features_acknowledged: bool = False  # Must acknowledge experimental nature
    
    # Genetic algorithm parameters (conservative defaults for safety)
    mutation_rate: float = 0.1          # 10% mutation rate (conservative)
    selection_pressure: float = 0.3     # Top 30% survive
    elite_preservation: float = 0.1     # Top 10% unchanged
    crossover_rate: float = 0.7         # 70% crossover rate
    
    # Safety controls
    safety_bounds: ExperimentalSafetyBounds = field(default_factory=ExperimentalSafetyBounds)
    enable_rollback: bool = True
    rollback_generations: int = 3
    performance_monitoring_window: int = 5
    min_confidence_threshold: float = 0.7
    
    # Experimental pattern recognition
    pattern_detection_enabled: bool = True
    breakthrough_threshold: float = 0.85
    emergence_detection_enabled: bool = True
    experimental_pattern_analysis: bool = False  # Advanced pattern analysis
    
    # Memory integration (experimental)
    memory_enhanced: bool = True
    historical_data_window: int = 100
    experience_replay_enabled: bool = True
    experimental_memory_features: bool = False  # Advanced memory features
    
    # Multi-population experiments
    separate_populations_per_swarm_type: bool = True
    population_migration_rate: float = 0.05
    experimental_cross_population_breeding: bool = False
    
    # Real-time evolution (highly experimental)
    real_time_evolution: bool = False  # Disabled by default - experimental
    adaptation_frequency: timedelta = field(default_factory=lambda: timedelta(hours=24))
    experimental_continuous_adaptation: bool = False
    
    # Validation and testing
    validation_enabled: bool = True
    dry_run_mode: bool = True  # Default to dry run for safety
    experimental_validation_disabled: bool = False  # Allow disabling validation (risky)
    
    def validate(self) -> List[str]:
        """Validate configuration and return any issues."""
        issues = []
        
        # Check experimental acknowledgment
        if self.enabled and not self.experimental_features_acknowledged:
            issues.append("Must acknowledge experimental nature to enable evolution")
            
        # Check bounds
        bounds = self.safety_bounds
        if not (bounds.min_mutation_rate <= self.mutation_rate <= bounds.max_mutation_rate):
            issues.append(f"Mutation rate {self.mutation_rate} outside experimental safe bounds")
            
        if not (bounds.min_selection_pressure <= self.selection_pressure <= bounds.max_selection_pressure):
            issues.append(f"Selection pressure {self.selection_pressure} outside experimental safe bounds")
            
        if not (bounds.min_crossover_rate <= self.crossover_rate <= bounds.max_crossover_rate):
            issues.append(f"Crossover rate {self.crossover_rate} outside experimental safe bounds")
            
        # Logical checks
        if self.elite_preservation > self.selection_pressure:
            issues.append("Elite preservation cannot exceed selection pressure")
            
        if self.mode == ExperimentalMode.AGGRESSIVE and not self.experimental_features_acknowledged:
            issues.append("Aggressive experimental mode requires explicit acknowledgment")
            
        # Experimental feature warnings
        if self.experimental_pattern_analysis and self.mode != ExperimentalMode.AGGRESSIVE:
            issues.append("Advanced experimental pattern analysis requires aggressive mode")
            
        if self.experimental_cross_population_breeding:
            issues.append("Cross-population breeding is highly experimental - use with caution")
            
        if self.experimental_continuous_adaptation:
            issues.append("Continuous adaptation is highly experimental - monitor closely")
            
        return issues


@dataclass
class SwarmChromosome:
    """Chromosome representation for experimental swarm configuration evolution."""
    chromosome_id: str
    swarm_type: str
    generation: int
    experimental_variant: bool = False  # Flag for experimental mutations
    
    # Agent configuration genes
    agent_roles: List[str]
    agent_parameters: Dict[str, Dict[str, float]]  # agent_name -> param -> value
    
    # Swarm behavior genes  
    coordination_style: str  # "hierarchical", "peer_to_peer", "hybrid", "experimental"
    communication_pattern: str  # "broadcast", "targeted", "adaptive", "experimental"
    consensus_mechanism: str  # "majority", "weighted", "expert", "experimental"
    
    # Performance genes
    quality_threshold: float
    speed_preference: float  # 0.0 = quality focused, 1.0 = speed focused
    risk_tolerance: float
    
    # Adaptation genes
    learning_rate: float
    memory_utilization: float
    pattern_recognition_sensitivity: float
    
    # Experimental genes (only active in experimental modes)
    experimental_creativity: float = 0.5
    experimental_exploration: float = 0.3
    experimental_cooperation: float = 0.7
    
    # Metadata
    fitness_score: float = 0.0
    parent_chromosomes: List[str] = field(default_factory=list)
    creation_timestamp: datetime = field(default_factory=datetime.now)
    performance_history: List[Dict[str, float]] = field(default_factory=list)
    experimental_mutations_count: int = 0
    
    def mutate(self, mutation_rate: float, safety_bounds: ExperimentalSafetyBounds, 
               experimental_mode: bool = False) -> 'SwarmChromosome':
        """Apply mutations to chromosome with experimental options."""
        mutated = deepcopy(self)
        mutated.chromosome_id = f"{self.chromosome_id}_mut_{random.randint(1000, 9999)}"
        mutated.parent_chromosomes = [self.chromosome_id]
        mutated.generation = self.generation + 1
        mutated.experimental_variant = experimental_mode
        
        # Standard mutations
        if random.random() < mutation_rate:
            # Safe parameter mutations
            for agent, params in mutated.agent_parameters.items():
                for param_name, value in params.items():
                    if random.random() < mutation_rate / len(params):
                        # Conservative mutation: ±10% of current value
                        mutation_factor = random.uniform(0.9, 1.1)
                        if experimental_mode:
                            # Experimental: slightly larger mutations
                            mutation_factor = random.uniform(0.8, 1.2)
                        new_value = max(0.0, min(1.0, value * mutation_factor))
                        mutated.agent_parameters[agent][param_name] = new_value
                        mutated.experimental_mutations_count += 1
            
            # Mutate performance preferences
            if random.random() < mutation_rate:
                delta = random.uniform(-0.1, 0.1)
                if experimental_mode:
                    delta = random.uniform(-0.15, 0.15)  # Larger experimental changes
                mutated.quality_threshold = max(0.5, min(1.0, self.quality_threshold + delta))
                    
            if random.random() < mutation_rate:
                delta = random.uniform(-0.1, 0.1)
                if experimental_mode:
                    delta = random.uniform(-0.15, 0.15)
                mutated.speed_preference = max(0.0, min(1.0, self.speed_preference + delta))
                    
            if random.random() < mutation_rate:
                delta = random.uniform(-0.05, 0.05)
                if experimental_mode:
                    delta = random.uniform(-0.1, 0.1)
                mutated.risk_tolerance = max(0.0, min(0.8, self.risk_tolerance + delta))  # Still cap at 0.8
            
            # Experimental gene mutations (only in experimental mode)
            if experimental_mode:
                if random.random() < mutation_rate:
                    mutated.experimental_creativity = max(0.0, min(1.0, 
                        self.experimental_creativity + random.uniform(-0.2, 0.2)))
                if random.random() < mutation_rate:
                    mutated.experimental_exploration = max(0.0, min(1.0,
                        self.experimental_exploration + random.uniform(-0.15, 0.15)))
                if random.random() < mutation_rate:
                    mutated.experimental_cooperation = max(0.0, min(1.0,
                        self.experimental_cooperation + random.uniform(-0.1, 0.1)))
        
        return mutated
    
    @staticmethod
    def crossover(parent1: 'SwarmChromosome', parent2: 'SwarmChromosome', 
                  experimental_mode: bool = False) -> Tuple['SwarmChromosome', 'SwarmChromosome']:
        """Create two offspring through crossover with experimental options."""
        child1 = deepcopy(parent1)
        child2 = deepcopy(parent2)
        
        # Generate new IDs
        child1.chromosome_id = f"cross_{parent1.chromosome_id}_{parent2.chromosome_id}_{random.randint(1000, 9999)}_1"
        child2.chromosome_id = f"cross_{parent1.chromosome_id}_{parent2.chromosome_id}_{random.randint(1000, 9999)}_2"
        
        # Set parents and experimental flag
        child1.parent_chromosomes = [parent1.chromosome_id, parent2.chromosome_id]
        child2.parent_chromosomes = [parent1.chromosome_id, parent2.chromosome_id]
        child1.experimental_variant = experimental_mode or parent1.experimental_variant or parent2.experimental_variant
        child2.experimental_variant = experimental_mode or parent1.experimental_variant or parent2.experimental_variant
        
        # Increment generation
        child1.generation = max(parent1.generation, parent2.generation) + 1
        child2.generation = max(parent1.generation, parent2.generation) + 1
        
        # Parameter crossover
        for agent in child1.agent_parameters:
            if agent in parent2.agent_parameters:
                for param in child1.agent_parameters[agent]:
                    if param in parent2.agent_parameters[agent]:
                        # Weighted average with randomization
                        weight = random.uniform(0.3, 0.7)
                        if experimental_mode:
                            weight = random.uniform(0.1, 0.9)  # More experimental blending
                            
                        child1.agent_parameters[agent][param] = (
                            weight * parent1.agent_parameters[agent][param] + 
                            (1 - weight) * parent2.agent_parameters[agent][param]
                        )
                        child2.agent_parameters[agent][param] = (
                            (1 - weight) * parent1.agent_parameters[agent][param] + 
                            weight * parent2.agent_parameters[agent][param]
                        )
        
        # Crossover performance and experimental genes
        crossover_genes = ['quality_threshold', 'speed_preference', 'risk_tolerance']
        if experimental_mode:
            crossover_genes.extend(['experimental_creativity', 'experimental_exploration', 'experimental_cooperation'])
            
        for gene in crossover_genes:
            if hasattr(parent1, gene) and hasattr(parent2, gene):
                if random.random() < 0.5:
                    setattr(child1, gene, getattr(parent2, gene))
                    setattr(child2, gene, getattr(parent1, gene))
            
        return child1, child2


@dataclass
class ExperimentalFitnessEvaluation:
    """Multi-objective fitness evaluation with experimental metrics."""
    chromosome_id: str
    overall_fitness: float
    
    # Standard performance metrics
    quality_score: float
    speed_score: float
    efficiency_score: float
    reliability_score: float
    
    # Behavioral metrics
    collaboration_score: float
    adaptability_score: float
    innovation_score: float
    
    # Safety metrics
    stability_score: float
    risk_score: float
    
    # Memory integration metrics
    memory_utilization_score: float
    pattern_recognition_score: float
    
    # Experimental metrics (only calculated in experimental modes)
    experimental_creativity_score: float = 0.0
    experimental_exploration_score: float = 0.0
    experimental_breakthrough_potential: float = 0.0
    
    # Weights used in calculation
    weights: Dict[str, float] = field(default_factory=lambda: {
        'quality': 0.25, 'speed': 0.15, 'efficiency': 0.15, 'reliability': 0.20,
        'collaboration': 0.10, 'adaptability': 0.05, 'innovation': 0.05,
        'stability': 0.03, 'memory_utilization': 0.02
    })
    
    experimental_weights: Dict[str, float] = field(default_factory=lambda: {
        'experimental_creativity': 0.03, 'experimental_exploration': 0.02, 
        'experimental_breakthrough': 0.01
    })
    
    evaluation_timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    experimental_evaluation: bool = False


class ExperimentalEvolutionEngine:
    """
    Experimental genetic algorithm engine for swarm evolution (ADR-002).
    
    ⚠️ EXPERIMENTAL SYSTEM ⚠️
    
    This system implements experimental evolution capabilities with safety controls:
    - Experimental parameter bounds with rollback mechanisms
    - Performance monitoring with automatic fallbacks
    - Pattern recognition and breakthrough detection (experimental)
    - Memory integration for historical learning (experimental)
    - Multi-population support for different swarm types (experimental)
    
    Use with caution in production environments!
    """
    
    def __init__(self, config: Optional[ExperimentalEvolutionConfig] = None, 
                 memory_client: Optional[SwarmMemoryClient] = None):
        """Initialize the experimental evolution engine."""
        self.config = config or ExperimentalEvolutionConfig()
        self.memory_client = memory_client
        
        # Validate configuration
        config_issues = self.config.validate()
        if config_issues:
            logger.error(f"Experimental evolution engine configuration issues: {config_issues}")
            if not self.config.dry_run_mode:
                raise ValueError(f"Invalid experimental evolution configuration: {'; '.join(config_issues)}")
        
        # Population management
        self.populations: Dict[str, List[SwarmChromosome]] = {}  # swarm_type -> chromosomes
        self.generation_counter: Dict[str, int] = {}
        self.fitness_history: Dict[str, List[ExperimentalFitnessEvaluation]] = {}
        
        # Performance tracking
        self.performance_baseline: Dict[str, float] = {}
        self.performance_history: Dict[str, List[Dict[str, float]]] = {}
        self.rollback_snapshots: Dict[str, List[SwarmChromosome]] = {}
        
        # Experimental pattern recognition
        self.successful_patterns: Dict[str, List[Dict[str, Any]]] = {}
        self.breakthrough_events: List[Dict[str, Any]] = []
        self.emergence_detections: List[Dict[str, Any]] = []
        self.experimental_discoveries: List[Dict[str, Any]] = []
        
        # Safety controls
        self.evolution_active: Dict[str, bool] = {}
        self.last_evolution_time: Dict[str, datetime] = {}
        self.safety_violations: List[Dict[str, Any]] = []
        self.experimental_warnings: List[Dict[str, Any]] = []
        
        # Experimental statistics
        self.evolution_stats = {
            'total_generations': 0,
            'successful_evolutions': 0,
            'rollbacks': 0,
            'breakthroughs': 0,
            'patterns_discovered': 0,
            'experimental_mutations': 0,
            'experimental_discoveries': 0,
            'safety_interventions': 0
        }
        
        logger.info(f"🧪 Experimental evolution engine initialized - Mode: {self.config.mode.value}")
        if not self.config.enabled:
            logger.info("⚠️ Experimental evolution engine is DISABLED - enable in config to activate")
        elif not self.config.experimental_features_acknowledged:
            logger.warning("⚠️ Experimental features not acknowledged - engine will not activate")
        else:
            logger.warning("🧪 EXPERIMENTAL EVOLUTION ACTIVE - Monitor closely for unexpected behavior")
    
    async def initialize_experimental_population(self, swarm_type: str, base_chromosome: SwarmChromosome,
                                               population_size: int = 5) -> bool:
        """Initialize experimental population for a swarm type."""
        if not self._can_experiment():
            logger.info(f"Experimental evolution disabled - skipping population initialization for {swarm_type}")
            return False
            
        if self.config.mode == ExperimentalMode.DISABLED:
            logger.info(f"Experimental evolution mode disabled - skipping {swarm_type}")
            return False
        
        try:
            logger.info(f"🧪 Initializing experimental population for {swarm_type}")
            
            # Start with base chromosome
            population = [base_chromosome]
            
            # Generate diverse variants with experimental features
            experimental_mode = self.config.mode in [ExperimentalMode.EXPERIMENTAL, ExperimentalMode.AGGRESSIVE]
            
            for i in range(population_size - 1):
                variant = base_chromosome.mutate(
                    mutation_rate=self.config.mutation_rate * 0.5,  # Reduced for initialization
                    safety_bounds=self.config.safety_bounds,
                    experimental_mode=experimental_mode
                )
                variant.chromosome_id = f"{swarm_type}_exp_init_{i+1}_{random.randint(1000, 9999)}"
                population.append(variant)
            
            self.populations[swarm_type] = population
            self.generation_counter[swarm_type] = 1
            self.fitness_history[swarm_type] = []
            self.performance_history[swarm_type] = []
            self.evolution_active[swarm_type] = True
            
            # Store memory if available
            if self.memory_client:
                await self.memory_client.log_swarm_event(
                    SwarmMemoryEventType.EVOLUTION_EVENT,
                    {
                        'event_type': 'experimental_population_initialized',
                        'swarm_type': swarm_type,
                        'population_size': len(population),
                        'experimental_mode': self.config.mode.value,
                        'experimental_features': experimental_mode
                    }
                )
            
            logger.info(f"🧪 Initialized experimental population of {len(population)} chromosomes for {swarm_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize experimental population for {swarm_type}: {e}")
            return False
    
    def _can_experiment(self) -> bool:
        """Check if experimental evolution is allowed."""
        if not self.config.enabled:
            return False
            
        if not self.config.experimental_features_acknowledged:
            logger.warning("🧪 Experimental features not acknowledged - evolution disabled")
            return False
            
        if self.config.mode == ExperimentalMode.DISABLED:
            return False
        
        return True
    
    async def experimental_evolve_population(self, swarm_type: str, performance_data: Dict[str, Any]) -> Optional[SwarmChromosome]:
        """
        Perform experimental evolution for a swarm population.
        
        ⚠️ EXPERIMENTAL OPERATION ⚠️
        This method implements experimental genetic algorithms that may produce unexpected results.
        
        Returns the best chromosome if evolution was successful, None otherwise.
        """
        if not self._can_evolve_experimental(swarm_type):
            return None
        
        if self.config.mode == ExperimentalMode.OBSERVE_ONLY:
            logger.info(f"🧪 Experimental evolution in observe-only mode for {swarm_type}")
            return await self._observe_experimental_performance(swarm_type, performance_data)
        
        try:
            logger.info(f"🧪 Starting experimental evolution for {swarm_type} generation {self.generation_counter.get(swarm_type, 1)}")
            
            population = self.populations.get(swarm_type, [])
            if not population:
                logger.error(f"No experimental population found for {swarm_type}")
                return None
            
            # Experimental evolution pipeline
            experimental_mode = self.config.mode in [ExperimentalMode.EXPERIMENTAL, ExperimentalMode.AGGRESSIVE]
            
            # Step 1: Experimental fitness evaluation
            fitness_evaluations = await self._evaluate_experimental_fitness(swarm_type, population, performance_data)
            
            # Step 2: Safety checks with experimental tolerance
            if await self._check_experimental_safety(swarm_type, fitness_evaluations):
                logger.warning(f"🧪 Experimental safety check triggered for {swarm_type}")
                return await self._perform_experimental_rollback(swarm_type)
            
            # Step 3: Experimental selection
            survivors, elites = self._experimental_selection_phase(population, fitness_evaluations)
            
            # Step 4: Experimental pattern recognition
            await self._detect_experimental_patterns(swarm_type, survivors, fitness_evaluations)
            
            # Step 5: Experimental crossover
            offspring = await self._experimental_crossover_phase(survivors, experimental_mode)
            
            # Step 6: Experimental mutation
            await self._experimental_mutation_phase(offspring + survivors, experimental_mode)
            
            # Step 7: Create experimental population
            new_population = elites + survivors + offspring
            
            # Step 8: Experimental validation
            if not await self._validate_experimental_population(swarm_type, new_population):
                logger.warning(f"🧪 Experimental population failed validation for {swarm_type}")
                return None
            
            # Step 9: Update population
            self.populations[swarm_type] = new_population[:len(population)]  # Maintain size
            self.generation_counter[swarm_type] += 1
            
            # Step 10: Create experimental snapshot
            self._create_experimental_snapshot(swarm_type, population)
            
            # Step 11: Store experimental results
            if self.memory_client:
                await self._store_experimental_results(swarm_type, fitness_evaluations, new_population)
            
            # Return best experimental chromosome
            best_fitness = max(fitness_evaluations, key=lambda f: f.overall_fitness)
            best_chromosome = next(c for c in new_population if c.chromosome_id == best_fitness.chromosome_id)
            
            self.evolution_stats['successful_evolutions'] += 1
            self.evolution_stats['total_generations'] += 1
            if experimental_mode:
                self.evolution_stats['experimental_mutations'] += sum(c.experimental_mutations_count for c in new_population)
            
            logger.info(f"🧪 Experimental evolution completed for {swarm_type} - Best fitness: {best_fitness.overall_fitness:.3f}")
            return best_chromosome
            
        except Exception as e:
            logger.error(f"🧪 Experimental evolution failed for {swarm_type}: {e}")
            self.experimental_warnings.append({
                'timestamp': datetime.now().isoformat(),
                'swarm_type': swarm_type,
                'error': str(e),
                'type': 'experimental_evolution_failure'
            })
            return None
    
    def _can_evolve_experimental(self, swarm_type: str) -> bool:
        """Check if experimental evolution is allowed for swarm type."""
        if not self._can_experiment():
            return False
        
        if not self.evolution_active.get(swarm_type, False):
            return False
        
        # Check time-based restrictions
        last_evolution = self.last_evolution_time.get(swarm_type)
        if last_evolution and datetime.now() - last_evolution < self.config.adaptation_frequency:
            return False
        
        return True
    
    async def _observe_experimental_performance(self, swarm_type: str, performance_data: Dict[str, Any]) -> Optional[SwarmChromosome]:
        """Observe and record experimental performance without evolving."""
        population = self.populations.get(swarm_type, [])
        if population:
            # Record experimental observations
            self.performance_history[swarm_type] = self.performance_history.get(swarm_type, [])
            self.performance_history[swarm_type].append({
                'timestamp': datetime.now().isoformat(),
                'performance_data': performance_data,
                'mode': 'experimental_observe_only',
                'experimental_features_active': any(c.experimental_variant for c in population)
            })
            return population[0]  # Return current best
        return None
    
    async def _evaluate_experimental_fitness(self, swarm_type: str, population: List[SwarmChromosome], 
                                           performance_data: Dict[str, Any]) -> List[ExperimentalFitnessEvaluation]:
        """Evaluate fitness with experimental metrics."""
        evaluations = []
        experimental_mode = self.config.mode in [ExperimentalMode.EXPERIMENTAL, ExperimentalMode.AGGRESSIVE]
        
        for chromosome in population:
            fitness = await self._evaluate_experimental_chromosome_fitness(chromosome, performance_data, experimental_mode)
            evaluations.append(fitness)
            
            # Update chromosome fitness
            chromosome.fitness_score = fitness.overall_fitness
            
            # Record performance history
            chromosome.performance_history.append({
                'timestamp': datetime.now().isoformat(),
                'fitness': fitness.overall_fitness,
                'performance_data': performance_data,
                'experimental_evaluation': experimental_mode
            })
        
        # Store in history
        self.fitness_history[swarm_type] = self.fitness_history.get(swarm_type, [])
        self.fitness_history[swarm_type].extend(evaluations)
        
        return evaluations
    
    async def _evaluate_experimental_chromosome_fitness(self, chromosome: SwarmChromosome, 
                                                      performance_data: Dict[str, Any],
                                                      experimental_mode: bool) -> ExperimentalFitnessEvaluation:
        """Evaluate fitness with experimental features."""
        # Standard metrics
        quality = performance_data.get('quality_score', 0.5)
        speed = performance_data.get('speed_score', 0.5)  
        efficiency = performance_data.get('efficiency_score', 0.5)
        reliability = performance_data.get('reliability_score', 0.5)
        
        # Behavioral scores
        collaboration = min(1.0, chromosome.agent_parameters.get('collaboration', {}).get('coordination', 0.5) * 1.2)
        adaptability = chromosome.learning_rate * 0.8 + chromosome.memory_utilization * 0.2
        innovation = chromosome.risk_tolerance * 0.6 + chromosome.pattern_recognition_sensitivity * 0.4
        
        # Safety metrics
        stability = 1.0 - chromosome.risk_tolerance
        risk_score = chromosome.risk_tolerance
        
        # Memory metrics
        memory_utilization = chromosome.memory_utilization
        pattern_recognition = chromosome.pattern_recognition_sensitivity
        
        # Experimental metrics (only in experimental mode)
        experimental_creativity = 0.0
        experimental_exploration = 0.0
        experimental_breakthrough = 0.0
        
        if experimental_mode and chromosome.experimental_variant:
            experimental_creativity = chromosome.experimental_creativity * 0.8 + innovation * 0.2
            experimental_exploration = chromosome.experimental_exploration * 0.7 + adaptability * 0.3
            # Breakthrough potential based on novelty and risk
            experimental_breakthrough = (experimental_creativity + experimental_exploration + chromosome.risk_tolerance) / 3.0
        
        # Create evaluation
        evaluation = ExperimentalFitnessEvaluation(
            chromosome_id=chromosome.chromosome_id,
            quality_score=quality,
            speed_score=speed,
            efficiency_score=efficiency,
            reliability_score=reliability,
            collaboration_score=collaboration,
            adaptability_score=adaptability,
            innovation_score=innovation,
            stability_score=stability,
            risk_score=risk_score,
            memory_utilization_score=memory_utilization,
            pattern_recognition_score=pattern_recognition,
            experimental_creativity_score=experimental_creativity,
            experimental_exploration_score=experimental_exploration,
            experimental_breakthrough_potential=experimental_breakthrough,
            experimental_evaluation=experimental_mode,
            overall_fitness=0.0  # Will be calculated below
        )
        
        # Calculate weighted overall fitness
        weights = evaluation.weights
        exp_weights = evaluation.experimental_weights
        
        overall = (
            quality * weights['quality'] +
            speed * weights['speed'] + 
            efficiency * weights['efficiency'] +
            reliability * weights['reliability'] +
            collaboration * weights['collaboration'] +
            adaptability * weights['adaptability'] +
            innovation * weights['innovation'] +
            stability * weights['stability'] +
            memory_utilization * weights['memory_utilization']
        )
        
        # Add experimental components if active
        if experimental_mode:
            overall += (
                experimental_creativity * exp_weights['experimental_creativity'] +
                experimental_exploration * exp_weights['experimental_exploration'] +
                experimental_breakthrough * exp_weights['experimental_breakthrough']
            )
        
        evaluation.overall_fitness = max(0.0, min(1.0, overall))
        
        return evaluation
    
    def get_experimental_status(self, swarm_type: Optional[str] = None) -> Dict[str, Any]:
        """Get current experimental evolution status and statistics."""
        if swarm_type:
            population = self.populations.get(swarm_type, [])
            experimental_variants = sum(1 for c in population if c.experimental_variant)
            
            return {
                'swarm_type': swarm_type,
                'experimental_enabled': self.config.enabled,
                'experimental_mode': self.config.mode.value,
                'experimental_acknowledged': self.config.experimental_features_acknowledged,
                'evolution_active': self.evolution_active.get(swarm_type, False),
                'generation': self.generation_counter.get(swarm_type, 0),
                'population_size': len(population),
                'experimental_variants': experimental_variants,
                'patterns_discovered': len(self.successful_patterns.get(swarm_type, [])),
                'breakthrough_events': len([b for b in self.breakthrough_events if b['swarm_type'] == swarm_type]),
                'experimental_discoveries': len([d for d in self.experimental_discoveries if d.get('swarm_type') == swarm_type]),
                'last_evolution': self.last_evolution_time.get(swarm_type, 'never'),
                'experimental_warnings': len([w for w in self.experimental_warnings if w.get('swarm_type') == swarm_type])
            }
        else:
            # Global experimental status
            return {
                'global_experimental_status': {
                    'enabled': self.config.enabled,
                    'mode': self.config.mode.value,
                    'experimental_acknowledged': self.config.experimental_features_acknowledged,
                    'dry_run_mode': self.config.dry_run_mode,
                    'total_swarm_types': len(self.populations),
                    'active_populations': len([s for s in self.evolution_active.values() if s]),
                    'config_validation': len(self.config.validate()) == 0
                },
                'experimental_statistics': self.evolution_stats,
                'swarm_types': list(self.populations.keys()),
                'experimental_warnings': len(self.experimental_warnings),
                'safety_violations': len(self.safety_violations),
                'breakthrough_events': len(self.breakthrough_events),
                'experimental_discoveries': len(self.experimental_discoveries)
            }
    
    # Additional experimental methods would continue here...
    # For brevity, I'll add key methods like safety checks, pattern detection, etc.
    
    async def _check_experimental_safety(self, swarm_type: str, evaluations: List[ExperimentalFitnessEvaluation]) -> bool:
        """Check experimental safety with higher tolerance for experimentation."""
        if not self.config.enable_rollback:
            return False
            
        # Get baseline performance
        baseline = self.performance_baseline.get(swarm_type)
        if baseline is None:
            # Establish baseline
            avg_fitness = sum(e.overall_fitness for e in evaluations) / len(evaluations)
            self.performance_baseline[swarm_type] = avg_fitness
            return False
        
        # Calculate current average fitness
        current_avg = sum(e.overall_fitness for e in evaluations) / len(evaluations)
        
        # Experimental mode allows for more risk
        threshold = self.config.safety_bounds.performance_degradation_threshold
        if self.config.mode == ExperimentalMode.AGGRESSIVE:
            threshold *= 2.0  # More tolerant in aggressive experimental mode
        
        degradation = baseline - current_avg
        
        if degradation > threshold:
            logger.warning(f"🧪 Experimental performance degradation detected for {swarm_type}: "
                         f"{baseline:.3f} -> {current_avg:.3f} (degradation: {degradation:.3f})")
            self.evolution_stats['safety_interventions'] += 1
            return True
            
        # Update baseline if performance improved
        if current_avg > baseline:
            self.performance_baseline[swarm_type] = current_avg
            
        return False
    
    async def _perform_experimental_rollback(self, swarm_type: str) -> Optional[SwarmChromosome]:
        """Perform experimental rollback to previous generation."""
        snapshots = self.rollback_snapshots.get(swarm_type, [])
        if not snapshots:
            logger.error(f"No experimental rollback snapshots available for {swarm_type}")
            return None
        
        # Restore previous population
        previous_population = snapshots[-1]  # Most recent snapshot
        self.populations[swarm_type] = previous_population
        
        # Record rollback
        self.evolution_stats['rollbacks'] += 1
        self.experimental_warnings.append({
            'timestamp': datetime.now().isoformat(),
            'swarm_type': swarm_type,
            'type': 'experimental_rollback',
            'action': 'restored_previous_generation',
            'experimental_mode': self.config.mode.value
        })
        
        # Store in memory if available
        if self.memory_client:
            await self.memory_client.log_swarm_event(
                SwarmMemoryEventType.EVOLUTION_EVENT,
                {
                    'event_type': 'experimental_rollback_performed',
                    'swarm_type': swarm_type,
                    'reason': 'experimental_performance_degradation',
                    'mode': self.config.mode.value
                }
            )
        
        logger.info(f"🧪 Experimental rollback performed for {swarm_type}")
        return previous_population[0] if previous_population else None
    
    def _experimental_selection_phase(self, population: List[SwarmChromosome], 
                                    fitness_evaluations: List[ExperimentalFitnessEvaluation]) -> Tuple[List[SwarmChromosome], List[SwarmChromosome]]:
        """Experimental selection phase with diversity preservation."""
        # Sort by fitness
        sorted_evaluations = sorted(fitness_evaluations, key=lambda e: e.overall_fitness, reverse=True)
        sorted_population = [next(c for c in population if c.chromosome_id == e.chromosome_id) 
                           for e in sorted_evaluations]
        
        population_size = len(sorted_population)
        
        # Experimental selection - preserve diversity
        elite_count = max(1, int(population_size * self.config.elite_preservation))
        survivor_count = max(2, int(population_size * self.config.selection_pressure))
        
        # In experimental mode, also preserve some low-performing but diverse variants
        if self.config.mode == ExperimentalMode.AGGRESSIVE:
            # Add some random selection for diversity
            diverse_candidates = sorted_population[survivor_count:]
            if diverse_candidates:
                random_selections = random.sample(diverse_candidates, min(1, len(diverse_candidates)))
                sorted_population = sorted_population[:survivor_count] + random_selections
                survivor_count += len(random_selections)
        
        elites = sorted_population[:elite_count]
        survivors = sorted_population[:survivor_count]
        
        logger.debug(f"🧪 Experimental selection: {elite_count} elites, {survivor_count} survivors from {population_size}")
        return survivors, elites
    
    async def _detect_experimental_patterns(self, swarm_type: str, successful_chromosomes: List[SwarmChromosome],
                                          fitness_evaluations: List[ExperimentalFitnessEvaluation]) -> None:
        """Detect experimental patterns and breakthroughs."""
        if not self.config.pattern_detection_enabled:
            return
        
        # Find high-performing experimental variants
        high_performers = [
            c for c in successful_chromosomes 
            if any(e.overall_fitness >= self.config.breakthrough_threshold 
                  for e in fitness_evaluations if e.chromosome_id == c.chromosome_id)
        ]
        
        # Detect experimental breakthroughs
        experimental_high_performers = [c for c in high_performers if c.experimental_variant]
        
        if experimental_high_performers:
            logger.info(f"🧪 Detected {len(experimental_high_performers)} experimental high-performers for {swarm_type}")
            
            # Record experimental discovery
            best_experimental_fitness = max(e.overall_fitness for e in fitness_evaluations 
                                           if e.chromosome_id in [c.chromosome_id for c in experimental_high_performers])
            
            self.experimental_discoveries.append({
                'timestamp': datetime.now().isoformat(),
                'swarm_type': swarm_type,
                'experimental_variants': len(experimental_high_performers),
                'best_experimental_fitness': best_experimental_fitness,
                'generation': self.generation_counter.get(swarm_type, 1)
            })
            
            self.evolution_stats['experimental_discoveries'] += 1
        
        # Standard pattern detection for all high performers
        if high_performers:
            patterns = self._extract_experimental_patterns(high_performers)
            
            if swarm_type not in self.successful_patterns:
                self.successful_patterns[swarm_type] = []
            
            for pattern in patterns:
                self.successful_patterns[swarm_type].append({
                    'pattern': pattern,
                    'timestamp': datetime.now().isoformat(),
                    'generation': self.generation_counter.get(swarm_type, 1),
                    'performance': max(e.overall_fitness for e in fitness_evaluations 
                                     if e.chromosome_id in [c.chromosome_id for c in high_performers]),
                    'experimental_pattern': any(c.experimental_variant for c in high_performers)
                })
            
            # Check for breakthroughs
            best_fitness = max(e.overall_fitness for e in fitness_evaluations)
            if best_fitness >= self.config.breakthrough_threshold:
                await self._record_experimental_breakthrough(swarm_type, best_fitness, high_performers[0])
                
            self.evolution_stats['patterns_discovered'] += len(patterns)
    
    def _extract_experimental_patterns(self, chromosomes: List[SwarmChromosome]) -> List[Dict[str, Any]]:
        """Extract patterns including experimental features."""
        if not chromosomes:
            return []
        
        patterns = []
        
        # Standard parameter patterns
        param_patterns = {}
        for chromosome in chromosomes:
            for agent, params in chromosome.agent_parameters.items():
                for param_name, value in params.items():
                    key = f"{agent}.{param_name}"
                    if key not in param_patterns:
                        param_patterns[key] = []
                    param_patterns[key].append(value)
        
        # Find consistent parameter ranges
        for key, values in param_patterns.items():
            if len(values) >= len(chromosomes) * 0.8:  # 80% consistency
                avg_value = sum(values) / len(values)
                patterns.append({
                    'type': 'parameter_convergence',
                    'parameter': key,
                    'average_value': avg_value,
                    'consistency': len(values) / len(chromosomes)
                })
        
        # Experimental gene patterns
        experimental_chromosomes = [c for c in chromosomes if c.experimental_variant]
        if experimental_chromosomes and len(experimental_chromosomes) >= len(chromosomes) * 0.5:
            # Experimental creativity patterns
            creativities = [c.experimental_creativity for c in experimental_chromosomes]
            avg_creativity = sum(creativities) / len(creativities)
            
            patterns.append({
                'type': 'experimental_creativity_pattern',
                'average_creativity': avg_creativity,
                'experimental_frequency': len(experimental_chromosomes) / len(chromosomes)
            })
            
            # Experimental exploration patterns
            explorations = [c.experimental_exploration for c in experimental_chromosomes]
            avg_exploration = sum(explorations) / len(explorations)
            
            patterns.append({
                'type': 'experimental_exploration_pattern',
                'average_exploration': avg_exploration,
                'experimental_frequency': len(experimental_chromosomes) / len(chromosomes)
            })
        
        return patterns
    
    async def _record_experimental_breakthrough(self, swarm_type: str, fitness_score: float, chromosome: SwarmChromosome):
        """Record an experimental breakthrough event."""
        breakthrough_type = 'experimental_breakthrough' if chromosome.experimental_variant else 'standard_breakthrough'
        
        breakthrough = {
            'timestamp': datetime.now().isoformat(),
            'swarm_type': swarm_type,
            'fitness_score': fitness_score,
            'chromosome_id': chromosome.chromosome_id,
            'generation': chromosome.generation,
            'breakthrough_type': breakthrough_type,
            'experimental_variant': chromosome.experimental_variant,
            'experimental_mutations': chromosome.experimental_mutations_count
        }
        
        self.breakthrough_events.append(breakthrough)
        self.evolution_stats['breakthroughs'] += 1
        
        # Store in memory if available
        if self.memory_client:
            await self.memory_client.log_swarm_event(
                SwarmMemoryEventType.EVOLUTION_EVENT,
                {
                    'event_type': 'experimental_breakthrough_detected',
                    'swarm_type': swarm_type,
                    'fitness_score': fitness_score,
                    'breakthrough_data': breakthrough,
                    'experimental': chromosome.experimental_variant
                }
            )
        
        logger.info(f"🧪🌟 EXPERIMENTAL BREAKTHROUGH detected for {swarm_type}: fitness {fitness_score:.3f} (experimental: {chromosome.experimental_variant})")
    
    async def _experimental_crossover_phase(self, survivors: List[SwarmChromosome], experimental_mode: bool) -> List[SwarmChromosome]:
        """Experimental crossover phase."""
        if len(survivors) < 2:
            return []
        
        offspring = []
        
        # Experimental approach: allow more offspring in experimental mode
        max_offspring = min(len(survivors), self.config.safety_bounds.max_population_changes)
        if experimental_mode:
            max_offspring = min(len(survivors), self.config.safety_bounds.max_population_changes * 2)
        
        for i in range(0, min(len(survivors) - 1, max_offspring), 2):
            if random.random() < self.config.crossover_rate:
                parent1, parent2 = survivors[i], survivors[i + 1]
                child1, child2 = SwarmChromosome.crossover(parent1, parent2, experimental_mode)
                offspring.extend([child1, child2])
        
        return offspring
    
    async def _experimental_mutation_phase(self, chromosomes: List[SwarmChromosome], experimental_mode: bool) -> None:
        """Experimental mutation phase."""
        mutation_count = 0
        experimental_mutations = 0
        
        for chromosome in chromosomes:
            mutation_rate = self.config.mutation_rate
            if experimental_mode and chromosome.experimental_variant:
                mutation_rate *= 1.5  # Higher mutation rate for experimental variants
                
            if random.random() < mutation_rate:
                # Apply mutation
                mutated = chromosome.mutate(
                    mutation_rate=mutation_rate * 0.5,  # Still conservative
                    safety_bounds=self.config.safety_bounds,
                    experimental_mode=experimental_mode
                )
                
                # Update chromosome in place
                chromosome.agent_parameters = mutated.agent_parameters
                chromosome.quality_threshold = mutated.quality_threshold
                chromosome.speed_preference = mutated.speed_preference
                chromosome.risk_tolerance = mutated.risk_tolerance
                
                if experimental_mode:
                    chromosome.experimental_creativity = mutated.experimental_creativity
                    chromosome.experimental_exploration = mutated.experimental_exploration
                    chromosome.experimental_cooperation = mutated.experimental_cooperation
                    chromosome.experimental_mutations_count = mutated.experimental_mutations_count
                    experimental_mutations += mutated.experimental_mutations_count
                
                mutation_count += 1
        
        logger.debug(f"🧪 Applied {mutation_count} mutations ({experimental_mutations} experimental)")
    
    async def _validate_experimental_population(self, swarm_type: str, population: List[SwarmChromosome]) -> bool:
        """Validate experimental population with adjusted safety requirements."""
        if self.config.experimental_validation_disabled:
            logger.warning(f"🧪 Experimental validation disabled for {swarm_type} - PROCEED WITH CAUTION")
            return True
            
        if not self.config.validation_enabled:
            return True
        
        # Check population size
        if len(population) == 0:
            logger.error(f"Empty experimental population for {swarm_type}")
            return False
        
        # Validate each chromosome
        for chromosome in population:
            if not self._validate_experimental_chromosome(chromosome):
                logger.warning(f"Invalid experimental chromosome {chromosome.chromosome_id} in {swarm_type} population")
                return False
        
        # Check for excessive risk (more tolerant in experimental mode)
        avg_risk = sum(c.risk_tolerance for c in population) / len(population)
        risk_threshold = 0.8
        if self.config.mode == ExperimentalMode.AGGRESSIVE:
            risk_threshold = 0.9  # More tolerant
            
        if avg_risk > risk_threshold:
            logger.warning(f"🧪 Experimental population risk too high for {swarm_type}: {avg_risk:.3f}")
            return False
        
        return True
    
    def _validate_experimental_chromosome(self, chromosome: SwarmChromosome) -> bool:
        """Validate experimental chromosome with adjusted bounds."""
        # Standard bounds still apply
        if not (0.0 <= chromosome.risk_tolerance <= 0.8):  # Risk still capped at 0.8 for safety
            return False
        if not (0.0 <= chromosome.quality_threshold <= 1.0):
            return False
        if not (0.0 <= chromosome.speed_preference <= 1.0):
            return False
        
        # Validate experimental genes if present
        if chromosome.experimental_variant:
            if not (0.0 <= chromosome.experimental_creativity <= 1.0):
                return False
            if not (0.0 <= chromosome.experimental_exploration <= 1.0):
                return False
            if not (0.0 <= chromosome.experimental_cooperation <= 1.0):
                return False
        
        # Validate parameters
        for agent, params in chromosome.agent_parameters.items():
            for param_name, value in params.items():
                if not (0.0 <= value <= 1.0):
                    return False
        
        return True
    
    def _create_experimental_snapshot(self, swarm_type: str, population: List[SwarmChromosome]):
        """Create snapshot for experimental rollback."""
        if swarm_type not in self.rollback_snapshots:
            self.rollback_snapshots[swarm_type] = []
        
        # Deep copy population
        snapshot = [deepcopy(chromosome) for chromosome in population]
        self.rollback_snapshots[swarm_type].append(snapshot)
        
        # Keep only recent snapshots
        max_snapshots = self.config.rollback_generations
        if len(self.rollback_snapshots[swarm_type]) > max_snapshots:
            self.rollback_snapshots[swarm_type] = self.rollback_snapshots[swarm_type][-max_snapshots:]
    
    async def _store_experimental_results(self, swarm_type: str, fitness_evaluations: List[ExperimentalFitnessEvaluation],
                                         population: List[SwarmChromosome]) -> None:
        """Store experimental evolution results in memory system."""
        if not self.memory_client:
            return
        
        try:
            # Store generation summary
            generation = self.generation_counter.get(swarm_type, 1)
            best_fitness = max(e.overall_fitness for e in fitness_evaluations)
            avg_fitness = sum(e.overall_fitness for e in fitness_evaluations) / len(fitness_evaluations)
            experimental_variants = sum(1 for c in population if c.experimental_variant)
            
            await self.memory_client.store_learning(
                learning_type="experimental_evolution_generation",
                content=f"🧪 Experimental Generation {generation} for {swarm_type}: best={best_fitness:.3f}, avg={avg_fitness:.3f}, experimental_variants={experimental_variants}",
                confidence=min(best_fitness + 0.1, 1.0),
                context={
                    'swarm_type': swarm_type,
                    'generation': generation,
                    'population_size': len(population),
                    'experimental_mode': self.config.mode.value,
                    'experimental_variants': experimental_variants,
                    'experimental_mutations': sum(c.experimental_mutations_count for c in population)
                }
            )
            
            # Store experimental patterns if discovered
            if swarm_type in self.successful_patterns:
                recent_patterns = [p for p in self.successful_patterns[swarm_type]
                                 if p.get('generation') == generation]
                if recent_patterns:
                    await self.memory_client.store_pattern(
                        pattern_name=f"experimental_evolution_patterns_{swarm_type}",
                        pattern_data={
                            'patterns': recent_patterns,
                            'generation': generation,
                            'best_fitness': best_fitness,
                            'experimental_discoveries': len([d for d in self.experimental_discoveries
                                                           if d.get('swarm_type') == swarm_type and d.get('generation') == generation])
                        },
                        success_score=best_fitness,
                        context={'experimental_evolution': True, 'swarm_type': swarm_type}
                    )
            
        except Exception as e:
            logger.warning(f"🧪 Failed to store experimental evolution results in memory: {e}")
    
    def get_best_experimental_chromosome(self, swarm_type: str) -> Optional[SwarmChromosome]:
        """Get the current best experimental chromosome for a swarm type."""
        population = self.populations.get(swarm_type)
        if not population:
            return None
        
        return max(population, key=lambda c: c.fitness_score)
    
    async def export_experimental_evolution_data(self, swarm_type: Optional[str] = None) -> Dict[str, Any]:
        """Export experimental evolution data for analysis."""
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'experimental_config': asdict(self.config),
            'experimental_statistics': self.evolution_stats,
            'breakthrough_events': self.breakthrough_events,
            'experimental_discoveries': self.experimental_discoveries,
            'experimental_warnings': self.experimental_warnings,
            'safety_violations': self.safety_violations
        }
        
        if swarm_type:
            population = self.populations.get(swarm_type, [])
            data['swarm_data'] = {
                'swarm_type': swarm_type,
                'generation': self.generation_counter.get(swarm_type, 0),
                'population': [asdict(c) for c in population],
                'experimental_variants': sum(1 for c in population if c.experimental_variant),
                'fitness_history': [asdict(f) for f in self.fitness_history.get(swarm_type, [])],
                'successful_patterns': self.successful_patterns.get(swarm_type, []),
                'performance_history': self.performance_history.get(swarm_type, []),
                'experimental_mutations_total': sum(c.experimental_mutations_count for c in population)
            }
        else:
            data['all_swarm_data'] = {}
            for stype in self.populations:
                pop = self.populations[stype]
                data['all_swarm_data'][stype] = {
                    'generation': self.generation_counter.get(stype, 0),
                    'population_size': len(pop),
                    'experimental_variants': sum(1 for c in pop if c.experimental_variant),
                    'patterns_count': len(self.successful_patterns.get(stype, [])),
                    'performance_baseline': self.performance_baseline.get(stype, 0),
                    'experimental_mutations_total': sum(c.experimental_mutations_count for c in pop)
                }
        
        return data
    
    async def experimental_shutdown(self):
        """Gracefully shutdown the experimental evolution engine."""
        logger.info("🧪 Shutting down experimental evolution engine")
        
        # Disable evolution for all swarm types
        for swarm_type in self.evolution_active:
            self.evolution_active[swarm_type] = False
        
        # Final experimental memory storage if available
        if self.memory_client:
            try:
                await self.memory_client.store_learning(
                    learning_type="experimental_evolution_shutdown",
                    content=f"🧪 Experimental evolution engine shutdown - Total generations: {self.evolution_stats['total_generations']}, Experimental discoveries: {self.evolution_stats['experimental_discoveries']}",
                    confidence=1.0,
                    context={
                        'experimental_shutdown': True,
                        'final_stats': self.evolution_stats,
                        'mode': self.config.mode.value,
                        'experimental_warnings': len(self.experimental_warnings)
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to store experimental shutdown data: {e}")
        
        logger.info(f"🧪 Experimental evolution engine shutdown complete - Stats: {self.evolution_stats}")


# Factory function for creating experimental evolution engines
def create_experimental_evolution_engine(
    mode: ExperimentalMode = ExperimentalMode.DISABLED,
    enable_experimental: bool = False,
    acknowledge_experimental: bool = False,
    memory_client: Optional[SwarmMemoryClient] = None,
    **kwargs
) -> ExperimentalEvolutionEngine:
    """
    Factory function to create an experimental evolution engine with safety checks.
    
    Args:
        mode: Experimental evolution mode
        enable_experimental: Must be True to enable experimental features
        acknowledge_experimental: Must be True to acknowledge experimental nature
        memory_client: Optional memory client for integration
        **kwargs: Additional configuration options
        
    Returns:
        ExperimentalEvolutionEngine instance
        
    Raises:
        ValueError: If experimental features are requested without proper acknowledgment
    """
    
    if enable_experimental and not acknowledge_experimental:
        raise ValueError(
            "🧪 EXPERIMENTAL EVOLUTION REQUIRES ACKNOWLEDGMENT: "
            "You must set acknowledge_experimental=True to enable experimental evolution features. "
            "These are experimental capabilities that may behave unexpectedly."
        )
    
    config = ExperimentalEvolutionConfig(
        mode=mode,
        enabled=enable_experimental,
        experimental_features_acknowledged=acknowledge_experimental,
        **kwargs
    )
    
    engine = ExperimentalEvolutionEngine(config=config, memory_client=memory_client)
    
    if enable_experimental:
        logger.warning(
            f"🧪 EXPERIMENTAL EVOLUTION ENGINE CREATED - Mode: {mode.value}\n"
            "⚠️  This is an experimental system. Monitor closely for unexpected behavior.\n"
            "⚠️  Use dry_run_mode=True for initial testing.\n"
            "⚠️  Ensure proper safety monitoring is in place."
        )
    
    return engine


# Example usage and configuration templates
EXPERIMENTAL_EVOLUTION_EXAMPLES = {
    "disabled": {
        "description": "Safe default - no evolution",
        "config": {
            "mode": ExperimentalMode.DISABLED,
            "enabled": False
        }
    },
    
    "observe_only": {
        "description": "Monitor patterns without evolving",
        "config": {
            "mode": ExperimentalMode.OBSERVE_ONLY,
            "enabled": True,
            "experimental_features_acknowledged": True,
            "dry_run_mode": True
        }
    },
    
    "cautious_experimental": {
        "description": "Very conservative experimental evolution",
        "config": {
            "mode": ExperimentalMode.CAUTIOUS,
            "enabled": True,
            "experimental_features_acknowledged": True,
            "dry_run_mode": True,
            "mutation_rate": 0.05,
            "selection_pressure": 0.2,
            "enable_rollback": True,
            "rollback_generations": 5
        }
    },
    
    "balanced_experimental": {
        "description": "Balanced experimental evolution with safety",
        "config": {
            "mode": ExperimentalMode.EXPERIMENTAL,
            "enabled": True,
            "experimental_features_acknowledged": True,
            "dry_run_mode": False,
            "mutation_rate": 0.1,
            "selection_pressure": 0.3,
            "experimental_pattern_analysis": True,
            "experimental_memory_features": True
        }
    },
    
    "aggressive_experimental": {
        "description": "High-risk experimental evolution - USE WITH EXTREME CAUTION",
        "config": {
            "mode": ExperimentalMode.AGGRESSIVE,
            "enabled": True,
            "experimental_features_acknowledged": True,
            "dry_run_mode": False,
            "mutation_rate": 0.15,
            "selection_pressure": 0.4,
            "experimental_pattern_analysis": True,
            "experimental_memory_features": True,
            "experimental_cross_population_breeding": True,
            "real_time_evolution": True,
            "experimental_continuous_adaptation": True
        }
    }
}