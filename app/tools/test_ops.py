from agno import Tool
import subprocess
from pathlib import Path
from typing import Optional

class RunTests(Tool):
    """Tool for running tests."""
    
    name = "run_tests"
    description = "Run tests for the project"
    parameters = {
        "type": "object",
        "properties": {
            "test_path": {
                "type": "string",
                "description": "Path to specific test file or directory",
                "default": "tests"
            },
            "verbose": {
                "type": "boolean",
                "description": "Run tests in verbose mode",
                "default": False
            }
        },
        "required": []
    }
    
    async def run(self, test_path: str = "tests", verbose: bool = False) -> str:
        """Run tests using pytest."""
        try:
            # Check if pytest is available
            pytest_check = subprocess.run(
                ["python", "-m", "pytest", "--version"],
                capture_output=True,
                text=True
            )
            
            if pytest_check.returncode != 0:
                return "pytest is not installed. Install it with: pip install pytest"
            
            # Run tests
            cmd = ["python", "-m", "pytest", test_path]
            if verbose:
                cmd.append("-v")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\n\nErrors:\n{result.stderr}"
            
            return f"Test results:\n{output}"
        except Exception as e:
            return f"Error running tests: {str(e)}"


class RunTypeCheck(Tool):
    """Tool for running type checking."""
    
    name = "run_typecheck"
    description = "Run type checking for the project"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to check",
                "default": "app"
            }
        },
        "required": []
    }
    
    async def run(self, path: str = "app") -> str:
        """Run type checking using mypy."""
        try:
            # Check if mypy is available
            mypy_check = subprocess.run(
                ["python", "-m", "mypy", "--version"],
                capture_output=True,
                text=True
            )
            
            if mypy_check.returncode != 0:
                return "mypy is not installed. Install it with: pip install mypy"
            
            # Run type checking
            result = subprocess.run(
                ["python", "-m", "mypy", path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return f"Type checking passed for {path}"
            
            return f"Type checking results:\n{result.stdout}"
        except Exception as e:
            return f"Error running type check: {str(e)}"