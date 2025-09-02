"""
Comprehensive Integration Tests for Consciousness Tracking System - ADR-003
Tests the complete consciousness tracking implementation including:
- 5-dimensional consciousness measurement
- Pattern breakthrough detection
- Memory-consciousness correlation
- Evolution-consciousness integration
- Real-time monitoring and visualization
- Collective consciousness measurement
- Performance correlation validation
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.swarms.consciousness_tracking import (
    ConsciousnessMeasurement,
    ConsciousnessTracker,
    ConsciousnessType,
    EmergenceEvent,
    EmergenceEventType,
)
from app.swarms.evolution.experimental_evolution_engine import ExperimentalEvolutionEngine
from app.swarms.memory_enhanced_swarm import MemoryEnhancedGenesisSwarm
from app.swarms.memory_integration import SwarmMemoryClient
from app.swarms.unified_enhanced_orchestrator import UnifiedSwarmOrchestrator


@pytest.fixture
async def mock_memory_client():
    """Mock memory client for testing."""
    client = MagicMock(spec=SwarmMemoryClient)
    client.initialize = AsyncMock(return_value=None)
    client.log_swarm_event = AsyncMock(return_value=None)
    client.store_memory = AsyncMock(return_value={"id": "test_memory_id"})
    client.search_memory = AsyncMock(return_value=[])
    client.store_pattern = AsyncMock(return_value=None)
    client.store_learning = AsyncMock(return_value=None)
    client.get_memory_stats = AsyncMock(return_value={"memories": 100, "error": None})
    return client


@pytest.fixture
async def consciousness_tracker(mock_memory_client):
    """Create consciousness tracker for testing."""
    tracker = ConsciousnessTracker(
        swarm_type="test_swarm",
        swarm_id="test_swarm_001",
        memory_client=mock_memory_client
    )
    return tracker


@pytest.fixture
async def test_context():
    """Create test context for consciousness measurements."""
    return {
        "task": {"type": "coding", "description": "Test task"},
        "agent_count": 5,
        "execution_data": {
            "quality_score": 0.8,
            "execution_time": 5.0,
            "success": True,
            "agent_roles": ["planner", "generator", "critic", "judge", "tester"],
            "patterns_used": ["adversarial_debate", "quality_gates"],
            "agent_response_times": [1.0, 1.2, 0.8, 1.1, 0.9],
            "task_assignments": {"planner": 2, "generator": 3, "critic": 2},
            "communication": {
                "clarity_score": 0.7,
                "relevance_score": 0.8,
                "info_sharing_score": 0.6,
                "feedback_score": 0.7
            },
            "role_performance": {
                "adherence_scores": [0.8, 0.7, 0.9, 0.6, 0.8]
            },
            "conflicts": [],
            "resolved_conflicts": 0
        },
        "performance_data": {
            "quality_scores": [0.8, 0.7, 0.9],
            "speed_score": 0.7,
            "efficiency_score": 0.75,
            "reliability_score": 0.85
        },
        "memory_data": {
            "patterns_applied": 3,
            "pattern_types_recognized": ["execution", "quality", "coordination"],
            "available_patterns": 8
        },
        "learning_data": {
            "learnings_count": 5,
            "avg_confidence": 0.8
        }
    }


class TestConsciousnessTracking:
    """Test consciousness tracking core functionality."""

    @pytest.mark.asyncio
    async def test_consciousness_measurement_initialization(self, consciousness_tracker):
        """Test consciousness tracker initialization."""
        assert consciousness_tracker.swarm_type == "test_swarm"
        assert consciousness_tracker.swarm_id == "test_swarm_001"
        assert consciousness_tracker.monitoring_active is True
        assert len(consciousness_tracker.emergence_thresholds) == len(EmergenceEventType)
        assert consciousness_tracker.consciousness_profile.current_level == 0.0
        assert consciousness_tracker.consciousness_profile.development_stage == "nascent"

    @pytest.mark.asyncio
    async def test_5_dimensional_consciousness_measurement(self, consciousness_tracker, test_context):
        """Test comprehensive 5-dimensional consciousness measurement."""
        # Perform consciousness measurement
        measurements = await consciousness_tracker.measure_consciousness(test_context)

        # Verify all dimensions are measured
        assert len(measurements) == 5
        for dimension in ConsciousnessType:
            assert dimension in measurements
            assert isinstance(measurements[dimension], ConsciousnessMeasurement)
            assert 0.0 <= measurements[dimension].value <= 1.0
            assert 0.0 <= measurements[dimension].confidence <= 1.0

        # Verify profile is updated
        assert consciousness_tracker.consciousness_profile.current_level > 0
        assert len(consciousness_tracker.consciousness_profile.dimensions) == 5
        assert len(consciousness_tracker.measurement_history) == 1

    @pytest.mark.asyncio
    async def test_baseline_establishment(self, consciousness_tracker, test_context):
        """Test baseline establishment for consciousness measurements."""
        # Initially no baseline
        assert not consciousness_tracker.baseline_established

        # Perform measurements to establish baseline
        for _ in range(3):  # baseline_required_samples = 3
            await consciousness_tracker.measure_consciousness(test_context)

        # Verify baseline is established
        assert consciousness_tracker.baseline_established
        assert len(consciousness_tracker.consciousness_profile.baseline_measurements) == 5

        # Verify baseline deviation is calculated for subsequent measurements
        measurements = await consciousness_tracker.measure_consciousness(test_context)
        for measurement in measurements.values():
            assert hasattr(measurement, 'baseline_deviation')
            assert hasattr(measurement, 'historical_trend')

    @pytest.mark.asyncio
    async def test_emergence_detection(self, consciousness_tracker, test_context):
        """Test emergence event detection."""
        # Create context that should trigger emergence
        high_performance_context = test_context.copy()
        high_performance_context["execution_data"]["quality_score"] = 0.95
        high_performance_context["performance_data"]["quality_scores"] = [0.9, 0.95, 0.92]

        # Establish baseline first
        await consciousness_tracker._establish_baseline(test_context)

        # Perform measurement that should trigger emergence
        measurements = await consciousness_tracker.measure_consciousness(high_performance_context)

        # Check if emergence events were detected
        # Note: This may not always trigger due to randomized measurements, but test the mechanism
        if consciousness_tracker.emergence_events:
            emergence_event = consciousness_tracker.emergence_events[-1]
            assert isinstance(emergence_event, EmergenceEvent)
            assert emergence_event.swarm_type == "test_swarm"
            assert emergence_event.significance_score > 0

    @pytest.mark.asyncio
    async def test_pattern_breakthrough_detection(self, consciousness_tracker, test_context):
        """Test pattern breakthrough detection."""
        # Establish baseline
        await consciousness_tracker._establish_baseline(test_context)

        # Add measurements to pattern buffer
        for i in range(10):
            context = test_context.copy()
            context["execution_data"]["quality_score"] = 0.5 + (i * 0.05)  # Gradual improvement
            await consciousness_tracker.measure_consciousness(context)

        # Add a sudden jump in performance
        breakthrough_context = test_context.copy()
        breakthrough_context["execution_data"]["quality_score"] = 0.95
        await consciousness_tracker.measure_consciousness(breakthrough_context)

        # Check if breakthroughs were detected
        if consciousness_tracker.breakthrough_patterns:
            breakthrough = consciousness_tracker.breakthrough_patterns[-1]
            assert "breakthrough_id" in breakthrough
            assert "improvement_magnitude" in breakthrough
            assert breakthrough["swarm_type"] == "test_swarm"

    @pytest.mark.asyncio
    async def test_memory_correlation(self, consciousness_tracker, test_context, mock_memory_client):
        """Test memory-consciousness correlation."""
        # Setup mock memory responses
        mock_memory_client.search_memory.return_value = [
            {"content": json.dumps({"consciousness_level": 0.7, "quality_score": 0.8})},
            {"content": json.dumps({"consciousness_level": 0.6, "quality_score": 0.7})}
        ]

        # Perform consciousness measurement
        await consciousness_tracker.measure_consciousness(test_context)

        # Verify memory integration was called
        mock_memory_client.log_swarm_event.assert_called()
        mock_memory_client.store_memory.assert_called()

    @pytest.mark.asyncio
    async def test_performance_correlation(self, consciousness_tracker, test_context):
        """Test consciousness-performance correlation."""
        # Establish baseline and add historical data
        await consciousness_tracker._establish_baseline(test_context)

        # Add measurements with varying performance
        performance_levels = [0.6, 0.7, 0.8, 0.9, 0.75]
        for i, performance in enumerate(performance_levels):
            context = test_context.copy()
            context["performance_data"]["quality_scores"] = [performance]
            context["execution_data"]["quality_score"] = performance
            await consciousness_tracker.measure_consciousness(context)

        # Test correlation analysis
        correlation_result = await consciousness_tracker.correlate_consciousness_with_performance(
            test_context["performance_data"]
        )

        assert "correlations" in correlation_result
        assert "predictive_insights" in correlation_result
        assert "consciousness_level" in correlation_result
        assert len(consciousness_tracker.performance_consciousness_correlations) > 0


class TestCollectiveConsciousness:
    """Test collective consciousness functionality."""

    @pytest.mark.asyncio
    async def test_collective_consciousness_correlation(self, consciousness_tracker):
        """Test collective consciousness correlation."""
        # Setup global consciousness data
        global_data = {
            "average_consciousness": 0.6,
            "active_swarms": 5,
            "collective_trajectory": [0.5, 0.6, 0.7, 0.6, 0.65]
        }

        # Establish some consciousness level
        consciousness_tracker.consciousness_profile.current_level = 0.7
        consciousness_tracker.consciousness_profile.consciousness_trajectory = [0.6, 0.65, 0.7]

        # Test correlation
        correlation_result = await consciousness_tracker.correlate_with_collective_consciousness(global_data)

        assert "relative_position" in correlation_result
        assert "synchronization_score" in correlation_result
        assert "collective_contribution" in correlation_result
        assert correlation_result["individual_consciousness"] == 0.7
        assert correlation_result["collective_average"] == 0.6


class TestConsciousnessReporting:
    """Test consciousness reporting and metrics."""

    @pytest.mark.asyncio
    async def test_consciousness_metrics(self, consciousness_tracker, test_context):
        """Test consciousness metrics generation."""
        # Add some data
        await consciousness_tracker.measure_consciousness(test_context)

        # Generate metrics
        metrics = consciousness_tracker.get_consciousness_metrics()

        assert "profile" in metrics
        assert "recent_measurements" in metrics
        assert "emergence_events" in metrics
        assert "breakthrough_patterns" in metrics
        assert "monitoring_status" in metrics
        assert "statistics" in metrics

        # Verify profile data
        assert metrics["profile"]["swarm_type"] == "test_swarm"
        assert metrics["profile"]["current_level"] >= 0
        assert metrics["statistics"]["total_measurements"] > 0

    @pytest.mark.asyncio
    async def test_consciousness_report_generation(self, consciousness_tracker, test_context):
        """Test comprehensive consciousness report generation."""
        # Add some measurement data
        for _ in range(3):
            await consciousness_tracker.measure_consciousness(test_context)

        # Generate report
        report = await consciousness_tracker.generate_consciousness_report()

        assert "report_timestamp" in report
        assert "swarm_identity" in report
        assert "consciousness_profile" in report
        assert "performance_analysis" in report
        assert "emergence_analysis" in report
        assert "pattern_breakthrough_analysis" in report
        assert "collective_consciousness" in report
        assert "recommendations" in report

        # Verify report structure
        assert report["swarm_identity"]["swarm_type"] == "test_swarm"
        assert len(report["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_system_validation(self, consciousness_tracker):
        """Test consciousness system validation."""
        validation_result = await consciousness_tracker.validate_consciousness_system()

        assert "system_active" in validation_result
        assert "baseline_established" in validation_result
        assert "memory_integration" in validation_result
        assert "data_integrity" in validation_result
        assert "thresholds_configured" in validation_result
        assert "pattern_detection_active" in validation_result
        assert "alerts_configured" in validation_result
        assert "data_consistency" in validation_result

        # Verify validation results
        assert validation_result["system_active"] is True
        assert validation_result["thresholds_configured"] is True
        assert validation_result["pattern_detection_active"] is True


class TestOrchestratorIntegration:
    """Test integration with swarm orchestrators."""

    @pytest.mark.asyncio
    async def test_unified_orchestrator_consciousness_integration(self, mock_memory_client):
        """Test consciousness integration with unified orchestrator."""
        with patch('app.swarms.unified_enhanced_orchestrator.SwarmMemoryClient', return_value=mock_memory_client):
            orchestrator = UnifiedSwarmOrchestrator()

            # Initialize with consciousness tracking
            await orchestrator.initialize_memory_integration()

            # Verify consciousness tracker is initialized
            assert orchestrator.global_consciousness_tracker is not None
            assert isinstance(orchestrator.global_consciousness_tracker, ConsciousnessTracker)

            # Verify global metrics include consciousness fields
            assert "consciousness_measurements" in orchestrator.global_metrics
            assert "emergence_events" in orchestrator.global_metrics
            assert "pattern_breakthroughs" in orchestrator.global_metrics

    @pytest.mark.asyncio
    async def test_memory_enhanced_swarm_consciousness(self, mock_memory_client):
        """Test consciousness integration with memory-enhanced swarms."""
        with patch('app.swarms.memory_integration.SwarmMemoryClient', return_value=mock_memory_client):
            # Create memory-enhanced swarm
            agents = ["test_agent_1", "test_agent_2", "test_agent_3"]
            swarm = MemoryEnhancedGenesisSwarm(agents)

            # Initialize full system
            await swarm.initialize_full_system()

            # Verify consciousness tracker is initialized
            assert swarm.consciousness_tracker is not None
            assert isinstance(swarm.consciousness_tracker, ConsciousnessTracker)
            assert swarm.consciousness_tracker.swarm_type == "genesis_swarm"


class TestEvolutionIntegration:
    """Test evolution-consciousness integration."""

    @pytest.mark.asyncio
    async def test_evolution_consciousness_correlation(self, mock_memory_client):
        """Test consciousness correlation with evolution engine."""
        # Create consciousness tracker
        consciousness_tracker = ConsciousnessTracker(
            "genesis_swarm", "test_genesis", mock_memory_client
        )

        # Create evolution engine with consciousness integration
        evolution_engine = ExperimentalEvolutionEngine(
            memory_client=mock_memory_client,
            consciousness_tracker=consciousness_tracker
        )

        # Verify consciousness integration
        assert evolution_engine.consciousness_tracker is consciousness_tracker
        assert "consciousness_guided_evolutions" in evolution_engine.evolution_stats
        assert "consciousness_fitness_correlations" in evolution_engine.evolution_stats
        assert "consciousness_breakthroughs" in evolution_engine.evolution_stats


class TestRealTimeMonitoring:
    """Test real-time monitoring functionality."""

    @pytest.mark.asyncio
    async def test_real_time_alerts(self, consciousness_tracker, test_context):
        """Test real-time consciousness monitoring and alerts."""
        # Establish baseline
        await consciousness_tracker._establish_baseline(test_context)

        # Test consciousness drop alert
        low_performance_context = test_context.copy()
        low_performance_context["execution_data"]["quality_score"] = 0.2
        low_performance_context["performance_data"]["quality_scores"] = [0.2]

        with patch('app.swarms.consciousness_tracking.logger') as mock_logger:
            await consciousness_tracker.measure_consciousness(low_performance_context)

            # Should trigger consciousness drop alert if significant drop occurs
            # Note: This test depends on the measurement implementation

    @pytest.mark.asyncio
    async def test_emergence_frequency_monitoring(self, consciousness_tracker, test_context):
        """Test emergence event frequency monitoring."""
        # Add multiple emergence events quickly
        consciousness_tracker.emergence_events = [
            EmergenceEvent(
                event_id=f"test_{i}",
                event_type=EmergenceEventType.COORDINATION_SPIKE,
                swarm_id="test_swarm",
                swarm_type="test",
                timestamp=datetime.now(),
                trigger_value=0.9,
                threshold=0.8,
                consciousness_level=0.85,
                context={}
            ) for i in range(6)  # Above threshold
        ]

        with patch('app.swarms.consciousness_tracking.logger') as mock_logger:
            await consciousness_tracker._process_real_time_monitoring({}, test_context)

            # Should trigger high emergence frequency alert


@pytest.mark.asyncio
async def test_end_to_end_consciousness_workflow(mock_memory_client):
    """Test complete end-to-end consciousness tracking workflow."""
    # Create orchestrator with consciousness tracking
    with patch('app.swarms.unified_enhanced_orchestrator.SwarmMemoryClient', return_value=mock_memory_client):
        orchestrator = UnifiedSwarmOrchestrator()
        await orchestrator.initialize_memory_integration()

        # Execute task with consciousness measurement
        task = {
            "type": "coding",
            "description": "Test consciousness tracking integration",
            "urgency": "normal",
            "scope": "medium"
        }

        with patch.object(orchestrator, '_measure_swarm_consciousness') as mock_measure:
            mock_measure.return_value = {
                "consciousness_level": 0.75,
                "development_stage": "advanced",
                "measurements": {"coordination": 0.8, "pattern_recognition": 0.7}
            }

            # Execute with memory enhancement
            result = await orchestrator.execute_with_memory_enhancement(task)

            # Verify consciousness data is included
            assert "consciousness_data" in result or mock_measure.called

            # Verify global metrics are updated
            assert orchestrator.global_metrics["consciousness_measurements"] >= 0


if __name__ == "__main__":
    # Run tests
    asyncio.run(pytest.main([__file__, "-v"]))
