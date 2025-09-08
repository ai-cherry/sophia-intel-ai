"""
Comprehensive Meta-Tagging System for Sophia AI

This module provides a unified meta-tagging infrastructure for intelligent code analysis,
classification, and enhancement suggestions. It enables AI systems to better understand
codebase structure, component relationships, and optimization opportunities.
"""

import ast
import asyncio
import hashlib
import json
import logging
import os
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, TypeVar

# Configure logging
logger = logging.getLogger(__name__)

T = TypeVar("T")


class SemanticRole(Enum):
    """Component classification based on architectural role."""

    # Core Infrastructure
    ORCHESTRATOR = "orchestrator"  # High-level coordination logic
    PROCESSOR = "processor"  # Data processing/transformation
    GATEWAY = "gateway"  # External interface/API endpoints
    REPOSITORY = "repository"  # Data persistence layer
    SERVICE = "service"  # Business logic services

    # AI/ML Components
    AGENT = "agent"  # AI agents/swarms
    MODEL = "model"  # ML models/inference
    PIPELINE = "pipeline"  # Data/ML pipelines
    ANALYZER = "analyzer"  # Analysis/evaluation tools

    # System Components
    MIDDLEWARE = "middleware"  # Cross-cutting concerns
    UTILITY = "utility"  # Helper functions/utilities
    CONFIG = "config"  # Configuration management
    ROUTER = "router"  # Request routing/dispatch

    # Data Components
    SCHEMA = "schema"  # Data models/schemas
    ADAPTER = "adapter"  # External integration
    CACHE = "cache"  # Caching mechanisms
    VALIDATOR = "validator"  # Data validation

    # Testing & Quality
    TEST = "test"  # Test cases/fixtures
    MOCK = "mock"  # Test mocks/stubs
    BENCHMARK = "benchmark"  # Performance tests

    # Documentation & Metadata
    DOCUMENTATION = "documentation"  # Documentation files
    EXAMPLE = "example"  # Example/demo code
    SCRIPT = "script"  # Automation scripts

    UNKNOWN = "unknown"  # Unclassified components


class Complexity(Enum):
    """Code complexity assessment."""

    TRIVIAL = 1  # Simple utilities, getters/setters
    LOW = 2  # Basic logic, simple transformations
    MODERATE = 3  # Multiple responsibilities, some complexity
    HIGH = 4  # Complex algorithms, multiple dependencies
    CRITICAL = 5  # Core systems, high risk modifications


class Priority(Enum):
    """Priority levels for maintenance and optimization."""

    LOW = 1  # Nice to have improvements
    MEDIUM = 2  # Beneficial optimizations
    HIGH = 3  # Important for system health
    CRITICAL = 4  # Essential for stability/security


class ModificationRisk(Enum):
    """Risk assessment for code modifications."""

    SAFE = 1  # Low impact, well-tested
    MODERATE = 2  # Some dependencies, moderate testing
    HIGH = 3  # Many dependencies, complex logic
    CRITICAL = 4  # Core infrastructure, high blast radius


@dataclass
class MetaTag:
    """Comprehensive metadata for code components."""

    # Core Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str = ""
    component_name: str = ""
    line_range: tuple[int, int] = (0, 0)

    # Classification
    semantic_role: SemanticRole = SemanticRole.UNKNOWN
    complexity: Complexity = Complexity.MODERATE
    priority: Priority = Priority.MEDIUM
    modification_risk: ModificationRisk = ModificationRisk.MODERATE

    # Capabilities & Dependencies
    capabilities: set[str] = field(default_factory=set)
    dependencies: set[str] = field(default_factory=set)
    dependents: set[str] = field(default_factory=set)
    external_integrations: set[str] = field(default_factory=set)

    # AI Enhancement Hints
    optimization_opportunities: list[str] = field(default_factory=list)
    refactoring_suggestions: list[str] = field(default_factory=list)
    test_requirements: list[str] = field(default_factory=list)
    security_considerations: list[str] = field(default_factory=list)

    # Quality Metrics
    cyclomatic_complexity: int = 0
    lines_of_code: int = 0
    test_coverage: Optional[float] = None
    documentation_score: float = 0.0
    type_safety_score: float = 0.0

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    confidence_score: float = 0.0
    tags: set[str] = field(default_factory=set)

    # Hash for change detection
    content_hash: str = ""

    def __post_init__(self):
        """Validate and normalize tag data."""
        self.updated_at = datetime.now()

        # Ensure sets are actually sets
        if isinstance(self.capabilities, list):
            self.capabilities = set(self.capabilities)
        if isinstance(self.dependencies, list):
            self.dependencies = set(self.dependencies)
        if isinstance(self.dependents, list):
            self.dependents = set(self.dependents)
        if isinstance(self.external_integrations, list):
            self.external_integrations = set(self.external_integrations)
        if isinstance(self.tags, list):
            self.tags = set(self.tags)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with serializable values."""
        data = asdict(self)

        # Convert enums to values
        data["semantic_role"] = self.semantic_role.value
        data["complexity"] = self.complexity.value
        data["priority"] = self.priority.value
        data["modification_risk"] = self.modification_risk.value

        # Convert sets to lists for JSON serialization
        for field_name in [
            "capabilities",
            "dependencies",
            "dependents",
            "external_integrations",
            "tags",
        ]:
            if field_name in data and isinstance(data[field_name], set):
                data[field_name] = list(data[field_name])

        # Convert datetime to ISO string
        for dt_field in ["created_at", "updated_at"]:
            if dt_field in data and isinstance(data[dt_field], datetime):
                data[dt_field] = data[dt_field].isoformat()

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MetaTag":
        """Create MetaTag from dictionary."""
        # Convert enum strings back to enums
        if "semantic_role" in data:
            data["semantic_role"] = SemanticRole(data["semantic_role"])
        if "complexity" in data:
            data["complexity"] = Complexity(data["complexity"])
        if "priority" in data:
            data["priority"] = Priority(data["priority"])
        if "modification_risk" in data:
            data["modification_risk"] = ModificationRisk(data["modification_risk"])

        # Convert lists back to sets
        for field_name in [
            "capabilities",
            "dependencies",
            "dependents",
            "external_integrations",
            "tags",
        ]:
            if field_name in data and isinstance(data[field_name], list):
                data[field_name] = set(data[field_name])

        # Convert datetime strings back to datetime
        for dt_field in ["created_at", "updated_at"]:
            if dt_field in data and isinstance(data[dt_field], str):
                data[dt_field] = datetime.fromisoformat(data[dt_field])

        return cls(**data)

    def update_confidence(self, confidence: float):
        """Update confidence score with validation."""
        self.confidence_score = max(0.0, min(1.0, confidence))
        self.updated_at = datetime.now()

    def add_capability(self, capability: str):
        """Add a capability with update tracking."""
        self.capabilities.add(capability)
        self.updated_at = datetime.now()

    def add_dependency(self, dependency: str):
        """Add a dependency with update tracking."""
        self.dependencies.add(dependency)
        self.updated_at = datetime.now()

    def add_optimization(self, optimization: str):
        """Add an optimization opportunity."""
        if optimization not in self.optimization_opportunities:
            self.optimization_opportunities.append(optimization)
            self.updated_at = datetime.now()


class MetaTagRegistry:
    """Centralized registry for managing meta-tags across the codebase."""

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize registry with optional persistent storage."""
        self.storage_path = storage_path or "meta_tags_registry.json"
        self._tags: dict[str, MetaTag] = {}
        self._file_index: dict[str, set[str]] = {}  # file_path -> tag_ids
        self._role_index: dict[SemanticRole, set[str]] = {}  # role -> tag_ids
        self._dependency_graph: dict[str, set[str]] = {}  # component -> dependencies

        # Initialize role index
        for role in SemanticRole:
            self._role_index[role] = set()

        self.load()

    def register(self, tag: MetaTag) -> str:
        """Register a meta-tag and update indices."""
        tag_id = tag.id
        self._tags[tag_id] = tag

        # Update file index
        if tag.file_path not in self._file_index:
            self._file_index[tag.file_path] = set()
        self._file_index[tag.file_path].add(tag_id)

        # Update role index
        self._role_index[tag.semantic_role].add(tag_id)

        # Update dependency graph
        if tag.component_name:
            self._dependency_graph[tag.component_name] = tag.dependencies.copy()

        logger.info(f"Registered meta-tag for {tag.component_name} in {tag.file_path}")
        return tag_id

    def get(self, tag_id: str) -> Optional[MetaTag]:
        """Retrieve a meta-tag by ID."""
        return self._tags.get(tag_id)

    def get_by_file(self, file_path: str) -> list[MetaTag]:
        """Get all meta-tags for a specific file."""
        tag_ids = self._file_index.get(file_path, set())
        return [self._tags[tag_id] for tag_id in tag_ids if tag_id in self._tags]

    def get_by_role(self, role: SemanticRole) -> list[MetaTag]:
        """Get all meta-tags for a specific semantic role."""
        tag_ids = self._role_index.get(role, set())
        return [self._tags[tag_id] for tag_id in tag_ids if tag_id in self._tags]

    def get_by_component(self, component_name: str) -> Optional[MetaTag]:
        """Get meta-tag for a specific component."""
        for tag in self._tags.values():
            if tag.component_name == component_name:
                return tag
        return None

    def search(
        self,
        role: Optional[SemanticRole] = None,
        complexity: Optional[Complexity] = None,
        capabilities: Optional[set[str]] = None,
        tags: Optional[set[str]] = None,
    ) -> list[MetaTag]:
        """Search meta-tags by various criteria."""
        results = list(self._tags.values())

        if role:
            results = [tag for tag in results if tag.semantic_role == role]

        if complexity:
            results = [tag for tag in results if tag.complexity == complexity]

        if capabilities:
            results = [
                tag for tag in results if capabilities.issubset(tag.capabilities)
            ]

        if tags:
            results = [tag for tag in results if tags.intersection(tag.tags)]

        return results

    def get_dependencies(self, component_name: str) -> set[str]:
        """Get dependencies for a component."""
        return self._dependency_graph.get(component_name, set())

    def get_dependents(self, component_name: str) -> set[str]:
        """Get components that depend on the given component."""
        dependents = set()
        for comp, deps in self._dependency_graph.items():
            if component_name in deps:
                dependents.add(comp)
        return dependents

    def update_dependencies(self):
        """Update bidirectional dependency relationships."""
        for tag in self._tags.values():
            if tag.component_name:
                # Update dependents for each dependency
                for dep in tag.dependencies:
                    dep_tag = self.get_by_component(dep)
                    if dep_tag:
                        dep_tag.dependents.add(tag.component_name)

    def get_high_risk_components(self) -> list[MetaTag]:
        """Get components with high modification risk."""
        return [
            tag
            for tag in self._tags.values()
            if tag.modification_risk
            in [ModificationRisk.HIGH, ModificationRisk.CRITICAL]
        ]

    def get_optimization_candidates(self) -> list[MetaTag]:
        """Get components with optimization opportunities."""
        return [tag for tag in self._tags.values() if tag.optimization_opportunities]

    def save(self):
        """Save registry to persistent storage."""
        try:
            data = {
                "tags": {tag_id: tag.to_dict() for tag_id, tag in self._tags.items()},
                "metadata": {
                    "total_tags": len(self._tags),
                    "last_updated": datetime.now().isoformat(),
                    "version": "1.0.0",
                },
            }

            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Saved {len(self._tags)} meta-tags to {self.storage_path}")

        except Exception as e:
            logger.error(f"Failed to save meta-tags: {e}")

    def load(self):
        """Load registry from persistent storage."""
        if not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path) as f:
                data = json.load(f)

            # Load tags
            for _tag_id, tag_data in data.get("tags", {}).items():
                tag = MetaTag.from_dict(tag_data)
                self.register(tag)

            # Update dependency relationships
            self.update_dependencies()

            logger.info(f"Loaded {len(self._tags)} meta-tags from {self.storage_path}")

        except Exception as e:
            logger.error(f"Failed to load meta-tags: {e}")

    def stats(self) -> dict[str, Any]:
        """Get registry statistics."""
        role_counts = {}
        for role in SemanticRole:
            role_counts[role.value] = len(self._role_index[role])

        complexity_counts = {}
        for complexity in Complexity:
            complexity_counts[complexity.value] = len(
                [tag for tag in self._tags.values() if tag.complexity == complexity]
            )

        return {
            "total_tags": len(self._tags),
            "files_covered": len(self._file_index),
            "role_distribution": role_counts,
            "complexity_distribution": complexity_counts,
            "high_risk_components": len(self.get_high_risk_components()),
            "optimization_candidates": len(self.get_optimization_candidates()),
            "avg_confidence": (
                sum(tag.confidence_score for tag in self._tags.values())
                / len(self._tags)
                if self._tags
                else 0
            ),
        }


class AutoTagger:
    """Automated tagging system using AST analysis and pattern matching."""

    def __init__(self, registry: MetaTagRegistry):
        self.registry = registry

        # Pattern matching for semantic roles
        self.role_patterns = {
            SemanticRole.ORCHESTRATOR: [
                r"orchestrat",
                r"coordinat",
                r"manage",
                r"control",
                r"supervisor",
            ],
            SemanticRole.PROCESSOR: [
                r"process",
                r"transform",
                r"convert",
                r"parse",
                r"encode",
                r"decode",
            ],
            SemanticRole.GATEWAY: [
                r"gateway",
                r"api",
                r"endpoint",
                r"route",
                r"handler",
                r"controller",
            ],
            SemanticRole.SERVICE: [r"service", r"business", r"logic", r"operation"],
            SemanticRole.AGENT: [
                r"agent",
                r"swarm",
                r"ai",
                r"autonomous",
                r"intelligent",
            ],
            SemanticRole.MODEL: [
                r"model",
                r"neural",
                r"ml",
                r"predict",
                r"inference",
                r"train",
            ],
            SemanticRole.REPOSITORY: [
                r"repository",
                r"repo",
                r"storage",
                r"persist",
                r"database",
                r"db",
            ],
            SemanticRole.UTILITY: [r"util", r"helper", r"tool", r"common", r"shared"],
        }

        # Capability patterns
        self.capability_patterns = {
            "async": r"async\s+def|await\s+",
            "api": r"@app\.|@router\.|FastAPI|APIRouter",
            "database": r"database|sql|query|transaction",
            "ai": r"model|agent|neural|ml|ai",
            "caching": r"cache|redis|memcache",
            "validation": r"valid|schema|pydantic",
            "logging": r"log|logger|logging",
            "config": r"config|settings|environment",
            "testing": r"test|mock|assert|pytest",
            "security": r"auth|security|token|encrypt|decrypt",
        }

    async def tag_file(self, file_path: str) -> list[MetaTag]:
        """Analyze and tag a single file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Generate content hash
            content_hash = hashlib.md5(content.encode()).hexdigest()

            tags = []

            # Try AST analysis for Python files
            if file_path.endswith(".py"):
                tags.extend(
                    await self._analyze_python_file(file_path, content, content_hash)
                )
            else:
                # Basic analysis for other files
                tag = await self._analyze_generic_file(file_path, content, content_hash)
                if tag:
                    tags.append(tag)

            # Register all tags
            for tag in tags:
                self.registry.register(tag)

            return tags

        except Exception as e:
            logger.error(f"Failed to tag file {file_path}: {e}")
            return []

    async def _analyze_python_file(
        self, file_path: str, content: str, content_hash: str
    ) -> list[MetaTag]:
        """Analyze Python file using AST."""
        try:
            tree = ast.parse(content)
            tags = []

            # Analyze classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    tag = await self._create_class_tag(
                        file_path, node, content, content_hash
                    )
                    tags.append(tag)

                elif isinstance(node, ast.FunctionDef):
                    # Only tag top-level functions
                    if hasattr(node, "parent") and isinstance(node.parent, ast.Module):
                        tag = await self._create_function_tag(
                            file_path, node, content, content_hash
                        )
                        tags.append(tag)

            # If no classes or functions, create a module-level tag
            if not tags:
                tag = await self._create_module_tag(file_path, content, content_hash)
                tags.append(tag)

            return tags

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return [await self._analyze_generic_file(file_path, content, content_hash)]

    async def _create_class_tag(
        self, file_path: str, node: ast.ClassDef, content: str, content_hash: str
    ) -> MetaTag:
        """Create meta-tag for a class."""
        tag = MetaTag(
            file_path=file_path,
            component_name=node.name,
            line_range=(node.lineno, getattr(node, "end_lineno", node.lineno)),
            content_hash=content_hash,
        )

        # Determine semantic role
        tag.semantic_role = self._determine_role(node.name, content)

        # Analyze capabilities
        tag.capabilities = self._extract_capabilities(content)

        # Calculate complexity
        tag.complexity = self._calculate_complexity(node)
        tag.cyclomatic_complexity = self._calculate_cyclomatic_complexity(node)

        # Extract dependencies
        tag.dependencies = self._extract_dependencies(content)

        # Generate AI hints
        await self._generate_ai_hints(tag, content)

        return tag

    async def _create_function_tag(
        self, file_path: str, node: ast.FunctionDef, content: str, content_hash: str
    ) -> MetaTag:
        """Create meta-tag for a function."""
        tag = MetaTag(
            file_path=file_path,
            component_name=node.name,
            line_range=(node.lineno, getattr(node, "end_lineno", node.lineno)),
            content_hash=content_hash,
        )

        # Determine semantic role
        tag.semantic_role = self._determine_role(node.name, content)

        # Analyze capabilities
        tag.capabilities = self._extract_capabilities(content)

        # Calculate complexity
        tag.complexity = self._calculate_complexity(node)
        tag.cyclomatic_complexity = self._calculate_cyclomatic_complexity(node)

        # Extract dependencies
        tag.dependencies = self._extract_dependencies(content)

        # Generate AI hints
        await self._generate_ai_hints(tag, content)

        return tag

    async def _create_module_tag(
        self, file_path: str, content: str, content_hash: str
    ) -> MetaTag:
        """Create meta-tag for a module."""
        module_name = Path(file_path).stem

        tag = MetaTag(
            file_path=file_path,
            component_name=module_name,
            line_range=(1, len(content.splitlines())),
            content_hash=content_hash,
        )

        # Determine semantic role
        tag.semantic_role = self._determine_role(module_name, content)

        # Analyze capabilities
        tag.capabilities = self._extract_capabilities(content)

        # Calculate basic metrics
        tag.lines_of_code = len(
            [
                line
                for line in content.splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
        )

        # Extract dependencies
        tag.dependencies = self._extract_dependencies(content)

        # Generate AI hints
        await self._generate_ai_hints(tag, content)

        return tag

    async def _analyze_generic_file(
        self, file_path: str, content: str, content_hash: str
    ) -> Optional[MetaTag]:
        """Analyze non-Python files."""
        file_name = Path(file_path).name

        tag = MetaTag(
            file_path=file_path,
            component_name=file_name,
            line_range=(1, len(content.splitlines())),
            content_hash=content_hash,
        )

        # Basic role determination
        if file_path.endswith((".json", ".yaml", ".yml", ".toml")):
            tag.semantic_role = SemanticRole.CONFIG
        elif file_path.endswith((".md", ".rst", ".txt")):
            tag.semantic_role = SemanticRole.DOCUMENTATION
        elif file_path.endswith((".sql",)):
            tag.semantic_role = SemanticRole.SCHEMA
        elif file_path.endswith((".sh", ".bat", ".ps1")):
            tag.semantic_role = SemanticRole.SCRIPT
        else:
            tag.semantic_role = SemanticRole.UNKNOWN

        # Basic metrics
        tag.lines_of_code = len(content.splitlines())
        tag.complexity = (
            Complexity.LOW if tag.lines_of_code < 50 else Complexity.MODERATE
        )

        return tag

    def _determine_role(self, name: str, content: str) -> SemanticRole:
        """Determine semantic role based on name and content patterns."""
        name_lower = name.lower()
        content_sample = content[:1000].lower()  # First 1000 chars for efficiency

        for role, patterns in self.role_patterns.items():
            for pattern in patterns:
                if re.search(pattern, name_lower) or re.search(pattern, content_sample):
                    return role

        return SemanticRole.UNKNOWN

    def _extract_capabilities(self, content: str) -> set[str]:
        """Extract capabilities from content analysis."""
        capabilities = set()
        content_lower = content.lower()

        for capability, pattern in self.capability_patterns.items():
            if re.search(pattern, content_lower):
                capabilities.add(capability)

        return capabilities

    def _calculate_complexity(self, node: ast.AST) -> Complexity:
        """Calculate complexity based on AST node analysis."""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Function complexity based on statements
            stmt_count = len([n for n in ast.walk(node) if isinstance(n, ast.stmt)])
            if stmt_count < 5:
                return Complexity.TRIVIAL
            elif stmt_count < 15:
                return Complexity.LOW
            elif stmt_count < 30:
                return Complexity.MODERATE
            elif stmt_count < 50:
                return Complexity.HIGH
            else:
                return Complexity.CRITICAL

        elif isinstance(node, ast.ClassDef):
            # Class complexity based on methods and attributes
            methods = [
                n
                for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            if len(methods) < 3:
                return Complexity.LOW
            elif len(methods) < 8:
                return Complexity.MODERATE
            elif len(methods) < 15:
                return Complexity.HIGH
            else:
                return Complexity.CRITICAL

        return Complexity.MODERATE

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(
                child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler)
            ):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _extract_dependencies(self, content: str) -> set[str]:
        """Extract dependencies from import statements."""
        dependencies = set()

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom) and node.module:
                    dependencies.add(node.module.split(".")[0])
        except:
            # Fallback to regex if AST parsing fails
            import_pattern = r"(?:from\s+(\w+)|import\s+(\w+))"
            matches = re.findall(import_pattern, content)
            for match in matches:
                dep = match[0] or match[1]
                if dep:
                    dependencies.add(dep)

        return dependencies

    async def _generate_ai_hints(self, tag: MetaTag, content: str):
        """Generate AI enhancement hints."""
        # Basic heuristics for optimization opportunities
        if "TODO" in content or "FIXME" in content:
            tag.optimization_opportunities.append("Contains TODO/FIXME comments")

        if tag.cyclomatic_complexity > 10:
            tag.optimization_opportunities.append(
                "High cyclomatic complexity - consider refactoring"
            )

        if tag.lines_of_code > 100 and tag.semantic_role != SemanticRole.CONFIG:
            tag.refactoring_suggestions.append(
                "Large file - consider breaking into smaller modules"
            )

        if "password" in content.lower() or "secret" in content.lower():
            tag.security_considerations.append("Contains sensitive data references")

        # Test requirements based on complexity
        if tag.complexity.value >= Complexity.MODERATE.value:
            tag.test_requirements.append(
                "Unit tests recommended for moderate+ complexity"
            )

        if "async" in tag.capabilities:
            tag.test_requirements.append("Async testing patterns required")

        # Set confidence based on available information
        confidence = 0.5  # Base confidence
        if tag.semantic_role != SemanticRole.UNKNOWN:
            confidence += 0.2
        if tag.capabilities:
            confidence += 0.2
        if tag.dependencies:
            confidence += 0.1

        tag.update_confidence(confidence)


# Global registry instance
_global_registry: Optional[MetaTagRegistry] = None


def get_global_registry() -> MetaTagRegistry:
    """Get the global meta-tag registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = MetaTagRegistry()
    return _global_registry


async def auto_tag_directory(
    directory_path: str, file_patterns: list[str] = None
) -> dict[str, list[MetaTag]]:
    """Auto-tag all files in a directory."""
    if file_patterns is None:
        file_patterns = ["*.py", "*.js", "*.ts", "*.json", "*.yaml", "*.yml"]

    registry = get_global_registry()
    tagger = AutoTagger(registry)

    results = {}

    for pattern in file_patterns:
        for file_path in Path(directory_path).rglob(pattern):
            if file_path.is_file() and not any(
                part.startswith(".") for part in file_path.parts
            ):
                try:
                    tags = await tagger.tag_file(str(file_path))
                    results[str(file_path)] = tags
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")

    return results


if __name__ == "__main__":
    # Example usage
    async def main():
        registry = get_global_registry()
        results = await auto_tag_directory(".", ["*.py"])

        print(f"Tagged {len(results)} files")
        print("Registry stats:", registry.stats())

    asyncio.run(main())
