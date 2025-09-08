#!/usr/bin/env python3
"""
Artemis Collaboration Demo
Demonstrates the full workflow: analyze → propose → review → apply
"""
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mcp.clients.stdio_client import detect_stdio_mcp
from app.swarms.artemis.agent_factory import ArtemisAgentFactory


async def demo_workflow():
    """Demonstrate the Artemis collaboration workflow."""

    print("Artemis Collaboration Demo")
    print("=" * 60)

    # Initialize MCP client
    client = detect_stdio_mcp(Path.cwd())
    if not client:
        print("ERROR: MCP stdio server not available")
        return 1

    print("✓ MCP client connected\n")

    # 1. Create a simple test file for analysis
    test_file = "tmp/demo_code.py"
    test_code = """
def calculate_average(numbers):
    # Calculate average of list
    total = 0
    for n in numbers:
        total = total + n
    avg = total / len(numbers)
    return avg

def find_max(items):
    max_val = items[0]
    for item in items:
        if item > max_val:
            max_val = item
    return max_val
"""

    print(f"Creating test file: {test_file}")
    client.fs_write(test_file, test_code)
    print("✓ Test file created\n")

    # 2. Code Review Phase
    print("Phase 1: Code Review")
    print("-" * 40)

    try:
        reviewer = ArtemisAgentFactory.create_code_reviewer()
        review_result = await reviewer.process_task(
            f"Review this Python code and identify improvements:\n{test_code}",
            context={"file": test_file},
        )

        # Store review in memory
        client.memory_add(
            topic=f"Code Review: {test_file}",
            content=json.dumps(
                {
                    "file": test_file,
                    "review": review_result["result"][:500],
                    "status": "pending_action",
                    "model": review_result["model_used"],
                }
            ),
            source="artemis_reviewer",
            tags=["review", "code_review", "demo"],
            memory_type="semantic",
        )

        print(f"Review completed by: {review_result['model_used']}")
        print(f"Review (truncated): {review_result['result'][:200]}...")
        print("✓ Review stored in memory\n")

    except Exception as e:
        print(f"Review skipped: {e}\n")

    # 3. Refactoring Proposal Phase
    print("Phase 2: Refactoring Proposal")
    print("-" * 40)

    refactor_prompt = """Refactor these functions to be more Pythonic:
1. Use sum() for calculate_average
2. Use max() for find_max
3. Add type hints
4. Add docstrings
Provide the complete refactored code."""

    try:
        refactorer = ArtemisAgentFactory.create_refactorer()
        refactor_result = await refactorer.process_task(
            refactor_prompt + f"\n\nOriginal code:\n{test_code}", context={"file": test_file}
        )

        # Create a proposal
        proposal_id = f"proposal_demo_{test_file.replace('/', '_')}"
        client.memory_add(
            topic=f"Refactor Proposal: {test_file}",
            content=json.dumps(
                {
                    "proposal_id": proposal_id,
                    "file": test_file,
                    "changes": refactor_result["result"][:1000],
                    "status": "pending_review",
                    "model": refactor_result["model_used"],
                }
            ),
            source="artemis_refactor",
            tags=["proposal", "pending_review", "refactor", "demo"],
            memory_type="procedural",
        )

        print(f"Proposal created by: {refactor_result['model_used']}")
        print(f"Proposal ID: {proposal_id}")
        print("✓ Proposal stored in memory\n")

    except Exception as e:
        print(f"Refactoring skipped: {e}\n")

    # 4. Query pending proposals (simulating Claude's review)
    print("Phase 3: Query Pending Proposals")
    print("-" * 40)

    pending = client.memory_search("proposal pending_review", limit=5)
    print(f"Found {len(pending)} pending proposals:")
    for p in pending:
        print(f"  - {p.get('topic', 'Unknown')}")
    print()

    # 5. Simulate approval (in real workflow, Claude would do this)
    print("Phase 4: Simulate Approval")
    print("-" * 40)

    if pending:
        # Mark first proposal as approved
        client.memory_add(
            topic=f"Review Approval: {proposal_id}",
            content=json.dumps(
                {
                    "proposal_id": proposal_id,
                    "status": "approved",
                    "comments": "Changes look good. Type hints and built-in functions improve readability.",
                    "reviewed_by": "demo_simulator",
                }
            ),
            source="review_system",
            tags=["review", "approved", "demo"],
            memory_type="episodic",
        )
        print(f"✓ Proposal {proposal_id} approved\n")

    # 6. Test Generation Phase
    print("Phase 5: Test Generation")
    print("-" * 40)

    try:
        tester = ArtemisAgentFactory.create_test_generator()
        test_result = await tester.process_task(
            f"Generate pytest unit tests for these functions:\n{test_code}",
            context={"file": test_file},
        )

        # Store test proposal
        client.memory_add(
            topic=f"Test Suite: {test_file}",
            content=json.dumps(
                {
                    "file": test_file,
                    "tests": test_result["result"][:1000],
                    "model": test_result["model_used"],
                }
            ),
            source="artemis_tester",
            tags=["test", "unit_test", "demo"],
            memory_type="procedural",
        )

        print(f"Tests generated by: {test_result['model_used']}")
        print("✓ Test suite stored in memory\n")

    except Exception as e:
        print(f"Test generation skipped: {e}\n")

    # 7. Summary
    print("Workflow Summary")
    print("=" * 60)

    # Query all demo-related entries
    demo_entries = client.memory_search("demo", limit=10)
    print(f"Total entries created: {len(demo_entries)}")

    for entry in demo_entries:
        print(f"\n{entry.get('topic', 'Unknown')}:")
        print(f"  Source: {entry.get('source', 'Unknown')}")
        print(f"  Tags: {', '.join(entry.get('tags', []))}")
        print(f"  Type: {entry.get('memory_type', 'Unknown')}")

    print("\n✓ Demonstration complete!")
    print("\nTo continue collaboration:")
    print("1. Claude can query proposals: memory.search('proposal pending_review')")
    print("2. Claude approves/rejects: memory.add with status='approved'")
    print("3. Artemis applies approved changes: fs.write")
    print("4. Both agents can track progress: memory.search('demo')")

    return 0


def main():
    """Run the demo."""

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

    return asyncio.run(demo_workflow())


if __name__ == "__main__":
    sys.exit(main())
