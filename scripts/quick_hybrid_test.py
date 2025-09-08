#!/usr/bin/env python3
"""Quick test of hybrid provider system"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from app.core.simple.hybrid_provider import HybridProviderManager, RequirementType


async def quick_test():
    """Quick test with one request per type"""
    provider = HybridProviderManager()

    print("HYBRID PROVIDER QUICK TEST")
    print("=" * 50)
    print(provider.get_provider_summary())
    print("=" * 50)

    # Test one request per type
    tests = [
        ("fast", RequirementType.REALTIME),
        ("complex", RequirementType.COMPLEX),
        ("cheap", RequirementType.CHEAP),
        ("default", RequirementType.DEFAULT),
    ]

    success = 0
    for name, req_type in tests:
        print(f"\nTest: {name} [{req_type.value}]")
        try:
            result = await provider.complete("Say OK if working", req_type, temperature=0)
            print(f"✅ {result['provider']} ({result['method']}): {result['latency_ms']}ms")
            success += 1
        except Exception as e:
            print(f"❌ Failed: {str(e)[:100]}")

    print(f"\n{'='*50}")
    print(f"Success: {success}/{len(tests)}")
    stats = provider.get_stats()
    print(f"Total Cost: ${stats['total_cost']:.4f}")

    return success == len(tests)


if __name__ == "__main__":
    success = asyncio.run(quick_test())
    exit(0 if success else 1)
