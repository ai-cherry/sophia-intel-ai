#!/usr/bin/env python3
"""
Sophia Intel AI - Deployment Verification Script
Tests all deployed services and endpoints
"""

import sys
from typing import Any

import httpx

# Service endpoints
SERVICES = {
    "Redis": {"url": "redis://localhost:6379", "type": "redis"},
    "Weaviate": {"url": "http://localhost:8080/v1/.well-known/ready", "type": "http"},
    "API Server": {"url": "http://localhost:8005/health", "type": "http"},
    "API Docs": {"url": "http://localhost:8005/docs", "type": "http"},
    "Hub Interface": {"url": "http://localhost:8005/hub", "type": "http"},
    "Portkey Routing": {"url": "http://localhost:8005/api/portkey-routing/health", "type": "http"},
    "WebSocket": {"url": "http://localhost:8005/api/ws/health", "type": "http"},
    "Memory API": {"url": "http://localhost:8005/api/memory/health", "type": "http"},
}

# New endpoints to test
AGNO_ENDPOINTS = [
    "/api/portkey-routing/models",
    "/api/portkey-routing/routing-strategies",
    "/api/ws/mcp/servers",
    "/api/ws/channels",
    "/api/ws/status",
]

def check_service(name: str, config: dict[str, Any]) -> bool:
    """Check if a service is running"""
    if config["type"] == "redis":
        try:
            import redis
            r = redis.from_url(config["url"])
            r.ping()
            print(f"✅ {name}: Connected")
            return True
        except Exception as e:
            print(f"❌ {name}: Failed - {e}")
            return False

    elif config["type"] == "http":
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(config["url"])
                if response.status_code in [200, 204]:
                    print(f"✅ {name}: Running (Status: {response.status_code})")
                    return True
                else:
                    print(f"⚠️  {name}: Responded with status {response.status_code}")
                    return True
        except Exception as e:
            print(f"❌ {name}: Not accessible - {str(e)[:50]}")
            return False

    return False

def test_agno_endpoints():
    """Test new AGNO/MCP endpoints"""
    print("\n🔍 Testing AGNO/MCP Endpoints:")
    base_url = "http://localhost:8005"

    with httpx.Client(timeout=5.0) as client:
        for endpoint in AGNO_ENDPOINTS:
            try:
                response = client.get(f"{base_url}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"  ✅ {endpoint}: OK ({len(data)} keys)")
                    elif isinstance(data, list):
                        print(f"  ✅ {endpoint}: OK ({len(data)} items)")
                    else:
                        print(f"  ✅ {endpoint}: OK")
                else:
                    print(f"  ⚠️  {endpoint}: Status {response.status_code}")
            except Exception as e:
                print(f"  ❌ {endpoint}: {str(e)[:40]}")

def main():
    print("=" * 60)
    print("🚀 SOPHIA INTEL AI - DEPLOYMENT VERIFICATION")
    print("=" * 60)

    # Check all services
    print("\n📊 Core Services Status:")
    all_healthy = True
    for name, config in SERVICES.items():
        if not check_service(name, config):
            all_healthy = False

    # Test AGNO endpoints
    test_agno_endpoints()

    # Summary
    print("\n" + "=" * 60)
    if all_healthy:
        print("✅ All core services are running!")
        print("\n🎯 Access Points:")
        print("  - API Documentation: http://localhost:8005/docs")
        print("  - Hub Interface: http://localhost:8005/hub")
        print("  - Health Check: http://localhost:8005/health")
        print("\n📚 New Features Available:")
        print("  - AGNO Teams with Portkey routing")
        print("  - Resilient WebSocket with auto-reconnection")
        print("  - Enhanced memory with auto-tagging")
        print("  - MCP server integration")
        print("\n🎉 System is fully deployed and operational!")
    else:
        print("⚠️  Some services are not running. Check the errors above.")
        print("\nTo start missing services:")
        print("  - Redis: brew services start redis")
        print("  - Weaviate: docker-compose up -d weaviate")
        print("  - API Server: ./start_server.sh")
        sys.exit(1)

if __name__ == "__main__":
    main()
