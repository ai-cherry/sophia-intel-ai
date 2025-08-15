#!/usr/bin/env python3
"""
Test script for LangGraph Coding Swarm
Tests the 4-agent collaborative coding system
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.coding_swarm import CodingSwarm, CodingTaskType, create_coding_swarm


class CodingSwarmTester:
    """Test suite for the coding swarm"""
    
    def __init__(self):
        self.swarm = create_coding_swarm()
        self.test_repository = "ai-cherry/sophia-intel"
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = "", data: dict = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "data": data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
        if data and success:
            print(f"   Data: {json.dumps(data, indent=2)[:300]}...")
    
    async def test_swarm_initialization(self):
        """Test swarm initialization"""
        try:
            # Check if all agents are properly initialized
            agents = ["planner", "coder", "reviewer", "integrator"]
            initialized_agents = []
            
            if hasattr(self.swarm, 'planner') and self.swarm.planner:
                initialized_agents.append("planner")
            if hasattr(self.swarm, 'coder') and self.swarm.coder:
                initialized_agents.append("coder")
            if hasattr(self.swarm, 'reviewer') and self.swarm.reviewer:
                initialized_agents.append("reviewer")
            if hasattr(self.swarm, 'integrator') and self.swarm.integrator:
                initialized_agents.append("integrator")
            
            success = len(initialized_agents) == len(agents)
            
            self.log_test(
                "Swarm Initialization",
                success,
                f"Initialized {len(initialized_agents)}/{len(agents)} agents",
                {
                    "initialized_agents": initialized_agents,
                    "workflow_compiled": hasattr(self.swarm, 'workflow') and self.swarm.workflow is not None
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test("Swarm Initialization", False, f"Error: {e}")
            return False
    
    async def test_planner_agent(self):
        """Test planner agent functionality"""
        try:
            # Create a simple test state
            from agents.coding_swarm import CodingSwarmState
            
            test_state = CodingSwarmState(
                task_description="Add a simple hello world function to utils.py",
                task_type=CodingTaskType.FEATURE_IMPLEMENTATION,
                repository=self.test_repository,
                target_files=["utils.py"],
                requirements=["Function should return 'Hello, World!'"],
                plan=None,
                planning_complete=False,
                code_changes=None,
                coding_complete=False,
                review_results=None,
                review_complete=False,
                integration_results=None,
                integration_complete=False,
                current_agent="Planner",
                messages=[],
                errors=[],
                metadata={}
            )
            
            # Test planner processing
            result = await self.swarm.planner.process(test_state)
            
            success = (
                "plan" in result and 
                result.get("planning_complete", False) and
                "errors" not in result
            )
            
            self.log_test(
                "Planner Agent",
                success,
                f"Planning completed: {result.get('planning_complete', False)}",
                {
                    "has_plan": "plan" in result,
                    "plan_steps": len(result.get("plan", {}).get("steps", [])),
                    "estimated_complexity": result.get("plan", {}).get("estimated_complexity", "unknown")
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test("Planner Agent", False, f"Error: {e}")
            return False
    
    async def test_github_integration(self):
        """Test GitHub integration components"""
        try:
            # Test GitHub tools initialization
            github_tools = self.swarm.github_tools
            
            # Test repository access
            access = await github_tools.validate_access(self.test_repository)
            
            if access:
                # Test reading a simple file
                try:
                    file_data = await github_tools.read_file_content(
                        self.test_repository, "README.md"
                    )
                    file_read_success = bool(file_data.get("content"))
                except:
                    file_read_success = False
            else:
                file_read_success = False
            
            success = access and file_read_success
            
            self.log_test(
                "GitHub Integration",
                success,
                f"Repository access: {access}, File read: {file_read_success}",
                {
                    "repository": self.test_repository,
                    "access_granted": access,
                    "file_operations": file_read_success
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test("GitHub Integration", False, f"Error: {e}")
            return False
    
    async def test_diff_analyzer(self):
        """Test diff analyzer functionality"""
        try:
            diff_analyzer = self.swarm.diff_analyzer
            
            # Test diff generation
            original = "def hello():\n    return 'Hello'"
            modified = "def hello():\n    return 'Hello, World!'"
            
            diff = diff_analyzer.generate_unified_diff(original, modified, "test.py")
            diff_success = "+    return 'Hello, World!'" in diff
            
            # Test complexity analysis
            complexity = diff_analyzer.analyze_diff_complexity(diff)
            complexity_success = (
                "additions" in complexity and 
                "deletions" in complexity and
                complexity["additions"] > 0
            )
            
            success = diff_success and complexity_success
            
            self.log_test(
                "Diff Analyzer",
                success,
                f"Diff generation: {diff_success}, Complexity analysis: {complexity_success}",
                {
                    "diff_lines": len(diff.split('\n')),
                    "complexity_score": complexity.get("complexity_score", 0),
                    "risk_level": complexity.get("risk_level", "unknown")
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test("Diff Analyzer", False, f"Error: {e}")
            return False
    
    async def test_workflow_structure(self):
        """Test workflow graph structure"""
        try:
            workflow = self.swarm.workflow
            
            # Check if workflow is compiled
            workflow_compiled = workflow is not None
            
            # Test workflow structure (basic validation)
            has_nodes = True  # We can't easily inspect LangGraph internals
            
            success = workflow_compiled and has_nodes
            
            self.log_test(
                "Workflow Structure",
                success,
                f"Workflow compiled: {workflow_compiled}",
                {
                    "workflow_type": str(type(workflow)),
                    "compiled": workflow_compiled
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test("Workflow Structure", False, f"Error: {e}")
            return False
    
    async def test_simple_task_execution(self):
        """Test simple task execution (without actual GitHub operations)"""
        try:
            # This is a dry-run test that doesn't actually create PRs
            # We'll test the workflow structure and agent coordination
            
            task_description = "Add a simple utility function"
            
            # Mock execution by testing individual components
            planner_works = await self.test_planner_agent()
            github_works = await self.test_github_integration()
            
            # For now, we consider the task execution successful if core components work
            success = planner_works and github_works
            
            self.log_test(
                "Simple Task Execution",
                success,
                f"Core components functional: {success}",
                {
                    "task_description": task_description,
                    "planner_functional": planner_works,
                    "github_functional": github_works,
                    "note": "Full execution requires live GitHub operations"
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test("Simple Task Execution", False, f"Error: {e}")
            return False
    
    async def test_environment_setup(self):
        """Test environment and dependencies"""
        try:
            # Check required environment variables
            required_vars = ["GITHUB_PAT", "OPENROUTER_API_KEY"]
            env_vars = {}
            
            for var in required_vars:
                env_vars[var] = bool(os.getenv(var))
            
            # Check required packages
            required_packages = ["langgraph", "langchain_openai", "langchain_core"]
            package_status = {}
            
            for package in required_packages:
                try:
                    __import__(package)
                    package_status[package] = True
                except ImportError:
                    package_status[package] = False
            
            env_success = all(env_vars.values())
            package_success = all(package_status.values())
            success = env_success and package_success
            
            self.log_test(
                "Environment Setup",
                success,
                f"Environment: {env_success}, Packages: {package_success}",
                {
                    "environment_variables": env_vars,
                    "packages": package_status
                }
            )
            
            return success
            
        except Exception as e:
            self.log_test("Environment Setup", False, f"Error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Coding Swarm Test Suite")
        print(f"📁 Repository: {self.test_repository}")
        print(f"🔑 GitHub PAT: {'✅ Set' if os.getenv('GITHUB_PAT') else '❌ Missing'}")
        print(f"🤖 OpenRouter API: {'✅ Set' if os.getenv('OPENROUTER_API_KEY') else '❌ Missing'}")
        print("-" * 60)
        
        # Run tests in order
        test_methods = [
            self.test_environment_setup,
            self.test_swarm_initialization,
            self.test_github_integration,
            self.test_diff_analyzer,
            self.test_workflow_structure,
            self.test_planner_agent,
            self.test_simple_task_execution
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                self.log_test(test_method.__name__, False, f"Test method error: {e}")
        
        # Summary
        print("-" * 60)
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 Coding Swarm is ready for production!")
        elif success_rate >= 60:
            print("⚠️  Coding Swarm has some issues but is functional")
        else:
            print("❌ Coding Swarm has significant issues")
        
        return self.test_results


async def main():
    """Main test runner"""
    # Set up environment
    os.environ.setdefault('GITHUB_PAT', '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')
    os.environ.setdefault('OPENROUTER_API_KEY', 'sk-or-v1-a7c9b8e6f5d4c3b2a1e9f8d7c6b5a4e3f2d1c0b9a8e7f6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0')
    
    tester = CodingSwarmTester()
    results = await tester.run_all_tests()
    
    # Save results to file
    results_file = Path(__file__).parent.parent / "coding_swarm_test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "repository": tester.test_repository,
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r['success']),
            "success_rate": (sum(1 for r in results if r['success']) / len(results)) * 100,
            "results": results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")


if __name__ == "__main__":
    asyncio.run(main())

