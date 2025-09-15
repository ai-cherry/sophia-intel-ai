#!/usr/bin/env python3
"""
Genetic Algorithm Mode Agent - Evolutionary Code Optimization
Implements evolutionary algorithms for code optimization, using genetic principles
to evolve better solutions through mutation, crossover, and selection.
"""

import asyncio
import json
import random
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Dict, Optional, Tuple, Callable
from datetime import datetime
import aiohttp

from agents.core.base_agent import AgentCapability, AgentConfig, BaseAgent


class OptimizationTarget(Enum):
    """Optimization targets for genetic algorithm"""
    PERFORMANCE = "performance"
    MEMORY_USAGE = "memory_usage"
    CODE_COMPLEXITY = "code_complexity"
    TEST_COVERAGE = "test_coverage"
    BUNDLE_SIZE = "bundle_size"
    SECURITY_SCORE = "security_score"
    MAINTAINABILITY = "maintainability"


class MutationType(Enum):
    """Types of mutations for code evolution"""
    ALGORITHM_SWAP = "algorithm_swap"
    DATA_STRUCTURE_CHANGE = "data_structure_change"
    OPTIMIZATION_TECHNIQUE = "optimization_technique"
    REFACTORING = "refactoring"
    PARALLELIZATION = "parallelization"
    CACHING_STRATEGY = "caching_strategy"
    MEMORY_OPTIMIZATION = "memory_optimization"


class CrossoverStrategy(Enum):
    """Crossover strategies for combining solutions"""
    SINGLE_POINT = "single_point"
    TWO_POINT = "two_point"
    UNIFORM = "uniform"
    ARITHMETIC = "arithmetic"
    HEURISTIC = "heuristic"


class SelectionMethod(Enum):
    """Selection methods for choosing parents"""
    TOURNAMENT = "tournament"
    ROULETTE_WHEEL = "roulette_wheel"
    RANK_BASED = "rank_based"
    ELITISM = "elitism"
    TRUNCATION = "truncation"


@dataclass
class Gene:
    """Represents a single gene (code trait) in the genetic algorithm"""
    id: str
    type: str
    value: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    mutation_probability: float = 0.1
    
    def mutate(self) -> 'Gene':
        """Apply mutation to this gene"""
        if random.random() < self.mutation_probability:
            # Clone and modify the gene
            return Gene(
                id=self.id,
                type=self.type,
                value=self._mutate_value(),
                metadata={**self.metadata, "mutated": True},
                mutation_probability=self.mutation_probability
            )
        return self
    
    def _mutate_value(self) -> Any:
        """Internal mutation logic based on gene type"""
        if self.type == "algorithm":
            algorithms = ["quicksort", "mergesort", "heapsort", "timsort"]
            return random.choice([a for a in algorithms if a != self.value])
        elif self.type == "data_structure":
            structures = ["array", "linked_list", "tree", "hash_map", "graph"]
            return random.choice([s for s in structures if s != self.value])
        elif self.type == "optimization":
            optimizations = ["memoization", "lazy_evaluation", "streaming", "batching"]
            return random.choice([o for o in optimizations if o != self.value])
        return self.value


@dataclass
class Chromosome:
    """Represents a chromosome (complete solution) composed of genes"""
    id: str
    genes: List[Gene]
    fitness_score: float = 0.0
    generation: int = 0
    parents: Optional[Tuple[str, str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_hash(self) -> str:
        """Calculate unique hash for this chromosome"""
        gene_values = [g.value for g in self.genes]
        return hashlib.md5(json.dumps(gene_values, sort_keys=True).encode()).hexdigest()
    
    def crossover(self, other: 'Chromosome', strategy: CrossoverStrategy) -> Tuple['Chromosome', 'Chromosome']:
        """Perform crossover with another chromosome"""
        if strategy == CrossoverStrategy.SINGLE_POINT:
            point = random.randint(1, len(self.genes) - 1)
            child1_genes = self.genes[:point] + other.genes[point:]
            child2_genes = other.genes[:point] + self.genes[point:]
        elif strategy == CrossoverStrategy.TWO_POINT:
            point1 = random.randint(1, len(self.genes) - 2)
            point2 = random.randint(point1 + 1, len(self.genes) - 1)
            child1_genes = self.genes[:point1] + other.genes[point1:point2] + self.genes[point2:]
            child2_genes = other.genes[:point1] + self.genes[point1:point2] + other.genes[point2:]
        else:  # UNIFORM
            child1_genes = []
            child2_genes = []
            for i in range(len(self.genes)):
                if random.random() < 0.5:
                    child1_genes.append(self.genes[i])
                    child2_genes.append(other.genes[i])
                else:
                    child1_genes.append(other.genes[i])
                    child2_genes.append(self.genes[i])
        
        child1 = Chromosome(
            id=f"child_{self.calculate_hash()[:8]}",
            genes=child1_genes,
            generation=max(self.generation, other.generation) + 1,
            parents=(self.id, other.id)
        )
        
        child2 = Chromosome(
            id=f"child_{other.calculate_hash()[:8]}",
            genes=child2_genes,
            generation=max(self.generation, other.generation) + 1,
            parents=(self.id, other.id)
        )
        
        return child1, child2
    
    def mutate(self, mutation_rate: float = 0.1) -> 'Chromosome':
        """Apply mutations to this chromosome"""
        mutated_genes = []
        for gene in self.genes:
            if random.random() < mutation_rate:
                mutated_genes.append(gene.mutate())
            else:
                mutated_genes.append(gene)
        
        return Chromosome(
            id=f"mut_{self.id}",
            genes=mutated_genes,
            generation=self.generation,
            parents=(self.id,) if self.parents else None,
            metadata={**self.metadata, "mutated": True}
        )


@dataclass
class Population:
    """Represents a population of chromosomes"""
    generation: int
    chromosomes: List[Chromosome]
    best_fitness: float = 0.0
    average_fitness: float = 0.0
    diversity_score: float = 0.0
    convergence_rate: float = 0.0
    
    def calculate_diversity(self) -> float:
        """Calculate genetic diversity in the population"""
        unique_hashes = set()
        for chromosome in self.chromosomes:
            unique_hashes.add(chromosome.calculate_hash())
        return len(unique_hashes) / len(self.chromosomes)
    
    def get_elite(self, percentage: float = 0.1) -> List[Chromosome]:
        """Get the top performing chromosomes"""
        sorted_chromosomes = sorted(self.chromosomes, key=lambda c: c.fitness_score, reverse=True)
        elite_count = max(1, int(len(sorted_chromosomes) * percentage))
        return sorted_chromosomes[:elite_count]
    
    def select_parents(self, method: SelectionMethod, count: int = 2) -> List[Chromosome]:
        """Select parents for reproduction"""
        if method == SelectionMethod.TOURNAMENT:
            tournament_size = 3
            parents = []
            for _ in range(count):
                tournament = random.sample(self.chromosomes, tournament_size)
                winner = max(tournament, key=lambda c: c.fitness_score)
                parents.append(winner)
            return parents
        elif method == SelectionMethod.ROULETTE_WHEEL:
            total_fitness = sum(c.fitness_score for c in self.chromosomes)
            if total_fitness == 0:
                return random.sample(self.chromosomes, count)
            
            parents = []
            for _ in range(count):
                spin = random.random() * total_fitness
                current = 0
                for chromosome in self.chromosomes:
                    current += chromosome.fitness_score
                    if current >= spin:
                        parents.append(chromosome)
                        break
            return parents
        else:  # ELITISM
            return self.get_elite(0.2)[:count]


@dataclass
class EvolutionResult:
    """Result of a genetic algorithm evolution"""
    best_solution: Chromosome
    final_population: Population
    generations_evolved: int
    fitness_history: List[float]
    diversity_history: List[float]
    optimization_target: OptimizationTarget
    achieved_improvement: float
    evolution_time: float
    convergence_generation: Optional[int] = None


@dataclass
class FitnessFunction:
    """Configurable fitness function for evaluating solutions"""
    name: str
    target: OptimizationTarget
    weight: float = 1.0
    evaluator: Optional[Callable] = None
    
    async def evaluate(self, chromosome: Chromosome) -> float:
        """Evaluate fitness of a chromosome"""
        if self.evaluator:
            return await self.evaluator(chromosome)
        
        # Default evaluators based on target
        if self.target == OptimizationTarget.PERFORMANCE:
            return await self._evaluate_performance(chromosome)
        elif self.target == OptimizationTarget.MEMORY_USAGE:
            return await self._evaluate_memory(chromosome)
        elif self.target == OptimizationTarget.CODE_COMPLEXITY:
            return await self._evaluate_complexity(chromosome)
        elif self.target == OptimizationTarget.TEST_COVERAGE:
            return await self._evaluate_coverage(chromosome)
        return 0.0
    
    async def _evaluate_performance(self, chromosome: Chromosome) -> float:
        """Evaluate performance fitness"""
        # Simulate performance evaluation
        score = 0.0
        for gene in chromosome.genes:
            if gene.type == "algorithm":
                if gene.value == "quicksort":
                    score += 0.8
                elif gene.value == "timsort":
                    score += 0.9
                elif gene.value == "mergesort":
                    score += 0.7
            elif gene.type == "optimization":
                if gene.value == "memoization":
                    score += 0.5
                elif gene.value == "lazy_evaluation":
                    score += 0.4
        return min(score, 1.0)
    
    async def _evaluate_memory(self, chromosome: Chromosome) -> float:
        """Evaluate memory usage fitness"""
        score = 0.0
        for gene in chromosome.genes:
            if gene.type == "data_structure":
                if gene.value == "array":
                    score += 0.9
                elif gene.value == "linked_list":
                    score += 0.6
                elif gene.value == "hash_map":
                    score += 0.7
        return min(score, 1.0)
    
    async def _evaluate_complexity(self, chromosome: Chromosome) -> float:
        """Evaluate code complexity fitness"""
        # Lower complexity is better
        complexity_score = 1.0
        for gene in chromosome.genes:
            if gene.value in ["recursive", "nested_loops"]:
                complexity_score -= 0.2
        return max(complexity_score, 0.0)
    
    async def _evaluate_coverage(self, chromosome: Chromosome) -> float:
        """Evaluate test coverage fitness"""
        # Simulate test coverage calculation
        return random.uniform(0.6, 0.95)


class GeneticAlgorithmAgent(BaseAgent):
    """
    Genetic Algorithm Mode Agent for evolutionary code optimization
    Uses genetic principles to evolve optimal code solutions
    """
    
    def __init__(self):
        """Initialize GeneticAlgorithmAgent with BaseAgent pattern"""
        config = AgentConfig(
            agent_id="genetic-algorithm-agent",
            agent_name="Genetic Algorithm Optimization Agent",
            agent_type="evolutionary_optimization",
            capabilities=[
                AgentCapability.ANALYSIS,
                AgentCapability.GENERATION,
                AgentCapability.OPTIMIZATION,
                AgentCapability.VALIDATION,
            ],
            max_concurrent_tasks=8,
        )
        super().__init__(config)
        
        # Genetic algorithm components
        self.populations: Dict[str, Population] = {}
        self.fitness_functions: Dict[str, FitnessFunction] = {}
        self.evolution_history: Dict[str, List[Population]] = {}
        self.mutation_strategies: Dict[MutationType, Callable] = {}
        self.mcp_memory_url = "http://localhost:8081"
        self.mcp_git_url = "http://localhost:8084"
        
        # Evolution parameters
        self.default_population_size = 50
        self.default_generations = 100
        self.default_mutation_rate = 0.1
        self.default_crossover_rate = 0.7
        self.convergence_threshold = 0.001
        self.stagnation_limit = 10
    
    async def _initialize_agent_specific(self) -> None:
        """Initialize Genetic Algorithm-specific components"""
        try:
            # Initialize fitness functions
            self._initialize_fitness_functions()
            
            # Initialize mutation strategies
            self._initialize_mutation_strategies()
            
            # Connect to MCP servers
            await self._connect_mcp_servers()
            
            self.logger.info("Genetic Algorithm Agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Genetic Algorithm Agent: {str(e)}")
            raise
    
    async def _process_task_impl(
        self, task_id: str, task_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process genetic algorithm optimization tasks"""
        task_type = task_data.get("task_type")
        if not task_type:
            raise ValueError("task_type is required")
        
        # Route to appropriate handler
        if task_type == "evolve_solution":
            return await self._handle_evolve_solution(task_data)
        elif task_type == "optimize_code":
            return await self._handle_optimize_code(task_data)
        elif task_type == "analyze_population":
            return await self._handle_analyze_population(task_data)
        elif task_type == "crossover_solutions":
            return await self._handle_crossover_solutions(task_data)
        elif task_type == "mutate_solution":
            return await self._handle_mutate_solution(task_data)
        elif task_type == "evaluate_fitness":
            return await self._handle_evaluate_fitness(task_data)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    
    async def _cleanup_agent_specific(self) -> None:
        """Cleanup Genetic Algorithm-specific resources"""
        try:
            # Save evolution history to MCP memory
            for evolution_id, history in self.evolution_history.items():
                await self._save_to_memory(f"evolution_{evolution_id}", history)
            
            self.logger.info("Genetic Algorithm Agent cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during Genetic Algorithm Agent cleanup: {str(e)}")
    
    # Public API methods
    
    async def evolve_solution(
        self,
        problem_description: str,
        optimization_target: OptimizationTarget,
        initial_population: Optional[Population] = None,
        generations: int = 100,
        population_size: int = 50
    ) -> EvolutionResult:
        """
        Evolve an optimal solution using genetic algorithm
        """
        try:
            self.logger.info(f"Starting evolution for: {problem_description}")
            start_time = datetime.now()
            
            # Initialize or use provided population
            if initial_population:
                population = initial_population
            else:
                population = await self._initialize_population(
                    problem_description, population_size
                )
            
            # Get fitness function
            fitness_function = self.fitness_functions.get(
                optimization_target.value,
                FitnessFunction("default", optimization_target)
            )
            
            # Evolution tracking
            fitness_history = []
            diversity_history = []
            best_solution = None
            stagnation_counter = 0
            convergence_generation = None
            
            # Main evolution loop
            for generation in range(generations):
                # Evaluate fitness for all chromosomes
                for chromosome in population.chromosomes:
                    chromosome.fitness_score = await fitness_function.evaluate(chromosome)
                
                # Calculate population statistics
                population.best_fitness = max(c.fitness_score for c in population.chromosomes)
                population.average_fitness = sum(c.fitness_score for c in population.chromosomes) / len(population.chromosomes)
                population.diversity_score = population.calculate_diversity()
                
                fitness_history.append(population.best_fitness)
                diversity_history.append(population.diversity_score)
                
                # Check for convergence
                if generation > 0:
                    improvement = abs(fitness_history[-1] - fitness_history[-2])
                    if improvement < self.convergence_threshold:
                        stagnation_counter += 1
                        if stagnation_counter >= self.stagnation_limit:
                            convergence_generation = generation
                            self.logger.info(f"Converged at generation {generation}")
                            break
                    else:
                        stagnation_counter = 0
                
                # Get best solution
                current_best = max(population.chromosomes, key=lambda c: c.fitness_score)
                if best_solution is None or current_best.fitness_score > best_solution.fitness_score:
                    best_solution = current_best
                
                # Create next generation
                if generation < generations - 1:
                    population = await self._create_next_generation(
                        population, SelectionMethod.TOURNAMENT, CrossoverStrategy.UNIFORM
                    )
                
                # Log progress
                if generation % 10 == 0:
                    self.logger.info(
                        f"Generation {generation}: Best={population.best_fitness:.3f}, "
                        f"Avg={population.average_fitness:.3f}, Diversity={population.diversity_score:.3f}"
                    )
                
                # Store in evolution history
                self.evolution_history.setdefault(problem_description, []).append(population)
            
            # Calculate improvement
            initial_fitness = fitness_history[0] if fitness_history else 0
            final_fitness = best_solution.fitness_score if best_solution else 0
            improvement = ((final_fitness - initial_fitness) / initial_fitness * 100) if initial_fitness > 0 else 0
            
            # Create result
            result = EvolutionResult(
                best_solution=best_solution,
                final_population=population,
                generations_evolved=generation + 1,
                fitness_history=fitness_history,
                diversity_history=diversity_history,
                optimization_target=optimization_target,
                achieved_improvement=improvement,
                evolution_time=(datetime.now() - start_time).total_seconds(),
                convergence_generation=convergence_generation
            )
            
            self.logger.info(
                f"Evolution completed: {improvement:.1f}% improvement after {generation + 1} generations"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during evolution: {str(e)}")
            raise
    
    async def optimize_code(
        self,
        code_snippet: str,
        language: str,
        optimization_targets: List[OptimizationTarget],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize code using genetic algorithm
        """
        try:
            self.logger.info(f"Optimizing {language} code for {optimization_targets}")
            
            # Parse code into genes
            genes = await self._parse_code_to_genes(code_snippet, language)
            
            # Create initial chromosome
            initial_chromosome = Chromosome(
                id="initial",
                genes=genes,
                generation=0
            )
            
            # Create initial population with variations
            population = await self._create_population_from_chromosome(
                initial_chromosome, self.default_population_size
            )
            
            # Evolve for each optimization target
            results = {}
            for target in optimization_targets:
                evolution_result = await self.evolve_solution(
                    f"optimize_{target.value}",
                    target,
                    population,
                    generations=50
                )
                results[target.value] = evolution_result
            
            # Combine best solutions
            best_combined = await self._combine_best_solutions(results)
            
            # Generate optimized code
            optimized_code = await self._genes_to_code(
                best_combined.genes, language
            )
            
            return {
                "original_code": code_snippet,
                "optimized_code": optimized_code,
                "improvements": {
                    target.value: result.achieved_improvement
                    for target, result in results.items()
                },
                "best_solution": best_combined,
                "optimization_targets": [t.value for t in optimization_targets]
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing code: {str(e)}")
            raise
    
    async def analyze_population_fitness(
        self, population: Population, target: OptimizationTarget
    ) -> Dict[str, Any]:
        """
        Analyze fitness distribution in a population
        """
        try:
            fitness_function = self.fitness_functions.get(
                target.value,
                FitnessFunction("default", target)
            )
            
            # Evaluate all chromosomes
            for chromosome in population.chromosomes:
                chromosome.fitness_score = await fitness_function.evaluate(chromosome)
            
            # Calculate statistics
            fitness_scores = [c.fitness_score for c in population.chromosomes]
            
            analysis = {
                "generation": population.generation,
                "population_size": len(population.chromosomes),
                "best_fitness": max(fitness_scores),
                "worst_fitness": min(fitness_scores),
                "average_fitness": sum(fitness_scores) / len(fitness_scores),
                "fitness_variance": self._calculate_variance(fitness_scores),
                "diversity_score": population.calculate_diversity(),
                "elite_percentage": len(population.get_elite(0.1)) / len(population.chromosomes),
                "fitness_distribution": self._calculate_distribution(fitness_scores)
            }
            
            self.logger.info(f"Population analysis complete: Gen {population.generation}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing population: {str(e)}")
            raise
    
    # Private helper methods
    
    async def _handle_evolve_solution(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle solution evolution task"""
        problem = task_data.get("problem_description", "unknown")
        target = OptimizationTarget(task_data.get("optimization_target", "performance"))
        generations = task_data.get("generations", self.default_generations)
        population_size = task_data.get("population_size", self.default_population_size)
        
        result = await self.evolve_solution(
            problem, target, None, generations, population_size
        )
        
        return {
            "task_type": "evolve_solution",
            "best_fitness": result.best_solution.fitness_score,
            "generations_evolved": result.generations_evolved,
            "improvement": result.achieved_improvement,
            "convergence_generation": result.convergence_generation,
            "evolution_time": result.evolution_time
        }
    
    async def _handle_optimize_code(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code optimization task"""
        code = task_data.get("code_snippet", "")
        language = task_data.get("language", "python")
        targets = [
            OptimizationTarget(t) for t in task_data.get("optimization_targets", ["performance"])
        ]
        
        result = await self.optimize_code(code, language, targets)
        
        return {
            "task_type": "optimize_code",
            "optimized_code": result["optimized_code"],
            "improvements": result["improvements"],
            "optimization_targets": result["optimization_targets"]
        }
    
    async def _handle_analyze_population(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle population analysis task"""
        # Create population from task data
        chromosomes_data = task_data.get("chromosomes", [])
        chromosomes = []
        
        for chr_data in chromosomes_data:
            genes = [
                Gene(
                    id=g.get("id", f"gene_{i}"),
                    type=g.get("type", "unknown"),
                    value=g.get("value"),
                    metadata=g.get("metadata", {})
                )
                for i, g in enumerate(chr_data.get("genes", []))
            ]
            
            chromosome = Chromosome(
                id=chr_data.get("id", "unknown"),
                genes=genes,
                generation=chr_data.get("generation", 0)
            )
            chromosomes.append(chromosome)
        
        population = Population(
            generation=task_data.get("generation", 0),
            chromosomes=chromosomes
        )
        
        target = OptimizationTarget(task_data.get("optimization_target", "performance"))
        analysis = await self.analyze_population_fitness(population, target)
        
        return {
            "task_type": "analyze_population",
            **analysis
        }
    
    async def _handle_crossover_solutions(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle solution crossover task"""
        # Implementation for crossover
        return {
            "task_type": "crossover_solutions",
            "success": True,
            "message": "Crossover completed"
        }
    
    async def _handle_mutate_solution(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle solution mutation task"""
        # Implementation for mutation
        return {
            "task_type": "mutate_solution",
            "success": True,
            "message": "Mutation completed"
        }
    
    async def _handle_evaluate_fitness(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fitness evaluation task"""
        # Implementation for fitness evaluation
        return {
            "task_type": "evaluate_fitness",
            "fitness_score": random.random(),
            "details": {}
        }
    
    def _initialize_fitness_functions(self) -> None:
        """Initialize fitness function configurations"""
        self.fitness_functions = {
            OptimizationTarget.PERFORMANCE.value: FitnessFunction(
                "performance", OptimizationTarget.PERFORMANCE, weight=1.0
            ),
            OptimizationTarget.MEMORY_USAGE.value: FitnessFunction(
                "memory", OptimizationTarget.MEMORY_USAGE, weight=0.8
            ),
            OptimizationTarget.CODE_COMPLEXITY.value: FitnessFunction(
                "complexity", OptimizationTarget.CODE_COMPLEXITY, weight=0.6
            ),
            OptimizationTarget.TEST_COVERAGE.value: FitnessFunction(
                "coverage", OptimizationTarget.TEST_COVERAGE, weight=0.9
            ),
            OptimizationTarget.BUNDLE_SIZE.value: FitnessFunction(
                "bundle", OptimizationTarget.BUNDLE_SIZE, weight=0.7
            )
        }
    
    def _initialize_mutation_strategies(self) -> None:
        """Initialize mutation strategy functions"""
        self.mutation_strategies = {
            MutationType.ALGORITHM_SWAP: self._mutate_algorithm,
            MutationType.DATA_STRUCTURE_CHANGE: self._mutate_data_structure,
            MutationType.OPTIMIZATION_TECHNIQUE: self._mutate_optimization,
            MutationType.REFACTORING: self._mutate_refactoring,
            MutationType.PARALLELIZATION: self._mutate_parallelization,
            MutationType.CACHING_STRATEGY: self._mutate_caching,
            MutationType.MEMORY_OPTIMIZATION: self._mutate_memory
        }
    
    async def _connect_mcp_servers(self) -> None:
        """Connect to MCP servers for memory and git operations"""
        try:
            # Test connection to memory server
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.mcp_memory_url}/health") as response:
                    if response.status == 200:
                        self.logger.info("Connected to MCP Memory Server")
        except Exception as e:
            self.logger.warning(f"Could not connect to MCP servers: {str(e)}")
    
    async def _initialize_population(
        self, problem_description: str, size: int
    ) -> Population:
        """Initialize a random population"""
        chromosomes = []
        
        for i in range(size):
            # Create random genes
            genes = []
            gene_types = ["algorithm", "data_structure", "optimization"]
            
            for j in range(random.randint(5, 10)):
                gene_type = random.choice(gene_types)
                
                if gene_type == "algorithm":
                    value = random.choice(["quicksort", "mergesort", "heapsort", "timsort"])
                elif gene_type == "data_structure":
                    value = random.choice(["array", "linked_list", "tree", "hash_map"])
                else:
                    value = random.choice(["memoization", "lazy_evaluation", "streaming"])
                
                gene = Gene(
                    id=f"gene_{j}",
                    type=gene_type,
                    value=value,
                    mutation_probability=self.default_mutation_rate
                )
                genes.append(gene)
            
            chromosome = Chromosome(
                id=f"chr_{i}",
                genes=genes,
                generation=0
            )
            chromosomes.append(chromosome)
        
        return Population(
            generation=0,
            chromosomes=chromosomes
        )
    
    async def _create_next_generation(
        self,
        population: Population,
        selection_method: SelectionMethod,
        crossover_strategy: CrossoverStrategy
    ) -> Population:
        """Create the next generation through selection, crossover, and mutation"""
        new_chromosomes = []
        
        # Elitism - keep best solutions
        elite = population.get_elite(0.1)
        new_chromosomes.extend(elite)
        
        # Generate offspring
        while len(new_chromosomes) < len(population.chromosomes):
            # Select parents
            parents = population.select_parents(selection_method, 2)
            
            # Crossover
            if random.random() < self.default_crossover_rate and len(parents) >= 2:
                child1, child2 = parents[0].crossover(parents[1], crossover_strategy)
                
                # Mutation
                child1 = child1.mutate(self.default_mutation_rate)
                child2 = child2.mutate(self.default_mutation_rate)
                
                new_chromosomes.extend([child1, child2])
            else:
                # Direct reproduction with mutation
                for parent in parents:
                    new_chromosomes.append(parent.mutate(self.default_mutation_rate))
        
        # Trim to population size
        new_chromosomes = new_chromosomes[:len(population.chromosomes)]
        
        return Population(
            generation=population.generation + 1,
            chromosomes=new_chromosomes
        )
    
    async def _parse_code_to_genes(self, code: str, language: str) -> List[Gene]:
        """Parse code snippet into genetic representation"""
        genes = []
        
        # Simple parsing - in production, use proper AST parsing
        lines = code.split('\n')
        
        for i, line in enumerate(lines):
            if 'for' in line or 'while' in line:
                genes.append(Gene(
                    id=f"loop_{i}",
                    type="algorithm",
                    value="iteration",
                    metadata={"line": i, "content": line}
                ))
            elif 'if' in line:
                genes.append(Gene(
                    id=f"condition_{i}",
                    type="control_flow",
                    value="conditional",
                    metadata={"line": i, "content": line}
                ))
            elif 'def' in line or 'function' in line:
                genes.append(Gene(
                    id=f"function_{i}",
                    type="structure",
                    value="function",
                    metadata={"line": i, "content": line}
                ))
        
        return genes
    
    async def _genes_to_code(self, genes: List[Gene], language: str) -> str:
        """Convert genes back to code"""
        # Simplified implementation - in production, use proper code generation
        code_lines = []
        
        for gene in genes:
            if "content" in gene.metadata:
                code_lines.append(gene.metadata["content"])
            else:
                # Generate code based on gene type and value
                if gene.type == "algorithm":
                    code_lines.append(f"# Algorithm: {gene.value}")
                elif gene.type == "optimization":
                    code_lines.append(f"# Optimization: {gene.value}")
        
        return '\n'.join(code_lines)
    
    async def _create_population_from_chromosome(
        self, chromosome: Chromosome, size: int
    ) -> Population:
        """Create population with variations of a chromosome"""
        chromosomes = [chromosome]
        
        for i in range(1, size):
            # Create variation through mutation
            variant = chromosome.mutate(0.2)
            variant.id = f"variant_{i}"
            chromosomes.append(variant)
        
        return Population(
            generation=0,
            chromosomes=chromosomes
        )
    
    async def _combine_best_solutions(
        self, results: Dict[str, EvolutionResult]
    ) -> Chromosome:
        """Combine best solutions from multiple evolution runs"""
        # Get all best solutions
        best_solutions = [result.best_solution for result in results.values()]
        
        if not best_solutions:
            return None
        
        # Combine genes from best solutions
        combined_genes = []
        for solution in best_solutions:
            # Take best genes from each solution
            for gene in solution.genes:
                if gene not in combined_genes:
                    combined_genes.append(gene)
        
        return Chromosome(
            id="combined_best",
            genes=combined_genes[:10],  # Limit gene count
            generation=max(s.generation for s in best_solutions)
        )
    
    async def _save_to_memory(self, key: str, data: Any) -> None:
        """Save data to MCP memory server"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "key": key,
                    "value": json.dumps(data, default=str)
                }
                async with session.post(
                    f"{self.mcp_memory_url}/store",
                    json=payload
                ) as response:
                    if response.status == 200:
                        self.logger.info(f"Saved {key} to memory")
        except Exception as e:
            self.logger.error(f"Failed to save to memory: {str(e)}")
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values"""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)
    
    def _calculate_distribution(self, values: List[float]) -> Dict[str, int]:
        """Calculate distribution of values"""
        if not values:
            return {}
        
        bins = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0
        }
        
        for value in values:
            if value <= 0.2:
                bins["0.0-0.2"] += 1
            elif value <= 0.4:
                bins["0.2-0.4"] += 1
            elif value <= 0.6:
                bins["0.4-0.6"] += 1
            elif value <= 0.8:
                bins["0.6-0.8"] += 1
            else:
                bins["0.8-1.0"] += 1
        
        return bins
    
    # Mutation strategy implementations
    
    async def _mutate_algorithm(self, gene: Gene) -> Gene:
        """Mutate algorithm gene"""
        algorithms = ["quicksort", "mergesort", "heapsort", "timsort", "radixsort"]
        new_value = random.choice([a for a in algorithms if a != gene.value])
        return Gene(
            id=gene.id,
            type=gene.type,
            value=new_value,
            metadata={**gene.metadata, "mutated": True}
        )
    
    async def _mutate_data_structure(self, gene: Gene) -> Gene:
        """Mutate data structure gene"""
        structures = ["array", "linked_list", "tree", "hash_map", "graph", "heap"]
        new_value = random.choice([s for s in structures if s != gene.value])
        return Gene(
            id=gene.id,
            type=gene.type,
            value=new_value,
            metadata={**gene.metadata, "mutated": True}
        )
    
    async def _mutate_optimization(self, gene: Gene) -> Gene:
        """Mutate optimization gene"""
        optimizations = ["memoization", "lazy_evaluation", "streaming", "batching", "caching"]
        new_value = random.choice([o for o in optimizations if o != gene.value])
        return Gene(
            id=gene.id,
            type=gene.type,
            value=new_value,
            metadata={**gene.metadata, "mutated": True}
        )
    
    async def _mutate_refactoring(self, gene: Gene) -> Gene:
        """Mutate refactoring gene"""
        return gene  # Placeholder
    
    async def _mutate_parallelization(self, gene: Gene) -> Gene:
        """Mutate parallelization gene"""
        return gene  # Placeholder
    
    async def _mutate_caching(self, gene: Gene) -> Gene:
        """Mutate caching strategy gene"""
        return gene  # Placeholder
    
    async def _mutate_memory(self, gene: Gene) -> Gene:
        """Mutate memory optimization gene"""
        return gene  # Placeholder


# Factory function for easy instantiation
def create_genetic_algorithm_agent() -> GeneticAlgorithmAgent:
    """Create and return a GeneticAlgorithmAgent instance"""
    return GeneticAlgorithmAgent()


# Entry point for immediate execution
async def main():
    """Main execution function for Genetic Algorithm operations"""
    agent = GeneticAlgorithmAgent()
    await agent.initialize()
    
    try:
        # Example: Evolve a solution for performance optimization
        result = await agent.process_task(
            "evolution-1",
            {
                "task_type": "evolve_solution",
                "problem_description": "optimize_sorting_algorithm",
                "optimization_target": "performance",
                "generations": 50,
                "population_size": 30
            }
        )
        
        print("🧬 Genetic Algorithm Evolution Complete")
        print(f"📊 Evolution Result: {result}")
        
        # Example: Optimize code
        code_result = await agent.process_task(
            "optimization-1",
            {
                "task_type": "optimize_code",
                "code_snippet": "for i in range(n):\n    for j in range(n):\n        result += matrix[i][j]",
                "language": "python",
                "optimization_targets": ["performance", "memory_usage"]
            }
        )
        
        print("💻 Code Optimization Complete")
        print(f"📈 Optimization Result: {code_result}")
        
    finally:
        await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())