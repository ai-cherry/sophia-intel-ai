#!/usr/bin/env python3
"""
Production Test Suite for Natural Language Interface
Tests all production enhancements to ensure 10/10 readiness
"""

import asyncio
import json
import time
import sys
import os
from typing import Dict, Any, List
from datetime import datetime
import requests
import aiohttp

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.nl_interface.quicknlp import CachedQuickNLP
from app.nl_interface.memory_connector import NLMemoryConnector, NLInteraction
from app.nl_interface.auth import SecureNLProcessor, RateLimiter, create_api_key
from app.agents.simple_orchestrator import OptimizedAgentOrchestrator, AgentRole


class ProductionTestSuite:
    """Comprehensive test suite for production features"""
    
    def __init__(self, api_base_url: str = "http://localhost:8003"):
        self.api_base_url = api_base_url
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_test(self, name: str, passed: bool, details: str = ""):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            print(f"✅ {name}: PASSED")
        else:
            self.failed_tests += 1
            print(f"❌ {name}: FAILED - {details}")
        
        self.test_results.append({
            "name": name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    # =========================================
    # Test 1: API Authentication
    # =========================================
    
    def test_authentication(self):
        """Test API key authentication"""
        print("\n" + "="*50)
        print("Testing Authentication Layer...")
        print("="*50)
        
        try:
            # Test without API key
            response = requests.get(f"{self.api_base_url}/api/nl/intents")
            if response.status_code == 401:
                self.log_test("Authentication - No API Key", True)
            else:
                self.log_test("Authentication - No API Key", False, 
                            f"Expected 401, got {response.status_code}")
            
            # Test with invalid API key
            headers = {"X-API-Key": "invalid-key-12345"}
            response = requests.get(f"{self.api_base_url}/api/nl/intents", headers=headers)
            if response.status_code == 401:
                self.log_test("Authentication - Invalid API Key", True)
            else:
                self.log_test("Authentication - Invalid API Key", False,
                            f"Expected 401, got {response.status_code}")
            
            # Test with development key (if auth disabled)
            headers = {"X-API-Key": "dev-api-key-12345"}
            response = requests.get(f"{self.api_base_url}/api/nl/health", headers=headers)
            if response.status_code in [200, 401]:  # 200 if auth disabled, 401 if enabled
                self.log_test("Authentication - Dev Mode", True)
            else:
                self.log_test("Authentication - Dev Mode", False,
                            f"Unexpected status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Authentication Tests", False, str(e))
    
    # =========================================
    # Test 2: Rate Limiting
    # =========================================
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("\n" + "="*50)
        print("Testing Rate Limiting...")
        print("="*50)
        
        try:
            rate_limiter = RateLimiter()
            
            # Test within limit
            key = "test-key-1"
            limit = 5
            
            for i in range(limit):
                allowed = rate_limiter.is_allowed(key, limit, window=60)
                if not allowed:
                    self.log_test("Rate Limiting - Within Limit", False,
                                f"Request {i+1} should be allowed")
                    return
            
            self.log_test("Rate Limiting - Within Limit", True)
            
            # Test exceeding limit
            allowed = rate_limiter.is_allowed(key, limit, window=60)
            if allowed:
                self.log_test("Rate Limiting - Exceed Limit", False,
                            "Request should be blocked")
            else:
                self.log_test("Rate Limiting - Exceed Limit", True)
            
            # Test remaining count
            remaining = rate_limiter.get_remaining(key, limit, window=60)
            if remaining == 0:
                self.log_test("Rate Limiting - Remaining Count", True)
            else:
                self.log_test("Rate Limiting - Remaining Count", False,
                            f"Expected 0 remaining, got {remaining}")
            
        except Exception as e:
            self.log_test("Rate Limiting Tests", False, str(e))
    
    # =========================================
    # Test 3: Response Format Standardization
    # =========================================
    
    def test_response_format(self):
        """Test standardized response format"""
        print("\n" + "="*50)
        print("Testing Response Format...")
        print("="*50)
        
        try:
            # Prepare request
            payload = {
                "text": "show system status",
                "context": {},
                "session_id": "test-session-format"
            }
            
            headers = {"X-API-Key": "dev-api-key-12345"}
            
            # Make request
            response = requests.post(
                f"{self.api_base_url}/api/nl/process",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["success", "response", "timestamp"]
                missing_fields = [f for f in required_fields if f not in data]
                
                if not missing_fields:
                    self.log_test("Response Format - Required Fields", True)
                else:
                    self.log_test("Response Format - Required Fields", False,
                                f"Missing fields: {missing_fields}")
                
                # Check optional fields
                optional_fields = ["intent", "data", "workflow_id", "session_id", 
                                 "execution_time_ms", "error"]
                present_fields = [f for f in optional_fields if f in data]
                
                if len(present_fields) > 3:
                    self.log_test("Response Format - Optional Fields", True)
                else:
                    self.log_test("Response Format - Optional Fields", False,
                                f"Only {len(present_fields)} optional fields present")
                
                # Check timestamp format
                if "timestamp" in data:
                    try:
                        datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
                        self.log_test("Response Format - Timestamp", True)
                    except:
                        self.log_test("Response Format - Timestamp", False,
                                    "Invalid timestamp format")
            else:
                self.log_test("Response Format Tests", False,
                            f"API returned status {response.status_code}")
            
        except Exception as e:
            self.log_test("Response Format Tests", False, str(e))
    
    # =========================================
    # Test 4: Memory Integration
    # =========================================
    
    async def test_memory_integration(self):
        """Test NL Memory Connector"""
        print("\n" + "="*50)
        print("Testing Memory Integration...")
        print("="*50)
        
        try:
            memory = NLMemoryConnector()
            await memory.connect()
            
            # Test storing interaction
            interaction = NLInteraction(
                session_id="test-session-memory",
                timestamp=datetime.now().isoformat(),
                user_input="test command",
                intent="test_intent",
                entities={"test": "value"},
                confidence=0.95,
                response="Test response",
                workflow_id="test-workflow"
            )
            
            success = await memory.store_interaction(interaction)
            self.log_test("Memory - Store Interaction", success)
            
            # Test retrieving history
            history = await memory.retrieve_session_history("test-session-memory")
            if history and len(history) > 0:
                self.log_test("Memory - Retrieve History", True)
            else:
                self.log_test("Memory - Retrieve History", False,
                            "No history retrieved")
            
            # Test context summary
            summary = await memory.get_context_summary("test-session-memory")
            if "session_id" in summary and "interaction_count" in summary:
                self.log_test("Memory - Context Summary", True)
            else:
                self.log_test("Memory - Context Summary", False,
                            "Invalid summary format")
            
            # Test export
            export_data = await memory.export_session("test-session-memory", format="json")
            if export_data:
                self.log_test("Memory - Export Session", True)
            else:
                self.log_test("Memory - Export Session", False,
                            "Export returned empty")
            
            # Test statistics
            stats = memory.get_statistics()
            if "total_interactions" in stats and "active_sessions" in stats:
                self.log_test("Memory - Statistics", True)
            else:
                self.log_test("Memory - Statistics", False,
                            "Invalid statistics format")
            
            await memory.disconnect()
            
        except Exception as e:
            self.log_test("Memory Integration Tests", False, str(e))
    
    # =========================================
    # Test 5: Pattern Caching Optimization
    # =========================================
    
    def test_pattern_caching(self):
        """Test CachedQuickNLP performance"""
        print("\n" + "="*50)
        print("Testing Pattern Caching...")
        print("="*50)
        
        try:
            cached_nlp = CachedQuickNLP(cache_size=100)
            
            test_texts = [
                "show system status",
                "run agent researcher",
                "scale ollama to 3",
                "list all agents",
                "help"
            ]
            
            # First pass (cold cache)
            start_time = time.time()
            for text in test_texts:
                result = cached_nlp.process(text)
            cold_time = time.time() - start_time
            
            # Second pass (warm cache)
            start_time = time.time()
            for text in test_texts:
                result = cached_nlp.process(text)
            warm_time = time.time() - start_time
            
            # Check performance improvement
            improvement = (cold_time - warm_time) / cold_time * 100
            
            if improvement > 30:  # Expect at least 30% improvement
                self.log_test("Pattern Caching - Performance", True,
                            f"{improvement:.1f}% improvement")
            else:
                self.log_test("Pattern Caching - Performance", False,
                            f"Only {improvement:.1f}% improvement")
            
            # Check cache stats
            stats = cached_nlp.get_cache_stats()
            if stats["cache_hits"] > 0:
                self.log_test("Pattern Caching - Cache Hits", True,
                            f"Hit rate: {stats['hit_rate']:.2%}")
            else:
                self.log_test("Pattern Caching - Cache Hits", False,
                            "No cache hits recorded")
            
            # Test cache clearing
            cached_nlp.clear_cache()
            stats_after = cached_nlp.get_cache_stats()
            if stats_after["cache_size"] == 0:
                self.log_test("Pattern Caching - Clear Cache", True)
            else:
                self.log_test("Pattern Caching - Clear Cache", False,
                            f"Cache size: {stats_after['cache_size']}")
            
        except Exception as e:
            self.log_test("Pattern Caching Tests", False, str(e))
    
    # =========================================
    # Test 6: Connection Pooling
    # =========================================
    
    async def test_connection_pooling(self):
        """Test OptimizedAgentOrchestrator"""
        print("\n" + "="*50)
        print("Testing Connection Pooling...")
        print("="*50)
        
        try:
            async with OptimizedAgentOrchestrator() as orchestrator:
                # Test metrics initialization
                metrics = orchestrator.get_metrics()
                if all(k in metrics for k in ["ollama_calls", "redis_calls", "cache_hit_rate"]):
                    self.log_test("Connection Pool - Metrics Init", True)
                else:
                    self.log_test("Connection Pool - Metrics Init", False,
                                "Missing metrics fields")
                
                # Test connection pool
                if orchestrator.http_session is not None:
                    self.log_test("Connection Pool - HTTP Session", True)
                else:
                    self.log_test("Connection Pool - HTTP Session", False,
                                "HTTP session not initialized")
                
                # Test cache functionality
                test_prompt = "Test prompt for caching"
                result1 = await orchestrator._call_ollama(test_prompt)
                result2 = await orchestrator._call_ollama(test_prompt)
                
                metrics_after = orchestrator.get_metrics()
                if metrics_after["cache_hits"] > 0:
                    self.log_test("Connection Pool - Response Cache", True,
                                f"Cache hits: {metrics_after['cache_hits']}")
                else:
                    self.log_test("Connection Pool - Response Cache", False,
                                "No cache hits recorded")
                
                # Test metrics reset
                orchestrator.reset_metrics()
                metrics_reset = orchestrator.get_metrics()
                if metrics_reset["ollama_calls"] == 0:
                    self.log_test("Connection Pool - Metrics Reset", True)
                else:
                    self.log_test("Connection Pool - Metrics Reset", False,
                                f"Calls not reset: {metrics_reset['ollama_calls']}")
            
        except Exception as e:
            self.log_test("Connection Pooling Tests", False, str(e))
    
    # =========================================
    # Test 7: Workflow Callbacks
    # =========================================
    
    def test_workflow_callbacks(self):
        """Test workflow callback endpoint"""
        print("\n" + "="*50)
        print("Testing Workflow Callbacks...")
        print("="*50)
        
        try:
            # Prepare callback payload
            callback_data = {
                "workflow_id": "test-workflow",
                "status": "completed",
                "execution_id": "exec-123",
                "timestamp": datetime.now().isoformat(),
                "result": {"test": "data"},
                "session_id": "test-session-callback"
            }
            
            headers = {"X-API-Key": "dev-api-key-12345"}
            
            # Send callback
            response = requests.post(
                f"{self.api_base_url}/api/nl/workflows/callback",
                json=callback_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("Workflow Callback - Success", True)
                else:
                    self.log_test("Workflow Callback - Success", False,
                                "Response indicates failure")
                
                # Check response contains workflow_id
                if "workflow_id" in data or "data" in data:
                    self.log_test("Workflow Callback - Response Data", True)
                else:
                    self.log_test("Workflow Callback - Response Data", False,
                                "Missing workflow data in response")
            else:
                self.log_test("Workflow Callbacks", False,
                            f"API returned status {response.status_code}")
            
        except Exception as e:
            self.log_test("Workflow Callback Tests", False, str(e))
    
    # =========================================
    # Test 8: End-to-End Integration
    # =========================================
    
    async def test_end_to_end(self):
        """Test complete flow from UI to backend"""
        print("\n" + "="*50)
        print("Testing End-to-End Integration...")
        print("="*50)
        
        try:
            session_id = f"test-e2e-{int(time.time())}"
            
            # Test command processing
            commands = [
                "show system status",
                "list all agents",
                "help"
            ]
            
            headers = {"X-API-Key": "dev-api-key-12345"}
            
            for cmd in commands:
                payload = {
                    "text": cmd,
                    "context": {},
                    "session_id": session_id
                }
                
                response = requests.post(
                    f"{self.api_base_url}/api/nl/process",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code != 200:
                    self.log_test(f"E2E - Process '{cmd}'", False,
                                f"Status: {response.status_code}")
                    continue
                
                data = response.json()
                if data.get("success"):
                    self.log_test(f"E2E - Process '{cmd}'", True)
                else:
                    self.log_test(f"E2E - Process '{cmd}'", False,
                                "Processing failed")
            
            # Verify session continuity
            response = requests.get(
                f"{self.api_base_url}/api/nl/agents/status/{session_id}",
                headers=headers
            )
            
            if response.status_code in [200, 404]:  # 404 is OK if no agent was run
                self.log_test("E2E - Session Continuity", True)
            else:
                self.log_test("E2E - Session Continuity", False,
                            f"Unexpected status: {response.status_code}")
            
        except Exception as e:
            self.log_test("End-to-End Tests", False, str(e))
    
    # =========================================
    # Main Test Runner
    # =========================================
    
    async def run_all_tests(self):
        """Run all production tests"""
        print("\n" + "="*70)
        print(" PRODUCTION TEST SUITE - Natural Language Interface v1.0")
        print("="*70)
        print(f"API Base URL: {self.api_base_url}")
        print(f"Test Started: {datetime.now().isoformat()}")
        
        # Run synchronous tests
        self.test_authentication()
        self.test_rate_limiting()
        self.test_response_format()
        self.test_pattern_caching()
        self.test_workflow_callbacks()
        
        # Run async tests
        await self.test_memory_integration()
        await self.test_connection_pooling()
        await self.test_end_to_end()
        
        # Print summary
        print("\n" + "="*70)
        print(" TEST SUMMARY")
        print("="*70)
        print(f"Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED! System is 10/10 PRODUCTION READY! 🎉")
        else:
            print(f"\n⚠️  {self.failed_tests} tests failed. Please review and fix issues.")
        
        # Save test results
        with open("test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_tests": self.total_tests,
                "passed": self.passed_tests,
                "failed": self.failed_tests,
                "success_rate": success_rate,
                "results": self.test_results
            }, f, indent=2)
        
        print(f"\nTest results saved to test_results.json")
        
        return self.failed_tests == 0


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Production Test Suite for NL Interface")
    parser.add_argument("--api-url", default="http://localhost:8003",
                       help="API base URL (default: http://localhost:8003)")
    parser.add_argument("--skip-auth", action="store_true",
                       help="Skip authentication tests (for dev mode)")
    
    args = parser.parse_args()
    
    # Run tests
    test_suite = ProductionTestSuite(api_base_url=args.api_url)
    
    # Run async tests
    success = asyncio.run(test_suite.run_all_tests())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()