"""
Advanced Semantic Classifier for Meta-Tagging System

This module provides sophisticated pattern-based semantic classification for code components,
including role detection, capability identification, risk assessment, and confidence scoring.
"""

import ast
import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from re import Pattern
from typing import Any, Optional

from .meta_tagging import Complexity, ModificationRisk, Priority, SemanticRole

logger = logging.getLogger(__name__)


class AnalysisContext(Enum):
    """Context for semantic analysis."""

    FILE_NAME = "file_name"
    CLASS_NAME = "class_name"
    FUNCTION_NAME = "function_name"
    MODULE_DOCSTRING = "module_docstring"
    IMPORT_STATEMENTS = "import_statements"
    INHERITANCE = "inheritance"
    DECORATORS = "decorators"
    COMMENTS = "comments"
    CODE_STRUCTURE = "code_structure"


@dataclass
class PatternMatch:
    """Represents a pattern match with confidence scoring."""

    pattern: str
    match_text: str
    confidence: float
    context: AnalysisContext
    line_number: Optional[int] = None


@dataclass
class ClassificationResult:
    """Complete classification result with confidence metrics."""

    semantic_role: SemanticRole
    confidence: float
    primary_matches: list[PatternMatch]
    secondary_matches: list[PatternMatch]
    reasoning: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "semantic_role": self.semantic_role.value,
            "confidence": self.confidence,
            "primary_matches": [
                {
                    "pattern": m.pattern,
                    "match_text": m.match_text,
                    "confidence": m.confidence,
                    "context": m.context.value,
                }
                for m in self.primary_matches
            ],
            "reasoning": self.reasoning,
        }


class SemanticClassifier:
    """Advanced semantic classifier with pattern matching and confidence scoring."""

    def __init__(self):
        """Initialize classifier with comprehensive pattern sets."""
        # Multi-layered pattern matching with confidence weights
        self.role_patterns = self._initialize_role_patterns()
        self.capability_patterns = self._initialize_capability_patterns()
        self.complexity_indicators = self._initialize_complexity_indicators()
        self.risk_indicators = self._initialize_risk_indicators()

        # Context-specific pattern weights
        self.context_weights = {
            AnalysisContext.FILE_NAME: 0.8,
            AnalysisContext.CLASS_NAME: 0.9,
            AnalysisContext.FUNCTION_NAME: 0.7,
            AnalysisContext.MODULE_DOCSTRING: 0.6,
            AnalysisContext.IMPORT_STATEMENTS: 0.5,
            AnalysisContext.INHERITANCE: 0.8,
            AnalysisContext.DECORATORS: 0.9,
            AnalysisContext.COMMENTS: 0.4,
            AnalysisContext.CODE_STRUCTURE: 0.6,
        }

    def _initialize_role_patterns(
        self,
    ) -> dict[SemanticRole, dict[AnalysisContext, list[tuple[Pattern, float]]]]:
        """Initialize comprehensive role-based pattern matching."""

        def compile_patterns(
            patterns: list[tuple[str, float]],
        ) -> list[tuple[Pattern, float]]:
            return [
                (re.compile(pattern, re.IGNORECASE), weight)
                for pattern, weight in patterns
            ]

        return {
            SemanticRole.ORCHESTRATOR: {
                AnalysisContext.FILE_NAME: compile_patterns(
                    [
                        (r"orchestrat", 0.9),
                        (r"coordinat", 0.8),
                        (r"manage", 0.7),
                        (r"control", 0.8),
                        (r"supervisor", 0.8),
                        (r"director", 0.7),
                        (r"commander", 0.8),
                    ]
                ),
                AnalysisContext.CLASS_NAME: compile_patterns(
                    [
                        (r".*Orchestrator$", 0.95),
                        (r".*Manager$", 0.8),
                        (r".*Controller$", 0.7),
                        (r".*Coordinator$", 0.9),
                        (r".*Supervisor$", 0.8),
                    ]
                ),
                AnalysisContext.CODE_STRUCTURE: compile_patterns(
                    [
                        (r"def\s+orchestrate", 0.8),
                        (r"def\s+coordinate", 0.7),
                        (r"def\s+manage", 0.6),
                        (r"workflow|pipeline", 0.6),
                    ]
                ),
            },
            SemanticRole.PROCESSOR: {
                AnalysisContext.FILE_NAME: compile_patterns(
                    [
                        (r"process", 0.9),
                        (r"transform", 0.8),
                        (r"convert", 0.8),
                        (r"parse", 0.7),
                        (r"encode", 0.7),
                        (r"decode", 0.7),
                        (r"filter", 0.6),
                        (r"mapper", 0.7),
                    ]
                ),
                AnalysisContext.CLASS_NAME: compile_patterns(
                    [
                        (r".*Processor$", 0.95),
                        (r".*Transformer$", 0.9),
                        (r".*Converter$", 0.9),
                        (r".*Parser$", 0.8),
                        (r".*Filter$", 0.7),
                        (r".*Mapper$", 0.8),
                    ]
                ),
                AnalysisContext.CODE_STRUCTURE: compile_patterns(
                    [
                        (r"def\s+process", 0.8),
                        (r"def\s+transform", 0.8),
                        (r"def\s+convert", 0.7),
                        (r"def\s+parse", 0.7),
                    ]
                ),
            },
            SemanticRole.GATEWAY: {
                AnalysisContext.FILE_NAME: compile_patterns(
                    [
                        (r"gateway", 0.9),
                        (r"api", 0.8),
                        (r"endpoint", 0.8),
                        (r"route", 0.7),
                        (r"handler", 0.7),
                        (r"controller", 0.6),
                        (r"interface", 0.6),
                    ]
                ),
                AnalysisContext.DECORATORS: compile_patterns(
                    [
                        (r"@app\.", 0.9),
                        (r"@router\.", 0.9),
                        (r"@api\.", 0.8),
                        (r"@route", 0.8),
                        (r"@endpoint", 0.8),
                    ]
                ),
                AnalysisContext.IMPORT_STATEMENTS: compile_patterns(
                    [
                        (r"fastapi", 0.8),
                        (r"flask", 0.8),
                        (r"django", 0.7),
                        (r"APIRouter", 0.9),
                    ]
                ),
            },
            SemanticRole.AGENT: {
                AnalysisContext.FILE_NAME: compile_patterns(
                    [
                        (r"agent", 0.9),
                        (r"swarm", 0.9),
                        (r"autonomous", 0.8),
                        (r"intelligent", 0.7),
                        (r"bot", 0.6),
                        (r"ai", 0.7),
                    ]
                ),
                AnalysisContext.CLASS_NAME: compile_patterns(
                    [
                        (r".*Agent$", 0.95),
                        (r".*Swarm$", 0.9),
                        (r".*Bot$", 0.7),
                        (r"AI.*", 0.8),
                    ]
                ),
                AnalysisContext.IMPORT_STATEMENTS: compile_patterns(
                    [
                        (r"langchain", 0.8),
                        (r"openai", 0.7),
                        (r"anthropic", 0.7),
                        (r"swarms", 0.9),
                    ]
                ),
            },
            SemanticRole.MODEL: {
                AnalysisContext.FILE_NAME: compile_patterns(
                    [
                        (r"model", 0.9),
                        (r"neural", 0.8),
                        (r"ml", 0.7),
                        (r"predict", 0.7),
                        (r"inference", 0.8),
                        (r"train", 0.6),
                    ]
                ),
                AnalysisContext.CLASS_NAME: compile_patterns(
                    [(r".*Model$", 0.9), (r".*Network$", 0.7), (r".*Predictor$", 0.8)]
                ),
                AnalysisContext.IMPORT_STATEMENTS: compile_patterns(
                    [
                        (r"torch", 0.8),
                        (r"tensorflow", 0.8),
                        (r"sklearn", 0.7),
                        (r"transformers", 0.8),
                    ]
                ),
            },
            SemanticRole.REPOSITORY: {
                AnalysisContext.FILE_NAME: compile_patterns(
                    [
                        (r"repository", 0.9),
                        (r"repo", 0.8),
                        (r"storage", 0.7),
                        (r"persist", 0.7),
                        (r"database", 0.8),
                        (r"db", 0.7),
                        (r"dao", 0.8),
                    ]
                ),
                AnalysisContext.CLASS_NAME: compile_patterns(
                    [
                        (r".*Repository$", 0.95),
                        (r".*Storage$", 0.8),
                        (r".*DAO$", 0.9),
                        (r".*Store$", 0.7),
                    ]
                ),
                AnalysisContext.IMPORT_STATEMENTS: compile_patterns(
                    [
                        (r"sqlalchemy", 0.8),
                        (r"pymongo", 0.8),
                        (r"redis", 0.6),
                        (r"sqlite", 0.7),
                    ]
                ),
            },
            SemanticRole.SERVICE: {
                AnalysisContext.FILE_NAME: compile_patterns(
                    [
                        (r"service", 0.9),
                        (r"business", 0.6),
                        (r"logic", 0.5),
                        (r"operation", 0.6),
                    ]
                ),
                AnalysisContext.CLASS_NAME: compile_patterns(
                    [(r".*Service$", 0.95), (r".*Logic$", 0.7), (r".*Operations$", 0.7)]
                ),
            },
            SemanticRole.UTILITY: {
                AnalysisContext.FILE_NAME: compile_patterns(
                    [
                        (r"util", 0.9),
                        (r"helper", 0.8),
                        (r"tool", 0.7),
                        (r"common", 0.6),
                        (r"shared", 0.6),
                    ]
                ),
                AnalysisContext.CLASS_NAME: compile_patterns(
                    [(r".*Utils?$", 0.9), (r".*Helper$", 0.9), (r".*Tools?$", 0.8)]
                ),
            },
            SemanticRole.CONFIG: {
                AnalysisContext.FILE_NAME: compile_patterns(
                    [
                        (r"config", 0.9),
                        (r"settings", 0.8),
                        (r"environment", 0.6),
                        (r"\.json$", 0.7),
                        (r"\.yaml$", 0.8),
                        (r"\.yml$", 0.8),
                        (r"\.toml$", 0.7),
                    ]
                )
            },
            SemanticRole.TEST: {
                AnalysisContext.FILE_NAME: compile_patterns(
                    [
                        (r"test", 0.9),
                        (r"spec", 0.7),
                        (r"_test\.py$", 0.95),
                        (r"test_.*\.py$", 0.95),
                    ]
                ),
                AnalysisContext.IMPORT_STATEMENTS: compile_patterns(
                    [(r"pytest", 0.9), (r"unittest", 0.8), (r"mock", 0.7)]
                ),
            },
        }

    def _initialize_capability_patterns(self) -> dict[str, list[tuple[Pattern, float]]]:
        """Initialize capability detection patterns."""

        def compile_patterns(
            patterns: list[tuple[str, float]],
        ) -> list[tuple[Pattern, float]]:
            return [
                (re.compile(pattern, re.IGNORECASE), weight)
                for pattern, weight in patterns
            ]

        return {
            "async": compile_patterns(
                [
                    (r"async\s+def", 0.9),
                    (r"await\s+", 0.8),
                    (r"asyncio", 0.7),
                    (r"aiohttp", 0.7),
                ]
            ),
            "api": compile_patterns(
                [
                    (r"@app\.", 0.9),
                    (r"@router\.", 0.9),
                    (r"FastAPI", 0.8),
                    (r"APIRouter", 0.8),
                    (r"@api_route", 0.8),
                ]
            ),
            "database": compile_patterns(
                [
                    (r"database", 0.8),
                    (r"sql", 0.7),
                    (r"query", 0.6),
                    (r"transaction", 0.7),
                    (r"session", 0.5),
                ]
            ),
            "ai": compile_patterns(
                [
                    (r"model", 0.6),
                    (r"agent", 0.8),
                    (r"neural", 0.8),
                    (r"ml", 0.7),
                    (r"ai", 0.7),
                    (r"openai", 0.8),
                    (r"anthropic", 0.8),
                ]
            ),
            "caching": compile_patterns(
                [
                    (r"cache", 0.8),
                    (r"redis", 0.9),
                    (r"memcache", 0.9),
                    (r"@lru_cache", 0.8),
                ]
            ),
            "validation": compile_patterns(
                [
                    (r"valid", 0.6),
                    (r"schema", 0.7),
                    (r"pydantic", 0.9),
                    (r"BaseModel", 0.8),
                ]
            ),
            "logging": compile_patterns(
                [(r"log", 0.7), (r"logger", 0.8), (r"logging", 0.8)]
            ),
            "config": compile_patterns(
                [(r"config", 0.8), (r"settings", 0.7), (r"environment", 0.6)]
            ),
            "testing": compile_patterns(
                [(r"test", 0.8), (r"mock", 0.8), (r"assert", 0.6), (r"pytest", 0.9)]
            ),
            "security": compile_patterns(
                [
                    (r"auth", 0.8),
                    (r"security", 0.8),
                    (r"token", 0.7),
                    (r"encrypt", 0.8),
                    (r"decrypt", 0.8),
                    (r"hash", 0.6),
                ]
            ),
            "monitoring": compile_patterns(
                [
                    (r"monitor", 0.8),
                    (r"metric", 0.7),
                    (r"telemetry", 0.8),
                    (r"observability", 0.8),
                ]
            ),
            "websocket": compile_patterns(
                [(r"websocket", 0.9), (r"ws", 0.6), (r"socket\.io", 0.8)]
            ),
            "streaming": compile_patterns(
                [(r"stream", 0.7), (r"chunk", 0.6), (r"yield", 0.5)]
            ),
        }

    def _initialize_complexity_indicators(self) -> dict[str, tuple[Pattern, float]]:
        """Initialize complexity assessment patterns."""
        return {
            "high_nesting": (re.compile(r"(\s{12,})", re.MULTILINE), 0.7),
            "many_conditionals": (
                re.compile(r"\bif\b.*\belse\b.*\belif\b", re.IGNORECASE),
                0.6,
            ),
            "exception_handling": (re.compile(r"try:.*except.*:", re.DOTALL), 0.5),
            "recursion": (re.compile(r"def\s+(\w+).*\1\s*\(", re.MULTILINE), 0.8),
            "metaclasses": (re.compile(r"metaclass=", re.IGNORECASE), 0.9),
            "decorators": (re.compile(r"@\w+", re.MULTILINE), 0.4),
            "lambda_functions": (re.compile(r"lambda\s+", re.IGNORECASE), 0.3),
            "comprehensions": (re.compile(r"\[.*for.*in.*\]", re.MULTILINE), 0.3),
        }

    def _initialize_risk_indicators(self) -> dict[str, tuple[Pattern, float]]:
        """Initialize risk assessment patterns."""
        return {
            "global_state": (re.compile(r"global\s+\w+", re.IGNORECASE), 0.7),
            "exec_eval": (re.compile(r"\b(exec|eval)\s*\(", re.IGNORECASE), 0.9),
            "dynamic_imports": (
                re.compile(r"__import__|importlib", re.IGNORECASE),
                0.6,
            ),
            "file_operations": (re.compile(r"open\s*\(|file\s*=", re.IGNORECASE), 0.4),
            "network_calls": (
                re.compile(r"requests\.|urllib|http", re.IGNORECASE),
                0.5,
            ),
            "subprocess": (
                re.compile(r"subprocess|os\.system|os\.popen", re.IGNORECASE),
                0.8,
            ),
            "database_writes": (
                re.compile(r"INSERT|UPDATE|DELETE|DROP", re.IGNORECASE),
                0.6,
            ),
            "environment_vars": (re.compile(r"os\.environ|getenv", re.IGNORECASE), 0.3),
        }

    def classify_component(
        self,
        component_name: str,
        file_path: str,
        content: str,
        ast_node: Optional[ast.AST] = None,
    ) -> ClassificationResult:
        """Classify a component with comprehensive analysis."""

        # Extract analysis contexts
        contexts = self._extract_contexts(component_name, file_path, content, ast_node)

        # Pattern matching across all contexts
        all_matches = []
        role_scores = {}

        for role in SemanticRole:
            if role in self.role_patterns:
                role_matches = self._match_role_patterns(role, contexts)
                all_matches.extend(role_matches)

                # Calculate weighted score for this role
                role_score = sum(
                    match.confidence * self.context_weights[match.context]
                    for match in role_matches
                )
                role_scores[role] = role_score

        # Determine best role
        if not role_scores:
            best_role = SemanticRole.UNKNOWN
            confidence = 0.1
            primary_matches = []
            reasoning = ["No pattern matches found"]
        else:
            best_role = max(role_scores, key=role_scores.get)
            raw_confidence = role_scores[best_role]

            # Normalize confidence (assuming max possible score is around 5.0)
            confidence = min(0.95, raw_confidence / 5.0)

            # Separate primary and secondary matches
            role_matches = [
                m
                for m in all_matches
                if self._get_role_for_pattern(m.pattern) == best_role
            ]
            primary_matches = sorted(
                role_matches, key=lambda m: m.confidence, reverse=True
            )[:3]

            reasoning = self._generate_reasoning(best_role, primary_matches, contexts)

        # Get secondary matches from other roles
        secondary_matches = [
            m for m in all_matches if self._get_role_for_pattern(m.pattern) != best_role
        ]
        secondary_matches = sorted(
            secondary_matches, key=lambda m: m.confidence, reverse=True
        )[:3]

        return ClassificationResult(
            semantic_role=best_role,
            confidence=confidence,
            primary_matches=primary_matches,
            secondary_matches=secondary_matches,
            reasoning=reasoning,
        )

    def _extract_contexts(
        self,
        component_name: str,
        file_path: str,
        content: str,
        ast_node: Optional[ast.AST] = None,
    ) -> dict[AnalysisContext, str]:
        """Extract all analysis contexts from the component."""

        contexts = {
            AnalysisContext.FILE_NAME: Path(file_path).name,
            AnalysisContext.CLASS_NAME: (
                component_name
                if ast_node and isinstance(ast_node, ast.ClassDef)
                else ""
            ),
            AnalysisContext.FUNCTION_NAME: (
                component_name
                if ast_node and isinstance(ast_node, ast.FunctionDef)
                else ""
            ),
            AnalysisContext.COMMENTS: self._extract_comments(content),
            AnalysisContext.CODE_STRUCTURE: content,
        }

        # Extract module docstring
        try:
            tree = ast.parse(content)
            if (
                tree.body
                and isinstance(tree.body[0], ast.Expr)
                and isinstance(tree.body[0].value, ast.Constant)
                and isinstance(tree.body[0].value.value, str)
            ):
                contexts[AnalysisContext.MODULE_DOCSTRING] = tree.body[0].value.value
        except:
            contexts[AnalysisContext.MODULE_DOCSTRING] = ""

        # Extract import statements
        contexts[AnalysisContext.IMPORT_STATEMENTS] = self._extract_imports(content)

        # Extract inheritance info
        if ast_node and isinstance(ast_node, ast.ClassDef):
            inheritance = [
                base.id if isinstance(base, ast.Name) else str(base)
                for base in ast_node.bases
            ]
            contexts[AnalysisContext.INHERITANCE] = " ".join(inheritance)
        else:
            contexts[AnalysisContext.INHERITANCE] = ""

        # Extract decorators
        contexts[AnalysisContext.DECORATORS] = self._extract_decorators(content)

        return contexts

    def _extract_comments(self, content: str) -> str:
        """Extract all comments from content."""
        comment_lines = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                comment_lines.append(stripped[1:].strip())
        return " ".join(comment_lines)

    def _extract_imports(self, content: str) -> str:
        """Extract import statements."""
        import_lines = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                import_lines.append(stripped)
        return " ".join(import_lines)

    def _extract_decorators(self, content: str) -> str:
        """Extract decorator usage."""
        decorator_pattern = re.compile(r"@[\w.]+", re.MULTILINE)
        decorators = decorator_pattern.findall(content)
        return " ".join(decorators)

    def _match_role_patterns(
        self, role: SemanticRole, contexts: dict[AnalysisContext, str]
    ) -> list[PatternMatch]:
        """Match patterns for a specific role across all contexts."""
        matches = []

        if role not in self.role_patterns:
            return matches

        role_pattern_set = self.role_patterns[role]

        for context, text in contexts.items():
            if not text or context not in role_pattern_set:
                continue

            patterns = role_pattern_set[context]
            for pattern, weight in patterns:
                match_obj = pattern.search(text)
                if match_obj:
                    matches.append(
                        PatternMatch(
                            pattern=pattern.pattern,
                            match_text=match_obj.group(0),
                            confidence=weight,
                            context=context,
                        )
                    )

        return matches

    def _get_role_for_pattern(self, pattern_str: str) -> SemanticRole:
        """Determine which role a pattern belongs to."""
        for role, context_patterns in self.role_patterns.items():
            for _context, patterns in context_patterns.items():
                for pattern, _ in patterns:
                    if pattern.pattern == pattern_str:
                        return role
        return SemanticRole.UNKNOWN

    def _generate_reasoning(
        self,
        role: SemanticRole,
        matches: list[PatternMatch],
        contexts: dict[AnalysisContext, str],
    ) -> list[str]:
        """Generate human-readable reasoning for classification."""
        reasoning = []

        if matches:
            strongest_match = matches[0]
            reasoning.append(
                f"Strong {role.value} pattern '{strongest_match.match_text}' found in {strongest_match.context.value}"
            )

        # Add context-specific reasoning
        if role == SemanticRole.ORCHESTRATOR and any(
            "manage" in str(m.match_text).lower() for m in matches
        ):
            reasoning.append(
                "Contains management/coordination patterns typical of orchestrators"
            )

        if role == SemanticRole.AGENT and contexts[AnalysisContext.IMPORT_STATEMENTS]:
            ai_imports = ["openai", "anthropic", "langchain", "swarms"]
            found_imports = [
                imp
                for imp in ai_imports
                if imp in contexts[AnalysisContext.IMPORT_STATEMENTS].lower()
            ]
            if found_imports:
                reasoning.append(f"AI/ML imports detected: {', '.join(found_imports)}")

        if role == SemanticRole.GATEWAY and contexts[AnalysisContext.DECORATORS]:
            api_decorators = ["@app.", "@router.", "@route"]
            found_decorators = [
                dec
                for dec in api_decorators
                if dec in contexts[AnalysisContext.DECORATORS]
            ]
            if found_decorators:
                reasoning.append(f"API decorators found: {', '.join(found_decorators)}")

        return reasoning or [f"Classified as {role.value} based on pattern analysis"]

    def identify_capabilities(self, content: str) -> dict[str, float]:
        """Identify component capabilities with confidence scores."""
        capabilities = {}

        for capability, patterns in self.capability_patterns.items():
            max_confidence = 0.0

            for pattern, weight in patterns:
                if pattern.search(content):
                    max_confidence = max(max_confidence, weight)

            if max_confidence > 0.0:
                capabilities[capability] = max_confidence

        return capabilities

    def assess_complexity(
        self, content: str, ast_node: Optional[ast.AST] = None
    ) -> tuple[Complexity, float, list[str]]:
        """Assess component complexity with detailed analysis."""
        indicators = []
        total_score = 0.0

        # Pattern-based complexity indicators
        for indicator, (pattern, weight) in self.complexity_indicators.items():
            matches = pattern.findall(content)
            if matches:
                count = len(matches)
                indicator_score = weight * min(count / 5.0, 1.0)  # Normalize to max 1.0
                total_score += indicator_score
                indicators.append(f"{indicator}: {count} occurrences")

        # AST-based complexity (if available)
        if ast_node:
            ast_complexity = self._calculate_ast_complexity(ast_node)
            total_score += ast_complexity
            if ast_complexity > 0.5:
                indicators.append(f"High AST complexity: {ast_complexity:.2f}")

        # Lines of code factor
        loc = len([line for line in content.splitlines() if line.strip()])
        if loc > 100:
            loc_factor = min((loc - 100) / 500.0, 1.0)
            total_score += loc_factor
            indicators.append(f"Large codebase: {loc} lines")

        # Determine complexity level
        if total_score < 0.5:
            complexity = Complexity.TRIVIAL
        elif total_score < 1.0:
            complexity = Complexity.LOW
        elif total_score < 2.0:
            complexity = Complexity.MODERATE
        elif total_score < 3.5:
            complexity = Complexity.HIGH
        else:
            complexity = Complexity.CRITICAL

        return complexity, total_score, indicators

    def _calculate_ast_complexity(self, node: ast.AST) -> float:
        """Calculate AST-based complexity score."""
        complexity = 0.0

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 0.1
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity += 0.05
            elif isinstance(child, (ast.ClassDef, ast.ExceptHandler)):
                complexity += 0.1
            elif isinstance(child, ast.BoolOp):
                complexity += 0.05 * (len(child.values) - 1)

        return complexity

    def assess_risk(
        self, content: str, contexts: dict[AnalysisContext, str]
    ) -> tuple[ModificationRisk, float, list[str]]:
        """Assess modification risk with detailed analysis."""
        risk_factors = []
        total_risk = 0.0

        # Pattern-based risk indicators
        for indicator, (pattern, weight) in self.risk_indicators.items():
            if pattern.search(content):
                total_risk += weight
                risk_factors.append(f"Contains {indicator}")

        # Context-based risk factors
        if "core" in contexts[AnalysisContext.FILE_NAME].lower():
            total_risk += 0.5
            risk_factors.append("Core system component")

        if "main" in contexts[AnalysisContext.FILE_NAME].lower():
            total_risk += 0.3
            risk_factors.append("Main module")

        # Import-based risk
        risky_imports = ["os", "sys", "subprocess", "pickle", "__import__"]
        imports_text = contexts.get(AnalysisContext.IMPORT_STATEMENTS, "").lower()
        for risky_import in risky_imports:
            if risky_import in imports_text:
                total_risk += 0.2
                risk_factors.append(f"Uses risky import: {risky_import}")

        # Determine risk level
        if total_risk < 0.5:
            risk = ModificationRisk.SAFE
        elif total_risk < 1.0:
            risk = ModificationRisk.MODERATE
        elif total_risk < 2.0:
            risk = ModificationRisk.HIGH
        else:
            risk = ModificationRisk.CRITICAL

        return risk, total_risk, risk_factors

    def generate_priority(
        self,
        semantic_role: SemanticRole,
        complexity: Complexity,
        risk: ModificationRisk,
        capabilities: dict[str, float],
    ) -> tuple[Priority, list[str]]:
        """Generate priority level with reasoning."""
        priority_score = 0.0
        reasoning = []

        # Role-based priority
        high_priority_roles = [
            SemanticRole.ORCHESTRATOR,
            SemanticRole.GATEWAY,
            SemanticRole.AGENT,
        ]
        if semantic_role in high_priority_roles:
            priority_score += 1.0
            reasoning.append(f"{semantic_role.value} is high-priority role")

        # Complexity factor
        if complexity.value >= Complexity.HIGH.value:
            priority_score += 0.5
            reasoning.append("High complexity requires attention")

        # Risk factor
        if risk.value >= ModificationRisk.HIGH.value:
            priority_score += 0.7
            reasoning.append("High modification risk")

        # Capability-based priority
        critical_capabilities = ["security", "database", "api"]
        for cap in critical_capabilities:
            if cap in capabilities and capabilities[cap] > 0.7:
                priority_score += 0.3
                reasoning.append(f"Critical capability: {cap}")

        # Determine priority level
        if priority_score < 0.5:
            priority = Priority.LOW
        elif priority_score < 1.0:
            priority = Priority.MEDIUM
        elif priority_score < 1.8:
            priority = Priority.HIGH
        else:
            priority = Priority.CRITICAL

        return priority, reasoning

    def enhanced_classify(
        self,
        component_name: str,
        file_path: str,
        content: str,
        ast_node: Optional[ast.AST] = None,
    ) -> dict[str, Any]:
        """Perform comprehensive classification with all metrics."""

        # Extract contexts
        contexts = self._extract_contexts(component_name, file_path, content, ast_node)

        # Primary classification
        classification = self.classify_component(
            component_name, file_path, content, ast_node
        )

        # Capability identification
        capabilities = self.identify_capabilities(content)

        # Complexity assessment
        complexity, complexity_score, complexity_indicators = self.assess_complexity(
            content, ast_node
        )

        # Risk assessment
        risk, risk_score, risk_factors = self.assess_risk(content, contexts)

        # Priority generation
        priority, priority_reasoning = self.generate_priority(
            classification.semantic_role, complexity, risk, capabilities
        )

        return {
            "classification": classification.to_dict(),
            "capabilities": capabilities,
            "complexity": {
                "level": complexity.value,
                "score": complexity_score,
                "indicators": complexity_indicators,
            },
            "risk": {"level": risk.value, "score": risk_score, "factors": risk_factors},
            "priority": {"level": priority.value, "reasoning": priority_reasoning},
            "contexts": {ctx.value: text for ctx, text in contexts.items()},
            "overall_confidence": classification.confidence,
        }


# Utility functions for external use
def quick_classify(component_name: str, file_path: str, content: str) -> SemanticRole:
    """Quick classification for simple use cases."""
    classifier = SemanticClassifier()
    result = classifier.classify_component(component_name, file_path, content)
    return result.semantic_role


def detailed_analysis(
    component_name: str,
    file_path: str,
    content: str,
    ast_node: Optional[ast.AST] = None,
) -> dict[str, Any]:
    """Comprehensive analysis for detailed insights."""
    classifier = SemanticClassifier()
    return classifier.enhanced_classify(component_name, file_path, content, ast_node)


if __name__ == "__main__":
    # Example usage
    sample_code = '''
    import asyncio
    from fastapi import FastAPI, APIRouter

    class UserOrchestrator:
        """Orchestrates user management operations."""

        def __init__(self):
            self.app = FastAPI()

        async def coordinate_user_creation(self, user_data):
            # Complex orchestration logic
            result = await self.process_user_data(user_data)
            return result
    '''

    result = detailed_analysis("UserOrchestrator", "user_orchestrator.py", sample_code)
    print("Classification Result:")
    print(f"Role: {result['classification']['semantic_role']}")
    print(f"Confidence: {result['classification']['confidence']:.2f}")
    print(f"Capabilities: {list(result['capabilities'].keys())}")
    print(f"Complexity: {result['complexity']['level']}")
    print(f"Risk: {result['risk']['level']}")
    print(f"Priority: {result['priority']['level']}")
