#!/usr/bin/env python3
"""
Test script for Enhanced Unified MCP Server
Validates core functionality and API endpoints
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

class EnhancedMCPServerTester:
    """Test suite for Enhanced MCP Server"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
    
    async def setup(self):
        """Setup test environment"""
        self.session = aiohttp.ClientSession()
        print("🚀 Starting Enhanced MCP Server Test Suite")
        print(f"📍 Testing server at: {self.base_url}")
        print("-" * 50)
    
    async def teardown(self):
        """Cleanup test environment"""
        if self.session:
            await self.session.close()
        
        # Print test summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result["passed"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"{status} {result['test_name']}")
            if not result["passed"]:
                print(f"   Error: {result.get('error', 'Unknown error')}")
        
        print(f"\n📈 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Enhanced MCP Server is ready for deployment.")
        else:
            print("⚠️  Some tests failed. Please review and fix issues before deployment.")
    
    async def test_health_endpoint(self):
        """Test health check endpoint"""
        test_name = "Health Check Endpoint"
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    assert "status" in data
                    assert data["status"] == "healthy"
                    assert "service" in data
                    assert "components" in data
                    
                    self.test_results.append({
                        "test_name": test_name,
                        "passed": True,
                        "response": data
                    })
                    print(f"✅ {test_name}: Server is healthy")
                else:
                    raise Exception(f"Health check failed with status {response.status}")
                    
        except Exception as e:
            self.test_results.append({
                "test_name": test_name,
                "passed": False,
                "error": str(e)
            })
            print(f"❌ {test_name}: {e}")
    
    async def test_ai_router_functionality(self):
        """Test AI Router functionality"""
        test_name = "AI Router Functionality"
        try:
            # Test model stats endpoint
            async with self.session.get(f"{self.base_url}/models") as response:
                if response.status == 200:
                    models = await response.json()
                    assert isinstance(models, dict)
                    assert len(models) > 0
                    
                    # Check if models have required fields
                    for model_id, model_info in models.items():
                        assert "provider" in model_info
                        assert "model_name" in model_info
                        assert "specialties" in model_info
                    
                    self.test_results.append({
                        "test_name": test_name,
                        "passed": True,
                        "models_count": len(models)
                    })
                    print(f"✅ {test_name}: {len(models)} models available")
                else:
                    raise Exception(f"Models endpoint failed with status {response.status}")
                    
        except Exception as e:
            self.test_results.append({
                "test_name": test_name,
                "passed": False,
                "error": str(e)
            })
            print(f"❌ {test_name}: {e}")
    
    async def test_context_management(self):
        """Test context storage and retrieval"""
        test_name = "Context Management"
        try:
            session_id = f"test_session_{int(time.time())}"
            
            # Store context
            store_payload = {
                "session_id": session_id,
                "content": "This is a test context for the enhanced MCP server",
                "metadata": {"test": True, "timestamp": time.time()},
                "context_type": "test"
            }
            
            async with self.session.post(
                f"{self.base_url}/context/store",
                json=store_payload
            ) as response:
                if response.status == 200:
                    store_result = await response.json()
                    assert store_result["success"] is True
                    assert "id" in store_result
                else:
                    raise Exception(f"Context store failed with status {response.status}")
            
            # Query context
            query_payload = {
                "session_id": session_id,
                "query": "test context",
                "top_k": 5,
                "threshold": 0.5
            }
            
            async with self.session.post(
                f"{self.base_url}/context/query",
                json=query_payload
            ) as response:
                if response.status == 200:
                    query_result = await response.json()
                    assert query_result["success"] is True
                    assert "results" in query_result
                    
                    self.test_results.append({
                        "test_name": test_name,
                        "passed": True,
                        "stored_id": store_result["id"],
                        "query_results": len(query_result["results"])
                    })
                    print(f"✅ {test_name}: Context stored and retrieved successfully")
                else:
                    raise Exception(f"Context query failed with status {response.status}")
                    
        except Exception as e:
            self.test_results.append({
                "test_name": test_name,
                "passed": False,
                "error": str(e)
            })
            print(f"❌ {test_name}: {e}")
    
    async def test_stats_endpoint(self):
        """Test statistics endpoint"""
        test_name = "Statistics Endpoint"
        try:
            async with self.session.get(f"{self.base_url}/stats") as response:
                if response.status == 200:
                    stats = await response.json()
                    assert "system" in stats
                    assert "ai_router" in stats
                    assert "memory_service" in stats
                    
                    self.test_results.append({
                        "test_name": test_name,
                        "passed": True,
                        "stats": stats
                    })
                    print(f"✅ {test_name}: Statistics retrieved successfully")
                else:
                    raise Exception(f"Stats endpoint failed with status {response.status}")
                    
        except Exception as e:
            self.test_results.append({
                "test_name": test_name,
                "passed": False,
                "error": str(e)
            })
            print(f"❌ {test_name}: {e}")
    
    async def run_all_tests(self):
        """Run all test cases"""
        await self.setup()
        
        # Wait a moment for server to be ready
        await asyncio.sleep(1)
        
        # Run tests
        await self.test_health_endpoint()
        await self.test_ai_router_functionality()
        await self.test_context_management()
        await self.test_stats_endpoint()
        
        await self.teardown()


async def main():
    """Main test runner"""
    tester = EnhancedMCPServerTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

