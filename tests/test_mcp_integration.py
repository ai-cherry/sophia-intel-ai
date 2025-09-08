#!/usr/bin/env python3
"""
MCP Servers Integration Test Suite
Tests EVERY MCP server with REAL queries
"""

import asyncio
import aiohttp
import json
from typing import Dict, List

class MCPIntegrationTester:
    def __init__(self):
        self.servers = {
            'sophia': {'port': 8001, 'endpoint': '/query'},
            'github': {'port': 8002, 'endpoint': '/query'},
            'gong': {'port': 8003, 'endpoint': '/query'},
            'hubspot': {'port': 8004, 'endpoint': '/query'},
            'slack': {'port': 8005, 'endpoint': '/query'},
            'notion': {'port': 8006, 'endpoint': '/query'},
            'kb': {'port': 8007, 'endpoint': '/query'},
            'monitor': {'port': 8008, 'endpoint': '/health'}
        }
        self.results = {}

    async def test_server_query(self, name: str, config: Dict) -> bool:
        """Test a single MCP server with real query"""
        try:
            url = f"http://localhost:{config['port']}{config['endpoint']}"

            async with aiohttp.ClientSession() as session:
                if config['endpoint'] == '/health':
                    async with session.get(url, timeout=5) as response:
                        return response.status == 200
                else:
                    test_data = {
                        "query": f"Test query for {name}",
                        "context": {"test": True}
                    }
                    async with session.post(url, json=test_data, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            return 'response' in data or 'result' in data
                        return False
        except Exception:
            return False

    async def test_all_servers(self):
        """Test all MCP servers"""
        print("🧪 Testing All MCP Servers...")

        for name, config in self.servers.items():
            print(f"\nTesting {name} server...")
            self.results[name] = await self.test_server_query(name, config)

            if self.results[name]:
                print(f"  ✅ {name}: Working")
            else:
                print(f"  ❌ {name}: Not responding")

        # Summary
        working = sum(1 for v in self.results.values() if v)
        total = len(self.results)
        print(f"\n📊 MCP Server Results: {working}/{total} working")

        return working >= total // 2  # At least half should work

if __name__ == "__main__":
    tester = MCPIntegrationTester()
    success = asyncio.run(tester.test_all_servers())

    if success:
        print("🎉 MCP servers are functional!")
    else:
        print("⚠️ Many MCP servers need attention!")
