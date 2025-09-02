#!/usr/bin/env python3
"""
Test script to verify MCP server connection and shared memory functionality
"""

import requests
import json
import sys

def test_mcp_server():
    """Test MCP server health and basic functionality"""
    base_url = "http://localhost:8004"
    
    print("🔍 Testing MCP Server Connection...")
    print("=" * 50)
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ MCP server health check: PASSED")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Version: {health_data.get('version')}")
            print(f"   Systems: {health_data.get('systems')}")
        else:
            print(f"❌ MCP server health check: FAILED (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ MCP server health check: FAILED (Error: {e})")
        return False
    
    # Test 2: Add memory (simulating Roo)
    try:
        memory_data = {
            "content": "Test from Roo",
            "topic": "mcp_verification",
            "source": "roo",
            "tags": ["test", "verification"],
            "memory_type": "semantic"
        }
        response = requests.post(f"{base_url}/mcp/memory/add", json=memory_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            print("✅ Memory storage (Roo simulation): PASSED")
            print(f"   Memory ID: {result.get('id')}")
            memory_id = result.get('id')
        else:
            print(f"❌ Memory storage: FAILED (Status: {response.status_code})")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Memory storage: FAILED (Error: {e})")
        return False
    
    # Test 3: Search memory (simulating Cline)
    try:
        search_data = {
            "query": "Test from Roo",
            "limit": 10
        }
        response = requests.post(f"{base_url}/mcp/memory/search", json=search_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            print("✅ Memory search (Cline simulation): PASSED")
            print(f"   Found {result.get('count')} results")
            if result.get('results'):
                for i, res in enumerate(result['results'][:2]):  # Show first 2 results
                    print(f"   Result {i+1}: {res.get('content', 'N/A')[:50]}...")
        else:
            print(f"❌ Memory search: FAILED (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Memory search: FAILED (Error: {e})")
        return False
    
    # Test 4: Get stats
    try:
        response = requests.get(f"{base_url}/mcp/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Memory stats: PASSED")
            print(f"   Stats: {json.dumps(stats, indent=2)}")
        else:
            print(f"⚠️  Memory stats: WARNING (Status: {response.status_code})")
    except Exception as e:
        print(f"⚠️  Memory stats: WARNING (Error: {e})")
    
    print("=" * 50)
    print("🎉 MCP Server verification completed successfully!")
    return True

if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)
