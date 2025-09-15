#!/usr/bin/env python3
"""
Reusable Evolutionary Components
Extracted from Genetic Algorithm Mode for use across multiple modes
Provides core genetic algorithm primitives: Gene, Chromosome, Population, FitnessFunction
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Dict, Optional, Tuple, Callable
import json
import hashlib
import random

class OptimizationTarget(Enum):
    """Optimization targets for genetic algorithms"""
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
        import random
        return random.uniform(0.6, 0.95)