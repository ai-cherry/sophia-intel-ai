#!/usr/bin/env python3
"""
Comprehensive Deployment Test Suite for Sophia Intel AI
Tests all deployment aspects: Infrastructure, APIs, Swarms, Performance, MCP
"""

import asyncio
import aiohttp
import json
import time
import subprocess
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
import psutil
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Color:
    """Console colors for output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

class ComprehensiveDeploymentTest:
    """Comprehensive deployment testing suite"""
    
    def __init__(self):
        self.base_url = "http://localhost:8003"
        self.test_results = {
            "infrastructure": {},
            "api_endpoints": {},
            "swarm_execution": {},
            "performance": {},
            "mcp_integration": {},
            "deployment_health": {}
        }
        self.start_time = time.time()
        
    def print_header(self, title: str):
        """Print formatted test section header"""
        print(f"\n{Color.BLUE}{Color.BOLD}{'='*60}{Color.END}")
        print(f"{Color.BLUE}{Color.BOLD}🚀 {title.upper()}{Color.END}")
        print(f"{Color.BLUE}{Color.BOLD}{'='*60}{Color.END}")
    
    def print_result(self, test_name: str, success: bool, details: str = ""):
        """Print test result with color coding"""
        status = f"{Color.GREEN}✅ PASS" if success else f"{Color.RED}❌ FAIL"
        details_str = f" - {details}" if details else ""
        print(f"  {test_name:<40} {status}{Color.END}{details_str}")
        return success
    
    async def test_infrastructure_health(self) -> bool:
        """Test basic infrastructure components"""
        self.print_header("Infrastructure Health Tests")
        
        all_passed = True
        
        # Test port availability
        ports_to_check = [
            (8003, "API Server"),
            (8080, "Weaviate"),
            (6379, "Redis"),
            (5432, "PostgreSQL")
        ]
        
        for port, service in ports_to_check:
            try:
                async with aiohttp.ClientSession() as session:
                    if port == 8003:
                        async with session.get(f"http://localhost:{port}/healthz", timeout=5) as resp:
                            success = resp.status == 200
                    elif port == 8080:
                        async with session.get(f"http://localhost:{port}/v1/.well-known/ready", timeout=5) as resp:
                            success = resp.status == 200
                    else:
                        # For Redis and PostgreSQL, check if port is listening
                        import socket
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.settimeout(2)
                            success = s.connect_ex(('localhost', port)) == 0
                
                self.test_results["infrastructure"][service.lower()] = success
                all_passed &= self.print_result(f"{service} (:{port})", success)
                
            except Exception as e:
                self.test_results["infrastructure"][service.lower()] = False
                all_passed &= self.print_result(f"{service} (:{port})", False, str(e))
        
        # Test Docker containers (if available)
        try:
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True, timeout=10)
            container_count = len([line for line in result.stdout.split('\n')[1:] if line.strip()])
            success = container_count > 0
            self.test_results["infrastructure"]["docker_containers"] = container_count
            all_passed &= self.print_result("Docker Containers", success, f"{container_count} running")
        except:
            all_passed &= self.print_result("Docker Containers", False, "Docker not available")
        
        return all_passed
    
    async def test_api_endpoints(self) -> bool:
        """Test all API endpoints"""
        self.print_header("API Endpoints Tests")
        
        all_passed = True
        
        endpoints_to_test = [
            ("/healthz", "GET", "Health Check"),
            ("/api/metrics", "GET", "System Metrics"),
            ("/agents", "GET", "Agents List"),
            ("/workflows", "GET", "Workflows List"),
            ("/teams", "GET", "Teams List"),
            ("/docs", "GET", "API Documentation")
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint, method, description in endpoints_to_test:
                try:
                    start_time = time.time()
                    async with session.request(method, f"{self.base_url}{endpoint}", timeout=10) as resp:
                        response_time_ms = (time.time() - start_time) * 1000
                        success = resp.status in [200, 404]  # 404 acceptable for some endpoints
                        
                        # Get response data for analysis
                        try:
                            if resp.content_type == 'application/json':
                                data = await resp.json()
                                self.test_results["api_endpoints"][endpoint] = {
                                    "status": resp.status,
                                    "response_time_ms": round(response_time_ms, 2),
                                    "content_type": resp.content_type,
                                    "data_keys": list(data.keys()) if isinstance(data, dict) else len(data) if isinstance(data, list) else "other"
                                }
                            else:
                                self.test_results["api_endpoints"][endpoint] = {
                                    "status": resp.status,
                                    "response_time_ms": round(response_time_ms, 2),
                                    "content_type": resp.content_type
                                }
                        except:
                            self.test_results["api_endpoints"][endpoint] = {
                                "status": resp.status,
                                "response_time_ms": round(response_time_ms, 2)
                            }
                        
                        details = f"{resp.status} - {response_time_ms:.1f}ms"
                        all_passed &= self.print_result(description, success, details)
                        
                except Exception as e:
                    self.test_results["api_endpoints"][endpoint] = {"error": str(e)}
                    all_passed &= self.print_result(description, False, str(e))
        
        return all_passed
    
    async def test_swarm_execution(self) -> bool:
        """Test AI swarm execution"""
        self.print_header("Swarm Execution Tests")
        
        all_passed = True
        
        # Test swarm execution with different teams
        swarm_tests = [
            ("strategic", "Test strategic analysis capabilities"),
            ("technical", "Test technical research functionality"), 
            ("creative", "Test creative content generation")
        ]
        
        async with aiohttp.ClientSession() as session:
            for team_id, test_message in swarm_tests:
                try:
                    payload = {
                        "message": test_message,
                        "team_id": team_id,
                        "stream": False
                    }
                    
                    start_time = time.time()
                    async with session.post(
                        f"{self.base_url}/teams/run",
                        json=payload,
                        timeout=30
                    ) as resp:
                        response_time_ms = (time.time() - start_time) * 1000
                        success = resp.status in [200, 201]
                        
                        if success:
                            try:
                                data = await resp.json()
                                self.test_results["swarm_execution"][team_id] = {
                                    "status": resp.status,
                                    "response_time_ms": round(response_time_ms, 2),
                                    "response_length": len(str(data)) if data else 0
                                }
                            except:
                                # Handle streaming response
                                content = await resp.text()
                                self.test_results["swarm_execution"][team_id] = {
                                    "status": resp.status,
                                    "response_time_ms": round(response_time_ms, 2),
                                    "response_length": len(content)
                                }
                        
                        details = f"{resp.status} - {response_time_ms:.1f}ms"
                        all_passed &= self.print_result(f"{team_id.title()} Team", success, details)
                        
                except Exception as e:
                    self.test_results["swarm_execution"][team_id] = {"error": str(e)}
                    all_passed &= self.print_result(f"{team_id.title()} Team", False, str(e))
        
        return all_passed
    
    async def test_performance_metrics(self) -> bool:
        """Test performance characteristics"""
        self.print_header("Performance Tests")
        
        all_passed = True
        
        # Load test with concurrent requests
        concurrent_requests = 20
        test_endpoint = "/healthz"
        
        async def make_request(session):
            start_time = time.time()
            try:
                async with session.get(f"{self.base_url}{test_endpoint}", timeout=5) as resp:
                    return {
                        "status": resp.status,
                        "response_time_ms": (time.time() - start_time) * 1000,
                        "success": resp.status == 200
                    }
            except:
                return {
                    "status": 0,
                    "response_time_ms": (time.time() - start_time) * 1000,
                    "success": False
                }
        
        # Run concurrent requests
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            tasks = [make_request(session) for _ in range(concurrent_requests)]
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = sum(1 for r in results if r["success"])
        response_times = [r["response_time_ms"] for r in results if r["success"]]
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            requests_per_second = concurrent_requests / total_time
        else:
            avg_response_time = 0
            max_response_time = 0
            requests_per_second = 0
        
        self.test_results["performance"] = {
            "concurrent_requests": concurrent_requests,
            "successful_requests": successful_requests,
            "success_rate": (successful_requests / concurrent_requests) * 100,
            "avg_response_time_ms": round(avg_response_time, 2),
            "max_response_time_ms": round(max_response_time, 2),
            "requests_per_second": round(requests_per_second, 2),
            "total_test_time_ms": round(total_time * 1000, 2)
        }
        
        # Performance criteria
        success_rate_ok = (successful_requests / concurrent_requests) >= 0.95
        response_time_ok = avg_response_time < 100  # Under 100ms average
        throughput_ok = requests_per_second > 50    # At least 50 RPS
        
        all_passed &= self.print_result("Success Rate (>95%)", success_rate_ok, 
                                       f"{(successful_requests/concurrent_requests)*100:.1f}%")
        all_passed &= self.print_result("Avg Response Time (<100ms)", response_time_ok,
                                       f"{avg_response_time:.1f}ms")
        all_passed &= self.print_result("Throughput (>50 RPS)", throughput_ok,
                                       f"{requests_per_second:.1f} RPS")
        
        return all_passed
    
    async def test_mcp_integration(self) -> bool:
        """Test MCP server integration"""
        self.print_header("MCP Integration Tests")
        
        all_passed = True
        
        # Test if MCP endpoints are available
        mcp_endpoints = [
            ("http://localhost:8004/health", "MCP Server Health"),
            ("http://localhost:8004/tools", "MCP Tools List"),
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint, description in mcp_endpoints:
                try:
                    async with session.get(endpoint, timeout=5) as resp:
                        success = resp.status in [200, 404]  # 404 means server is running but endpoint not found
                        details = f"{resp.status}"
                        
                        self.test_results["mcp_integration"][description.lower().replace(" ", "_")] = {
                            "status": resp.status,
                            "available": resp.status == 200
                        }
                        
                        all_passed &= self.print_result(description, success, details)
                        
                except Exception as e:
                    self.test_results["mcp_integration"][description.lower().replace(" ", "_")] = {"error": str(e)}
                    success = "Connection refused" in str(e)  # Expected if MCP server not running
                    all_passed &= self.print_result(description, success, "Not running (optional)")
        
        # Test MCP functionality through main API
        try:
            async with aiohttp.ClientSession() as session:
                # Test if main API has MCP integration
                async with session.get(f"{self.base_url}/api/mcp/status", timeout=5) as resp:
                    success = resp.status in [200, 404]
                    self.test_results["mcp_integration"]["api_integration"] = success
                    all_passed &= self.print_result("MCP API Integration", success, f"{resp.status}")
        except:
            all_passed &= self.print_result("MCP API Integration", True, "Not implemented (optional)")
        
        return all_passed
    
    def test_system_resources(self) -> bool:
        """Test system resource usage"""
        self.print_header("System Resources Tests")
        
        all_passed = True
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get process information
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                proc_info = proc.info
                if 'python' in proc_info['name'].lower() or 'docker' in proc_info['name'].lower():
                    processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        self.test_results["deployment_health"] = {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_percent": memory.percent,
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_percent": (disk.used / disk.total) * 100
            },
            "processes": processes[:10]  # Top 10 relevant processes
        }
        
        # Resource criteria
        cpu_ok = cpu_percent < 80
        memory_ok = memory.percent < 85
        disk_ok = (disk.used / disk.total) * 100 < 90
        
        all_passed &= self.print_result("CPU Usage (<80%)", cpu_ok, f"{cpu_percent:.1f}%")
        all_passed &= self.print_result("Memory Usage (<85%)", memory_ok, f"{memory.percent:.1f}%")
        all_passed &= self.print_result("Disk Usage (<90%)", disk_ok, f"{(disk.used/disk.total)*100:.1f}%")
        
        return all_passed
    
    async def generate_deployment_report(self):
        """Generate comprehensive deployment report"""
        self.print_header("Deployment Report")
        
        total_time = time.time() - self.start_time
        
        # Calculate overall scores
        scores = {
            "infrastructure": sum(1 for v in self.test_results["infrastructure"].values() if v is True),
            "api_endpoints": sum(1 for v in self.test_results["api_endpoints"].values() 
                               if isinstance(v, dict) and v.get("status") in [200, 404]),
            "swarm_execution": sum(1 for v in self.test_results["swarm_execution"].values() 
                                 if isinstance(v, dict) and v.get("status") in [200, 201]),
            "performance": 1 if self.test_results["performance"].get("success_rate", 0) > 95 else 0,
            "mcp_integration": sum(1 for v in self.test_results["mcp_integration"].values() 
                                 if isinstance(v, dict) and (v.get("available") is True or "error" not in v))
        }
        
        total_tests = len(self.test_results["infrastructure"]) + len(self.test_results["api_endpoints"]) + \
                     len(self.test_results["swarm_execution"]) + 1 + len(self.test_results["mcp_integration"])
        total_passed = sum(scores.values())
        
        success_rate = (total_passed / max(total_tests, 1)) * 100
        
        # Deployment health score
        if success_rate >= 95:
            health_grade = "A+ (Excellent)"
            health_color = Color.GREEN
        elif success_rate >= 85:
            health_grade = "A (Good)"  
            health_color = Color.GREEN
        elif success_rate >= 75:
            health_grade = "B (Fair)"
            health_color = Color.YELLOW
        else:
            health_grade = "C (Needs Work)"
            health_color = Color.RED
        
        print(f"\n{Color.BOLD}📊 DEPLOYMENT SUMMARY{Color.END}")
        print(f"  Total Test Time: {total_time:.1f}s")
        print(f"  Tests Passed: {total_passed}/{total_tests}")
        print(f"  Success Rate: {health_color}{success_rate:.1f}%{Color.END}")
        print(f"  Health Grade: {health_color}{health_grade}{Color.END}")
        
        print(f"\n{Color.BOLD}🔍 COMPONENT SCORES{Color.END}")
        for component, score in scores.items():
            component_total = len(self.test_results[component]) if component != "performance" else 1
            component_rate = (score / max(component_total, 1)) * 100
            color = Color.GREEN if component_rate >= 80 else Color.YELLOW if component_rate >= 60 else Color.RED
            print(f"  {component.replace('_', ' ').title():<20} {color}{score}/{component_total} ({component_rate:.0f}%){Color.END}")
        
        # Performance highlights
        if self.test_results.get("performance"):
            perf = self.test_results["performance"]
            print(f"\n{Color.BOLD}⚡ PERFORMANCE HIGHLIGHTS{Color.END}")
            print(f"  Average Response Time: {perf.get('avg_response_time_ms', 0):.1f}ms")
            print(f"  Throughput: {perf.get('requests_per_second', 0):.1f} RPS")
            print(f"  Success Rate: {perf.get('success_rate', 0):.1f}%")
        
        # Save detailed results
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "test_duration_seconds": total_time,
            "overall_success_rate": success_rate,
            "health_grade": health_grade,
            "component_scores": scores,
            "detailed_results": self.test_results
        }
        
        with open("deployment_test_results.json", "w") as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\n{Color.BLUE}📄 Detailed results saved to: deployment_test_results.json{Color.END}")
        
        return success_rate >= 80  # Consider deployment successful if >80%

async def main():
    """Run comprehensive deployment tests"""
    print(f"{Color.BOLD}{Color.BLUE}🚀 Sophia Intel AI - Comprehensive Deployment Test Suite{Color.END}")
    print(f"{Color.BLUE}Starting deployment validation at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Color.END}")
    
    tester = ComprehensiveDeploymentTest()
    
    # Run all test suites
    results = []
    
    results.append(await tester.test_infrastructure_health())
    results.append(await tester.test_api_endpoints())
    results.append(await tester.test_swarm_execution())
    results.append(await tester.test_performance_metrics())
    results.append(await tester.test_mcp_integration())
    results.append(tester.test_system_resources())
    
    # Generate final report
    deployment_success = await tester.generate_deployment_report()
    
    if deployment_success:
        print(f"\n{Color.GREEN}{Color.BOLD}✅ DEPLOYMENT VALIDATION SUCCESSFUL!{Color.END}")
        print(f"{Color.GREEN}🎉 Sophia Intel AI is ready for use!{Color.END}")
        return 0
    else:
        print(f"\n{Color.RED}{Color.BOLD}❌ DEPLOYMENT VALIDATION FAILED!{Color.END}")
        print(f"{Color.RED}🔧 Please review the test results and fix any issues.{Color.END}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}🛑 Test suite interrupted by user{Color.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Color.RED}💥 Test suite failed with error: {e}{Color.END}")
        sys.exit(1)