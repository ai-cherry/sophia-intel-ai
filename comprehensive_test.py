#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced Sophia & Artemis
========================================================
Tests all API endpoints and enhanced functionality
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ComprehensiveTestSuite:
    def __init__(self):
        self.sophia_url = "http://localhost:9000"
        self.artemis_url = "http://localhost:8001"
        self.results = []
        
    async def test_sophia_api_commands(self) -> Dict[str, Any]:
        """Test Sophia's enhanced API testing capabilities"""
        logger.info("\n" + "="*60)
        logger.info("💎 TESTING SOPHIA API COMMANDS")
        logger.info("="*60)
        
        test_cases = [
            {"message": "test gong api connection", "expected": "api_test", "service": "gong"},
            {"message": "test hubspot api", "expected": "api_test", "service": "hubspot"},
            {"message": "check salesforce connection", "expected": "api_test", "service": "salesforce"},
            {"message": "validate github integration", "expected": "api_test", "service": "github"},
            {"message": "gong api status", "expected": "api_status", "service": "gong"},
        ]
        
        results = {"passed": 0, "failed": 0, "details": []}
        
        async with httpx.AsyncClient() as client:
            for test in test_cases:
                try:
                    response = await client.post(
                        f"{self.sophia_url}/api/sophia/chat",
                        json={"message": test["message"], "session_id": f"test_{test['service']}"}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Check if it's not a generic response
                        is_proper = (
                            data.get("command_type") == test["expected"] and
                            "first principles" not in data.get("response", "").lower() and
                            "let me analyze" not in data.get("response", "").lower()
                        )
                        
                        if is_proper:
                            logger.info(f"  ✅ PASS: '{test['message']}' -> {data.get('command_type')}")
                            results["passed"] += 1
                        else:
                            logger.warning(f"  ❌ FAIL: '{test['message']}' returned generic response")
                            results["failed"] += 1
                        
                        results["details"].append({
                            "test": test["message"],
                            "success": is_proper,
                            "command_type": data.get("command_type"),
                            "connected": data.get("success", False)
                        })
                    else:
                        logger.error(f"  ❌ HTTP Error: {response.status_code}")
                        results["failed"] += 1
                        
                except Exception as e:
                    logger.error(f"  ❌ Error testing '{test['message']}': {str(e)}")
                    results["failed"] += 1
        
        return results
    
    async def test_sophia_business_intelligence(self) -> Dict[str, Any]:
        """Test Sophia's business intelligence capabilities"""
        logger.info("\n" + "="*60)
        logger.info("📊 TESTING SOPHIA BUSINESS INTELLIGENCE")
        logger.info("="*60)
        
        test_cases = [
            "analyze my sales pipeline",
            "show client health metrics",
            "what are the market trends",
            "competitive analysis for our product"
        ]
        
        results = {"passed": 0, "failed": 0}
        
        async with httpx.AsyncClient() as client:
            for test in test_cases:
                try:
                    response = await client.post(
                        f"{self.sophia_url}/api/sophia/chat",
                        json={"message": test, "session_id": "test_bi"}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            logger.info(f"  ✅ PASS: '{test}' processed successfully")
                            results["passed"] += 1
                        else:
                            logger.warning(f"  ⚠️  WARN: '{test}' failed")
                            results["failed"] += 1
                    else:
                        results["failed"] += 1
                        
                except Exception as e:
                    logger.error(f"  ❌ Error: {str(e)}")
                    results["failed"] += 1
        
        return results
    
    async def test_artemis_technical_ops(self) -> Dict[str, Any]:
        """Test Artemis technical operations"""
        logger.info("\n" + "="*60)
        logger.info("⚛️ TESTING ARTEMIS TECHNICAL OPERATIONS")
        logger.info("="*60)
        
        test_cases = [
            "review this code for security issues",
            "analyze system architecture",
            "performance optimization suggestions",
            "test api connections"
        ]
        
        results = {"passed": 0, "failed": 0}
        
        async with httpx.AsyncClient() as client:
            for test in test_cases:
                try:
                    response = await client.post(
                        f"{self.artemis_url}/api/artemis/chat",
                        json={"message": test, "session_id": "test_tech"}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            logger.info(f"  ✅ PASS: '{test}' processed")
                            results["passed"] += 1
                        else:
                            logger.warning(f"  ⚠️  WARN: '{test}' failed")
                            results["failed"] += 1
                    else:
                        results["failed"] += 1
                        
                except Exception as e:
                    logger.error(f"  ❌ Error: {str(e)}")
                    results["failed"] += 1
        
        return results
    
    async def test_health_endpoints(self) -> Dict[str, Any]:
        """Test health check endpoints"""
        logger.info("\n" + "="*60)
        logger.info("🏥 TESTING HEALTH ENDPOINTS")
        logger.info("="*60)
        
        endpoints = [
            ("Sophia", f"{self.sophia_url}/health"),
            ("Artemis", f"{self.artemis_url}/health"),
            ("MCP Server", "http://localhost:3333/health"),
            ("Unified API", "http://localhost:8006/health")
        ]
        
        results = {"healthy": 0, "unhealthy": 0}
        
        async with httpx.AsyncClient() as client:
            for name, url in endpoints:
                try:
                    response = await client.get(url, timeout=5.0)
                    if response.status_code == 200:
                        logger.info(f"  ✅ {name}: HEALTHY")
                        results["healthy"] += 1
                    else:
                        logger.warning(f"  ⚠️  {name}: Status {response.status_code}")
                        results["unhealthy"] += 1
                except Exception as e:
                    logger.error(f"  ❌ {name}: UNREACHABLE")
                    results["unhealthy"] += 1
        
        return results
    
    async def run_all_tests(self):
        """Run all test suites"""
        logger.info("\n" + "#"*60)
        logger.info("#  COMPREHENSIVE TEST SUITE FOR ENHANCED PLATFORM  #")
        logger.info("#"*60)
        
        # Run tests
        sophia_api_results = await self.test_sophia_api_commands()
        sophia_bi_results = await self.test_sophia_business_intelligence()
        artemis_results = await self.test_artemis_technical_ops()
        health_results = await self.test_health_endpoints()
        
        # Generate summary
        logger.info("\n" + "="*60)
        logger.info("📄 FINAL TEST SUMMARY")
        logger.info("="*60)
        
        total_passed = (
            sophia_api_results["passed"] + 
            sophia_bi_results["passed"] + 
            artemis_results["passed"] + 
            health_results["healthy"]
        )
        
        total_failed = (
            sophia_api_results["failed"] + 
            sophia_bi_results["failed"] + 
            artemis_results["failed"] + 
            health_results["unhealthy"]
        )
        
        logger.info(f"")
        logger.info(f"🎆 Sophia API Commands:  {sophia_api_results['passed']}/{sophia_api_results['passed'] + sophia_api_results['failed']} passed")
        logger.info(f"📊 Sophia Business Intel: {sophia_bi_results['passed']}/{sophia_bi_results['passed'] + sophia_bi_results['failed']} passed")
        logger.info(f"⚛️  Artemis Technical:    {artemis_results['passed']}/{artemis_results['passed'] + artemis_results['failed']} passed")
        logger.info(f"🏥 Health Checks:        {health_results['healthy']}/{health_results['healthy'] + health_results['unhealthy']} healthy")
        logger.info(f"")
        logger.info(f"TOTAL: {total_passed}/{total_passed + total_failed} tests passed")
        
        success_rate = (total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0
        
        if success_rate >= 90:
            logger.info(f"\n🎆 EXCELLENT! {success_rate:.1f}% success rate! 🎆")
        elif success_rate >= 70:
            logger.info(f"\n✅ GOOD: {success_rate:.1f}% success rate")
        else:
            logger.info(f"\n⚠️  NEEDS WORK: {success_rate:.1f}% success rate")
        
        # Show specific API test results
        if sophia_api_results.get("details"):
            logger.info("\n🔍 API Connection Status:")
            for detail in sophia_api_results["details"]:
                status = "✅" if detail["success"] else "❌"
                logger.info(f"  {status} {detail['test'].split()[1].upper()}: {detail.get('command_type', 'unknown')}")
        
        # Save results
        with open("test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "sophia_api": sophia_api_results,
                "sophia_bi": sophia_bi_results,
                "artemis": artemis_results,
                "health": health_results,
                "success_rate": success_rate
            }, f, indent=2)
        
        logger.info("\n💾 Results saved to test_results.json")


async def main():
    suite = ComprehensiveTestSuite()
    await suite.run_all_tests()


if __name__ == "__main__":
    print("""
🚀 COMPREHENSIVE PLATFORM TEST SUITE
=====================================
Testing enhanced Sophia & Artemis capabilities
including API testing, business intelligence,
and technical operations.
    """)
    
    asyncio.run(main())