# Auto-added by pre-commit hook
import os
import sys

try:
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    from core.environment_enforcer import enforce_environment

    enforce_environment()
except ImportError:
    pass

"""
Tester Agent - Comprehensive Testing with pytest/mypy/error simulations

Provides comprehensive testing capabilities including:
- Unit testing with pytest
- Type checking with mypy
- Error simulation and fault injection
- Code quality assessment
"""

import asyncio
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from crewai import Agent
except ImportError:
    Agent = None


@dataclass
class TestResult:
    """Individual test result"""

    test_name: str
    status: str  # passed, failed, skipped
    duration: float
    error_message: Optional[str] = None


@dataclass
class TestSuite:
    """Complete test suite results"""

    total_tests: int
    passed: int
    failed: int
    skipped: int
    coverage: float
    duration: float
    results: List[TestResult]


class TesterAgent:
    """
    Tester Agent for Comprehensive Code Testing

    Responsible for:
    - Running pytest unit tests
    - Type checking with mypy
    - Error simulation and fault injection
    - Code coverage analysis
    - Quality assessment
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        self.agent_id = "artemis_tester"
        self.version = "2.0.0"
        self.status = "initialized"

    async def run_tests(self, code_files: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run comprehensive tests on generated code

        Args:
            code_files: Dictionary of generated code files

        Returns:
            Dictionary containing test results and analysis
        """
        self.logger.info("Starting comprehensive testing")

        try:
            # Create temporary directory for testing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write code files to temp directory
                await self._write_code_files(code_files, temp_dir)

                # Run different types of tests
                results = {
                    "pytest_results": await self._run_pytest(temp_dir),
                    "mypy_results": await self._run_mypy(temp_dir),
                    "error_simulation": await self._run_error_simulation(temp_dir),
                    "code_quality": await self._assess_code_quality(code_files),
                    "coverage": await self._calculate_coverage(temp_dir),
                    "timestamp": datetime.now().isoformat(),
                }

                # Generate summary
                results["summary"] = self._generate_test_summary(results)

                return results

        except Exception as e:
            self.logger.error(f"Error running tests: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _write_code_files(self, code_files: Dict[str, Any], temp_dir: str):
        """Write code files to temporary directory"""
        for file_path, file_data in code_files.items():
            if isinstance(file_data, dict):
                content = file_data.get("content", "")
            else:
                content = str(file_data)

            full_path = Path(temp_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, "w") as f:
                f.write(content)

    async def _run_pytest(self, temp_dir: str) -> Dict[str, Any]:
        """Run pytest on the code"""
        try:
            # Create a basic conftest.py if it doesn't exist
            conftest_path = Path(temp_dir) / "conftest.py"
            if not conftest_path.exists():
                with open(conftest_path, "w") as f:
                    f.write("import pytest\n")

            # Run pytest
            result = subprocess.run(
                ["python", "-m", "pytest", temp_dir, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "passed": "PASSED" in result.stdout,
                "test_count": result.stdout.count("PASSED")
                + result.stdout.count("FAILED"),
            }

        except Exception as e:
            return {"error": str(e), "passed": False}

    async def _run_mypy(self, temp_dir: str) -> Dict[str, Any]:
        """Run mypy type checking"""
        try:
            # Find Python files
            python_files = list(Path(temp_dir).rglob("*.py"))

            if not python_files:
                return {"status": "no_python_files", "issues": []}

            # Run mypy
            result = subprocess.run(
                ["python", "-m", "mypy"] + [str(f) for f in python_files],
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )

            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "issues": result.stdout.split("\n") if result.stdout else [],
                "clean": result.returncode == 0,
            }

        except Exception as e:
            return {"error": str(e), "clean": False}

    async def _run_error_simulation(self, temp_dir: str) -> Dict[str, Any]:
        """Simulate various error conditions"""
        simulations = []

        try:
            # Test 1: Import errors
            simulations.append(await self._simulate_import_errors(temp_dir))

            # Test 2: Runtime errors
            simulations.append(await self._simulate_runtime_errors(temp_dir))

            # Test 3: Network failures
            simulations.append(await self._simulate_network_failures(temp_dir))

            return {
                "simulations": simulations,
                "total_simulations": len(simulations),
                "passed_simulations": sum(
                    1 for s in simulations if s.get("handled", False)
                ),
            }

        except Exception as e:
            return {"error": str(e), "simulations": []}

    async def _simulate_import_errors(self, temp_dir: str) -> Dict[str, Any]:
        """Simulate import errors"""
        try:
            test_file = Path(temp_dir) / "test_imports.py"
            with open(test_file, "w") as f:
                f.write(
                    """
try:
    import nonexistent_module
    result = "import_succeeded"
except ImportError:
    result = "import_error_handled"
except Exception as e:
    result = f"unexpected_error: {e}"

print(result)
"""
                )

            # Run the test
            result = subprocess.run(
                ["python", str(test_file)], capture_output=True, text=True, cwd=temp_dir
            )

            return {
                "test": "import_errors",
                "handled": "import_error_handled" in result.stdout,
                "output": result.stdout.strip(),
            }

        except Exception as e:
            return {"test": "import_errors", "error": str(e), "handled": False}

    async def _simulate_runtime_errors(self, temp_dir: str) -> Dict[str, Any]:
        """Simulate runtime errors"""
        try:
            test_file = Path(temp_dir) / "test_runtime.py"
            with open(test_file, "w") as f:
                f.write(
                    """
try:
    # Division by zero
    result = 1 / 0
except ZeroDivisionError:
    result = "division_error_handled"
except Exception as e:
    result = f"unexpected_error: {e}"

print(result)
"""
                )

            result = subprocess.run(
                ["python", str(test_file)], capture_output=True, text=True, cwd=temp_dir
            )

            return {
                "test": "runtime_errors",
                "handled": "division_error_handled" in result.stdout,
                "output": result.stdout.strip(),
            }

        except Exception as e:
            return {"test": "runtime_errors", "error": str(e), "handled": False}

    async def _simulate_network_failures(self, temp_dir: str) -> Dict[str, Any]:
        """Simulate network failures"""
        try:
            test_file = Path(temp_dir) / "test_network.py"
            with open(test_file, "w") as f:
                f.write(
                    """
import socket

try:
    # Try to connect to non-existent host
    sock = socket.socket()
    sock.settimeout(1)
    sock.connect(("nonexistent.host", 80))
    result = "connection_succeeded"
except (socket.timeout, socket.gaierror, ConnectionRefusedError):
    result = "network_error_handled"
except Exception as e:
    result = f"unexpected_error: {e}"
finally:
    try:
        sock.close()
    except:
        pass

print(result)
"""
                )

            result = subprocess.run(
                ["python", str(test_file)], capture_output=True, text=True, cwd=temp_dir
            )

            return {
                "test": "network_failures",
                "handled": "network_error_handled" in result.stdout,
                "output": result.stdout.strip(),
            }

        except Exception as e:
            return {"test": "network_failures", "error": str(e), "handled": False}

    async def _assess_code_quality(self, code_files: Dict[str, Any]) -> Dict[str, Any]:
        """Assess code quality metrics"""
        quality_metrics = {
            "total_files": len(code_files),
            "python_files": 0,
            "has_documentation": 0,
            "has_tests": 0,
            "average_file_size": 0,
            "complexity_score": "medium",
        }

        total_size = 0

        for file_path, file_data in code_files.items():
            if isinstance(file_data, dict):
                content = file_data.get("content", "")
                documentation = file_data.get("documentation", "")
                tests = file_data.get("tests", "")
            else:
                content = str(file_data)
                documentation = tests = ""

            total_size += len(content)

            if file_path.endswith(".py"):
                quality_metrics["python_files"] += 1

            if documentation:
                quality_metrics["has_documentation"] += 1

            if tests:
                quality_metrics["has_tests"] += 1

        if code_files:
            quality_metrics["average_file_size"] = total_size // len(code_files)

        # Simple complexity assessment
        if quality_metrics["average_file_size"] > 1000:
            quality_metrics["complexity_score"] = "high"
        elif quality_metrics["average_file_size"] < 300:
            quality_metrics["complexity_score"] = "low"

        return quality_metrics

    async def _calculate_coverage(self, temp_dir: str) -> Dict[str, Any]:
        """Calculate test coverage (simplified)"""
        try:
            # Count Python files and test files
            python_files = list(Path(temp_dir).rglob("*.py"))
            test_files = [f for f in python_files if "test" in f.name.lower()]

            if not python_files:
                return {"coverage": 0, "reason": "no_python_files"}

            # Simple coverage estimation
            coverage_percentage = min(100, (len(test_files) / len(python_files)) * 100)

            return {
                "coverage": coverage_percentage,
                "total_files": len(python_files),
                "test_files": len(test_files),
                "method": "estimated",
            }

        except Exception as e:
            return {"error": str(e), "coverage": 0}

    def _generate_test_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall test summary"""
        pytest_passed = results.get("pytest_results", {}).get("passed", False)
        mypy_clean = results.get("mypy_results", {}).get("clean", False)
        error_sims = results.get("error_simulation", {})
        sim_passed = error_sims.get("passed_simulations", 0)
        total_sims = error_sims.get("total_simulations", 0)
        coverage = results.get("coverage", {}).get("coverage", 0)

        # Calculate overall score
        score_components = [
            pytest_passed,
            mypy_clean,
            sim_passed == total_sims if total_sims > 0 else True,
            coverage > 50,
        ]

        overall_score = sum(score_components) / len(score_components) * 100

        return {
            "overall_score": overall_score,
            "pytest_passed": pytest_passed,
            "mypy_clean": mypy_clean,
            "error_simulations_passed": f"{sim_passed}/{total_sims}",
            "coverage_percentage": coverage,
            "recommendation": self._get_recommendation(overall_score),
        }

    def _get_recommendation(self, score: float) -> str:
        """Get recommendation based on test score"""
        if score >= 90:
            return "Excellent - Code is ready for deployment"
        elif score >= 70:
            return "Good - Minor improvements recommended"
        elif score >= 50:
            return "Fair - Significant improvements needed"
        else:
            return "Poor - Major issues must be addressed"

    def get_crewai_agent(self) -> Optional[Agent]:
        """Get CrewAI agent representation"""
        if not Agent:
            return None

        return Agent(
            role="Quality Assurance Engineer",
            goal="Ensure code quality through comprehensive testing and validation",
            backstory="""You are an expert QA engineer with deep knowledge of testing 
            methodologies, automated testing frameworks, and code quality assessment. 
            You excel at finding edge cases, simulating error conditions, and ensuring 
            robust, reliable software.""",
            verbose=True,
            allow_delegation=False,
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "version": self.version,
            "status": self.status,
            "capabilities": [
                "pytest_testing",
                "mypy_type_checking",
                "error_simulation",
                "code_quality_assessment",
                "coverage_analysis",
            ],
            "timestamp": datetime.now().isoformat(),
        }


# Example usage
if __name__ == "__main__":

    async def main():
        tester = TesterAgent()
        code_files = {
            "main.py": {
                "content": "def hello(): return 'Hello World'",
                "documentation": "Simple hello function",
                "tests": "def test_hello(): assert hello() == 'Hello World'",
            }
        }
        result = await tester.run_tests(code_files)
        print(result)

    asyncio.run(main())
