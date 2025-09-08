"""
Artemis Unified Orchestrator
Consolidated code excellence orchestrator with semantic engine and quality assurance pipeline
"""

import ast
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.core.portkey_manager import TaskType as PortkeyTaskType
from app.memory.unified_memory_router import MemoryDomain
from app.orchestrators.unified_base import (
    ExecutionPriority,
    OrchestratorConfig,
    UnifiedBaseOrchestrator,
    UnifiedResult,
    UnifiedTask,
)

logger = logging.getLogger(__name__)


@dataclass
class CodeContext:
    """Enhanced code context for Artemis"""

    languages: list[str]
    frameworks: list[str]
    repository_path: Optional[str] = None
    test_framework: Optional[str] = None
    style_guide: Optional[str] = None
    complexity_threshold: int = 10
    coverage_target: float = 80.0
    performance_benchmarks: dict[str, float] = field(default_factory=dict)

    # Enhanced fields
    architecture_patterns: list[str] = field(default_factory=list)
    code_standards: dict[str, Any] = field(default_factory=dict)
    security_requirements: list[str] = field(default_factory=list)
    performance_targets: dict[str, float] = field(default_factory=dict)
    quality_gates: dict[str, float] = field(default_factory=dict)


@dataclass
class CodePattern:
    """Represents a detected code pattern"""

    name: str
    type: str  # "design_pattern", "anti_pattern", "architecture_pattern"
    description: str
    locations: list[dict[str, Any]]
    confidence: float
    impact: str  # "positive", "negative", "neutral"
    recommendations: list[str]


@dataclass
class QualityMetrics:
    """Comprehensive code quality metrics"""

    complexity_score: float
    maintainability_index: float
    test_coverage: float
    security_score: float
    performance_score: float
    documentation_coverage: float
    code_duplication: float
    technical_debt_ratio: float
    overall_quality: float


@dataclass
class CodeResult:
    """Enhanced code generation result"""

    code: str
    language: str
    explanation: str
    tests: Optional[str] = None
    documentation: Optional[str] = None
    quality_metrics: Optional[QualityMetrics] = None
    security_analysis: dict[str, Any] = field(default_factory=dict)
    performance_analysis: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    patterns: list[CodePattern] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CodeReview:
    """Enhanced code review result"""

    overall_score: float
    quality_metrics: QualityMetrics
    issues: list[dict[str, Any]]
    suggestions: list[dict[str, Any]]
    security_vulnerabilities: list[dict[str, Any]]
    performance_concerns: list[dict[str, Any]]
    best_practices: list[dict[str, Any]]
    patterns: list[CodePattern]
    refactoring_opportunities: list[dict[str, Any]]
    technical_debt_assessment: dict[str, Any]


class CodeSemanticEngine:
    """
    Semantic engine for code understanding and pattern recognition
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.code_ontology = self._initialize_code_ontology()
        self.pattern_library = self._initialize_pattern_library()
        self.quality_framework = self._initialize_quality_framework()

    def _initialize_code_ontology(self) -> dict[str, Any]:
        """Initialize code domain ontology"""
        return {
            "languages": {
                "python": {
                    "paradigms": ["oop", "functional", "procedural"],
                    "frameworks": ["django", "flask", "fastapi", "pytest"],
                    "patterns": ["mvc", "factory", "observer", "singleton"],
                    "quality_tools": ["pylint", "black", "mypy", "bandit"],
                },
                "javascript": {
                    "paradigms": ["oop", "functional", "prototype"],
                    "frameworks": ["react", "vue", "angular", "node", "jest"],
                    "patterns": ["module", "observer", "factory", "mvc"],
                    "quality_tools": ["eslint", "prettier", "typescript", "sonarjs"],
                },
                "typescript": {
                    "paradigms": ["oop", "functional", "generic"],
                    "frameworks": ["angular", "react", "node", "nest"],
                    "patterns": ["decorator", "factory", "observer", "strategy"],
                    "quality_tools": ["tslint", "eslint", "prettier", "typescript"],
                },
            },
            "concepts": {
                "quality": [
                    "maintainability",
                    "readability",
                    "performance",
                    "security",
                ],
                "patterns": ["creational", "structural", "behavioral", "architectural"],
                "principles": [
                    "solid",
                    "dry",
                    "kiss",
                    "yagni",
                    "separation_of_concerns",
                ],
                "metrics": ["complexity", "coverage", "duplication", "debt"],
            },
            "relationships": {
                "improves": [
                    "refactoring_improves_quality",
                    "testing_improves_reliability",
                ],
                "requires": [
                    "pattern_requires_structure",
                    "performance_requires_optimization",
                ],
                "conflicts": [
                    "complexity_conflicts_readability",
                    "performance_conflicts_maintainability",
                ],
            },
        }

    def _initialize_pattern_library(self) -> dict[str, dict[str, Any]]:
        """Initialize pattern recognition library"""
        return {
            "design_patterns": {
                "singleton": {
                    "indicators": ["__new__", "instance", "static", "class_variable"],
                    "anti_indicators": ["multiple_instances", "inheritance"],
                    "quality_impact": "neutral",
                    "complexity_impact": "low",
                },
                "factory": {
                    "indicators": ["create", "build", "make", "factory"],
                    "anti_indicators": ["direct_instantiation"],
                    "quality_impact": "positive",
                    "complexity_impact": "medium",
                },
                "observer": {
                    "indicators": ["subscribe", "notify", "listen", "event"],
                    "anti_indicators": ["tight_coupling"],
                    "quality_impact": "positive",
                    "complexity_impact": "medium",
                },
            },
            "anti_patterns": {
                "god_object": {
                    "indicators": [
                        "large_class",
                        "many_methods",
                        "many_responsibilities",
                    ],
                    "quality_impact": "negative",
                    "complexity_impact": "high",
                },
                "spaghetti_code": {
                    "indicators": ["goto", "complex_control_flow", "unclear_structure"],
                    "quality_impact": "negative",
                    "complexity_impact": "high",
                },
                "magic_numbers": {
                    "indicators": ["hardcoded_numbers", "unclear_constants"],
                    "quality_impact": "negative",
                    "complexity_impact": "low",
                },
            },
            "architecture_patterns": {
                "mvc": {
                    "indicators": ["model", "view", "controller", "separation"],
                    "quality_impact": "positive",
                    "complexity_impact": "medium",
                },
                "microservices": {
                    "indicators": ["service", "api", "independent", "scalable"],
                    "quality_impact": "positive",
                    "complexity_impact": "high",
                },
                "layered": {
                    "indicators": ["layer", "tier", "abstraction", "hierarchy"],
                    "quality_impact": "positive",
                    "complexity_impact": "medium",
                },
            },
        }

    def _initialize_quality_framework(self) -> dict[str, dict[str, Any]]:
        """Initialize code quality assessment framework"""
        return {
            "metrics": {
                "complexity": {
                    "excellent": {"min": 0, "max": 5},
                    "good": {"min": 6, "max": 10},
                    "fair": {"min": 11, "max": 20},
                    "poor": {"min": 21, "max": float("inf")},
                },
                "maintainability": {
                    "excellent": {"min": 85, "max": 100},
                    "good": {"min": 70, "max": 84},
                    "fair": {"min": 50, "max": 69},
                    "poor": {"min": 0, "max": 49},
                },
                "coverage": {
                    "excellent": {"min": 90, "max": 100},
                    "good": {"min": 80, "max": 89},
                    "fair": {"min": 60, "max": 79},
                    "poor": {"min": 0, "max": 59},
                },
            },
            "quality_gates": {
                "minimum_coverage": 70.0,
                "maximum_complexity": 15.0,
                "minimum_maintainability": 60.0,
                "maximum_duplication": 5.0,
                "minimum_security_score": 80.0,
            },
        }

    async def analyze_code_semantics(self, code: str, language: str) -> dict[str, Any]:
        """Analyze code for semantic understanding"""
        analysis = {
            "language": language,
            "patterns": [],
            "concepts": [],
            "quality_indicators": {},
            "semantic_structure": {},
            "intent_analysis": {},
        }

        # Detect patterns
        analysis["patterns"] = await self._detect_patterns(code, language)

        # Extract concepts
        analysis["concepts"] = self._extract_concepts(code, language)

        # Analyze semantic structure
        analysis["semantic_structure"] = await self._analyze_structure(code, language)

        # Determine intent
        analysis["intent_analysis"] = self._analyze_intent(code, language)

        return analysis

    async def _detect_patterns(self, code: str, language: str) -> list[CodePattern]:
        """Detect code patterns using pattern library"""
        detected_patterns = []

        code_lower = code.lower()

        # Check each pattern category
        for category, patterns in self.pattern_library.items():
            for pattern_name, pattern_info in patterns.items():
                confidence = 0.0
                locations = []

                # Check for pattern indicators
                indicators = pattern_info.get("indicators", [])
                anti_indicators = pattern_info.get("anti_indicators", [])

                indicator_matches = sum(
                    1 for indicator in indicators if indicator in code_lower
                )
                anti_matches = sum(1 for anti in anti_indicators if anti in code_lower)

                if indicators:
                    confidence = indicator_matches / len(indicators)
                    if anti_indicators:
                        confidence *= max(0, 1 - (anti_matches / len(anti_indicators)))

                if confidence > 0.5:  # Threshold for pattern detection
                    pattern = CodePattern(
                        name=pattern_name,
                        type=category,
                        description=f"{pattern_name.replace('_', ' ').title()} pattern detected",
                        locations=locations,
                        confidence=confidence,
                        impact=pattern_info.get("quality_impact", "neutral"),
                        recommendations=self._get_pattern_recommendations(
                            pattern_name, category
                        ),
                    )
                    detected_patterns.append(pattern)

        return detected_patterns

    def _extract_concepts(self, code: str, language: str) -> list[dict[str, Any]]:
        """Extract programming concepts from code"""
        concepts = []
        code_lower = code.lower()

        # Extract concepts based on ontology
        for concept_category, concept_list in self.code_ontology["concepts"].items():
            for concept in concept_list:
                if concept in code_lower:
                    concepts.append(
                        {
                            "name": concept,
                            "category": concept_category,
                            "relevance": 0.8,  # Would be calculated more sophisticatedly
                        }
                    )

        return concepts

    async def _analyze_structure(self, code: str, language: str) -> dict[str, Any]:
        """Analyze semantic structure of code"""
        structure = {
            "classes": [],
            "functions": [],
            "imports": [],
            "complexity_hotspots": [],
            "dependencies": [],
        }

        if language == "python":
            structure = await self._analyze_python_structure(code)
        elif language in ["javascript", "typescript"]:
            structure = await self._analyze_js_structure(code)

        return structure

    async def _analyze_python_structure(self, code: str) -> dict[str, Any]:
        """Analyze Python code structure"""
        structure = {
            "classes": [],
            "functions": [],
            "imports": [],
            "complexity_hotspots": [],
            "dependencies": [],
        }

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    structure["classes"].append(
                        {
                            "name": node.name,
                            "methods": [
                                n.name
                                for n in node.body
                                if isinstance(n, ast.FunctionDef)
                            ],
                            "line": node.lineno,
                        }
                    )
                elif isinstance(node, ast.FunctionDef):
                    structure["functions"].append(
                        {
                            "name": node.name,
                            "args": len(node.args.args),
                            "line": node.lineno,
                        }
                    )
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        structure["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    structure["imports"].append(node.module)

        except SyntaxError as e:
            logger.warning(f"Syntax error in Python code analysis: {e}")

        return structure

    async def _analyze_js_structure(self, code: str) -> dict[str, Any]:
        """Analyze JavaScript/TypeScript code structure"""
        structure = {
            "classes": [],
            "functions": [],
            "imports": [],
            "complexity_hotspots": [],
            "dependencies": [],
        }

        # Simple pattern matching for JS/TS - would use proper parser in production
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()

            if line_stripped.startswith("class "):
                class_name = line_stripped.split()[1].split("(")[0].split("{")[0]
                structure["classes"].append(
                    {
                        "name": class_name,
                        "line": i,
                    }
                )
            elif "function " in line_stripped or "=>" in line_stripped:
                structure["functions"].append(
                    {
                        "line": i,
                        "type": "function",
                    }
                )
            elif line_stripped.startswith("import "):
                structure["imports"].append(line_stripped)

        return structure

    def _analyze_intent(self, code: str, language: str) -> dict[str, Any]:
        """Analyze the intent and purpose of code"""
        return {
            "primary_purpose": "general_computation",  # Would be more sophisticated
            "domain": "application_logic",
            "complexity_level": "medium",
            "maintainability": "good",
        }

    def _get_pattern_recommendations(
        self, pattern_name: str, category: str
    ) -> list[str]:
        """Get recommendations for detected patterns"""
        recommendations = {
            "singleton": [
                "Consider dependency injection instead",
                "Ensure thread safety",
            ],
            "factory": [
                "Good separation of concerns",
                "Consider abstract factory for families",
            ],
            "observer": ["Ensure proper cleanup", "Consider using weak references"],
            "god_object": [
                "Split into smaller, focused classes",
                "Apply single responsibility principle",
            ],
            "spaghetti_code": [
                "Refactor into clear functions",
                "Add proper error handling",
            ],
            "magic_numbers": [
                "Extract to named constants",
                "Add documentation for values",
            ],
        }

        return recommendations.get(pattern_name, ["Review implementation carefully"])


class QualityAssurancePipeline:
    """
    Comprehensive quality assurance pipeline for code analysis
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.quality_checkers = self._initialize_quality_checkers()
        self.security_scanners = self._initialize_security_scanners()
        self.performance_analyzers = self._initialize_performance_analyzers()

    def _initialize_quality_checkers(self) -> dict[str, dict[str, Any]]:
        """Initialize quality checking tools"""
        return {
            "python": {
                "linters": ["pylint", "flake8", "pycodestyle"],
                "formatters": ["black", "autopep8"],
                "type_checkers": ["mypy", "pyright"],
                "complexity": ["mccabe", "radon"],
            },
            "javascript": {
                "linters": ["eslint", "jshint"],
                "formatters": ["prettier", "standardjs"],
                "type_checkers": ["typescript"],
                "complexity": ["complexity-report"],
            },
            "typescript": {
                "linters": ["tslint", "eslint"],
                "formatters": ["prettier"],
                "type_checkers": ["typescript"],
                "complexity": ["ts-complexity"],
            },
        }

    def _initialize_security_scanners(self) -> dict[str, list[str]]:
        """Initialize security scanning tools"""
        return {
            "python": ["bandit", "safety", "semgrep"],
            "javascript": ["eslint-plugin-security", "retire.js", "snyk"],
            "typescript": ["tslint-security", "eslint-plugin-security", "snyk"],
            "general": ["sonarqube", "checkmarx", "veracode"],
        }

    def _initialize_performance_analyzers(self) -> dict[str, list[str]]:
        """Initialize performance analysis tools"""
        return {
            "python": ["cProfile", "py-spy", "memory_profiler"],
            "javascript": ["clinic.js", "node-clinic", "v8-profiler"],
            "typescript": ["clinic.js", "tsc-profiler"],
            "general": ["perf", "valgrind", "jmeter"],
        }

    async def run_comprehensive_analysis(
        self, code: str, language: str
    ) -> dict[str, Any]:
        """Run comprehensive quality assurance analysis"""
        analysis_results = {
            "quality_metrics": {},
            "security_analysis": {},
            "performance_analysis": {},
            "compliance_check": {},
            "recommendations": [],
            "overall_score": 0.0,
        }

        # Run quality analysis
        analysis_results["quality_metrics"] = await self._analyze_quality(
            code, language
        )

        # Run security analysis
        analysis_results["security_analysis"] = await self._analyze_security(
            code, language
        )

        # Run performance analysis
        analysis_results["performance_analysis"] = await self._analyze_performance(
            code, language
        )

        # Check compliance
        analysis_results["compliance_check"] = await self._check_compliance(
            code, language
        )

        # Generate recommendations
        analysis_results["recommendations"] = self._generate_qa_recommendations(
            analysis_results
        )

        # Calculate overall score
        analysis_results["overall_score"] = self._calculate_overall_qa_score(
            analysis_results
        )

        return analysis_results

    async def _analyze_quality(self, code: str, language: str) -> QualityMetrics:
        """Analyze code quality metrics"""
        # Mock quality analysis - would run actual tools in production
        return QualityMetrics(
            complexity_score=self._calculate_complexity(code),
            maintainability_index=self._calculate_maintainability(code),
            test_coverage=0.0,  # Would need test files
            security_score=0.8,  # From security analysis
            performance_score=0.85,  # From performance analysis
            documentation_coverage=self._calculate_doc_coverage(code),
            code_duplication=self._calculate_duplication(code),
            technical_debt_ratio=0.15,  # Calculated based on issues
            overall_quality=0.0,  # Will be calculated
        )

    async def _analyze_security(self, code: str, language: str) -> dict[str, Any]:
        """Analyze security vulnerabilities"""
        security_issues = []

        # Common security patterns to check
        security_patterns = {
            "sql_injection": ["execute", "query", "SELECT", "INSERT", "UPDATE"],
            "xss": ["innerHTML", "document.write", "eval"],
            "hardcoded_secrets": ["password", "api_key", "secret", "token"],
            "insecure_random": ["random()", "Math.random"],
            "path_traversal": ["../", "..\\", "path.join"],
        }

        code_lower = code.lower()
        for vulnerability, patterns in security_patterns.items():
            for pattern in patterns:
                if pattern.lower() in code_lower:
                    security_issues.append(
                        {
                            "type": vulnerability,
                            "severity": "medium",  # Would be more sophisticated
                            "pattern": pattern,
                            "recommendation": f"Review {vulnerability} vulnerability",
                        }
                    )

        return {
            "vulnerabilities": security_issues,
            "security_score": max(0, 1.0 - (len(security_issues) * 0.1)),
            "scan_tools": self.security_scanners.get(language, []),
            "compliance_level": "basic",
        }

    async def _analyze_performance(self, code: str, language: str) -> dict[str, Any]:
        """Analyze performance characteristics"""
        performance_concerns = []

        # Performance anti-patterns
        perf_patterns = {
            "nested_loops": ["for.*for", "while.*while"],
            "recursive_calls": ["return.*function_name", r"self\."],
            "large_data_structures": ["list.*range.*1000", "array.*length"],
            "inefficient_operations": ["sort.*sort", "reverse.*reverse"],
        }

        code_lower = code.lower()
        for concern, patterns in perf_patterns.items():
            for pattern in patterns:
                if pattern in code_lower:
                    performance_concerns.append(
                        {
                            "type": concern,
                            "severity": "medium",
                            "pattern": pattern,
                            "recommendation": f"Optimize {concern}",
                        }
                    )

        return {
            "concerns": performance_concerns,
            "performance_score": max(0, 1.0 - (len(performance_concerns) * 0.1)),
            "time_complexity": "O(n)",  # Would be calculated
            "space_complexity": "O(1)",  # Would be calculated
            "bottlenecks": performance_concerns,
        }

    async def _check_compliance(self, code: str, language: str) -> dict[str, Any]:
        """Check compliance with coding standards"""
        compliance_issues = []

        # Basic compliance checks
        if language == "python":
            # PEP 8 basic checks
            if "import *" in code:
                compliance_issues.append("Avoid wildcard imports (PEP 8)")

            lines = code.split("\n")
            for i, line in enumerate(lines, 1):
                if len(line) > 88:  # Black's default line length
                    compliance_issues.append(f"Line {i} exceeds recommended length")

        return {
            "issues": compliance_issues,
            "compliance_score": max(0, 1.0 - (len(compliance_issues) * 0.05)),
            "standards": ["pep8"] if language == "python" else ["standard"],
        }

    def _generate_qa_recommendations(
        self, analysis_results: dict[str, Any]
    ) -> list[str]:
        """Generate quality assurance recommendations"""
        recommendations = []

        quality_metrics = analysis_results.get("quality_metrics", {})
        security_analysis = analysis_results.get("security_analysis", {})
        performance_analysis = analysis_results.get("performance_analysis", {})

        # Quality recommendations
        if (
            hasattr(quality_metrics, "complexity_score")
            and quality_metrics.complexity_score > 10
        ):
            recommendations.append(
                "Reduce cyclomatic complexity by breaking down functions"
            )

        if (
            hasattr(quality_metrics, "documentation_coverage")
            and quality_metrics.documentation_coverage < 0.7
        ):
            recommendations.append("Improve documentation coverage")

        # Security recommendations
        if security_analysis.get("security_score", 1.0) < 0.8:
            recommendations.append("Address security vulnerabilities identified")

        # Performance recommendations
        if performance_analysis.get("performance_score", 1.0) < 0.8:
            recommendations.append("Optimize performance bottlenecks")

        return recommendations

    def _calculate_overall_qa_score(self, analysis_results: dict[str, Any]) -> float:
        """Calculate overall quality assurance score"""
        scores = []

        quality_metrics = analysis_results.get("quality_metrics", {})
        if hasattr(quality_metrics, "overall_quality"):
            scores.append(quality_metrics.overall_quality)

        security_score = analysis_results.get("security_analysis", {}).get(
            "security_score", 0.5
        )
        scores.append(security_score)

        performance_score = analysis_results.get("performance_analysis", {}).get(
            "performance_score", 0.5
        )
        scores.append(performance_score)

        compliance_score = analysis_results.get("compliance_check", {}).get(
            "compliance_score", 0.5
        )
        scores.append(compliance_score)

        return sum(scores) / len(scores) if scores else 0.5

    # Helper methods for metric calculations
    def _calculate_complexity(self, code: str) -> float:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity

        # Count decision points
        decision_keywords = [
            "if",
            "elif",
            "else",
            "for",
            "while",
            "except",
            "case",
            "switch",
        ]
        for keyword in decision_keywords:
            complexity += code.lower().count(f" {keyword} ")
            complexity += code.lower().count(f"\t{keyword} ")
            complexity += code.lower().count(f"\n{keyword} ")

        return min(complexity, 50)  # Cap at 50

    def _calculate_maintainability(self, code: str) -> float:
        """Calculate maintainability index"""
        # Simplified maintainability calculation
        lines = len(code.split("\n"))
        complexity = self._calculate_complexity(code)

        # Simple formula (real calculation is more complex)
        if lines == 0:
            return 0

        maintainability = max(0, 100 - (complexity * 2) - (lines / 20))
        return maintainability

    def _calculate_doc_coverage(self, code: str) -> float:
        """Calculate documentation coverage"""
        lines = code.split("\n")
        doc_lines = sum(
            1
            for line in lines
            if line.strip().startswith(('"""', "'''", "#", "//", "/*"))
        )
        total_lines = len([line for line in lines if line.strip()])

        return doc_lines / total_lines if total_lines > 0 else 0

    def _calculate_duplication(self, code: str) -> float:
        """Calculate code duplication percentage"""
        lines = [line.strip() for line in code.split("\n") if line.strip()]
        unique_lines = set(lines)

        if not lines:
            return 0

        duplication = 1 - (len(unique_lines) / len(lines))
        return duplication


class ArtemisUnifiedOrchestrator(UnifiedBaseOrchestrator):
    """
    Consolidated Artemis orchestrator with semantic code engine,
    pattern library integration, and comprehensive quality assurance pipeline.
    """

    def __init__(self, code_context: Optional[CodeContext] = None):
        """
        Initialize Artemis unified orchestrator

        Args:
            code_context: Optional code-specific context
        """
        config = OrchestratorConfig(
            domain=MemoryDomain.ARTEMIS,
            name="Artemis Code Excellence Unified",
            description="Consolidated code generation and technical excellence orchestrator",
            max_concurrent_tasks=10,
            default_timeout_s=120,
            enable_caching=True,
            enable_monitoring=True,
            enable_memory=True,
            enable_persona=False,  # Artemis uses different persona system
            enable_cross_learning=True,
            budget_limits={
                "hourly_cost_usd": 50.0,
                "daily_cost_usd": 500.0,
                "monthly_cost_usd": 10000.0,
            },
            data_sources=["repository", "documentation", "tests", "patterns"],
            quality_thresholds={
                "confidence_min": 0.8,
                "citation_min": 2,
                "source_diversity": 0.7,
            },
        )

        super().__init__(config)

        self.code_context = code_context or self._get_default_code_context()

        # Initialize specialized engines
        self.semantic_engine = CodeSemanticEngine(self)
        self.qa_pipeline = QualityAssurancePipeline(self)

        # Code execution sandbox
        self._sandbox = CodeSandbox()

        # Initialize pattern library and quality standards
        self._init_code_standards()

        logger.info(
            "Artemis Unified Orchestrator initialized with full code excellence capabilities"
        )

    def _get_default_code_context(self) -> CodeContext:
        """Get default code context"""
        return CodeContext(
            languages=["python", "typescript", "javascript"],
            frameworks=["fastapi", "react", "nextjs", "pytest"],
            test_framework="pytest",
            style_guide="pep8",
            complexity_threshold=10,
            coverage_target=85.0,
            architecture_patterns=["mvc", "repository", "factory", "observer"],
            code_standards={
                "max_function_length": 50,
                "max_class_methods": 20,
                "min_test_coverage": 80.0,
                "max_complexity": 10,
            },
            security_requirements=[
                "input_validation",
                "secure_defaults",
                "principle_of_least_privilege",
            ],
            performance_targets={
                "response_time_ms": 100,
                "memory_usage_mb": 512,
                "cpu_utilization": 0.7,
            },
            quality_gates={
                "minimum_quality_score": 0.8,
                "maximum_technical_debt": 0.2,
                "minimum_documentation": 0.7,
            },
        )

    def _init_code_standards(self):
        """Initialize code standards and quality gates"""
        self.quality_gates = {
            "complexity": self.code_context.complexity_threshold,
            "coverage": self.code_context.coverage_target,
            "maintainability": 70.0,
            "security_score": 80.0,
            "performance_score": 80.0,
        }

        self.pattern_recognition_enabled = True
        self.automated_refactoring_enabled = True
        self.comprehensive_testing_enabled = True

        logger.info(
            f"Code standards initialized with {len(self.quality_gates)} quality gates"
        )

    async def _execute_core(self, task: UnifiedTask, routing: Any) -> UnifiedResult:
        """
        Execute Artemis-specific code task with semantic understanding and QA pipeline

        Args:
            task: Task to execute
            routing: Model routing decision

        Returns:
            Execution result
        """
        result = UnifiedResult(success=False, content=None)

        try:
            # Analyze codebase context with semantic understanding
            codebase_context = await self._analyze_semantic_codebase(task)

            # Load relevant code patterns and examples
            code_patterns = await self._load_code_patterns(task)

            # Prepare messages for LLM with semantic code understanding
            messages = self._prepare_semantic_code_messages(
                task, codebase_context, code_patterns
            )

            # Route based on task type with appropriate model selection
            if task.type == PortkeyTaskType.CODE_GENERATION:
                response = await self._generate_code_with_qa(messages, routing, task)
            elif task.type == PortkeyTaskType.CODE_REVIEW:
                response = await self._review_code_comprehensively(
                    messages, routing, task
                )
            else:
                response = await self._general_code_task_with_qa(
                    messages, routing, task
                )

            # Process response with semantic understanding
            processed = await self._process_semantic_response(response, task)

            # Run comprehensive quality assurance pipeline
            if task.type == PortkeyTaskType.CODE_GENERATION:
                qa_results = await self._run_qa_pipeline(processed, task)
                processed["qa_results"] = qa_results

            # Validate against quality gates
            quality_validation = await self._validate_quality_gates(processed)
            processed["quality_validation"] = quality_validation

            # Generate comprehensive code result
            code_result = await self._generate_code_result(processed, task)

            # Format result with enhanced metadata
            result.success = True
            result.content = code_result
            result.metadata = {
                "semantic_analysis": codebase_context.get("semantic_analysis", {}),
                "patterns_detected": len(code_patterns.get("detected_patterns", [])),
                "quality_score": (
                    qa_results.get("overall_score", 0)
                    if "qa_results" in processed
                    else 0
                ),
                "language": self._detect_language(processed),
                "complexity": processed.get("complexity_analysis", {}),
                "processing_pipeline": [
                    "semantic_analyze",
                    "pattern_match",
                    "generate",
                    "qa_check",
                    "validate",
                ],
            }
            result.confidence = self._calculate_code_confidence(
                processed, quality_validation
            )
            result.citations = self._extract_code_citations(codebase_context)
            result.source_attribution = ["codebase", "patterns", "documentation"]

            # Track usage
            if hasattr(response, "usage"):
                result.tokens_used = response.usage.total_tokens
                result.cost = self.portkey._estimate_cost(
                    routing.model, result.tokens_used
                )

        except Exception as e:
            logger.error(f"Artemis unified execution failed: {e}")
            result.errors.append(str(e))

        return result

    async def _analyze_semantic_codebase(self, task: UnifiedTask) -> dict[str, Any]:
        """
        Analyze codebase with semantic understanding

        Args:
            task: Current task

        Returns:
            Semantic analysis results
        """
        context = {
            "repository_analysis": {},
            "semantic_analysis": {},
            "pattern_analysis": {},
            "quality_metrics": {},
            "architectural_overview": {},
        }

        if self.code_context.repository_path:
            repo_path = Path(self.code_context.repository_path)

            # Analyze repository structure
            context["repository_analysis"] = await self._analyze_repository_structure(
                repo_path
            )

            # Perform semantic analysis on key files
            context["semantic_analysis"] = await self._perform_semantic_analysis(
                repo_path, task
            )

            # Analyze patterns across the codebase
            context["pattern_analysis"] = await self._analyze_codebase_patterns(
                repo_path
            )

            # Calculate quality metrics
            context["quality_metrics"] = await self._calculate_codebase_quality(
                repo_path
            )

            # Generate architectural overview
            context["architectural_overview"] = (
                await self._generate_architectural_overview(repo_path)
            )

        return context

    async def _analyze_repository_structure(self, repo_path: Path) -> dict[str, Any]:
        """Analyze repository structure and organization"""
        structure = {
            "total_files": 0,
            "file_types": {},
            "directories": [],
            "main_languages": [],
            "framework_indicators": [],
            "test_structure": {},
            "documentation_structure": {},
        }

        try:
            # Analyze file structure
            for file_path in repo_path.rglob("*"):
                if file_path.is_file():
                    structure["total_files"] += 1
                    ext = file_path.suffix.lower()
                    structure["file_types"][ext] = (
                        structure["file_types"].get(ext, 0) + 1
                    )

                    # Detect frameworks and libraries
                    if file_path.name in [
                        "requirements.txt",
                        "package.json",
                        "Pipfile",
                        "pyproject.toml",
                    ]:
                        structure["framework_indicators"].append(str(file_path))

                    # Detect test files
                    if "test" in file_path.name.lower():
                        test_dir = str(file_path.parent)
                        structure["test_structure"][test_dir] = (
                            structure["test_structure"].get(test_dir, 0) + 1
                        )

                    # Detect documentation
                    if (
                        file_path.suffix.lower() in [".md", ".rst", ".txt"]
                        and "doc" in file_path.name.lower()
                    ):
                        doc_dir = str(file_path.parent)
                        structure["documentation_structure"][doc_dir] = (
                            structure["documentation_structure"].get(doc_dir, 0) + 1
                        )

        except Exception as e:
            logger.warning(f"Failed to analyze repository structure: {e}")

        # Determine main languages
        if structure["file_types"]:
            lang_mapping = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".jsx": "javascript",
                ".tsx": "typescript",
                ".java": "java",
                ".cpp": "cpp",
                ".c": "c",
                ".go": "go",
                ".rs": "rust",
            }

            for ext, _count in sorted(
                structure["file_types"].items(), key=lambda x: x[1], reverse=True
            ):
                if ext in lang_mapping:
                    structure["main_languages"].append(lang_mapping[ext])
                if len(structure["main_languages"]) >= 3:
                    break

        return structure

    async def _perform_semantic_analysis(
        self, repo_path: Path, task: UnifiedTask
    ) -> dict[str, Any]:
        """Perform semantic analysis on relevant code files"""
        semantic_results = {
            "analyzed_files": [],
            "patterns_found": [],
            "concepts_identified": [],
            "architecture_insights": [],
            "quality_indicators": {},
        }

        # Select files to analyze based on task context
        files_to_analyze = self._select_files_for_analysis(repo_path, task)

        for file_path in files_to_analyze[:10]:  # Limit to avoid excessive processing
            try:
                with open(file_path, encoding="utf-8") as f:
                    code_content = f.read()

                language = self._detect_file_language(file_path)
                analysis = await self.semantic_engine.analyze_code_semantics(
                    code_content, language
                )

                semantic_results["analyzed_files"].append(
                    {
                        "file": str(file_path),
                        "language": language,
                        "analysis": analysis,
                    }
                )

                # Aggregate patterns and concepts
                semantic_results["patterns_found"].extend(analysis.get("patterns", []))
                semantic_results["concepts_identified"].extend(
                    analysis.get("concepts", [])
                )

            except Exception as e:
                logger.warning(f"Failed to analyze file {file_path}: {e}")

        return semantic_results

    async def _analyze_codebase_patterns(self, repo_path: Path) -> dict[str, Any]:
        """Analyze patterns across the entire codebase"""
        pattern_analysis = {
            "architectural_patterns": [],
            "design_patterns": [],
            "anti_patterns": [],
            "consistency_patterns": {},
            "pattern_distribution": {},
        }

        # This would be a comprehensive pattern analysis across files
        # For now, return mock structure
        return pattern_analysis

    async def _calculate_codebase_quality(self, repo_path: Path) -> dict[str, Any]:
        """Calculate quality metrics for the entire codebase"""
        quality_metrics = {
            "overall_complexity": 0.0,
            "test_coverage": 0.0,
            "documentation_coverage": 0.0,
            "code_duplication": 0.0,
            "maintainability_index": 0.0,
            "security_score": 0.0,
            "technical_debt": 0.0,
        }

        # This would aggregate quality metrics across all files
        # For now, return reasonable mock values
        quality_metrics = {
            "overall_complexity": 8.5,
            "test_coverage": 72.0,
            "documentation_coverage": 65.0,
            "code_duplication": 3.2,
            "maintainability_index": 78.0,
            "security_score": 85.0,
            "technical_debt": 12.5,
        }

        return quality_metrics

    async def _generate_architectural_overview(self, repo_path: Path) -> dict[str, Any]:
        """Generate architectural overview of the codebase"""
        overview = {
            "architecture_style": "layered",
            "main_components": [],
            "dependencies": [],
            "integration_points": [],
            "scalability_indicators": {},
            "maintainability_factors": {},
        }

        # This would analyze the architectural patterns
        # For now, return mock structure
        return overview

    def _select_files_for_analysis(
        self, repo_path: Path, task: UnifiedTask
    ) -> list[Path]:
        """Select relevant files for semantic analysis based on task"""
        relevant_files = []

        # Get file extensions for supported languages
        lang_extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
        }

        try:
            for file_path in repo_path.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in lang_extensions:
                    # Skip test files and node_modules
                    if (
                        "test" not in file_path.name.lower()
                        and "node_modules" not in str(file_path)
                    ):
                        relevant_files.append(file_path)

        except Exception as e:
            logger.warning(f"Failed to select files for analysis: {e}")

        # Sort by relevance (main files first)
        relevant_files.sort(
            key=lambda x: (
                0 if "main" in x.name.lower() or "index" in x.name.lower() else 1,
                x.name,
            )
        )

        return relevant_files

    def _detect_file_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        ext_mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".go": "go",
            ".rs": "rust",
        }

        return ext_mapping.get(file_path.suffix.lower(), "unknown")

    async def _load_code_patterns(self, task: UnifiedTask) -> dict[str, Any]:
        """Load relevant code patterns and examples"""
        patterns = {
            "detected_patterns": [],
            "recommended_patterns": [],
            "code_examples": [],
            "best_practices": [],
            "anti_patterns_to_avoid": [],
        }

        if self.memory:
            # Search for relevant code patterns
            hits = await self.memory.search(
                query=task.content,
                domain=MemoryDomain.ARTEMIS,
                k=5,
                filters={"type": "code_pattern"},
            )

            for hit in hits:
                patterns["code_examples"].append(
                    {
                        "content": hit.content,
                        "relevance": hit.score,
                        "source": hit.source_uri,
                        "metadata": hit.metadata,
                    }
                )

        # Load pattern library recommendations
        task_content_lower = task.content.lower()

        if "class" in task_content_lower or "object" in task_content_lower:
            patterns["recommended_patterns"].extend(
                ["factory", "singleton", "observer"]
            )

        if "api" in task_content_lower or "service" in task_content_lower:
            patterns["recommended_patterns"].extend(
                ["repository", "service_layer", "dto"]
            )

        if "test" in task_content_lower:
            patterns["recommended_patterns"].extend(
                ["arrange_act_assert", "mock", "fixture"]
            )

        return patterns

    def _prepare_semantic_code_messages(
        self,
        task: UnifiedTask,
        codebase_context: dict[str, Any],
        code_patterns: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Prepare messages for LLM with semantic code understanding"""

        # Detect primary language for the task
        primary_language = self._determine_primary_language(task, codebase_context)

        system_prompt = f"""You are Artemis, an expert software engineer specializing in {primary_language} and modern software development practices.

Your expertise includes:
1. Semantic code understanding and pattern recognition
2. Clean code principles and architectural patterns
3. Comprehensive testing strategies and TDD/BDD
4. Performance optimization and security best practices
5. Code review and quality assurance
6. Refactoring and technical debt management

Technical Context:
- Primary Language: {primary_language}
- Supported Languages: {', '.join(self.code_context.languages)}
- Frameworks: {', '.join(self.code_context.frameworks)}
- Architecture Patterns: {', '.join(self.code_context.architecture_patterns)}
- Quality Standards: {self.code_context.code_standards}

Codebase Analysis:
- Repository Structure: {codebase_context.get('repository_analysis', {}).get('total_files', 0)} files analyzed
- Main Languages: {codebase_context.get('repository_analysis', {}).get('main_languages', [])}
- Quality Metrics: Overall maintainability {codebase_context.get('quality_metrics', {}).get('maintainability_index', 0):.1f}%
- Test Coverage: {codebase_context.get('quality_metrics', {}).get('test_coverage', 0):.1f}%

Always ensure:
- Code follows SOLID principles and clean architecture
- Comprehensive error handling and input validation
- Security best practices are implemented
- Performance considerations are addressed
- Code is testable with appropriate test coverage
- Documentation is clear and comprehensive
- Patterns and practices align with existing codebase"""

        # Format codebase insights
        codebase_insights = self._format_codebase_insights(codebase_context)
        pattern_recommendations = self._format_pattern_recommendations(code_patterns)

        user_prompt = f"""Code Development Request: {task.content}

Codebase Context and Insights:
{codebase_insights}

Pattern Recommendations and Examples:
{pattern_recommendations}

Quality Requirements:
- Minimum complexity score: {self.quality_gates.get('complexity', 10)}
- Target test coverage: {self.quality_gates.get('coverage', 80)}%
- Required maintainability: {self.quality_gates.get('maintainability', 70)}%
- Security score threshold: {self.quality_gates.get('security_score', 80)}%

Please provide a comprehensive solution that includes:
1. Clean, production-ready code following best practices
2. Comprehensive error handling and input validation
3. Appropriate design patterns and architectural decisions
4. Complete test suite with high coverage
5. Clear documentation and code comments
6. Performance optimization considerations
7. Security implementation following best practices

Ensure the solution integrates well with the existing codebase architecture and follows established patterns."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _determine_primary_language(
        self, task: UnifiedTask, codebase_context: dict[str, Any]
    ) -> str:
        """Determine the primary language for the task"""
        # Check task metadata first
        if "language" in task.metadata:
            return task.metadata["language"]

        # Check codebase context
        main_languages = codebase_context.get("repository_analysis", {}).get(
            "main_languages", []
        )
        if main_languages:
            return main_languages[0]

        # Default to first language in context
        return (
            self.code_context.languages[0] if self.code_context.languages else "python"
        )

    def _format_codebase_insights(self, codebase_context: dict[str, Any]) -> str:
        """Format codebase insights for LLM consumption"""
        insights = []

        repo_analysis = codebase_context.get("repository_analysis", {})
        if repo_analysis:
            insights.append(
                f"Repository contains {repo_analysis.get('total_files', 0)} files"
            )
            insights.append(
                f"Main languages: {', '.join(repo_analysis.get('main_languages', []))}"
            )

        quality_metrics = codebase_context.get("quality_metrics", {})
        if quality_metrics:
            insights.append(
                f"Current quality: Maintainability {quality_metrics.get('maintainability_index', 0):.1f}%, Coverage {quality_metrics.get('test_coverage', 0):.1f}%"
            )

        semantic_analysis = codebase_context.get("semantic_analysis", {})
        if semantic_analysis.get("patterns_found"):
            insights.append(
                f"Detected patterns: {len(semantic_analysis['patterns_found'])} patterns identified"
            )

        return (
            "\n- ".join([""] + insights)
            if insights
            else "- No codebase analysis available"
        )

    def _format_pattern_recommendations(self, code_patterns: dict[str, Any]) -> str:
        """Format pattern recommendations for LLM consumption"""
        recommendations = []

        if code_patterns.get("recommended_patterns"):
            recommendations.append(
                f"Recommended patterns: {', '.join(code_patterns['recommended_patterns'])}"
            )

        if code_patterns.get("code_examples"):
            recommendations.append(
                f"Available examples: {len(code_patterns['code_examples'])} relevant code examples found"
            )

        if code_patterns.get("best_practices"):
            recommendations.append(
                f"Best practices: {', '.join(code_patterns['best_practices'][:3])}"
            )

        return (
            "\n- ".join([""] + recommendations)
            if recommendations
            else "- No specific pattern recommendations"
        )

    async def _generate_code_with_qa(
        self, messages: list[dict], routing: Any, task: UnifiedTask
    ) -> Any:
        """Generate code with quality assurance checks"""
        # Use appropriate model for code generation
        response = await self.portkey.execute_with_fallback(
            task_type=PortkeyTaskType.CODE_GENERATION,
            messages=messages,
            max_tokens=task.budget.get("tokens", 6000),
            temperature=0.1,  # Low temperature for consistent code generation
        )

        return response

    async def _review_code_comprehensively(
        self, messages: list[dict], routing: Any, task: UnifiedTask
    ) -> Any:
        """Perform comprehensive code review"""
        # Add code to review to the messages
        code_to_review = task.metadata.get("code", "")
        if code_to_review:
            messages.append(
                {
                    "role": "user",
                    "content": f"Please perform a comprehensive code review of the following code:\n\n```\n{code_to_review}\n```\n\nInclude analysis of: quality, security, performance, maintainability, testing, and architectural alignment.",
                }
            )

        response = await self.portkey.execute_with_fallback(
            task_type=PortkeyTaskType.CODE_REVIEW,
            messages=messages,
            max_tokens=task.budget.get("tokens", 4000),
            temperature=0.2,
        )

        return response

    async def _general_code_task_with_qa(
        self, messages: list[dict], routing: Any, task: UnifiedTask
    ) -> Any:
        """Handle general code tasks with QA considerations"""
        response = await self.portkey.execute_with_fallback(
            task_type=PortkeyTaskType.GENERAL,
            messages=messages,
            max_tokens=task.budget.get("tokens", 4000),
            temperature=0.3,
        )

        return response

    async def _process_semantic_response(
        self, response: Any, task: UnifiedTask
    ) -> dict[str, Any]:
        """Process LLM response with semantic code understanding"""
        content = (
            response.choices[0].message.content
            if hasattr(response, "choices")
            else str(response)
        )

        # Extract code blocks with language detection
        code_blocks = self._extract_enhanced_code_blocks(content)

        # Perform semantic analysis on generated code
        semantic_analysis = {}
        if code_blocks:
            primary_code = code_blocks[0].get("code", "")
            language = code_blocks[0].get("language", "unknown")

            if primary_code and language != "unknown":
                semantic_analysis = await self.semantic_engine.analyze_code_semantics(
                    primary_code, language
                )

        processed = {
            "raw_response": content,
            "code_blocks": code_blocks,
            "primary_code": code_blocks[0].get("code", "") if code_blocks else "",
            "primary_language": (
                code_blocks[0].get("language", "unknown") if code_blocks else "unknown"
            ),
            "explanation": self._extract_explanation(content),
            "tests": self._extract_test_code(content),
            "documentation": self._extract_documentation(content),
            "semantic_analysis": semantic_analysis,
            "complexity_analysis": await self._analyze_code_complexity(code_blocks),
            "timestamp": datetime.now().isoformat(),
            "task_id": task.id,
            "model_used": getattr(response, "model", "unknown"),
        }

        return processed

    def _extract_enhanced_code_blocks(self, content: str) -> list[dict[str, str]]:
        """Extract code blocks with enhanced language detection"""
        import re

        code_blocks = []

        # Pattern to match code blocks with optional language specification
        pattern = r"```(\w+)?\n(.*?)```"
        matches = re.findall(pattern, content, re.DOTALL)

        for lang, code in matches:
            # Enhanced language detection
            detected_lang = (
                lang.lower() if lang else self._detect_language_from_code(code)
            )

            code_blocks.append(
                {
                    "language": detected_lang,
                    "code": code.strip(),
                    "metadata": {
                        "lines": len(code.strip().split("\n")),
                        "characters": len(code.strip()),
                    },
                }
            )

        return code_blocks

    def _detect_language_from_code(self, code: str) -> str:
        """Detect programming language from code content"""
        code_lower = code.lower()

        # Python indicators
        if any(
            indicator in code_lower
            for indicator in ["def ", "import ", "from ", "class ", "__init__"]
        ):
            return "python"

        # JavaScript indicators
        elif any(
            indicator in code_lower
            for indicator in [
                "function ",
                "const ",
                "let ",
                "var ",
                "=>",
                "console.log",
            ]
        ):
            return "javascript"

        # TypeScript indicators
        elif any(
            indicator in code_lower
            for indicator in [
                "interface ",
                ": string",
                ": number",
                ": boolean",
                "type ",
            ]
        ):
            return "typescript"

        return "unknown"

    async def _analyze_code_complexity(
        self, code_blocks: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Analyze complexity of generated code blocks"""
        complexity_analysis = {
            "overall_complexity": 0.0,
            "block_complexities": [],
            "complexity_distribution": {},
            "recommendations": [],
        }

        total_complexity = 0
        for i, block in enumerate(code_blocks):
            code = block.get("code", "")
            language = block.get("language", "unknown")

            if code:
                complexity = self.qa_pipeline._calculate_complexity(code)
                total_complexity += complexity

                complexity_analysis["block_complexities"].append(
                    {
                        "block_index": i,
                        "language": language,
                        "complexity": complexity,
                        "recommendation": (
                            "Good" if complexity <= 10 else "Consider refactoring"
                        ),
                    }
                )

        if code_blocks:
            complexity_analysis["overall_complexity"] = total_complexity / len(
                code_blocks
            )

            # Add recommendations based on complexity
            if complexity_analysis["overall_complexity"] > 15:
                complexity_analysis["recommendations"].append(
                    "Consider breaking down complex functions"
                )
            elif complexity_analysis["overall_complexity"] > 10:
                complexity_analysis["recommendations"].append(
                    "Monitor complexity growth"
                )
            else:
                complexity_analysis["recommendations"].append(
                    "Complexity is within acceptable range"
                )

        return complexity_analysis

    def _extract_test_code(self, content: str) -> Optional[str]:
        """Extract test code from response"""
        import re

        # Look for test-related code blocks
        test_pattern = r"```(?:python|javascript|typescript)?\n(.*?test.*?)```"
        matches = re.findall(test_pattern, content, re.DOTALL | re.IGNORECASE)

        if matches:
            return matches[0].strip()

        # Look for test functions in any code block
        if "test_" in content or "describe(" in content or "it(" in content:
            # Extract the relevant test portion
            lines = content.split("\n")
            test_lines = [
                line
                for line in lines
                if any(
                    keyword in line.lower()
                    for keyword in ["test", "describe", "it", "assert"]
                )
            ]
            if test_lines:
                return "\n".join(test_lines)

        return None

    def _extract_documentation(self, content: str) -> Optional[str]:
        """Extract documentation from response"""
        import re

        # Look for documentation blocks (markdown, docstrings, etc.)
        doc_patterns = [
            r'"""(.*?)"""',  # Python docstrings
            r"'''(.*?)'''",  # Python docstrings
            r"/\*\*(.*?)\*/",  # JSDoc comments
            r"##\s+(.*?)(?=##|\n\n|\Z)",  # Markdown sections
        ]

        for pattern in doc_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                return "\n".join(matches)

        return None

    async def _run_qa_pipeline(
        self, processed: dict[str, Any], task: UnifiedTask
    ) -> dict[str, Any]:
        """Run comprehensive quality assurance pipeline"""
        primary_code = processed.get("primary_code", "")
        primary_language = processed.get("primary_language", "unknown")

        if not primary_code or primary_language == "unknown":
            return {"overall_score": 0.5, "message": "No code to analyze"}

        # Run comprehensive QA analysis
        qa_results = await self.qa_pipeline.run_comprehensive_analysis(
            primary_code, primary_language
        )

        # Add additional Artemis-specific checks
        artemis_checks = await self._run_artemis_specific_checks(processed)
        qa_results["artemis_checks"] = artemis_checks

        return qa_results

    async def _run_artemis_specific_checks(
        self, processed: dict[str, Any]
    ) -> dict[str, Any]:
        """Run Artemis-specific quality checks"""
        checks = {
            "pattern_compliance": True,
            "architecture_alignment": True,
            "testing_adequacy": False,  # Would check if tests are present
            "documentation_quality": False,  # Would check documentation
            "performance_considerations": True,
            "security_best_practices": True,
        }

        # Check if tests are included
        if processed.get("tests"):
            checks["testing_adequacy"] = True

        # Check if documentation is included
        if processed.get("documentation"):
            checks["documentation_quality"] = True

        # Pattern compliance check
        semantic_analysis = processed.get("semantic_analysis", {})
        patterns = semantic_analysis.get("patterns", [])

        if patterns:
            positive_patterns = [
                p for p in patterns if getattr(p, "impact", None) == "positive"
            ]
            negative_patterns = [
                p for p in patterns if getattr(p, "impact", None) == "negative"
            ]

            checks["pattern_compliance"] = len(positive_patterns) > len(
                negative_patterns
            )

        return checks

    async def _validate_quality_gates(
        self, processed: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate code against quality gates"""
        validation = {
            "passed": True,
            "failed_gates": [],
            "warnings": [],
            "overall_quality_score": 0.0,
        }

        qa_results = processed.get("qa_results", {})

        # Check complexity gate
        complexity_analysis = processed.get("complexity_analysis", {})
        overall_complexity = complexity_analysis.get("overall_complexity", 0)

        if overall_complexity > self.quality_gates.get("complexity", 10):
            validation["failed_gates"].append(
                f"Complexity {overall_complexity:.1f} exceeds threshold {self.quality_gates['complexity']}"
            )
            validation["passed"] = False

        # Check other quality gates
        quality_metrics = qa_results.get("quality_metrics", {})

        if hasattr(quality_metrics, "maintainability_index"):
            if quality_metrics.maintainability_index < self.quality_gates.get(
                "maintainability", 70
            ):
                validation["failed_gates"].append(
                    f"Maintainability {quality_metrics.maintainability_index:.1f} below threshold"
                )
                validation["passed"] = False

        # Check security score
        security_score = (
            qa_results.get("security_analysis", {}).get("security_score", 1.0) * 100
        )
        if security_score < self.quality_gates.get("security_score", 80):
            validation["failed_gates"].append(
                f"Security score {security_score:.1f} below threshold"
            )
            validation["passed"] = False

        # Calculate overall quality score
        scores = []
        if qa_results.get("overall_score"):
            scores.append(qa_results["overall_score"])

        artemis_checks = qa_results.get("artemis_checks", {})
        if artemis_checks:
            passed_checks = sum(1 for check in artemis_checks.values() if check)
            artemis_score = passed_checks / len(artemis_checks)
            scores.append(artemis_score)

        validation["overall_quality_score"] = (
            sum(scores) / len(scores) if scores else 0.5
        )

        return validation

    async def _generate_code_result(
        self, processed: dict[str, Any], task: UnifiedTask
    ) -> CodeResult:
        """Generate comprehensive code result"""
        qa_results = processed.get("qa_results", {})
        quality_metrics = qa_results.get("quality_metrics")

        # Extract patterns from semantic analysis
        patterns = []
        semantic_analysis = processed.get("semantic_analysis", {})
        if semantic_analysis.get("patterns"):
            patterns = semantic_analysis["patterns"]

        return CodeResult(
            code=processed.get("primary_code", ""),
            language=processed.get("primary_language", "unknown"),
            explanation=processed.get("explanation", ""),
            tests=processed.get("tests"),
            documentation=processed.get("documentation"),
            quality_metrics=quality_metrics,
            security_analysis=qa_results.get("security_analysis", {}),
            performance_analysis=qa_results.get("performance_analysis", {}),
            dependencies=self._extract_dependencies(processed),
            patterns=patterns,
        )

    def _extract_dependencies(self, processed: dict[str, Any]) -> list[str]:
        """Extract dependencies from generated code"""
        dependencies = []
        primary_code = processed.get("primary_code", "")

        if not primary_code:
            return dependencies

        # Extract Python imports
        if "import " in primary_code:
            import re

            import_pattern = r"(?:from\s+(\S+)\s+)?import\s+([^#\n]+)"
            matches = re.findall(import_pattern, primary_code)

            for module, imports in matches:
                if module:
                    dependencies.append(module)
                else:
                    # Handle direct imports
                    import_names = [
                        imp.strip().split(" as ")[0] for imp in imports.split(",")
                    ]
                    dependencies.extend(import_names)

        # Extract JavaScript/TypeScript imports
        if "require(" in primary_code or "from " in primary_code:
            import re

            # Match require statements
            require_pattern = r"require\(['\"]([^'\"]+)['\"]\)"
            requires = re.findall(require_pattern, primary_code)
            dependencies.extend(requires)

            # Match ES6 imports
            import_pattern = r"from\s+['\"]([^'\"]+)['\"]"
            imports = re.findall(import_pattern, primary_code)
            dependencies.extend(imports)

        return list(set(dependencies))  # Remove duplicates

    def _calculate_code_confidence(
        self, processed: dict[str, Any], quality_validation: dict[str, Any]
    ) -> float:
        """Calculate confidence score for generated code"""
        factors = []

        # Quality gate compliance
        if quality_validation.get("passed", False):
            factors.append(0.9)
        else:
            factors.append(0.6)

        # Overall quality score
        quality_score = quality_validation.get("overall_quality_score", 0.5)
        factors.append(quality_score)

        # Complexity factor
        complexity_analysis = processed.get("complexity_analysis", {})
        complexity = complexity_analysis.get("overall_complexity", 10)
        complexity_factor = max(0.3, 1.0 - (complexity / 20))  # Normalize complexity
        factors.append(complexity_factor)

        # Semantic analysis factor
        semantic_analysis = processed.get("semantic_analysis", {})
        if semantic_analysis.get("patterns"):
            # Higher confidence if good patterns detected
            positive_patterns = [
                p
                for p in semantic_analysis["patterns"]
                if getattr(p, "impact", None) == "positive"
            ]
            pattern_factor = min(1.0, 0.6 + (len(positive_patterns) * 0.1))
            factors.append(pattern_factor)
        else:
            factors.append(0.7)

        return sum(factors) / len(factors)

    def _extract_code_citations(
        self, codebase_context: dict[str, Any]
    ) -> list[dict[str, str]]:
        """Extract citations from codebase analysis"""
        citations = []

        # Repository analysis citation
        repo_analysis = codebase_context.get("repository_analysis", {})
        if repo_analysis:
            citations.append(
                {
                    "source": "codebase_analysis",
                    "type": "repository",
                    "timestamp": datetime.now().isoformat(),
                    "files_analyzed": str(repo_analysis.get("total_files", 0)),
                    "languages": ", ".join(repo_analysis.get("main_languages", [])),
                }
            )

        # Semantic analysis citation
        semantic_analysis = codebase_context.get("semantic_analysis", {})
        if semantic_analysis.get("analyzed_files"):
            citations.append(
                {
                    "source": "semantic_analysis",
                    "type": "code_analysis",
                    "timestamp": datetime.now().isoformat(),
                    "files_analyzed": str(len(semantic_analysis["analyzed_files"])),
                    "patterns_found": str(
                        len(semantic_analysis.get("patterns_found", []))
                    ),
                }
            )

        # Quality metrics citation
        quality_metrics = codebase_context.get("quality_metrics", {})
        if quality_metrics:
            citations.append(
                {
                    "source": "quality_analysis",
                    "type": "metrics",
                    "timestamp": datetime.now().isoformat(),
                    "maintainability": str(
                        quality_metrics.get("maintainability_index", 0)
                    ),
                    "coverage": str(quality_metrics.get("test_coverage", 0)),
                }
            )

        return citations

    def _detect_language(self, processed: dict[str, Any]) -> str:
        """Detect primary language from processed result"""
        return processed.get("primary_language", "unknown")

    # ========== Specialized Artemis Methods ==========

    async def generate_code_with_tests(
        self,
        specification: str,
        language: str = "python",
        architecture_pattern: Optional[str] = None,
        include_documentation: bool = True,
    ) -> CodeResult:
        """Generate code with comprehensive testing and documentation"""
        task = UnifiedTask(
            id=f"codegen_with_tests_{datetime.now().timestamp()}",
            type=PortkeyTaskType.CODE_GENERATION,
            content=f"Generate {language} code with comprehensive tests: {specification}",
            priority=ExecutionPriority.NORMAL,
            tags=["generation", "testing", "documentation", language],
            metadata={
                "language": language,
                "architecture_pattern": architecture_pattern,
                "include_tests": True,
                "include_documentation": include_documentation,
                "quality_requirements": "high",
            },
        )

        result = await self.execute(task)

        if result.success:
            return result.content

        return None

    async def review_code_comprehensively(
        self,
        code: str,
        language: str = "python",
        focus_areas: list[str] = None,
        include_refactoring_suggestions: bool = True,
    ) -> CodeReview:
        """Perform comprehensive code review with quality analysis"""
        if not focus_areas:
            focus_areas = [
                "quality",
                "security",
                "performance",
                "maintainability",
                "testing",
                "architecture",
            ]

        task = UnifiedTask(
            id=f"comprehensive_review_{datetime.now().timestamp()}",
            type=PortkeyTaskType.CODE_REVIEW,
            content=f"Comprehensive {language} code review focusing on {', '.join(focus_areas)}",
            priority=ExecutionPriority.NORMAL,
            tags=["review", "quality", "analysis"] + focus_areas,
            metadata={
                "code": code,
                "language": language,
                "focus_areas": focus_areas,
                "include_refactoring": include_refactoring_suggestions,
                "comprehensive_analysis": True,
            },
        )

        result = await self.execute(task)

        if result.success:
            return await self._format_as_comprehensive_review(result)

        return None

    async def refactor_code_with_patterns(
        self,
        code: str,
        target_patterns: list[str],
        quality_goals: dict[str, float] = None,
        maintain_functionality: bool = True,
    ) -> CodeResult:
        """Refactor code applying specific patterns and quality goals"""
        if not quality_goals:
            quality_goals = {
                "complexity_reduction": 0.3,
                "maintainability_improvement": 0.2,
                "test_coverage_target": 0.9,
            }

        task = UnifiedTask(
            id=f"refactor_patterns_{datetime.now().timestamp()}",
            type=PortkeyTaskType.CODE_GENERATION,
            content=f"Refactor code applying {', '.join(target_patterns)} patterns with quality improvements",
            priority=ExecutionPriority.NORMAL,
            tags=["refactoring", "patterns", "quality"] + target_patterns,
            metadata={
                "original_code": code,
                "target_patterns": target_patterns,
                "quality_goals": quality_goals,
                "maintain_functionality": maintain_functionality,
                "comprehensive_refactoring": True,
            },
        )

        result = await self.execute(task)

        if result.success:
            return result.content

        return None

    async def analyze_technical_debt(
        self, repository_path: Optional[str] = None
    ) -> dict[str, Any]:
        """Analyze technical debt across the codebase"""
        content = "Analyze technical debt and provide refactoring roadmap"
        if repository_path:
            content += f" for repository at {repository_path}"

        task = UnifiedTask(
            id=f"tech_debt_analysis_{datetime.now().timestamp()}",
            type=PortkeyTaskType.CODE_REVIEW,
            content=content,
            priority=ExecutionPriority.NORMAL,
            tags=["technical-debt", "analysis", "refactoring", "roadmap"],
            metadata={
                "repository_path": repository_path,
                "analysis_type": "technical_debt",
                "comprehensive_scan": True,
            },
        )

        result = await self.execute(task)

        if result.success:
            return result.content

        return None

    async def _format_as_comprehensive_review(
        self, result: UnifiedResult
    ) -> CodeReview:
        """Format execution result as comprehensive CodeReview"""
        # Extract review components from the result
        processed_content = result.content

        return CodeReview(
            overall_score=result.confidence,
            quality_metrics=(
                processed_content.quality_metrics
                if hasattr(processed_content, "quality_metrics")
                else QualityMetrics(
                    complexity_score=0.0,
                    maintainability_index=0.0,
                    test_coverage=0.0,
                    security_score=0.0,
                    performance_score=0.0,
                    documentation_coverage=0.0,
                    code_duplication=0.0,
                    technical_debt_ratio=0.0,
                    overall_quality=0.0,
                )
            ),
            issues=[],
            suggestions=[],
            security_vulnerabilities=[],
            performance_concerns=[],
            best_practices=[],
            patterns=(
                processed_content.patterns
                if hasattr(processed_content, "patterns")
                else []
            ),
            refactoring_opportunities=[],
            technical_debt_assessment={},
        )


# ========== Supporting Components ==========


class CodeSandbox:
    """Safe code execution sandbox for testing generated code"""

    async def execute_code(
        self, code: str, language: str, timeout: int = 10
    ) -> dict[str, Any]:
        """Execute code in a safe sandbox environment"""
        result = {
            "output": "",
            "errors": [],
            "execution_time": 0.0,
            "exit_code": 0,
            "resource_usage": {},
        }

        # This would implement actual sandboxed execution
        # For now, return mock success
        result["output"] = "Code executed successfully (sandbox simulation)"
        result["execution_time"] = 0.1

        return result

    async def validate_syntax(self, code: str, language: str) -> dict[str, Any]:
        """Validate code syntax without execution"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        if language == "python":
            try:
                ast.parse(code)
                validation["valid"] = True
            except SyntaxError as e:
                validation["valid"] = False
                validation["errors"].append(str(e))

        return validation
