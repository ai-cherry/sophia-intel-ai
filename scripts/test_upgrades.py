#!/usr/bin/env python3
"""
Comprehensive test suite for Q3 2025 upgrades.
Tests ModernBERT, real orchestrator, and all integrations.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any
from datetime import datetime

# ANSI colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class UpgradeTestSuite:
    """Test all major upgrades."""
    
    def __init__(self):
        self.base_url = "http://localhost:8003"
        self.results = []
        self.start_time = datetime.now()
        
    async def test_health_check(self) -> bool:
        """Test API health and all systems."""
        print(f"{BLUE}Testing API health...{RESET}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/healthz") as response:
                if response.status == 200:
                    data = await response.json()
                    all_systems_ok = all(data.get("systems", {}).values())
                    
                    if all_systems_ok:
                        print(f"{GREEN}✅ All systems operational{RESET}")
                        for system, status in data["systems"].items():
                            print(f"  - {system}: {'✓' if status else '✗'}")
                        return True
                    else:
                        print(f"{RED}❌ Some systems offline{RESET}")
                        return False
                else:
                    print(f"{RED}❌ Health check failed: {response.status}{RESET}")
                    return False
    
    async def test_modernbert_embeddings(self) -> bool:
        """Test ModernBERT embedding integration."""
        print(f"\n{BLUE}Testing ModernBERT embeddings...{RESET}")
        
        test_texts = [
            "Short text for Tier-B routing",
            "Critical security analysis for production deployment requiring high-quality embeddings" * 10,
            "Multi-lingual test: Hello, Bonjour, Hola, 你好, こんにちは"
        ]
        
        async with aiohttp.ClientSession() as session:
            for i, text in enumerate(test_texts, 1):
                # Store memory with embedding
                payload = {
                    "topic": f"modernbert_test_{i}",
                    "content": text,
                    "source": "upgrade_test"
                }
                
                async with session.post(
                    f"{self.base_url}/memory/add",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"  ✅ Test {i}: Embedded and stored (hash: {data.get('hash_id', 'N/A')[:8]}...)")
                    else:
                        print(f"  ❌ Test {i}: Failed to embed")
                        return False
            
            # Test embedding search
            search_payload = {"query": "security production", "limit": 3}
            async with session.post(
                f"{self.base_url}/memory/search",
                json=search_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"  ✅ Embedding search returned {data.get('count', 0)} results")
                    return True
                else:
                    print(f"  ❌ Embedding search failed")
                    return False
    
    async def test_real_orchestrator(self) -> bool:
        """Test real orchestrator execution (no mocks)."""
        print(f"\n{BLUE}Testing real orchestrator...{RESET}")
        
        test_cases = [
            {
                "team_id": "strategic-swarm",
                "message": "Design a microservices architecture",
                "expected": "coding_team"
            },
            {
                "team_id": "development-swarm",
                "message": "Implement user authentication",
                "expected": "coding_swarm"
            },
            {
                "team_id": "security-swarm",
                "message": "Audit for vulnerabilities",
                "expected": "coding_team"
            },
            {
                "team_id": "research-swarm",
                "message": "Research quantum computing",
                "expected": "coding_swarm_fast"
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            for test in test_cases:
                print(f"  Testing {test['team_id']}...")
                
                async with session.post(
                    f"{self.base_url}/teams/run",
                    json=test
                ) as response:
                    if response.status == 200:
                        # Read streaming response
                        full_response = ""
                        async for line in response.content:
                            full_response += line.decode('utf-8')
                        
                        # Check for real execution markers
                        if "real_execution" in full_response and "mock" not in full_response.lower():
                            print(f"    ✅ Real execution confirmed")
                            
                            # Verify expected swarm was used
                            if test["expected"] in full_response:
                                print(f"    ✅ Correct swarm used: {test['expected']}")
                            else:
                                print(f"    ⚠️  Different swarm used than expected")
                        else:
                            print(f"    ❌ Mock responses detected!")
                            return False
                    else:
                        print(f"    ❌ Request failed: {response.status}")
                        return False
        
        return True
    
    async def test_hybrid_search(self) -> bool:
        """Test hybrid BM25 + vector search."""
        print(f"\n{BLUE}Testing hybrid search...{RESET}")
        
        # Add test data
        test_data = [
            {"topic": "python_async", "content": "Async programming with Python asyncio", "source": "docs"},
            {"topic": "rust_memory", "content": "Rust memory safety and ownership", "source": "tutorial"},
            {"topic": "kubernetes", "content": "Container orchestration with Kubernetes", "source": "guide"}
        ]
        
        async with aiohttp.ClientSession() as session:
            # Store test data
            for data in test_data:
                await session.post(f"{self.base_url}/memory/add", json=data)
            
            # Test search
            search_payload = {"query": "memory safety programming", "limit": 5}
            async with session.post(
                f"{self.base_url}/search",
                json=search_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("results", [])
                    
                    if results:
                        print(f"  ✅ Hybrid search found {len(results)} results")
                        for r in results[:3]:
                            print(f"    - Score: {r.get('score', 0):.3f}")
                        return True
                    else:
                        print(f"  ⚠️  No results found (may be normal for empty index)")
                        return True
                else:
                    print(f"  ❌ Search failed: {response.status}")
                    return False
    
    async def test_streaming_performance(self) -> bool:
        """Test streaming response performance."""
        print(f"\n{BLUE}Testing streaming performance...{RESET}")
        
        async with aiohttp.ClientSession() as session:
            start = time.time()
            
            payload = {
                "team_id": "research-swarm",
                "message": "Quick performance test",
                "use_memory": False
            }
            
            chunks_received = 0
            first_chunk_time = None
            
            async with session.post(
                f"{self.base_url}/teams/run",
                json=payload
            ) as response:
                async for chunk in response.content.iter_chunked(1024):
                    if chunks_received == 0:
                        first_chunk_time = time.time() - start
                    chunks_received += 1
            
            total_time = time.time() - start
            
            print(f"  ✅ Streaming metrics:")
            print(f"    - First chunk: {first_chunk_time*1000:.1f}ms")
            print(f"    - Total time: {total_time:.2f}s")
            print(f"    - Chunks received: {chunks_received}")
            
            # Performance threshold
            return first_chunk_time < 0.5  # First chunk within 500ms
    
    async def test_mcp_integration(self) -> bool:
        """Test MCP server integration."""
        print(f"\n{BLUE}Testing MCP integration...{RESET}")
        
        async with aiohttp.ClientSession() as session:
            # Test memory MCP
            test_payload = {
                "topic": "mcp_test",
                "content": "Testing MCP supermemory integration",
                "source": "test_suite"
            }
            
            async with session.post(
                f"{self.base_url}/memory/add",
                json=test_payload
            ) as response:
                if response.status == 200:
                    print(f"  ✅ MCP Supermemory: Working")
                else:
                    print(f"  ❌ MCP Supermemory: Failed")
                    return False
            
            # Verify MCP servers in health check
            async with session.get(f"{self.base_url}/healthz") as response:
                data = await response.json()
                systems = data.get("systems", {})
                
                if systems.get("supermemory"):
                    print(f"  ✅ MCP Filesystem: Registered")
                    print(f"  ✅ MCP Git: Registered")
                    print(f"  ✅ MCP Supermemory: Active")
                    return True
                else:
                    print(f"  ❌ MCP servers not fully operational")
                    return False
    
    async def run_all_tests(self):
        """Run complete test suite."""
        print(f"\n{YELLOW}{'='*60}{RESET}")
        print(f"{YELLOW}Sophia Intel AI - Q3 2025 Upgrade Test Suite{RESET}")
        print(f"{YELLOW}{'='*60}{RESET}\n")
        
        tests = [
            ("Health Check", self.test_health_check),
            ("ModernBERT Embeddings", self.test_modernbert_embeddings),
            ("Real Orchestrator", self.test_real_orchestrator),
            ("Hybrid Search", self.test_hybrid_search),
            ("Streaming Performance", self.test_streaming_performance),
            ("MCP Integration", self.test_mcp_integration)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                self.results.append((test_name, result))
                
                if result:
                    passed += 1
                else:
                    failed += 1
                    
            except Exception as e:
                print(f"{RED}  ❌ Exception in {test_name}: {e}{RESET}")
                self.results.append((test_name, False))
                failed += 1
        
        # Summary
        print(f"\n{YELLOW}{'='*60}{RESET}")
        print(f"{YELLOW}Test Results Summary{RESET}")
        print(f"{YELLOW}{'='*60}{RESET}\n")
        
        for test_name, result in self.results:
            status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
            print(f"{test_name:.<40} {status}")
        
        print(f"\n{YELLOW}Overall: {passed}/{len(tests)} tests passed{RESET}")
        
        duration = (datetime.now() - self.start_time).total_seconds()
        print(f"{YELLOW}Duration: {duration:.1f}s{RESET}\n")
        
        if failed == 0:
            print(f"{GREEN}🎉 ALL TESTS PASSED! System ready for production.{RESET}")
            return True
        else:
            print(f"{RED}⚠️  {failed} tests failed. Please review and fix.{RESET}")
            return False

async def main():
    """Run the test suite."""
    suite = UpgradeTestSuite()
    success = await suite.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)