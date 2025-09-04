#!/usr/bin/env python3
"""
Test Enhanced API Testing Capabilities
=======================================
Verifies that Sophia can now properly handle API testing commands
with the new dynamic tool integration and enhanced command recognition.
"""

import asyncio
import logging
from datetime import datetime
import json
from typing import Dict, Any

# Import the enhanced orchestrator
from app.orchestrators.sophia_agno_orchestrator import (
    SophiaAGNOOrchestrator,
    BusinessContext
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APITestingSuite:
    """Test suite for enhanced API testing capabilities"""
    
    def __init__(self):
        self.orchestrator = None
        self.test_results = []
        
    async def setup(self):
        """Initialize the orchestrator"""
        logger.info("🚀 Initializing Sophia AGNO Orchestrator with enhanced capabilities...")
        
        self.orchestrator = SophiaAGNOOrchestrator()
        success = await self.orchestrator.initialize()
        
        if success:
            logger.info("✅ Orchestrator initialized successfully")
        else:
            logger.error("❌ Failed to initialize orchestrator")
            
        return success
    
    async def test_api_connection(self, service: str) -> Dict[str, Any]:
        """Test API connection command"""
        test_name = f"Test {service} API Connection"
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 Testing: {test_name}")
        logger.info(f"{'='*60}")
        
        # Create test context
        context = BusinessContext(
            user_id="test_user",
            session_id=f"test_session_{service}"
        )
        
        # Test the exact command that was failing
        test_command = f"test {service} api connection"
        logger.info(f"📨 Sending command: '{test_command}'")
        
        try:
            # Process through the orchestrator
            response = await self.orchestrator.process_business_request(
                test_command,
                context
            )
            
            # Analyze response
            result = {
                "test": test_name,
                "command": test_command,
                "success": response.success,
                "command_type": response.command_type,
                "response_preview": response.content[:200] if response.content else "No response",
                "has_api_data": bool(response.data),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Check if this is an actual API test response (not generic)
            is_generic = "first principles" in response.content.lower() or \
                        "let me analyze" in response.content.lower() or \
                        "strategic approach" in response.content.lower()
            
            result["is_generic_response"] = is_generic
            result["properly_handled"] = not is_generic and response.command_type == "api_test"
            
            # Log the response
            if result["properly_handled"]:
                logger.info(f"✅ PASS: {service} API test properly handled!")
                logger.info(f"   Command Type: {response.command_type}")
                logger.info(f"   Response: {response.content[:150]}...")
            else:
                logger.warning(f"⚠️ FAIL: {service} API test returned generic response")
                logger.warning(f"   Command Type: {response.command_type}")
                logger.warning(f"   Response: {response.content[:150]}...")
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error testing {service}: {str(e)}")
            result = {
                "test": test_name,
                "command": test_command,
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.test_results.append(result)
            return result
    
    async def test_api_variations(self) -> None:
        """Test various API command variations"""
        variations = [
            "test gong api",
            "check hubspot connection",
            "validate salesforce integration",
            "verify github api",
            "connect to slack",
            "gong api status",
            "is hubspot connected"
        ]
        
        logger.info(f"\n{'='*60}")
        logger.info("🔬 Testing API Command Variations")
        logger.info(f"{'='*60}")
        
        for command in variations:
            logger.info(f"\n📨 Testing: '{command}'")
            
            context = BusinessContext(
                user_id="test_user",
                session_id=f"variation_test_{hash(command)}"
            )
            
            try:
                response = await self.orchestrator.process_business_request(command, context)
                
                is_properly_handled = (
                    response.command_type in ["api_test", "api_status", "api_connect"] and
                    "first principles" not in response.content.lower()
                )
                
                if is_properly_handled:
                    logger.info(f"  ✅ Properly handled as {response.command_type}")
                else:
                    logger.warning(f"  ⚠️ Generic response (type: {response.command_type})")
                    
            except Exception as e:
                logger.error(f"  ❌ Error: {str(e)}")
    
    async def run_all_tests(self):
        """Run all API testing capability tests"""
        logger.info("🏁 Starting Enhanced API Testing Capability Tests")
        logger.info("="*60)
        
        # Initialize orchestrator
        if not await self.setup():
            logger.error("Failed to setup orchestrator")
            return
        
        # Test main services that were failing
        main_services = ["gong", "hubspot", "salesforce", "github"]
        
        for service in main_services:
            await self.test_api_connection(service)
            await asyncio.sleep(0.5)  # Small delay between tests
        
        # Test command variations
        await self.test_api_variations()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        logger.info(f"\n{'='*60}")
        logger.info("📄 TEST SUMMARY")
        logger.info(f"{'='*60}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.get("properly_handled", False))
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
        
        # Show failed tests
        if failed_tests > 0:
            logger.info("\n😕 Failed Tests:")
            for result in self.test_results:
                if not result.get("properly_handled", False):
                    logger.info(f"  - {result['test']}: {result.get('command_type', 'unknown')}")
        
        # Save results to file
        with open("api_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        logger.info("\n💾 Results saved to api_test_results.json")
        
        # Final verdict
        if passed_tests == total_tests:
            logger.info("\n🎆 ALL TESTS PASSED! Sophia can now properly handle API testing commands! 🎆")
        elif passed_tests > 0:
            logger.info(f"\n🎅 PARTIAL SUCCESS: {passed_tests}/{total_tests} tests passed")
        else:
            logger.info("\n😢 Tests failed - API command handling needs more work")


async def main():
    """Main test runner"""
    suite = APITestingSuite()
    await suite.run_all_tests()


if __name__ == "__main__":
    print("""
🚀 ENHANCED API TESTING CAPABILITY TEST
========================================
Testing Sophia's ability to handle API commands
with the new dynamic tool integration system.

This addresses the issue where Sophia was giving
generic responses to specific API test commands.
    """)
    
    asyncio.run(main())