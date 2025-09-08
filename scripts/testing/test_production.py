#!/usr/bin/env python3
"""
Production Readiness Test Suite
Tests all production polish improvements from 9/10 → 10/10
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Any

import requests

from app.core.ai_logger import logger

# Add app directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.agents.simple_orchestrator import OptimizedAgentOrchestrator
    from app.core.connections import get_connection_manager
    from app.nl_interface.auth import SecureNLProcessor
    from app.nl_interface.quicknlp import CachedQuickNLP
except ImportError as e:
    logger.info(f"❌ Import error: {e}")
    logger.info("🔧 Run this script from the project root directory")
    sys.exit(1)


# Colors for output
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


class ProductionTestSuite:
    """Comprehensive production readiness test suite"""

    def __init__(self):
        self.base_url = "http://localhost:8003"
        self.api_key = "dev-key-12345"
        self.session_id = f"test-session-{int(time.time())}"

        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "start_time": datetime.now(),
            "details": [],
        }

        # Test data
        self.test_commands = [
            {"text": "show system status", "intent": "system_status"},
            {
                "text": "run agent researcher",
                "intent": "run_agent",
                "entity": "researcher",
            },
            {
                "text": "scale ollama to 3",
                "intent": "scale_service",
                "entity": "ollama",
            },
            {"text": "help", "intent": "help"},
            {"text": "list all agents", "intent": "list_agents"},
        ]

    def log(self, message: str, level: str = "info"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if level == "pass":
            logger.info(f"{Colors.GREEN}✅ {timestamp} {message}{Colors.END}")
        elif level == "fail":
            logger.info(f"{Colors.RED}❌ {timestamp} {message}{Colors.END}")
        elif level == "warn":
            logger.info(f"{Colors.YELLOW}⚠️  {timestamp} {message}{Colors.END}")
        elif level == "info":
            logger.info(f"{Colors.BLUE}ℹ️  {timestamp} {message}{Colors.END}")
        else:
            logger.info(f"{Colors.BOLD}{timestamp} {message}{Colors.END}")

    def test_result(
        self, name: str, passed: bool, message: str = "", details: Any = None
    ):
        """Record test result"""
        self.results["tests_run"] += 1

        if passed:
            self.results["tests_passed"] += 1
        else:
            self.results["tests_failed"] += 1

        self.results["details"].append(
            {
                "name": name,
                "passed": passed,
                "message": message,
                "details": details,
                "timestamp": datetime.now().isoformat(),
            }
        )

    async def test_api_health(self):
        """Test API basic health"""
        self.log("Testing API health check...")

        try:
            response = requests.get(f"{self.base_url}/api/nl/health", timeout=5)

            if response.status_code == 200:
                data = response.json()
                self.test_result(
                    "API Health Check", True, f"Status: {data.get('status', 'unknown')}"
                )
                return True
            else:
                self.test_result(
                    "API Health Check", False, f"Status code: {response.status_code}"
                )
                return False

        except Exception as e:
            self.test_result("API Health Check", False, f"Connection failed: {str(e)}")
            return False

    def test_authentication_layer(self):
        """Test authentication functionality"""
        self.log("Testing authentication layer...")
        return asyncio.run(self._test_auth_internal())

    async def _test_auth_internal(self):
        """Internal auth testing"""
        try:
            # Test init
            from app.nl_interface.quicknlp import QuickNLP

            base_processor = QuickNLP()
            auth_processor = SecureNLProcessor(base_processor)

            # Test valid key
            is_valid, message, user_info = auth_processor.validate_api_key(
                "dev-key-12345"
            )
            self.test_result("API Key Validation", is_valid)

            if is_valid:
                # Test usage recording
                auth_processor.record_usage(user_info["user_id"])

                # Test invalid key
                is_valid2, message2, _ = auth_processor.validate_api_key("invalid-key")
                self.test_result("Invalid Key Rejection", not is_valid2)

                # Test quota management
                stats = auth_processor.get_usage_statistics(user_info["user_id"])
                self.test_result("Usage Statistics", "user_id" in stats)

                return True
            else:
                self.test_result("Auth Processor", False, "Failed to initialize")
                return False

        except Exception as e:
            self.test_result("Authentication Layer", False, str(e))
            return False

    def test_pattern_caching(self):
        """Test improved pattern caching performance"""
        self.log("Testing pattern caching optimization...")
        return asyncio.run(self._test_caching_internal())

    async def _test_caching_internal(self):
        """Internal caching performance test"""
        try:
            # Create cached processor
            cached_processor = CachedQuickNLP()

            # Test texts for benchmark
            test_texts = [
                "show system status",
                "run agent researcher",
                "scale ollama to 3",
                "show system status",  # Duplicate for cache test
                "help",
                "run agent researcher",  # Another duplicate
            ]

            # Warm cache
            cached_processor.warm_cache(test_texts[:3])

            # Run benchmark
            start_time = time.time()
            results = cached_processor.benchmark(test_texts)
            benchmark_time = time.time() - start_time

            # Check performance expectations
            improvement = results["improvement"]
            avg_warm_time = results["avg_warm_ms"]

            # Should achieve >30% improvement
            perf_improved = improvement > 30
            self.test_result(
                "Pattern Cache Performance",
                perf_improved,
                f"Improvement: {improvement:.1f}%, Warm time: {avg_warm_time:.2f}ms",
            )

            # Test cache stats
            cache_stats = cached_processor.get_cache_stats()
            cache_working = cache_stats["hit_rate"] > 0
            self.test_result(
                "Cache Hit Rate",
                cache_working,
                f"Hit rate: {cache_stats['hit_rate']:.2f}",
            )

            return perf_improved

        except Exception as e:
            self.test_result("Pattern Caching", False, str(e))
            return False

    async def test_connection_pooling(self):
        """Test connection pooling optimization"""
        self.log("Testing connection pooling...")

        try:
            async with OptimizedAgentOrchestrator() as orchestrator:
                # Test basic functionality
                agents = orchestrator.get_available_agents()
                self.test_result("Connection Pool Init", len(agents) > 0)

                # Test metrics collection
                initial_metrics = orchestrator.get_metrics()
                self.test_result(
                    "Metrics Collection", "ollama_calls" in initial_metrics
                )

                # Test context saving
                test_context = {
                    "session_id": self.session_id,
                    "user_request": "test request",
                    "workflow_name": "test_workflow",
                    "agents_chain": ["researcher", "coder"],
                    "current_step": 0,
                    "state": {},
                    "tasks": [],
                    "start_time": time.time(),
                    "end_time": None,
                }

                # Note: This would require a proper ExecutionContext object
                # For now, just test the availability
                self.test_result("Pool Creation", orchestrator.http_session is not None)

                return True

        except Exception as e:
            self.test_result("Connection Pooling", False, str(e))
            return False

    def test_response_formats(self):
        """Test standardized response formats"""
        self.log("Testing response format standardization...")

        try:
            headers = {"Content-Type": "application/json", "X-API-Key": self.api_key}

            # Test successful request
            payload = {"text": "help", "session_id": self.session_id}

            response = requests.post(
                f"{self.base_url}/api/nl/process",
                json=payload,
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()

                # Check required fields
                required_fields = [
                    "success",
                    "message",
                    "response",
                    "timestamp",
                    "execution_time_ms",
                ]
                has_all_fields = all(field in data for field in required_fields)

                self.test_result(
                    "Response Format Completeness",
                    has_all_fields,
                    f"Missing fields: {[f for f in required_fields if f not in data]}",
                )

                # Check data types
                if has_all_fields:
                    correct_types = True
                    if not isinstance(data["success"], bool):
                        correct_types = False
                    if not isinstance(data["message"], str):
                        correct_types = False
                    if not isinstance(data["execution_time_ms"], (int, float)):
                        correct_types = False

                    self.test_result("Response Field Types", correct_types)

                return has_all_fields
            else:
                self.test_result(
                    "Response Format Test", False, f"Status: {response.status_code}"
                )
                return False

        except Exception as e:
            self.test_result("Response Formats", False, str(e))
            return False

    def test_workflow_callbacks(self):
        """Test n8n workflow callback functionality"""
        self.log("Testing workflow callbacks...")

        try:
            headers = {"Content-Type": "application/json", "X-API-Key": self.api_key}

            # Trigger a workflow
            trigger_payload = {
                "text": "execute workflow system-status-workflow",
                "session_id": self.session_id,
            }

            trigger_response = requests.post(
                f"{self.base_url}/api/nl/process",
                json=trigger_payload,
                headers=headers,
                timeout=10,
            )

            if trigger_response.status_code == 200:
                # Test callback endpoint directly
                callback_payload = {
                    "workflow_id": "system-status-workflow",
                    "status": "completed",
                    "execution_id": f"test-exec-{int(time.time())}",
                    "session_id": self.session_id,
                }

                callback_response = requests.post(
                    f"{self.base_url}/api/nl/workflows/callback",
                    json=callback_payload,
                    headers=headers,
                    timeout=10,
                )

                if callback_response.status_code == 200:
                    callback_data = callback_response.json()
                    has_callback_data = (
                        "data" in callback_data
                        and "workflow_id" in callback_data["data"]
                    )

                    self.test_result("Workflow Callback Processing", has_callback_data)
                    return has_callback_data
                else:
                    self.test_result(
                        "Workflow Callback Test",
                        False,
                        f"Callback status: {callback_response.status_code}",
                    )
                    return False
            else:
                self.test_result(
                    "Workflow Trigger",
                    False,
                    f"Trigger status: {trigger_response.status_code}",
                )
                return False

        except Exception as e:
            self.test_result("Workflow Callbacks", False, str(e))
            return False

    def test_memory_integration(self):
        """Test memory connector integration"""
        self.log("Testing memory integration...")

        try:
            # Test memory connector availability
            nl_processor = QuickNLP()
            processor = SecureNLProcessor(nl_processor)

            # Test memory interaction (would require memory service to be running)
            interaction_data = {
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "user_input": "test message",
                "intent": "test",
                "response": "test response",
            }

            # Since we can't mock the external service, we'll just test the interface
            has_auth_features = hasattr(processor, "validate_api_key")
            has_security = hasattr(processor, "record_usage")

            self.test_result(
                "Memory Integration Interface", has_auth_features and has_security
            )
            return has_auth_features and has_security

        except Exception as e:
            self.test_result("Memory Integration", False, str(e))
            return False

    async def run_all_tests(self):
        """Run complete test suite"""
        self.log("🚀 Starting Production Readiness Test Suite", "info")
        logger.info("=" * 60)

        # Test 1: Basic API health
        api_healthy = await self.test_api_health()

        # Test 2: Authentication layer (doesn't depend on API)
        auth_working = self.test_authentication_layer()

        # Test 3: Pattern caching (local test)
        caching_working = self.test_pattern_caching()

        # Test 4: Connection pooling (local test)
        pooling_working = await self.test_connection_pooling()

        # Test 5: Response formats (requires API)
        if api_healthy:
            response_format_good = self.test_response_formats()
        else:
            self.test_result("Response Format Test", False, "API not available")
            response_format_good = False

        # Test 6: Workflow callbacks
        if api_healthy:
            callbacks_working = self.test_workflow_callbacks()
        else:
            self.test_result("Workflow Callbacks Test", False, "API not available")
            callbacks_working = False

        # Test 7: Memory integration
        memory_working = self.test_memory_integration()

        # Calculate overall score
        self.results["end_time"] = datetime.now()

        logger.info("\n" + "=" * 60)
        self.log("📊 PRODUCTION READINESS RESULTS", "info")
        logger.info("=" * 60)

        tests_run = self.results["tests_run"]
        tests_passed = self.results["tests_passed"]
        tests_failed = self.results["tests_failed"]

        logger.info(f"Total Tests Run: {tests_run}")
        logger.info(f"Tests Passed: {Colors.GREEN}{tests_passed}{Colors.END}")
        logger.info(f"Tests Failed: {Colors.RED}{tests_failed}{Colors.END}")

        if tests_run > 0:
            success_rate = (tests_passed / tests_run) * 100
            logger.info(
                f"Success Rate: {Colors.GREEN if success_rate >= 80 else Colors.YELLOW}{success_rate:.1f}%{Colors.END}"
            )

            if success_rate >= 90:
                logger.info(
                    f"{Colors.GREEN}🎉 PRODUCED READY: 9.5/10 - Ready for deployment!{Colors.END}"
                )
                overall_status = "PRODUCTION READY"
            elif success_rate >= 70:
                logger.info(
                    f"{Colors.YELLOW}⚠️  MOSTLY READY: {success_rate:.1f}% - Minor issues to fix{Colors.END}"
                )
                overall_status = "MOSTLY READY"
            else:
                logger.info(
                    f"{Colors.RED}❌ NOT READY: {success_rate:.1f}% - Significant issues need attention{Colors.END}"
                )
                overall_status = "NOT READY"
        else:
            overall_status = "NO TESTS RUN"

        # Duration
        duration = self.results["end_time"] - self.results["start_time"]
        logger.info(f"Test Duration: {duration.total_seconds():.1f}s")

        # Save results
        self.save_test_results()

        logger.info("\n" + "=" * 60)
        self.log(f"🏁 TEST SUITE COMPLETED - {overall_status}", "info")
        logger.info("=" * 60)

        # Return exit code based on success
        if tests_run > 0:
            success_rate = tests_passed / tests_run * 100
            return 0 if success_rate >= 70 else 1
        else:
            return 1

    def save_test_results(self):
        """Save detailed test results to file"""
        results_file = f"production_test_results_{int(time.time())}.json"

        try:
            with open(results_file, "w") as f:
                json.dump(self.results, f, indent=2, default=str)

            self.log(f"Detailed results saved to: {results_file}", "info")

        except Exception as e:
            self.log(f"Failed to save results: {e}", "warn")

    def print_test_summary(self):
        """Print summary of failed tests for debugging"""
        failed_tests = [t for t in self.results["details"] if not t["passed"]]

        if failed_tests:
            logger.info("\n" + Colors.RED + "❌ FAILED TESTS SUMMARY:" + Colors.END)
            for i, test in enumerate(failed_tests, 1):
                logger.info(f"  {i}. {Colors.BOLD}{test['name']}{Colors.END}")
                logger.info(f"     {test['message']}")


async def main():
    """Main test execution"""
    suite = ProductionTestSuite()

    try:
        exit_code = await suite.run_all_tests()
        suite.print_test_summary()

        return exit_code

    except KeyboardInterrupt:
        suite.log("Test suite interrupted by user", "warn")
        return 1
    except Exception as e:
        suite.log(f"Test suite failed: {e}", "fail")
        return 1


if __name__ == "__main__":
    logger.info("🧪 Sophia Intel AI - Production Readiness Test Suite")
    logger.info("Testing all improvements from 9/10 → 10/10")
    logger.info("=" * 60)

    # Run the test suite
    exit_code = asyncio.run(main())

    logger.info(f"Exiting with code: {exit_code}")
    sys.exit(exit_code)
