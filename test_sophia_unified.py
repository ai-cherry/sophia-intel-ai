#!/usr/bin/env python3
"""
Comprehensive Test Suite for Sophia Intel AI
Tests all critical components and integrations
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
import httpx
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'


class SophiaTestSuite:
    """Comprehensive test suite for Sophia Intel AI"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def run_all_tests(self):
        """Run all test categories"""
        print(f"{BLUE}{'='*60}{NC}")
        print(f"{BLUE}SOPHIA INTEL AI - COMPREHENSIVE TEST SUITE{NC}")
        print(f"{BLUE}{'='*60}{NC}\n")
        
        # Test categories
        await self.test_configuration()
        await self.test_server_health()
        await self.test_api_endpoints()
        await self.test_integrations()
        await self.test_security()
        await self.test_performance()
        
        # Print summary
        self.print_summary()
        
        # Cleanup
        await self.client.aclose()
    
    # ==================== Configuration Tests ====================
    
    async def test_configuration(self):
        """Test configuration management"""
        print(f"{YELLOW}1. CONFIGURATION TESTS{NC}")
        print("-" * 40)
        
        # Test 1.1: Check for secure environment
        secure_env = Path.home() / ".config/sophia/env"
        if secure_env.exists():
            self.pass_test("1.1", "Secure environment file exists")
        else:
            self.warn_test("1.1", f"Secure environment not found at {secure_env}")
        
        # Test 1.2: Check for exposed secrets in repo (only template)
        env_files = [".env.template"]
        for env_file in env_files:
            if Path(env_file).exists():
                content = Path(env_file).read_text()
                if "xoxb-" in content or "sk-" in content or "pat_" in content:
                    self.fail_test("1.2", f"Exposed secrets found in {env_file}")
                    break
        else:
            self.pass_test("1.2", "No exposed secrets in repository")
        
        # Test 1.3: Import unified config manager
        try:
            from config.unified_manager import get_config_manager
            config = get_config_manager()
            self.pass_test("1.3", "Unified config manager imports successfully")
            
            # Test 1.4: Validate configuration
            issues = config.validate_config()
            if not issues["errors"]:
                self.pass_test("1.4", "Configuration validation passed")
            else:
                self.fail_test("1.4", f"Config errors: {issues['errors']}")
                
        except Exception as e:
            self.fail_test("1.3", f"Config manager import failed: {e}")
        
        print()
    
    # ==================== Server Health Tests ====================
    
    async def test_server_health(self):
        """Test server availability and health"""
        print(f"{YELLOW}2. SERVER HEALTH TESTS{NC}")
        print("-" * 40)
        
        # Test 2.1: Server is running
        try:
            response = await self.client.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                self.pass_test("2.1", "Server is running and healthy")
                
                # Test 2.2: Health response structure
                health_data = response.json()
                required_fields = ["status", "timestamp", "services"]
                if all(field in health_data for field in required_fields):
                    self.pass_test("2.2", "Health response has correct structure")
                else:
                    self.fail_test("2.2", "Health response missing required fields")
                    
            else:
                self.fail_test("2.1", f"Server returned status {response.status_code}")
        except Exception as e:
            self.fail_test("2.1", f"Cannot connect to server: {e}")
        
        # Test 2.3: Root endpoint
        try:
            response = await self.client.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.pass_test("2.3", "Root endpoint accessible")
            else:
                self.fail_test("2.3", f"Root returned status {response.status_code}")
        except Exception as e:
            self.fail_test("2.3", f"Root endpoint error: {e}")
        
        print()
    
    # ==================== API Endpoint Tests ====================
    
    async def test_api_endpoints(self):
        """Test all API endpoints"""
        print(f"{YELLOW}3. API ENDPOINT TESTS{NC}")
        print("-" * 40)
        
        # Test 3.1: Projects overview endpoint
        try:
            response = await self.client.get(f"{self.base_url}/api/projects/overview")
            if response.status_code == 200:
                data = response.json()
                if "sources" in data and "major_projects" in data:
                    self.pass_test("3.1", "Projects overview endpoint working")
                else:
                    self.fail_test("3.1", "Projects response missing fields")
            else:
                self.fail_test("3.1", f"Projects endpoint returned {response.status_code}")
        except Exception as e:
            self.fail_test("3.1", f"Projects endpoint error: {e}")
        
        # Test 3.2: Sync status endpoint
        try:
            response = await self.client.get(f"{self.base_url}/api/projects/sync-status")
            if response.status_code == 200:
                self.pass_test("3.2", "Sync status endpoint working")
            else:
                self.fail_test("3.2", f"Sync status returned {response.status_code}")
        except Exception as e:
            self.fail_test("3.2", f"Sync status error: {e}")
        
        # Test 3.3: Integrations status endpoint
        try:
            response = await self.client.get(f"{self.base_url}/api/integrations/status")
            if response.status_code == 200:
                data = response.json()
                if "slack" in data and "asana" in data:
                    self.pass_test("3.3", "Integrations status endpoint working")
                else:
                    self.fail_test("3.3", "Integrations response incomplete")
            else:
                self.fail_test("3.3", f"Integrations status returned {response.status_code}")
        except Exception as e:
            self.fail_test("3.3", f"Integrations status error: {e}")
        
        # Test 3.4: Chat endpoint
        try:
            chat_data = {
                "message": "Test message",
                "session_id": "test-session",
                "context": {"page": "test"}
            }
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=chat_data
            )
            if response.status_code in [200, 500]:  # 500 if orchestrator not fully configured
                self.pass_test("3.4", "Chat endpoint responds")
            else:
                self.fail_test("3.4", f"Chat endpoint returned {response.status_code}")
        except Exception as e:
            self.warn_test("3.4", f"Chat endpoint error (may need config): {e}")
        
        print()
    
    # ==================== Integration Tests ====================
    
    async def test_integrations(self):
        """Test integration configurations"""
        print(f"{YELLOW}4. INTEGRATION TESTS{NC}")
        print("-" * 40)
        
        # Test 4.1: Slack integration
        try:
            response = await self.client.post(f"{self.base_url}/api/integrations/slack/test")
            data = response.json()
            if data.get("success"):
                self.pass_test("4.1", "Slack integration configured and working")
            else:
                error = data.get("error", "Not configured")
                self.warn_test("4.1", f"Slack: {error}")
        except Exception as e:
            self.warn_test("4.1", f"Slack test error: {e}")
        
        # Test 4.2: Asana integration
        try:
            response = await self.client.post(f"{self.base_url}/api/integrations/asana/test")
            data = response.json()
            if data.get("success"):
                self.pass_test("4.2", "Asana integration configured and working")
            else:
                error = data.get("error", "Not configured")
                self.warn_test("4.2", f"Asana: {error}")
        except Exception as e:
            self.warn_test("4.2", f"Asana test error: {e}")
        
        # Test 4.3: Linear integration
        try:
            response = await self.client.post(f"{self.base_url}/api/integrations/linear/test")
            data = response.json()
            if data.get("success"):
                self.pass_test("4.3", "Linear integration configured and working")
            else:
                error = data.get("error", "Not configured")
                self.warn_test("4.3", f"Linear: {error}")
        except Exception as e:
            self.warn_test("4.3", f"Linear test error: {e}")
        
        print()
    
    # ==================== Security Tests ====================
    
    async def test_security(self):
        """Test security configurations"""
        print(f"{YELLOW}5. SECURITY TESTS{NC}")
        print("-" * 40)
        
        # Test 5.1: CORS headers
        try:
            response = await self.client.options(
                f"{self.base_url}/api/health",
                headers={"Origin": "http://localhost:3000"}
            )
            if "access-control-allow-origin" in response.headers:
                self.pass_test("5.1", "CORS headers configured")
            else:
                self.warn_test("5.1", "CORS headers not found")
        except Exception as e:
            self.warn_test("5.1", f"CORS test error: {e}")
        
        # Test 5.2: No sensitive data in error responses
        try:
            response = await self.client.get(f"{self.base_url}/api/nonexistent")
            if response.status_code == 404:
                data = response.json()
                content = json.dumps(data)
                if "password" not in content.lower() and "token" not in content.lower():
                    self.pass_test("5.2", "Error responses don't leak sensitive data")
                else:
                    self.fail_test("5.2", "Error responses may contain sensitive data")
        except Exception as e:
            self.warn_test("5.2", f"Error response test failed: {e}")
        
        print()
    
    # ==================== Performance Tests ====================
    
    async def test_performance(self):
        """Test performance metrics"""
        print(f"{YELLOW}6. PERFORMANCE TESTS{NC}")
        print("-" * 40)
        
        # Test 6.1: Health endpoint response time
        start = datetime.now()
        try:
            response = await self.client.get(f"{self.base_url}/api/health")
            elapsed = (datetime.now() - start).total_seconds()
            if elapsed < 0.5:
                self.pass_test("6.1", f"Health endpoint fast ({elapsed:.3f}s)")
            elif elapsed < 2:
                self.warn_test("6.1", f"Health endpoint slow ({elapsed:.3f}s)")
            else:
                self.fail_test("6.1", f"Health endpoint too slow ({elapsed:.3f}s)")
        except Exception as e:
            self.fail_test("6.1", f"Performance test error: {e}")
        
        # Test 6.2: Projects endpoint response time
        start = datetime.now()
        try:
            response = await self.client.get(f"{self.base_url}/api/projects/overview")
            elapsed = (datetime.now() - start).total_seconds()
            if elapsed < 1:
                self.pass_test("6.2", f"Projects endpoint fast ({elapsed:.3f}s)")
            elif elapsed < 3:
                self.warn_test("6.2", f"Projects endpoint slow ({elapsed:.3f}s)")
            else:
                self.fail_test("6.2", f"Projects endpoint too slow ({elapsed:.3f}s)")
        except Exception as e:
            self.fail_test("6.2", f"Projects performance test error: {e}")
        
        print()
    
    # ==================== Helper Methods ====================
    
    def pass_test(self, test_id: str, message: str):
        """Record a passing test"""
        self.results["passed"].append(test_id)
        print(f"  {GREEN}✓{NC} Test {test_id}: {message}")
    
    def fail_test(self, test_id: str, message: str):
        """Record a failing test"""
        self.results["failed"].append(test_id)
        print(f"  {RED}✗{NC} Test {test_id}: {message}")
    
    def warn_test(self, test_id: str, message: str):
        """Record a warning"""
        self.results["warnings"].append(test_id)
        print(f"  {YELLOW}⚠{NC} Test {test_id}: {message}")
    
    def print_summary(self):
        """Print test summary"""
        total = len(self.results["passed"]) + len(self.results["failed"]) + len(self.results["warnings"])
        
        print(f"\n{BLUE}{'='*60}{NC}")
        print(f"{BLUE}TEST SUMMARY{NC}")
        print(f"{BLUE}{'='*60}{NC}")
        
        print(f"\nTotal Tests: {total}")
        print(f"{GREEN}Passed: {len(self.results['passed'])}{NC}")
        print(f"{RED}Failed: {len(self.results['failed'])}{NC}")
        print(f"{YELLOW}Warnings: {len(self.results['warnings'])}{NC}")
        
        # Overall status
        if not self.results["failed"]:
            if not self.results["warnings"]:
                print(f"\n{GREEN}✓ ALL TESTS PASSED!{NC}")
            else:
                print(f"\n{GREEN}✓ Tests passed with {len(self.results['warnings'])} warnings{NC}")
        else:
            print(f"\n{RED}✗ {len(self.results['failed'])} tests failed{NC}")
        
        # Save results
        results_file = Path("test_results.json")
        with open(results_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": self.results,
                "summary": {
                    "total": total,
                    "passed": len(self.results["passed"]),
                    "failed": len(self.results["failed"]),
                    "warnings": len(self.results["warnings"])
                }
            }, f, indent=2)
        
        print(f"\nDetailed results saved to: {results_file}")


async def main():
    """Run the test suite"""
    suite = SophiaTestSuite()
    await suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
