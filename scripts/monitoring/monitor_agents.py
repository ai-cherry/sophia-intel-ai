#!/usr/bin/env python3
"""
Monitor Agno/MCP — AgentOps for prod insights
"""

import asyncio
import os
from datetime import datetime

import aiohttp
import redis

# Import AgentOps if available, otherwise graceful degradation
try:
    import agentops

    agentops_available = True
except ImportError:
    agentops_available = False
    print("⚠️ AgentOps not installed - monitoring without telemetry")


async def check_mcp_health():
    """Check health of all MCP servers"""
    servers = [
        ("ai_providers", 8001),
        ("enhanced_enterprise", 8002),
        ("github", 8003),
        ("gong", 8004),
        ("hubspot", 8005),
        ("slack", 8006),
        ("notion", 8007),
        ("kb", 8008),
        ("monitor", 8009),
        ("data", 8010),
    ]

    results = {}
    async with aiohttp.ClientSession() as session:
        for name, port in servers:
            try:
                async with session.get(
                    f"http://localhost:{port}/health", timeout=5
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if not data.get("mock", False):
                            results[name] = "✅ Healthy (Real)"
                        else:
                            results[name] = "❌ Mock alert!"
                    else:
                        results[name] = f"❌ HTTP {resp.status}"
            except asyncio.TimeoutError:
                results[name] = "❌ Timeout"
            except Exception as e:
                results[name] = f"❌ Error: {str(e)[:30]}"

    return results


async def monitor_redis_memory():
    """Monitor Redis memory usage and keys"""
    try:
        r = redis.from_url(os.getenv("REDIS_URL", "${REDIS_URL}"))
        info = r.info()
        return {
            "status": "✅ Connected",
            "used_memory": info["used_memory_human"],
            "keys": r.dbsize(),
            "connected_clients": info["connected_clients"],
        }
    except Exception as e:
        return {"status": f"❌ Error: {str(e)[:50]}"}


async def monitor_qdrant():
    """Monitor Qdrant vector database"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:6333/collections", timeout=5
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    collections = data.get("result", {}).get("collections", [])
                    return {"status": "✅ Connected", "collections": len(collections)}
                else:
                    return {"status": f"❌ HTTP {resp.status}"}
    except Exception as e:
        return {"status": f"❌ Error: {str(e)[:50]}"}


async def monitor_neo4j():
    """Monitor Neo4j graph database"""
    try:
        # Simple HTTP check for Neo4j HTTP API
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:7474", timeout=5) as resp:
                if resp.status == 200:
                    return {"status": "✅ Connected"}
                else:
                    return {"status": f"❌ HTTP {resp.status}"}
    except Exception as e:
        return {"status": f"❌ Error: {str(e)[:50]}"}


async def main():
    """Main monitoring function"""
    if agentops_available and os.getenv("AGENTOPS_API_KEY"):
        agentops.init()

    print("🔍 Sophia AI Fortress Monitor — Real Metrics Only")
    print("=" * 60)

    # Check MCP servers
    print("\n📡 MCP Servers:")
    mcp_health = await check_mcp_health()
    for server, status in mcp_health.items():
        print(f"  {server:20}: {status}")

    # Check databases
    print("\n🗄️ Databases:")

    redis_stats = await monitor_redis_memory()
    print(f"  Redis:              {redis_stats['status']}")
    if "used_memory" in redis_stats:
        print(
            f"    Memory: {redis_stats['used_memory']} | Keys: {redis_stats['keys']} | Clients: {redis_stats['connected_clients']}"
        )

    qdrant_stats = await monitor_qdrant()
    print(f"  Qdrant:             {qdrant_stats['status']}")
    if "collections" in qdrant_stats:
        print(f"    Collections: {qdrant_stats['collections']}")

    neo4j_stats = await monitor_neo4j()
    print(f"  Neo4j:              {neo4j_stats['status']}")

    # Summary
    healthy_mcp = sum(1 for status in mcp_health.values() if "✅" in status)
    total_mcp = len(mcp_health)

    print("\n📊 Summary:")
    print(f"  MCP Servers: {healthy_mcp}/{total_mcp} healthy")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if agentops_available and os.getenv("AGENTOPS_API_KEY"):
        agentops.log(
            f"Monitoring complete - {healthy_mcp}/{total_mcp} MCP servers healthy"
        )
        agentops.stop()


if __name__ == "__main__":
    asyncio.run(main())
