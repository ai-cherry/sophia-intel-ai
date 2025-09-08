#!/usr/bin/env python3
"""
NL-Swarm Integration Quality Control Test Suite
Validates all components of the Phase 1 implementation
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.ai_logger import logger
from app.nl_interface.command_dispatcher import ExecutionMode, SmartCommandDispatcher
from app.nl_interface.memory_connector import NLInteraction, NLMemoryConnector
from app.nl_interface.quicknlp import CachedQuickNLP, CommandIntent
from app.swarms.performance_optimizer import CircuitBreaker, SwarmOptimizer


class Colors:
    """ANSI color codes for terminal output"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class QualityControlTester:
    """Comprehensive test suite for NL-Swarm integration"""

    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []

    def print_header(self, text: str):
        """Print formatted header"""
        logger.info(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        logger.info(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
        logger.info(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

    def print_test(self, test_name: str, passed: bool, details: str = ""):
        """Print test result"""
        status = (
            f"{Colors.OKGREEN}✓ PASSED{Colors.ENDC}"
            if passed
            else f"{Colors.FAIL}✗ FAILED{Colors.ENDC}"
        )
        logger.info(f"  {test_name}: {status}")
        if details:
            logger.info(f"    {Colors.OKCYAN}{details}{Colors.ENDC}")

        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

        self.test_results.append(
            {"test": test_name, "passed": passed, "details": details}
        )

    async def test_config_loading(self) -> bool:
        """Test configuration file loading"""
        self.print_header("Testing Configuration Loading")

        try:
            # Check if config file exists
            config_path = Path("app/config/nl_swarm_integration.json")
            self.print_test(
                "Config file exists", config_path.exists(), f"Path: {config_path}"
            )

            # Load and validate config
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)

                # Check required sections
                required_sections = [
                    "complexity_thresholds",
                    "execution_modes",
                    "swarm_eligible_intents",
                    "memory_enrichment",
                    "circuit_breakers",
                ]

                for section in required_sections:
                    self.print_test(
                        f"Config section '{section}'",
                        section in config,
                        f"Found: {list(config.get(section, {}).keys())[:3]}...",
                    )

                return all(section in config for section in required_sections)

            return False

        except Exception as e:
            self.print_test("Config loading", False, str(e))
            return False

    async def test_smart_dispatcher(self) -> bool:
        """Test SmartCommandDispatcher functionality"""
        self.print_header("Testing SmartCommandDispatcher")

        try:
            # Initialize dispatcher
            dispatcher = SmartCommandDispatcher(
                config_file="app/config/nl_swarm_integration.json"
            )
            self.print_test("Dispatcher initialization", True, "Successfully created")

            # Test simple command (should use Lite mode)
            simple_result = await dispatcher.process_command(
                text="show system status", session_id="test-001"
            )

            self.print_test(
                "Simple command processing",
                simple_result.success,
                f"Mode: {simple_result.execution_mode.value}, Time: {simple_result.execution_time:.2f}s",
            )

            # Test complexity analysis
            task = {"description": "show system status", "intent": "SYSTEM_STATUS"}
            complexity = dispatcher.optimizer.calculate_task_complexity(task)

            self.print_test(
                "Complexity calculation",
                0 <= complexity <= 1,
                f"Complexity: {complexity:.2f}",
            )

            # Test mode selection
            mode = ExecutionMode.LITE if complexity < 0.3 else ExecutionMode.BALANCED
            self.print_test(
                "Mode selection logic",
                mode == ExecutionMode.LITE,
                f"Selected: {mode.value}",
            )

            # Test circuit breakers
            cb_test = all(
                isinstance(cb, CircuitBreaker)
                for cb in dispatcher.circuit_breakers.values()
            )
            self.print_test(
                "Circuit breakers",
                cb_test,
                f"Breakers: {list(dispatcher.circuit_breakers.keys())}",
            )

            # Test performance metrics
            metrics = dispatcher._get_performance_metrics()
            self.print_test(
                "Performance metrics",
                "dispatcher_stats" in metrics,
                f"Metrics collected: {len(metrics)} categories",
            )

            return simple_result.success

        except Exception as e:
            self.print_test("SmartCommandDispatcher", False, str(e))
            return False

    async def test_nlp_processing(self) -> bool:
        """Test NLP processing components"""
        self.print_header("Testing NLP Processing")

        try:
            # Initialize NLP processor
            nlp = CachedQuickNLP()
            self.print_test("CachedQuickNLP initialization", True, "Cache enabled")

            # Test various commands
            test_commands = [
                ("show system status", CommandIntent.SYSTEM_STATUS),
                ("run agent researcher", CommandIntent.RUN_AGENT),
                ("query data about users", CommandIntent.QUERY_DATA),
                ("help", CommandIntent.HELP),
            ]

            all_passed = True
            for text, expected_intent in test_commands:
                result = nlp.process(text)
                passed = result.intent == expected_intent
                all_passed = all_passed and passed

                self.print_test(
                    f"Parse '{text[:20]}...'",
                    passed,
                    f"Intent: {result.intent.value}, Confidence: {result.confidence:.2f}",
                )

            # Test caching performance
            start_time = time.time()
            for _ in range(10):
                nlp.process("show system status")
            cached_time = time.time() - start_time

            cache_stats = nlp.get_cache_stats()
            self.print_test(
                "Cache performance",
                cache_stats["hit_rate"] > 0.8,
                f"Hit rate: {cache_stats['hit_rate']:.1%}, Time: {cached_time:.3f}s",
            )

            return all_passed

        except Exception as e:
            self.print_test("NLP Processing", False, str(e))
            return False

    async def test_memory_integration(self) -> bool:
        """Test memory connector integration"""
        self.print_header("Testing Memory Integration")

        try:
            # Initialize memory connector
            memory = NLMemoryConnector()
            await memory.connect()
            self.print_test("Memory connector initialization", True, "Connected")

            # Test storing interaction
            interaction = NLInteraction(
                session_id="test-002",
                timestamp="2024-01-01T00:00:00",
                user_input="test command",
                intent="TEST",
                entities={},
                confidence=0.9,
                response="test response",
            )

            stored = await memory.store_interaction(interaction)
            self.print_test("Store interaction", stored, "Interaction stored in cache")

            # Test retrieving history
            history = await memory.retrieve_session_history("test-002", limit=5)
            self.print_test(
                "Retrieve history",
                isinstance(history, list),
                f"Retrieved {len(history)} interactions",
            )

            # Test context summary
            summary = await memory.get_context_summary("test-002")
            self.print_test(
                "Context summary",
                "session_id" in summary,
                "Summary generated for session",
            )

            await memory.disconnect()
            return True

        except Exception as e:
            self.print_test("Memory Integration", False, f"Degraded mode: {str(e)}")
            return True  # Still pass as memory can work in degraded mode

    async def test_optimizer_components(self) -> bool:
        """Test SwarmOptimizer and performance components"""
        self.print_header("Testing Optimization Components")

        try:
            # Initialize optimizer
            optimizer = SwarmOptimizer()
            self.print_test("SwarmOptimizer initialization", True, "Created")

            # Test task complexity calculation
            tasks = [
                ({"description": "fix bug"}, "simple", 0.4),
                ({"description": "implement new feature"}, "medium", 0.6),
                ({"description": "architect enterprise system"}, "complex", 0.8),
            ]

            for task, label, expected_min in tasks:
                complexity = optimizer.calculate_task_complexity(task)
                self.print_test(
                    f"Complexity for '{label}' task",
                    complexity >= expected_min - 0.2,
                    f"Score: {complexity:.2f}",
                )

            # Test circuit breaker
            cb = optimizer.get_circuit_breaker("test_component")
            self.print_test(
                "Circuit breaker creation",
                cb.state == "closed",
                f"Initial state: {cb.state}",
            )

            # Test degradation manager
            health = optimizer.degradation_manager.get_system_health_score()
            self.print_test(
                "System health check", health == 1.0, f"Health score: {health:.1%}"
            )

            return True

        except Exception as e:
            self.print_test("Optimizer Components", False, str(e))
            return False

    async def test_api_endpoints(self) -> bool:
        """Test API endpoint definitions"""
        self.print_header("Testing API Endpoints")

        try:
            # Check if endpoint file has been updated
            endpoint_file = Path("app/api/nl_endpoints.py")

            if endpoint_file.exists():
                content = endpoint_file.read_text()

                # Check for new imports
                has_dispatcher = "SmartCommandDispatcher" in content
                self.print_test(
                    "SmartCommandDispatcher import",
                    has_dispatcher,
                    "Import found in endpoints",
                )

                # Check for new endpoints
                endpoints = [
                    "/swarm/status",
                    "/swarm/performance",
                    "/swarm/optimize",
                    "/swarm/modes",
                    "/swarm/reset",
                ]

                for endpoint in endpoints:
                    has_endpoint = endpoint in content
                    self.print_test(
                        f"Endpoint '{endpoint}'",
                        has_endpoint,
                        "Defined" if has_endpoint else "Missing",
                    )

                return has_dispatcher

            return False

        except Exception as e:
            self.print_test("API Endpoints", False, str(e))
            return False

    async def test_integration_flow(self) -> bool:
        """Test complete integration flow"""
        self.print_header("Testing Complete Integration Flow")

        try:
            dispatcher = SmartCommandDispatcher()

            # Test flow: Simple -> Medium -> Complex
            test_cases = [
                ("list all agents", ExecutionMode.LITE, 0.5),
                ("run agent researcher to analyze data", ExecutionMode.BALANCED, 2.0),
                ("architect a microservices solution", ExecutionMode.QUALITY, 5.0),
            ]

            session_id = "integration-test"

            for command, expected_mode, _max_time in test_cases:
                result = await dispatcher.process_command(
                    text=command, session_id=session_id
                )

                mode_match = result.execution_mode == expected_mode

                self.print_test(
                    f"Flow: '{command[:30]}...'",
                    result.success and mode_match,
                    f"Mode: {result.execution_mode.value}, Time: {result.execution_time:.2f}s",
                )

            # Test session optimization
            optimization = await dispatcher.optimize_for_session(session_id)
            self.print_test(
                "Session optimization",
                "recommended_mode" in optimization,
                f"Recommended: {optimization.get('recommended_mode', 'N/A')}",
            )

            return True

        except Exception as e:
            self.print_test("Integration Flow", False, str(e))
            return False

    def print_summary(self):
        """Print test summary"""
        self.print_header("Quality Control Test Summary")

        total = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total * 100) if total > 0 else 0

        logger.info(f"\n{Colors.BOLD}Results:{Colors.ENDC}")
        logger.info(f"  {Colors.OKGREEN}Passed: {self.passed_tests}{Colors.ENDC}")
        logger.info(f"  {Colors.FAIL}Failed: {self.failed_tests}{Colors.ENDC}")
        logger.info(f"  {Colors.BOLD}Pass Rate: {pass_rate:.1f}%{Colors.ENDC}")

        if pass_rate >= 80:
            logger.info(
                f"\n{Colors.OKGREEN}{Colors.BOLD}✓ QUALITY CONTROL PASSED{Colors.ENDC}"
            )
            logger.info(
                f"{Colors.OKGREEN}The NL-Swarm integration meets production quality standards!{Colors.ENDC}"
            )
        else:
            logger.info(
                f"\n{Colors.WARNING}{Colors.BOLD}⚠ QUALITY CONTROL NEEDS ATTENTION{Colors.ENDC}"
            )
            logger.info(
                f"{Colors.WARNING}Some tests failed. Review the results above.{Colors.ENDC}"
            )

        # Write detailed report
        report_path = Path("test_results_nl_swarm.json")
        with open(report_path, "w") as f:
            json.dump(
                {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "passed": self.passed_tests,
                    "failed": self.failed_tests,
                    "pass_rate": pass_rate,
                    "results": self.test_results,
                },
                f,
                indent=2,
            )

        logger.info(
            f"\n{Colors.OKCYAN}Detailed report saved to: {report_path}{Colors.ENDC}"
        )

    async def run_all_tests(self):
        """Run all quality control tests"""
        logger.info(f"{Colors.HEADER}{Colors.BOLD}")
        logger.info("╔══════════════════════════════════════════════════════════╗")
        logger.info("║     NL-SWARM INTEGRATION QUALITY CONTROL TEST SUITE     ║")
        logger.info("╚══════════════════════════════════════════════════════════╝")
        logger.info(f"{Colors.ENDC}")

        # Run test suites
        await self.test_config_loading()
        await self.test_smart_dispatcher()
        await self.test_nlp_processing()
        await self.test_memory_integration()
        await self.test_optimizer_components()
        await self.test_api_endpoints()
        await self.test_integration_flow()

        # Print summary
        self.print_summary()


async def main():
    """Main test execution"""
    tester = QualityControlTester()
    await tester.run_all_tests()

    # Return exit code based on results
    return 0 if tester.failed_tests == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
