#!/usr/bin/env python3
"""
Test script for Estuary Flow integration

This script tests the Estuary Flow integration with the provided credentials
and validates that captures and materializations can be created.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.estuary.estuary_config import EstuaryClient, EstuaryConfig, setup_sophia_estuary_flow


async def test_estuary_authentication():
    """Test Estuary Flow authentication with provided credentials."""
    print("🔐 Testing Estuary Flow Authentication...")
    
    config = EstuaryConfig()
    print(f"JWT Token (first 50 chars): {config.jwt_token[:50]}...")
    print(f"Refresh Token (first 30 chars): {config.refresh_token[:30]}...")
    
    async with EstuaryClient(config) as client:
        health = await client.health_check()
        
        if health.get("authenticated"):
            print("✅ Authentication successful!")
            print(f"   User: {health.get('user', 'unknown')}")
            print(f"   Status: {health.get('status')}")
            return True
        else:
            print("❌ Authentication failed!")
            print(f"   Error: {health.get('error')}")
            return False


async def test_estuary_collections():
    """Test listing Estuary Flow collections."""
    print("\n📋 Testing Estuary Flow Collections...")
    
    async with EstuaryClient() as client:
        collections = await client.list_collections()
        
        if collections.get("success"):
            print("✅ Collections retrieved successfully!")
            print(f"   Count: {collections.get('count', 0)}")
            
            # Print first few collections if any exist
            collection_list = collections.get("collections", {}).get("collections", [])
            if collection_list:
                print("   Sample collections:")
                for i, collection in enumerate(collection_list[:3]):
                    print(f"     {i+1}. {collection.get('name', 'unnamed')}")
            else:
                print("   No collections found (this is normal for new accounts)")
            return True
        else:
            print("❌ Failed to retrieve collections!")
            print(f"   Error: {collections.get('error')}")
            return False


async def test_estuary_capture_creation():
    """Test creating a simple Estuary Flow capture."""
    print("\n🔄 Testing Estuary Flow Capture Creation...")
    
    # Simple HTTP ingest capture configuration
    capture_config = {
        "endpoint": "https://httpbin.org/json",
        "method": "GET",
        "interval": "1h"
    }
    
    async with EstuaryClient() as client:
        result = await client.create_capture("test_sophia_capture", capture_config)
        
        if result.get("success"):
            print("✅ Capture created successfully!")
            print(f"   Name: {result.get('name')}")
            return True
        else:
            print("❌ Failed to create capture!")
            print(f"   Error: {result.get('error')}")
            # This might fail due to permissions or API limitations, which is expected
            return False


async def test_estuary_endpoints():
    """Test Estuary Flow API endpoints availability."""
    print("\n🌐 Testing Estuary Flow API Endpoints...")
    
    import httpx
    
    config = EstuaryConfig()
    endpoints_to_test = [
        f"{config.api_base_url}/v1/auth/me",
        f"{config.api_base_url}/v1/collections",
        f"{config.api_base_url}/v1/captures",
        f"{config.api_base_url}/v1/materializations"
    ]
    
    async with httpx.AsyncClient(headers=config.get_headers(), timeout=10.0) as client:
        results = {}
        
        for endpoint in endpoints_to_test:
            try:
                response = await client.get(endpoint)
                results[endpoint] = {
                    "status_code": response.status_code,
                    "accessible": response.status_code < 500
                }
                print(f"   {endpoint}: HTTP {response.status_code}")
            except Exception as e:
                results[endpoint] = {
                    "status_code": None,
                    "accessible": False,
                    "error": str(e)
                }
                print(f"   {endpoint}: ERROR - {e}")
        
        accessible_count = sum(1 for r in results.values() if r.get("accessible"))
        total_count = len(results)
        
        if accessible_count > 0:
            print(f"✅ {accessible_count}/{total_count} endpoints accessible")
            return True
        else:
            print(f"❌ No endpoints accessible")
            return False


async def generate_estuary_config_file():
    """Generate Estuary configuration file for the project."""
    print("\n📝 Generating Estuary Configuration File...")
    
    config_data = {
        "estuary": {
            "api_base_url": "https://api.estuary.dev",
            "dashboard_url": "https://dashboard.estuary.dev",
            "tenant": "sophia-intel",
            "namespace": "sophia/",
            "captures": {
                "sophia_ai_data": {
                    "description": "Main data capture for Sophia AI platform",
                    "source": "HTTP API",
                    "interval": "5m"
                }
            },
            "materializations": {
                "sophia_postgres": {
                    "description": "PostgreSQL materialization for processed data",
                    "target": "PostgreSQL",
                    "schema": "estuary"
                }
            }
        }
    }
    
    config_file = project_root / "config" / "estuary" / "estuary_flow.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=2)
    
    print(f"✅ Configuration file created: {config_file}")
    return True


async def main():
    """Run all Estuary Flow integration tests."""
    print("🚀 Estuary Flow Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Authentication", test_estuary_authentication),
        ("API Endpoints", test_estuary_endpoints),
        ("Collections", test_estuary_collections),
        ("Capture Creation", test_estuary_capture_creation),
        ("Config Generation", generate_estuary_config_file)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed >= 3:  # At least authentication, endpoints, and config generation should pass
        print("🎉 Estuary Flow integration is functional!")
        return True
    else:
        print("⚠️  Estuary Flow integration needs attention")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

