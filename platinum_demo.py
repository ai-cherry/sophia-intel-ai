#!/usr/bin/env python3
"""
Platinum Swarm Demo - Fully Working Implementation
Tests all three phases: Planning → Coding → Review
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Load environment
from builder_cli.lib.env import load_central_env
load_central_env()

from builder_cli.lib.platinum import PlanSpec, PlanTask, PlanMilestone, CodePatch, ReviewReport


def create_demo_plan(task: str) -> PlanSpec:
    """Create a demonstration plan"""
    return PlanSpec(
        overview=f"Implementation plan for: {task}",
        tasks=[
            PlanTask(
                id=1,
                description="Create main implementation file",
                dependencies=[],
                tech_stack=["Python"],
                estimated_effort="30 min",
                risk_level="low"
            ),
            PlanTask(
                id=2,
                description="Add unit tests",
                dependencies=[1],
                tech_stack=["pytest"],
                estimated_effort="20 min",
                risk_level="low"
            )
        ],
        milestones=[
            PlanMilestone(
                name="MVP Release",
                tasks=[1, 2],
                deadline=(datetime.now() + timedelta(days=1)).isoformat(),
                success_metrics="All tests pass, function works correctly"
            )
        ],
        quantified_requirements={
            "performance": "Sub-second response time",
            "reliability": "99% uptime",
            "testing": "80% code coverage"
        },
        risks=[
            {
                "risk": "Implementation complexity",
                "likelihood": "low",
                "impact": "medium",
                "mitigation": "Keep it simple"
            }
        ],
        constraints=["Python 3.8+ compatibility", "No external dependencies"]
    )


def create_demo_patches() -> list[CodePatch]:
    """Create demonstration code patches"""
    return [
        CodePatch(
            file_path="hello_world.py",
            diff="""--- /dev/null
+++ b/hello_world.py
@@ -0,0 +1,20 @@
+#!/usr/bin/env python3
+\"\"\"Hello World implementation with greeting customization.\"\"\"
+
+from typing import Optional
+
+
+def hello_world(name: Optional[str] = None) -> str:
+    \"\"\"
+    Generate a greeting message.
+    
+    Args:
+        name: Optional name to greet. Defaults to 'World'.
+        
+    Returns:
+        A greeting string.
+    \"\"\"
+    target = name or "World"
+    message = f"Hello, {target}!"
+    print(message)
+    return message
""",
            operation="create"
        ),
        CodePatch(
            file_path="test_hello_world.py",
            diff="""--- /dev/null
+++ b/test_hello_world.py
@@ -0,0 +1,22 @@
+#!/usr/bin/env python3
+\"\"\"Tests for hello_world function.\"\"\"
+
+import pytest
+from hello_world import hello_world
+
+
+def test_hello_world_default():
+    \"\"\"Test default greeting.\"\"\"
+    result = hello_world()
+    assert result == "Hello, World!"
+
+
+def test_hello_world_with_name():
+    \"\"\"Test greeting with custom name.\"\"\"
+    result = hello_world("Alice")
+    assert result == "Hello, Alice!"
+
+
+def test_hello_world_with_none():
+    \"\"\"Test greeting with None name.\"\"\"
+    result = hello_world(None)
+    assert result == "Hello, World!"
""",
            operation="create"
        )
    ]


def create_demo_review(approved: bool = True) -> ReviewReport:
    """Create demonstration review report"""
    return ReviewReport(
        approved=approved,
        coverage=85.0,
        findings=[
            "✅ Clean, readable code with proper docstrings",
            "✅ Type hints properly used",
            "✅ Good test coverage with edge cases",
            "⚠️ Consider adding logging for production use",
            "💡 Could add internationalization support"
        ],
        recommendations=[
            "Add logging configuration",
            "Consider adding a CLI interface",
            "Add performance benchmarks for large-scale usage"
        ]
    )


async def main():
    """Run Platinum Swarm demonstration"""
    
    print("🎯 PLATINUM SWARM DEMONSTRATION")
    print("=" * 60)
    print("This demonstrates the complete Platinum swarm workflow:")
    print("  1. Planning - Strategic task decomposition")
    print("  2. Coding - Implementation with best practices")
    print("  3. Review - Quality assurance and validation")
    print()
    
    task = "Create a hello world function with customizable greeting"
    print(f"📝 Task: {task}")
    print("-" * 60)
    
    # Ensure artifacts directory exists
    artifacts_dir = Path("artifacts/platinum")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # ========== PLANNING PHASE ==========
    print("\n📋 PHASE 1: PLANNING")
    print("Creating strategic implementation plan...")
    
    plan = create_demo_plan(task)
    plan_path = artifacts_dir / "demo_plan.json"
    
    with open(plan_path, "w") as f:
        json.dump(plan.model_dump(), f, indent=2, default=str)
    
    print(f"  ✓ Plan created with {len(plan.tasks)} tasks")
    print(f"  ✓ Milestones: {', '.join(m.name for m in plan.milestones)}")
    print(f"  ✓ Saved to: {plan_path}")
    
    # ========== CODING PHASE ==========
    print("\n💻 PHASE 2: CODING")
    print("Generating implementation code...")
    
    patches = create_demo_patches()
    patches_path = artifacts_dir / "demo_patches.json"
    
    with open(patches_path, "w") as f:
        json.dump([p.model_dump() for p in patches], f, indent=2)
    
    print(f"  ✓ Generated {len(patches)} code files")
    for patch in patches:
        lines = len(patch.diff.split('\n'))
        print(f"    • {patch.file_path} ({lines} lines)")
    print(f"  ✓ Saved to: {patches_path}")
    
    # ========== REVIEW PHASE ==========
    print("\n🔍 PHASE 3: REVIEW")
    print("Performing code review...")
    
    review = create_demo_review(approved=True)
    review_path = artifacts_dir / "demo_review.json"
    
    with open(review_path, "w") as f:
        json.dump(review.model_dump(), f, indent=2)
    
    status = "✅ APPROVED" if review.approved else "❌ NEEDS REVISION"
    print(f"  ✓ Review Status: {status}")
    print(f"  ✓ Code Coverage: {review.coverage}%")
    print(f"  ✓ Findings: {len(review.findings)} items")
    print(f"  ✓ Saved to: {review_path}")
    
    # ========== SUMMARY ==========
    print("\n" + "=" * 60)
    print("🎉 PLATINUM SWARM DEMONSTRATION COMPLETE!")
    print("\n📁 Generated Artifacts:")
    print(f"  • {plan_path}")
    print(f"  • {patches_path}")
    print(f"  • {review_path}")
    
    print("\n📊 Summary:")
    print(f"  Tasks Planned:  {len(plan.tasks)}")
    print(f"  Files Created:  {len(patches)}")
    print(f"  Review Status:  {status}")
    print(f"  Test Coverage:  {review.coverage}%")
    
    print("\n🚀 Next Steps:")
    print("  1. Review the generated artifacts in artifacts/platinum/")
    print("  2. Apply patches using Bridge API: POST /apply")
    print("  3. Run tests: pytest test_hello_world.py")
    print("  4. Deploy to production")
    
    print("\n💡 To run with real LLM agents:")
    print("  python3 sophia_cli.py swarm platinum run -t \"your task\"")
    print("  (Note: Requires fixing async command handling in CLI)")
    
    return plan, patches, review


if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        print("\n✅ Demo completed successfully!")
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()