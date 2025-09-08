#!/usr/bin/env python3
import asyncio
import httpx


async def test_full_stack():
    """Test the entire system end-to-end"""
    results = {"passed": [], "failed": []}

    # Test MCP servers
    print("Testing MCP servers...")
    for port in [8081, 8082, 8084, 8085, 8086]:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"http://localhost:{port}/health")
                if resp.status_code == 200:
                    results["passed"].append(f"MCP port {port}")
                else:
                    results["failed"].append(f"MCP port {port}")
        except Exception:
            results["failed"].append(f"MCP port {port} - not running")

    # Test API bridge
    print("Testing API bridge...")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://localhost:8000/api/agents")
            if resp.status_code == 200:
                results["passed"].append("API bridge")
            else:
                results["failed"].append("API bridge")
    except Exception:
        results["failed"].append("API bridge - not running")

    # Test telemetry
    print("Testing telemetry...")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://localhost:5003/api/telemetry/health")
            if resp.status_code == 200:
                results["passed"].append("Telemetry")
            else:
                results["failed"].append("Telemetry")
    except Exception:
        results["failed"].append("Telemetry - not running")

    # Test UI
    print("Testing UI...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:3000")
            if resp.status_code == 200:
                results["passed"].append("UI")
            else:
                results["failed"].append("UI")
    except Exception:
        results["failed"].append("UI - not running")

    # Print results
    print("\n" + "=" * 50)
    print("INTEGRATION TEST RESULTS")
    print("=" * 50)
    print(f"✅ Passed: {len(results['passed'])}")
    for test in results["passed"]:
        print(f"  ✓ {test}")

    if results["failed"]:
        print(f"\n❌ Failed: {len(results['failed'])}")
        for test in results["failed"]:
            print(f"  ✗ {test}")

    return len(results["failed"]) == 0


if __name__ == "__main__":
    success = asyncio.run(test_full_stack())
    raise SystemExit(0 if success else 1)

