#!/usr/bin/env python3
"""
Simple WebSocket test for MCP monitoring
"""

import asyncio

import httpx


async def test_websocket_via_http():
    """Test WebSocket endpoint via HTTP first"""

    print("Testing MCP Server endpoints...\n")

    # Test endpoints
    endpoints = [
        ("MCP Code Review", "http://localhost:8003/health"),
        ("Unified API Root", "http://localhost:8005/"),
        ("Unified API Docs", "http://localhost:8005/docs"),
        ("Teams Endpoint", "http://localhost:8005/teams/"),
        ("MCP Embeddings", "http://localhost:8005/mcp/embeddings"),
    ]

    async with httpx.AsyncClient() as client:
        for name, url in endpoints:
            try:
                response = await client.get(url, timeout=2.0)
                print(f"✅ {name}: Status {response.status_code}")
                if response.status_code == 200:
                    content = response.text[:200]
                    print(f"   Response: {content}...")
            except Exception as e:
                print(f"❌ {name}: {e}")
            print()

    # Check if WebSocket endpoint exists
    print("\nChecking WebSocket endpoint registration...")
    try:
        response = await client.get("http://localhost:8005/docs")
        if "ws/bus" in response.text:
            print("✅ WebSocket endpoint '/ws/bus' is registered")
        else:
            print("⚠️ WebSocket endpoint '/ws/bus' not found in API docs")
    except:
        pass

if __name__ == "__main__":
    asyncio.run(test_websocket_via_http())
