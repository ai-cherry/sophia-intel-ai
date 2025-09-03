#!/usr/bin/env python3
"""
AI Orchestra Dashboard Integration Test Suite
Tests all connections, APIs, and WebSocket functionality
"""

import asyncio
import json
import time
from typing import Dict, List, Any
import httpx
import websockets
from datetime import datetime
from colored import fg, attr

# Configuration
API_BASE_URL = "http://localhost:8003"
WS_URL = "ws://localhost:8003"
FRONTEND_URL = "http://localhost:3000"

class IntegrationTester:
    """Comprehensive integration testing for Orchestra Dashboard"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        
    def print_header(self, title: str):
        """Print formatted section header"""
        print(f"\n{fg('cyan')}{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}{attr('reset')}")
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result with formatting"""
        if success:
            print(f"{fg('green')}✅ {test_name}{attr('reset')}")
            self.passed += 1
        else:
            print(f"{fg('red')}❌ {test_name}{attr('reset')}")
            if details:
                print(f"   {fg('yellow')}{details}{attr('reset')}")
            self.failed += 1
            
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    async def test_backend_health(self) -> bool:
        """Test backend API health endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/health")
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(
                        "Backend Health Check",
                        True,
                        f"Service: {data.get('service', 'Unknown')}"
                    )
                    return True
                else:
                    self.log_result(
                        "Backend Health Check",
                        False,
                        f"Status code: {response.status_code}"
                    )
                    return False
        except Exception as e:
            self.log_result("Backend Health Check", False, str(e))
            return False
            
    async def test_frontend_availability(self) -> bool:
        """Test frontend server availability"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(FRONTEND_URL)
                if response.status_code == 200:
                    self.log_result("Frontend Server", True, "Next.js running")
                    return True
                else:
                    self.log_result(
                        "Frontend Server",
                        False,
                        f"Status code: {response.status_code}"
                    )
                    return False
        except Exception as e:
            self.log_result("Frontend Server", False, str(e))
            return False
            
    async def test_cors_configuration(self) -> bool:
        """Test CORS headers for cross-origin requests"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.options(
                    f"{API_BASE_URL}/health",
                    headers={
                        "Origin": "http://localhost:3000",
                        "Access-Control-Request-Method": "GET"
                    }
                )
                
                cors_headers = response.headers.get("access-control-allow-origin")
                if cors_headers:
                    self.log_result(
                        "CORS Configuration",
                        True,
                        f"Allow-Origin: {cors_headers}"
                    )
                    return True
                else:
                    self.log_result(
                        "CORS Configuration",
                        False,
                        "No CORS headers found"
                    )
                    return False
        except Exception as e:
            self.log_result("CORS Configuration", False, str(e))
            return False
            
    async def test_websocket_connection(self) -> bool:
        """Test WebSocket connection establishment"""
        ws_endpoints = [
            "/ws",
            "/api/v2/ws",
            "/orchestrator/ws",
            "/v2/ws"
        ]
        
        for endpoint in ws_endpoints:
            try:
                uri = f"{WS_URL}{endpoint}"
                async with websockets.connect(uri) as websocket:
                    # Send test message
                    await websocket.send(json.dumps({
                        "type": "ping",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Wait for response (with timeout)
                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=2.0
                        )
                        self.log_result(
                            f"WebSocket {endpoint}",
                            True,
                            "Connection established"
                        )
                        return True
                    except asyncio.TimeoutError:
                        self.log_result(
                            f"WebSocket {endpoint}",
                            False,
                            "No response received"
                        )
                        
            except Exception as e:
                # Continue trying other endpoints
                continue
                
        self.log_result("WebSocket Connection", False, "No working endpoint found")
        return False
        
    async def test_api_endpoints(self) -> Dict[str, bool]:
        """Test various API endpoints"""
        endpoints = {
            "/docs": "API Documentation",
            "/openapi.json": "OpenAPI Spec",
            "/api/v2/orchestrator/status": "Orchestrator Status",
            "/api/v2/agents/list": "Agent List",
            "/api/v2/metrics": "Metrics Endpoint",
            "/api/teams": "Teams Endpoint"
        }
        
        results = {}
        async with httpx.AsyncClient() as client:
            for endpoint, name in endpoints.items():
                try:
                    response = await client.get(f"{API_BASE_URL}{endpoint}")
                    success = response.status_code in [200, 401, 403]  # Auth errors are OK
                    self.log_result(
                        f"API Endpoint: {name}",
                        success,
                        f"Status: {response.status_code}"
                    )
                    results[endpoint] = success
                except Exception as e:
                    self.log_result(f"API Endpoint: {name}", False, "Connection failed")
                    results[endpoint] = False
                    
        return results
        
    async def test_authentication_flow(self) -> bool:
        """Test authentication endpoints if available"""
        try:
            async with httpx.AsyncClient() as client:
                # Try to access protected endpoint
                response = await client.get(f"{API_BASE_URL}/api/v2/protected")
                
                if response.status_code == 401:
                    self.log_result(
                        "Authentication System",
                        True,
                        "Protected endpoints require auth"
                    )
                    return True
                elif response.status_code == 404:
                    self.log_result(
                        "Authentication System",
                        False,
                        "Not implemented yet"
                    )
                    return False
                else:
                    self.log_result(
                        "Authentication System",
                        False,
                        "Unexpected response"
                    )
                    return False
        except Exception as e:
            self.log_result("Authentication System", False, str(e))
            return False
            
    async def test_data_persistence(self) -> bool:
        """Test if data persistence layer is working"""
        try:
            async with httpx.AsyncClient() as client:
                # Try to create test data
                test_data = {
                    "test_id": f"test_{int(time.time())}",
                    "data": "Integration test data"
                }
                
                # Attempt to store data
                response = await client.post(
                    f"{API_BASE_URL}/api/v2/data",
                    json=test_data
                )
                
                if response.status_code in [200, 201]:
                    self.log_result("Data Persistence", True, "Write successful")
                    return True
                elif response.status_code == 404:
                    self.log_result(
                        "Data Persistence",
                        False,
                        "Endpoint not implemented"
                    )
                    return False
                else:
                    self.log_result(
                        "Data Persistence",
                        False,
                        f"Status: {response.status_code}"
                    )
                    return False
        except Exception as e:
            self.log_result("Data Persistence", False, "Not available")
            return False
            
    def generate_report(self):
        """Generate final test report"""
        self.print_header("TEST RESULTS SUMMARY")
        
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n{fg('white')}Total Tests: {total}")
        print(f"{fg('green')}Passed: {self.passed}")
        print(f"{fg('red')}Failed: {self.failed}")
        print(f"{fg('cyan')}Success Rate: {success_rate:.1f}%{attr('reset')}")
        
        if self.failed > 0:
            print(f"\n{fg('yellow')}⚠️  Failed Tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['test']}")
                    if result["details"]:
                        print(f"    {result['details']}")
            print(attr('reset'))
            
        # Save detailed report
        report_file = f"integration_test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total,
                    "passed": self.passed,
                    "failed": self.failed,
                    "success_rate": success_rate
                },
                "results": self.results
            }, f, indent=2)
            
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return success_rate >= 70  # Consider test suite passed if 70%+ tests pass
        
    async def run_all_tests(self):
        """Execute all integration tests"""
        print(f"{fg('magenta')}🚀 AI Orchestra Dashboard Integration Test Suite")
        print(f"   Testing: {API_BASE_URL} | {FRONTEND_URL}{attr('reset')}")
        
        self.print_header("CONNECTIVITY TESTS")
        await self.test_backend_health()
        await self.test_frontend_availability()
        await self.test_cors_configuration()
        
        self.print_header("WEBSOCKET TESTS")
        await self.test_websocket_connection()
        
        self.print_header("API ENDPOINT TESTS")
        await self.test_api_endpoints()
        
        self.print_header("AUTHENTICATION TESTS")
        await self.test_authentication_flow()
        
        self.print_header("DATA LAYER TESTS")
        await self.test_data_persistence()
        
        # Generate final report
        success = self.generate_report()
        
        if success:
            print(f"\n{fg('green')}✅ Integration tests completed successfully!{attr('reset')}")
        else:
            print(f"\n{fg('red')}❌ Integration tests completed with failures.{attr('reset')}")
            print(f"{fg('yellow')}   Review the upgrade plan for implementation priorities.{attr('reset')}")
            
        return success


async def main():
    """Main test execution"""
    tester = IntegrationTester()
    success = await tester.run_all_tests()
    
    # Provide recommendations based on results
    print(f"\n{fg('cyan')}📋 RECOMMENDATIONS:{attr('reset')}")
    
    if tester.failed > 0:
        print(f"{fg('yellow')}Priority fixes needed:")
        print("1. Implement WebSocket endpoint for real-time communication")
        print("2. Add OpenAPI documentation for API discovery")
        print("3. Create authentication system for security")
        print("4. Implement data persistence layer")
        print("5. Add more API endpoints for full functionality")
        print(f"\nRefer to AI_ORCHESTRA_UPGRADE_PLAN.md for detailed implementation guide.{attr('reset')}")
    else:
        print(f"{fg('green')}System is working well! Consider implementing advanced features:")
        print("1. Enhanced monitoring dashboard")
        print("2. Agent management interface")
        print("3. Analytics and cost tracking")
        print("4. Multi-tenant support{attr('reset')}")
        
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{fg('yellow')}Test suite interrupted by user.{attr('reset')}")
        exit(1)
    except Exception as e:
        print(f"\n{fg('red')}Test suite failed: {e}{attr('reset')}")
        exit(1)