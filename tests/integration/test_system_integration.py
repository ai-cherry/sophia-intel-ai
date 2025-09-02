#!/usr/bin/env python3
"""
Comprehensive System Integration Test Suite
Tests the full 6-way AI coordination system
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any

# Configuration
MCP_SERVER = "http://localhost:8003"
STREAMLIT_UI = "http://localhost:8501"
NEXT_UI = "http://localhost:3000"

# Test results tracker
results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}

def test_endpoint(name: str, url: str, method: str = "GET", 
                  data: Dict = None, expected_status: int = 200) -> bool:
    """Test a single endpoint"""
    print(f"\n🧪 Testing: {name}")
    print(f"   URL: {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            print(f"   ❌ Unsupported method: {method}")
            return False
            
        if response.status_code == expected_status:
            print(f"   ✅ Status: {response.status_code}")
            if response.text:
                try:
                    data = response.json()
                    print(f"   📦 Response: {json.dumps(data)[:100]}...")
                except:
                    print(f"   📦 Response: {response.text[:100]}...")
            results["passed"] += 1
            results["tests"].append({"name": name, "status": "PASSED"})
            return True
        else:
            print(f"   ❌ Status: {response.status_code} (expected {expected_status})")
            results["failed"] += 1
            results["tests"].append({"name": name, "status": "FAILED"})
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection failed - service not running?")
        results["failed"] += 1
        results["tests"].append({"name": name, "status": "CONNECTION_FAILED"})
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        results["failed"] += 1
        results["tests"].append({"name": name, "status": "ERROR"})
        return False

def run_tests():
    """Run all system integration tests"""
    print("=" * 60)
    print("🚀 SYSTEM INTEGRATION TEST SUITE")
    print("=" * 60)
    
    # Test MCP Server endpoints
    print("\n📡 MCP SERVER TESTS")
    print("-" * 40)
    
    test_endpoint(
        "MCP Health Check",
        f"{MCP_SERVER}/health"
    )
    
    test_endpoint(
        "Swarm Status",
        f"{MCP_SERVER}/mcp/swarm-status"
    )
    
    test_endpoint(
        "Code Review",
        f"{MCP_SERVER}/mcp/code-review",
        method="POST",
        data={"code": "def hello():\n    print('world')"}
    )
    
    # Security tests
    print("\n🔒 SECURITY TESTS")
    print("-" * 40)
    
    test_endpoint(
        "Command Injection Protection",
        f"{MCP_SERVER}/mcp/quality-check",
        method="POST",
        data={"url": "http://localhost:8501; rm -rf /"},
        expected_status=500  # Should reject malicious input
    )
    
    test_endpoint(
        "External URL Blocking",
        f"{MCP_SERVER}/mcp/quality-check",
        method="POST",
        data={"url": "http://evil.com:8501"},
        expected_status=403  # Should block external URLs
    )
    
    # Input validation tests
    print("\n✅ INPUT VALIDATION TESTS")
    print("-" * 40)
    
    test_endpoint(
        "Invalid Agent Count",
        f"{MCP_SERVER}/mcp/swarm-config",
        method="POST",
        data={"num_agents": 999, "agent_type": "GPU", "max_concurrency": 10},
        expected_status=400  # Should reject invalid count
    )
    
    test_endpoint(
        "Invalid Agent Type",
        f"{MCP_SERVER}/mcp/swarm-config",
        method="POST",
        data={"num_agents": 5, "agent_type": "INVALID", "max_concurrency": 10},
        expected_status=400  # Should reject invalid type
    )
    
    test_endpoint(
        "Valid Configuration",
        f"{MCP_SERVER}/mcp/swarm-config",
        method="POST",
        data={"num_agents": 5, "agent_type": "GPU", "max_concurrency": 10}
    )
    
    # UI Tests
    print("\n🎨 UI AVAILABILITY TESTS")
    print("-" * 40)
    
    test_endpoint(
        "Streamlit UI",
        STREAMLIT_UI
    )
    
    test_endpoint(
        "Next.js UI",
        NEXT_UI
    )
    
    # Performance test
    print("\n⚡ PERFORMANCE TESTS")
    print("-" * 40)
    
    start_time = time.time()
    success = test_endpoint(
        "Response Time Test",
        f"{MCP_SERVER}/mcp/swarm-status"
    )
    elapsed = time.time() - start_time
    
    if success:
        if elapsed < 0.05:  # 50ms target
            print(f"   ⚡ Response time: {elapsed*1000:.2f}ms - EXCELLENT")
        elif elapsed < 0.1:
            print(f"   ⚡ Response time: {elapsed*1000:.2f}ms - GOOD")
        else:
            print(f"   ⚠️  Response time: {elapsed*1000:.2f}ms - SLOW")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📈 Total:  {results['passed'] + results['failed']}")
    print(f"🎯 Success Rate: {(results['passed']/(results['passed']+results['failed'])*100):.1f}%")
    
    if results['failed'] == 0:
        print("\n🎉 ALL TESTS PASSED! System is ready for production!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review and fix issues.")
        print("\nFailed tests:")
        for test in results['tests']:
            if test['status'] != 'PASSED':
                print(f"  - {test['name']}: {test['status']}")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())