#!/usr/bin/env python3
"""
SOPHIA Code Analysis MCP Server
Provides code analysis, linting, testing, and security scanning capabilities
"""
import asyncio
import json
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

from mcp.server import Server
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Result of code analysis"""
    tool: str
    status: str
    output: str
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    metrics: Dict[str, Any]

class CodeAnalysisServer:
    """MCP Server for code analysis operations"""
    
    def __init__(self):
        self.server = Server("sophia-code-analysis")
        self.setup_tools()
    
    def setup_tools(self):
        """Setup MCP tools for code analysis"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="analyze_python_code",
                    description="Analyze Python code with pylint, flake8, and mypy",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Python code to analyze"},
                            "filename": {"type": "string", "description": "Filename for context"},
                            "tools": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Analysis tools to run",
                                "default": ["pylint", "flake8", "mypy"]
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="run_python_tests",
                    description="Run Python tests with pytest",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "test_code": {"type": "string", "description": "Test code to run"},
                            "source_code": {"type": "string", "description": "Source code being tested"},
                            "test_framework": {
                                "type": "string",
                                "enum": ["pytest", "unittest"],
                                "default": "pytest"
                            }
                        },
                        "required": ["test_code"]
                    }
                ),
                Tool(
                    name="security_scan",
                    description="Scan code for security vulnerabilities",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Code to scan"},
                            "language": {
                                "type": "string",
                                "enum": ["python", "javascript", "typescript"],
                                "default": "python"
                            },
                            "scan_type": {
                                "type": "string",
                                "enum": ["basic", "comprehensive"],
                                "default": "basic"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="code_complexity_analysis",
                    description="Analyze code complexity metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Code to analyze"},
                            "language": {
                                "type": "string",
                                "enum": ["python", "javascript", "typescript"],
                                "default": "python"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="format_code",
                    description="Format code according to style guidelines",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Code to format"},
                            "language": {
                                "type": "string",
                                "enum": ["python", "javascript", "typescript"],
                                "default": "python"
                            },
                            "formatter": {
                                "type": "string",
                                "enum": ["black", "autopep8", "prettier"],
                                "default": "black"
                            }
                        },
                        "required": ["code"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "analyze_python_code":
                    result = await self._analyze_python_code(
                        arguments["code"],
                        arguments.get("filename", "temp.py"),
                        arguments.get("tools", ["pylint", "flake8", "mypy"])
                    )
                elif name == "run_python_tests":
                    result = await self._run_python_tests(
                        arguments["test_code"],
                        arguments.get("source_code", ""),
                        arguments.get("test_framework", "pytest")
                    )
                elif name == "security_scan":
                    result = await self._security_scan(
                        arguments["code"],
                        arguments.get("language", "python"),
                        arguments.get("scan_type", "basic")
                    )
                elif name == "code_complexity_analysis":
                    result = await self._code_complexity_analysis(
                        arguments["code"],
                        arguments.get("language", "python")
                    )
                elif name == "format_code":
                    result = await self._format_code(
                        arguments["code"],
                        arguments.get("language", "python"),
                        arguments.get("formatter", "black")
                    )
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
                
                return [TextContent(type="text", text=json.dumps(result.__dict__, indent=2))]
                
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _analyze_python_code(self, code: str, filename: str, tools: List[str]) -> AnalysisResult:
        """Analyze Python code with specified tools"""
        results = AnalysisResult(
            tool="python_analysis",
            status="success",
            output="",
            errors=[],
            warnings=[],
            suggestions=[],
            metrics={}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / filename
            file_path.write_text(code)
            
            for tool in tools:
                try:
                    if tool == "pylint":
                        await self._run_pylint(file_path, results)
                    elif tool == "flake8":
                        await self._run_flake8(file_path, results)
                    elif tool == "mypy":
                        await self._run_mypy(file_path, results)
                except Exception as e:
                    results.errors.append(f"{tool} error: {str(e)}")
        
        return results
    
    async def _run_pylint(self, file_path: Path, results: AnalysisResult):
        """Run pylint analysis"""
        try:
            process = await asyncio.create_subprocess_exec(
                "pylint", str(file_path), "--output-format=json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if stdout:
                pylint_output = json.loads(stdout.decode())
                for issue in pylint_output:
                    message = f"Line {issue['line']}: {issue['message']} ({issue['type']})"
                    if issue['type'] in ['error', 'fatal']:
                        results.errors.append(message)
                    elif issue['type'] == 'warning':
                        results.warnings.append(message)
                    else:
                        results.suggestions.append(message)
            
            results.output += f"Pylint completed. "
            
        except FileNotFoundError:
            results.warnings.append("Pylint not installed")
        except json.JSONDecodeError:
            results.warnings.append("Pylint output parsing failed")
    
    async def _run_flake8(self, file_path: Path, results: AnalysisResult):
        """Run flake8 analysis"""
        try:
            process = await asyncio.create_subprocess_exec(
                "flake8", str(file_path), "--format=json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if stdout:
                for line in stdout.decode().strip().split('\n'):
                    if line:
                        results.warnings.append(f"Flake8: {line}")
            
            results.output += f"Flake8 completed. "
            
        except FileNotFoundError:
            results.warnings.append("Flake8 not installed")
    
    async def _run_mypy(self, file_path: Path, results: AnalysisResult):
        """Run mypy type checking"""
        try:
            process = await asyncio.create_subprocess_exec(
                "mypy", str(file_path), "--show-error-codes",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if stdout:
                for line in stdout.decode().strip().split('\n'):
                    if line and "error:" in line:
                        results.errors.append(f"MyPy: {line}")
                    elif line and "note:" in line:
                        results.suggestions.append(f"MyPy: {line}")
            
            results.output += f"MyPy completed. "
            
        except FileNotFoundError:
            results.warnings.append("MyPy not installed")
    
    async def _run_python_tests(self, test_code: str, source_code: str, framework: str) -> AnalysisResult:
        """Run Python tests"""
        results = AnalysisResult(
            tool=f"test_{framework}",
            status="success",
            output="",
            errors=[],
            warnings=[],
            suggestions=[],
            metrics={}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write source code if provided
            if source_code:
                source_path = Path(temp_dir) / "source.py"
                source_path.write_text(source_code)
            
            # Write test code
            test_path = Path(temp_dir) / "test_code.py"
            test_path.write_text(test_code)
            
            try:
                if framework == "pytest":
                    process = await asyncio.create_subprocess_exec(
                        "pytest", str(test_path), "-v", "--tb=short",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=temp_dir
                    )
                else:  # unittest
                    process = await asyncio.create_subprocess_exec(
                        "python", "-m", "unittest", "test_code.py", "-v",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=temp_dir
                    )
                
                stdout, stderr = await process.communicate()
                
                results.output = stdout.decode() if stdout else ""
                if stderr:
                    results.errors.append(stderr.decode())
                
                # Parse test results
                if process.returncode == 0:
                    results.status = "passed"
                else:
                    results.status = "failed"
                
            except FileNotFoundError:
                results.errors.append(f"{framework} not installed")
                results.status = "error"
        
        return results
    
    async def _security_scan(self, code: str, language: str, scan_type: str) -> AnalysisResult:
        """Perform security scan on code"""
        results = AnalysisResult(
            tool="security_scan",
            status="success",
            output="",
            errors=[],
            warnings=[],
            suggestions=[],
            metrics={}
        )
        
        # Basic security patterns to check
        security_patterns = {
            "python": [
                ("eval(", "Dangerous use of eval()"),
                ("exec(", "Dangerous use of exec()"),
                ("os.system(", "Potential command injection"),
                ("subprocess.call(", "Check for command injection"),
                ("pickle.loads(", "Unsafe deserialization"),
                ("yaml.load(", "Unsafe YAML loading"),
                ("password", "Potential hardcoded password"),
                ("secret", "Potential hardcoded secret"),
                ("api_key", "Potential hardcoded API key")
            ]
        }
        
        patterns = security_patterns.get(language, [])
        
        for pattern, message in patterns:
            if pattern in code.lower():
                results.warnings.append(f"Security: {message} - found '{pattern}'")
        
        # Additional comprehensive scan for bandit (Python)
        if language == "python" and scan_type == "comprehensive":
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = Path(temp_dir) / "code.py"
                file_path.write_text(code)
                
                try:
                    process = await asyncio.create_subprocess_exec(
                        "bandit", "-f", "json", str(file_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    
                    if stdout:
                        bandit_results = json.loads(stdout.decode())
                        for issue in bandit_results.get("results", []):
                            severity = issue.get("issue_severity", "UNKNOWN")
                            message = f"Bandit {severity}: {issue.get('issue_text', 'Unknown issue')}"
                            
                            if severity in ["HIGH", "MEDIUM"]:
                                results.errors.append(message)
                            else:
                                results.warnings.append(message)
                
                except (FileNotFoundError, json.JSONDecodeError):
                    results.suggestions.append("Install bandit for comprehensive security scanning")
        
        results.output = f"Security scan completed for {language} code"
        return results
    
    async def _code_complexity_analysis(self, code: str, language: str) -> AnalysisResult:
        """Analyze code complexity"""
        results = AnalysisResult(
            tool="complexity_analysis",
            status="success",
            output="",
            errors=[],
            warnings=[],
            suggestions=[],
            metrics={}
        )
        
        # Basic complexity metrics
        lines = code.split('\n')
        results.metrics["lines_of_code"] = len([line for line in lines if line.strip()])
        results.metrics["total_lines"] = len(lines)
        results.metrics["blank_lines"] = len([line for line in lines if not line.strip()])
        
        if language == "python":
            # Count functions and classes
            results.metrics["functions"] = code.count("def ")
            results.metrics["classes"] = code.count("class ")
            
            # Estimate cyclomatic complexity (basic)
            complexity_keywords = ["if", "elif", "for", "while", "except", "and", "or"]
            complexity_score = 1  # Base complexity
            for keyword in complexity_keywords:
                complexity_score += code.count(f" {keyword} ") + code.count(f"\t{keyword} ")
            
            results.metrics["estimated_complexity"] = complexity_score
            
            # Suggestions based on metrics
            if complexity_score > 10:
                results.suggestions.append("High complexity detected - consider refactoring")
            
            if results.metrics["lines_of_code"] > 100:
                results.suggestions.append("Large function/file - consider breaking into smaller pieces")
        
        results.output = f"Complexity analysis completed for {language}"
        return results
    
    async def _format_code(self, code: str, language: str, formatter: str) -> AnalysisResult:
        """Format code using specified formatter"""
        results = AnalysisResult(
            tool=f"format_{formatter}",
            status="success",
            output="",
            errors=[],
            warnings=[],
            suggestions=[],
            metrics={}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / f"code.{language}"
            file_path.write_text(code)
            
            try:
                if formatter == "black" and language == "python":
                    process = await asyncio.create_subprocess_exec(
                        "black", "--diff", str(file_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                elif formatter == "autopep8" and language == "python":
                    process = await asyncio.create_subprocess_exec(
                        "autopep8", "--diff", str(file_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                elif formatter == "prettier" and language in ["javascript", "typescript"]:
                    process = await asyncio.create_subprocess_exec(
                        "prettier", "--diff", str(file_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                else:
                    results.errors.append(f"Formatter {formatter} not supported for {language}")
                    return results
                
                stdout, stderr = await process.communicate()
                
                if stdout:
                    results.output = stdout.decode()
                    if results.output.strip():
                        results.suggestions.append("Code formatting changes suggested")
                    else:
                        results.output = "Code is already properly formatted"
                
                if stderr:
                    results.errors.append(stderr.decode())
            
            except FileNotFoundError:
                results.errors.append(f"{formatter} not installed")
        
        return results
    
    async def run(self, host: str = "localhost", port: int = 8001):
        """Run the MCP server"""
        logger.info(f"Starting SOPHIA Code Analysis MCP Server on {host}:{port}")
        await self.server.run(host=host, port=port)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SOPHIA Code Analysis MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run server
    server = CodeAnalysisServer()
    asyncio.run(server.run(args.host, args.port))

