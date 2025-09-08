#!/usr/bin/env python3
"""
RAG Memory Services Test Script
Tests both Sophia and Artemis memory services
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any, List
import sys
import time

# Service configurations
SERVICES = {
    "sophia": {
        "url": "http://localhost:8767",
        "name": "Sophia BI Memory",
        "test_data": [
            {
                "content": "Q3 revenue exceeded projections by 15%, driven by new enterprise sales.",
                "metadata": {"quarter": "Q3 2024", "metric": "revenue"},
                "source": "salesforce",
                "type": "financial"
            },
            {
                "content": "Customer churn rate decreased to 2.3% following improved onboarding.",
                "metadata": {"metric": "churn_rate", "date": "2024-09"},
                "source": "hubspot",
                "type": "customer"
            },
            {
                "content": "Sales pipeline value reached $4.2M with 87 active opportunities.",
                "metadata": {"pipeline_value": 4200000, "opportunities": 87},
                "source": "salesforce",
                "type": "sales"
            }
        ],
        "test_queries": [
            "revenue projections",
            "customer churn",
            "sales pipeline",
            "Q3 performance"
        ]
    },
    "artemis": {
        "url": "http://localhost:8768",
        "name": "Artemis Code Memory",
        "test_data": [
            {
                "code": "def calculate_revenue(sales: List[float]) -> float:\n    return sum(sales) * 1.15",
                "filepath": "/app/utils/calculations.py",
                "language": "python",
                "description": "Revenue calculation with tax"
            },
            {
                "code": "async function fetchCustomerData(id) {\n    const response = await api.get(`/customers/${id}`);\n    return response.data;\n}",
                "filepath": "/frontend/api/customers.js",
                "language": "javascript",
                "description": "Async customer data fetcher"
            },
            {
                "code": "class UserAuthService:\n    def authenticate(self, username: str, password: str) -> bool:\n        # Implementation here\n        pass",
                "filepath": "/app/auth/service.py",
                "language": "python",
                "description": "User authentication service"
            }
        ],
        "test_queries": [
            "calculate revenue",
            "customer data",
            "authentication",
            "async function"
        ]
    }
}

class RAGServiceTester:
    def __init__(self):
        self.results = {}
        self.passed = 0
        self.failed = 0
        
    async def test_service(self, service_name: str, config: Dict[str, Any]):
        """Test a single RAG service"""
        print(f"\n" + "="*60)
        print(f"🧪 Testing {config['name']} ({config['url']})")
        print("="*60)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Test health endpoint
            health_ok = await self.test_health(client, service_name, config)
            if not health_ok:
                print(f"❌ {config['name']} is not healthy, skipping tests")
                return
            
            # 2. Test indexing
            await self.test_indexing(client, service_name, config)
            
            # 3. Test querying
            await self.test_querying(client, service_name, config)
            
            # 4. Test stats endpoint
            await self.test_stats(client, service_name, config)
    
    async def test_health(self, client: httpx.AsyncClient, service_name: str, config: Dict) -> bool:
        """Test health endpoint"""
        print(f"\n📍 Testing health endpoint...")
        try:
            response = await client.get(f"{config['url']}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data}")
                self.passed += 1
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                self.failed += 1
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            self.failed += 1
            return False
    
    async def test_indexing(self, client: httpx.AsyncClient, service_name: str, config: Dict):
        """Test document indexing"""
        print(f"\n📍 Testing document indexing...")
        
        for i, doc in enumerate(config['test_data'], 1):
            try:
                response = await client.post(
                    f"{config['url']}/index",
                    json=doc
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Document {i} indexed: {result.get('document_id', 'auto-generated')}")
                    self.passed += 1
                else:
                    print(f"❌ Failed to index document {i}: {response.status_code}")
                    self.failed += 1
                    
            except Exception as e:
                print(f"❌ Error indexing document {i}: {e}")
                self.failed += 1
        
        # Wait for indexing to complete
        await asyncio.sleep(1)
    
    async def test_querying(self, client: httpx.AsyncClient, service_name: str, config: Dict):
        """Test document querying"""
        print(f"\n📍 Testing document queries...")
        
        for query in config['test_queries']:
            try:
                response = await client.post(
                    f"{config['url']}/query",
                    json={
                        "query": query,
                        "limit": 5,
                        "include_context": True
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    total = result.get('total_results', 0)
                    print(f"✅ Query '{query}': Found {total} results")
                    
                    # Show first result if available
                    if result.get('results'):
                        first = result['results'][0]
                        content = first.get('content', first.get('code', 'N/A'))[:100]
                        print(f"   First result: {content}...")
                    
                    self.passed += 1
                else:
                    print(f"❌ Query '{query}' failed: {response.status_code}")
                    self.failed += 1
                    
            except Exception as e:
                print(f"❌ Error querying '{query}': {e}")
                self.failed += 1
    
    async def test_stats(self, client: httpx.AsyncClient, service_name: str, config: Dict):
        """Test stats endpoint"""
        print(f"\n📍 Testing stats endpoint...")
        try:
            response = await client.get(f"{config['url']}/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Stats retrieved:")
                print(f"   - Domain: {stats.get('domain', 'N/A')}")
                print(f"   - Documents: {stats.get('total_documents', 0)}")
                print(f"   - Backend: {stats.get('backend', 'N/A')}")
                if 'memory_used_mb' in stats:
                    print(f"   - Memory: {stats['memory_used_mb']} MB")
                self.passed += 1
            else:
                print(f"❌ Stats endpoint failed: {response.status_code}")
                self.failed += 1
        except Exception as e:
            print(f"❌ Stats error: {e}")
            self.failed += 1
    
    async def run_all_tests(self):
        """Run tests for all services"""
        print("\n" + "="*60)
        print("🚀 RAG Memory Services Test Suite")
        print("="*60)
        print(f"Testing {len(SERVICES)} services...")
        
        start_time = time.time()
        
        for service_name, config in SERVICES.items():
            await self.test_service(service_name, config)
        
        duration = time.time() - start_time
        
        # Print summary
        print("\n" + "="*60)
        print("📊 Test Summary")
        print("="*60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        success_rate = (self.passed / (self.passed + self.failed) * 100) if (self.passed + self.failed) > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.failed == 0:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print(f"\n⚠️  {self.failed} tests failed")
            return 1

async def test_integration():
    """Test integration between services"""
    print("\n" + "="*60)
    print("🔗 Testing Service Integration")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Index business data in Sophia
        print("\n📍 Creating cross-domain test...")
        
        # Add business context to Sophia
        business_doc = {
            "content": "The new authentication service reduced login time by 40%.",
            "metadata": {"service": "auth", "improvement": "40%"},
            "source": "performance_report",
            "type": "metric"
        }
        
        try:
            response = await client.post(
                "http://localhost:8767/index",
                json=business_doc
            )
            if response.status_code == 200:
                print("✅ Business context indexed in Sophia")
        except Exception as e:
            print(f"⚠️  Could not index to Sophia: {e}")
        
        # Add code context to Artemis
        code_doc = {
            "code": "class AuthService:\n    def login(self, user, pass):\n        # Optimized login\n        return token",
            "filepath": "/services/auth.py",
            "language": "python",
            "description": "Optimized authentication service"
        }
        
        try:
            response = await client.post(
                "http://localhost:8768/index",
                json=code_doc
            )
            if response.status_code == 200:
                print("✅ Code context indexed in Artemis")
        except Exception as e:
            print(f"⚠️  Could not index to Artemis: {e}")
        
        # Query both services for authentication
        await asyncio.sleep(1)
        
        print("\n📍 Querying both services for 'authentication'...")
        
        for service_name, port in [("Sophia", 8767), ("Artemis", 8768)]:
            try:
                response = await client.post(
                    f"http://localhost:{port}/query",
                    json={"query": "authentication", "limit": 3}
                )
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ {service_name}: Found {result.get('total_results', 0)} results")
            except Exception as e:
                print(f"⚠️  {service_name} query failed: {e}")

async def main():
    """Main test runner"""
    # Check if services are specified
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("Usage: python3 test_rag_services.py [sophia|artemis|integration|all]")
            print("  sophia:      Test only Sophia BI Memory")
            print("  artemis:     Test only Artemis Code Memory")
            print("  integration: Test cross-service integration")
            print("  all:         Run all tests (default)")
            return 0
        
        test_mode = sys.argv[1]
    else:
        test_mode = "all"
    
    tester = RAGServiceTester()
    
    if test_mode == "sophia":
        await tester.test_service("sophia", SERVICES["sophia"])
    elif test_mode == "artemis":
        await tester.test_service("artemis", SERVICES["artemis"])
    elif test_mode == "integration":
        await test_integration()
    else:  # all
        exit_code = await tester.run_all_tests()
        await test_integration()
        return exit_code
    
    # Return based on test results
    return 1 if tester.failed > 0 else 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)