#!/usr/bin/env python3

"""
Focused test for consciousness measurement functionality.
"""

import asyncio
from app.swarms.consciousness_tracking import ConsciousnessTracker

async def test_consciousness_measurement():
    """Test basic consciousness measurement."""
    print("🧠 Testing consciousness measurement...")
    
    # Create tracker
    tracker = ConsciousnessTracker("test_swarm", "test_swarm_001")
    print(f"   ✅ Tracker created: {tracker}")
    
    # Test context data
    test_context = {
        "agent_count": 5,
        "execution_data": {
            "agent_response_times": [1.0, 1.2, 0.8, 1.1, 0.9],
            "agent_roles": ["planner", "generator", "critic", "judge", "coordinator"],
            "quality_score": 0.85,
            "success": True,
            "patterns_used": ["coordination", "quality_gates", "adversarial_debate"],
            "task_assignments": {"agent_1": 2, "agent_2": 3, "agent_3": 2, "agent_4": 1, "agent_5": 2},
            "communication": {
                "clarity_score": 0.8,
                "relevance_score": 0.7,
                "info_sharing_score": 0.6,
                "feedback_score": 0.75
            },
            "role_performance": {
                "adherence_scores": [0.8, 0.9, 0.7, 0.85, 0.8]
            },
            "conflicts": [],
            "resolved_conflicts": 0
        },
        "memory_data": {
            "patterns_applied": 3,
            "available_patterns": 8,
            "pattern_types_recognized": ["execution", "quality", "coordination"],
        },
        "performance_data": {
            "quality_scores": [0.7, 0.8, 0.85],
            "reliability_score": 0.9,
            "efficiency_score": 0.8
        },
        "learning_data": {
            "learnings_count": 5,
            "avg_confidence": 0.7
        }
    }
    
    try:
        # Test consciousness measurement
        measurements = await tracker.measure_consciousness(test_context)
        print(f"   📊 Measurements returned: {len(measurements)} dimensions")
        
        if measurements:
            for dim_type, measurement in measurements.items():
                print(f"      {dim_type.value}: {measurement.value:.3f} (confidence: {measurement.confidence:.3f})")
            print(f"   ✅ Consciousness measurement - SUCCESS")
        else:
            print(f"   🚨 Consciousness measurement - FAILED (empty result)")
            
    except Exception as e:
        print(f"   🚨 Consciousness measurement - ERROR: {e}")
        import traceback
        print(f"   📋 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_consciousness_measurement())