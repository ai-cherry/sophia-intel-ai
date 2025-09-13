#!/usr/bin/env python3
"""Test Platinum swarm directly"""

import asyncio
import json
from pathlib import Path
from builder_cli.lib.env import load_central_env
load_central_env()

from builder_cli.lib.platinum import PlanningSwarm, CodingSwarm, ReviewSwarm, save_artifact


async def test_platinum():
    """Test the Platinum swarm end-to-end"""
    
    task = "Add a hello world function that prints a greeting message"
    
    print("🎯 Testing Platinum Swarm")
    print(f"Task: {task}")
    print("-" * 50)
    
    # 1. Planning
    print("\n📋 PLANNING PHASE")
    planner = PlanningSwarm()
    plan = await planner.run(task)
    save_artifact(plan, "artifacts/platinum/test_plan.json")
    print(f"✅ Plan saved to artifacts/platinum/test_plan.json")
    print(f"   Overview: {plan.overview[:100]}...")
    print(f"   Tasks: {len(plan.tasks)} tasks")
    print(f"   Milestones: {len(plan.milestones)} milestones")
    
    # 2. Coding
    print("\n💻 CODING PHASE")
    coder = CodingSwarm()
    patches = await coder.run(plan)
    save_artifact(patches, "artifacts/platinum/test_patches.json")
    print(f"✅ Patches saved to artifacts/platinum/test_patches.json")
    print(f"   Generated {len(patches)} patches")
    if patches:
        print(f"   First patch targets: {patches[0].file_path}")
    
    # 3. Review
    print("\n🔍 REVIEW PHASE")
    reviewer = ReviewSwarm()
    review = await reviewer.run(plan, patches)
    save_artifact(review, "artifacts/platinum/test_review.json")
    print(f"✅ Review saved to artifacts/platinum/test_review.json")
    print(f"   Approved: {review.approved}")
    print(f"   Coverage: {review.coverage:.1f}%")
    print(f"   Findings: {len(review.findings)} issues")
    
    print("\n" + "=" * 50)
    print("🎉 Platinum Swarm Test Complete!")
    print("Artifacts saved in artifacts/platinum/")
    
    return plan, patches, review


if __name__ == "__main__":
    try:
        asyncio.run(test_platinum())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()