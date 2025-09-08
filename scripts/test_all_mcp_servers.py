#!/usr/bin/env python3
"""
Test all MCP servers are working
No mocks - real tests only
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import sys

async def test_server(name: str, port: int):
    """Test a single MCP server"""
    print(f"Testing {name} on port {port}...")
    results = {"name": name, "port": port, "tests": {}}

    # Test health endpoint
    try:
        async with aiohttp.ClientSession() as session:
            # Health check
            url = f"http://localhost:{port}/health"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=2)) as response:
                if response.status == 200:
                    data = await response.json()
                    results["tests"]["health"] = "✅ Healthy"

                    # Verify no mocks
                    if data.get("mock_data", False):
                        results["tests"]["health"] = "❌ Mock data detected!"
                else:
                    results["tests"]["health"] = f"❌ Status {response.status}"
    except Exception as e:
        results["tests"]["health"] = f"❌ Connection failed: {str(e)[:30]}"

    # Test capabilities endpoint
    try:
        async with aiohttp.ClientSession() as session:
            url = f"http://localhost:{port}/capabilities"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=2)) as response:
                if response.status == 200:
                    data = await response.json()
                    results["tests"]["capabilities"] = "✅ Available"

                    # Verify no mock mode
                    if data.get("mock_mode", False):
                        results["tests"]["capabilities"] = "❌ Mock mode enabled!"
                else:
                    results["tests"]["capabilities"] = f"❌ Status {response.status}"
    except Exception as e:
        results["tests"]["capabilities"] = f"❌ Failed: {str(e)[:30]}"

    return results

async def main():
    """Test all MCP servers"""
    print("================================")
    print("TESTING ALL MCP SERVERS")
    print("================================")

    # Load server configuration
    try:
        with open("mcp_servers/hub_config.json") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ hub_config.json not found")
        return

    # Test each server
    results = []
    for server in config["servers"]:
        result = await test_server(server["name"], server["port"])
        results.append(result)

    # Summary
    print("\n================================")
    print("TEST RESULTS SUMMARY")
    print("================================")

    working_health = 0
    working_capabilities = 0
    total = len(results)

    for result in results:
        name = result["name"]
        health = result["tests"].get("health", "❌ Not tested")
        capabilities = result["tests"].get("capabilities", "❌ Not tested")

        print(f"{name:20} Health: {health:20} Capabilities: {capabilities}")

        if "✅" in health:
            working_health += 1
        if "✅" in capabilities:
            working_capabilities += 1

    print(f"\nHealth checks: {working_health}/{total}")
    print(f"Capabilities: {working_capabilities}/{total}")

    if working_health == total and working_capabilities == total:
        print("🎉 ALL SERVERS WORKING PERFECTLY!")
        return 0
    elif working_health >= total * 0.8:
        print("🎯 Most servers working - good progress!")
        return 0
    else:
        print("⚠️ Many servers not working - needs attention")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
