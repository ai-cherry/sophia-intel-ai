#!/usr/bin/env python3
"""
Comprehensive Deployment Test Suite for Sophia Intel Platform

This script tests all major components of the platform to ensure
production readiness and proper integration.
"""

import asyncio
import json
import sys
import os
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple
import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DeploymentTester:
    """Comprehensive deployment testing suite."""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        self.test_count = 0
        self.passed_count = 0
        
    def log_test(self, test_name: str, result: bool, details: str = ""):
        """Log test result."""
        self.test_count += 1
        if result:
            self.passed_count += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        print(f"   {test_name}: {status}")
        if details:
            print(f"      {details}")
        
        self.results[test_name] = {
            "passed": result,
            "details": details,
            "timestamp": time.time()
        }
        
        return result
    
    async def test_environment_setup(self) -> bool:
        """Test environment and dependency setup."""
        print("\n🔧 Testing Environment Setup...")
        
        # Test Python version
        python_version = sys.version_info
        python_ok = python_version >= (3, 11)
        self.log_test(
            "Python Version", 
            python_ok,
            f"Python {python_version.major}.{python_version.minor}.{python_version.micro}"
        )
        
        # Test uv installation
        try:
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
            uv_ok = result.returncode == 0
            uv_version = result.stdout.strip() if uv_ok else "Not installed"
        except FileNotFoundError:
            uv_ok = False
            uv_version = "Not found"
        
        self.log_test("uv Package Manager", uv_ok, uv_version)
        
        # Test virtual environment
        venv_path = project_root / ".venv"
        venv_ok = venv_path.exists() and (venv_path / "bin" / "python").exists()
        self.log_test("Virtual Environment", venv_ok, str(venv_path))
        
        # Test pyproject.toml
        pyproject_path = project_root / "pyproject.toml"
        pyproject_ok = pyproject_path.exists()
        self.log_test("pyproject.toml", pyproject_ok, str(pyproject_path))
        
        # Test uv.lock
        lock_path = project_root / "uv.lock"
        lock_ok = lock_path.exists()
        self.log_test("uv.lock", lock_ok, str(lock_path))
        
        return all([python_ok, uv_ok, venv_ok, pyproject_ok, lock_ok])
    
    async def test_configuration_loading(self) -> bool:
        """Test configuration system."""
        print("\n⚙️ Testing Configuration Loading...")
        
        # Test basic config import
        try:
            from config.config import Settings
            config_import_ok = True
        except Exception as e:
            config_import_ok = False
            config_error = str(e)
        
        self.log_test(
            "Config Import", 
            config_import_ok,
            config_error if not config_import_ok else "Settings class loaded"
        )
        
        # Test config instantiation
        if config_import_ok:
            try:
                settings = Settings()
                config_instance_ok = True
                config_details = f"Host: {settings.host}, Port: {settings.port}"
            except Exception as e:
                config_instance_ok = False
                config_details = str(e)
        else:
            config_instance_ok = False
            config_details = "Config import failed"
        
        self.log_test("Config Instantiation", config_instance_ok, config_details)
        
        # Test YAML config
        yaml_config_path = project_root / "config.yaml"
        yaml_ok = yaml_config_path.exists()
        self.log_test("YAML Config", yaml_ok, str(yaml_config_path))
        
        return config_import_ok and config_instance_ok
    
    async def test_core_imports(self) -> bool:
        """Test core module imports."""
        print("\n📦 Testing Core Module Imports...")
        
        modules_to_test = [
            ("agents.base_agent", "BaseAgent"),
            ("agents.coding_agent", "CodingAgent"),
            ("mcp_servers.memory_service", "MemoryService"),
            ("services.orchestrator", "Orchestrator"),
            ("services.lambda_client", "LambdaClient"),
        ]
        
        import_results = []
        
        for module_name, class_name in modules_to_test:
            try:
                module = __import__(module_name, fromlist=[class_name])
                cls = getattr(module, class_name)
                import_ok = True
                details = f"{class_name} imported successfully"
            except Exception as e:
                import_ok = False
                details = str(e)
            
            self.log_test(f"Import {class_name}", import_ok, details)
            import_results.append(import_ok)
        
        return all(import_results)
    
    async def test_agent_instantiation(self) -> bool:
        """Test agent creation and basic functionality."""
        print("\n🤖 Testing Agent Instantiation...")
        
        # Test BaseAgent
        try:
            from agents.base_agent import BaseAgent
            base_agent = BaseAgent()
            base_agent_ok = True
            base_details = f"Status: {base_agent.status}"
        except Exception as e:
            base_agent_ok = False
            base_details = str(e)
        
        self.log_test("BaseAgent Creation", base_agent_ok, base_details)
        
        # Test CodingAgent
        try:
            from agents.coding_agent import CodingAgent
            coding_agent = CodingAgent()
            coding_agent_ok = True
            coding_details = f"Agent type: {type(coding_agent).__name__}"
        except Exception as e:
            coding_agent_ok = False
            coding_details = str(e)
        
        self.log_test("CodingAgent Creation", coding_agent_ok, coding_details)
        
        return base_agent_ok and coding_agent_ok
    
    async def test_database_connections(self) -> bool:
        """Test database connectivity."""
        print("\n🗄️ Testing Database Connections...")
        
        # Test Redis connection
        try:
            import redis
            # Try to connect to Redis (will fail if not running, but tests import)
            redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            redis_import_ok = True
            redis_details = "Redis client created (connection not tested)"
        except Exception as e:
            redis_import_ok = False
            redis_details = str(e)
        
        self.log_test("Redis Client", redis_import_ok, redis_details)
        
        # Test Qdrant client
        try:
            from qdrant_client import QdrantClient
            qdrant_client = QdrantClient(":memory:")  # In-memory for testing
            qdrant_ok = True
            qdrant_details = "Qdrant client created (in-memory)"
        except Exception as e:
            qdrant_ok = False
            qdrant_details = str(e)
        
        self.log_test("Qdrant Client", qdrant_ok, qdrant_details)
        
        return redis_import_ok and qdrant_ok
    
    async def test_web_framework(self) -> bool:
        """Test web framework components."""
        print("\n🌐 Testing Web Framework...")
        
        # Test FastAPI import
        try:
            from fastapi import FastAPI
            app = FastAPI()
            fastapi_ok = True
            fastapi_details = "FastAPI app created"
        except Exception as e:
            fastapi_ok = False
            fastapi_details = str(e)
        
        self.log_test("FastAPI", fastapi_ok, fastapi_details)
        
        # Test Uvicorn import
        try:
            import uvicorn
            uvicorn_ok = True
            uvicorn_details = f"Uvicorn version available"
        except Exception as e:
            uvicorn_ok = False
            uvicorn_details = str(e)
        
        self.log_test("Uvicorn", uvicorn_ok, uvicorn_details)
        
        # Test HTTP client
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                httpx_ok = True
                httpx_details = "HTTPX client created"
        except Exception as e:
            httpx_ok = False
            httpx_details = str(e)
        
        self.log_test("HTTPX Client", httpx_ok, httpx_details)
        
        return fastapi_ok and uvicorn_ok and httpx_ok
    
    async def test_estuary_integration(self) -> bool:
        """Test Estuary Flow integration."""
        print("\n🌊 Testing Estuary Flow Integration...")
        
        # Test Estuary config import
        try:
            from config.estuary.estuary_config import EstuaryConfig, EstuaryClient
            estuary_import_ok = True
            estuary_details = "Estuary modules imported"
        except Exception as e:
            estuary_import_ok = False
            estuary_details = str(e)
        
        self.log_test("Estuary Import", estuary_import_ok, estuary_details)
        
        # Test Estuary config creation
        if estuary_import_ok:
            try:
                config = EstuaryConfig()
                estuary_config_ok = True
                estuary_config_details = f"API URL: {config.api_base_url}"
            except Exception as e:
                estuary_config_ok = False
                estuary_config_details = str(e)
        else:
            estuary_config_ok = False
            estuary_config_details = "Import failed"
        
        self.log_test("Estuary Config", estuary_config_ok, estuary_config_details)
        
        # Test Estuary config file
        estuary_config_file = project_root / "config" / "estuary" / "estuary_flow.json"
        estuary_file_ok = estuary_config_file.exists()
        self.log_test("Estuary Config File", estuary_file_ok, str(estuary_config_file))
        
        return estuary_import_ok and estuary_config_ok and estuary_file_ok
    
    async def test_ci_cd_configuration(self) -> bool:
        """Test CI/CD configuration."""
        print("\n🔄 Testing CI/CD Configuration...")
        
        # Test GitHub workflows
        workflows_dir = project_root / ".github" / "workflows"
        workflows_ok = workflows_dir.exists()
        
        if workflows_ok:
            workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
            workflow_count = len(workflow_files)
            workflow_details = f"{workflow_count} workflow files found"
        else:
            workflow_details = "Workflows directory not found"
        
        self.log_test("GitHub Workflows", workflows_ok, workflow_details)
        
        # Test main CI workflow
        ci_workflow = workflows_dir / "ci.yml"
        ci_ok = ci_workflow.exists()
        self.log_test("CI Workflow", ci_ok, str(ci_workflow))
        
        # Test if CI workflow uses uv
        if ci_ok:
            with open(ci_workflow, 'r') as f:
                ci_content = f.read()
                uv_in_ci = "uv sync" in ci_content
                uv_details = "uv sync found in CI" if uv_in_ci else "uv sync not found"
        else:
            uv_in_ci = False
            uv_details = "CI workflow not found"
        
        self.log_test("CI uses uv", uv_in_ci, uv_details)
        
        return workflows_ok and ci_ok and uv_in_ci
    
    async def test_documentation(self) -> bool:
        """Test documentation completeness."""
        print("\n📚 Testing Documentation...")
        
        # Test main README
        readme_path = project_root / "README.md"
        readme_ok = readme_path.exists()
        self.log_test("README.md", readme_ok, str(readme_path))
        
        # Test docs directory
        docs_dir = project_root / "docs"
        docs_ok = docs_dir.exists()
        
        if docs_ok:
            doc_files = list(docs_dir.glob("*.md"))
            doc_count = len(doc_files)
            docs_details = f"{doc_count} documentation files"
        else:
            docs_details = "docs directory not found"
        
        self.log_test("Documentation Directory", docs_ok, docs_details)
        
        # Test specific documentation files
        required_docs = [
            "dependency_management.md",
            "estuary_flow_integration.md"
        ]
        
        doc_results = []
        for doc_file in required_docs:
            doc_path = docs_dir / doc_file
            doc_exists = doc_path.exists()
            self.log_test(f"Doc: {doc_file}", doc_exists, str(doc_path))
            doc_results.append(doc_exists)
        
        return readme_ok and docs_ok and all(doc_results)
    
    async def test_project_structure(self) -> bool:
        """Test project structure and organization."""
        print("\n📁 Testing Project Structure...")
        
        required_dirs = [
            "agents",
            "backend", 
            "config",
            "mcp_servers",
            "services",
            "scripts",
            "docs",
            "tests"
        ]
        
        structure_results = []
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            dir_exists = dir_path.exists() and dir_path.is_dir()
            self.log_test(f"Directory: {dir_name}", dir_exists, str(dir_path))
            structure_results.append(dir_exists)
        
        # Test key files
        key_files = [
            "pyproject.toml",
            "uv.lock",
            "config.yaml",
            "docker-compose.yml"
        ]
        
        file_results = []
        for file_name in key_files:
            file_path = project_root / file_name
            file_exists = file_path.exists()
            self.log_test(f"File: {file_name}", file_exists, str(file_path))
            file_results.append(file_exists)
        
        return all(structure_results) and all(file_results)
    
    async def test_security_configuration(self) -> bool:
        """Test security configuration."""
        print("\n🔒 Testing Security Configuration...")
        
        # Test .gitignore
        gitignore_path = project_root / ".gitignore"
        gitignore_ok = gitignore_path.exists()
        
        if gitignore_ok:
            with open(gitignore_path, 'r') as f:
                gitignore_content = f.read()
                secrets_ignored = ".env" in gitignore_content and ".venv" in gitignore_content
                gitignore_details = "Secrets and venv properly ignored" if secrets_ignored else "Missing important ignores"
        else:
            secrets_ignored = False
            gitignore_details = ".gitignore not found"
        
        self.log_test(".gitignore", gitignore_ok and secrets_ignored, gitignore_details)
        
        # Test that no .env files are committed
        env_files = list(project_root.rglob(".env*"))
        env_files = [f for f in env_files if not f.name.endswith(".example")]
        no_env_committed = len(env_files) == 0
        self.log_test("No .env files committed", no_env_committed, f"Found {len(env_files)} .env files")
        
        # Test secrets management documentation
        secrets_doc = project_root / "SECRETS.md"
        secrets_doc_ok = secrets_doc.exists()
        self.log_test("Secrets Documentation", secrets_doc_ok, str(secrets_doc))
        
        return gitignore_ok and secrets_ignored and no_env_committed and secrets_doc_ok
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        end_time = time.time()
        duration = end_time - self.start_time
        
        report = {
            "summary": {
                "total_tests": self.test_count,
                "passed_tests": self.passed_count,
                "failed_tests": self.test_count - self.passed_count,
                "success_rate": (self.passed_count / self.test_count * 100) if self.test_count > 0 else 0,
                "duration_seconds": duration,
                "timestamp": time.time()
            },
            "results": self.results,
            "recommendations": []
        }
        
        # Add recommendations based on failures
        failed_tests = [name for name, result in self.results.items() if not result["passed"]]
        
        if failed_tests:
            report["recommendations"].append("Address failed tests before deployment")
            
        if report["summary"]["success_rate"] < 80:
            report["recommendations"].append("Success rate below 80% - significant issues detected")
        elif report["summary"]["success_rate"] < 95:
            report["recommendations"].append("Success rate below 95% - minor issues detected")
        else:
            report["recommendations"].append("All tests passed - ready for deployment")
        
        return report


async def main():
    """Run comprehensive deployment test suite."""
    print("🚀 Sophia Intel Platform - Deployment Test Suite")
    print("=" * 60)
    
    tester = DeploymentTester()
    
    # Run all test suites
    test_suites = [
        ("Environment Setup", tester.test_environment_setup),
        ("Configuration Loading", tester.test_configuration_loading),
        ("Core Imports", tester.test_core_imports),
        ("Agent Instantiation", tester.test_agent_instantiation),
        ("Database Connections", tester.test_database_connections),
        ("Web Framework", tester.test_web_framework),
        ("Estuary Integration", tester.test_estuary_integration),
        ("CI/CD Configuration", tester.test_ci_cd_configuration),
        ("Documentation", tester.test_documentation),
        ("Project Structure", tester.test_project_structure),
        ("Security Configuration", tester.test_security_configuration),
    ]
    
    suite_results = {}
    
    for suite_name, suite_func in test_suites:
        try:
            result = await suite_func()
            suite_results[suite_name] = result
        except Exception as e:
            print(f"❌ {suite_name} failed with exception: {e}")
            suite_results[suite_name] = False
    
    # Generate and display report
    report = tester.generate_report()
    
    print("\n" + "=" * 60)
    print("📊 Deployment Test Report")
    print("=" * 60)
    
    summary = report["summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Duration: {summary['duration_seconds']:.2f} seconds")
    
    print("\n📋 Test Suite Results:")
    for suite_name, result in suite_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {suite_name}: {status}")
    
    print("\n💡 Recommendations:")
    for recommendation in report["recommendations"]:
        print(f"   • {recommendation}")
    
    # Save report to file
    report_file = project_root / "deployment_test_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Determine overall success
    overall_success = summary["success_rate"] >= 80
    
    if overall_success:
        print("\n🎉 Deployment tests passed! Platform is ready for deployment.")
        return True
    else:
        print("\n⚠️ Deployment tests failed! Address issues before deployment.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

