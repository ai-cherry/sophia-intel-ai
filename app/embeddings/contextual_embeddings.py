"""
Contextual Embeddings with Graph-Based Relationship Analysis

Analyzes code relationships, dependencies, and data flow to generate context-aware embeddings.
Builds comprehensive graphs of code structure and usage patterns for enhanced semantic understanding.
"""

import ast
import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import numpy as np

from .multi_modal_system import EmbeddingType, MultiModalEmbeddings

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of code relationships"""

    IMPORTS = "imports"
    INHERITS = "inherits"
    CALLS = "calls"
    DEFINES = "defines"
    USES = "uses"
    CONTAINS = "contains"
    IMPLEMENTS = "implements"
    DECORATES = "decorates"
    ASSIGNS = "assigns"
    REFERENCES = "references"


class NodeType(Enum):
    """Types of nodes in the code graph"""

    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    PROPERTY = "property"


@dataclass
class CodeNode:
    """Node in the code relationship graph"""

    id: str
    node_type: NodeType
    name: str
    file_path: str
    line_start: int
    line_end: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parent_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeRelationship:
    """Relationship between code nodes"""

    source_id: str
    target_id: str
    relationship_type: RelationshipType
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyGraph:
    """Complete dependency and relationship graph"""

    nodes: dict[str, CodeNode] = field(default_factory=dict)
    relationships: list[CodeRelationship] = field(default_factory=list)
    adjacency_list: dict[str, list[str]] = field(
        default_factory=lambda: defaultdict(list)
    )
    reverse_adjacency: dict[str, list[str]] = field(
        default_factory=lambda: defaultdict(list)
    )


class PythonASTAnalyzer:
    """Analyzes Python AST to extract code relationships"""

    def __init__(self):
        self.current_file = ""
        self.current_class = None
        self.current_function = None
        self.nodes = {}
        self.relationships = []
        self.imports = {}

    def analyze_file(
        self, file_path: str, content: str
    ) -> tuple[dict[str, CodeNode], list[CodeRelationship]]:
        """Analyze a Python file and extract code graph"""
        self.current_file = file_path
        self.nodes = {}
        self.relationships = []
        self.imports = {}
        self.current_class = None
        self.current_function = None

        try:
            tree = ast.parse(content, filename=file_path)
            self.visit_node(tree)
            return self.nodes, self.relationships

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return {}, []
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {}, []

    def visit_node(self, node):
        """Visit AST node and extract information"""
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """Generic visitor for unhandled nodes"""
        for child in ast.iter_child_nodes(node):
            self.visit_node(child)

    def visit_Module(self, node):
        """Visit module node"""
        module_id = f"module:{self.current_file}"
        module_node = CodeNode(
            id=module_id,
            node_type=NodeType.MODULE,
            name=Path(self.current_file).stem,
            file_path=self.current_file,
            line_start=1,
            line_end=(
                max(
                    getattr(child, "lineno", 1)
                    for child in ast.walk(node)
                    if hasattr(child, "lineno")
                )
                if list(ast.walk(node))
                else 1
            ),
            docstring=ast.get_docstring(node),
        )
        self.nodes[module_id] = module_node

        self.generic_visit(node)

    def visit_Import(self, node):
        """Visit import statement"""
        for alias in node.names:
            import_name = alias.name
            alias_name = alias.asname or alias.name.split(".")[-1]
            self.imports[alias_name] = import_name

            # Create import relationship
            relationship = CodeRelationship(
                source_id=f"module:{self.current_file}",
                target_id=f"module:{import_name}",
                relationship_type=RelationshipType.IMPORTS,
                metadata={"line": node.lineno, "alias": alias_name},
            )
            self.relationships.append(relationship)

    def visit_ImportFrom(self, node):
        """Visit from import statement"""
        module_name = node.module or ""
        for alias in node.names:
            import_name = alias.name
            alias_name = alias.asname or import_name
            full_name = f"{module_name}.{import_name}" if module_name else import_name
            self.imports[alias_name] = full_name

            # Create import relationship
            relationship = CodeRelationship(
                source_id=f"module:{self.current_file}",
                target_id=f"function:{full_name}",  # Could be function, class, etc.
                relationship_type=RelationshipType.IMPORTS,
                metadata={"line": node.lineno, "from_module": module_name},
            )
            self.relationships.append(relationship)

    def visit_ClassDef(self, node):
        """Visit class definition"""
        class_id = f"class:{self.current_file}:{node.name}"
        parent_class = self.current_class
        self.current_class = node.name

        # Create class node
        class_node = CodeNode(
            id=class_id,
            node_type=NodeType.CLASS,
            name=node.name,
            file_path=self.current_file,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node),
            parent_id=(
                f"class:{self.current_file}:{parent_class}"
                if parent_class
                else f"module:{self.current_file}"
            ),
            metadata={
                "decorators": [
                    self._get_decorator_name(d) for d in node.decorator_list
                ],
                "bases": [self._get_name(base) for base in node.bases],
            },
        )
        self.nodes[class_id] = class_node

        # Create inheritance relationships
        for base in node.bases:
            base_name = self._get_name(base)
            if base_name:
                relationship = CodeRelationship(
                    source_id=class_id,
                    target_id=f"class:{base_name}",  # May need resolution
                    relationship_type=RelationshipType.INHERITS,
                    metadata={"line": node.lineno},
                )
                self.relationships.append(relationship)

        # Create containment relationship
        parent_id = (
            f"class:{self.current_file}:{parent_class}"
            if parent_class
            else f"module:{self.current_file}"
        )
        relationship = CodeRelationship(
            source_id=parent_id,
            target_id=class_id,
            relationship_type=RelationshipType.CONTAINS,
            metadata={"line": node.lineno},
        )
        self.relationships.append(relationship)

        self.generic_visit(node)
        self.current_class = parent_class

    def visit_FunctionDef(self, node):
        """Visit function definition"""
        if self.current_class:
            func_id = f"method:{self.current_file}:{self.current_class}:{node.name}"
            node_type = NodeType.METHOD
            parent_id = f"class:{self.current_file}:{self.current_class}"
        else:
            func_id = f"function:{self.current_file}:{node.name}"
            node_type = NodeType.FUNCTION
            parent_id = f"module:{self.current_file}"

        # Create function signature
        signature = self._build_function_signature(node)

        # Create function node
        func_node = CodeNode(
            id=func_id,
            node_type=node_type,
            name=node.name,
            file_path=self.current_file,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            signature=signature,
            docstring=ast.get_docstring(node),
            parent_id=parent_id,
            metadata={
                "decorators": [
                    self._get_decorator_name(d) for d in node.decorator_list
                ],
                "arguments": [arg.arg for arg in node.args.args],
                "returns": self._get_annotation(node.returns) if node.returns else None,
            },
        )
        self.nodes[func_id] = func_node

        # Create containment relationship
        relationship = CodeRelationship(
            source_id=parent_id,
            target_id=func_id,
            relationship_type=RelationshipType.CONTAINS,
            metadata={"line": node.lineno},
        )
        self.relationships.append(relationship)

        # Analyze function body for calls and references
        previous_function = self.current_function
        self.current_function = node.name

        self.generic_visit(node)
        self.current_function = previous_function

    def visit_Call(self, node):
        """Visit function call"""
        caller_id = self._get_current_context_id()
        call_name = self._get_call_name(node)

        if call_name and caller_id:
            # Create call relationship
            relationship = CodeRelationship(
                source_id=caller_id,
                target_id=f"function:{call_name}",  # May need resolution
                relationship_type=RelationshipType.CALLS,
                metadata={"line": node.lineno, "args_count": len(node.args)},
            )
            self.relationships.append(relationship)

        self.generic_visit(node)

    def visit_Name(self, node):
        """Visit name reference"""
        if isinstance(node.ctx, (ast.Load, ast.Del)):
            context_id = self._get_current_context_id()
            if context_id:
                relationship = CodeRelationship(
                    source_id=context_id,
                    target_id=f"variable:{node.id}",  # May need resolution
                    relationship_type=RelationshipType.REFERENCES,
                    metadata={"line": node.lineno, "context": type(node.ctx).__name__},
                )
                self.relationships.append(relationship)

        self.generic_visit(node)

    def visit_Assign(self, node):
        """Visit assignment"""
        context_id = self._get_current_context_id()

        for target in node.targets:
            if isinstance(target, ast.Name):
                # Create variable node if it doesn't exist
                var_id = f"variable:{self.current_file}:{target.id}"
                if var_id not in self.nodes:
                    var_node = CodeNode(
                        id=var_id,
                        node_type=NodeType.VARIABLE,
                        name=target.id,
                        file_path=self.current_file,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        parent_id=context_id,
                    )
                    self.nodes[var_id] = var_node

                # Create assignment relationship
                if context_id:
                    relationship = CodeRelationship(
                        source_id=context_id,
                        target_id=var_id,
                        relationship_type=RelationshipType.ASSIGNS,
                        metadata={"line": node.lineno},
                    )
                    self.relationships.append(relationship)

        self.generic_visit(node)

    def _get_current_context_id(self) -> Optional[str]:
        """Get the ID of the current context (function/class/module)"""
        if self.current_function and self.current_class:
            return f"method:{self.current_file}:{self.current_class}:{self.current_function}"
        elif self.current_function:
            return f"function:{self.current_file}:{self.current_function}"
        elif self.current_class:
            return f"class:{self.current_file}:{self.current_class}"
        else:
            return f"module:{self.current_file}"

    def _get_name(self, node) -> Optional[str]:
        """Extract name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_name(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return None

    def _get_call_name(self, node) -> Optional[str]:
        """Extract function call name"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return self._get_name(node.func)
        return None

    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name"""
        return self._get_name(decorator) or "unknown"

    def _get_annotation(self, annotation) -> str:
        """Extract type annotation"""
        return self._get_name(annotation) or "unknown"

    def _build_function_signature(self, node) -> str:
        """Build function signature string"""
        args = []

        # Regular arguments
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {self._get_annotation(arg.annotation)}"
            args.append(arg_str)

        # Default arguments
        defaults = node.args.defaults
        if defaults:
            num_defaults = len(defaults)
            for i, default in enumerate(defaults):
                arg_idx = len(args) - num_defaults + i
                if arg_idx >= 0:
                    args[arg_idx] += f" = {self._get_name(default) or 'default'}"

        # Varargs and kwargs
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")

        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")

        signature = f"({', '.join(args)})"

        if node.returns:
            signature += f" -> {self._get_annotation(node.returns)}"

        return signature


class GraphAnalyzer:
    """Analyzes code graphs for patterns and relationships"""

    def __init__(self):
        self.graph = DependencyGraph()

    def build_graph(self, file_contents: dict[str, str]) -> DependencyGraph:
        """Build complete dependency graph from multiple files"""
        logger.info(f"Building dependency graph for {len(file_contents)} files")

        analyzer = PythonASTAnalyzer()
        all_nodes = {}
        all_relationships = []

        # Analyze each file
        for file_path, content in file_contents.items():
            try:
                nodes, relationships = analyzer.analyze_file(file_path, content)
                all_nodes.update(nodes)
                all_relationships.extend(relationships)
                logger.debug(
                    f"Analyzed {file_path}: {len(nodes)} nodes, {len(relationships)} relationships"
                )
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")

        # Build graph structure
        self.graph.nodes = all_nodes
        self.graph.relationships = all_relationships

        # Build adjacency lists
        self._build_adjacency_lists()

        # Resolve references
        self._resolve_references()

        logger.info(
            f"Built graph: {len(all_nodes)} nodes, {len(all_relationships)} relationships"
        )
        return self.graph

    def _build_adjacency_lists(self):
        """Build adjacency lists for efficient traversal"""
        self.graph.adjacency_list = defaultdict(list)
        self.graph.reverse_adjacency = defaultdict(list)

        for rel in self.graph.relationships:
            self.graph.adjacency_list[rel.source_id].append(rel.target_id)
            self.graph.reverse_adjacency[rel.target_id].append(rel.source_id)

    def _resolve_references(self):
        """Resolve symbolic references to actual nodes"""
        # This is a simplified resolution - in practice, this would be more sophisticated
        resolved_relationships = []

        for rel in self.graph.relationships:
            # Check if target exists in our graph
            if rel.target_id in self.graph.nodes:
                resolved_relationships.append(rel)
            else:
                # Try to find similar nodes
                resolved_target = self._find_similar_node(rel.target_id)
                if resolved_target:
                    resolved_rel = CodeRelationship(
                        source_id=rel.source_id,
                        target_id=resolved_target,
                        relationship_type=rel.relationship_type,
                        confidence=0.8,  # Lower confidence for resolved references
                        metadata=rel.metadata,
                    )
                    resolved_relationships.append(resolved_rel)

        self.graph.relationships = resolved_relationships
        self._build_adjacency_lists()  # Rebuild adjacency lists

    def _find_similar_node(self, node_id: str) -> Optional[str]:
        """Find similar node by name matching"""
        # Extract name from node_id
        parts = node_id.split(":")
        if len(parts) < 2:
            return None

        target_name = parts[-1]
        node_type = parts[0]

        # Look for nodes with matching name and type
        for existing_id, node in self.graph.nodes.items():
            if node.node_type.value == node_type and node.name == target_name:
                return existing_id

        return None

    def find_strongly_connected_components(self) -> list[list[str]]:
        """Find strongly connected components using Tarjan's algorithm"""
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = {}
        sccs = []

        def strongconnect(node_id):
            index[node_id] = index_counter[0]
            lowlinks[node_id] = index_counter[0]
            index_counter[0] += 1
            stack.append(node_id)
            on_stack[node_id] = True

            # Consider successors
            for successor in self.graph.adjacency_list.get(node_id, []):
                if successor not in index:
                    strongconnect(successor)
                    lowlinks[node_id] = min(lowlinks[node_id], lowlinks[successor])
                elif on_stack.get(successor, False):
                    lowlinks[node_id] = min(lowlinks[node_id], index[successor])

            # If node is a root node, pop the stack and create SCC
            if lowlinks[node_id] == index[node_id]:
                component = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    component.append(w)
                    if w == node_id:
                        break
                sccs.append(component)

        # Run algorithm on all nodes
        for node_id in self.graph.nodes:
            if node_id not in index:
                strongconnect(node_id)

        return sccs

    def compute_centrality_metrics(self) -> dict[str, dict[str, float]]:
        """Compute various centrality metrics for nodes"""
        metrics = {}

        # Degree centrality
        for node_id in self.graph.nodes:
            in_degree = len(self.graph.reverse_adjacency.get(node_id, []))
            out_degree = len(self.graph.adjacency_list.get(node_id, []))
            total_degree = in_degree + out_degree

            metrics[node_id] = {
                "in_degree_centrality": in_degree,
                "out_degree_centrality": out_degree,
                "degree_centrality": total_degree,
            }

        # Betweenness centrality (simplified)
        betweenness = self._compute_betweenness_centrality()
        for node_id, bc in betweenness.items():
            metrics[node_id]["betweenness_centrality"] = bc

        return metrics

    def _compute_betweenness_centrality(self) -> dict[str, float]:
        """Compute betweenness centrality using shortest paths"""
        betweenness = dict.fromkeys(self.graph.nodes, 0.0)

        # For each node as source
        for source in self.graph.nodes:
            # Find shortest paths using BFS
            paths = self._find_shortest_paths(source)

            # Count paths through each node
            for target in self.graph.nodes:
                if source != target and target in paths:
                    path = paths[target]
                    if len(path) > 2:  # Only consider paths with intermediate nodes
                        for intermediate in path[1:-1]:
                            betweenness[intermediate] += 1.0

        # Normalize
        n = len(self.graph.nodes)
        if n > 2:
            norm = 2.0 / ((n - 1) * (n - 2))
            for node_id in betweenness:
                betweenness[node_id] *= norm

        return betweenness

    def _find_shortest_paths(self, source: str) -> dict[str, list[str]]:
        """Find shortest paths from source to all other nodes using BFS"""
        visited = {source}
        queue = deque([(source, [source])])
        paths = {source: [source]}

        while queue:
            current, path = queue.popleft()

            for neighbor in self.graph.adjacency_list.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = path + [neighbor]
                    paths[neighbor] = new_path
                    queue.append((neighbor, new_path))

        return paths

    def find_code_clusters(self) -> dict[str, list[str]]:
        """Find clusters of related code based on relationships"""
        # Use relationship strength to cluster related code
        clusters = {}
        visited = set()
        cluster_id = 0

        for node_id in self.graph.nodes:
            if node_id not in visited:
                cluster = self._explore_cluster(node_id, visited)
                if len(cluster) > 1:  # Only keep non-trivial clusters
                    clusters[f"cluster_{cluster_id}"] = cluster
                    cluster_id += 1

        return clusters

    def _explore_cluster(self, start_node: str, visited: set[str]) -> list[str]:
        """Explore connected nodes to form a cluster"""
        cluster = []
        stack = [start_node]

        while stack:
            node_id = stack.pop()
            if node_id in visited:
                continue

            visited.add(node_id)
            cluster.append(node_id)

            # Add strongly connected neighbors
            for neighbor in self.graph.adjacency_list.get(node_id, []):
                if neighbor not in visited:
                    # Check if there's a strong relationship
                    rel_count = sum(
                        1
                        for rel in self.graph.relationships
                        if (rel.source_id == node_id and rel.target_id == neighbor)
                        or (rel.source_id == neighbor and rel.target_id == node_id)
                    )
                    if rel_count > 0:  # Simplified clustering criteria
                        stack.append(neighbor)

        return cluster

    def get_node_context(self, node_id: str, depth: int = 2) -> dict[str, Any]:
        """Get contextual information about a node"""
        if node_id not in self.graph.nodes:
            return {}

        node = self.graph.nodes[node_id]
        context = {
            "node": node,
            "incoming_relationships": [],
            "outgoing_relationships": [],
            "neighbors": {"incoming": set(), "outgoing": set()},
            "context_nodes": set(),
        }

        # Get direct relationships
        for rel in self.graph.relationships:
            if rel.target_id == node_id:
                context["incoming_relationships"].append(rel)
                context["neighbors"]["incoming"].add(rel.source_id)
            elif rel.source_id == node_id:
                context["outgoing_relationships"].append(rel)
                context["neighbors"]["outgoing"].add(rel.target_id)

        # Get extended context (neighbors of neighbors)
        context_nodes = {node_id}
        current_level = {node_id}

        for _d in range(depth):
            next_level = set()
            for current_node in current_level:
                # Add neighbors
                next_level.update(self.graph.adjacency_list.get(current_node, []))
                next_level.update(self.graph.reverse_adjacency.get(current_node, []))

            context_nodes.update(next_level)
            current_level = next_level

        context["context_nodes"] = context_nodes
        return context


class ContextualEmbeddings:
    """
    Generates context-aware embeddings using graph analysis and relationship information.
    Combines semantic embeddings with structural context for enhanced code understanding.
    """

    def __init__(self, embedding_system: MultiModalEmbeddings):
        """
        Initialize contextual embeddings system

        Args:
            embedding_system: Multi-modal embedding system for base embeddings
        """
        self.embedding_system = embedding_system
        self.graph_analyzer = GraphAnalyzer()
        self.dependency_graph = None
        self.centrality_metrics = {}
        self.code_clusters = {}

    async def build_contextual_index(
        self, file_contents: dict[str, str]
    ) -> dict[str, Any]:
        """
        Build contextual embeddings for a codebase

        Args:
            file_contents: Dictionary mapping file paths to content

        Returns:
            Dictionary with contextual embedding data
        """
        logger.info("Building contextual embeddings index")

        # Build dependency graph
        self.dependency_graph = self.graph_analyzer.build_graph(file_contents)

        # Compute graph metrics
        self.centrality_metrics = self.graph_analyzer.compute_centrality_metrics()
        self.code_clusters = self.graph_analyzer.find_code_clusters()

        # Generate contextual embeddings for each node
        contextual_embeddings = {}

        for node_id, node in self.dependency_graph.nodes.items():
            try:
                # Generate base embedding
                node_content = self._extract_node_content(node, file_contents)

                if node_content:
                    base_embedding, metadata = (
                        await self.embedding_system.generate_embedding(
                            node_content, EmbeddingType.CODE, metadata=None
                        )
                    )

                    # Get contextual information
                    context = self.graph_analyzer.get_node_context(node_id)

                    # Generate context-aware embedding
                    contextual_embedding = await self._generate_contextual_embedding(
                        base_embedding, context, node
                    )

                    contextual_embeddings[node_id] = {
                        "base_embedding": base_embedding,
                        "contextual_embedding": contextual_embedding,
                        "node": node,
                        "context": context,
                        "centrality": self.centrality_metrics.get(node_id, {}),
                        "metadata": metadata,
                    }

            except Exception as e:
                logger.warning(
                    f"Failed to generate contextual embedding for {node_id}: {e}"
                )

        logger.info(f"Generated {len(contextual_embeddings)} contextual embeddings")

        return {
            "embeddings": contextual_embeddings,
            "graph": self.dependency_graph,
            "clusters": self.code_clusters,
            "centrality_metrics": self.centrality_metrics,
            "stats": self._compute_contextual_stats(),
        }

    def _extract_node_content(
        self, node: CodeNode, file_contents: dict[str, str]
    ) -> Optional[str]:
        """Extract content for a specific node"""
        if node.file_path not in file_contents:
            return None

        content = file_contents[node.file_path]
        lines = content.split("\n")

        # Extract relevant lines for the node
        start_line = max(0, node.line_start - 1)
        end_line = min(len(lines), node.line_end)

        node_lines = lines[start_line:end_line]

        # Add context information
        context_parts = []

        # Add docstring if available
        if node.docstring:
            context_parts.append(f"'''{node.docstring}'''")

        # Add signature for functions/methods
        if node.signature:
            context_parts.append(f"def {node.name}{node.signature}:")

        # Add actual code
        context_parts.extend(node_lines)

        return "\n".join(context_parts)

    async def _generate_contextual_embedding(
        self, base_embedding: np.ndarray, context: dict[str, Any], node: CodeNode
    ) -> np.ndarray:
        """
        Generate context-aware embedding by incorporating relationship information

        Args:
            base_embedding: Base semantic embedding
            context: Contextual information from graph analysis
            node: Code node

        Returns:
            Context-enhanced embedding
        """
        # Start with base embedding
        contextual_embedding = base_embedding.copy()

        # Get neighbor embeddings
        neighbor_embeddings = []

        # Collect embeddings from related nodes
        for rel in context["incoming_relationships"][:5]:  # Limit to top 5
            neighbor_content = self._extract_neighbor_context(rel.source_id)
            if neighbor_content:
                try:
                    neighbor_emb, _ = await self.embedding_system.generate_embedding(
                        neighbor_content, EmbeddingType.CONTEXTUAL
                    )
                    neighbor_embeddings.append(neighbor_emb * rel.confidence)
                except:
                    pass

        for rel in context["outgoing_relationships"][:5]:  # Limit to top 5
            neighbor_content = self._extract_neighbor_context(rel.target_id)
            if neighbor_content:
                try:
                    neighbor_emb, _ = await self.embedding_system.generate_embedding(
                        neighbor_content, EmbeddingType.CONTEXTUAL
                    )
                    neighbor_embeddings.append(neighbor_emb * rel.confidence)
                except:
                    pass

        # Incorporate neighbor information
        if neighbor_embeddings:
            # Weighted average of neighbor embeddings
            neighbor_context = np.mean(neighbor_embeddings, axis=0)

            # Combine with base embedding (80% base, 20% context)
            contextual_embedding = 0.8 * base_embedding + 0.2 * neighbor_context

        # Add structural features based on centrality
        centrality = self.centrality_metrics.get(node.id, {})
        structural_weight = 1.0 + 0.1 * centrality.get("betweenness_centrality", 0)
        contextual_embedding *= structural_weight

        # Normalize
        norm = np.linalg.norm(contextual_embedding)
        if norm > 0:
            contextual_embedding = contextual_embedding / norm

        return contextual_embedding

    def _extract_neighbor_context(self, node_id: str) -> Optional[str]:
        """Extract brief context for a neighbor node"""
        if not self.dependency_graph or node_id not in self.dependency_graph.nodes:
            return None

        node = self.dependency_graph.nodes[node_id]

        # Return a brief description of the node
        context_parts = [f"{node.node_type.value}: {node.name}"]

        if node.docstring:
            # Use first line of docstring
            first_line = node.docstring.split("\n")[0].strip()
            if first_line:
                context_parts.append(first_line)

        if node.signature:
            context_parts.append(node.signature)

        return " | ".join(context_parts)

    def _compute_contextual_stats(self) -> dict[str, Any]:
        """Compute statistics about the contextual embedding process"""
        if not self.dependency_graph:
            return {}

        node_types = defaultdict(int)
        relationship_types = defaultdict(int)

        for node in self.dependency_graph.nodes.values():
            node_types[node.node_type.value] += 1

        for rel in self.dependency_graph.relationships:
            relationship_types[rel.relationship_type.value] += 1

        return {
            "total_nodes": len(self.dependency_graph.nodes),
            "total_relationships": len(self.dependency_graph.relationships),
            "node_type_distribution": dict(node_types),
            "relationship_type_distribution": dict(relationship_types),
            "clusters_found": len(self.code_clusters),
            "strongly_connected_components": len(
                self.graph_analyzer.find_strongly_connected_components()
            ),
        }

    def find_similar_contexts(
        self, node_id: str, k: int = 5
    ) -> list[tuple[str, float]]:
        """Find nodes with similar contextual patterns"""
        if not self.dependency_graph or node_id not in self.dependency_graph.nodes:
            return []

        self.dependency_graph.nodes[node_id]
        target_context = self.graph_analyzer.get_node_context(node_id)

        similarities = []

        for other_id, _other_node in self.dependency_graph.nodes.items():
            if other_id == node_id:
                continue

            other_context = self.graph_analyzer.get_node_context(other_id)

            # Compute contextual similarity
            similarity = self._compute_contextual_similarity(
                target_context, other_context
            )

            if similarity > 0:
                similarities.append((other_id, similarity))

        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]

    def _compute_contextual_similarity(
        self, context1: dict[str, Any], context2: dict[str, Any]
    ) -> float:
        """Compute similarity between two contextual patterns"""
        # Simple structural similarity based on relationship patterns

        # Compare relationship types
        rel_types1 = {
            rel.relationship_type
            for rel in context1["incoming_relationships"]
            + context1["outgoing_relationships"]
        }
        rel_types2 = {
            rel.relationship_type
            for rel in context2["incoming_relationships"]
            + context2["outgoing_relationships"]
        }

        if not rel_types1 and not rel_types2:
            return 0.0

        if not rel_types1 or not rel_types2:
            return 0.0

        # Jaccard similarity of relationship types
        intersection = len(rel_types1.intersection(rel_types2))
        union = len(rel_types1.union(rel_types2))

        return intersection / union if union > 0 else 0.0

    def export_graph(self, output_path: str):
        """Export dependency graph for visualization"""
        if not self.dependency_graph:
            logger.warning("No dependency graph to export")
            return

        # Export as JSON for visualization tools
        export_data = {
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.node_type.value,
                    "file": node.file_path,
                    "line_start": node.line_start,
                    "line_end": node.line_end,
                    "centrality": self.centrality_metrics.get(node.id, {}),
                }
                for node in self.dependency_graph.nodes.values()
            ],
            "edges": [
                {
                    "source": rel.source_id,
                    "target": rel.target_id,
                    "type": rel.relationship_type.value,
                    "confidence": rel.confidence,
                }
                for rel in self.dependency_graph.relationships
            ],
            "clusters": self.code_clusters,
            "stats": self._compute_contextual_stats(),
        }

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported dependency graph to {output_path}")
