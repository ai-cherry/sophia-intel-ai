"""
AI-Powered Documentation Generation Pipeline
=============================================

Self-documenting code system with living documentation that evolves
with the codebase, semantic indexing, and tiered complexity examples.

AI Context:
- Generates documentation from code analysis
- Creates living documentation that updates automatically
- Provides semantic concept mapping
- Generates examples for different skill levels
"""

import ast
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from app.scaffolding.meta_tagging import CodeMetadata, MetaTaggingEngine
from app.scaffolding.semantic_classifier import get_semantic_classifier

logger = logging.getLogger(__name__)


class DocumentationType(Enum):
    """Types of documentation to generate"""

    API_REFERENCE = "api_reference"
    USER_GUIDE = "user_guide"
    DEVELOPER_GUIDE = "developer_guide"
    ARCHITECTURE = "architecture"
    TUTORIAL = "tutorial"
    CHANGELOG = "changelog"
    README = "readme"
    INLINE_COMMENTS = "inline_comments"
    DOCSTRINGS = "docstrings"


class ComplexityTier(Enum):
    """Complexity tiers for examples"""

    BEGINNER = "beginner"  # Basic usage, simple cases
    INTERMEDIATE = "intermediate"  # Common patterns
    ADVANCED = "advanced"  # Complex scenarios
    EXPERT = "expert"  # Edge cases, optimizations


@dataclass
class DocumentationSection:
    """A section of documentation"""

    title: str
    content: str
    section_type: str  # overview, parameters, returns, examples, etc.
    metadata: dict[str, Any] = field(default_factory=dict)
    subsections: list["DocumentationSection"] = field(default_factory=list)
    code_examples: list[dict[str, str]] = field(default_factory=list)
    references: list[str] = field(default_factory=list)

    def to_markdown(self, level: int = 1) -> str:
        """Convert to markdown format"""
        lines = []

        # Title
        lines.append(f"{'#' * level} {self.title}")
        lines.append("")

        # Content
        if self.content:
            lines.append(self.content)
            lines.append("")

        # Code examples
        for example in self.code_examples:
            lines.append(f"**{example.get('title', 'Example')}:**")
            lines.append("```python")
            lines.append(example.get("code", ""))
            lines.append("```")
            lines.append("")

        # Subsections
        for subsection in self.subsections:
            lines.append(subsection.to_markdown(level + 1))

        # References
        if self.references:
            lines.append("**See Also:**")
            for ref in self.references:
                lines.append(f"- {ref}")
            lines.append("")

        return "\n".join(lines)


@dataclass
class ConceptMap:
    """Semantic concept mapping for documentation"""

    concepts: dict[str, list[str]]  # concept -> related items
    relationships: list[tuple[str, str, str]]  # (from, relationship, to)
    hierarchy: dict[str, list[str]]  # parent -> children

    def get_related_concepts(self, concept: str) -> list[str]:
        """Get concepts related to a given concept"""
        related = set()

        # Direct relations
        if concept in self.concepts:
            related.update(self.concepts[concept])

        # Through relationships
        for from_c, _rel, to_c in self.relationships:
            if from_c == concept:
                related.add(to_c)
            elif to_c == concept:
                related.add(from_c)

        return list(related)

    def to_mermaid(self) -> str:
        """Generate Mermaid diagram of concept map"""
        lines = ["graph TD"]

        # Add hierarchy
        for parent, children in self.hierarchy.items():
            for child in children:
                lines.append(f"    {parent} --> {child}")

        # Add relationships
        for from_c, rel, to_c in self.relationships:
            lines.append(f"    {from_c} -.{rel}.-> {to_c}")

        return "\n".join(lines)


class DocumentationGenerator:
    """Main documentation generation engine"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.meta_tagger = MetaTaggingEngine(project_root)
        self.classifier = get_semantic_classifier()
        self.template_cache: dict[str, str] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load documentation templates"""
        self.template_cache = {
            "function": """
## {name}

{description}

### Parameters

{parameters}

### Returns

{returns}

### Examples

{examples}

### Notes

{notes}
""",
            "class": """
## {name}

{description}

### Attributes

{attributes}

### Methods

{methods}

### Usage

{usage}

### See Also

{see_also}
""",
            "module": """
# {name}

{description}

## Overview

{overview}

## Installation

{installation}

## Quick Start

{quick_start}

## API Reference

{api_reference}

## Examples

{examples}

## Contributing

{contributing}
""",
        }

    def generate_documentation(
        self,
        file_path: Path,
        doc_type: DocumentationType = DocumentationType.API_REFERENCE,
        complexity_tier: ComplexityTier = ComplexityTier.INTERMEDIATE,
    ) -> DocumentationSection:
        """Generate documentation for a file"""

        # Analyze file
        metadata_list = self.meta_tagger.analyze_file(file_path)

        if not metadata_list:
            return DocumentationSection(
                title=file_path.name,
                content="No documentation available",
                section_type="empty",
            )

        # Read source code
        source = file_path.read_text()

        # Generate based on type
        if doc_type == DocumentationType.API_REFERENCE:
            return self._generate_api_reference(metadata_list, source, complexity_tier)
        elif doc_type == DocumentationType.DOCSTRINGS:
            return self._generate_docstrings(metadata_list, source)
        elif doc_type == DocumentationType.USER_GUIDE:
            return self._generate_user_guide(metadata_list, source, complexity_tier)
        else:
            return self._generate_generic(metadata_list, source, doc_type)

    def _generate_api_reference(
        self,
        metadata_list: list[CodeMetadata],
        source: str,
        complexity_tier: ComplexityTier,
    ) -> DocumentationSection:
        """Generate API reference documentation"""

        # Main section
        main_section = DocumentationSection(
            title="API Reference",
            content="Complete API documentation",
            section_type="api_reference",
        )

        # Group by type
        classes = [m for m in metadata_list if m.type == "class"]
        functions = [m for m in metadata_list if m.type in ["function", "async_function"]]

        # Document classes
        if classes:
            class_section = DocumentationSection(
                title="Classes",
                content="",
                section_type="classes",
            )

            for cls_meta in classes:
                cls_doc = self._document_class(cls_meta, source, complexity_tier)
                class_section.subsections.append(cls_doc)

            main_section.subsections.append(class_section)

        # Document functions
        if functions:
            func_section = DocumentationSection(
                title="Functions",
                content="",
                section_type="functions",
            )

            for func_meta in functions:
                func_doc = self._document_function(func_meta, source, complexity_tier)
                func_section.subsections.append(func_doc)

            main_section.subsections.append(func_section)

        return main_section

    def _document_class(
        self,
        metadata: CodeMetadata,
        source: str,
        complexity_tier: ComplexityTier,
    ) -> DocumentationSection:
        """Document a class"""

        # Extract class source
        lines = source.split("\n")
        class_source = "\n".join(lines[metadata.line_start - 1 : metadata.line_end])

        # Parse class
        try:
            tree = ast.parse(class_source)
            class_node = next(node for node in ast.walk(tree) if isinstance(node, ast.ClassDef))

            # Get docstring
            docstring = ast.get_docstring(class_node) or "No description available"

            # Get methods
            methods = []
            for item in class_node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_doc = self._extract_function_signature(item)
                    methods.append(method_doc)

            # Generate examples
            examples = self._generate_class_examples(metadata.name, methods, complexity_tier)

            section = DocumentationSection(
                title=metadata.name,
                content=docstring,
                section_type="class",
                metadata={"semantic_role": metadata.semantic_role.value},
            )

            # Add method documentation
            if methods:
                methods_section = DocumentationSection(
                    title="Methods",
                    content="",
                    section_type="methods",
                )

                for method in methods:
                    methods_section.content += (
                        f"\n- **{method['name']}**: {method.get('description', '')}"
                    )

                section.subsections.append(methods_section)

            # Add examples
            section.code_examples = examples

            return section

        except Exception as e:
            logger.error(f"Failed to document class {metadata.name}: {e}")
            return DocumentationSection(
                title=metadata.name,
                content="Documentation generation failed",
                section_type="class",
            )

    def _document_function(
        self,
        metadata: CodeMetadata,
        source: str,
        complexity_tier: ComplexityTier,
    ) -> DocumentationSection:
        """Document a function"""

        # Extract function source
        lines = source.split("\n")
        func_source = "\n".join(lines[metadata.line_start - 1 : metadata.line_end])

        try:
            tree = ast.parse(func_source)
            func_node = next(
                node
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            )

            # Get signature info
            sig_info = self._extract_function_signature(func_node)

            # Generate examples
            examples = self._generate_function_examples(metadata.name, sig_info, complexity_tier)

            section = DocumentationSection(
                title=metadata.name,
                content=sig_info.get("description", ""),
                section_type="function",
                metadata={
                    "semantic_role": metadata.semantic_role.value,
                    "is_async": metadata.type == "async_function",
                },
            )

            # Add parameter documentation
            if sig_info.get("parameters"):
                param_section = DocumentationSection(
                    title="Parameters",
                    content="",
                    section_type="parameters",
                )

                for param in sig_info["parameters"]:
                    param_section.content += f"\n- **{param['name']}** ({param.get('type', 'Any')}): {param.get('description', '')}"

                section.subsections.append(param_section)

            # Add return documentation
            if sig_info.get("returns"):
                return_section = DocumentationSection(
                    title="Returns",
                    content=f"{sig_info['returns'].get('type', 'Any')}: {sig_info['returns'].get('description', '')}",
                    section_type="returns",
                )
                section.subsections.append(return_section)

            # Add examples
            section.code_examples = examples

            # Add AI hints
            if metadata.ai_hints:
                hints_section = DocumentationSection(
                    title="AI Hints",
                    content=f"- Modification Risk: {metadata.ai_hints.modification_risk:.1%}\n"
                    f"- Optimization Potential: {metadata.ai_hints.optimization_potential:.1%}\n"
                    f"- Test Requirements: {', '.join(metadata.ai_hints.test_requirements)}",
                    section_type="ai_hints",
                )
                section.subsections.append(hints_section)

            return section

        except Exception as e:
            logger.error(f"Failed to document function {metadata.name}: {e}")
            return DocumentationSection(
                title=metadata.name,
                content="Documentation generation failed",
                section_type="function",
            )

    def _extract_function_signature(self, node: ast.FunctionDef) -> dict[str, Any]:
        """Extract function signature information"""
        info = {
            "name": node.name,
            "description": ast.get_docstring(node) or "",
            "parameters": [],
            "returns": {},
        }

        # Extract parameters
        for arg in node.args.args:
            param = {"name": arg.arg}

            # Get type annotation
            if arg.annotation:
                param["type"] = ast.unparse(arg.annotation)

            info["parameters"].append(param)

        # Extract return type
        if node.returns:
            info["returns"] = {"type": ast.unparse(node.returns)}

        # Parse docstring for parameter descriptions
        docstring = info["description"]
        if docstring:
            # Simple docstring parsing
            param_pattern = r":param\s+(\w+):\s*(.+)"
            return_pattern = r":return:\s*(.+)"

            for match in re.finditer(param_pattern, docstring):
                param_name, param_desc = match.groups()
                for param in info["parameters"]:
                    if param["name"] == param_name:
                        param["description"] = param_desc

            return_match = re.search(return_pattern, docstring)
            if return_match and info["returns"]:
                info["returns"]["description"] = return_match.group(1)

        return info

    def _generate_function_examples(
        self,
        func_name: str,
        sig_info: dict[str, Any],
        complexity_tier: ComplexityTier,
    ) -> list[dict[str, str]]:
        """Generate examples for a function"""
        examples = []

        # Generate based on complexity tier
        if complexity_tier == ComplexityTier.BEGINNER:
            examples.append(
                {
                    "title": "Basic Usage",
                    "code": f"""# Simple example
result = {func_name}()
print(result)""",
                }
            )

        elif complexity_tier == ComplexityTier.INTERMEDIATE:
            params = ", ".join(f"{p['name']}=value" for p in sig_info.get("parameters", [])[:2])
            examples.append(
                {
                    "title": "Common Usage",
                    "code": f"""# Example with parameters
result = {func_name}({params})

# Process result
if result:
    print(f"Success: {{result}}")""",
                }
            )

        elif complexity_tier == ComplexityTier.ADVANCED:
            examples.append(
                {
                    "title": "Advanced Usage",
                    "code": f"""# Advanced example with error handling
try:
    result = {func_name}(
        # Add all parameters
    )

    # Process complex result
    processed = process_result(result)

except Exception as e:
    logger.error(f"Failed: {{e}}")""",
                }
            )

        return examples

    def _generate_class_examples(
        self,
        class_name: str,
        methods: list[dict[str, Any]],
        complexity_tier: ComplexityTier,
    ) -> list[dict[str, str]]:
        """Generate examples for a class"""
        examples = []

        if complexity_tier == ComplexityTier.BEGINNER:
            examples.append(
                {
                    "title": "Basic Instantiation",
                    "code": f"""# Create instance
obj = {class_name}()

# Use basic method
result = obj.method()""",
                }
            )

        elif complexity_tier == ComplexityTier.INTERMEDIATE:
            examples.append(
                {
                    "title": "Common Pattern",
                    "code": f"""# Initialize with parameters
obj = {class_name}(param1=value1, param2=value2)

# Chain operations
result = obj.setup().process().get_result()""",
                }
            )

        return examples

    def _generate_docstrings(
        self, metadata_list: list[CodeMetadata], source: str
    ) -> DocumentationSection:
        """Generate docstring recommendations"""

        section = DocumentationSection(
            title="Docstring Recommendations",
            content="Suggested docstrings for undocumented code",
            section_type="docstrings",
        )

        for metadata in metadata_list:
            if not metadata.description:
                # Generate suggested docstring
                docstring = self._generate_suggested_docstring(metadata)

                sub_section = DocumentationSection(
                    title=metadata.name,
                    content=docstring,
                    section_type="docstring",
                    metadata={"type": metadata.type, "location": f"L{metadata.line_start}"},
                )

                section.subsections.append(sub_section)

        return section

    def _generate_suggested_docstring(self, metadata: CodeMetadata) -> str:
        """Generate suggested docstring for code element"""

        if metadata.type == "class":
            return f'''"""
{metadata.name} - {metadata.semantic_role.value.replace("_", " ").title()}

This class implements...

Attributes:
    attribute1: Description
    attribute2: Description

Example:
    >>> obj = {metadata.name}()
    >>> obj.method()
"""'''

        elif metadata.type in ["function", "async_function"]:
            async_prefix = "async " if metadata.type == "async_function" else ""
            return f'''"""
{metadata.semantic_role.value.replace("_", " ").title()} function

Args:
    param1: Description
    param2: Description

Returns:
    Description of return value

Raises:
    ExceptionType: When this happens

Example:
    >>> {async_prefix}result = {metadata.name}(param1, param2)
"""'''

        return '"""Add description here"""'

    def _generate_user_guide(
        self,
        metadata_list: list[CodeMetadata],
        source: str,
        complexity_tier: ComplexityTier,
    ) -> DocumentationSection:
        """Generate user guide"""

        section = DocumentationSection(
            title="User Guide",
            content="Guide for using this module",
            section_type="user_guide",
        )

        # Add getting started
        section.subsections.append(
            DocumentationSection(
                title="Getting Started",
                content="Quick introduction to using this module",
                section_type="getting_started",
                code_examples=[
                    {
                        "title": "Installation",
                        "code": "pip install module-name",
                    }
                ],
            )
        )

        # Add common use cases
        use_cases = self._generate_use_cases(metadata_list, complexity_tier)
        section.subsections.append(use_cases)

        return section

    def _generate_use_cases(
        self, metadata_list: list[CodeMetadata], complexity_tier: ComplexityTier
    ) -> DocumentationSection:
        """Generate common use cases"""

        section = DocumentationSection(
            title="Common Use Cases",
            content="",
            section_type="use_cases",
        )

        # Group by semantic role
        roles = {}
        for metadata in metadata_list:
            role = metadata.semantic_role.value
            if role not in roles:
                roles[role] = []
            roles[role].append(metadata)

        # Generate use cases for each role
        for role, items in roles.items():
            if items:
                use_case = DocumentationSection(
                    title=role.replace("_", " ").title(),
                    content=f"How to use {role} components",
                    section_type="use_case",
                )
                section.subsections.append(use_case)

        return section

    def _generate_generic(
        self,
        metadata_list: list[CodeMetadata],
        source: str,
        doc_type: DocumentationType,
    ) -> DocumentationSection:
        """Generate generic documentation"""

        return DocumentationSection(
            title=doc_type.value.replace("_", " ").title(),
            content=f"Generated {doc_type.value} documentation",
            section_type=doc_type.value,
        )

    def build_concept_map(self, metadata_list: list[CodeMetadata]) -> ConceptMap:
        """Build semantic concept map from metadata"""

        concepts = {}
        relationships = []
        hierarchy = {}

        # Extract concepts
        for metadata in metadata_list:
            concept = metadata.semantic_role.value

            if concept not in concepts:
                concepts[concept] = []

            concepts[concept].append(metadata.name)

            # Build hierarchy
            if metadata.parent:
                if metadata.parent not in hierarchy:
                    hierarchy[metadata.parent] = []
                hierarchy[metadata.parent].append(metadata.name)

            # Extract relationships
            for called in metadata.calls:
                relationships.append((metadata.name, "calls", called))

        return ConceptMap(concepts, relationships, hierarchy)

    def generate_living_documentation(self, output_dir: Path, watch: bool = False) -> None:
        """Generate living documentation that updates automatically"""

        output_dir.mkdir(parents=True, exist_ok=True)

        # Analyze entire codebase
        all_metadata = self.meta_tagger.analyze_directory(self.project_root)

        # Generate main documentation
        main_doc = DocumentationSection(
            title=self.project_root.name,
            content="Auto-generated documentation",
            section_type="main",
        )

        # Add sections for each module
        for file_path, metadata_list in all_metadata.items():
            if metadata_list:
                module_doc = self.generate_documentation(
                    Path(file_path),
                    DocumentationType.API_REFERENCE,
                    ComplexityTier.INTERMEDIATE,
                )
                main_doc.subsections.append(module_doc)

        # Generate concept map
        all_meta_flat = [m for mlist in all_metadata.values() for m in mlist]
        concept_map = self.build_concept_map(all_meta_flat)

        # Write documentation
        main_file = output_dir / "index.md"
        main_file.write_text(main_doc.to_markdown())

        # Write concept map
        concept_file = output_dir / "concepts.md"
        concept_content = f"""# Concept Map

## Visualization

```mermaid
{concept_map.to_mermaid()}
```

## Concepts

"""
        for concept, items in concept_map.concepts.items():
            concept_content += f"\n### {concept}\n"
            for item in items:
                concept_content += f"- {item}\n"

        concept_file.write_text(concept_content)

        logger.info(f"Generated documentation in {output_dir}")

        # Watch for changes if requested
        if watch:
            self._watch_for_changes(output_dir)

    def _watch_for_changes(self, output_dir: Path) -> None:
        """Watch for code changes and update documentation"""
        # This would implement file watching
        # For now, just log
        logger.info("Watching for changes (not implemented)")


# Convenience function
def generate_project_docs(
    project_root: str = ".",
    output_dir: str = "docs/generated",
    watch: bool = False,
) -> None:
    """Generate documentation for entire project"""
    generator = DocumentationGenerator(Path(project_root))
    generator.generate_living_documentation(Path(output_dir), watch)
