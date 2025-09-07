"""
AI Hints Generation Pipeline
=============================

Intelligent hint generation for AI-assisted code modification,
providing context-aware guidance for safe and effective code changes.

AI Context:
- Generates modification risk scores based on code complexity
- Identifies test requirements automatically
- Suggests optimization opportunities
- Provides refactoring recommendations
"""

import ast
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Tuple

from app.scaffolding.meta_tagging import AIHints, CodeMetadata, ComplexityLevel
from app.scaffolding.semantic_classifier import get_semantic_classifier

logger = logging.getLogger(__name__)


class RiskFactor(Enum):
    """Risk factors for code modification"""

    DATABASE_OPERATIONS = 0.9
    EXTERNAL_API_CALLS = 0.8
    FILE_SYSTEM_OPERATIONS = 0.7
    AUTHENTICATION_LOGIC = 0.9
    PAYMENT_PROCESSING = 1.0
    CRYPTOGRAPHIC_OPERATIONS = 0.95
    CONCURRENT_OPERATIONS = 0.75
    GLOBAL_STATE_MODIFICATION = 0.7
    CONFIGURATION_CHANGES = 0.6
    CACHE_OPERATIONS = 0.5
    LOGGING_ONLY = 0.1
    PURE_COMPUTATION = 0.05


class TestStrategy(Enum):
    """Test strategies for different code types"""

    UNIT_TEST = "unit_test"
    INTEGRATION_TEST = "integration_test"
    E2E_TEST = "end_to_end_test"
    REGRESSION_TEST = "regression_test"
    PERFORMANCE_TEST = "performance_test"
    SECURITY_TEST = "security_test"
    LOAD_TEST = "load_test"
    CHAOS_TEST = "chaos_test"


@dataclass
class OptimizationOpportunity:
    """Identified optimization opportunity"""

    type: str
    description: str
    potential_impact: float  # 0.0 to 1.0
    complexity: str  # easy, medium, hard
    code_location: str
    suggested_approach: str


@dataclass
class RefactoringRecommendation:
    """Specific refactoring recommendation"""

    pattern: str
    reason: str
    priority: int  # 1 (high) to 5 (low)
    estimated_effort: str  # hours/days
    breaking_change: bool
    migration_steps: List[str] = field(default_factory=list)


class AIHintsGenerator:
    """Main generator for AI hints"""

    def __init__(self):
        self.classifier = get_semantic_classifier()
        self.risk_patterns = self._compile_risk_patterns()
        self.optimization_patterns = self._compile_optimization_patterns()

    def _compile_risk_patterns(self) -> Dict[str, RiskFactor]:
        """Compile patterns that indicate risk"""
        return {
            # Database patterns
            r"\.execute\(": RiskFactor.DATABASE_OPERATIONS,
            r"\.query\(": RiskFactor.DATABASE_OPERATIONS,
            r"\.insert\(": RiskFactor.DATABASE_OPERATIONS,
            r"\.update\(": RiskFactor.DATABASE_OPERATIONS,
            r"\.delete\(": RiskFactor.DATABASE_OPERATIONS,
            r"BEGIN TRANSACTION": RiskFactor.DATABASE_OPERATIONS,
            # API patterns
            r"requests\.(get|post|put|delete)": RiskFactor.EXTERNAL_API_CALLS,
            r"httpx\.(get|post|put|delete)": RiskFactor.EXTERNAL_API_CALLS,
            r"aiohttp\.(get|post|put|delete)": RiskFactor.EXTERNAL_API_CALLS,
            r"openai\.": RiskFactor.EXTERNAL_API_CALLS,
            r"anthropic\.": RiskFactor.EXTERNAL_API_CALLS,
            # File system patterns
            r"open\(": RiskFactor.FILE_SYSTEM_OPERATIONS,
            r"\.write\(": RiskFactor.FILE_SYSTEM_OPERATIONS,
            r"\.read\(": RiskFactor.FILE_SYSTEM_OPERATIONS,
            r"shutil\.": RiskFactor.FILE_SYSTEM_OPERATIONS,
            r"os\.remove": RiskFactor.FILE_SYSTEM_OPERATIONS,
            # Security patterns
            r"jwt\.": RiskFactor.AUTHENTICATION_LOGIC,
            r"bcrypt\.": RiskFactor.AUTHENTICATION_LOGIC,
            r"hashlib\.": RiskFactor.CRYPTOGRAPHIC_OPERATIONS,
            r"cryptography\.": RiskFactor.CRYPTOGRAPHIC_OPERATIONS,
            r"stripe\.": RiskFactor.PAYMENT_PROCESSING,
            # Concurrency patterns
            r"asyncio\.": RiskFactor.CONCURRENT_OPERATIONS,
            r"threading\.": RiskFactor.CONCURRENT_OPERATIONS,
            r"multiprocessing\.": RiskFactor.CONCURRENT_OPERATIONS,
            r"async def": RiskFactor.CONCURRENT_OPERATIONS,
            # State patterns
            r"global ": RiskFactor.GLOBAL_STATE_MODIFICATION,
            r"__setattr__": RiskFactor.GLOBAL_STATE_MODIFICATION,
            r"os\.environ\[": RiskFactor.CONFIGURATION_CHANGES,
        }

    def _compile_optimization_patterns(self) -> List[Tuple[str, str, str]]:
        """Compile patterns that indicate optimization opportunities"""
        return [
            (
                r"for .* in .*:\n.*for .* in",
                "nested_loops",
                "Consider vectorization or optimization",
            ),
            (r"time\.sleep\(", "blocking_sleep", "Use async sleep in async context"),
            (r"\+ \[.*\]", "list_concatenation", "Use extend() instead of + for lists"),
            (r"except:$", "bare_except", "Specify exception types"),
            (r"if .* == True:", "explicit_bool_check", "Use 'if variable:' for boolean checks"),
            (r"len\(.*\) > 0", "len_comparison", "Use 'if collection:' for emptiness check"),
            (r"dict\(\)", "dict_constructor", "Use {} for empty dict"),
            (r"list\(\)", "list_constructor", "Use [] for empty list"),
        ]

    def generate_hints(self, metadata: CodeMetadata, source_code: str) -> AIHints:
        """Generate comprehensive AI hints for a code element"""
        hints = AIHints()

        # Calculate modification risk
        hints.modification_risk = self._calculate_modification_risk(metadata, source_code)

        # Determine test requirements
        hints.test_requirements = self._determine_test_requirements(
            metadata, hints.modification_risk
        )

        # Identify optimization potential
        optimization = self._identify_optimization_potential(metadata, source_code)
        hints.optimization_potential = optimization["score"]
        hints.refactoring_suggestions = optimization["suggestions"]

        # Extract dependencies
        hints.dependencies = self._extract_dependencies(source_code)

        # Identify side effects
        hints.side_effects = self._identify_side_effects(source_code)

        # Check concurrency safety
        hints.concurrency_safe = self._check_concurrency_safety(source_code, hints.side_effects)

        # Check idempotency
        hints.idempotent = self._check_idempotency(metadata, source_code)

        # Check if pure function
        hints.pure_function = self._is_pure_function(source_code, hints.side_effects)

        return hints

    def _calculate_modification_risk(self, metadata: CodeMetadata, source_code: str) -> float:
        """Calculate the risk of modifying this code"""
        risk_score = 0.0
        risk_factors = []

        # Check for risk patterns
        for pattern, risk_factor in self.risk_patterns.items():
            import re

            if re.search(pattern, source_code):
                risk_factors.append(risk_factor.value)

        # Take the maximum risk factor found
        if risk_factors:
            risk_score = max(risk_factors)
        else:
            # Base risk on complexity
            complexity_risks = {
                ComplexityLevel.TRIVIAL: 0.1,
                ComplexityLevel.LOW: 0.2,
                ComplexityLevel.MEDIUM: 0.4,
                ComplexityLevel.HIGH: 0.6,
                ComplexityLevel.CRITICAL: 0.8,
            }
            risk_score = complexity_risks.get(metadata.complexity, 0.5)

        # Adjust based on relationships
        if len(metadata.called_by) > 5:
            risk_score = min(risk_score + 0.2, 1.0)  # High fan-in increases risk

        # Adjust based on semantic role
        high_risk_roles = ["orchestrator", "validator", "repository", "api_endpoint"]
        if metadata.semantic_role.value in high_risk_roles:
            risk_score = min(risk_score + 0.1, 1.0)

        return risk_score

    def _determine_test_requirements(self, metadata: CodeMetadata, risk: float) -> List[str]:
        """Determine required test strategies"""
        requirements = []

        # Always need unit tests
        requirements.append(TestStrategy.UNIT_TEST.value)

        # Add based on risk level
        if risk > 0.3:
            requirements.append(TestStrategy.INTEGRATION_TEST.value)

        if risk > 0.6:
            requirements.append(TestStrategy.REGRESSION_TEST.value)

        if risk > 0.8:
            requirements.append(TestStrategy.E2E_TEST.value)

        # Add based on semantic role
        role_tests = {
            "api_endpoint": [TestStrategy.INTEGRATION_TEST, TestStrategy.LOAD_TEST],
            "repository": [TestStrategy.INTEGRATION_TEST],
            "validator": [TestStrategy.UNIT_TEST, TestStrategy.SECURITY_TEST],
            "llm_interface": [TestStrategy.INTEGRATION_TEST, TestStrategy.PERFORMANCE_TEST],
        }

        if metadata.semantic_role.value in role_tests:
            for test in role_tests[metadata.semantic_role.value]:
                if test.value not in requirements:
                    requirements.append(test.value)

        # Add based on specific patterns
        if "async" in metadata.type:
            if TestStrategy.INTEGRATION_TEST.value not in requirements:
                requirements.append(TestStrategy.INTEGRATION_TEST.value)

        return requirements

    def _identify_optimization_potential(
        self, metadata: CodeMetadata, source_code: str
    ) -> Dict[str, Any]:
        """Identify optimization opportunities"""
        score = 0.0
        suggestions = []

        import re

        for pattern, opt_type, suggestion in self.optimization_patterns:
            if re.search(pattern, source_code, re.MULTILINE):
                score += 0.2
                suggestions.append(f"{opt_type}: {suggestion}")

        # Check for common antipatterns
        lines = source_code.split("\n")

        # Long functions
        if len(lines) > 100:
            score += 0.3
            suggestions.append("long_function: Consider breaking into smaller functions")

        # Deep nesting
        max_indent = (
            max((len(line) - len(line.lstrip())) // 4 for line in lines if line.strip())
            if lines
            else 0
        )

        if max_indent > 4:
            score += 0.3
            suggestions.append("deep_nesting: Reduce nesting depth for better readability")

        # Duplicate code detection (simple check)
        code_blocks = []
        current_block = []

        for line in lines:
            if line.strip():
                current_block.append(line.strip())
            else:
                if len(current_block) > 3:
                    block_str = "\n".join(current_block)
                    if block_str in code_blocks:
                        score += 0.2
                        suggestions.append("duplicate_code: Extract duplicate code to functions")
                        break
                    code_blocks.append(block_str)
                current_block = []

        # Check complexity
        if metadata.complexity == ComplexityLevel.CRITICAL:
            score += 0.4
            suggestions.append("high_complexity: Consider refactoring to reduce complexity")

        return {
            "score": min(score, 1.0),
            "suggestions": suggestions,
        }

    def _extract_dependencies(self, source_code: str) -> List[str]:
        """Extract external dependencies from code"""
        dependencies = []

        try:
            tree = ast.parse(source_code)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.append(node.module)

        except Exception as e:
            logger.warning(f"Failed to parse dependencies: {e}")

        return list(set(dependencies))

    def _identify_side_effects(self, source_code: str) -> List[str]:
        """Identify potential side effects"""
        side_effects = []

        # Check for I/O operations
        if any(op in source_code for op in ["open(", "print(", "write(", "read("]):
            side_effects.append("io_operations")

        # Check for network operations
        if any(op in source_code for op in ["requests.", "httpx.", "aiohttp.", "urllib."]):
            side_effects.append("network_operations")

        # Check for database operations
        if any(op in source_code for op in [".execute(", ".query(", ".insert(", ".update("]):
            side_effects.append("database_operations")

        # Check for global state
        if "global " in source_code:
            side_effects.append("global_state_modification")

        # Check for file system changes
        if any(op in source_code for op in ["os.remove", "shutil.", "pathlib."]):
            side_effects.append("file_system_changes")

        # Check for environment changes
        if "os.environ" in source_code:
            side_effects.append("environment_modification")

        # Check for threading/async
        if any(op in source_code for op in ["threading.", "asyncio.", "multiprocessing."]):
            side_effects.append("concurrent_execution")

        return side_effects

    def _check_concurrency_safety(self, source_code: str, side_effects: List[str]) -> bool:
        """Check if code is safe for concurrent execution"""

        # Not safe if modifies global state
        if "global_state_modification" in side_effects:
            return False

        # Check for thread-unsafe operations
        unsafe_patterns = [
            "global ",
            "__setattr__",
            "__delattr__",
            "signal.",
            "sys.modules",
        ]

        for pattern in unsafe_patterns:
            if pattern in source_code:
                return False

        # Check for proper locking
        has_locks = any(
            lock in source_code for lock in ["Lock(", "RLock(", "Semaphore(", "asyncio.Lock("]
        )

        # If has concurrent operations but no locks, not safe
        if "concurrent_execution" in side_effects and not has_locks:
            return False

        return True

    def _check_idempotency(self, metadata: CodeMetadata, source_code: str) -> bool:
        """Check if operation is idempotent"""

        # Check for non-idempotent operations
        non_idempotent = [
            ".append(",
            ".extend(",
            "+=",
            "-=",
            "*=",
            "/=",
            ".pop(",
            ".remove(",
            "random.",
            "uuid.",
            "datetime.now(",
            ".increment(",
            ".decrement(",
        ]

        for pattern in non_idempotent:
            if pattern in source_code:
                return False

        # Repository methods are often idempotent by design
        if metadata.semantic_role.value == "repository":
            # Check for specific patterns
            if any(method in metadata.name for method in ["get", "find", "fetch", "retrieve"]):
                return True

        return True

    def _is_pure_function(self, source_code: str, side_effects: List[str]) -> bool:
        """Check if function is pure (no side effects, deterministic)"""

        # Has side effects? Not pure
        if side_effects:
            return False

        # Uses random or time? Not pure
        non_pure_modules = ["random", "datetime", "time", "uuid"]
        for module in non_pure_modules:
            if module in source_code:
                return False

        # Modifies arguments? Not pure
        if any(op in source_code for op in [".append(", ".extend(", ".update("]):
            return False

        # No obvious impurities found
        return True

    def generate_batch_hints(
        self, metadata_list: List[CodeMetadata], source_codes: Dict[str, str]
    ) -> Dict[str, AIHints]:
        """Generate hints for multiple code elements efficiently"""
        results = {}

        for metadata in metadata_list:
            source = source_codes.get(metadata.path, "")
            hints = self.generate_hints(metadata, source)
            results[metadata.name] = hints

        return results

    def get_refactoring_recommendations(
        self, metadata: CodeMetadata, source_code: str
    ) -> List[RefactoringRecommendation]:
        """Get specific refactoring recommendations"""
        recommendations = []

        # Check for long methods
        lines = source_code.split("\n")
        if len(lines) > 50:
            recommendations.append(
                RefactoringRecommendation(
                    pattern="extract_method",
                    reason="Method is too long, affecting readability",
                    priority=2,
                    estimated_effort="2-4 hours",
                    breaking_change=False,
                    migration_steps=[
                        "Identify logical sections",
                        "Extract each section to separate methods",
                        "Add appropriate parameters",
                        "Update tests",
                    ],
                )
            )

        # Check for duplicate code
        # (Simple check - in production, use more sophisticated analysis)
        if source_code.count("if ") > 5:
            recommendations.append(
                RefactoringRecommendation(
                    pattern="strategy_pattern",
                    reason="Multiple conditional branches, consider strategy pattern",
                    priority=3,
                    estimated_effort="4-8 hours",
                    breaking_change=False,
                    migration_steps=[
                        "Define strategy interface",
                        "Implement concrete strategies",
                        "Replace conditionals with strategy selection",
                        "Test each strategy independently",
                    ],
                )
            )

        # Check complexity
        if metadata.complexity == ComplexityLevel.CRITICAL:
            recommendations.append(
                RefactoringRecommendation(
                    pattern="decompose_class",
                    reason="High complexity, should be broken down",
                    priority=1,
                    estimated_effort="1-2 days",
                    breaking_change=True,
                    migration_steps=[
                        "Identify responsibilities",
                        "Create new classes for each responsibility",
                        "Move relevant methods",
                        "Update dependencies",
                        "Add migration guide",
                    ],
                )
            )

        return recommendations


# Singleton instance
_generator = None


def get_hints_generator() -> AIHintsGenerator:
    """Get or create the hints generator"""
    global _generator
    if _generator is None:
        _generator = AIHintsGenerator()
    return _generator
