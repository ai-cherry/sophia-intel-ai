#!/usr/bin/env python3
"""Integration tests for all swarm systems."""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
import aiohttp
from datetime import datetime

class SwarmIntegrationTester:
    """Test all swarm endpoints and MCP servers."""
    
    def __init__(self):
        self.api_base = "http://localhost:8003"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "api_tests": {},
            "mcp_tests": {},
            "swarm_tests": {},
            "quality_metrics": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }
        
    async def test_api_endpoints(self):
        """Test all API endpoints."""
        print("\n🔍 Testing API Endpoints...")
        
        endpoints = {
            "health": "/healthz",
            "teams": "/teams",
            "workflows": "/workflows",
            "search": "/search",
            "memory_stats": "/memory/stats",
            "memory_index": "/memory/index",
            "mcp_filesystem": "/mcp/filesystem/list",
            "mcp_git": "/mcp/git/status"
        }
        
        async with aiohttp.ClientSession() as session:
            for name, endpoint in endpoints.items():
                try:
                    async with session.get(f"{self.api_base}{endpoint}") as resp:
                        status = resp.status
                        if status == 200:
                            data = await resp.json()
                            self.results["api_tests"][name] = {
                                "status": "passed",
                                "code": status,
                                "response": str(data)[:100] + "..." if data else None
                            }
                            print(f"  ✅ {name}: {status}")
                        else:
                            self.results["api_tests"][name] = {
                                "status": "failed",
                                "code": status
                            }
                            print(f"  ❌ {name}: {status}")
                except Exception as e:
                    self.results["api_tests"][name] = {
                        "status": "error",
                        "error": str(e)
                    }
                    print(f"  ❌ {name}: Error - {e}")
                    
    async def test_team_endpoint(self):
        """Test team creation and execution."""
        print("\n🔍 Testing Team Endpoint...")
        
        test_cases = [
            {
                "name": "simple_task",
                "payload": {
                    "problem": "Write a Python function to reverse a string",
                    "config": {
                        "team_size": 3,
                        "max_rounds": 1
                    }
                }
            },
            {
                "name": "complex_task",
                "payload": {
                    "problem": "Design a REST API for a todo application with CRUD operations",
                    "config": {
                        "team_size": 5,
                        "max_rounds": 2,
                        "quality_threshold": 0.8
                    }
                }
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            for test in test_cases:
                try:
                    async with session.post(
                        f"{self.api_base}/teams",
                        json=test["payload"]
                    ) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            self.results["swarm_tests"][test["name"]] = {
                                "status": "passed",
                                "response_time": result.get("duration", 0),
                                "agents_used": result.get("agents_used", 0)
                            }
                            print(f"  ✅ {test['name']}: Success")
                        else:
                            self.results["swarm_tests"][test["name"]] = {
                                "status": "failed",
                                "code": resp.status
                            }
                            print(f"  ❌ {test['name']}: Failed ({resp.status})")
                except Exception as e:
                    self.results["swarm_tests"][test["name"]] = {
                        "status": "error",
                        "error": str(e)
                    }
                    print(f"  ❌ {test['name']}: Error - {e}")
                    
    async def test_mcp_operations(self):
        """Test MCP server operations."""
        print("\n🔍 Testing MCP Operations...")
        
        operations = [
            {
                "name": "filesystem_read",
                "method": "POST",
                "endpoint": "/mcp/filesystem/read",
                "payload": {"path": "README.md"}
            },
            {
                "name": "git_status",
                "method": "GET",
                "endpoint": "/mcp/git/status",
                "payload": None
            },
            {
                "name": "memory_add",
                "method": "POST",
                "endpoint": "/memory/add",
                "payload": {
                    "content": "Test memory entry",
                    "metadata": {"type": "test", "timestamp": datetime.now().isoformat()}
                }
            },
            {
                "name": "memory_search",
                "method": "POST",
                "endpoint": "/memory/search",
                "payload": {"query": "test", "top_k": 5}
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            for op in operations:
                try:
                    if op["method"] == "GET":
                        async with session.get(f"{self.api_base}{op['endpoint']}") as resp:
                            status = resp.status
                    else:
                        async with session.post(
                            f"{self.api_base}{op['endpoint']}",
                            json=op["payload"]
                        ) as resp:
                            status = resp.status
                            
                    if status == 200:
                        self.results["mcp_tests"][op["name"]] = {"status": "passed"}
                        print(f"  ✅ {op['name']}: Success")
                    else:
                        self.results["mcp_tests"][op["name"]] = {
                            "status": "failed",
                            "code": status
                        }
                        print(f"  ❌ {op['name']}: Failed ({status})")
                except Exception as e:
                    self.results["mcp_tests"][op["name"]] = {
                        "status": "error",
                        "error": str(e)
                    }
                    print(f"  ❌ {op['name']}: Error - {e}")
                    
    async def test_workflow_endpoint(self):
        """Test workflow execution endpoint."""
        print("\n🔍 Testing Workflow Endpoint...")
        
        workflow = {
            "steps": [
                {
                    "type": "analyze",
                    "input": "Analyze Python code for security issues"
                },
                {
                    "type": "generate",
                    "input": "Generate security recommendations"
                },
                {
                    "type": "validate",
                    "input": "Validate recommendations"
                }
            ],
            "config": {
                "parallel": False,
                "timeout": 30
            }
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.api_base}/workflows",
                    json=workflow
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        self.results["swarm_tests"]["workflow"] = {
                            "status": "passed",
                            "steps_completed": len(result.get("results", [])),
                            "total_duration": result.get("duration", 0)
                        }
                        print(f"  ✅ Workflow: Success ({len(result.get('results', []))} steps)")
                    else:
                        self.results["swarm_tests"]["workflow"] = {
                            "status": "failed",
                            "code": resp.status
                        }
                        print(f"  ❌ Workflow: Failed ({resp.status})")
            except Exception as e:
                self.results["swarm_tests"]["workflow"] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"  ❌ Workflow: Error - {e}")
                
    def analyze_code_quality(self):
        """Analyze code quality and architecture."""
        print("\n🔬 Code Quality Analysis...")
        
        # Check key files exist
        critical_files = [
            "app/api/unified_server.py",
            "app/swarms/improved_swarm.py",
            "app/swarms/unified_enhanced_orchestrator.py",
            "app/tools/live_tools.py",
            "app/config/local_dev_config.py",
            "swarm_config.json"
        ]
        
        files_present = []
        files_missing = []
        
        for file in critical_files:
            path = Path(file)
            if path.exists():
                files_present.append(file)
            else:
                files_missing.append(file)
                
        self.results["quality_metrics"]["files"] = {
            "present": len(files_present),
            "missing": len(files_missing),
            "missing_files": files_missing
        }
        
        # Analyze patterns implementation
        patterns = [
            "Adversarial Debate",
            "Quality Gates",
            "Strategy Archive",
            "Safety Boundaries",
            "Dynamic Role Assignment",
            "Consensus with Tie-Breaking",
            "Adaptive Parameters",
            "Knowledge Transfer"
        ]
        
        improved_swarm_path = Path("app/swarms/improved_swarm.py")
        if improved_swarm_path.exists():
            content = improved_swarm_path.read_text()
            implemented_patterns = []
            
            pattern_checks = {
                "Adversarial Debate": "adversarial_debate",
                "Quality Gates": "quality_gates",
                "Strategy Archive": "strategy_archive",
                "Safety Boundaries": "safety_boundaries",
                "Dynamic Role Assignment": "dynamic_role_assignment",
                "Consensus with Tie-Breaking": "consensus_mechanism",
                "Adaptive Parameters": "adaptive_parameters",
                "Knowledge Transfer": "knowledge_transfer"
            }
            
            for pattern_name, pattern_code in pattern_checks.items():
                if pattern_code in content:
                    implemented_patterns.append(pattern_name)
                    
            self.results["quality_metrics"]["patterns"] = {
                "total": len(patterns),
                "implemented": len(implemented_patterns),
                "patterns": implemented_patterns
            }
            print(f"  ✅ Patterns implemented: {len(implemented_patterns)}/{len(patterns)}")
        else:
            print(f"  ❌ Improved swarm file not found")
            
        # Check configuration
        config_path = Path("swarm_config.json")
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
                
            config_sections = [
                "quality_gates",
                "safety_config",
                "role_assignment",
                "consensus_config",
                "adaptive_parameters",
                "knowledge_transfer"
            ]
            
            present_sections = [s for s in config_sections if s in config]
            self.results["quality_metrics"]["configuration"] = {
                "sections_present": len(present_sections),
                "sections_total": len(config_sections),
                "sections": present_sections
            }
            print(f"  ✅ Config sections: {len(present_sections)}/{len(config_sections)}")
            
    def calculate_summary(self):
        """Calculate test summary statistics."""
        total = 0
        passed = 0
        
        for category in ["api_tests", "mcp_tests", "swarm_tests"]:
            for test_name, result in self.results.get(category, {}).items():
                total += 1
                if result.get("status") == "passed":
                    passed += 1
                    
        self.results["summary"]["total"] = total
        self.results["summary"]["passed"] = passed
        self.results["summary"]["failed"] = total - passed
        
        return passed, total
        
    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "="*60)
        print("📊 SWARM SYSTEM TEST REPORT")
        print("="*60)
        
        passed, total = self.calculate_summary()
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n✅ Tests Passed: {passed}/{total} ({pass_rate:.1f}%)")
        
        # API Endpoints
        print("\n📡 API Endpoints:")
        api_passed = sum(1 for r in self.results["api_tests"].values() if r.get("status") == "passed")
        api_total = len(self.results["api_tests"])
        print(f"  • Status: {api_passed}/{api_total} endpoints working")
        
        # MCP Servers
        print("\n🔌 MCP Servers:")
        mcp_passed = sum(1 for r in self.results["mcp_tests"].values() if r.get("status") == "passed")
        mcp_total = len(self.results["mcp_tests"])
        print(f"  • Status: {mcp_passed}/{mcp_total} operations successful")
        
        # Swarm Operations
        print("\n🐝 Swarm Operations:")
        swarm_passed = sum(1 for r in self.results["swarm_tests"].values() if r.get("status") == "passed")
        swarm_total = len(self.results["swarm_tests"])
        print(f"  • Status: {swarm_passed}/{swarm_total} swarm tests passed")
        
        # Code Quality
        if "quality_metrics" in self.results:
            print("\n📂 Code Quality:")
            metrics = self.results["quality_metrics"]
            
            if "files" in metrics:
                print(f"  • Critical files: {metrics['files']['present']}/{metrics['files']['present'] + metrics['files']['missing']} present")
                
            if "patterns" in metrics:
                print(f"  • Enhancement patterns: {metrics['patterns']['implemented']}/{metrics['patterns']['total']} implemented")
                
            if "configuration" in metrics:
                print(f"  • Config sections: {metrics['configuration']['sections_present']}/{metrics['configuration']['sections_total']} configured")
                
        # Overall Assessment
        print("\n🎯 Overall Assessment:")
        if pass_rate >= 90:
            print("  ✅ System is FULLY OPERATIONAL and ready for use")
        elif pass_rate >= 70:
            print("  ⚠️  System is MOSTLY OPERATIONAL with some issues")
        else:
            print("  ❌ System has CRITICAL ISSUES requiring attention")
            
        # Save report
        report_path = Path("tests/integration_report.json")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)
            
        print(f"\n📁 Full report saved to: {report_path}")
        
        return pass_rate >= 90
        
    async def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "="*60)
        print("🚀 SWARM INTEGRATION TESTING")
        print("="*60)
        
        # Check server is running
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/healthz") as resp:
                    if resp.status != 200:
                        print("❌ Server not responding. Please ensure it's running on port 8003")
                        return False
        except:
            print("❌ Cannot connect to server on port 8003")
            return False
            
        # Run tests
        await self.test_api_endpoints()
        await self.test_mcp_operations()
        await self.test_team_endpoint()
        await self.test_workflow_endpoint()
        
        # Analyze code
        self.analyze_code_quality()
        
        # Generate report
        all_good = self.generate_report()
        
        print("\n✨ Testing complete!")
        return all_good
        

async def main():
    """Main test runner."""
    tester = SwarmIntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 All systems operational! Ready to push to GitHub.")
    else:
        print("\n⚠️  Some issues detected. Review report before pushing.")
        
    return success
    

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)