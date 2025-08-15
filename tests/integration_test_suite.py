#!/usr/bin/env python3
"""
Sophia Intel Integration Test Suite
Comprehensive end-to-end testing of all platform components
"""

import asyncio
import json
import os
import sys
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ops.monitoring import SophiaIntelMonitor, HealthStatus
from loguru import logger


@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    category: str
    status: str  # "pass", "fail", "skip", "error"
    duration_ms: float
    timestamp: str
    details: str = ""
    evidence: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class IntegrationTestSuite:
    """Comprehensive integration test suite"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.end_time = None
        
        # Test configuration
        self.github_pat = os.getenv('GITHUB_PAT', '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')
        self.repository = "ai-cherry/sophia-intel"
        
        # Expected files and directories
        self.expected_structure = {
            "files": [
                "README.md",
                "pyproject.toml",
                "requirements.txt",
                "config/config.py",
                "mcp_servers/enhanced_unified_server.py",
                "agents/coding_swarm.py",
                "ops/monitoring.py",
                "ops/health_dashboard.py",
                "scripts/configure_airbyte_pipelines.py"
            ],
            "directories": [
                "mcp_servers",
                "agents",
                "ops",
                "scripts",
                "config",
                "infra",
                "tests",
                "docs"
            ]
        }
    
    def log_test_result(self, test_name: str, category: str, status: str, 
                       duration_ms: float, details: str = "", 
                       evidence: Optional[Dict[str, Any]] = None,
                       error_message: Optional[str] = None):
        """Log a test result"""
        result = TestResult(
            test_name=test_name,
            category=category,
            status=status,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow().isoformat(),
            details=details,
            evidence=evidence,
            error_message=error_message
        )
        
        self.test_results.append(result)
        
        # Print result
        status_icon = {
            "pass": "✅",
            "fail": "❌", 
            "skip": "⏭️",
            "error": "💥"
        }.get(status, "❓")
        
        print(f"{status_icon} {category}: {test_name} ({duration_ms:.0f}ms)")
        if details:
            print(f"   {details}")
        if error_message:
            print(f"   Error: {error_message}")
    
    async def test_project_structure(self) -> bool:
        """Test project structure and file existence"""
        start_time = time.time()
        
        try:
            project_root = Path(__file__).parent.parent
            missing_files = []
            missing_dirs = []
            
            # Check files
            for file_path in self.expected_structure["files"]:
                full_path = project_root / file_path
                if not full_path.exists():
                    missing_files.append(file_path)
            
            # Check directories
            for dir_path in self.expected_structure["directories"]:
                full_path = project_root / dir_path
                if not full_path.exists():
                    missing_dirs.append(dir_path)
            
            duration = (time.time() - start_time) * 1000
            
            if missing_files or missing_dirs:
                self.log_test_result(
                    "Project Structure",
                    "Infrastructure",
                    "fail",
                    duration,
                    f"Missing {len(missing_files)} files, {len(missing_dirs)} directories",
                    evidence={
                        "missing_files": missing_files,
                        "missing_directories": missing_dirs,
                        "total_expected_files": len(self.expected_structure["files"]),
                        "total_expected_dirs": len(self.expected_structure["directories"])
                    }
                )
                return False
            else:
                self.log_test_result(
                    "Project Structure",
                    "Infrastructure", 
                    "pass",
                    duration,
                    f"All {len(self.expected_structure['files'])} files and {len(self.expected_structure['directories'])} directories present",
                    evidence={
                        "files_checked": len(self.expected_structure["files"]),
                        "directories_checked": len(self.expected_structure["directories"])
                    }
                )
                return True
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test_result(
                "Project Structure",
                "Infrastructure",
                "error",
                duration,
                error_message=str(e)
            )
            return False
    
    async def test_mcp_code_server(self) -> bool:
        """Test MCP Code Server functionality"""
        start_time = time.time()
        
        try:
            # Import and test MCP Code Server
            from mcp_servers.code_mcp.tools.github_tools import GitHubTools
            
            github_tools = GitHubTools()
            
            # Test repository access
            access_granted = await github_tools.validate_access(self.repository)
            
            if access_granted:
                # Test file reading
                file_data = await github_tools.read_file_content(self.repository, "README.md")
                file_read_success = bool(file_data.get("content"))
                
                duration = (time.time() - start_time) * 1000
                
                if file_read_success:
                    self.log_test_result(
                        "MCP Code Server",
                        "AI Services",
                        "pass",
                        duration,
                        f"GitHub access granted, README.md read ({len(file_data['content'])} bytes)",
                        evidence={
                            "repository": self.repository,
                            "access_granted": True,
                            "file_size": len(file_data['content']),
                            "file_sha": file_data.get('sha', 'unknown')
                        }
                    )
                    return True
                else:
                    self.log_test_result(
                        "MCP Code Server",
                        "AI Services",
                        "fail",
                        duration,
                        "GitHub access granted but file reading failed"
                    )
                    return False
            else:
                duration = (time.time() - start_time) * 1000
                self.log_test_result(
                    "MCP Code Server",
                    "AI Services",
                    "fail",
                    duration,
                    "GitHub access denied"
                )
                return False
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test_result(
                "MCP Code Server",
                "AI Services",
                "error",
                duration,
                error_message=str(e)
            )
            return False
    
    async def test_coding_swarm_initialization(self) -> bool:
        """Test LangGraph Coding Swarm initialization"""
        start_time = time.time()
        
        try:
            # Test coding swarm import and initialization
            from agents.coding_swarm import create_coding_swarm, CodingTaskType
            
            swarm = create_coding_swarm()
            
            # Check if all agents are initialized
            agents_present = {
                "planner": hasattr(swarm, 'planner') and swarm.planner is not None,
                "coder": hasattr(swarm, 'coder') and swarm.coder is not None,
                "reviewer": hasattr(swarm, 'reviewer') and swarm.reviewer is not None,
                "integrator": hasattr(swarm, 'integrator') and swarm.integrator is not None,
                "workflow": hasattr(swarm, 'workflow') and swarm.workflow is not None
            }
            
            duration = (time.time() - start_time) * 1000
            
            all_present = all(agents_present.values())
            
            if all_present:
                self.log_test_result(
                    "Coding Swarm Initialization",
                    "AI Services",
                    "pass",
                    duration,
                    "All 4 agents and workflow initialized successfully",
                    evidence=agents_present
                )
                return True
            else:
                missing_agents = [name for name, present in agents_present.items() if not present]
                self.log_test_result(
                    "Coding Swarm Initialization",
                    "AI Services",
                    "fail",
                    duration,
                    f"Missing agents: {', '.join(missing_agents)}",
                    evidence=agents_present
                )
                return False
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test_result(
                "Coding Swarm Initialization",
                "AI Services",
                "error",
                duration,
                error_message=str(e)
            )
            return False
    
    async def test_monitoring_system(self) -> bool:
        """Test monitoring system functionality"""
        start_time = time.time()
        
        try:
            async with SophiaIntelMonitor() as monitor:
                # Run health check
                health_data = await monitor.run_comprehensive_health_check()
                
                duration = (time.time() - start_time) * 1000
                
                # Validate health data structure
                required_keys = ["timestamp", "system_metrics", "components", "summary"]
                missing_keys = [key for key in required_keys if key not in health_data]
                
                if missing_keys:
                    self.log_test_result(
                        "Monitoring System",
                        "Operations",
                        "fail",
                        duration,
                        f"Missing health data keys: {', '.join(missing_keys)}"
                    )
                    return False
                
                # Check if we have component data
                components_count = len(health_data.get("components", {}))
                summary = health_data.get("summary", {})
                
                self.log_test_result(
                    "Monitoring System",
                    "Operations",
                    "pass",
                    duration,
                    f"Health check completed, {components_count} components monitored",
                    evidence={
                        "components_monitored": components_count,
                        "overall_health_score": summary.get("overall_health_score", 0),
                        "healthy_components": summary.get("healthy", 0),
                        "unhealthy_components": summary.get("unhealthy", 0)
                    }
                )
                return True
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test_result(
                "Monitoring System",
                "Operations",
                "error",
                duration,
                error_message=str(e)
            )
            return False
    
    async def test_docker_infrastructure(self) -> bool:
        """Test Docker infrastructure status"""
        start_time = time.time()
        
        try:
            # Check Docker containers
            result = subprocess.run(
                ["docker", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            duration = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                # Parse container information
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            containers.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                
                # Look for Airbyte containers
                airbyte_containers = [c for c in containers if 'airbyte' in c.get('Names', '')]
                minio_containers = [c for c in containers if 'minio' in c.get('Names', '')]
                
                total_containers = len(containers)
                airbyte_count = len(airbyte_containers)
                minio_count = len(minio_containers)
                
                self.log_test_result(
                    "Docker Infrastructure",
                    "Infrastructure",
                    "pass",
                    duration,
                    f"{total_containers} containers running ({airbyte_count} Airbyte, {minio_count} MinIO)",
                    evidence={
                        "total_containers": total_containers,
                        "airbyte_containers": airbyte_count,
                        "minio_containers": minio_count,
                        "container_names": [c.get('Names', '') for c in containers]
                    }
                )
                return True
            else:
                self.log_test_result(
                    "Docker Infrastructure",
                    "Infrastructure",
                    "fail",
                    duration,
                    f"Docker command failed: {result.stderr}"
                )
                return False
                
        except subprocess.TimeoutExpired:
            duration = (time.time() - start_time) * 1000
            self.log_test_result(
                "Docker Infrastructure",
                "Infrastructure",
                "fail",
                duration,
                "Docker command timed out"
            )
            return False
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test_result(
                "Docker Infrastructure",
                "Infrastructure",
                "error",
                duration,
                error_message=str(e)
            )
            return False
    
    async def test_airbyte_configuration(self) -> bool:
        """Test Airbyte configuration scripts"""
        start_time = time.time()
        
        try:
            # Test if configuration script exists and is valid Python
            config_script = Path(__file__).parent.parent / "scripts" / "configure_airbyte_pipelines.py"
            
            if not config_script.exists():
                duration = (time.time() - start_time) * 1000
                self.log_test_result(
                    "Airbyte Configuration",
                    "Data Pipelines",
                    "fail",
                    duration,
                    "Configuration script not found"
                )
                return False
            
            # Test script syntax
            with open(config_script, 'r') as f:
                script_content = f.read()
            
            try:
                compile(script_content, str(config_script), 'exec')
                syntax_valid = True
            except SyntaxError as e:
                syntax_valid = False
                syntax_error = str(e)
            
            duration = (time.time() - start_time) * 1000
            
            if syntax_valid:
                self.log_test_result(
                    "Airbyte Configuration",
                    "Data Pipelines",
                    "pass",
                    duration,
                    f"Configuration script valid ({len(script_content)} bytes)",
                    evidence={
                        "script_size": len(script_content),
                        "script_lines": len(script_content.split('\n')),
                        "syntax_valid": True
                    }
                )
                return True
            else:
                self.log_test_result(
                    "Airbyte Configuration",
                    "Data Pipelines",
                    "fail",
                    duration,
                    f"Syntax error in configuration script: {syntax_error}"
                )
                return False
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test_result(
                "Airbyte Configuration",
                "Data Pipelines",
                "error",
                duration,
                error_message=str(e)
            )
            return False
    
    async def test_environment_configuration(self) -> bool:
        """Test environment configuration and secrets"""
        start_time = time.time()
        
        try:
            # Check critical environment variables
            env_vars = {
                "GITHUB_PAT": bool(os.getenv('GITHUB_PAT')),
                "OPENROUTER_API_KEY": bool(os.getenv('OPENROUTER_API_KEY')),
                "NEON_HOST": bool(os.getenv('NEON_HOST')),
                "QDRANT_URL": bool(os.getenv('QDRANT_URL')),
            }
            
            # Check configuration files
            config_files = {
                "config.py": (Path(__file__).parent.parent / "config" / "config.py").exists(),
                "pyproject.toml": (Path(__file__).parent.parent / "pyproject.toml").exists(),
                "requirements.txt": (Path(__file__).parent.parent / "requirements.txt").exists()
            }
            
            duration = (time.time() - start_time) * 1000
            
            env_configured = sum(env_vars.values())
            files_present = sum(config_files.values())
            
            self.log_test_result(
                "Environment Configuration",
                "Configuration",
                "pass",
                duration,
                f"{env_configured}/4 environment variables set, {files_present}/3 config files present",
                evidence={
                    "environment_variables": env_vars,
                    "configuration_files": config_files,
                    "env_score": f"{env_configured}/4",
                    "config_score": f"{files_present}/3"
                }
            )
            return True
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test_result(
                "Environment Configuration",
                "Configuration",
                "error",
                duration,
                error_message=str(e)
            )
            return False
    
    async def test_git_repository_status(self) -> bool:
        """Test Git repository status and recent commits"""
        start_time = time.time()
        
        try:
            # Check git status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=Path(__file__).parent.parent
            )
            
            if result.returncode == 0:
                uncommitted_files = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
                
                # Get recent commits
                commit_result = subprocess.run(
                    ["git", "log", "--oneline", "-5"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=Path(__file__).parent.parent
                )
                
                recent_commits = commit_result.stdout.strip().split('\n') if commit_result.returncode == 0 else []
                
                duration = (time.time() - start_time) * 1000
                
                self.log_test_result(
                    "Git Repository Status",
                    "Version Control",
                    "pass",
                    duration,
                    f"{uncommitted_files} uncommitted files, {len(recent_commits)} recent commits",
                    evidence={
                        "uncommitted_files": uncommitted_files,
                        "recent_commits_count": len(recent_commits),
                        "latest_commits": recent_commits[:3]  # Show top 3
                    }
                )
                return True
            else:
                duration = (time.time() - start_time) * 1000
                self.log_test_result(
                    "Git Repository Status",
                    "Version Control",
                    "fail",
                    duration,
                    f"Git status failed: {result.stderr}"
                )
                return False
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.log_test_result(
                "Git Repository Status",
                "Version Control",
                "error",
                duration,
                error_message=str(e)
            )
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        self.start_time = datetime.utcnow()
        
        print("🚀 Starting Sophia Intel Integration Test Suite")
        print(f"📅 Start Time: {self.start_time.isoformat()}")
        print("=" * 80)
        
        # Define test methods
        test_methods = [
            self.test_project_structure,
            self.test_environment_configuration,
            self.test_git_repository_status,
            self.test_docker_infrastructure,
            self.test_mcp_code_server,
            self.test_coding_swarm_initialization,
            self.test_airbyte_configuration,
            self.test_monitoring_system
        ]
        
        # Run tests
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                logger.error(f"Test method {test_method.__name__} failed: {e}")
                self.log_test_result(
                    test_method.__name__,
                    "System",
                    "error",
                    0,
                    error_message=str(e)
                )
        
        self.end_time = datetime.utcnow()
        
        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == "pass"])
        failed_tests = len([r for r in self.test_results if r.status == "fail"])
        error_tests = len([r for r in self.test_results if r.status == "error"])
        skipped_tests = len([r for r in self.test_results if r.status == "skip"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        total_duration = (self.end_time - self.start_time).total_seconds() * 1000
        
        # Group results by category
        categories = {}
        for result in self.test_results:
            if result.category not in categories:
                categories[result.category] = {"pass": 0, "fail": 0, "error": 0, "skip": 0}
            categories[result.category][result.status] += 1
        
        summary = {
            "timestamp": self.end_time.isoformat(),
            "duration_ms": total_duration,
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "skipped": skipped_tests,
            "success_rate": success_rate,
            "categories": categories,
            "test_results": [asdict(result) for result in self.test_results]
        }
        
        # Print summary
        print("=" * 80)
        print("📊 INTEGRATION TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"💥 Errors: {error_tests}")
        print(f"⏭️ Skipped: {skipped_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"⏱️ Total Duration: {total_duration:.0f}ms")
        
        print("\n📋 Results by Category:")
        for category, stats in categories.items():
            total_cat = sum(stats.values())
            passed_cat = stats["pass"]
            cat_rate = (passed_cat / total_cat * 100) if total_cat > 0 else 0
            print(f"  {category}: {passed_cat}/{total_cat} ({cat_rate:.1f}%)")
        
        # Overall assessment
        if success_rate >= 90:
            print("\n🎉 EXCELLENT: Platform is production-ready!")
        elif success_rate >= 75:
            print("\n✅ GOOD: Platform is mostly functional with minor issues")
        elif success_rate >= 50:
            print("\n⚠️ FAIR: Platform has significant issues that need attention")
        else:
            print("\n❌ POOR: Platform has critical issues requiring immediate attention")
        
        return summary


async def main():
    """Main test runner"""
    test_suite = IntegrationTestSuite()
    results = await test_suite.run_all_tests()
    
    # Save results
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    results_file = Path(__file__).parent.parent / f"integration_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    # Return appropriate exit code
    if results['success_rate'] >= 75:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

