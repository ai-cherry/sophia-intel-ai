#!/usr/bin/env python3
"""Test Hybrid Provider System"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
import time
from app.core.simple.hybrid_provider import HybridProviderManager, RequirementType
async def test_all_providers():
    """Test all providers with different requirements"""
    provider = HybridProviderManager()
    print("\n" + "=" * 60)
    print("HYBRID PROVIDER SYSTEM TEST")
    print("=" * 60)
    # Show configuration
    print("\n" + provider.get_provider_summary())
    # Test each requirement type
    test_cases = [
        ("Fastest response test", RequirementType.REALTIME),
        ("Complex reasoning test", RequirementType.COMPLEX),
        ("Cost optimization test", RequirementType.CHEAP),
        ("Reliability test", RequirementType.RELIABLE),
        ("Default routing test", RequirementType.DEFAULT),
    ]
    results = []
    print("\n" + "=" * 60)
    print("RUNNING TESTS")
    print("=" * 60)
    for description, req_type in test_cases:
        print(f"\n🧪 {description} [{req_type.value}]")
        try:
            start = time.time()
            result = await provider.complete(
                f"Respond with OK if working. Test: {description}", req_type
            )
            results.append(
                {
                    "test": description,
                    "requirement": req_type.value,
                    "provider": result["provider"],
                    "method": result["method"],
                    "latency_ms": result["latency_ms"],
                    "success": True,
                }
            )
            print(f"  ✅ Provider: {result['provider']} ({result['method']})")
            print(f"     Latency: {result['latency_ms']}ms")
        except Exception as e:
            results.append(
                {
                    "test": description,
                    "requirement": req_type.value,
                    "error": str(e),
                    "success": False,
                }
            )
            print(f"  ❌ Failed: {e}")
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    successful = sum(1 for r in results if r["success"])
    total = len(results)
    print(f"\n✅ Success Rate: {successful}/{total} ({successful/total*100:.0f}%)")
    # Performance stats
    if successful > 0:
        avg_latency = (
            sum(r["latency_ms"] for r in results if r.get("latency_ms")) / successful
        )
        print(f"⚡ Average Latency: {avg_latency:.0f}ms")
    # Provider usage
    provider_usage = {}
    for r in results:
        if r["success"]:
            key = f"{r['provider']} ({r['method']})"
            provider_usage[key] = provider_usage.get(key, 0) + 1
    print("\n📊 Provider Usage:")
    for provider, count in provider_usage.items():
        print(f"  • {provider}: {count} requests")
    # Get final stats
    stats = provider.get_stats()
    print(f"\n💰 Total Cost: ${stats['total_cost']:.4f}")
    return results
if __name__ == "__main__":
    asyncio.run(test_all_providers())
