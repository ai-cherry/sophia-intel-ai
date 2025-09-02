"""
Test script for Natural Language Interface
Tests QuickNLP processing, agent orchestration, and API endpoints
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import requests

from app.agents.simple_orchestrator import AgentRole, SimpleAgentOrchestrator
from app.nl_interface.intents import format_help_text, get_all_intents
from app.nl_interface.quicknlp import CommandIntent, QuickNLP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NLInterfaceTest:
    """Test suite for Natural Language Interface"""

    def __init__(self, api_base_url: str = "http://localhost:8003"):
        self.api_base_url = api_base_url
        self.nlp = QuickNLP()
        self.orchestrator = SimpleAgentOrchestrator()
        self.test_results = []

    def run_all_tests(self):
        """Run all test suites"""
        logger.info("=" * 60)
        logger.info("Starting Natural Language Interface Tests")
        logger.info("=" * 60)

        # Test 1: QuickNLP Processing
        self.test_nlp_processing()

        # Test 2: Intent Recognition
        self.test_intent_recognition()

        # Test 3: Agent Orchestrator
        asyncio.run(self.test_agent_orchestrator())

        # Test 4: API Endpoints (if server is running)
        self.test_api_endpoints()

        # Print summary
        self.print_summary()

    def test_nlp_processing(self):
        """Test NLP processing capabilities"""
        logger.info("\n" + "=" * 40)
        logger.info("Test 1: NLP Processing")
        logger.info("=" * 40)

        test_cases = [
            ("show system status", CommandIntent.SYSTEM_STATUS),
            ("run agent researcher", CommandIntent.RUN_AGENT),
            ("scale redis to 3", CommandIntent.SCALE_SERVICE),
            ("execute workflow backup", CommandIntent.EXECUTE_WORKFLOW),
            ("search for user documents", CommandIntent.QUERY_DATA),
            ("stop ollama", CommandIntent.STOP_SERVICE),
            ("list all agents", CommandIntent.LIST_AGENTS),
            ("show metrics", CommandIntent.GET_METRICS),
            ("help", CommandIntent.HELP),
            ("random gibberish text", CommandIntent.UNKNOWN),
        ]

        for text, expected_intent in test_cases:
            result = self.nlp.process(text)
            success = result.intent == expected_intent

            logger.info(f"  Input: '{text}'")
            logger.info(f"  Expected: {expected_intent.value}")
            logger.info(f"  Got: {result.intent.value}")
            logger.info(f"  Confidence: {result.confidence:.2f}")
            logger.info(f"  Entities: {result.entities}")
            logger.info("  ✅ PASS" if success else "  ❌ FAIL")
            logger.info("-" * 40)

            self.test_results.append({
                "test": "nlp_processing",
                "input": text,
                "success": success,
                "details": {
                    "expected": expected_intent.value,
                    "got": result.intent.value,
                    "confidence": result.confidence
                }
            })

    def test_intent_recognition(self):
        """Test intent pattern matching"""
        logger.info("\n" + "=" * 40)
        logger.info("Test 2: Intent Recognition Patterns")
        logger.info("=" * 40)

        intents = get_all_intents()

        for intent_name, pattern in intents.items():
            logger.info(f"\nTesting intent: {intent_name}")

            # Test with examples
            for example in pattern.examples[:2]:  # Test first 2 examples
                result = self.nlp.process(example)
                success = result.intent.value == intent_name

                logger.info(f"  Example: '{example}'")
                logger.info(f"  Recognized: {result.intent.value}")
                logger.info("  ✅ PASS" if success else "  ❌ FAIL")

                self.test_results.append({
                    "test": "intent_recognition",
                    "intent": intent_name,
                    "example": example,
                    "success": success
                })

    async def test_agent_orchestrator(self):
        """Test agent orchestration"""
        logger.info("\n" + "=" * 40)
        logger.info("Test 3: Agent Orchestrator")
        logger.info("=" * 40)

        try:
            # Test simple workflow
            session_id = "test_session_001"
            user_request = "Create a function to calculate fibonacci numbers"

            logger.info(f"  Session ID: {session_id}")
            logger.info(f"  Request: {user_request}")
            logger.info("  Executing workflow...")

            # Run with just researcher agent for quick test
            context = await self.orchestrator.execute_workflow(
                session_id=session_id,
                user_request=user_request,
                workflow_name="test_workflow",
                agents_chain=[AgentRole.RESEARCHER]
            )

            success = context.end_time is not None

            logger.info(f"  Workflow completed: {success}")
            logger.info(f"  Execution time: {context.end_time - context.start_time:.2f}s" if context.end_time else "N/A")
            logger.info(f"  Tasks executed: {len(context.tasks)}")
            logger.info(f"  Final state keys: {list(context.state.keys())}")
            logger.info("  ✅ PASS" if success else "  ❌ FAIL")

            self.test_results.append({
                "test": "agent_orchestrator",
                "success": success,
                "details": {
                    "session_id": session_id,
                    "tasks_executed": len(context.tasks),
                    "execution_time": context.end_time - context.start_time if context.end_time else None
                }
            })

        except Exception as e:
            logger.error(f"  ❌ FAIL: {e}")
            self.test_results.append({
                "test": "agent_orchestrator",
                "success": False,
                "error": str(e)
            })

    def test_api_endpoints(self):
        """Test API endpoints if server is running"""
        logger.info("\n" + "=" * 40)
        logger.info("Test 4: API Endpoints")
        logger.info("=" * 40)

        endpoints = [
            ("GET", "/api/nl/health", None),
            ("GET", "/api/nl/intents", None),
            ("POST", "/api/nl/process", {"text": "show system status"}),
            ("GET", "/api/nl/system/status", None),
            ("GET", "/api/nl/agents/list", None),
        ]

        for method, endpoint, data in endpoints:
            url = f"{self.api_base_url}{endpoint}"

            try:
                if method == "GET":
                    response = requests.get(url, timeout=2)
                else:
                    response = requests.post(url, json=data, timeout=2)

                success = response.status_code == 200

                logger.info(f"  {method} {endpoint}")
                logger.info(f"  Status: {response.status_code}")
                logger.info("  ✅ PASS" if success else "  ❌ FAIL")

                if success and endpoint == "/api/nl/process":
                    result = response.json()
                    logger.info(f"    Intent: {result.get('intent')}")
                    logger.info(f"    Confidence: {result.get('confidence')}")

                self.test_results.append({
                    "test": "api_endpoint",
                    "endpoint": endpoint,
                    "method": method,
                    "success": success,
                    "status_code": response.status_code
                })

            except requests.exceptions.ConnectionError:
                logger.warning(f"  {method} {endpoint}")
                logger.warning("  ⚠️  SKIP: Server not running")
                self.test_results.append({
                    "test": "api_endpoint",
                    "endpoint": endpoint,
                    "method": method,
                    "success": None,
                    "error": "Server not running"
                })
            except Exception as e:
                logger.error(f"  {method} {endpoint}")
                logger.error(f"  ❌ FAIL: {e}")
                self.test_results.append({
                    "test": "api_endpoint",
                    "endpoint": endpoint,
                    "method": method,
                    "success": False,
                    "error": str(e)
                })

    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)

        # Count results by test type
        test_types = {}
        for result in self.test_results:
            test_type = result["test"]
            if test_type not in test_types:
                test_types[test_type] = {"pass": 0, "fail": 0, "skip": 0}

            if result["success"] is True:
                test_types[test_type]["pass"] += 1
            elif result["success"] is False:
                test_types[test_type]["fail"] += 1
            else:
                test_types[test_type]["skip"] += 1

        # Print summary
        total_pass = 0
        total_fail = 0
        total_skip = 0

        for test_type, counts in test_types.items():
            logger.info(f"\n{test_type}:")
            logger.info(f"  ✅ Passed: {counts['pass']}")
            logger.info(f"  ❌ Failed: {counts['fail']}")
            logger.info(f"  ⚠️  Skipped: {counts['skip']}")

            total_pass += counts["pass"]
            total_fail += counts["fail"]
            total_skip += counts["skip"]

        logger.info("\n" + "-" * 40)
        logger.info("TOTAL:")
        logger.info(f"  ✅ Passed: {total_pass}")
        logger.info(f"  ❌ Failed: {total_fail}")
        logger.info(f"  ⚠️  Skipped: {total_skip}")

        # Overall result
        if total_fail == 0 and total_skip == 0:
            logger.info("\n🎉 ALL TESTS PASSED!")
        elif total_fail == 0:
            logger.info("\n✅ All runnable tests passed (some skipped)")
        else:
            logger.info(f"\n⚠️  {total_fail} tests failed")

        # Save results to file
        results_file = Path(__file__).parent / "test_results.json"
        with open(results_file, "w") as f:
            json.dump(self.test_results, f, indent=2)
        logger.info(f"\nDetailed results saved to: {results_file}")


def test_individual_components():
    """Test individual components without full integration"""
    logger.info("\n" + "=" * 60)
    logger.info("QUICK COMPONENT TESTS")
    logger.info("=" * 60)

    # Test QuickNLP
    logger.info("\n1. Testing QuickNLP...")
    nlp = QuickNLP()

    test_commands = [
        "show me the system status",
        "run the researcher agent",
        "scale ollama to 5 instances",
        "help me understand what you can do"
    ]

    for cmd in test_commands:
        result = nlp.process(cmd)
        logger.info(f"  '{cmd}' -> {result.intent.value} (confidence: {result.confidence:.2f})")

    # Test Intent Patterns
    logger.info("\n2. Testing Intent Patterns...")
    intents = get_all_intents()
    logger.info(f"  Loaded {len(intents)} intent patterns")

    # Test Help Text
    logger.info("\n3. Testing Help Text Generation...")
    help_text = format_help_text()
    logger.info(f"  Generated help text ({len(help_text)} chars)")
    logger.info("  First 200 chars: " + help_text[:200] + "...")

    logger.info("\n✅ Component tests completed")


def main():
    """Main test runner"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Natural Language Interface")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8003",
        help="API base URL (default: http://localhost:8003)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick component tests only"
    )

    args = parser.parse_args()

    if args.quick:
        test_individual_components()
    else:
        tester = NLInterfaceTest(api_base_url=args.api_url)
        tester.run_all_tests()


if __name__ == "__main__":
    main()
