"""
AI Enhancement Hints Pipeline for Meta-Tagging System
This module provides intelligent analysis and suggestions for code improvements,
including modification risk assessment, test requirement identification, optimization
opportunities detection, and refactoring recommendations.
"""
import asyncio
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from .meta_tagging import Complexity, MetaTag, SemanticRole
from .semantic_classifier import SemanticClassifier
logger = logging.getLogger(__name__)
class HintType(Enum):
    """Types of AI enhancement hints."""
    OPTIMIZATION = "optimization"
    REFACTORING = "refactoring"
    TESTING = "testing"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTENANCE = "maintenance"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
class Severity(Enum):
    """Severity levels for hints."""
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5
@dataclass
class AIHint:
    """Represents an AI-generated enhancement hint."""
    hint_type: HintType
    severity: Severity
    title: str
    description: str
    rationale: str
    suggested_action: str
    # Context information
    file_path: str = ""
    line_range: tuple[int, int] = (0, 0)
    component_name: str = ""
    # Implementation details
    estimated_effort: str = "medium"  # low, medium, high
    prerequisites: list[str] = field(default_factory=list)
    risk_level: str = "moderate"  # low, moderate, high
    # Metadata
    confidence: float = 0.0
    tags: set[str] = field(default_factory=set)
    related_patterns: list[str] = field(default_factory=list)
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "hint_type": self.hint_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "suggested_action": self.suggested_action,
            "file_path": self.file_path,
            "line_range": self.line_range,
            "component_name": self.component_name,
            "estimated_effort": self.estimated_effort,
            "prerequisites": self.prerequisites,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "tags": list(self.tags),
            "related_patterns": self.related_patterns,
        }
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AIHint":
        """Create AIHint from dictionary."""
        data["hint_type"] = HintType(data["hint_type"])
        data["severity"] = Severity(data["severity"])
        data["tags"] = set(data.get("tags", []))
        return cls(**data)
class PatternAnalyzer:
    """Analyzes code patterns for specific improvement opportunities."""
    def __init__(self):
        """Initialize with pattern definitions."""
        self.optimization_patterns = self._init_optimization_patterns()
        self.refactoring_patterns = self._init_refactoring_patterns()
        self.security_patterns = self._init_security_patterns()
        self.performance_patterns = self._init_performance_patterns()
        self.test_patterns = self._init_test_patterns()
    def _init_optimization_patterns(
        self,
    ) -> dict[str, tuple[re.Pattern, str, Severity]]:
        """Initialize optimization opportunity patterns."""
        return {
            "todo_fixme": (
                re.compile(r"#\s*(TODO|FIXME|HACK|XXX|NOTE):", re.IGNORECASE),
                "Unresolved TODO/FIXME comments indicate pending work",
                Severity.MEDIUM,
            ),
            "unused_imports": (
                re.compile(r"^import\s+(\w+)(?:\s+as\s+\w+)?$", re.MULTILINE),
                "Potentially unused imports should be removed",
                Severity.LOW,
            ),
            "magic_numbers": (
                re.compile(r"\b(?<![\w.])\d{2,}\b(?![\w.])"),
                "Magic numbers should be replaced with named constants",
                Severity.LOW,
            ),
            "long_parameter_lists": (
                re.compile(r"def\s+\w+\([^)]{80,}\):"),
                "Long parameter lists indicate need for parameter objects",
                Severity.MEDIUM,
            ),
            "nested_loops": (
                re.compile(
                    r"^\s+for\s+.*:\s*$.*?^\s+for\s+.*:\s*$", re.MULTILINE | re.DOTALL
                ),
                "Deeply nested loops may benefit from optimization",
                Severity.MEDIUM,
            ),
            "string_concatenation": (
                re.compile(r'(\w+\s*\+=\s*["\'].*["\'])'),
                "String concatenation in loops should use join() or f-strings",
                Severity.LOW,
            ),
            "inefficient_dict_access": (
                re.compile(r"if\s+\w+\s+in\s+\w+:\s*\n\s*\w+\[\w+\]"),
                "Dictionary access patterns can be optimized with get()",
                Severity.LOW,
            ),
        }
    def _init_refactoring_patterns(self) -> dict[str, tuple[re.Pattern, str, Severity]]:
        """Initialize refactoring opportunity patterns."""
        return {
            "long_methods": (
                re.compile(
                    r"def\s+\w+\([^)]*\):.*?(?=def\s+\w+\([^)]*\):|class\s+\w+|$)",
                    re.DOTALL,
                ),
                "Long methods should be broken into smaller functions",
                Severity.MEDIUM,
            ),
            "duplicate_code": (
                re.compile(r"(\S.*\n){3,}.*?(\S.*\n){3,}"),
                "Duplicate code blocks should be extracted to methods",
                Severity.HIGH,
            ),
            "god_class": (
                re.compile(r"class\s+\w+.*?(?=class\s+\w+|$)", re.DOTALL),
                "Large classes with many responsibilities need decomposition",
                Severity.HIGH,
            ),
            "complex_conditionals": (
                re.compile(r"if\s+.*?\s+and\s+.*?\s+and\s+.*?:", re.IGNORECASE),
                "Complex conditionals should be extracted to methods",
                Severity.MEDIUM,
            ),
            "feature_envy": (
                re.compile(r"(\w+)\.(\w+)\.(\w+)\.(\w+)"),
                "Excessive method chaining indicates misplaced functionality",
                Severity.MEDIUM,
            ),
            "primitive_obsession": (
                re.compile(r"def\s+\w+\([^)]*str[^)]*str[^)]*str[^)]*\):"),
                "Multiple primitive parameters suggest need for data classes",
                Severity.LOW,
            ),
        }
    def _init_security_patterns(self) -> dict[str, tuple[re.Pattern, str, Severity]]:
        """Initialize security concern patterns."""
        return {
            "sql_injection": (
                re.compile(
                    r'["\'].*%s.*["\']|["\'].*\+.*["\'].*execute|cursor\.execute\([^)]*%'
                ),
                "Potential SQL injection vulnerability",
                Severity.CRITICAL,
            ),
            "hardcoded_secrets": (
                re.compile(
                    r'(password|secret|key|token)\s*=\s*["\'][^"\']*["\']',
                    re.IGNORECASE,
                ),
                "Hardcoded secrets should be moved to environment variables",
                Severity.CRITICAL,
            ),
            "eval_exec": (
                re.compile(r"\b(eval|exec)\s*\(", re.IGNORECASE),
                "Use of eval/exec creates security vulnerabilities",
                Severity.CRITICAL,
            ),
            "unsafe_deserialization": (
                re.compile(r"pickle\.loads?|yaml\.load(?!_safe)", re.IGNORECASE),
                "Unsafe deserialization can lead to code execution",
                Severity.HIGH,
            ),
            "path_traversal": (
                re.compile(r"open\s*\([^)]*\+.*[^)]*\)", re.IGNORECASE),
                "Path concatenation may allow directory traversal",
                Severity.HIGH,
            ),
            "weak_crypto": (
                re.compile(r"md5|sha1|des|rc4", re.IGNORECASE),
                "Weak cryptographic algorithms should be replaced",
                Severity.HIGH,
            ),
            "debug_info": (
                re.compile(
                    r"print\s*\([^)]*password|traceback\.print_exc|debug\s*=\s*True",
                    re.IGNORECASE,
                ),
                "Debug information may leak sensitive data",
                Severity.MEDIUM,
            ),
        }
    def _init_performance_patterns(self) -> dict[str, tuple[re.Pattern, str, Severity]]:
        """Initialize performance issue patterns."""
        return {
            "n_plus_one": (
                re.compile(
                    r"for\s+\w+\s+in\s+.*?:\s*\n.*?\.get\(|for\s+\w+\s+in\s+.*?:\s*\n.*?\.filter\(",
                    re.MULTILINE,
                ),
                "N+1 query pattern detected in loops",
                Severity.HIGH,
            ),
            "inefficient_loops": (
                re.compile(r"for\s+\w+\s+in\s+range\(len\("),
                "Use enumerate() instead of range(len())",
                Severity.LOW,
            ),
            "repeated_expensive_calls": (
                re.compile(r"(len\(.*?\)|.*?\.count\(\)).*?\n.*?\1"),
                "Expensive calls should be cached",
                Severity.MEDIUM,
            ),
            "large_data_in_memory": (
                re.compile(r"\.readlines\(\)|\.read\(\).*file"),
                "Large file operations may cause memory issues",
                Severity.MEDIUM,
            ),
            "synchronous_io": (
                re.compile(
                    r"requests\.(get|post|put|delete)(?!\s*,\s*async)", re.IGNORECASE
                ),
                "Synchronous I/O in async contexts blocks event loop",
                Severity.HIGH,
            ),
            "unoptimized_database": (
                re.compile(r"\.all\(\).*?len\(|\.count\(\).*?\.all\(\)"),
                "Database queries can be optimized",
                Severity.MEDIUM,
            ),
        }
    def _init_test_patterns(self) -> dict[str, tuple[re.Pattern, str, Severity]]:
        """Initialize test requirement patterns."""
        return {
            "missing_tests": (
                re.compile(r"def\s+\w+\([^)]*\):(?!.*test)", re.IGNORECASE),
                "Functions without tests need test coverage",
                Severity.MEDIUM,
            ),
            "complex_logic_untested": (
                re.compile(r"if\s+.*?else.*?:|try:.*?except:|for.*?in.*?:.*?if"),
                "Complex logic requires comprehensive testing",
                Severity.HIGH,
            ),
            "async_functions": (
                re.compile(r"async\s+def\s+\w+"),
                "Async functions need specialized testing patterns",
                Severity.MEDIUM,
            ),
            "external_dependencies": (
                re.compile(
                    r"requests\.|urllib|http|database|redis|mongo", re.IGNORECASE
                ),
                "External dependencies require mocking in tests",
                Severity.MEDIUM,
            ),
            "error_handling": (
                re.compile(r"except\s+\w+|raise\s+\w+"),
                "Error handling paths need test coverage",
                Severity.HIGH,
            ),
            "configuration_dependent": (
                re.compile(r"os\.environ|getenv|config\.|settings\.", re.IGNORECASE),
                "Configuration-dependent code needs environment-specific tests",
                Severity.MEDIUM,
            ),
        }
    def analyze_patterns(self, content: str, file_path: str) -> list[AIHint]:
        """Analyze content for all pattern types."""
        hints = []
        # Analyze each pattern category
        hints.extend(
            self._analyze_category(
                content, file_path, self.optimization_patterns, HintType.OPTIMIZATION
            )
        )
        hints.extend(
            self._analyze_category(
                content, file_path, self.refactoring_patterns, HintType.REFACTORING
            )
        )
        hints.extend(
            self._analyze_category(
                content, file_path, self.security_patterns, HintType.SECURITY
            )
        )
        hints.extend(
            self._analyze_category(
                content, file_path, self.performance_patterns, HintType.PERFORMANCE
            )
        )
        hints.extend(
            self._analyze_category(
                content, file_path, self.test_patterns, HintType.TESTING
            )
        )
        return hints
    def _analyze_category(
        self,
        content: str,
        file_path: str,
        patterns: dict[str, tuple[re.Pattern, str, Severity]],
        hint_type: HintType,
    ) -> list[AIHint]:
        """Analyze content for a specific category of patterns."""
        hints = []
        for pattern_name, (pattern, description, severity) in patterns.items():
            matches = list(pattern.finditer(content))
            if matches:
                # Create hint for this pattern
                match_count = len(matches)
                first_match = matches[0]
                # Calculate line number
                line_number = content[: first_match.start()].count("\n") + 1
                # Generate specific title and action
                title, action = self._generate_hint_details(
                    pattern_name, match_count, hint_type
                )
                hint = AIHint(
                    hint_type=hint_type,
                    severity=severity,
                    title=title,
                    description=description,
                    rationale=f"Found {match_count} instance(s) of pattern '{pattern_name}'",
                    suggested_action=action,
                    file_path=file_path,
                    line_range=(line_number, line_number),
                    confidence=min(0.9, 0.5 + (match_count * 0.1)),
                    tags={pattern_name, hint_type.value},
                    related_patterns=[pattern_name],
                )
                hints.append(hint)
        return hints
    def _generate_hint_details(
        self, pattern_name: str, count: int, hint_type: HintType
    ) -> tuple[str, str]:
        """Generate specific title and action for a pattern match."""
        actions = {
            "todo_fixme": (
                f"Resolve {count} TODO/FIXME comment(s)",
                "Review and address all TODO/FIXME comments by implementing the required functionality or removing obsolete comments",
            ),
            "unused_imports": (
                f"Remove {count} potentially unused import(s)",
                "Use tools like autoflake or manual review to identify and remove unused imports",
            ),
            "magic_numbers": (
                f"Replace {count} magic number(s) with constants",
                "Extract magic numbers to named constants with descriptive names",
            ),
            "long_parameter_lists": (
                "Refactor long parameter lists",
                "Consider using parameter objects, dataclasses, or **kwargs for functions with many parameters",
            ),
            "sql_injection": (
                "Fix potential SQL injection vulnerability",
                "Use parameterized queries or ORM methods instead of string concatenation",
            ),
            "hardcoded_secrets": (
                "Remove hardcoded secrets",
                "Move secrets to environment variables or secure configuration files",
            ),
            "n_plus_one": (
                "Optimize N+1 query pattern",
                "Use bulk operations, select_related, or prefetch_related to reduce database queries",
            ),
            "missing_tests": (
                f"Add tests for {count} untested function(s)",
                "Write unit tests covering all code paths, edge cases, and error conditions",
            ),
            "complex_logic_untested": (
                "Add tests for complex logic paths",
                "Write comprehensive tests covering all conditional branches and error handling",
            ),
        }
        return actions.get(
            pattern_name,
            (
                f"Address {pattern_name} issue(s)",
                f"Review and improve code related to {pattern_name} pattern",
            ),
        )
class RiskAssessmentEngine:
    """Assesses modification risks for code components."""
    def __init__(self):
        """Initialize risk assessment rules."""
        self.risk_factors = self._init_risk_factors()
        self.dependency_weights = {
            "core_system": 0.8,
            "external_api": 0.6,
            "database": 0.7,
            "configuration": 0.5,
            "testing": 0.3,
        }
    def _init_risk_factors(self) -> dict[str, tuple[re.Pattern, float, str]]:
        """Initialize risk factor patterns with weights and descriptions."""
        return {
            "global_state_mutation": (
                re.compile(r"global\s+\w+.*?=|globals\(\)\["),
                0.8,
                "Modifies global state which can have system-wide effects",
            ),
            "database_schema_changes": (
                re.compile(
                    r"CREATE\s+TABLE|ALTER\s+TABLE|DROP\s+TABLE|migration",
                    re.IGNORECASE,
                ),
                0.9,
                "Database schema changes affect data persistence and compatibility",
            ),
            "external_api_integration": (
                re.compile(r"requests\.|urllib|http|api_key|endpoint", re.IGNORECASE),
                0.6,
                "External API integrations can break due to external changes",
            ),
            "core_business_logic": (
                re.compile(
                    r"def\s+(calculate|process|validate|authenticate|authorize)",
                    re.IGNORECASE,
                ),
                0.7,
                "Core business logic changes affect system functionality",
            ),
            "configuration_changes": (
                re.compile(r"config\.|settings\.|environment|\.env", re.IGNORECASE),
                0.5,
                "Configuration changes affect system behavior across environments",
            ),
            "security_critical": (
                re.compile(r"auth|security|password|token|crypto|hash", re.IGNORECASE),
                0.9,
                "Security-critical code requires careful review and testing",
            ),
            "performance_critical": (
                re.compile(
                    r"cache|index|query|optimization|performance", re.IGNORECASE
                ),
                0.6,
                "Performance-critical code changes can affect system responsiveness",
            ),
            "error_handling": (
                re.compile(r"except\s+.*?:|raise\s+|try:.*?finally:", re.DOTALL),
                0.5,
                "Error handling changes affect system stability and debugging",
            ),
            "data_transformation": (
                re.compile(
                    r"json\.|pickle\.|serialize|deserialize|encode|decode",
                    re.IGNORECASE,
                ),
                0.6,
                "Data transformation changes can cause compatibility issues",
            ),
            "concurrency_control": (
                re.compile(r"async|await|thread|lock|semaphore|queue", re.IGNORECASE),
                0.8,
                "Concurrency control changes can introduce race conditions",
            ),
        }
    def assess_modification_risk(self, content: str, meta_tag: MetaTag) -> list[AIHint]:
        """Assess modification risk and generate relevant hints."""
        hints = []
        risk_score = 0.0
        identified_risks = []
        # Analyze risk factors
        for factor_name, (pattern, weight, description) in self.risk_factors.items():
            if pattern.search(content):
                risk_score += weight
                identified_risks.append((factor_name, description))
        # Adjust risk based on component characteristics
        risk_score *= self._get_role_risk_multiplier(meta_tag.semantic_role)
        risk_score *= self._get_complexity_risk_multiplier(meta_tag.complexity)
        # Generate risk assessment hint
        if risk_score > 0.3:  # Threshold for generating risk hints
            severity = self._calculate_severity(risk_score)
            risk_hint = AIHint(
                hint_type=HintType.MAINTENANCE,
                severity=severity,
                title=f"High modification risk detected (score: {risk_score:.2f})",
                description="This component has characteristics that increase modification risk",
                rationale=f"Risk factors: {', '.join([risk[0] for risk in identified_risks])}",
                suggested_action=self._generate_risk_mitigation_action(
                    identified_risks, severity
                ),
                file_path=meta_tag.file_path,
                component_name=meta_tag.component_name,
                confidence=min(0.95, risk_score),
                risk_level="high" if risk_score > 0.7 else "moderate",
                estimated_effort="high" if risk_score > 0.8 else "medium",
                tags={"risk_assessment", "modification_risk"},
                related_patterns=[risk[0] for risk in identified_risks],
            )
            hints.append(risk_hint)
        return hints
    def _get_role_risk_multiplier(self, role: SemanticRole) -> float:
        """Get risk multiplier based on semantic role."""
        high_risk_roles = {
            SemanticRole.ORCHESTRATOR: 1.3,
            SemanticRole.GATEWAY: 1.2,
            SemanticRole.REPOSITORY: 1.2,
            SemanticRole.AGENT: 1.1,
            SemanticRole.SERVICE: 1.1,
        }
        return high_risk_roles.get(role, 1.0)
    def _get_complexity_risk_multiplier(self, complexity: Complexity) -> float:
        """Get risk multiplier based on complexity."""
        complexity_multipliers = {
            Complexity.TRIVIAL: 0.8,
            Complexity.LOW: 0.9,
            Complexity.MODERATE: 1.0,
            Complexity.HIGH: 1.2,
            Complexity.CRITICAL: 1.4,
        }
        return complexity_multipliers.get(complexity, 1.0)
    def _calculate_severity(self, risk_score: float) -> Severity:
        """Calculate severity based on risk score."""
        if risk_score >= 1.5:
            return Severity.CRITICAL
        elif risk_score >= 1.0:
            return Severity.HIGH
        elif risk_score >= 0.6:
            return Severity.MEDIUM
        else:
            return Severity.LOW
    def _generate_risk_mitigation_action(
        self, risks: list[tuple[str, str]], severity: Severity
    ) -> str:
        """Generate specific risk mitigation actions."""
        actions = []
        if severity in [Severity.HIGH, Severity.CRITICAL]:
            actions.append("Require thorough code review and testing before changes")
            actions.append("Consider pair programming or team review sessions")
            actions.append("Implement comprehensive integration tests")
        if any("database" in risk[0] for risk in risks):
            actions.append("Create database migration backup and rollback plan")
        if any("security" in risk[0] for risk in risks):
            actions.append("Conduct security review and penetration testing")
        if any("performance" in risk[0] for risk in risks):
            actions.append("Perform load testing and performance benchmarking")
        if any("concurrency" in risk[0] for risk in risks):
            actions.append("Review for race conditions and deadlock scenarios")
        return (
            "; ".join(actions) if actions else "Proceed with careful testing and review"
        )
class OptimizationDetector:
    """Detects optimization opportunities in code."""
    def __init__(self):
        """Initialize optimization detection rules."""
        self.optimization_rules = self._init_optimization_rules()
    def _init_optimization_rules(self) -> dict[str, Any]:
        """Initialize optimization detection rules."""
        return {
            "caching_opportunities": {
                "patterns": [
                    re.compile(
                        r"def\s+(\w+).*?return\s+.*?expensive.*?calculation",
                        re.IGNORECASE | re.DOTALL,
                    ),
                    re.compile(
                        r"for\s+.*?in\s+.*?:\s*\n.*?database.*?query", re.IGNORECASE
                    ),
                    re.compile(r"\.get\(.*?\).*?\.get\(.*?\)"),  # Repeated API calls
                ],
                "description": "Functions that perform expensive operations repeatedly",
                "suggestion": "Implement caching using @lru_cache, Redis, or in-memory cache",
            },
            "database_optimization": {
                "patterns": [
                    re.compile(r"for\s+.*?in\s+.*?\.all\(\):", re.IGNORECASE),
                    re.compile(
                        r"\.filter\(.*?\)\.count\(\).*?\.filter\(.*?\)", re.IGNORECASE
                    ),
                    re.compile(r"select_related|prefetch_related", re.IGNORECASE),
                ],
                "description": "Database queries that can be optimized",
                "suggestion": "Use select_related, prefetch_related, or bulk operations",
            },
            "algorithmic_improvements": {
                "patterns": [
                    re.compile(
                        r"for\s+.*?in\s+.*?:\s*\n.*?for\s+.*?in\s+.*?:", re.MULTILINE
                    ),
                    re.compile(r"\.sort\(\).*?\.sort\(\)"),
                    re.compile(r"if\s+.*?in\s+\[.*?\]:"),  # Linear search in list
                ],
                "description": "Algorithmic patterns that can be improved",
                "suggestion": "Consider more efficient algorithms or data structures",
            },
            "resource_management": {
                "patterns": [
                    re.compile(r"open\(.*?\)(?!.*?with)", re.IGNORECASE),
                    re.compile(r"requests\.get\(.*?\)(?!.*?session)", re.IGNORECASE),
                    re.compile(r"Thread\(.*?\)(?!.*?with)", re.IGNORECASE),
                ],
                "description": "Resource management that can be improved",
                "suggestion": "Use context managers or connection pooling",
            },
        }
    def detect_optimizations(self, content: str, meta_tag: MetaTag) -> list[AIHint]:
        """Detect optimization opportunities."""
        hints = []
        for opt_type, rules in self.optimization_rules.items():
            matches_found = 0
            matched_lines = []
            for pattern in rules["patterns"]:
                matches = list(pattern.finditer(content))
                if matches:
                    matches_found += len(matches)
                    for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        matched_lines.append(line_num)
            if matches_found > 0:
                hint = AIHint(
                    hint_type=HintType.OPTIMIZATION,
                    severity=self._calculate_optimization_severity(
                        matches_found, meta_tag.complexity
                    ),
                    title=f"Optimization opportunity: {opt_type.replace('_', ' ').title()}",
                    description=rules["description"],
                    rationale=f"Found {matches_found} potential optimization point(s)",
                    suggested_action=rules["suggestion"],
                    file_path=meta_tag.file_path,
                    line_range=(
                        (min(matched_lines), max(matched_lines))
                        if matched_lines
                        else (0, 0)
                    ),
                    component_name=meta_tag.component_name,
                    confidence=min(0.8, 0.4 + (matches_found * 0.1)),
                    estimated_effort="medium" if matches_found < 3 else "high",
                    tags={"optimization", opt_type},
                    related_patterns=[opt_type],
                )
                hints.append(hint)
        return hints
    def _calculate_optimization_severity(
        self, match_count: int, complexity: Complexity
    ) -> Severity:
        """Calculate severity based on match count and complexity."""
        base_severity = Severity.LOW
        if match_count >= 5:
            base_severity = Severity.HIGH
        elif match_count >= 3:
            base_severity = Severity.MEDIUM
        # Increase severity for complex components
        if (
            complexity.value >= Complexity.HIGH.value
            and base_severity.value < Severity.HIGH.value
        ):
            return Severity(base_severity.value + 1)
        return base_severity
class TestRequirementAnalyzer:
    """Analyzes test requirements and coverage gaps."""
    def __init__(self):
        """Initialize test analysis rules."""
        self.test_rules = self._init_test_rules()
    def _init_test_rules(self) -> dict[str, Any]:
        """Initialize test requirement rules."""
        return {
            "edge_case_testing": {
                "patterns": [
                    re.compile(r"if\s+.*?is\s+None:", re.IGNORECASE),
                    re.compile(r"if\s+not\s+.*?:", re.IGNORECASE),
                    re.compile(r"try:.*?except.*?:", re.DOTALL),
                    re.compile(r"assert\s+.*?>", re.IGNORECASE),
                ],
                "description": "Code paths that require edge case testing",
                "requirements": [
                    "Test null/empty inputs",
                    "Test boundary conditions",
                    "Test error conditions",
                ],
            },
            "integration_testing": {
                "patterns": [
                    re.compile(r"requests\.|urllib|http", re.IGNORECASE),
                    re.compile(r"database|sql|query", re.IGNORECASE),
                    re.compile(r"redis|cache|session", re.IGNORECASE),
                    re.compile(r"async\s+def|await", re.IGNORECASE),
                ],
                "description": "External dependencies requiring integration tests",
                "requirements": [
                    "Mock external services",
                    "Test async behavior",
                    "Test error scenarios",
                ],
            },
            "security_testing": {
                "patterns": [
                    re.compile(r"password|secret|token|auth", re.IGNORECASE),
                    re.compile(r"hash|encrypt|decrypt", re.IGNORECASE),
                    re.compile(r"validate|sanitize|escape", re.IGNORECASE),
                ],
                "description": "Security-related code requiring specialized testing",
                "requirements": [
                    "Test authentication scenarios",
                    "Test authorization boundaries",
                    "Test input validation",
                ],
            },
            "performance_testing": {
                "patterns": [
                    re.compile(r"cache|optimization|performance", re.IGNORECASE),
                    re.compile(r"for\s+.*?in\s+.*?:\s*\n.*?for", re.MULTILINE),
                    re.compile(r"async|concurrent|parallel", re.IGNORECASE),
                ],
                "description": "Performance-critical code requiring load testing",
                "requirements": [
                    "Benchmark performance",
                    "Test under load",
                    "Test memory usage",
                ],
            },
        }
    def analyze_test_requirements(
        self, content: str, meta_tag: MetaTag
    ) -> list[AIHint]:
        """Analyze test requirements for the component."""
        hints = []
        for test_type, rules in self.test_rules.items():
            matches_found = []
            for pattern in rules["patterns"]:
                matches = list(pattern.finditer(content))
                matches_found.extend(matches)
            if matches_found:
                # Generate test requirement hint
                hint = AIHint(
                    hint_type=HintType.TESTING,
                    severity=self._calculate_test_severity(
                        len(matches_found), meta_tag
                    ),
                    title=f"Test requirements: {test_type.replace('_', ' ').title()}",
                    description=rules["description"],
                    rationale=f"Found {len(matches_found)} pattern(s) requiring {test_type}",
                    suggested_action="; ".join(rules["requirements"]),
                    file_path=meta_tag.file_path,
                    component_name=meta_tag.component_name,
                    confidence=0.7,
                    estimated_effort="medium" if len(matches_found) < 5 else "high",
                    prerequisites=["Test framework setup", "Mock dependencies"],
                    tags={"testing", test_type},
                    related_patterns=[test_type],
                )
                hints.append(hint)
        return hints
    def _calculate_test_severity(self, match_count: int, meta_tag: MetaTag) -> Severity:
        """Calculate test severity based on patterns and component characteristics."""
        base_severity = Severity.MEDIUM
        # Increase severity for critical roles
        if meta_tag.semantic_role in [
            SemanticRole.ORCHESTRATOR,
            SemanticRole.GATEWAY,
            SemanticRole.AGENT,
        ]:
            base_severity = Severity.HIGH
        # Increase severity for complex components
        if meta_tag.complexity.value >= Complexity.HIGH.value:
            base_severity = Severity.HIGH
        # Increase severity for many patterns
        if match_count >= 5 and base_severity.value < Severity.HIGH.value:
            return Severity.HIGH
        return base_severity
class AIHintsPipeline:
    """Main pipeline for generating AI enhancement hints."""
    def __init__(self):
        """Initialize the hints pipeline."""
        self.pattern_analyzer = PatternAnalyzer()
        self.risk_engine = RiskAssessmentEngine()
        self.optimization_detector = OptimizationDetector()
        self.test_analyzer = TestRequirementAnalyzer()
        self.classifier = SemanticClassifier()
    async def generate_hints(self, content: str, meta_tag: MetaTag) -> list[AIHint]:
        """Generate comprehensive AI hints for a component."""
        hints = []
        try:
            # Pattern-based analysis
            pattern_hints = self.pattern_analyzer.analyze_patterns(
                content, meta_tag.file_path
            )
            hints.extend(pattern_hints)
            # Risk assessment
            risk_hints = self.risk_engine.assess_modification_risk(content, meta_tag)
            hints.extend(risk_hints)
            # Optimization detection
            optimization_hints = self.optimization_detector.detect_optimizations(
                content, meta_tag
            )
            hints.extend(optimization_hints)
            # Test requirements analysis
            test_hints = self.test_analyzer.analyze_test_requirements(content, meta_tag)
            hints.extend(test_hints)
            # Architecture-level hints
            architecture_hints = await self._generate_architecture_hints(
                content, meta_tag
            )
            hints.extend(architecture_hints)
            # Documentation hints
            doc_hints = self._generate_documentation_hints(content, meta_tag)
            hints.extend(doc_hints)
            # Sort hints by severity and confidence
            hints.sort(key=lambda h: (h.severity.value, h.confidence), reverse=True)
            logger.info(f"Generated {len(hints)} hints for {meta_tag.component_name}")
        except Exception as e:
            logger.error(f"Error generating hints for {meta_tag.component_name}: {e}")
        return hints
    async def _generate_architecture_hints(
        self, content: str, meta_tag: MetaTag
    ) -> list[AIHint]:
        """Generate architecture-level improvement hints."""
        hints = []
        # Analyze component relationships and architecture patterns
        if meta_tag.semantic_role == SemanticRole.ORCHESTRATOR:
            if len(meta_tag.dependencies) > 10:
                hints.append(
                    AIHint(
                        hint_type=HintType.ARCHITECTURE,
                        severity=Severity.MEDIUM,
                        title="High coupling detected in orchestrator",
                        description="Orchestrator has many dependencies indicating tight coupling",
                        rationale=f"Component depends on {len(meta_tag.dependencies)} other components",
                        suggested_action="Consider using dependency injection or facade pattern to reduce coupling",
                        file_path=meta_tag.file_path,
                        component_name=meta_tag.component_name,
                        confidence=0.8,
                        estimated_effort="high",
                        tags={"architecture", "coupling"},
                    )
                )
        # Check for missing error boundaries
        if (
            not re.search(r"try:.*?except.*?:", content, re.DOTALL)
            and meta_tag.complexity.value >= Complexity.MODERATE.value
        ):
            hints.append(
                AIHint(
                    hint_type=HintType.ARCHITECTURE,
                    severity=Severity.MEDIUM,
                    title="Missing error boundaries",
                    description="Complex component lacks comprehensive error handling",
                    rationale="No try-except blocks found in moderately complex component",
                    suggested_action="Add appropriate error handling and logging for failure scenarios",
                    file_path=meta_tag.file_path,
                    component_name=meta_tag.component_name,
                    confidence=0.6,
                    estimated_effort="medium",
                    tags={"architecture", "error_handling"},
                )
            )
        return hints
    def _generate_documentation_hints(
        self, content: str, meta_tag: MetaTag
    ) -> list[AIHint]:
        """Generate documentation improvement hints."""
        hints = []
        # Check for missing docstrings
        if not re.search(r'""".*?"""', content, re.DOTALL):
            severity = (
                Severity.MEDIUM
                if meta_tag.complexity.value >= Complexity.MODERATE.value
                else Severity.LOW
            )
            hints.append(
                AIHint(
                    hint_type=HintType.DOCUMENTATION,
                    severity=severity,
                    title="Missing or inadequate documentation",
                    description="Component lacks comprehensive docstrings",
                    rationale="No docstrings found in component",
                    suggested_action="Add docstrings explaining purpose, parameters, return values, and usage examples",
                    file_path=meta_tag.file_path,
                    component_name=meta_tag.component_name,
                    confidence=0.9,
                    estimated_effort="low",
                    tags={"documentation", "docstrings"},
                )
            )
        # Check for complex functions without type hints
        if re.search(r"def\s+\w+\([^)]*\):", content) and not re.search(
            r"def\s+\w+\([^)]*\)\s*->", content
        ):
            hints.append(
                AIHint(
                    hint_type=HintType.DOCUMENTATION,
                    severity=Severity.LOW,
                    title="Missing type hints",
                    description="Functions lack type annotations for better code clarity",
                    rationale="Function definitions without return type annotations found",
                    suggested_action="Add type hints for function parameters and return values",
                    file_path=meta_tag.file_path,
                    component_name=meta_tag.component_name,
                    confidence=0.7,
                    estimated_effort="low",
                    tags={"documentation", "type_hints"},
                )
            )
        return hints
    def filter_hints(
        self,
        hints: list[AIHint],
        min_severity: Severity = Severity.LOW,
        min_confidence: float = 0.3,
        max_hints: Optional[int] = None,
    ) -> list[AIHint]:
        """Filter and prioritize hints based on criteria."""
        # Filter by severity and confidence
        filtered_hints = [
            hint
            for hint in hints
            if hint.severity.value >= min_severity.value
            and hint.confidence >= min_confidence
        ]
        # Sort by priority (severity * confidence)
        filtered_hints.sort(key=lambda h: h.severity.value * h.confidence, reverse=True)
        # Limit number of hints if specified
        if max_hints:
            filtered_hints = filtered_hints[:max_hints]
        return filtered_hints
    def generate_summary_report(self, hints: list[AIHint]) -> dict[str, Any]:
        """Generate a summary report of all hints."""
        # Group hints by type and severity
        by_type = {}
        by_severity = {}
        for hint in hints:
            hint_type = hint.hint_type.value
            severity = hint.severity.value
            if hint_type not in by_type:
                by_type[hint_type] = []
            by_type[hint_type].append(hint)
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(hint)
        # Calculate statistics
        total_hints = len(hints)
        avg_confidence = (
            sum(h.confidence for h in hints) / total_hints if total_hints > 0 else 0
        )
        critical_count = len([h for h in hints if h.severity == Severity.CRITICAL])
        high_count = len([h for h in hints if h.severity == Severity.HIGH])
        return {
            "total_hints": total_hints,
            "by_type": {t: len(h_list) for t, h_list in by_type.items()},
            "by_severity": {s: len(h_list) for s, h_list in by_severity.items()},
            "average_confidence": avg_confidence,
            "critical_issues": critical_count,
            "high_priority": high_count,
            "estimated_total_effort": self._estimate_total_effort(hints),
            "top_recommendations": [hint.to_dict() for hint in hints[:5]],
        }
    def _estimate_total_effort(self, hints: list[AIHint]) -> str:
        """Estimate total effort required to address all hints."""
        effort_mapping = {"low": 1, "medium": 3, "high": 8}
        total_points = sum(
            effort_mapping.get(hint.estimated_effort, 3) for hint in hints
        )
        if total_points <= 5:
            return "low"
        elif total_points <= 15:
            return "medium"
        else:
            return "high"
# Utility functions for external use
async def generate_ai_hints(content: str, meta_tag: MetaTag) -> list[AIHint]:
    """Generate AI hints for a component."""
    pipeline = AIHintsPipeline()
    return await pipeline.generate_hints(content, meta_tag)
def quick_pattern_analysis(content: str, file_path: str) -> list[AIHint]:
    """Quick pattern-based analysis for immediate insights."""
    analyzer = PatternAnalyzer()
    return analyzer.analyze_patterns(content, file_path)
if __name__ == "__main__":
    # Example usage
    import asyncio
    from .meta_tagging import Complexity, MetaTag, SemanticRole
    async def main():
        sample_code = """
        import requests
        import json
        def get_user_data(user_id):
            # Add caching when performance requires it
            response = requests.get(f"https://api.example.com/users/{user_id}")
            return json.loads(response.text)
        def process_users():
            users = []
            for i in range(100):
                user = get_user_data(i)  # N+1 query problem
                users.append(user)
            return users
        """
        meta_tag = MetaTag(
            file_path="user_service.py",
            component_name="UserService",
            semantic_role=SemanticRole.SERVICE,
            complexity=Complexity.MODERATE,
        )
        pipeline = AIHintsPipeline()
        hints = await pipeline.generate_hints(sample_code, meta_tag)
        print(f"Generated {len(hints)} hints:")
        for hint in hints[:3]:  # Show top 3
            print(f"- {hint.title} ({hint.severity.name})")
            print(f"  {hint.description}")
            print(f"  Action: {hint.suggested_action}\n")
    asyncio.run(main())
