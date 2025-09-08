"""
Living Documentation System
==========================

Self-maintaining documentation system with AI context integration,
tiered complexity examples, and semantic concept mapping.

Features:
- Automatic documentation generation and updates
- AI context sections for model understanding
- Multi-tier examples (beginner, intermediate, advanced)
- Semantic concept mapping and cross-references
- Integration with meta-tagging and embedding systems
- Real-time documentation health monitoring

AI Context:
- Documents are living entities that evolve with code changes
- AI can understand and extend documentation automatically
- Semantic relationships enable intelligent navigation
- Context-aware examples adapt to user expertise level
"""

import ast
import asyncio
import hashlib
import logging
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from jinja2 import DictLoader, Environment

from app.memory.hierarchical_memory import (
    AccessPattern,
    HierarchicalMemorySystem,
    MemoryEntry,
    QueryContext,
    QueryType,
)
from app.personas.persona_manager import PersonaType
from app.scaffolding.embedding_system import EmbeddingVector

# Import existing infrastructure
from app.scaffolding.meta_tagging import MetaTag

logger = logging.getLogger(__name__)


class DocumentationType(Enum):
    """Types of documentation"""

    API_REFERENCE = "api_reference"
    USER_GUIDE = "user_guide"
    TUTORIAL = "tutorial"
    ARCHITECTURE = "architecture"
    TROUBLESHOOTING = "troubleshooting"
    CHANGELOG = "changelog"
    README = "readme"
    INLINE_CODE = "inline_code"
    SYSTEM_DESIGN = "system_design"


class ComplexityLevel(Enum):
    """Complexity levels for tiered examples"""

    BEGINNER = "beginner"  # Basic usage
    INTERMEDIATE = "intermediate"  # Common patterns
    ADVANCED = "advanced"  # Complex scenarios
    EXPERT = "expert"  # Edge cases and optimizations


class DocumentStatus(Enum):
    """Status of documentation"""

    CURRENT = "current"  # Up to date
    STALE = "stale"  # Needs minor updates
    OUTDATED = "outdated"  # Needs major revision
    MISSING = "missing"  # Should exist but doesn't
    DEPRECATED = "deprecated"  # No longer relevant


class AIContextType(Enum):
    """Types of AI context sections"""

    PURPOSE = "purpose"  # What this component does
    USAGE_PATTERNS = "usage_patterns"  # How it's typically used
    INTEGRATION_POINTS = "integration_points"  # How it connects to other components
    PERFORMANCE_NOTES = "performance_notes"  # Performance characteristics
    EVOLUTION_HISTORY = "evolution_history"  # How it has changed over time
    FUTURE_CONSIDERATIONS = "future_considerations"  # Planned changes or extensions


@dataclass
class ConceptMapping:
    """Semantic concept mapping for cross-references"""

    concept_id: str
    concept_name: str
    description: str
    related_concepts: set[str] = field(default_factory=set)
    document_references: set[str] = field(default_factory=set)
    code_references: set[str] = field(default_factory=set)
    embedding_vector: Optional[EmbeddingVector] = None
    importance_score: float = 1.0
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExampleTier:
    """Example with specific complexity level"""

    level: ComplexityLevel
    title: str
    description: str
    code: str
    output: Optional[str] = None
    explanation: Optional[str] = None
    prerequisites: list[str] = field(default_factory=list)
    related_concepts: set[str] = field(default_factory=set)
    meta_tags: list[MetaTag] = field(default_factory=list)


@dataclass
class AIContextSection:
    """AI-specific context section"""

    context_type: AIContextType
    title: str
    content: str
    confidence_score: float = 1.0  # How confident we are in this context
    auto_generated: bool = False
    last_updated: datetime = field(default_factory=datetime.utcnow)
    source_analysis: Optional[dict[str, Any]] = None  # Analysis that generated this


@dataclass
class DocumentMetrics:
    """Documentation quality metrics"""

    completeness_score: float = 0.0  # 0-1, how complete is the documentation
    freshness_score: float = 0.0  # 0-1, how up-to-date is it
    clarity_score: float = 0.0  # 0-1, how clear and understandable
    coverage_score: float = 0.0  # 0-1, how much of the code is documented
    ai_context_score: float = 0.0  # 0-1, quality of AI context
    example_quality_score: float = 0.0  # 0-1, quality of examples
    cross_reference_score: float = 0.0  # 0-1, how well connected to other docs


@dataclass
class DocumentEntry:
    """Living documentation entry"""

    id: str
    title: str
    document_type: DocumentationType
    content: str
    status: DocumentStatus = DocumentStatus.CURRENT

    # Tiered examples
    examples: dict[ComplexityLevel, list[ExampleTier]] = field(default_factory=dict)

    # AI context sections
    ai_contexts: dict[AIContextType, AIContextSection] = field(default_factory=dict)

    # Semantic mappings
    concepts: set[str] = field(default_factory=set)
    related_documents: set[str] = field(default_factory=set)

    # Metadata
    meta_tags: list[MetaTag] = field(default_factory=list)
    source_files: set[str] = field(default_factory=set)
    auto_generated: bool = False
    template_used: Optional[str] = None

    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    last_code_change: Optional[datetime] = None
    update_count: int = 0

    # Quality metrics
    metrics: DocumentMetrics = field(default_factory=DocumentMetrics)

    # Embedding for semantic search
    embedding_vector: Optional[EmbeddingVector] = None


class CodeAnalyzer:
    """Analyzes code to extract documentation insights"""

    def __init__(self):
        self.function_pattern = re.compile(r"def\s+(\w+)\s*\([^)]*\):", re.MULTILINE)
        self.class_pattern = re.compile(r"class\s+(\w+)(?:\([^)]*\))?:", re.MULTILINE)
        self.docstring_pattern = re.compile(r'"""([^"]+)"""', re.DOTALL)
        self.import_pattern = re.compile(r"from\s+(\S+)\s+import|import\s+(\S+)", re.MULTILINE)

    def analyze_python_file(self, file_path: Path) -> dict[str, Any]:
        """Analyze Python file for documentation insights"""
        if not file_path.exists():
            return {}

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            analysis = {
                "file_path": str(file_path),
                "functions": self._extract_functions(tree),
                "classes": self._extract_classes(tree),
                "imports": self._extract_imports(content),
                "docstrings": self._extract_docstrings(content),
                "complexity": self._estimate_complexity(tree),
                "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime),
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {"error": str(e)}

    def _extract_functions(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extract function definitions"""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "docstring": ast.get_docstring(node),
                    "line_number": node.lineno,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                }
                functions.append(func_info)

        return functions

    def _extract_classes(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extract class definitions"""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "bases": [self._get_base_name(base) for base in node.bases],
                    "docstring": ast.get_docstring(node),
                    "line_number": node.lineno,
                    "methods": [],
                    "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                }

                # Extract methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            "name": item.name,
                            "args": [arg.arg for arg in item.args.args],
                            "docstring": ast.get_docstring(item),
                            "line_number": item.lineno,
                            "is_async": isinstance(item, ast.AsyncFunctionDef),
                        }
                        class_info["methods"].append(method_info)

                classes.append(class_info)

        return classes

    def _extract_imports(self, content: str) -> list[str]:
        """Extract import statements"""
        imports = []
        for match in self.import_pattern.finditer(content):
            if match.group(1):  # from ... import
                imports.append(match.group(1))
            if match.group(2):  # import
                imports.append(match.group(2))
        return imports

    def _extract_docstrings(self, content: str) -> list[str]:
        """Extract all docstrings"""
        return [match.group(1).strip() for match in self.docstring_pattern.finditer(content)]

    def _estimate_complexity(self, tree: ast.AST) -> dict[str, int]:
        """Estimate code complexity metrics"""
        complexity = {
            "cyclomatic_complexity": 0,
            "total_lines": 0,
            "function_count": 0,
            "class_count": 0,
        }

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                complexity["cyclomatic_complexity"] += 1
            elif isinstance(node, ast.FunctionDef):
                complexity["function_count"] += 1
            elif isinstance(node, ast.ClassDef):
                complexity["class_count"] += 1

        return complexity

    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Get decorator name as string"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{decorator.value.id}.{decorator.attr}"
        return "unknown"

    def _get_base_name(self, base: ast.AST) -> str:
        """Get base class name as string"""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{base.value.id}.{base.attr}"
        return "unknown"


class TemplateManager:
    """Manages documentation templates"""

    def __init__(self):
        self.templates = self._initialize_templates()
        self.jinja_env = Environment(loader=DictLoader(self.templates))

    def _initialize_templates(self) -> dict[str, str]:
        """Initialize built-in templates"""
        return {
            "api_reference": """# {{ title }}

## Overview

{{ description }}

{% if ai_contexts.purpose %}
### AI Context: Purpose
{{ ai_contexts.purpose.content }}
{% endif %}

## Functions

{% for func in functions %}
### {{ func.name }}

{% if func.docstring %}
{{ func.docstring }}
{% endif %}

**Parameters:**
{% for arg in func.args %}
- `{{ arg }}`: {% if arg in parameter_docs %}{{ parameter_docs[arg] }}{% else %}No description{% endif %}
{% endfor %}

{% if examples[func.name] %}
**Examples:**

{% for level, example_list in examples[func.name].items() %}
#### {{ level.value.title() }} Level
{% for example in example_list %}
{{ example.description }}

```python
{{ example.code }}
```

{% if example.output %}
**Output:**
```
{{ example.output }}
```
{% endif %}

{% if example.explanation %}
**Explanation:** {{ example.explanation }}
{% endif %}

{% endfor %}
{% endfor %}
{% endif %}

---
{% endfor %}

## Classes

{% for cls in classes %}
### {{ cls.name }}

{% if cls.docstring %}
{{ cls.docstring }}
{% endif %}

**Methods:**
{% for method in cls.methods %}
- `{{ method.name }}`: {% if method.docstring %}{{ method.docstring }}{% else %}No description{% endif %}
{% endfor %}

---
{% endfor %}

{% if related_concepts %}
## Related Concepts

{% for concept in related_concepts %}
- [{{ concept }}](#{{ concept|lower|replace(' ', '-') }})
{% endfor %}
{% endif %}

---

*This documentation was automatically generated {% if auto_generated %}by AI{% endif %} on {{ last_updated.strftime('%Y-%m-%d %H:%M:%S') }}*
""",
            "user_guide": """# {{ title }}

{{ description }}

{% if ai_contexts.usage_patterns %}
## AI Context: Usage Patterns
{{ ai_contexts.usage_patterns.content }}
{% endif %}

## Getting Started

{% if examples.beginner %}
### Basic Usage

{% for example in examples.beginner %}
#### {{ example.title }}

{{ example.description }}

```python
{{ example.code }}
```

{% if example.explanation %}
{{ example.explanation }}
{% endif %}
{% endfor %}
{% endif %}

## Common Patterns

{% if examples.intermediate %}
{% for example in examples.intermediate %}
### {{ example.title }}

{{ example.description }}

```python
{{ example.code }}
```

{% if example.explanation %}
**How it works:** {{ example.explanation }}
{% endif %}
{% endfor %}
{% endif %}

## Advanced Usage

{% if examples.advanced %}
{% for example in examples.advanced %}
### {{ example.title }}

{{ example.description }}

```python
{{ example.code }}
```

{% if example.explanation %}
**Advanced notes:** {{ example.explanation }}
{% endif %}
{% endfor %}
{% endif %}

{% if related_documents %}
## See Also

{% for doc in related_documents %}
- [{{ doc }}]({{ doc|lower|replace(' ', '-') }}.md)
{% endfor %}
{% endif %}

---

*Last updated: {{ last_updated.strftime('%Y-%m-%d %H:%M:%S') }}*
""",
            "architecture": """# {{ title }} - Architecture

{{ description }}

{% if ai_contexts.integration_points %}
## AI Context: Integration Points
{{ ai_contexts.integration_points.content }}
{% endif %}

## System Overview

{{ system_overview | default("No system overview provided.") }}

## Components

{% for component in components %}
### {{ component.name }}

**Role:** {{ component.role }}
**Description:** {{ component.description }}

{% if component.dependencies %}
**Dependencies:**
{% for dep in component.dependencies %}
- {{ dep }}
{% endfor %}
{% endif %}

{% if component.interfaces %}
**Interfaces:**
{% for interface in component.interfaces %}
- `{{ interface.name }}`: {{ interface.description }}
{% endfor %}
{% endif %}

---
{% endfor %}

## Data Flow

{{ data_flow | default("No data flow description provided.") }}

{% if performance_characteristics %}
## Performance Characteristics

{{ performance_characteristics }}
{% endif %}

{% if evolution_notes %}
## Evolution Notes

{{ evolution_notes }}
{% endif %}

---

*Architecture documented on {{ last_updated.strftime('%Y-%m-%d %H:%M:%S') }}*
""",
        }

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """Render template with context"""
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            return f"# Error\n\nFailed to render documentation: {str(e)}"

    def add_custom_template(self, name: str, content: str):
        """Add custom template"""
        self.templates[name] = content
        self.jinja_env = Environment(loader=DictLoader(self.templates))


class LivingDocumentationSystem:
    """Main living documentation system"""

    def __init__(
        self, docs_directory: Path, memory_system: Optional[HierarchicalMemorySystem] = None
    ):
        self.docs_directory = Path(docs_directory)
        self.docs_directory.mkdir(exist_ok=True)

        self.memory_system = memory_system
        self.code_analyzer = CodeAnalyzer()
        self.template_manager = TemplateManager()

        # Document storage
        self.documents: dict[str, DocumentEntry] = {}
        self.concepts: dict[str, ConceptMapping] = {}

        # Change tracking
        self.file_hashes: dict[str, str] = {}
        self.last_scan: Optional[datetime] = None

        # Metrics
        self.system_metrics = {
            "total_documents": 0,
            "auto_generated_documents": 0,
            "outdated_documents": 0,
            "average_completeness": 0.0,
            "last_update": None,
        }

    async def initialize(self):
        """Initialize the documentation system"""
        # Load existing documents
        await self._load_existing_documents()

        # Initialize concepts from memory if available
        if self.memory_system:
            await self._load_concepts_from_memory()

        logger.info(f"Initialized living documentation system with {len(self.documents)} documents")

    async def scan_and_update(self, source_directory: Path) -> dict[str, Any]:
        """Scan source code and update documentation"""
        scan_results = {
            "files_scanned": 0,
            "documents_updated": 0,
            "documents_created": 0,
            "concepts_extracted": 0,
            "errors": [],
        }

        try:
            # Scan Python files
            python_files = list(source_directory.rglob("*.py"))

            for file_path in python_files:
                try:
                    # Check if file has changed
                    current_hash = self._get_file_hash(file_path)
                    file_key = str(file_path.relative_to(source_directory))

                    if self.file_hashes.get(file_key) == current_hash:
                        continue  # No changes

                    # Analyze file
                    analysis = self.code_analyzer.analyze_python_file(file_path)
                    if "error" in analysis:
                        scan_results["errors"].append(f"{file_path}: {analysis['error']}")
                        continue

                    # Update or create documentation
                    updated = await self._update_documentation_for_file(file_path, analysis)

                    if updated:
                        scan_results["documents_updated"] += 1
                        self.file_hashes[file_key] = current_hash

                    scan_results["files_scanned"] += 1

                except Exception as e:
                    scan_results["errors"].append(f"{file_path}: {str(e)}")

            # Update system metrics
            await self._update_system_metrics()
            self.last_scan = datetime.utcnow()

        except Exception as e:
            scan_results["errors"].append(f"Scan failed: {str(e)}")

        return scan_results

    async def create_document(
        self,
        doc_id: str,
        title: str,
        doc_type: DocumentationType,
        content: str = "",
        template_name: Optional[str] = None,
        auto_generate: bool = False,
        **context,
    ) -> DocumentEntry:
        """Create new documentation entry"""

        document = DocumentEntry(
            id=doc_id,
            title=title,
            document_type=doc_type,
            content=content,
            auto_generated=auto_generate,
            template_used=template_name,
        )

        # Generate content if auto_generate is True
        if auto_generate and template_name:
            document.content = self.template_manager.render_template(
                template_name,
                {
                    "title": title,
                    "description": context.get("description", ""),
                    "last_updated": document.last_updated,
                    "auto_generated": True,
                    **context,
                },
            )

        # Extract concepts
        await self._extract_concepts_from_document(document)

        # Store document
        self.documents[doc_id] = document

        # Save to disk
        await self._save_document(document)

        # Store in memory system if available
        if self.memory_system:
            await self._store_document_in_memory(document)

        self.system_metrics["total_documents"] += 1
        if auto_generate:
            self.system_metrics["auto_generated_documents"] += 1

        return document

    async def update_document(
        self, doc_id: str, updates: dict[str, Any], preserve_manual_changes: bool = True
    ) -> Optional[DocumentEntry]:
        """Update existing document"""

        if doc_id not in self.documents:
            return None

        document = self.documents[doc_id]

        # Preserve manual changes if requested
        if preserve_manual_changes and not document.auto_generated:
            # Only update metadata, not content
            safe_updates = {
                k: v for k, v in updates.items() if k not in ["content", "examples", "ai_contexts"]
            }
            updates = safe_updates

        # Apply updates
        for key, value in updates.items():
            if hasattr(document, key):
                setattr(document, key, value)

        document.last_updated = datetime.utcnow()
        document.update_count += 1

        # Re-extract concepts
        await self._extract_concepts_from_document(document)

        # Save updates
        await self._save_document(document)

        if self.memory_system:
            await self._store_document_in_memory(document)

        return document

    async def add_example(self, doc_id: str, level: ComplexityLevel, example: ExampleTier) -> bool:
        """Add example to document"""

        if doc_id not in self.documents:
            return False

        document = self.documents[doc_id]

        if level not in document.examples:
            document.examples[level] = []

        document.examples[level].append(example)
        document.last_updated = datetime.utcnow()

        await self._save_document(document)
        return True

    async def add_ai_context(
        self, doc_id: str, context_type: AIContextType, context: AIContextSection
    ) -> bool:
        """Add AI context section to document"""

        if doc_id not in self.documents:
            return False

        document = self.documents[doc_id]
        document.ai_contexts[context_type] = context
        document.last_updated = datetime.utcnow()

        await self._save_document(document)
        return True

    async def search_documents(
        self,
        query: str,
        doc_types: Optional[list[DocumentationType]] = None,
        complexity_levels: Optional[list[ComplexityLevel]] = None,
        limit: int = 10,
    ) -> list[DocumentEntry]:
        """Search documents with semantic understanding"""

        results = []

        # Filter by type if specified
        candidates = self.documents.values()
        if doc_types:
            candidates = [d for d in candidates if d.document_type in doc_types]

        # Simple text search for now - could be enhanced with embeddings
        query_lower = query.lower()

        for document in candidates:
            score = 0.0

            # Title match
            if query_lower in document.title.lower():
                score += 10.0

            # Content match
            content_matches = document.content.lower().count(query_lower)
            score += content_matches * 2.0

            # Example matches
            for level, examples in document.examples.items():
                if not complexity_levels or level in complexity_levels:
                    for example in examples:
                        if query_lower in example.description.lower():
                            score += 5.0
                        if query_lower in example.code.lower():
                            score += 3.0

            # AI context matches
            for context in document.ai_contexts.values():
                if query_lower in context.content.lower():
                    score += 4.0

            if score > 0:
                results.append((document, score))

        # Sort by score and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in results[:limit]]

    async def get_related_documents(self, doc_id: str, limit: int = 5) -> list[DocumentEntry]:
        """Get documents related to the given document"""

        if doc_id not in self.documents:
            return []

        source_doc = self.documents[doc_id]
        related = []

        for other_id, other_doc in self.documents.items():
            if other_id == doc_id:
                continue

            # Calculate relationship score
            score = 0.0

            # Shared concepts
            shared_concepts = source_doc.concepts & other_doc.concepts
            score += len(shared_concepts) * 3.0

            # Explicit relationships
            if other_id in source_doc.related_documents:
                score += 10.0

            # Same source files
            shared_files = source_doc.source_files & other_doc.source_files
            score += len(shared_files) * 2.0

            if score > 0:
                related.append((other_doc, score))

        # Sort by score and return top results
        related.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in related[:limit]]

    async def generate_documentation_health_report(self) -> dict[str, Any]:
        """Generate comprehensive documentation health report"""

        report = {
            "overview": self.system_metrics.copy(),
            "document_status": defaultdict(int),
            "type_distribution": defaultdict(int),
            "quality_scores": {
                "completeness": [],
                "freshness": [],
                "clarity": [],
                "coverage": [],
                "ai_context": [],
                "examples": [],
                "cross_references": [],
            },
            "recommendations": [],
            "outdated_documents": [],
            "missing_examples": [],
            "weak_ai_context": [],
        }

        for document in self.documents.values():
            # Status distribution
            report["document_status"][document.status.value] += 1

            # Type distribution
            report["type_distribution"][document.document_type.value] += 1

            # Quality metrics
            metrics = document.metrics
            report["quality_scores"]["completeness"].append(metrics.completeness_score)
            report["quality_scores"]["freshness"].append(metrics.freshness_score)
            report["quality_scores"]["clarity"].append(metrics.clarity_score)
            report["quality_scores"]["coverage"].append(metrics.coverage_score)
            report["quality_scores"]["ai_context"].append(metrics.ai_context_score)
            report["quality_scores"]["examples"].append(metrics.example_quality_score)
            report["quality_scores"]["cross_references"].append(metrics.cross_reference_score)

            # Identify issues
            if document.status in [DocumentStatus.STALE, DocumentStatus.OUTDATED]:
                report["outdated_documents"].append(
                    {
                        "id": document.id,
                        "title": document.title,
                        "status": document.status.value,
                        "last_updated": document.last_updated.isoformat(),
                    }
                )

            if len(document.examples) == 0:
                report["missing_examples"].append(
                    {
                        "id": document.id,
                        "title": document.title,
                        "type": document.document_type.value,
                    }
                )

            if metrics.ai_context_score < 0.3:
                report["weak_ai_context"].append(
                    {"id": document.id, "title": document.title, "score": metrics.ai_context_score}
                )

        # Calculate averages
        for quality_type, scores in report["quality_scores"].items():
            if scores:
                report["quality_scores"][quality_type] = {
                    "average": sum(scores) / len(scores),
                    "min": min(scores),
                    "max": max(scores),
                    "count": len(scores),
                }
            else:
                report["quality_scores"][quality_type] = {
                    "average": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "count": 0,
                }

        # Generate recommendations
        if report["outdated_documents"]:
            report["recommendations"].append(
                f"Update {len(report['outdated_documents'])} outdated documents"
            )

        if report["missing_examples"]:
            report["recommendations"].append(
                f"Add examples to {len(report['missing_examples'])} documents"
            )

        if report["weak_ai_context"]:
            report["recommendations"].append(
                f"Enhance AI context for {len(report['weak_ai_context'])} documents"
            )

        return report

    async def _update_documentation_for_file(
        self, file_path: Path, analysis: dict[str, Any]
    ) -> bool:
        """Update documentation for a specific file"""

        # Create document ID from file path
        relative_path = file_path.relative_to(file_path.parent.parent)  # Adjust as needed
        doc_id = str(relative_path).replace("/", "_").replace("\\", "_").replace(".py", "")

        # Check if document exists
        if doc_id in self.documents:
            # Update existing document
            document = self.documents[doc_id]
            document.last_code_change = analysis.get("last_modified")
            document.source_files.add(str(file_path))

            # Mark as stale if code changed recently
            if document.last_code_change and document.last_code_change > document.last_updated:
                document.status = DocumentStatus.STALE

        else:
            # Create new document
            title = f"{file_path.stem.title()} Module"

            document = await self.create_document(
                doc_id=doc_id,
                title=title,
                doc_type=DocumentationType.API_REFERENCE,
                template_name="api_reference",
                auto_generate=True,
                description=f"API reference for {file_path.name}",
                functions=analysis.get("functions", []),
                classes=analysis.get("classes", []),
                imports=analysis.get("imports", []),
            )

            document.source_files.add(str(file_path))
            document.last_code_change = analysis.get("last_modified")

        # Update metrics
        await self._calculate_document_metrics(document, analysis)

        return True

    async def _extract_concepts_from_document(self, document: DocumentEntry):
        """Extract semantic concepts from document"""

        # Simple concept extraction - could be enhanced with NLP
        text_content = f"{document.title} {document.content}"

        # Extract from AI contexts
        for context in document.ai_contexts.values():
            text_content += f" {context.content}"

        # Extract from examples
        for examples_list in document.examples.values():
            for example in examples_list:
                text_content += f" {example.description} {example.explanation or ''}"

        # Simple keyword extraction (would be enhanced with proper NLP)
        words = re.findall(r"\b[A-Za-z]{4,}\b", text_content.lower())
        important_words = [
            w for w in words if w not in ["this", "that", "with", "from", "they", "have", "been"]
        ]

        # Create concepts for important terms
        for word in set(important_words[:20]):  # Top 20 concepts
            concept_id = f"concept_{hashlib.md5(word.encode()).hexdigest()[:8]}"

            if concept_id not in self.concepts:
                self.concepts[concept_id] = ConceptMapping(
                    concept_id=concept_id,
                    concept_name=word,
                    description=f"Concept extracted from {document.title}",
                )

            # Link concept to document
            self.concepts[concept_id].document_references.add(document.id)
            document.concepts.add(concept_id)

    async def _calculate_document_metrics(
        self, document: DocumentEntry, code_analysis: dict[str, Any]
    ):
        """Calculate quality metrics for document"""

        metrics = document.metrics

        # Completeness score
        completeness_factors = []
        completeness_factors.append(1.0 if document.content else 0.0)
        completeness_factors.append(1.0 if document.examples else 0.0)
        completeness_factors.append(1.0 if document.ai_contexts else 0.0)
        completeness_factors.append(1.0 if document.related_documents else 0.0)

        metrics.completeness_score = sum(completeness_factors) / len(completeness_factors)

        # Freshness score (how recent is the documentation)
        age_days = (datetime.utcnow() - document.last_updated).days
        metrics.freshness_score = max(0.0, 1.0 - (age_days / 30.0))  # Decay over 30 days

        # Clarity score (length and structure heuristics)
        content_length = len(document.content)
        if content_length > 0:
            # Simple heuristics - could be enhanced
            has_headers = bool(re.search(r"^#+\s", document.content, re.MULTILINE))
            has_lists = bool(re.search(r"^\s*[-\*]\s", document.content, re.MULTILINE))

            clarity_score = 0.5  # Base score
            if has_headers:
                clarity_score += 0.3
            if has_lists:
                clarity_score += 0.2
            if 100 < content_length < 5000:  # Good length range
                clarity_score += 0.3

            metrics.clarity_score = min(1.0, clarity_score)
        else:
            metrics.clarity_score = 0.0

        # Coverage score (how much of the code is documented)
        if code_analysis:
            total_functions = len(code_analysis.get("functions", []))
            documented_functions = sum(
                1 for f in code_analysis.get("functions", []) if f.get("docstring")
            )

            if total_functions > 0:
                metrics.coverage_score = documented_functions / total_functions
            else:
                metrics.coverage_score = 1.0  # No functions to document
        else:
            metrics.coverage_score = 0.5  # Unknown

        # AI context score
        ai_context_count = len(document.ai_contexts)
        expected_contexts = len(AIContextType)  # All context types
        metrics.ai_context_score = min(1.0, ai_context_count / expected_contexts)

        # Example quality score
        example_levels = len(document.examples)
        expected_levels = len(ComplexityLevel)
        metrics.example_quality_score = min(1.0, example_levels / expected_levels)

        # Cross-reference score
        reference_count = len(document.related_documents) + len(document.concepts)
        metrics.cross_reference_score = min(
            1.0, reference_count / 10.0
        )  # Max score at 10 references

    async def _load_existing_documents(self):
        """Load documents from disk"""
        if not self.docs_directory.exists():
            return

        for md_file in self.docs_directory.glob("*.md"):
            try:
                # Simple loading - would be enhanced with proper parsing
                content = md_file.read_text(encoding="utf-8")
                doc_id = md_file.stem

                document = DocumentEntry(
                    id=doc_id,
                    title=self._extract_title_from_content(content),
                    document_type=DocumentationType.USER_GUIDE,  # Default
                    content=content,
                    auto_generated=False,
                )

                self.documents[doc_id] = document

            except Exception as e:
                logger.error(f"Error loading document {md_file}: {e}")

    async def _load_concepts_from_memory(self):
        """Load concepts from memory system"""
        if not self.memory_system:
            return

        # Search for concept entries
        context = QueryContext(
            query_type=QueryType.SEMANTIC_SEARCH, persona_domain=PersonaType.SOPHIA
        )

        results = await self.memory_system.search("concept", context, limit=100)

        for entry in results.entries:
            if isinstance(entry.content, dict) and "concept_name" in entry.content:
                concept = ConceptMapping(**entry.content)
                self.concepts[concept.concept_id] = concept

    async def _save_document(self, document: DocumentEntry):
        """Save document to disk"""
        file_path = self.docs_directory / f"{document.id}.md"

        try:
            file_path.write_text(document.content, encoding="utf-8")
        except Exception as e:
            logger.error(f"Error saving document {document.id}: {e}")

    async def _store_document_in_memory(self, document: DocumentEntry):
        """Store document in memory system"""
        if not self.memory_system:
            return

        context = QueryContext(query_type=QueryType.EXACT_MATCH, persona_domain=PersonaType.SOPHIA)

        entry = MemoryEntry(
            id=document.id,
            content=asdict(document),
            tier=None,  # Will be determined by system
            persona_domain=PersonaType.SOPHIA,
            access_pattern=AccessPattern.WARM,
            meta_tags=document.meta_tags,
        )

        await self.memory_system.set(document.id, entry, context)

    async def _update_system_metrics(self):
        """Update system-wide metrics"""
        self.system_metrics.update(
            {
                "total_documents": len(self.documents),
                "auto_generated_documents": sum(
                    1 for d in self.documents.values() if d.auto_generated
                ),
                "outdated_documents": sum(
                    1
                    for d in self.documents.values()
                    if d.status in [DocumentStatus.STALE, DocumentStatus.OUTDATED]
                ),
                "average_completeness": sum(
                    d.metrics.completeness_score for d in self.documents.values()
                )
                / max(1, len(self.documents)),
                "last_update": datetime.utcnow(),
            }
        )

    def _extract_title_from_content(self, content: str) -> str:
        """Extract title from markdown content"""
        # Look for first h1 header
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return match.group(1) if match else "Untitled Document"

    def _get_file_hash(self, file_path: Path) -> str:
        """Get hash of file content"""
        try:
            content = file_path.read_bytes()
            return hashlib.md5(content).hexdigest()
        except Exception:
            return ""


# Factory function for easy instantiation
async def create_living_documentation_system(
    docs_directory: str, memory_system: Optional[HierarchicalMemorySystem] = None
) -> LivingDocumentationSystem:
    """Create and initialize living documentation system"""

    system = LivingDocumentationSystem(
        docs_directory=Path(docs_directory), memory_system=memory_system
    )

    await system.initialize()
    return system


# Usage example
async def main():
    """Example usage of living documentation system"""

    # Create system
    docs_system = await create_living_documentation_system("./docs")

    # Create a sample document
    await docs_system.create_document(
        doc_id="example_api",
        title="Example API Documentation",
        doc_type=DocumentationType.API_REFERENCE,
        template_name="api_reference",
        auto_generate=True,
        description="Example API for demonstration",
        functions=[
            {"name": "hello_world", "args": ["name"], "docstring": "Greet the user by name"}
        ],
    )

    # Add an example
    example = ExampleTier(
        level=ComplexityLevel.BEGINNER,
        title="Basic Greeting",
        description="Simple hello world example",
        code='hello_world("Alice")',
        output="Hello, Alice!",
        explanation="Calls the hello_world function with a name parameter",
    )

    await docs_system.add_example("example_api", ComplexityLevel.BEGINNER, example)

    # Add AI context
    ai_context = AIContextSection(
        context_type=AIContextType.PURPOSE,
        title="API Purpose",
        content="This API provides basic greeting functionality for user interaction.",
    )

    await docs_system.add_ai_context("example_api", AIContextType.PURPOSE, ai_context)

    # Generate health report
    health_report = await docs_system.generate_documentation_health_report()
    print(f"Documentation health: {health_report['overview']['total_documents']} total documents")

    # Search documents
    results = await docs_system.search_documents("greeting")
    print(f"Search results: {len(results)} documents found")


if __name__ == "__main__":
    asyncio.run(main())
