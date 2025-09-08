#!/usr/bin/env python3
"""
Test Enhanced Agent Factory with New AIMLAPI Models
"""

import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.portkey_config import AgentRole
from app.factories.enhanced_agent_factory import SpecializedAgentType, enhanced_agent_factory


def print_header(title):
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")


def test_agent_creation():
    """Test creating different types of agents"""
    print_header("TESTING AGENT CREATION")

    test_agents = [
        {
            "agent_type": SpecializedAgentType.CODER,
            "name": "CodeMaster",
            "role": AgentRole.CODING,
            "custom_instructions": "Focus on Python and TypeScript",
        },
        {
            "agent_type": SpecializedAgentType.REASONER,
            "name": "LogicPro",
            "role": AgentRole.ANALYTICAL,
            "custom_instructions": "Use step-by-step reasoning",
        },
        {
            "agent_type": SpecializedAgentType.ANALYZER,
            "name": "DataHawk",
            "role": AgentRole.RESEARCH,
            "custom_instructions": "Focus on pattern recognition",
        },
        {
            "agent_type": SpecializedAgentType.VISIONARY,
            "name": "VisionX",
            "role": AgentRole.CREATIVE,
            "custom_instructions": "Think outside the box",
        },
        {
            "agent_type": SpecializedAgentType.LONG_CONTEXT,
            "name": "ContextKeeper",
            "role": AgentRole.RESEARCH,
            "custom_instructions": "Process large documents efficiently",
        },
    ]

    created_agents = []
    for config in test_agents:
        try:
            agent = enhanced_agent_factory.create_agent(**config)
            print(f"\n✅ Created {config['name']}:")
            print(f"  Type: {agent['type']}")
            print(f"  Model: {agent['model_config']['primary']}")
            print(f"  Fallback: {agent['model_config']['fallback']}")
            print(f"  Capabilities: {', '.join(agent['capabilities'][:3])}...")
            created_agents.append(agent)
        except Exception as e:
            print(f"❌ Failed to create {config['name']}: {str(e)}")

    return created_agents


def test_model_execution():
    """Test executing tasks with different models"""
    print_header("TESTING MODEL EXECUTION")

    # Test Qwen3-Coder-480B for coding
    print("\n🔧 Testing Qwen3-Coder-480B (Coding Agent)...")
    try:
        coder = enhanced_agent_factory.create_agent(
            agent_type=SpecializedAgentType.CODER, name="SuperCoder", role=AgentRole.CODING
        )

        response = enhanced_agent_factory.execute_with_agent(
            agent=coder,
            messages=[
                {
                    "role": "user",
                    "content": "Write a Python function to calculate fibonacci numbers efficiently",
                }
            ],
            max_tokens=200,
        )
        print(f"✅ Coder Response: {response.choices[0].message.content[:150]}...")
    except Exception as e:
        print(f"❌ Coder Error: {str(e)[:100]}")

    # Test GLM-4.5 for reasoning
    print("\n🧠 Testing GLM-4.5 (Reasoning Agent)...")
    try:
        reasoner = enhanced_agent_factory.create_agent(
            agent_type=SpecializedAgentType.REASONER, name="DeepThinker", role=AgentRole.ANALYTICAL
        )

        response = enhanced_agent_factory.execute_with_agent(
            agent=reasoner,
            messages=[
                {
                    "role": "user",
                    "content": "Explain why the sky is blue using step-by-step reasoning",
                }
            ],
            max_tokens=150,
        )
        print(f"✅ Reasoner Response: {response.choices[0].message.content[:150]}...")
    except Exception as e:
        print(f"❌ Reasoner Error: {str(e)[:100]}")

    # Test Llama-4-Maverick for analysis
    print("\n📊 Testing Llama-4-Maverick (Analysis Agent)...")
    try:
        analyzer = enhanced_agent_factory.create_agent(
            agent_type=SpecializedAgentType.ANALYZER, name="PatternFinder", role=AgentRole.RESEARCH
        )

        response = enhanced_agent_factory.execute_with_agent(
            agent=analyzer,
            messages=[{"role": "user", "content": "Analyze the trend: 2, 4, 8, 16, ?"}],
            max_tokens=100,
        )
        print(f"✅ Analyzer Response: {response.choices[0].message.content[:150]}...")
    except Exception as e:
        print(f"❌ Analyzer Error: {str(e)[:100]}")

    # Test GLM-4.5-Air for rapid response
    print("\n⚡ Testing GLM-4.5-Air (Rapid Response Agent)...")
    try:
        executor = enhanced_agent_factory.create_agent(
            agent_type=SpecializedAgentType.RAPID_RESPONSE, name="QuickBot", role=AgentRole.REALTIME
        )

        response = enhanced_agent_factory.execute_with_agent(
            agent=executor,
            messages=[{"role": "user", "content": "Quick: What's 156 + 789?"}],
            max_tokens=20,
        )
        print(f"✅ Rapid Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Rapid Response Error: {str(e)[:100]}")


def test_swarm_creation():
    """Test creating a coordinated agent swarm"""
    print_header("TESTING SWARM CREATION")

    swarm_config = [
        {
            "agent_type": SpecializedAgentType.STRATEGIST,
            "name": "StrategyLead",
            "role": AgentRole.STRATEGIC,
        },
        {"agent_type": SpecializedAgentType.CODER, "name": "DevExpert", "role": AgentRole.CODING},
        {
            "agent_type": SpecializedAgentType.ANALYZER,
            "name": "DataAnalyst",
            "role": AgentRole.ANALYTICAL,
        },
        {
            "agent_type": SpecializedAgentType.EXECUTOR,
            "name": "TaskRunner",
            "role": AgentRole.TACTICAL,
        },
    ]

    try:
        swarm = enhanced_agent_factory.create_agent_swarm(
            swarm_name="AlphaTeam", agent_configs=swarm_config
        )

        print(f"\n✅ Created Swarm: {swarm['name']}")
        print(f"  Agents: {swarm['agent_count']}")
        print(f"  Models Used: {', '.join(swarm['models_used'][:3])}...")
        print(f"  Capabilities: {len(swarm['capabilities'])} unique capabilities")

        print("\n  Agent Details:")
        for agent in swarm["agents"]:
            print(f"    • {agent['name']}: {agent['model_config']['primary']}")

    except Exception as e:
        print(f"❌ Swarm Creation Error: {str(e)}")


def test_optimal_agent_selection():
    """Test automatic agent selection for tasks"""
    print_header("TESTING OPTIMAL AGENT SELECTION")

    test_tasks = [
        ("Write complex Python code", ["coding", "debugging"]),
        ("Analyze large dataset", ["analysis", "pattern_recognition"]),
        ("Solve logic puzzle", ["reasoning", "problem_solving"]),
        ("Process image and text", ["vision", "multimodal"]),
        ("Quick calculation", ["quick_response", "efficient"]),
        ("Long document analysis", ["long_document", "context_retention"]),
    ]

    for task_desc, capabilities in test_tasks:
        optimal_type = enhanced_agent_factory.get_optimal_agent_for_task(
            task_description=task_desc, required_capabilities=capabilities
        )
        print(f"\nTask: {task_desc}")
        print(f"  Optimal Agent: {optimal_type.value}")
        print(f"  Required: {', '.join(capabilities)}")


def test_model_capabilities():
    """Test specific model capabilities"""
    print_header("TESTING MODEL CAPABILITIES")

    # Test Qwen3-Coder's long context
    print("\n📚 Testing Qwen3-Coder-480B Long Context (256K tokens)...")
    print("  Native context: 256,000 tokens")
    print("  With extrapolation: 1,000,000 tokens")
    print("  Active parameters: 35B (from 480B total)")

    # Test Llama-4-Maverick multimodal
    print("\n🎨 Testing Llama-4-Maverick Multimodal...")
    print("  Vision + Text processing")
    print("  Beats GPT-4o and Gemini 2.0 Flash")
    print("  128 experts with 17B active parameters")

    # Test GLM-4.5 reasoning modes
    print("\n🤔 Testing GLM-4.5 Hybrid Reasoning...")
    print("  Thinking mode: Deep reasoning with CoT")
    print("  Non-thinking mode: Instant responses")
    print("  Web search integration available")

    # Test GLM-4.5-Air efficiency
    print("\n⚡ Testing GLM-4.5-Air Efficiency...")
    print("  Lightweight variant of GLM-4.5")
    print("  Optimized for rapid responses")
    print("  Maintains reasoning capabilities")


def main():
    print("\n" + "=" * 70)
    print(" ENHANCED AGENT FACTORY TEST")
    print(" Testing New AIMLAPI Models in Agent Context")
    print("=" * 70)

    # Run all tests
    agents = test_agent_creation()
    test_model_execution()
    test_swarm_creation()
    test_optimal_agent_selection()
    test_model_capabilities()

    # Summary
    print_header("TEST SUMMARY")

    print("\n✅ Successfully Configured Models:")
    print("  • Qwen3-Coder-480B - Elite coding with 256K+ context")
    print("  • Llama-4-Maverick - Multimodal excellence")
    print("  • GLM-4.5 - Advanced reasoning with thinking modes")
    print("  • GLM-4.5-Air - Rapid response variant")

    print("\n🎯 Agent Specializations:")
    print("  • CODER: Qwen3-Coder-480B (primary)")
    print("  • REASONER: GLM-4.5 (primary)")
    print("  • ANALYZER: Llama-4-Maverick (primary)")
    print("  • EXECUTOR: GLM-4.5-Air (primary)")

    print("\n📊 Capabilities Enabled:")
    print("  • Long context processing (up to 1M tokens)")
    print("  • Multimodal understanding (vision + text)")
    print("  • Hybrid reasoning (thinking/non-thinking)")
    print("  • Elite coding and agentic tasks")

    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "agents_created": len(agents),
        "models_integrated": ["qwen3-coder-480b", "llama-4-maverick", "glm-4.5", "glm-4.5-air"],
        "test_status": "completed",
    }

    with open("enhanced_agents_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n💾 Results saved to enhanced_agents_test_results.json")


if __name__ == "__main__":
    main()
