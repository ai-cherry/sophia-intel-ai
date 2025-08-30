from agno import Tool
import subprocess
from typing import Optional

class RunLint(Tool):
    """Tool for running linting on the codebase."""
    
    name = "run_lint"
    description = "Run linting checks on the codebase"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to lint",
                "default": "app"
            },
            "fix": {
                "type": "boolean",
                "description": "Automatically fix issues where possible",
                "default": False
            }
        },
        "required": []
    }
    
    async def run(self, path: str = "app", fix: bool = False) -> str:
        """Run linting using ruff."""
        try:
            # Check if ruff is available
            ruff_check = subprocess.run(
                ["python", "-m", "ruff", "--version"],
                capture_output=True,
                text=True
            )
            
            if ruff_check.returncode != 0:
                # Try with flake8 as fallback
                return await self._run_flake8(path)
            
            # Run ruff
            cmd = ["python", "-m", "ruff", "check", path]
            if fix:
                cmd.append("--fix")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return f"Linting passed for {path}"
            
            return f"Linting results:\n{result.stdout}"
        except Exception as e:
            return f"Error running lint: {str(e)}"
    
    async def _run_flake8(self, path: str) -> str:
        """Fallback to flake8 if ruff is not available."""
        try:
            flake8_check = subprocess.run(
                ["python", "-m", "flake8", "--version"],
                capture_output=True,
                text=True
            )
            
            if flake8_check.returncode != 0:
                return "No linter installed. Install ruff or flake8: pip install ruff"
            
            result = subprocess.run(
                ["python", "-m", "flake8", path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return f"Linting passed for {path}"
            
            return f"Linting results:\n{result.stdout}"
        except Exception as e:
            return f"Error running flake8: {str(e)}"


class FormatCode(Tool):
    """Tool for formatting code."""
    
    name = "format_code"
    description = "Format code using black"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to format",
                "default": "app"
            },
            "check": {
                "type": "boolean",
                "description": "Only check, don't modify files",
                "default": False
            }
        },
        "required": []
    }
    
    async def run(self, path: str = "app", check: bool = False) -> str:
        """Format code using black."""
        try:
            # Check if black is available
            black_check = subprocess.run(
                ["python", "-m", "black", "--version"],
                capture_output=True,
                text=True
            )
            
            if black_check.returncode != 0:
                return "black is not installed. Install it with: pip install black"
            
            # Run black
            cmd = ["python", "-m", "black", path]
            if check:
                cmd.append("--check")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                if check:
                    return f"Code formatting is correct for {path}"
                return f"Successfully formatted {path}"
            
            return f"Formatting results:\n{result.stdout}"
        except Exception as e:
            return f"Error formatting code: {str(e)}"