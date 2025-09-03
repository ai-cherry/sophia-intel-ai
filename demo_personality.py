#!/usr/bin/env python3
"""
Demo Script: SuperOrchestrator with Personality
Shows off the enthusiasm, smarts, and attitude you requested
"""

import asyncio
import json
from datetime import datetime

from app.core.super_orchestrator import get_orchestrator
from app.core.orchestrator_enhancements import RegisteredSystem, SystemStatus, SystemType

async def demo_personality():
    """Run a full demo of the personality system"""
    
    print("\n" + "="*60)
    print("🚀 SUPERORCHESTRATOR PERSONALITY DEMO")
    print("="*60)
    
    # Get the orchestrator
    orchestrator = get_orchestrator()
    
    # Initialize it
    await orchestrator.initialize()
    
    print("\n1️⃣ GREETING TEST")
    print("-"*40)
    greeting = orchestrator.personality.generate_response("greeting")
    print(f"SuperOrchestrator: {greeting}")
    
    print("\n2️⃣ SUCCESS RESPONSE")
    print("-"*40)
    success = orchestrator.personality.generate_response(
        "success",
        data={"metrics": "5 micro-swarms deployed in 0.3 seconds!"}
    )
    print(f"SuperOrchestrator: {success}")
    
    print("\n3️⃣ ERROR HANDLING")
    print("-"*40)
    error = orchestrator.personality.generate_response(
        "error",
        data={"error": "Connection timeout to embedding service"}
    )
    print(f"SuperOrchestrator: {error}")
    
    print("\n4️⃣ RISKY COMMAND PUSHBACK")
    print("-"*40)
    risky_command = "delete all systems"
    risk_analysis = orchestrator.personality.analyze_command_risk(risky_command)
    if risk_analysis["should_pushback"]:
        pushback = orchestrator.personality.generate_response(
            "processing",
            command=risky_command
        )
        print(f"User: {risky_command}")
        print(f"SuperOrchestrator: {pushback}")
        
        # Show alternatives
        alternatives = orchestrator.personality.suggest_alternatives(risky_command)
        if alternatives:
            print("\n💡 Suggested alternatives:")
            for alt in alternatives:
                print(f"  • {alt}")
    
    print("\n5️⃣ SYSTEM STATUS WITH PERSONALITY")
    print("-"*40)
    
    # Register some test systems
    test_systems = [
        RegisteredSystem(
            id="agent_001",
            name="DataAnalyzer",
            type=SystemType.AGENT,
            status=SystemStatus.ACTIVE,
            capabilities=["analyze", "report"]
        ),
        RegisteredSystem(
            id="swarm_001",
            name="LogProcessors",
            type=SystemType.SWARM,
            status=SystemStatus.ACTIVE,
            capabilities=["parallel_process", "aggregate"]
        ),
        RegisteredSystem(
            id="agent_002",
            name="ErrorAgent",
            type=SystemType.AGENT,
            status=SystemStatus.ERROR,
            capabilities=["debug"]
        ),
        RegisteredSystem(
            id="micro_001",
            name="QuickTask",
            type=SystemType.MICRO_SWARM,
            status=SystemStatus.IDLE,
            capabilities=["rapid_execute"]
        )
    ]
    
    for system in test_systems:
        await orchestrator.registry.register(system)
    
    # Get personality-formatted status
    status = orchestrator.personality.format_system_status([
        {"status": s.status.value, "type": s.type.value}
        for s in test_systems
    ])
    print(f"SuperOrchestrator:\n{status}")
    
    print("\n6️⃣ ANALYSIS WITH PERSONALITY")
    print("-"*40)
    analysis = orchestrator.personality.generate_response(
        "analysis",
        data={
            "health_score": 85,
            "active_systems": 3,
            "cost": 12.50,
            "recommendations": [
                "Scale down idle systems",
                "Optimize embedding cache",
                "Enable auto-healing for error agents"
            ]
        }
    )
    print(f"SuperOrchestrator:\n{analysis}")
    
    print("\n7️⃣ CONTEXTUAL SUGGESTIONS")
    print("-"*40)
    context = {
        "error_count": 1,
        "cost_today": 12.50,
        "idle_systems": 1,
        "active_systems": 2
    }
    suggestions = orchestrator.suggestions.get_contextual_suggestions(context)
    print("AI-Powered Suggestions:")
    for suggestion in suggestions:
        print(f"  • {suggestion}")
    
    print("\n8️⃣ NATURAL LANGUAGE COMMAND")
    print("-"*40)
    nl_command = "spawn 50 agents to analyze logs"
    print(f"User: {nl_command}")
    
    risk = orchestrator.personality.analyze_command_risk(nl_command)
    if risk["should_pushback"]:
        response = orchestrator.personality.generate_response(
            "processing",
            command=nl_command
        )
        print(f"SuperOrchestrator: {response}")
    else:
        print(f"SuperOrchestrator: Hell yeah! Spawning 50 agents now!")
    
    print("\n9️⃣ THINKING RESPONSE")
    print("-"*40)
    thinking = orchestrator.personality.generate_response("thinking")
    print(f"SuperOrchestrator: {thinking}")
    
    print("\n🔟 COST WARNING")
    print("-"*40)
    cost_analysis = orchestrator.personality.generate_response(
        "analysis",
        data={
            "health_score": 95,
            "active_systems": 150,
            "cost": 250.00
        }
    )
    print(f"SuperOrchestrator:\n{cost_analysis}")
    
    # Cleanup
    await orchestrator.shutdown()
    
    print("\n" + "="*60)
    print("✅ DEMO COMPLETE - Personality system is fucking awesome!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(demo_personality())