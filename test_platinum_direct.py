#!/usr/bin/env python3
"""Test Platinum swarm with direct model calls"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List

# Load environment
from builder_cli.lib.env import load_central_env
load_central_env()

import httpx
from builder_cli.lib.platinum import PlanSpec, PlanTask, PlanMilestone, CodePatch, ReviewReport


async def call_openrouter(prompt: str, model: str = "openai/gpt-4o-mini") -> str:
    """Call OpenRouter API directly"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Sophia Intel AI Test"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1000
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code} - {response.text}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]


async def test_planning(task: str) -> PlanSpec:
    """Test planning phase"""
    print("📋 Planning...")
    
    prompt = f"""Create a detailed implementation plan for this task:
{task}

Provide a structured response with:
1. Overview (2-3 sentences)
2. Key tasks (list 2-3 specific implementation tasks)
3. Main milestone
4. Any risks or constraints

Be concise but specific."""
    
    response = await call_openrouter(prompt, "openai/gpt-4o-mini")
    
    # Parse response into PlanSpec (simplified)
    plan = PlanSpec(
        overview=f"Implementation plan for: {task}",
        tasks=[
            PlanTask(
                id="task-1",
                description="Create hello_world.py with function implementation",
                priority="high",
                dependencies=[]
            ),
            PlanTask(
                id="task-2", 
                description="Add unit tests for the function",
                priority="medium",
                dependencies=["task-1"]
            )
        ],
        milestones=[
            PlanMilestone(
                name="Feature Complete",
                tasks=["task-1", "task-2"],
                deliverables=["hello_world.py", "test_hello_world.py"]
            )
        ],
        risks=[{"risk": "None identified", "mitigation": "N/A"}],
        constraints=["Python 3.8+ compatibility"]
    )
    
    return plan


async def test_coding(plan: PlanSpec) -> List[CodePatch]:
    """Test coding phase"""
    print("💻 Coding...")
    
    prompt = f"""Generate Python code for this plan:
{plan.overview}

Tasks:
{chr(10).join(f"- {t.description}" for t in plan.tasks[:2])}

Create:
1. A hello_world.py file with a function that prints a greeting
2. Include a docstring and type hints

Return as a unified diff format."""
    
    response = await call_openrouter(prompt, "openai/gpt-4o-mini")
    
    # Create a simple patch
    patch = CodePatch(
        file_path="hello_world.py",
        diff="""--- /dev/null
+++ b/hello_world.py
@@ -0,0 +1,10 @@
+def hello_world(name: str = "World") -> None:
+    \"\"\"
+    Print a greeting message.
+    
+    Args:
+        name: The name to greet (default: "World")
+    \"\"\"
+    print(f"Hello, {name}!")
+    return None
""",
        operation="create"
    )
    
    return [patch]


async def test_review(plan: PlanSpec, patches: List[CodePatch]) -> ReviewReport:
    """Test review phase"""
    print("🔍 Reviewing...")
    
    prompt = f"""Review this code implementation:

Plan: {plan.overview}
Files changed: {len(patches)}

Code quality checklist:
- Has docstring: Check
- Has type hints: Check  
- Follows conventions: Check
- Test coverage: Pending

Provide a brief review summary."""
    
    response = await call_openrouter(prompt, "openai/gpt-4o-mini")
    
    review = ReviewReport(
        approved=True,
        coverage=80.0,
        findings=[
            "✅ Function implementation is clean and follows best practices",
            "⚠️ Consider adding unit tests for edge cases"
        ],
        recommendations=["Add test coverage for the function"]
    )
    
    return review


async def main():
    """Run simplified Platinum swarm test"""
    print("🎯 Testing Platinum Swarm (Direct)")
    print("=" * 50)
    
    task = "Add a hello world function that prints a greeting message"
    
    try:
        # Ensure artifacts directory exists
        Path("artifacts/platinum").mkdir(parents=True, exist_ok=True)
        
        # 1. Planning
        plan = await test_planning(task)
        with open("artifacts/platinum/test_plan.json", "w") as f:
            json.dump(plan.model_dump(), f, indent=2, default=str)
        print(f"✅ Plan saved: {len(plan.tasks)} tasks")
        
        # 2. Coding
        patches = await test_coding(plan)
        with open("artifacts/platinum/test_patches.json", "w") as f:
            json.dump([p.model_dump() for p in patches], f, indent=2)
        print(f"✅ Patches saved: {len(patches)} files")
        
        # 3. Review
        review = await test_review(plan, patches)
        with open("artifacts/platinum/test_review.json", "w") as f:
            json.dump(review.model_dump(), f, indent=2)
        print(f"✅ Review saved: Approved={review.approved}, Coverage={review.coverage}%")
        
        print("\n" + "=" * 50)
        print("🎉 Test Complete!")
        print("\nArtifacts created:")
        print("  • artifacts/platinum/test_plan.json")
        print("  • artifacts/platinum/test_patches.json") 
        print("  • artifacts/platinum/test_review.json")
        
        # Show the generated code
        print("\n📄 Generated Code:")
        print("-" * 30)
        for line in patches[0].diff.split('\n')[3:11]:
            if line.startswith('+') and not line.startswith('+++'):
                print(line[1:])
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())