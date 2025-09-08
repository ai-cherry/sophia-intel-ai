#!/usr/bin/env python3
"""
Test Artemis agent creation and model assignments.
Verifies that task-specific models are correctly configured.
"""
import asyncio
import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.swarms.artemis.agent_factory import ArtemisAgentFactory


async def test_agent_creation():
    """Test creating each type of Artemis agent."""

    print("Testing Artemis Agent Factory\n" + "=" * 40)

    agent_types = [
        ("code_review", "Code Reviewer"),
        ("refactor", "Refactorer"),
        ("test", "Test Generator"),
        ("architecture", "Architect"),
        ("security", "Security Auditor"),
        ("docs", "Documentation Writer"),
    ]

    results = []

    for task_type, description in agent_types:
        try:
            # Load task config
            config = ArtemisAgentFactory.load_task_config(task_type)

            # Create agent
            agent = ArtemisAgentFactory.create_agent(task_type)

            result = {
                "task": task_type,
                "description": description,
                "success": True,
                "provider": config.provider,
                "model": config.model,
                "agent_name": agent.profile.name,
            }

            print(f"✓ {description}:")
            print(f"  Provider: {config.provider}")
            print(f"  Model: {config.model}")
            print()

        except Exception as e:
            result = {
                "task": task_type,
                "description": description,
                "success": False,
                "error": str(e),
            }

            print(f"✗ {description}:")
            print(f"  Error: {e}")
            print()

        results.append(result)

    # Summary
    print("\nSummary:")
    print("-" * 40)
    successful = sum(1 for r in results if r["success"])
    print(f"Successfully configured: {successful}/{len(results)}")

    # Missing configurations
    failed = [r for r in results if not r["success"]]
    if failed:
        print("\nMissing configurations:")
        for r in failed:
            print(f"  - {r['description']}: {r.get('error', 'Unknown error')}")

    return results


async def test_agent_execution():
    """Test actual agent execution with a simple task."""

    print("\n\nTesting Agent Execution\n" + "=" * 40)

    # Only test if quick_check is configured (uses Groq for speed)
    try:
        agent = ArtemisAgentFactory.create_agent("quick_check", "test_agent")

        print("Testing quick check agent with simple task...")
        result = await agent.process_task(
            "Respond with 'OK' if you're ready.", context={"test": True}
        )

        print(f"Response: {result['result'][:100]}")
        print(f"Model: {result['model_used']}")
        print(f"Tokens: {result.get('tokens', 'N/A')}")

    except Exception as e:
        print(f"Execution test skipped: {e}")


def main():
    """Run all tests."""

    # Load environment
    env_file = ".env.artemis.local"
    if os.path.exists(env_file):
        print(f"Loading environment from {env_file}\n")
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    parts = line.strip().split("=", 1)
                    if len(parts) == 2:
                        os.environ[parts[0]] = parts[1]

    # Run tests
    asyncio.run(test_agent_creation())

    # Optionally test execution
    if "--execute" in sys.argv:
        asyncio.run(test_agent_execution())
    else:
        print("\nTo test actual LLM execution, run with --execute flag")

    return 0


if __name__ == "__main__":
    sys.exit(main())
