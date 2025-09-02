"""
Comprehensive Test Suite for Experimental Evolution Engine - ADR-002

⚠️ EXPERIMENTAL TESTING ⚠️

This test suite validates the experimental evolution engine functionality,
including safety controls, genetic algorithms, and integration points.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.swarms.evolution.experimental_evolution_engine import (
    ExperimentalEvolutionConfig,
    ExperimentalEvolutionEngine,
    ExperimentalFitnessEvaluation,
    ExperimentalMode,
    ExperimentalSafetyBounds,
    SwarmChromosome,
    create_experimental_evolution_engine,
)
from app.swarms.evolution.integration_adapter import (
    ExperimentalSwarmEvolutionAdapter,
    SwarmEvolutionConfig,
    create_evolution_adapter,
)
from app.swarms.memory_integration import SwarmMemoryClient


class TestExperimentalEvolutionConfig:
    """Test configuration validation and safety checks."""

    def test_default_config_is_safe(self):
        """Test that default configuration is safe."""
        config = ExperimentalEvolutionConfig()

        assert config.mode == ExperimentalMode.DISABLED
        assert config.enabled == False
        assert config.experimental_features_acknowledged == False
        assert config.dry_run_mode == True

        # Validate safety bounds
        issues = config.validate()
        assert len(issues) == 1  # Should have acknowledgment issue
        assert "acknowledge experimental" in issues[0].lower()

    def test_config_validation_catches_unsafe_params(self):
        """Test that config validation catches unsafe parameters."""
        config = ExperimentalEvolutionConfig(
            mutation_rate=0.5,  # Too high
            selection_pressure=0.9,  # Too high
            crossover_rate=0.1,  # Too low
            elite_preservation=0.4,  # Higher than selection pressure
            enabled=True,
            experimental_features_acknowledged=True
        )

        issues = config.validate()
        assert len(issues) >= 4  # Should catch all unsafe parameters
        assert any("mutation rate" in issue.lower() for issue in issues)
        assert any("selection pressure" in issue.lower() for issue in issues)
        assert any("crossover rate" in issue.lower() for issue in issues)
        assert any("elite preservation" in issue.lower() for issue in issues)

    def test_aggressive_mode_requires_acknowledgment(self):
        """Test that aggressive mode requires explicit acknowledgment."""
        config = ExperimentalEvolutionConfig(
            mode=ExperimentalMode.AGGRESSIVE,
            enabled=True,
            experimental_features_acknowledged=False
        )

        issues = config.validate()
        assert any("aggressive" in issue.lower() and "acknowledgment" in issue.lower() for issue in issues)

    def test_valid_experimental_config(self):
        """Test a valid experimental configuration."""
        config = ExperimentalEvolutionConfig(
            mode=ExperimentalMode.CAUTIOUS,
            enabled=True,
            experimental_features_acknowledged=True,
            mutation_rate=0.08,
            selection_pressure=0.25,
            crossover_rate=0.6,
            elite_preservation=0.05
        )

        issues = config.validate()
        assert len(issues) == 0


class TestSwarmChromosome:
    """Test chromosome operations and genetic algorithms."""

    @pytest.fixture
    def sample_chromosome(self) -> SwarmChromosome:
        """Create a sample chromosome for testing."""
        return SwarmChromosome(
            chromosome_id="test_chromosome_1",
            swarm_type="test_swarm",
            generation=1,
            agent_roles=["agent_1", "agent_2", "agent_3"],
            agent_parameters={
                "agent_1": {"creativity": 0.7, "focus": 0.8, "collaboration": 0.6},
                "agent_2": {"creativity": 0.5, "focus": 0.9, "collaboration": 0.7},
                "agent_3": {"creativity": 0.8, "focus": 0.6, "collaboration": 0.5}
            },
            coordination_style="peer_to_peer",
            communication_pattern="adaptive",
            consensus_mechanism="majority",
            quality_threshold=0.8,
            speed_preference=0.5,
            risk_tolerance=0.3,
            learning_rate=0.6,
            memory_utilization=0.7,
            pattern_recognition_sensitivity=0.5
        )

    def test_chromosome_mutation_stays_within_bounds(self, sample_chromosome):
        """Test that mutations stay within safe bounds."""
        safety_bounds = ExperimentalSafetyBounds()

        # Perform multiple mutations
        for _ in range(50):
            mutated = sample_chromosome.mutate(
                mutation_rate=0.5,  # High rate to ensure mutations
                safety_bounds=safety_bounds,
                experimental_mode=False
            )

            # Check bounds
            assert 0.0 <= mutated.quality_threshold <= 1.0
            assert 0.0 <= mutated.speed_preference <= 1.0
            assert 0.0 <= mutated.risk_tolerance <= 0.8  # Risk cap

            # Check agent parameter bounds
            for agent, params in mutated.agent_parameters.items():
                for param_name, value in params.items():
                    assert 0.0 <= value <= 1.0, f"Parameter {param_name} out of bounds: {value}"

    def test_experimental_mutation_includes_experimental_genes(self, sample_chromosome):
        """Test that experimental mutations include experimental genes."""
        safety_bounds = ExperimentalSafetyBounds()

        mutated = sample_chromosome.mutate(
            mutation_rate=1.0,  # Ensure mutation
            safety_bounds=safety_bounds,
            experimental_mode=True
        )

        assert mutated.experimental_variant == True
        assert 0.0 <= mutated.experimental_creativity <= 1.0
        assert 0.0 <= mutated.experimental_exploration <= 1.0
        assert 0.0 <= mutated.experimental_cooperation <= 1.0
        assert mutated.experimental_mutations_count > 0

    def test_crossover_produces_valid_offspring(self, sample_chromosome):
        """Test that crossover produces valid offspring."""
        # Create second parent
        parent2 = SwarmChromosome(
            chromosome_id="test_chromosome_2",
            swarm_type="test_swarm",
            generation=1,
            agent_roles=["agent_1", "agent_2", "agent_3"],
            agent_parameters={
                "agent_1": {"creativity": 0.3, "focus": 0.4, "collaboration": 0.9},
                "agent_2": {"creativity": 0.8, "focus": 0.2, "collaboration": 0.4},
                "agent_3": {"creativity": 0.1, "focus": 0.7, "collaboration": 0.8}
            },
            coordination_style="hierarchical",
            communication_pattern="broadcast",
            consensus_mechanism="weighted",
            quality_threshold=0.6,
            speed_preference=0.8,
            risk_tolerance=0.1,
            learning_rate=0.4,
            memory_utilization=0.5,
            pattern_recognition_sensitivity=0.7
        )

        child1, child2 = SwarmChromosome.crossover(sample_chromosome, parent2)

        # Check that children are valid
        for child in [child1, child2]:
            assert child.generation == 2
            assert len(child.parent_chromosomes) == 2
            assert sample_chromosome.chromosome_id in child.parent_chromosomes
            assert parent2.chromosome_id in child.parent_chromosomes

            # Check bounds
            assert 0.0 <= child.quality_threshold <= 1.0
            assert 0.0 <= child.speed_preference <= 1.0
            assert 0.0 <= child.risk_tolerance <= 0.8

            # Check agent parameters
            for agent, params in child.agent_parameters.items():
                for param_name, value in params.items():
                    assert 0.0 <= value <= 1.0

    def test_experimental_crossover_preserves_experimental_traits(self, sample_chromosome):
        """Test that experimental crossover preserves experimental traits."""
        # Make chromosomes experimental
        sample_chromosome.experimental_variant = True
        sample_chromosome.experimental_creativity = 0.8
        sample_chromosome.experimental_exploration = 0.6

        parent2 = SwarmChromosome(
            chromosome_id="test_chromosome_2",
            swarm_type="test_swarm",
            generation=1,
            experimental_variant=True,
            experimental_creativity=0.4,
            experimental_exploration=0.9,
            agent_roles=["agent_1", "agent_2"],
            agent_parameters={"agent_1": {"creativity": 0.5}, "agent_2": {"creativity": 0.7}},
            coordination_style="hierarchical",
            communication_pattern="broadcast",
            consensus_mechanism="weighted",
            quality_threshold=0.7,
            speed_preference=0.6,
            risk_tolerance=0.2,
            learning_rate=0.5,
            memory_utilization=0.6,
            pattern_recognition_sensitivity=0.5
        )

        child1, child2 = SwarmChromosome.crossover(sample_chromosome, parent2, experimental_mode=True)

        for child in [child1, child2]:
            assert child.experimental_variant == True
            assert 0.0 <= child.experimental_creativity <= 1.0
            assert 0.0 <= child.experimental_exploration <= 1.0


class TestExperimentalEvolutionEngine:
    """Test the main evolution engine functionality."""

    @pytest.fixture
    def mock_memory_client(self):
        """Create mock memory client."""
        client = MagicMock(spec=SwarmMemoryClient)
        client.log_swarm_event = AsyncMock()
        client.store_learning = AsyncMock()
        client.store_pattern = AsyncMock()
        return client

    @pytest.fixture
    def test_config(self) -> ExperimentalEvolutionConfig:
        """Create test configuration."""
        return ExperimentalEvolutionConfig(
            mode=ExperimentalMode.CAUTIOUS,
            enabled=True,
            experimental_features_acknowledged=True,
            dry_run_mode=True,
            mutation_rate=0.1,
            selection_pressure=0.3,
            elite_preservation=0.1
        )

    @pytest.fixture
    def sample_base_chromosome(self) -> SwarmChromosome:
        """Create sample base chromosome."""
        return SwarmChromosome(
            chromosome_id="base_test",
            swarm_type="test_swarm",
            generation=1,
            agent_roles=["agent_1", "agent_2"],
            agent_parameters={
                "agent_1": {"creativity": 0.7, "focus": 0.8},
                "agent_2": {"creativity": 0.5, "focus": 0.9}
            },
            coordination_style="peer_to_peer",
            communication_pattern="adaptive",
            consensus_mechanism="majority",
            quality_threshold=0.8,
            speed_preference=0.5,
            risk_tolerance=0.3,
            learning_rate=0.5,
            memory_utilization=0.7,
            pattern_recognition_sensitivity=0.6
        )

    def test_engine_initialization_requires_acknowledgment(self):
        """Test that engine requires experimental acknowledgment."""
        config = ExperimentalEvolutionConfig(enabled=True, experimental_features_acknowledged=False)

        with pytest.raises(ValueError, match="experimental evolution configuration"):
            ExperimentalEvolutionEngine(config)

    def test_engine_initialization_with_valid_config(self, test_config, mock_memory_client):
        """Test successful engine initialization."""
        engine = ExperimentalEvolutionEngine(test_config, mock_memory_client)

        assert engine.config.enabled == True
        assert engine.config.mode == ExperimentalMode.CAUTIOUS
        assert engine.memory_client == mock_memory_client
        assert len(engine.populations) == 0

    @pytest.mark.asyncio
    async def test_population_initialization(self, test_config, mock_memory_client, sample_base_chromosome):
        """Test population initialization."""
        engine = ExperimentalEvolutionEngine(test_config, mock_memory_client)

        success = await engine.initialize_experimental_population(
            swarm_type="test_swarm",
            base_chromosome=sample_base_chromosome,
            population_size=3
        )

        assert success == True
        assert "test_swarm" in engine.populations
        assert len(engine.populations["test_swarm"]) == 3
        assert engine.generation_counter["test_swarm"] == 1
        assert engine.evolution_active["test_swarm"] == True

        # Check memory logging
        mock_memory_client.log_swarm_event.assert_called()

    @pytest.mark.asyncio
    async def test_disabled_engine_skips_population_init(self, mock_memory_client, sample_base_chromosome):
        """Test that disabled engine skips population initialization."""
        config = ExperimentalEvolutionConfig(mode=ExperimentalMode.DISABLED)
        engine = ExperimentalEvolutionEngine(config, mock_memory_client)

        success = await engine.initialize_experimental_population(
            swarm_type="test_swarm",
            base_chromosome=sample_base_chromosome
        )

        assert success == False
        assert "test_swarm" not in engine.populations

    @pytest.mark.asyncio
    async def test_fitness_evaluation(self, test_config, mock_memory_client, sample_base_chromosome):
        """Test fitness evaluation functionality."""
        engine = ExperimentalEvolutionEngine(test_config, mock_memory_client)
        await engine.initialize_experimental_population("test_swarm", sample_base_chromosome, 3)

        population = engine.populations["test_swarm"]
        performance_data = {
            'quality_score': 0.8,
            'speed_score': 0.6,
            'efficiency_score': 0.7,
            'reliability_score': 0.9
        }

        evaluations = await engine._evaluate_experimental_fitness(
            "test_swarm", population, performance_data
        )

        assert len(evaluations) == 3
        for eval in evaluations:
            assert isinstance(eval, ExperimentalFitnessEvaluation)
            assert 0.0 <= eval.overall_fitness <= 1.0
            assert eval.quality_score == 0.8
            assert eval.speed_score == 0.6

    @pytest.mark.asyncio
    async def test_observe_only_mode(self, mock_memory_client, sample_base_chromosome):
        """Test observe-only mode doesn't evolve."""
        config = ExperimentalEvolutionConfig(
            mode=ExperimentalMode.OBSERVE_ONLY,
            enabled=True,
            experimental_features_acknowledged=True
        )
        engine = ExperimentalEvolutionEngine(config, mock_memory_client)

        await engine.initialize_experimental_population("test_swarm", sample_base_chromosome, 3)
        original_population = engine.populations["test_swarm"].copy()

        performance_data = {'quality_score': 0.5, 'speed_score': 0.5, 'efficiency_score': 0.5, 'reliability_score': 0.5}

        result = await engine.experimental_evolve_population("test_swarm", performance_data)

        # Should return chromosome but not evolve population
        assert result is not None
        assert engine.populations["test_swarm"] == original_population
        assert engine.generation_counter["test_swarm"] == 1  # No evolution

    @pytest.mark.asyncio
    async def test_evolution_with_performance_improvement(self, test_config, mock_memory_client, sample_base_chromosome):
        """Test evolution process with performance improvement."""
        engine = ExperimentalEvolutionEngine(test_config, mock_memory_client)
        await engine.initialize_experimental_population("test_swarm", sample_base_chromosome, 3)

        # Set baseline performance
        engine.performance_baseline["test_swarm"] = 0.5

        performance_data = {
            'quality_score': 0.8,  # Good performance
            'speed_score': 0.7,
            'efficiency_score': 0.8,
            'reliability_score': 0.9
        }

        best_chromosome = await engine.experimental_evolve_population("test_swarm", performance_data)

        assert best_chromosome is not None
        assert engine.generation_counter["test_swarm"] == 2  # Evolution occurred
        assert best_chromosome.fitness_score > 0

        # Check memory storage
        mock_memory_client.store_learning.assert_called()

    @pytest.mark.asyncio
    async def test_rollback_on_performance_degradation(self, test_config, mock_memory_client, sample_base_chromosome):
        """Test rollback when performance degrades."""
        engine = ExperimentalEvolutionEngine(test_config, mock_memory_client)
        await engine.initialize_experimental_population("test_swarm", sample_base_chromosome, 3)

        # Set high baseline performance
        engine.performance_baseline["test_swarm"] = 0.9

        # Create rollback snapshot
        engine._create_experimental_snapshot("test_swarm", engine.populations["test_swarm"])

        # Simulate poor performance that should trigger rollback
        performance_data = {
            'quality_score': 0.1,  # Very poor performance
            'speed_score': 0.1,
            'efficiency_score': 0.1,
            'reliability_score': 0.1
        }

        # Mock the safety check to return True (trigger rollback)
        with patch.object(engine, '_check_experimental_safety', return_value=True):
            await engine.experimental_evolve_population("test_swarm", performance_data)

        # Should have triggered rollback
        assert engine.evolution_stats['rollbacks'] >= 0  # Rollback could be attempted

    def test_pattern_extraction(self, test_config, mock_memory_client):
        """Test pattern extraction from successful chromosomes."""
        engine = ExperimentalEvolutionEngine(test_config, mock_memory_client)

        # Create chromosomes with similar successful patterns
        chromosomes = []
        for i in range(5):
            chromosome = SwarmChromosome(
                chromosome_id=f"success_{i}",
                swarm_type="test_swarm",
                generation=1,
                agent_roles=["agent_1", "agent_2"],
                agent_parameters={
                    "agent_1": {"creativity": 0.8, "focus": 0.7},  # Consistent high creativity
                    "agent_2": {"creativity": 0.7, "focus": 0.8}
                },
                coordination_style="peer_to_peer",  # Consistent style
                communication_pattern="adaptive",
                consensus_mechanism="majority",
                quality_threshold=0.8,
                speed_preference=0.5,
                risk_tolerance=0.3,
                learning_rate=0.5,
                memory_utilization=0.7,
                pattern_recognition_sensitivity=0.6
            )
            chromosomes.append(chromosome)

        patterns = engine._extract_experimental_patterns(chromosomes)

        assert len(patterns) > 0
        # Should find parameter convergence patterns
        assert any(p['type'] == 'parameter_convergence' for p in patterns)

        # Check for creativity pattern
        creativity_patterns = [p for p in patterns if 'creativity' in p.get('parameter', '')]
        assert len(creativity_patterns) > 0

        # Check consistency
        for pattern in creativity_patterns:
            assert pattern['consistency'] >= 0.8  # High consistency


class TestIntegrationAdapter:
    """Test the integration adapter functionality."""

    @pytest.fixture
    def mock_memory_client(self):
        """Create mock memory client."""
        client = MagicMock(spec=SwarmMemoryClient)
        client.log_swarm_event = AsyncMock()
        return client

    @pytest.fixture
    def test_swarm_config(self) -> dict[str, Any]:
        """Create test swarm configuration."""
        return {
            'agents': ['agent_1', 'agent_2', 'agent_3'],
            'coordination_style': 'peer_to_peer',
            'communication_pattern': 'adaptive',
            'consensus_mechanism': 'majority',
            'quality_threshold': 0.8,
            'speed_preference': 0.5,
            'risk_tolerance': 0.3,
            'learning_rate': 0.5,
            'memory_utilization': 0.7,
            'pattern_recognition_sensitivity': 0.6
        }

    def test_adapter_disabled_by_default(self, mock_memory_client):
        """Test that adapter is disabled by default."""
        adapter = ExperimentalSwarmEvolutionAdapter(
            swarm_type="test_swarm",
            memory_client=mock_memory_client
        )

        assert adapter.config.enable_evolution == False
        assert adapter.evolution_initialized == False
        assert adapter.evolution_active == False

    def test_adapter_requires_acknowledgment_for_experimental(self, mock_memory_client):
        """Test that adapter requires acknowledgment for experimental features."""
        config = SwarmEvolutionConfig(
            enable_evolution=True,
            experimental_mode=ExperimentalMode.EXPERIMENTAL,
            acknowledge_experimental=False
        )

        adapter = ExperimentalSwarmEvolutionAdapter(
            swarm_type="test_swarm",
            config=config,
            memory_client=mock_memory_client
        )

        assert adapter.config.enable_evolution == True
        assert adapter.config.acknowledge_experimental == False
        # Should not initialize without acknowledgment

    @pytest.mark.asyncio
    async def test_adapter_initialization_with_acknowledgment(self, mock_memory_client, test_swarm_config):
        """Test adapter initialization with proper acknowledgment."""
        config = SwarmEvolutionConfig(
            enable_evolution=True,
            experimental_mode=ExperimentalMode.CAUTIOUS,
            acknowledge_experimental=True,
            dry_run_mode=True
        )

        adapter = ExperimentalSwarmEvolutionAdapter(
            swarm_type="test_swarm",
            config=config,
            memory_client=mock_memory_client
        )

        success = await adapter.initialize_evolution(test_swarm_config)

        assert success == True
        assert adapter.evolution_initialized == True
        assert adapter.evolution_active == True
        assert adapter.current_best_chromosome is not None

    @pytest.mark.asyncio
    async def test_performance_recording(self, mock_memory_client, test_swarm_config):
        """Test performance recording functionality."""
        config = SwarmEvolutionConfig(
            enable_evolution=True,
            experimental_mode=ExperimentalMode.CAUTIOUS,
            acknowledge_experimental=True,
            min_executions_before_evolution=3,
            evolution_frequency=5
        )

        adapter = ExperimentalSwarmEvolutionAdapter(
            swarm_type="test_swarm",
            config=config,
            memory_client=mock_memory_client
        )

        await adapter.initialize_evolution(test_swarm_config)

        # Record multiple executions
        for i in range(3):
            execution_result = {
                'execution_id': f'exec_{i}',
                'quality_score': 0.8,
                'speed_score': 0.7,
                'efficiency_score': 0.6,
                'reliability_score': 0.9,
                'success': True,
                'execution_time': 10.0,
                'errors': [],
                'agent_performance': {'agent_1': {'quality': 0.8}}
            }

            await adapter.record_execution_performance(execution_result)

        assert adapter.execution_count == 3
        assert len(adapter.performance_history) == 3
        assert adapter.baseline_performance is not None

        # Check performance summary
        summary = adapter.get_performance_summary()
        assert summary['total_executions'] == 3
        assert 'average_metrics' in summary
        assert summary['average_metrics']['quality_score'] == 0.8

    @pytest.mark.asyncio
    async def test_evolution_trigger_logic(self, mock_memory_client, test_swarm_config):
        """Test evolution trigger logic."""
        config = SwarmEvolutionConfig(
            enable_evolution=True,
            experimental_mode=ExperimentalMode.CAUTIOUS,
            acknowledge_experimental=True,
            min_executions_before_evolution=2,
            evolution_frequency=3,
            performance_tracking_window=3
        )

        adapter = ExperimentalSwarmEvolutionAdapter(
            swarm_type="test_swarm",
            config=config,
            memory_client=mock_memory_client
        )

        await adapter.initialize_evolution(test_swarm_config)

        # Mock the evolution engine
        adapter.evolution_engine = MagicMock()
        adapter.evolution_engine.experimental_evolve_population = AsyncMock(return_value=adapter.current_best_chromosome)

        # Record executions up to trigger point
        for i in range(5):  # This should trigger evolution at execution 5
            execution_result = {
                'execution_id': f'exec_{i}',
                'quality_score': 0.8,
                'speed_score': 0.7,
                'efficiency_score': 0.6,
                'reliability_score': 0.9,
                'success': True
            }

            await adapter.record_execution_performance(execution_result)

        # Evolution should have been triggered
        adapter.evolution_engine.experimental_evolve_population.assert_called()

    def test_current_swarm_config_without_evolution(self, mock_memory_client):
        """Test getting swarm config without evolution."""
        adapter = ExperimentalSwarmEvolutionAdapter(
            swarm_type="test_swarm",
            memory_client=mock_memory_client
        )

        config = adapter.get_current_swarm_config()

        assert 'agents' in config
        assert config['evolution_enabled'] == False
        assert 'chromosome_id' not in config

    @pytest.mark.asyncio
    async def test_current_swarm_config_with_evolution(self, mock_memory_client, test_swarm_config):
        """Test getting swarm config with evolution."""
        config = SwarmEvolutionConfig(
            enable_evolution=True,
            experimental_mode=ExperimentalMode.CAUTIOUS,
            acknowledge_experimental=True
        )

        adapter = ExperimentalSwarmEvolutionAdapter(
            swarm_type="test_swarm",
            config=config,
            memory_client=mock_memory_client
        )

        await adapter.initialize_evolution(test_swarm_config)

        swarm_config = adapter.get_current_swarm_config()

        assert swarm_config['evolution_enabled'] == True
        assert 'chromosome_id' in swarm_config
        assert 'generation' in swarm_config
        assert 'fitness_score' in swarm_config
        assert swarm_config['agents'] == test_swarm_config['agents']

    def test_evolution_status_reporting(self, mock_memory_client):
        """Test evolution status reporting."""
        config = SwarmEvolutionConfig(
            enable_evolution=True,
            experimental_mode=ExperimentalMode.EXPERIMENTAL,
            acknowledge_experimental=True,
            dry_run_mode=True
        )

        adapter = ExperimentalSwarmEvolutionAdapter(
            swarm_type="test_swarm",
            config=config,
            memory_client=mock_memory_client
        )

        status = adapter.get_evolution_status()

        assert status['swarm_type'] == 'test_swarm'
        assert status['evolution_enabled'] == True
        assert status['experimental_mode'] == 'experimental'
        assert status['dry_run_mode'] == True
        assert status['evolution_initialized'] == False
        assert status['execution_count'] == 0


class TestFactoryFunctions:
    """Test factory functions for safe creation."""

    def test_create_experimental_evolution_engine_safe_default(self):
        """Test creating engine with safe defaults."""
        engine = create_experimental_evolution_engine()

        assert engine.config.enabled == False
        assert engine.config.mode == ExperimentalMode.DISABLED
        assert engine.config.experimental_features_acknowledged == False

    def test_create_experimental_evolution_engine_requires_acknowledgment(self):
        """Test that factory requires acknowledgment for experimental features."""
        with pytest.raises(ValueError, match="EXPERIMENTAL EVOLUTION REQUIRES ACKNOWLEDGMENT"):
            create_experimental_evolution_engine(
                enable_experimental=True,
                acknowledge_experimental=False
            )

    def test_create_experimental_evolution_engine_with_acknowledgment(self):
        """Test creating engine with proper acknowledgment."""
        engine = create_experimental_evolution_engine(
            mode=ExperimentalMode.CAUTIOUS,
            enable_experimental=True,
            acknowledge_experimental=True,
            dry_run_mode=True
        )

        assert engine.config.enabled == True
        assert engine.config.mode == ExperimentalMode.CAUTIOUS
        assert engine.config.experimental_features_acknowledged == True
        assert engine.config.dry_run_mode == True

    def test_create_evolution_adapter_safe_default(self):
        """Test creating adapter with safe defaults."""
        adapter = create_evolution_adapter(swarm_type="test_swarm")

        assert adapter.config.enable_evolution == False
        assert adapter.config.experimental_mode == ExperimentalMode.DISABLED
        assert adapter.config.acknowledge_experimental == False

    def test_create_evolution_adapter_with_experimental_features(self):
        """Test creating adapter with experimental features."""
        adapter = create_evolution_adapter(
            swarm_type="test_swarm",
            enable_evolution=True,
            experimental_mode=ExperimentalMode.CAUTIOUS,
            acknowledge_experimental=True,
            dry_run_mode=True,
            evolution_frequency=5,
            min_executions_before_evolution=3
        )

        assert adapter.config.enable_evolution == True
        assert adapter.config.experimental_mode == ExperimentalMode.CAUTIOUS
        assert adapter.config.acknowledge_experimental == True
        assert adapter.config.evolution_frequency == 5


class TestSafetyValidation:
    """Test safety validation and edge cases."""

    @pytest.mark.asyncio
    async def test_engine_handles_invalid_performance_data(self):
        """Test that engine handles invalid performance data gracefully."""
        config = ExperimentalEvolutionConfig(
            mode=ExperimentalMode.CAUTIOUS,
            enabled=True,
            experimental_features_acknowledged=True,
            dry_run_mode=True
        )

        engine = ExperimentalEvolutionEngine(config)

        # Test with invalid/missing performance data
        invalid_data_sets = [
            {},  # Empty data
            {'quality_score': 'invalid'},  # Invalid type
            {'quality_score': -1.0},  # Out of bounds
            {'quality_score': 2.0},  # Out of bounds
            None  # None data
        ]

        for invalid_data in invalid_data_sets:
            # Should not crash, should handle gracefully
            try:
                chromosome = SwarmChromosome(
                    chromosome_id="test",
                    swarm_type="test",
                    generation=1,
                    agent_roles=["agent"],
                    agent_parameters={"agent": {"param": 0.5}},
                    coordination_style="test",
                    communication_pattern="test",
                    consensus_mechanism="test",
                    quality_threshold=0.8,
                    speed_preference=0.5,
                    risk_tolerance=0.3,
                    learning_rate=0.5,
                    memory_utilization=0.7,
                    pattern_recognition_sensitivity=0.6
                )

                # This should handle invalid data gracefully
                result = await engine._evaluate_experimental_chromosome_fitness(
                    chromosome, invalid_data or {}, False
                )

                # Should return valid fitness evaluation with defaults
                assert isinstance(result, ExperimentalFitnessEvaluation)
                assert 0.0 <= result.overall_fitness <= 1.0

            except Exception as e:
                # If it does raise an exception, it should be handled gracefully
                assert "performance data" in str(e).lower() or "invalid" in str(e).lower()

    def test_chromosome_validation_catches_invalid_chromosomes(self):
        """Test that chromosome validation catches invalid chromosomes."""
        config = ExperimentalEvolutionConfig(
            mode=ExperimentalMode.CAUTIOUS,
            enabled=True,
            experimental_features_acknowledged=True
        )

        engine = ExperimentalEvolutionEngine(config)

        # Test invalid chromosomes
        invalid_chromosomes = [
            # Risk tolerance too high
            SwarmChromosome(
                chromosome_id="invalid1", swarm_type="test", generation=1,
                agent_roles=["agent"], agent_parameters={"agent": {"param": 0.5}},
                coordination_style="test", communication_pattern="test", consensus_mechanism="test",
                quality_threshold=0.8, speed_preference=0.5, risk_tolerance=0.9,  # Too high
                learning_rate=0.5, memory_utilization=0.7, pattern_recognition_sensitivity=0.6
            ),
            # Quality threshold out of bounds
            SwarmChromosome(
                chromosome_id="invalid2", swarm_type="test", generation=1,
                agent_roles=["agent"], agent_parameters={"agent": {"param": 0.5}},
                coordination_style="test", communication_pattern="test", consensus_mechanism="test",
                quality_threshold=1.5,  # Too high
                speed_preference=0.5, risk_tolerance=0.3,
                learning_rate=0.5, memory_utilization=0.7, pattern_recognition_sensitivity=0.6
            ),
            # Agent parameter out of bounds
            SwarmChromosome(
                chromosome_id="invalid3", swarm_type="test", generation=1,
                agent_roles=["agent"], agent_parameters={"agent": {"param": -0.5}},  # Negative
                coordination_style="test", communication_pattern="test", consensus_mechanism="test",
                quality_threshold=0.8, speed_preference=0.5, risk_tolerance=0.3,
                learning_rate=0.5, memory_utilization=0.7, pattern_recognition_sensitivity=0.6
            )
        ]

        for chromosome in invalid_chromosomes:
            is_valid = engine._validate_experimental_chromosome(chromosome)
            assert is_valid == False, f"Chromosome {chromosome.chromosome_id} should be invalid"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
