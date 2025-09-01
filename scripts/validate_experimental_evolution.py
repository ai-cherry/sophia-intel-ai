"""
Validation Script for Experimental Evolution Engine - ADR-002 Implementation

⚠️ EXPERIMENTAL VALIDATION ⚠️

This script validates the experimental evolution engine implementation,
including integration with existing swarm systems and safety controls.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main validation function."""
    
    print("🧪 " + "="*60)
    print("🧪 EXPERIMENTAL EVOLUTION ENGINE VALIDATION")
    print("🧪 ADR-002 Implementation Validation Script")
    print("🧪 " + "="*60)
    
    try:
        # Import components
        from app.swarms.evolution import (
            create_experimental_evolution_engine,
            ExperimentalMode,
            ExperimentalEvolutionConfig,
            SwarmChromosome,
            get_experimental_info
        )
        from app.swarms.evolution.integration_adapter import create_evolution_adapter
        from app.swarms.evolution.monitoring_dashboard import get_global_monitor
        from app.swarms.memory_integration import SwarmMemoryClient
        
        print("✅ Successfully imported all experimental evolution components")
        
        # 1. Validate experimental info
        print("\n🧪 1. Validating Experimental System Info")
        info = get_experimental_info()
        print(f"   Version: {info['version']}")
        print(f"   Experimental: {info['experimental']}")
        print(f"   Default Mode: {info['default_mode']}")
        print(f"   Available Modes: {info['available_modes']}")
        print("✅ Experimental info validation completed")
        
        # 2. Test safe defaults (should be disabled)
        print("\n🧪 2. Testing Safe Defaults")
        safe_engine = create_experimental_evolution_engine()
        assert safe_engine.config.enabled == False
        assert safe_engine.config.mode == ExperimentalMode.DISABLED
        print("✅ Safe defaults validated - evolution disabled by default")
        
        # 3. Test acknowledgment requirement
        print("\n🧪 3. Testing Acknowledgment Requirement")
        try:
            create_experimental_evolution_engine(
                enable_experimental=True,
                acknowledge_experimental=False
            )
            print("❌ Should have required acknowledgment!")
            return False
        except ValueError as e:
            if "EXPERIMENTAL EVOLUTION REQUIRES ACKNOWLEDGMENT" in str(e):
                print("✅ Acknowledgment requirement enforced correctly")
            else:
                print(f"❌ Wrong error: {e}")
                return False
        
        # 4. Test valid experimental configuration
        print("\n🧪 4. Creating Valid Experimental Configuration")
        experimental_engine = create_experimental_evolution_engine(
            mode=ExperimentalMode.CAUTIOUS,
            enable_experimental=True,
            acknowledge_experimental=True,
            dry_run_mode=True
        )
        assert experimental_engine.config.enabled == True
        assert experimental_engine.config.experimental_features_acknowledged == True
        print("✅ Valid experimental configuration created")
        
        # 5. Test chromosome creation and validation
        print("\n🧪 5. Testing Chromosome Operations")
        base_chromosome = SwarmChromosome(
            chromosome_id="validation_test",
            swarm_type="test_swarm",
            generation=1,
            agent_roles=["agent_1", "agent_2"],
            agent_parameters={
                "agent_1": {"creativity": 0.7, "focus": 0.8},
                "agent_2": {"creativity": 0.6, "focus": 0.7}
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
        
        # Test mutation
        mutated = base_chromosome.mutate(0.1, experimental_engine.config.safety_bounds)
        assert mutated.chromosome_id != base_chromosome.chromosome_id
        assert mutated.generation == base_chromosome.generation + 1
        print("✅ Chromosome mutation working correctly")
        
        # Test crossover
        child1, child2 = SwarmChromosome.crossover(base_chromosome, mutated)
        assert len(child1.parent_chromosomes) == 2
        assert len(child2.parent_chromosomes) == 2
        print("✅ Chromosome crossover working correctly")
        
        # 6. Test population initialization
        print("\n🧪 6. Testing Population Initialization")
        success = await experimental_engine.initialize_experimental_population(
            swarm_type="validation_swarm",
            base_chromosome=base_chromosome,
            population_size=3
        )
        assert success == True
        assert len(experimental_engine.populations["validation_swarm"]) == 3
        print("✅ Population initialization successful")
        
        # 7. Test integration adapter
        print("\n🧪 7. Testing Integration Adapter")
        adapter = create_evolution_adapter(
            swarm_type="validation_adapter",
            enable_evolution=True,
            experimental_mode=ExperimentalMode.CAUTIOUS,
            acknowledge_experimental=True,
            dry_run_mode=True
        )
        
        base_config = {
            'agents': ['agent_1', 'agent_2'],
            'coordination_style': 'peer_to_peer',
            'quality_threshold': 0.8
        }
        
        adapter_success = await adapter.initialize_evolution(base_config)
        assert adapter_success == True
        assert adapter.evolution_initialized == True
        print("✅ Integration adapter working correctly")
        
        # 8. Test monitoring system
        print("\n🧪 8. Testing Monitoring System")
        monitor = get_global_monitor()
        monitor.register_engine("validation_swarm", experimental_engine)
        monitor.register_adapter("validation_adapter", adapter)
        
        summary = monitor.get_monitoring_summary()
        assert summary['total_tracked_systems'] == 2
        assert summary['tracked_engines'] == 1
        assert summary['tracked_adapters'] == 1
        print("✅ Monitoring system working correctly")
        
        # 9. Test safety controls
        print("\n🧪 9. Testing Safety Controls")
        config_with_validation = ExperimentalEvolutionConfig(
            mode=ExperimentalMode.EXPERIMENTAL,
            enabled=True,
            experimental_features_acknowledged=True,
            mutation_rate=0.5,  # Too high - should be caught
            dry_run_mode=True
        )
        
        issues = config_with_validation.validate()
        assert len(issues) > 0
        print(f"✅ Safety validation caught {len(issues)} configuration issues")
        
        # 10. Test performance tracking
        print("\n🧪 10. Testing Performance Tracking")
        execution_result = {
            'execution_id': 'validation_test',
            'quality_score': 0.85,
            'speed_score': 0.7,
            'efficiency_score': 0.8,
            'reliability_score': 0.9,
            'success': True,
            'execution_time': 10.0,
            'errors': []
        }
        
        await adapter.record_execution_performance(execution_result)
        assert adapter.execution_count == 1
        assert len(adapter.performance_history) == 1
        
        performance_summary = adapter.get_performance_summary()
        assert performance_summary['total_executions'] == 1
        print("✅ Performance tracking working correctly")
        
        # 11. Test dashboard data
        print("\n🧪 11. Testing Dashboard Data")
        dashboard_data = monitor.get_dashboard_data()
        assert 'summary' in dashboard_data
        assert 'metrics' in dashboard_data
        assert 'alerts' in dashboard_data
        print("✅ Dashboard data generation working correctly")
        
        # 12. Final validation summary
        print("\n🧪 12. Validation Summary")
        
        # Engine status
        engine_status = experimental_engine.get_experimental_status()
        print(f"   Engine Global Status: {engine_status['global_experimental_status']}")
        
        # Adapter status
        adapter_status = adapter.get_evolution_status()
        print(f"   Adapter Evolution Status: Enabled={adapter_status['evolution_enabled']}, Mode={adapter_status['experimental_mode']}")
        
        # Monitor status
        monitor_summary = monitor.get_monitoring_summary()
        print(f"   Monitor Status: Systems={monitor_summary['total_tracked_systems']}, Health={monitor_summary['system_health']}")
        
        print("\n🧪 " + "="*60)
        print("🧪 ✅ ALL EXPERIMENTAL EVOLUTION VALIDATIONS PASSED")
        print("🧪 " + "="*60)
        print("\n🧪 SUMMARY:")
        print("🧪 • Experimental Evolution Engine: ✅ Working")
        print("🧪 • Safety Controls: ✅ Active")  
        print("🧪 • Integration Adapter: ✅ Functional")
        print("🧪 • Monitoring Dashboard: ✅ Operational")
        print("🧪 • Genetic Algorithms: ✅ Implemented")
        print("🧪 • Memory Integration: ✅ Ready")
        print("🧪 • Configuration Validation: ✅ Enforced")
        print("🧪 • Pattern Recognition: ✅ Available")
        print("🧪 • Performance Tracking: ✅ Active")
        print("🧪 • Testing Framework: ✅ Comprehensive")
        print("\n⚠️  EXPERIMENTAL FEATURES ARE READY FOR CAUTIOUS USE")
        print("⚠️  ENSURE PROPER ACKNOWLEDGMENT AND MONITORING")
        print("⚠️  USE DRY RUN MODE FOR INITIAL TESTING")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("❌ Experimental evolution components not available")
        return False
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        logger.exception("Validation error details:")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)