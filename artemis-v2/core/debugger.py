"""
Debugger Module
===============

Handles debugging, error analysis, and automated fix generation.
"""

import ast
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class BugType(Enum):
    """Types of bugs"""

    SYNTAX = "syntax"
    RUNTIME = "runtime"
    LOGIC = "logic"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MEMORY = "memory"


class BugSeverity(Enum):
    """Bug severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class BugReport:
    """Bug report model"""

    bug_type: BugType
    severity: BugSeverity
    file_path: str
    line_number: int
    description: str
    stack_trace: Optional[str] = None
    suggested_fix: Optional[str] = None
    confidence: float = 0.0


@dataclass
class DebugSession:
    """Debug session information"""

    session_id: str
    target_file: str
    breakpoints: List[int]
    watch_variables: List[str]
    step_count: int = 0
    state: Dict[str, Any] = None


class Debugger:
    """
    Main debugging engine for Artemis.
    Handles error analysis, debugging, and fix generation.
    """

    def __init__(self, llm_client=None):
        """Initialize the debugger"""
        self.llm_client = llm_client
        self.error_patterns = self._load_error_patterns()
        self.fix_strategies = self._load_fix_strategies()
        self.active_sessions = {}

    def _load_error_patterns(self) -> Dict[str, Dict]:
        """Load common error patterns for different languages"""
        return {
            "python": {
                "TypeError": {
                    "pattern": r"TypeError: (.+)",
                    "severity": BugSeverity.HIGH,
                    "common_causes": [
                        "Incorrect type passed to function",
                        "Operations between incompatible types",
                        "Missing required arguments",
                    ],
                },
                "AttributeError": {
                    "pattern": r"AttributeError: (.+)",
                    "severity": BugSeverity.HIGH,
                    "common_causes": [
                        "Accessing non-existent attribute",
                        "Typo in attribute name",
                        "Object is None",
                    ],
                },
                "IndentationError": {
                    "pattern": r"IndentationError: (.+)",
                    "severity": BugSeverity.CRITICAL,
                    "common_causes": [
                        "Inconsistent indentation",
                        "Mixed tabs and spaces",
                        "Missing indentation",
                    ],
                },
                "KeyError": {
                    "pattern": r"KeyError: (.+)",
                    "severity": BugSeverity.MEDIUM,
                    "common_causes": [
                        "Key doesn't exist in dictionary",
                        "Typo in key name",
                        "Dictionary not properly initialized",
                    ],
                },
            },
            "javascript": {
                "TypeError": {
                    "pattern": r"TypeError: (.+)",
                    "severity": BugSeverity.HIGH,
                    "common_causes": [
                        "Cannot read property of undefined",
                        "Not a function",
                        "Cannot convert undefined or null",
                    ],
                },
                "ReferenceError": {
                    "pattern": r"ReferenceError: (.+)",
                    "severity": BugSeverity.HIGH,
                    "common_causes": [
                        "Variable not defined",
                        "Typo in variable name",
                        "Variable out of scope",
                    ],
                },
                "SyntaxError": {
                    "pattern": r"SyntaxError: (.+)",
                    "severity": BugSeverity.CRITICAL,
                    "common_causes": [
                        "Missing closing bracket",
                        "Unexpected token",
                        "Invalid syntax",
                    ],
                },
            },
        }

    def _load_fix_strategies(self) -> Dict[str, List[Dict]]:
        """Load fix strategies for common bugs"""
        return {
            "TypeError": [
                {
                    "check": "type conversion",
                    "fix": "Add type conversion or validation",
                },
                {
                    "check": "null check",
                    "fix": "Add null/undefined check before operation",
                },
            ],
            "AttributeError": [
                {
                    "check": "hasattr",
                    "fix": "Use hasattr() to check attribute existence",
                },
                {
                    "check": "null check",
                    "fix": "Check if object is None before accessing",
                },
            ],
            "KeyError": [
                {"check": "get method", "fix": "Use dict.get() with default value"},
                {
                    "check": "in operator",
                    "fix": "Check key existence with 'in' operator",
                },
            ],
        }

    def analyze_error(self, error_info: Dict[str, Any]) -> BugReport:
        """
        Analyze an error and generate a bug report.

        Args:
            error_info: Error information including stack trace

        Returns:
            Detailed bug report
        """
        # Parse error information
        error_type = error_info.get("type", "Unknown")
        error_message = error_info.get("message", "")
        stack_trace = error_info.get("stack_trace", "")
        file_path = error_info.get("file", "")
        line_number = error_info.get("line", 0)

        # Determine bug type and severity
        bug_type = self._classify_bug_type(error_type, error_message)
        severity = self._assess_severity(error_type, bug_type)

        # Generate suggested fix
        suggested_fix = self._generate_fix_suggestion(
            error_type, error_message, file_path, line_number
        )

        # Calculate confidence
        confidence = self._calculate_fix_confidence(suggested_fix, error_type)

        return BugReport(
            bug_type=bug_type,
            severity=severity,
            file_path=file_path,
            line_number=line_number,
            description=f"{error_type}: {error_message}",
            stack_trace=stack_trace,
            suggested_fix=suggested_fix,
            confidence=confidence,
        )

    def debug_code(
        self, file_path: str, error: Optional[str] = None
    ) -> List[BugReport]:
        """
        Debug code and identify issues.

        Args:
            file_path: Path to the code file
            error: Optional error message

        Returns:
            List of bug reports
        """
        bugs = []

        # Read the code
        code = self._read_code(file_path)
        language = self._detect_language(file_path)

        # Static analysis
        static_bugs = self._static_analysis(code, language)
        bugs.extend(static_bugs)

        # Runtime analysis if error provided
        if error:
            error_info = self._parse_error(error, file_path)
            bug_report = self.analyze_error(error_info)
            bugs.append(bug_report)

        # Check for common issues
        common_bugs = self._check_common_issues(code, language)
        bugs.extend(common_bugs)

        return bugs

    def generate_fix(self, bug_report: BugReport) -> str:
        """
        Generate a fix for the identified bug.

        Args:
            bug_report: Bug report with details

        Returns:
            Generated fix code
        """
        # Read the problematic code
        code = self._read_code(bug_report.file_path)
        lines = code.split("\n")

        # Get the problematic line
        if 0 < bug_report.line_number <= len(lines):
            problematic_line = lines[bug_report.line_number - 1]
        else:
            problematic_line = ""

        # Generate fix based on bug type
        if bug_report.bug_type == BugType.SYNTAX:
            fix = self._fix_syntax_error(problematic_line, bug_report.description)
        elif bug_report.bug_type == BugType.RUNTIME:
            fix = self._fix_runtime_error(
                problematic_line, bug_report.description, bug_report.file_path
            )
        elif bug_report.bug_type == BugType.LOGIC:
            fix = self._fix_logic_error(code, bug_report)
        elif bug_report.bug_type == BugType.PERFORMANCE:
            fix = self._optimize_performance(problematic_line)
        else:
            fix = self._fix_security_issue(problematic_line, bug_report)

        return fix

    def start_debug_session(
        self, file_path: str, breakpoints: List[int] = None
    ) -> DebugSession:
        """
        Start an interactive debug session.

        Args:
            file_path: File to debug
            breakpoints: List of line numbers for breakpoints

        Returns:
            Debug session object
        """
        import uuid

        session_id = str(uuid.uuid4())

        session = DebugSession(
            session_id=session_id,
            target_file=file_path,
            breakpoints=breakpoints or [],
            watch_variables=[],
            state={},
        )

        self.active_sessions[session_id] = session
        return session

    def step_through(self, session_id: str, step_type: str = "next") -> Dict[str, Any]:
        """
        Step through code in debug session.

        Args:
            session_id: Debug session ID
            step_type: Type of step (next, into, over, out)

        Returns:
            Current execution state
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        session.step_count += 1

        # Simulate stepping through code
        state = {
            "line": session.step_count,
            "variables": self._get_variables_at_line(
                session.target_file, session.step_count
            ),
            "stack": self._get_call_stack(session),
        }

        session.state = state
        return state

    def add_breakpoint(self, session_id: str, line_number: int) -> bool:
        """Add a breakpoint to debug session"""
        session = self.active_sessions.get(session_id)
        if session:
            if line_number not in session.breakpoints:
                session.breakpoints.append(line_number)
            return True
        return False

    def watch_variable(self, session_id: str, variable_name: str) -> bool:
        """Add a variable to watch list"""
        session = self.active_sessions.get(session_id)
        if session:
            if variable_name not in session.watch_variables:
                session.watch_variables.append(variable_name)
            return True
        return False

    def _classify_bug_type(self, error_type: str, error_message: str) -> BugType:
        """Classify the type of bug"""
        error_lower = error_type.lower()

        if "syntax" in error_lower or "indent" in error_lower:
            return BugType.SYNTAX
        elif (
            "type" in error_lower or "attribute" in error_lower or "key" in error_lower
        ):
            return BugType.RUNTIME
        elif "memory" in error_lower or "overflow" in error_lower:
            return BugType.MEMORY
        elif "security" in error_lower or "injection" in error_lower:
            return BugType.SECURITY
        elif "performance" in error_lower or "timeout" in error_lower:
            return BugType.PERFORMANCE
        else:
            return BugType.LOGIC

    def _assess_severity(self, error_type: str, bug_type: BugType) -> BugSeverity:
        """Assess the severity of a bug"""
        # Critical errors
        if bug_type == BugType.SECURITY:
            return BugSeverity.CRITICAL

        # High severity
        if bug_type in [BugType.SYNTAX, BugType.MEMORY]:
            return BugSeverity.HIGH

        # Medium severity
        if bug_type == BugType.RUNTIME:
            return BugSeverity.MEDIUM

        # Low severity
        if bug_type == BugType.PERFORMANCE:
            return BugSeverity.LOW

        return BugSeverity.INFO

    def _generate_fix_suggestion(
        self, error_type: str, error_message: str, file_path: str, line_number: int
    ) -> str:
        """Generate a suggestion for fixing the error"""
        strategies = self.fix_strategies.get(error_type, [])

        if strategies:
            # Use the first applicable strategy
            strategy = strategies[0]
            return strategy.get("fix", "No fix suggestion available")

        # Generic suggestion
        return f"Review line {line_number} in {file_path} for {error_type}"

    def _calculate_fix_confidence(self, suggested_fix: str, error_type: str) -> float:
        """Calculate confidence in the suggested fix"""
        if not suggested_fix or suggested_fix == "No fix suggestion available":
            return 0.0

        # Higher confidence for known error types
        known_errors = ["TypeError", "AttributeError", "KeyError", "IndentationError"]
        if error_type in known_errors:
            return 0.85

        return 0.5

    def _read_code(self, file_path: str) -> str:
        """Read code from file"""
        try:
            with open(file_path) as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
        }

        suffix = Path(file_path).suffix
        return extensions.get(suffix, "unknown")

    def _static_analysis(self, code: str, language: str) -> List[BugReport]:
        """Perform static code analysis"""
        bugs = []

        if language == "python":
            bugs.extend(self._analyze_python_code(code))
        elif language in ["javascript", "typescript"]:
            bugs.extend(self._analyze_javascript_code(code))

        return bugs

    def _analyze_python_code(self, code: str) -> List[BugReport]:
        """Analyze Python code for issues"""
        bugs = []

        try:
            # Parse the code
            tree = ast.parse(code)

            # Check for common issues
            for node in ast.walk(tree):
                # Check for bare except
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    bugs.append(
                        BugReport(
                            bug_type=BugType.LOGIC,
                            severity=BugSeverity.MEDIUM,
                            file_path="",
                            line_number=node.lineno,
                            description="Bare except clause - catches all exceptions",
                            suggested_fix="Specify exception type to catch",
                            confidence=0.9,
                        )
                    )

                # Check for assert in production code
                if isinstance(node, ast.Assert):
                    bugs.append(
                        BugReport(
                            bug_type=BugType.LOGIC,
                            severity=BugSeverity.LOW,
                            file_path="",
                            line_number=node.lineno,
                            description="Assert statement in code - disabled in production",
                            suggested_fix="Replace with proper error handling",
                            confidence=0.7,
                        )
                    )
        except SyntaxError as e:
            bugs.append(
                BugReport(
                    bug_type=BugType.SYNTAX,
                    severity=BugSeverity.CRITICAL,
                    file_path="",
                    line_number=e.lineno or 0,
                    description=str(e),
                    suggested_fix="Fix syntax error",
                    confidence=0.95,
                )
            )

        return bugs

    def _analyze_javascript_code(self, code: str) -> List[BugReport]:
        """Analyze JavaScript code for issues"""
        bugs = []

        # Check for common JavaScript issues
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            # Check for == instead of ===
            if "==" in line and "===" not in line:
                bugs.append(
                    BugReport(
                        bug_type=BugType.LOGIC,
                        severity=BugSeverity.LOW,
                        file_path="",
                        line_number=i,
                        description="Use of == instead of ===",
                        suggested_fix="Use === for strict equality",
                        confidence=0.8,
                    )
                )

            # Check for var instead of let/const
            if line.strip().startswith("var "):
                bugs.append(
                    BugReport(
                        bug_type=BugType.LOGIC,
                        severity=BugSeverity.LOW,
                        file_path="",
                        line_number=i,
                        description="Use of var instead of let/const",
                        suggested_fix="Use let or const for variable declaration",
                        confidence=0.9,
                    )
                )

        return bugs

    def _check_common_issues(self, code: str, language: str) -> List[BugReport]:
        """Check for common coding issues"""
        bugs = []
        lines = code.split("\n")

        # Check for TODO comments
        for i, line in enumerate(lines, 1):
            if "TODO" in line or "FIXME" in line:
                bugs.append(
                    BugReport(
                        bug_type=BugType.LOGIC,
                        severity=BugSeverity.INFO,
                        file_path="",
                        line_number=i,
                        description="TODO/FIXME comment found",
                        suggested_fix="Address the TODO item",
                        confidence=1.0,
                    )
                )

        # Check for hardcoded credentials (simple check)
        for i, line in enumerate(lines, 1):
            if "password" in line.lower() and "=" in line and '"' in line:
                bugs.append(
                    BugReport(
                        bug_type=BugType.SECURITY,
                        severity=BugSeverity.CRITICAL,
                        file_path="",
                        line_number=i,
                        description="Possible hardcoded password",
                        suggested_fix="Use environment variables or secure storage",
                        confidence=0.7,
                    )
                )

        return bugs

    def _parse_error(self, error: str, file_path: str) -> Dict[str, Any]:
        """Parse error string into structured format"""
        lines = error.split("\n")

        error_info = {
            "type": "Unknown",
            "message": error,
            "file": file_path,
            "line": 0,
            "stack_trace": error,
        }

        # Try to extract error type and message
        for line in lines:
            if "Error" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    error_info["type"] = parts[0].strip()
                    error_info["message"] = parts[1].strip()
                break

        # Try to extract line number
        line_match = re.search(r"line (\d+)", error, re.IGNORECASE)
        if line_match:
            error_info["line"] = int(line_match.group(1))

        return error_info

    def _fix_syntax_error(self, line: str, error_description: str) -> str:
        """Fix syntax errors in code"""
        # Common Python syntax fixes
        if "IndentationError" in error_description:
            # Fix indentation by removing leading whitespace
            return line.lstrip()

        if "SyntaxError" in error_description:
            # Check for missing colons
            if "def " in line and not line.rstrip().endswith(":"):
                return line.rstrip() + ":"

            # Check for missing parentheses
            if "print " in line and "(" not in line:
                content = line.replace("print ", "")
                return f"print({content})"

        return line

    def _fix_runtime_error(
        self, line: str, error_description: str, file_path: str
    ) -> str:
        """Fix runtime errors"""
        if "TypeError" in error_description:
            # Add type checking
            return f"# Add type checking\nif value is not None:\n    {line}"

        if "AttributeError" in error_description:
            # Add hasattr check
            return f"# Check attribute existence\nif hasattr(obj, 'attribute'):\n    {line}"

        if "KeyError" in error_description:
            # Use dict.get()
            if "[" in line and "]" in line:
                return line.replace("[", ".get(").replace("]", ", None)")

        return line

    def _fix_logic_error(self, code: str, bug_report: BugReport) -> str:
        """Fix logic errors in code"""
        # This would use more sophisticated analysis
        return f"# Logic fix needed at line {bug_report.line_number}"

    def _optimize_performance(self, line: str) -> str:
        """Optimize code for performance"""
        # Simple optimization examples
        if "append" in line and "for" in line:
            return "# Consider using list comprehension for better performance"

        if "+=" in line and "str" in line:
            return "# Consider using join() for string concatenation"

        return line

    def _fix_security_issue(self, line: str, bug_report: BugReport) -> str:
        """Fix security issues in code"""
        if "password" in line.lower():
            return "# Use environment variable: os.environ.get('PASSWORD')"

        if "eval(" in line:
            return "# Avoid eval() - use ast.literal_eval() or json.loads()"

        return line

    def _get_variables_at_line(
        self, file_path: str, line_number: int
    ) -> Dict[str, Any]:
        """Get variable values at a specific line (simulation)"""
        # This would integrate with actual debugger
        return {"local_vars": {}, "global_vars": {}}

    def _get_call_stack(self, session: DebugSession) -> List[str]:
        """Get current call stack (simulation)"""
        # This would integrate with actual debugger
        return [f"{session.target_file}:{session.step_count}"]
