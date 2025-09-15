#!/usr/bin/env python3
"""
Test harness for Genetic Algorithm Mode
Comprehensive test suite for evolutionary code optimization
"""

import asyncio
import unittest
import json
import random
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.specialized.genetic_algorithm_agent import (
    GeneticAlgorithmAgent,
    Gene,
    Chromosome,
    Population,
    EvolutionResult,
    FitnessFunction,
    OptimizationTarget,
    MutationType,
    CrossoverStrategy,
    SelectionMethod,
    create_genetic_algorithm_agent
)


class TestGene(unittest.TestCase):
    """Test Gene class functionality"""
    
    def test_gene_creation(self):
        """Test creating a gene"""
        gene = Gene(
            id="test_gene",
            type="algorithm",
            value="quicksort",
            metadata={"complexity": "O(nlogn)"},
            mutation_probability=0.1
        )
        
        self.assertEqual(gene.id, "test_gene")
        self.assertEqual(gene.type, "algorithm")
        self.assertEqual(gene.value, "quicksort")
        self.assertEqual(gene.metadata["complexity"], "O(nlogn)")
        self.assertEqual(gene.mutation_probability, 0.1)
    
    def test_gene_mutation(self):
        """Test gene mutation"""
        gene = Gene(
            id="test_gene",
            type="algorithm",
            value="quicksort",
            mutation_probability=1.0  # Always mutate for testing
        )
        
        mutated = gene.mutate()
        
        # Should have same ID and type but different value
        self.assertEqual(mutated.id, gene.id)
        self.assertEqual(mutated.type, gene.type)
        self.assertNotEqual(mutated.value, gene.value)
        self.assertTrue(mutated.metadata.get("mutated"))
    
    def test_gene_mutation_probability(self):
        """Test that mutation respects probability"""
        gene = Gene(
            id="test_gene",
            type="algorithm",
            value="quicksort",
            mutation_probability=0.0  # Never mutate
        )
        
        mutated = gene.mutate()
        
        # Should be unchanged
        self.assertEqual(mutated.value, gene.value)
        self.assertFalse(mutated.metadata.get("mutated"))


class TestChromosome(unittest.TestCase):
    """Test Chromosome class functionality"""
    
    def setUp(self):
        """Set up test chromosomes"""
        self.genes = [
            Gene(id=f"gene_{i}", type="algorithm", value=f"algo_{i}")
            for i in range(5)
        ]
        
        self.chromosome = Chromosome(
            id="test_chr",
            genes=self.genes,
            fitness_score=0.8,
            generation=1
        )
    
    def test_chromosome_creation(self):
        """Test creating a chromosome"""
        self.assertEqual(self.chromosome.id, "test_chr")
        self.assertEqual(len(self.chromosome.genes), 5)
        self.assertEqual(self.chromosome.fitness_score, 0.8)
        self.assertEqual(self.chromosome.generation, 1)
    
    def test_chromosome_hash(self):
        """Test chromosome hash calculation"""
        hash1 = self.chromosome.calculate_hash()
        
        # Same genes should produce same hash
        chr2 = Chromosome(id="chr2", genes=self.genes)
        hash2 = chr2.calculate_hash()
        
        self.assertEqual(hash1, hash2)
        
        # Different genes should produce different hash
        different_genes = [
            Gene(id=f"gene_{i}", type="algorithm", value=f"different_{i}")
            for i in range(5)
        ]
        chr3 = Chromosome(id="chr3", genes=different_genes)
        hash3 = chr3.calculate_hash()
        
        self.assertNotEqual(hash1, hash3)
    
    def test_single_point_crossover(self):
        """Test single point crossover"""
        other_genes = [
            Gene(id=f"gene_b_{i}", type="data_structure", value=f"struct_{i}")
            for i in range(5)
        ]
        other = Chromosome(id="other_chr", genes=other_genes, generation=1)
        
        child1, child2 = self.chromosome.crossover(other, CrossoverStrategy.SINGLE_POINT)
        
        # Children should have correct generation
        self.assertEqual(child1.generation, 2)
        self.assertEqual(child2.generation, 2)
        
        # Children should have correct parents
        self.assertEqual(child1.parents, (self.chromosome.id, other.id))
        self.assertEqual(child2.parents, (self.chromosome.id, other.id))
        
        # Children should have mixed genes
        self.assertEqual(len(child1.genes), 5)
        self.assertEqual(len(child2.genes), 5)
    
    def test_two_point_crossover(self):
        """Test two point crossover"""
        other_genes = [
            Gene(id=f"gene_b_{i}", type="data_structure", value=f"struct_{i}")
            for i in range(5)
        ]
        other = Chromosome(id="other_chr", genes=other_genes)
        
        child1, child2 = self.chromosome.crossover(other, CrossoverStrategy.TWO_POINT)
        
        # Children should have genes from both parents
        self.assertEqual(len(child1.genes), 5)
        self.assertEqual(len(child2.genes), 5)
    
    def test_uniform_crossover(self):
        """Test uniform crossover"""
        other_genes = [
            Gene(id=f"gene_b_{i}", type="data_structure", value=f"struct_{i}")
            for i in range(5)
        ]
        other = Chromosome(id="other_chr", genes=other_genes)
        
        child1, child2 = self.chromosome.crossover(other, CrossoverStrategy.UNIFORM)
        
        # Each gene should come from one parent or the other
        for i in range(len(child1.genes)):
            self.assertTrue(
                child1.genes[i] in self.genes or child1.genes[i] in other_genes
            )
    
    def test_chromosome_mutation(self):
        """Test chromosome mutation"""
        mutated = self.chromosome.mutate(mutation_rate=0.5)
        
        # Should have new ID
        self.assertTrue(mutated.id.startswith("mut_"))
        
        # Should have same number of genes
        self.assertEqual(len(mutated.genes), len(self.chromosome.genes))
        
        # Should be marked as mutated
        self.assertTrue(mutated.metadata.get("mutated"))


class TestPopulation(unittest.TestCase):
    """Test Population class functionality"""
    
    def setUp(self):
        """Set up test population"""
        self.chromosomes = []
        for i in range(10):
            genes = [
                Gene(id=f"gene_{j}", type="algorithm", value=f"algo_{i}_{j}")
                for j in range(3)
            ]
            chromosome = Chromosome(
                id=f"chr_{i}",
                genes=genes,
                fitness_score=random.random()
            )
            self.chromosomes.append(chromosome)
        
        self.population = Population(
            generation=1,
            chromosomes=self.chromosomes
        )
    
    def test_population_creation(self):
        """Test creating a population"""
        self.assertEqual(self.population.generation, 1)
        self.assertEqual(len(self.population.chromosomes), 10)
    
    def test_diversity_calculation(self):
        """Test genetic diversity calculation"""
        diversity = self.population.calculate_diversity()
        
        # All chromosomes are unique, so diversity should be 1.0
        self.assertEqual(diversity, 1.0)
        
        # Create population with duplicates
        duplicate_genes = [
            Gene(id=f"gene_{j}", type="algorithm", value=f"same_{j}")
            for j in range(3)
        ]
        
        duplicate_chromosomes = [
            Chromosome(id=f"dup_{i}", genes=duplicate_genes)
            for i in range(10)
        ]
        
        dup_population = Population(
            generation=1,
            chromosomes=duplicate_chromosomes
        )
        
        # All chromosomes are identical, so diversity should be 0.1
        self.assertEqual(dup_population.calculate_diversity(), 0.1)
    
    def test_get_elite(self):
        """Test getting elite chromosomes"""
        elite = self.population.get_elite(0.2)
        
        # Should return top 20% (2 chromosomes)
        self.assertEqual(len(elite), 2)
        
        # Elite should be sorted by fitness
        self.assertGreaterEqual(elite[0].fitness_score, elite[1].fitness_score)
    
    def test_tournament_selection(self):
        """Test tournament selection"""
        parents = self.population.select_parents(SelectionMethod.TOURNAMENT, count=2)
        
        self.assertEqual(len(parents), 2)
        
        # Parents should be from the population
        for parent in parents:
            self.assertIn(parent, self.population.chromosomes)
    
    def test_roulette_wheel_selection(self):
        """Test roulette wheel selection"""
        parents = self.population.select_parents(SelectionMethod.ROULETTE_WHEEL, count=3)
        
        self.assertEqual(len(parents), 3)
        
        # Parents should be from the population
        for parent in parents:
            self.assertIn(parent, self.population.chromosomes)
    
    def test_elitism_selection(self):
        """Test elitism selection"""
        parents = self.population.select_parents(SelectionMethod.ELITISM, count=2)
        
        self.assertEqual(len(parents), 2)
        
        # Should return the best chromosomes
        sorted_chromosomes = sorted(
            self.population.chromosomes,
            key=lambda c: c.fitness_score,
            reverse=True
        )
        self.assertEqual(parents[0], sorted_chromosomes[0])


class TestFitnessFunction(unittest.TestCase):
    """Test FitnessFunction class"""
    
    def setUp(self):
        """Set up test fitness function"""
        self.fitness_func = FitnessFunction(
            name="test_fitness",
            target=OptimizationTarget.PERFORMANCE,
            weight=1.0
        )
    
    async def test_performance_evaluation(self):
        """Test performance fitness evaluation"""
        genes = [
            Gene(id="gene_1", type="algorithm", value="quicksort"),
            Gene(id="gene_2", type="optimization", value="memoization")
        ]
        chromosome = Chromosome(id="test_chr", genes=genes)
        
        score = await self.fitness_func.evaluate(chromosome)
        
        # Should return a score between 0 and 1
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
    
    async def test_memory_evaluation(self):
        """Test memory usage fitness evaluation"""
        fitness_func = FitnessFunction(
            name="memory_fitness",
            target=OptimizationTarget.MEMORY_USAGE
        )
        
        genes = [
            Gene(id="gene_1", type="data_structure", value="array"),
            Gene(id="gene_2", type="data_structure", value="hash_map")
        ]
        chromosome = Chromosome(id="test_chr", genes=genes)
        
        score = await fitness_func.evaluate(chromosome)
        
        # Should return a score between 0 and 1
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
    
    async def test_custom_evaluator(self):
        """Test custom fitness evaluator"""
        async def custom_evaluator(chromosome: Chromosome) -> float:
            return 0.42
        
        fitness_func = FitnessFunction(
            name="custom",
            target=OptimizationTarget.PERFORMANCE,
            evaluator=custom_evaluator
        )
        
        chromosome = Chromosome(id="test_chr", genes=[])
        score = await fitness_func.evaluate(chromosome)
        
        self.assertEqual(score, 0.42)


class TestGeneticAlgorithmAgent(unittest.IsolatedAsyncioTestCase):
    """Test GeneticAlgorithmAgent class"""
    
    async def asyncSetUp(self):
        """Set up test agent"""
        self.agent = GeneticAlgorithmAgent()
        
        # Mock MCP servers
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value.status = 200
            await self.agent.initialize()
    
    async def asyncTearDown(self):
        """Clean up test agent"""
        await self.agent.shutdown()
    
    async def test_agent_initialization(self):
        """Test agent initialization"""
        self.assertEqual(self.agent.config.agent_id, "genetic-algorithm-agent")
        self.assertEqual(self.agent.config.agent_name, "Genetic Algorithm Optimization Agent")
        self.assertEqual(self.agent.config.max_concurrent_tasks, 8)
        
        # Check fitness functions initialized
        self.assertIn(OptimizationTarget.PERFORMANCE.value, self.agent.fitness_functions)
        self.assertIn(OptimizationTarget.MEMORY_USAGE.value, self.agent.fitness_functions)
    
    async def test_evolve_solution_task(self):
        """Test evolve_solution task processing"""
        task_data = {
            "task_type": "evolve_solution",
            "problem_description": "test_problem",
            "optimization_target": "performance",
            "generations": 5,
            "population_size": 10
        }
        
        result = await self.agent.process_task("test_task_1", task_data)
        
        self.assertEqual(result["task_type"], "evolve_solution")
        self.assertIn("best_fitness", result)
        self.assertIn("generations_evolved", result)
        self.assertIn("improvement", result)
    
    async def test_optimize_code_task(self):
        """Test optimize_code task processing"""
        task_data = {
            "task_type": "optimize_code",
            "code_snippet": "for i in range(n): result += i",
            "language": "python",
            "optimization_targets": ["performance", "memory_usage"]
        }
        
        result = await self.agent.process_task("test_task_2", task_data)
        
        self.assertEqual(result["task_type"], "optimize_code")
        self.assertIn("optimized_code", result)
        self.assertIn("improvements", result)
    
    async def test_analyze_population_task(self):
        """Test analyze_population task processing"""
        task_data = {
            "task_type": "analyze_population",
            "chromosomes": [
                {
                    "id": "chr_1",
                    "genes": [
                        {"id": "gene_1", "type": "algorithm", "value": "quicksort"}
                    ],
                    "generation": 1
                }
            ],
            "generation": 1,
            "optimization_target": "performance"
        }
        
        result = await self.agent.process_task("test_task_3", task_data)
        
        self.assertEqual(result["task_type"], "analyze_population")
        self.assertIn("best_fitness", result)
        self.assertIn("average_fitness", result)
        self.assertIn("diversity_score", result)
    
    async def test_evolution_convergence(self):
        """Test that evolution converges"""
        # Create a simple problem with known optimal solution
        result = await self.agent.evolve_solution(
            problem_description="test_convergence",
            optimization_target=OptimizationTarget.PERFORMANCE,
            generations=20,
            population_size=10
        )
        
        # Check that evolution produced results
        self.assertIsNotNone(result.best_solution)
        self.assertGreater(result.generations_evolved, 0)
        self.assertGreater(len(result.fitness_history), 0)
        
        # Check that fitness improved over time
        if len(result.fitness_history) > 1:
            # Later generations should have better or equal fitness
            self.assertGreaterEqual(
                result.fitness_history[-1],
                result.fitness_history[0]
            )
    
    async def test_parallel_optimization(self):
        """Test parallel optimization of multiple targets"""
        code = "def process(data): return [x*2 for x in data]"
        
        result = await self.agent.optimize_code(
            code_snippet=code,
            language="python",
            optimization_targets=[
                OptimizationTarget.PERFORMANCE,
                OptimizationTarget.MEMORY_USAGE,
                OptimizationTarget.CODE_COMPLEXITY
            ]
        )
        
        self.assertIn("optimized_code", result)
        self.assertIn("improvements", result)
        
        # Should have improvements for each target
        self.assertIn("performance", result["improvements"])
        self.assertIn("memory_usage", result["improvements"])
        self.assertIn("code_complexity", result["improvements"])
    
    async def test_error_handling(self):
        """Test error handling for invalid tasks"""
        # Test invalid task type
        with self.assertRaises(ValueError):
            await self.agent.process_task(
                "test_error",
                {"task_type": "invalid_type"}
            )
        
        # Test missing required fields
        with self.assertRaises(ValueError):
            await self.agent.process_task(
                "test_error",
                {}  # No task_type
            )


class TestIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for the complete genetic algorithm workflow"""
    
    async def test_end_to_end_evolution(self):
        """Test complete evolution workflow"""
        agent = GeneticAlgorithmAgent()
        
        # Mock MCP servers
        with patch('aiohttp.ClientSession'):
            await agent.initialize()
            
            # Run evolution
            result = await agent.evolve_solution(
                problem_description="optimize_sorting",
                optimization_target=OptimizationTarget.PERFORMANCE,
                generations=10,
                population_size=20
            )
            
            # Verify results
            self.assertIsInstance(result, EvolutionResult)
            self.assertIsNotNone(result.best_solution)
            self.assertGreater(result.best_solution.fitness_score, 0)
            self.assertEqual(len(result.fitness_history), result.generations_evolved)
            
            await agent.shutdown()
    
    async def test_code_optimization_workflow(self):
        """Test code optimization workflow"""
        agent = GeneticAlgorithmAgent()
        
        with patch('aiohttp.ClientSession'):
            await agent.initialize()
            
            code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
"""
            
            result = await agent.optimize_code(
                code_snippet=code,
                language="python",
                optimization_targets=[OptimizationTarget.PERFORMANCE]
            )
            
            self.assertIn("optimized_code", result)
            self.assertIn("improvements", result)
            self.assertIn("best_solution", result)
            
            await agent.shutdown()
    
    async def test_factory_function(self):
        """Test factory function creation"""
        agent = create_genetic_algorithm_agent()
        
        self.assertIsInstance(agent, GeneticAlgorithmAgent)
        self.assertEqual(agent.config.agent_id, "genetic-algorithm-agent")


class TestModeConfiguration(unittest.TestCase):
    """Test mode configuration loading and validation"""
    
    def test_mode_config_structure(self):
        """Test that mode configuration file has correct structure"""
        config_path = "modes/genetic_algorithm_mode.json"
        
        # Check if file exists
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Verify required sections
            self.assertIn("mode", config)
            self.assertIn("configuration", config)
            self.assertIn("capabilities", config)
            self.assertIn("workflows", config)
            self.assertIn("fitness_functions", config)
            
            # Verify mode metadata
            mode = config["mode"]
            self.assertEqual(mode["id"], "genetic-algorithm")
            self.assertEqual(mode["name"], "Genetic Algorithm Mode")
            
            # Verify MCP integration
            mcp = config["configuration"]["mcp_integration"]
            self.assertIn("memory_server", mcp)
            self.assertIn("filesystem_server", mcp)
            self.assertIn("git_server", mcp)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGene))
    suite.addTests(loader.loadTestsFromTestCase(TestChromosome))
    suite.addTests(loader.loadTestsFromTestCase(TestPopulation))
    suite.addTests(loader.loadTestsFromTestCase(TestFitnessFunction))
    suite.addTests(loader.loadTestsFromTestCase(TestGeneticAlgorithmAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestModeConfiguration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run async tests properly
    success = run_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)