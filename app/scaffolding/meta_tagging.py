"""
Meta-Tagging Engine for AI Scaffolding
=======================================

This module provides comprehensive AST-based analysis and meta-tagging for Python code,
enabling semantic understanding and AI-driven code operations.

AI Context:
- Primary consumer: AI coding assistants and swarms
- Optimization: High-frequency reads, infrequent writes
- Critical for: Code understanding, modification risk assessment, test generation
"""

import ast
import hashlib
import inspect
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class SemanticRole(Enum):
    """Semantic roles for code components"""
    
    # Orchestration roles
    ORCHESTRATOR = "orchestrator"
    COORDINATOR = "coordinator"
    DISPATCHER = "dispatcher"
    
    # Processing roles
    TRANSFORMER = "transformer"
    PROCESSOR = "processor"
    ANALYZER = "analyzer"
    
    # Validation roles
    VALIDATOR = "validator"
    SANITIZER = "sanitizer"
    GUARD = "guard"
    
    # Storage roles
    REPOSITORY = "repository"
    CACHE = "cache"
    STORE = "store"
    
    # Communication roles
    API_ENDPOINT = "api_endpoint"
    EVENT_HANDLER = "event_handler"
    MESSAGE_BROKER = "message_broker"
    
    # Utility roles
    HELPER = "helper"
    UTILITY = "utility"
    FACTORY = "factory"
    BUILDER = "builder"
    
    # AI-specific roles
    PROMPT_TEMPLATE = "prompt_template"
    EMBEDDING_GENERATOR = "embedding_generator"
    VECTOR_STORE = "vector_store"
    LLM_INTERFACE = "llm_interface"


class ComplexityLevel(Enum):
    """Code complexity levels for AI guidance"""
    
    TRIVIAL = 1  # Simple getters/setters
    LOW = 2      # Basic logic, <10 lines
    MEDIUM = 3   # Moderate logic, 10-50 lines
    HIGH = 4     # Complex logic, 50-200 lines
    CRITICAL = 5  # Critical/complex logic, >200 lines or high cyclomatic complexity


@dataclass
class AIHints:
    """AI-specific hints for code modification and understanding"""
    
    modification_risk: float = 0.5  # 0.0 (safe) to 1.0 (dangerous)
    test_requirements: List[str] = field(default_factory=list)
    optimization_potential: float = 0.0  # 0.0 (optimized) to 1.0 (needs work)
    refactoring_suggestions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    concurrency_safe: bool = True
    idempotent: bool = True
    pure_function: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "modification_risk": self.modification_risk,
            "test_requirements": self.test_requirements,
            "optimization_potential": self.optimization_potential,
            "refactoring_suggestions": self.refactoring_suggestions,
            "dependencies": self.dependencies,
            "side_effects": self.side_effects,
            "concurrency_safe": self.concurrency_safe,
            "idempotent": self.idempotent,
            "pure_function": self.pure_function,
        }


@dataclass
class CodeMetadata:
    """Comprehensive metadata for a code element"""
    
    # Identity
    name: str
    type: str  # function, class, method, module
    path: str
    line_start: int
    line_end: int
    
    # Semantic information
    semantic_role: SemanticRole
    complexity: ComplexityLevel
    description: str = ""
    
    # Structural information
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    
    # AI hints
    ai_hints: AIHints = field(default_factory=AIHints)
    
    # Relationships
    calls: List[str] = field(default_factory=list)
    called_by: List[str] = field(default_factory=list)
    
    # Content hash for change detection
    content_hash: str = ""
    
    # Tags for categorization
    tags: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "path": self.path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "semantic_role": self.semantic_role.value,
            "complexity": self.complexity.value,
            "description": self.description,
            "parent": self.parent,
            "children": self.children,
            "imports": self.imports,
            "exports": self.exports,
            "ai_hints": self.ai_hints.to_dict(),
            "calls": self.calls,
            "called_by": self.called_by,
            "content_hash": self.content_hash,
            "tags": list(self.tags),
        }


class ASTAnalyzer(ast.NodeVisitor):
    """AST visitor for extracting code metadata"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.current_class = None
        self.metadata: List[CodeMetadata] = []
        self.imports: List[str] = []
        self.call_graph: Dict[str, Set[str]] = {}
        
    def visit_Import(self, node: ast.Import) -> None:
        """Track imports"""
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track from imports"""
        if node.module:
            for alias in node.names:
                self.imports.append(f"{node.module}.{alias.name}")
        self.generic_visit(node)
        
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Analyze class definitions"""
        self.current_class = node.name
        
        # Determine semantic role
        role = self._infer_semantic_role(node.name, node)
        
        # Calculate complexity
        complexity = self._calculate_complexity(node)
        
        # Generate AI hints
        ai_hints = self._generate_ai_hints(node, is_class=True)
        
        # Extract docstring
        description = ast.get_docstring(node) or ""
        
        metadata = CodeMetadata(
            name=node.name,
            type="class",
            path=self.file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            semantic_role=role,
            complexity=complexity,
            description=description[:200],  # Limit description length
            imports=self.imports.copy(),
            ai_hints=ai_hints,
            content_hash=self._generate_hash(ast.unparse(node)),
            tags=self._generate_tags(node.name, role),
        )
        
        self.metadata.append(metadata)
        self.generic_visit(node)
        self.current_class = None
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Analyze function definitions"""
        self._analyze_function(node)
        
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Analyze async function definitions"""
        self._analyze_function(node, is_async=True)
        
    def _analyze_function(self, node: ast.FunctionDef, is_async: bool = False) -> None:
        """Common function analysis logic"""
        # Determine full name
        if self.current_class:
            full_name = f"{self.current_class}.{node.name}"
            parent = self.current_class
        else:
            full_name = node.name
            parent = None
            
        # Determine semantic role
        role = self._infer_semantic_role(node.name, node)
        
        # Calculate complexity
        complexity = self._calculate_complexity(node)
        
        # Generate AI hints
        ai_hints = self._generate_ai_hints(node, is_async=is_async)
        
        # Extract docstring
        description = ast.get_docstring(node) or ""
        
        # Find function calls
        calls = self._extract_function_calls(node)
        
        metadata = CodeMetadata(
            name=full_name,
            type="async_function" if is_async else "function",
            path=self.file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            semantic_role=role,
            complexity=complexity,
            description=description[:200],
            parent=parent,
            ai_hints=ai_hints,
            calls=calls,
            content_hash=self._generate_hash(ast.unparse(node)),
            tags=self._generate_tags(node.name, role),
        )
        
        self.metadata.append(metadata)
        self.generic_visit(node)
        
    def _infer_semantic_role(self, name: str, node: ast.AST) -> SemanticRole:
        """Infer semantic role from name and context"""
        name_lower = name.lower()
        
        # Check for specific patterns
        if "orchestrat" in name_lower:
            return SemanticRole.ORCHESTRATOR
        elif "transform" in name_lower:
            return SemanticRole.TRANSFORMER
        elif "process" in name_lower:
            return SemanticRole.PROCESSOR
        elif "validat" in name_lower:
            return SemanticRole.VALIDATOR
        elif "analyz" in name_lower or "analyse" in name_lower:
            return SemanticRole.ANALYZER
        elif "repositor" in name_lower or "repo" in name_lower:
            return SemanticRole.REPOSITORY
        elif "cache" in name_lower:
            return SemanticRole.CACHE
        elif "store" in name_lower or "storage" in name_lower:
            return SemanticRole.STORE
        elif "endpoint" in name_lower or "route" in name_lower:
            return SemanticRole.API_ENDPOINT
        elif "handler" in name_lower or "handle" in name_lower:
            return SemanticRole.EVENT_HANDLER
        elif "factory" in name_lower:
            return SemanticRole.FACTORY
        elif "builder" in name_lower or "build" in name_lower:
            return SemanticRole.BUILDER
        elif "prompt" in name_lower:
            return SemanticRole.PROMPT_TEMPLATE
        elif "embed" in name_lower:
            return SemanticRole.EMBEDDING_GENERATOR
        elif "vector" in name_lower:
            return SemanticRole.VECTOR_STORE
        elif "llm" in name_lower or "model" in name_lower:
            return SemanticRole.LLM_INTERFACE
        elif "util" in name_lower or "helper" in name_lower:
            return SemanticRole.UTILITY
        else:
            # Default based on node type
            if isinstance(node, ast.ClassDef):
                if any(base.id == "BaseModel" for base in node.bases if hasattr(base, "id")):
                    return SemanticRole.VALIDATOR
                return SemanticRole.UTILITY
            return SemanticRole.HELPER
            
    def _calculate_complexity(self, node: ast.AST) -> ComplexityLevel:
        """Calculate code complexity"""
        # Count nodes for complexity
        total_nodes = sum(1 for _ in ast.walk(node))
        
        # Count control flow statements
        control_flow = sum(
            1 for n in ast.walk(node)
            if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With))
        )
        
        # Estimate based on metrics
        if total_nodes < 20 and control_flow <= 1:
            return ComplexityLevel.TRIVIAL
        elif total_nodes < 50 and control_flow <= 3:
            return ComplexityLevel.LOW
        elif total_nodes < 200 and control_flow <= 10:
            return ComplexityLevel.MEDIUM
        elif total_nodes < 500 and control_flow <= 20:
            return ComplexityLevel.HIGH
        else:
            return ComplexityLevel.CRITICAL
            
    def _generate_ai_hints(
        self, node: ast.AST, is_class: bool = False, is_async: bool = False
    ) -> AIHints:
        """Generate AI-specific hints for code modification"""
        hints = AIHints()
        
        # Analyze for side effects
        has_io = any(
            isinstance(n, ast.Call) and hasattr(n.func, "id") and
            n.func.id in ["print", "open", "write", "read"]
            for n in ast.walk(node)
        )
        
        has_network = any(
            isinstance(n, ast.Call) and hasattr(n.func, "attr") and
            n.func.attr in ["get", "post", "put", "delete", "request"]
            for n in ast.walk(node)
        )
        
        has_db = any(
            isinstance(n, ast.Call) and hasattr(n.func, "attr") and
            any(db_op in n.func.attr.lower() for db_op in ["query", "insert", "update", "delete", "execute"])
            for n in ast.walk(node)
        )
        
        # Set modification risk
        if has_db:
            hints.modification_risk = 0.9
            hints.side_effects.append("database_operations")
        elif has_network:
            hints.modification_risk = 0.7
            hints.side_effects.append("network_operations")
        elif has_io:
            hints.modification_risk = 0.5
            hints.side_effects.append("io_operations")
        else:
            hints.modification_risk = 0.2
            
        # Analyze for concurrency safety
        if is_async:
            hints.concurrency_safe = False  # Needs careful review
            hints.test_requirements.append("async_test_required")
            
        # Check for global state modification
        has_global = any(isinstance(n, ast.Global) for n in ast.walk(node))
        if has_global:
            hints.concurrency_safe = False
            hints.side_effects.append("global_state_modification")
            hints.modification_risk = max(hints.modification_risk, 0.7)
            
        # Test requirements
        if is_class:
            hints.test_requirements.extend(["unit_test", "integration_test"])
        elif hints.modification_risk > 0.5:
            hints.test_requirements.extend(["unit_test", "integration_test", "regression_test"])
        else:
            hints.test_requirements.append("unit_test")
            
        # Optimization potential
        nested_loops = sum(
            1 for n in ast.walk(node)
            if isinstance(n, (ast.For, ast.While)) and
            any(isinstance(child, (ast.For, ast.While)) for child in ast.walk(n))
        )
        
        if nested_loops > 2:
            hints.optimization_potential = 0.9
            hints.refactoring_suggestions.append("consider_vectorization")
        elif nested_loops > 0:
            hints.optimization_potential = 0.5
            hints.refactoring_suggestions.append("review_loop_efficiency")
            
        return hints
        
    def _extract_function_calls(self, node: ast.AST) -> List[str]:
        """Extract function calls from a node"""
        calls = []
        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                if hasattr(n.func, "id"):
                    calls.append(n.func.id)
                elif hasattr(n.func, "attr"):
                    calls.append(n.func.attr)
        return calls
        
    def _generate_hash(self, content: str) -> str:
        """Generate content hash for change detection"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
        
    def _generate_tags(self, name: str, role: SemanticRole) -> Set[str]:
        """Generate descriptive tags"""
        tags = {role.value}
        
        # Add pattern-based tags
        if name.startswith("test_") or name.endswith("_test"):
            tags.add("test")
        if name.startswith("_"):
            tags.add("private")
        if name.isupper():
            tags.add("constant")
        if "async" in name.lower():
            tags.add("async")
            
        return tags


class MetaTaggingEngine:
    """Main engine for meta-tagging Python code"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.metadata_cache: Dict[str, List[CodeMetadata]] = {}
        self.call_graph: Dict[str, Set[str]] = {}
        
    def analyze_file(self, file_path: Path) -> List[CodeMetadata]:
        """Analyze a single Python file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
                
            tree = ast.parse(source, filename=str(file_path))
            analyzer = ASTAnalyzer(str(file_path.relative_to(self.project_root)))
            analyzer.visit(tree)
            
            # Cache results
            self.metadata_cache[str(file_path)] = analyzer.metadata
            
            # Update call graph
            for meta in analyzer.metadata:
                if meta.calls:
                    self.call_graph[meta.name] = set(meta.calls)
                    
            return analyzer.metadata
            
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            return []
            
    def analyze_directory(self, directory: Path) -> Dict[str, List[CodeMetadata]]:
        """Analyze all Python files in a directory recursively"""
        results = {}
        
        for py_file in directory.rglob("*.py"):
            # Skip virtual environments and cache directories
            if any(skip in py_file.parts for skip in [".venv", "venv", "__pycache__", ".git"]):
                continue
                
            metadata = self.analyze_file(py_file)
            if metadata:
                results[str(py_file)] = metadata
                
        # Build reverse call graph
        self._build_reverse_call_graph()
        
        return results
        
    def _build_reverse_call_graph(self) -> None:
        """Build the called_by relationships from call graph"""
        for caller, callees in self.call_graph.items():
            for callee in callees:
                # Find all metadata entries for the callee
                for file_meta in self.metadata_cache.values():
                    for meta in file_meta:
                        if meta.name == callee or meta.name.endswith(f".{callee}"):
                            if caller not in meta.called_by:
                                meta.called_by.append(caller)
                                
    def export_metadata(self, output_path: Path) -> None:
        """Export all metadata to JSON"""
        export_data = {}
        
        for file_path, metadata_list in self.metadata_cache.items():
            export_data[file_path] = [meta.to_dict() for meta in metadata_list]
            
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)
            
        logger.info(f"Exported metadata to {output_path}")
        
    def query_by_role(self, role: SemanticRole) -> List[CodeMetadata]:
        """Query all code elements with a specific semantic role"""
        results = []
        for metadata_list in self.metadata_cache.values():
            for meta in metadata_list:
                if meta.semantic_role == role:
                    results.append(meta)
        return results
        
    def query_by_complexity(
        self, min_complexity: ComplexityLevel, max_complexity: ComplexityLevel = None
    ) -> List[CodeMetadata]:
        """Query code elements by complexity range"""
        results = []
        max_complexity = max_complexity or ComplexityLevel.CRITICAL
        
        for metadata_list in self.metadata_cache.values():
            for meta in metadata_list:
                if min_complexity.value <= meta.complexity.value <= max_complexity.value:
                    results.append(meta)
        return results
        
    def get_modification_risks(self) -> List[Tuple[CodeMetadata, float]]:
        """Get all code elements sorted by modification risk"""
        risks = []
        for metadata_list in self.metadata_cache.values():
            for meta in metadata_list:
                risks.append((meta, meta.ai_hints.modification_risk))
                
        return sorted(risks, key=lambda x: x[1], reverse=True)


# Convenience function for quick analysis
def analyze_codebase(project_root: str = ".") -> MetaTaggingEngine:
    """Quick analysis of entire codebase"""
    engine = MetaTaggingEngine(Path(project_root))
    engine.analyze_directory(Path(project_root))
    return engine