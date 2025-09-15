
#!/usr/bin/env python3
"""
Genetic Algorithm Mode Agent - Evolutionary Code Optimization
Implements evolutionary algorithms for code optimization using the shared ModeFramework
"""

import asyncio
import json
import random
from typing import Any, Dict, List

from agents.core.mode_framework import ModeFramework, ModeConfig, ModePhase
from agents.core.evolutionary_components import (
    OptimizationTarget,
    MutationType,
    CrossoverStrategy,
    SelectionMethod,
    Gene,
    Chromosome,
    Population,
    EvolutionResult,
    FitnessFunction,
)

class GeneticAlgorithmModeConfig(ModeConfig):
    """Configuration for Genetic Algorithm Mode"""
    def __init__(self):
        super().__init__(
            mode_id="genetic-algorithm",
            mode_name="Genetic Algorithm Mode",
            version="1.1.0",  # Updated for framework integration
            description="Evolutionary code optimization using genetic algorithms",
            category="optimization",
            workflow_steps=[
                "initialization",
                "evaluation",
                "evolution",
                "optimization",
                "synthesis"
            ],
            model_phases={
                "initialization": "claude-opus-4.1",
                "evaluation": "deepseek-v3",
                "evolution": "grok-code-fast-1",
                "optimization": "google-flash-2.5",
                "synthesis": "claude-opus-4.1"
            },
            mcp_hooks=[
                "store_evolution_history",
                "retrieve_populations",
                "search_solutions",
                "read_code",
                "write_optimized_code",
                "backup_generations",
                "symbol_search",
                "dependency_analysis",
                "commit_optimizations"
            ],
            parameters={
                "default_population_size": 50,
                "default_generations": 100,
                "mutation_rate": 0.1,
                "crossover_rate": 0.7,
                "elitism_percentage": 0.1,
                "convergence_threshold": 0.001,
                "stagnation_limit": 10,
                "tournament_size": 3,
                "max_concurrent_tasks": 8
            },
            dependencies=[
                "agents.core.mode_framework",
                "agents.core.evolutionary_components"
            ]
        )

class GeneticAlgorithmMode(ModeFramework):
    """
    Genetic Algorithm Mode - Subclass of ModeFramework
    Uses shared framework for workflow execution and model routing
    """
    
    def __init__(self):
        mode_config = GeneticAlgorithmModeConfig()
        super().__init__(mode_config)
        
        # GA-specific state
        self.populations: Dict[str, Population] = {}
        self.evolution_history: Dict[str, List[Population]] = {}
        self.mutation_strategies: Dict[MutationType, callable] = {}
        self.fitness_functions: Dict[str, FitnessFunction] = {}
        
        # Evolution parameters (from config)
        self.default_population_size = self.mode_config.parameters["default_population_size"]
        self.default_generations = self.mode_config.parameters["default_generations"]
        self.default_mutation_rate = self.mode_config.parameters["mutation_rate"]
        self.default_crossover_rate = self.mode_config.parameters["crossover_rate"]
        self.convergence_threshold = self.mode_config.parameters["convergence_threshold"]
        self.stagnation_limit = self.mode_config.parameters["stagnation_limit"]
    
    async def _load_mode_components(self) -> None:
        """
        Load Genetic Algorithm specific components
        """
        # Initialize fitness functions using shared components
        self._initialize_fitness_functions()
        
        # Initialize mutation strategies
        self._initialize_mutation_strategies()
        
        # Register GA-specific phases
        self.workflow_engine.register_phase_handlers({
            ModePhase.INITIALIZATION: self._ga_initialize_phase,
            ModePhase.EVALUATION: self._ga_evaluate_phase,
            ModePhase.OPTIMIZATION: self._ga_optimize_phase,
            ModePhase.SYNTHESIS: self._ga_synthesize_phase
        })
        
        self.logger.info("Genetic Algorithm Mode components loaded")

    def _initialize_fitness_functions(self) -> None:
        """Initialize GA-specific fitness functions"""
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
        """Initialize GA-specific mutation strategies"""
        self.mutation_strategies = {
            MutationType.ALGORITHM_SWAP: self._mutate_algorithm,
            MutationType.DATA_STRUCTURE_CHANGE: self._mutate_data_structure,
            MutationType.OPTIMIZATION_TECHNIQUE: self._mutate_optimization,
            MutationType.REFACTORING: self._mutate_refactoring,
            MutationType.PARALLELIZATION: self._mutate_parallelization,
            MutationType.CACHING_STRATEGY: self._mutate_caching,
            MutationType.MEMORY_OPTIMIZATION: self._mutate_memory
        }

    # GA-specific phase handlers
    async def _ga_initialize_phase(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """GA initialization phase"""
        problem_description = input_data.get("problem_description", "unknown")
        population_size = input_data.get("population_size", self.default_population_size)
        
        # Initialize population using shared components
        population = await self._initialize_population(problem_description, population_size)
        
        # Store initial population
        self.populations[problem_description] = population
        
        return {
            "population": population,
            "initial_genes": [g.value for g in population.chromosomes[0].genes],
            "generation": 0
        }

    async def _ga_evaluate_phase(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """GA evaluation phase"""
        problem_description = input_data.get("problem_description")
        target = OptimizationTarget(input_data.get("optimization_target", "performance"))
        
        if problem_description not in self.populations:
            raise ValueError(f"Population not initialized for {problem_description}")
        
        population = self.populations[problem_description]
        fitness_function = self.fitness_functions.get(target.value)
        
        # Evaluate fitness for all chromosomes
        for chromosome in population.chromosomes:
            chromosome.fitness_score = await fitness_function.evaluate(chromosome)
        
        # Calculate statistics
        population.best_fitness = max(c.fitness_score for c in population.chromosomes)
        population.average_fitness = sum(c.fitness_score for c in population.chromosomes) / len(population.chromosomes)
        population.diversity_score = population.calculate_diversity()
        
        return {
            "fitness_scores": [c.fitness_score for c in population.chromosomes],
            "best_fitness": population.best_fitness,
            "average_fitness": population.average_fitness,
            "diversity_score": population.diversity_score
        }

    async def _ga_optimize_phase(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """GA evolution and optimization phase"""
        problem_description = input_data.get("problem_description")
        generations = input_data.get("generations", self.default_generations)
        
        if problem_description not in self.populations:
            raise ValueError(f"Population not initialized for {problem_description}")
        
        population = self.populations[problem_description]
        fitness_history = []
        diversity_history = []
        best_solution = None
        stagnation_counter = 0
        
        for generation in range(generations):
            # Evaluate fitness (already done in evaluation phase, but re-evaluate if needed)
            target = OptimizationTarget(input_data.get("optimization_target", "performance"))
            fitness_function = self.fitness_functions.get(target.value)
            for chromosome in population.chromosomes:
                if chromosome.fitness_score == 0.0:  # Only if not evaluated
                    chromosome.fitness_score = await fitness_function.evaluate(chromosome)
            
            # Track fitness history
            fitness_history.append(population.best_fitness)
            diversity_history.append(population.diversity_score)
            
            # Check for convergence
            if generation > 0:
                improvement = abs(fitness_history[-1] - fitness_history[-2])
                if improvement < self.convergence_threshold:
                    stagnation_counter += 1
                    if stagnation_counter >= self.stagnation_limit:
                        self.logger.info(f"Converged at generation {generation}")
                        break
                else:
                    stagnation_counter = 0
            
            # Get best solution
            current_best = max(population.chromosomes, key=lambda c: c.fitness_score)
            if best_solution is None or current_best.fitness_score > best_solution.fitness_score:
                best_solution = current_best
            
            # Create next generation using shared components
            population = await self._create_next_generation(
                population, SelectionMethod.TOURNAMENT, CrossoverStrategy.UNIFORM
            )
        
        # Store evolution history
        self.evolution_history.setdefault(problem_description, []).append(population)
        
        return {
            "final_population": population,
            "best_solution": best_solution,
            "generations_evolved": generation + 1,
            "fitness_history": fitness_history,
            "diversity_history": diversity_history
        }

    async def _ga_synthesize_phase(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """GA synthesis phase - combine and validate results"""
        problem_description = input_data.get("problem_description")
        
        if problem_description not in self.populations:
            raise ValueError(f"Population not initialized for {problem_description}")
        
        population = self.populations[problem_description]
        best_solution = max(population.chromosomes, key=lambda c: c.fitness_score)
        
        # Generate final code from best solution
        language = input_data.get("language", "python")
        optimized_code = await self._genes_to_code(best_solution.genes, language)
        
        # Calculate improvement
        initial_fitness = self.evolution_history[problem_description][0].best_fitness if self.evolution_history[problem_description] else 0
        final_fitness = best_solution.fitness_score
        improvement = ((final_fitness - initial_fitness) / initial_fitness * 100) if initial_fitness > 0 else 0
        
        # Create evolution result using shared components
        evolution_result = EvolutionResult(
            best_solution=best_solution,
            final_population=population,
            generations_evolved=len(self.evolution_history[problem_description]),
            fitness_history=[p.best_fitness for p in self.evolution_history[problem_description]],
            diversity_history=[p.diversity_score for p in self.evolution_history[problem_description]],
            optimization_target=OptimizationTarget(input_data.get("optimization_target", "performance")),
            achieved_improvement=improvement,
            evolution_time=0.0,  # Would be measured in real implementation
        )
        
        # Save to MCP memory
        await self.mcp_client.store(
            key=f"evolution_result_{problem_description}",
            value={
                "best_fitness": best_solution.fitness_score,
                "improvement": improvement,
                "optimized_code": optimized_code,
                "generation": population.generation
            }
        )
        
        return {
            "optimized_code": optimized_code,
            "evolution_result": evolution_result,
            "improvement_percentage": improvement,
            "final_fitness": best_solution.fitness_score
        }

    # GA-specific utility methods (retained from original)
    async def _initialize_population(
        self, problem_description: str, size: int
    ) -> Population:
        """Initialize a random population using shared components"""
        chromosomes = []
        
        for i in range(size):
            # Create random genes using shared Gene class
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
        """Create next generation using shared components"""
        new_chromosomes = []
        
        # Elitism - keep best solutions
        elite = population.get_elite(0.1)
        new_chromosomes.extend(elite)
        
        # Generate offspring using shared crossover/mutation
        while len(new_chromosomes) < len(population.chromosomes):
            # Select parents using shared selection
            parents = population.select_parents(selection_method, 2)
            
            # Crossover using shared method
            if random.random() < self.default_crossover_rate and len(parents) >= 2:
                child1, child2 = parents[0].crossover(parents[1], crossover_strategy)
                
                # Mutation using shared method
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

    async def _genes_to_code(self, genes: List[Gene], language: str) -> str:
        """Convert genes back to code - GA specific"""
        # Simplified implementation
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

    async def _parse_code_to_genes(self, code: str, language: str) -> List[Gene]:
        """Parse code snippet into genetic representation - GA specific"""
        genes = []
        
        # Simple parsing
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

    # Mutation strategy implementations (GA specific)
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
        new_value