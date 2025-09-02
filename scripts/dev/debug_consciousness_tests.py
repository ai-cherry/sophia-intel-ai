#!/usr/bin/env python3
"""
Debug script to validate consciousness tracking test assumptions
"""

import asyncio
import sys
import os
sys.path.insert(0, '.')

# Mock imports to avoid dependency issues
from unittest.mock import MagicMock
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def validate_consciousness_assumptions():
    """Validate our assumptions about the failing tests."""
    
    print("🔍 DEBUGGING CONSCIOUSNESS TRACKING TEST ISSUES")
    print("=" * 60)
    
    # Check 1: UnifiedSwarmOrchestrator consciousness integration
    try:
        print("\n1️⃣ Testing UnifiedSwarmOrchestrator consciousness integration...")
        
        # Mock memory client to avoid dependency issues  
        mock_memory_client = MagicMock()
        mock_memory_client.initialize = MagicMock(return_value=None)
        mock_memory_client.log_swarm_event = MagicMock(return_value=None)
        
        with unittest.mock.patch('app.swarms.unified_enhanced_orchestrator.SwarmMemoryClient', return_value=mock_memory_client):
            from app.swarms.unified_enhanced_orchestrator import UnifiedSwarmOrchestrator
            
            orchestrator = UnifiedSwarmOrchestrator()
            print(f"   ✅ Orchestrator created: {type(orchestrator)}")
            
            # Check if global_consciousness_tracker exists before initialization
            has_tracker_before = hasattr(orchestrator, 'global_consciousness_tracker')
            tracker_value_before = getattr(orchestrator, 'global_consciousness_tracker', 'NOT_SET')
            print(f"   📊 global_consciousness_tracker before init: {has_tracker_before} (value: {tracker_value_before})")
            
            # Initialize memory integration
            await orchestrator.initialize_memory_integration()
            
            # Check after initialization
            has_tracker_after = hasattr(orchestrator, 'global_consciousness_tracker')
            tracker_value_after = getattr(orchestrator, 'global_consciousness_tracker', 'NOT_SET')
            print(f"   📊 global_consciousness_tracker after init: {has_tracker_after} (value: {type(tracker_value_after) if tracker_value_after else 'None'})")
            
            # Check if it's the expected ConsciousnessTracker type
            if tracker_value_after:
                from app.swarms.consciousness_tracking import ConsciousnessTracker
                is_consciousness_tracker = isinstance(tracker_value_after, ConsciousnessTracker)
                print(f"   📊 Is ConsciousnessTracker instance: {is_consciousness_tracker}")
                
            print("   ✅ UnifiedSwarmOrchestrator consciousness integration - LIKELY WORKING")
    
    except Exception as e:
        print(f"   ❌ UnifiedSwarmOrchestrator consciousness integration - ERROR: {e}")
        print("   🚨 THIS IS LIKELY A FAILING TEST SOURCE")
    
    # Check 2: MemoryEnhancedGenesisSwarm consciousness integration  
    try:
        print("\n2️⃣ Testing MemoryEnhancedGenesisSwarm consciousness integration...")
        
        with unittest.mock.patch('app.swarms.memory_integration.SwarmMemoryClient', return_value=mock_memory_client):
            from app.swarms.memory_enhanced_swarm import MemoryEnhancedGenesisSwarm
            
            agents = ["test_agent_1", "test_agent_2", "test_agent_3"]
            swarm = MemoryEnhancedGenesisSwarm(agents)
            print(f"   ✅ Swarm created: {type(swarm)}")
            
            # Check consciousness_tracker before full system initialization
            has_tracker_before = hasattr(swarm, 'consciousness_tracker')
            tracker_value_before = getattr(swarm, 'consciousness_tracker', 'NOT_SET')
            print(f"   📊 consciousness_tracker before init: {has_tracker_before} (value: {tracker_value_before})")
            
            # Initialize full system
            await swarm.initialize_full_system()
            
            # Check after initialization
            has_tracker_after = hasattr(swarm, 'consciousness_tracker')
            tracker_value_after = getattr(swarm, 'consciousness_tracker', 'NOT_SET')
            print(f"   📊 consciousness_tracker after init: {has_tracker_after} (value: {type(tracker_value_after) if tracker_value_after else 'None'})")
            
            # Check swarm type
            expected_swarm_type = "genesis_swarm"
            actual_swarm_type = getattr(swarm.consciousness_tracker, 'swarm_type', 'NOT_SET') if tracker_value_after else 'NO_TRACKER'
            print(f"   📊 Swarm type check: expected='{expected_swarm_type}', actual='{actual_swarm_type}'")
            
            if tracker_value_after and actual_swarm_type == expected_swarm_type:
                print("   ✅ MemoryEnhancedGenesisSwarm consciousness integration - LIKELY WORKING")
            else:
                print("   🚨 MemoryEnhancedGenesisSwarm consciousness integration - POTENTIAL ISSUE")
                
    except Exception as e:
        print(f"   ❌ MemoryEnhancedGenesisSwarm consciousness integration - ERROR: {e}")
        print("   🚨 THIS IS LIKELY A FAILING TEST SOURCE")
    
    # Check 3: ExperimentalEvolutionEngine consciousness integration
    try:
        print("\n3️⃣ Testing ExperimentalEvolutionEngine consciousness integration...")
        
        from app.swarms.consciousness_tracking import ConsciousnessTracker
        from app.swarms.evolution.experimental_evolution_engine import ExperimentalEvolutionEngine
        
        # Create consciousness tracker
        consciousness_tracker = ConsciousnessTracker(
            "genesis_swarm", "test_genesis", mock_memory_client
        )
        print(f"   ✅ ConsciousnessTracker created: {type(consciousness_tracker)}")
        
        # Create evolution engine with consciousness integration
        evolution_engine = ExperimentalEvolutionEngine(
            memory_client=mock_memory_client,
            consciousness_tracker=consciousness_tracker
        )
        print(f"   ✅ ExperimentalEvolutionEngine created: {type(evolution_engine)}")
        
        # Check expected attributes
        has_consciousness_tracker = hasattr(evolution_engine, 'consciousness_tracker')
        tracker_matches = evolution_engine.consciousness_tracker is consciousness_tracker
        print(f"   📊 Has consciousness_tracker: {has_consciousness_tracker}")
        print(f"   📊 Tracker matches: {tracker_matches}")
        
        # Check evolution stats
        expected_stats = ["consciousness_guided_evolutions", "consciousness_fitness_correlations", "consciousness_breakthroughs"]
        stats_present = all(stat in evolution_engine.evolution_stats for stat in expected_stats)
        print(f"   📊 Consciousness stats present: {stats_present}")
        
        if has_consciousness_tracker and tracker_matches and stats_present:
            print("   ✅ ExperimentalEvolutionEngine consciousness integration - LIKELY WORKING")
        else:
            print("   🚨 ExperimentalEvolutionEngine consciousness integration - POTENTIAL ISSUE")
            
    except Exception as e:
        print(f"   ❌ ExperimentalEvolutionEngine consciousness integration - ERROR: {e}")
        print("   🚨 THIS IS LIKELY A FAILING TEST SOURCE")
    
    print("\n" + "=" * 60)
    print("🔍 DIAGNOSIS COMPLETE")

if __name__ == "__main__":
    # Add mock import for unittest since we need it
    import unittest.mock
    asyncio.run(validate_consciousness_assumptions())