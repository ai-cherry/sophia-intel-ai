"""
GraphRAG System for Multi-hop Reasoning and Relational Understanding.
Builds knowledge graphs from code, docs, and commits for enhanced context.
"""

import os
import json
import ast
import re
import networkx as nx
import sqlite3
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from collections import defaultdict

# ============================================
# Entity Types
# ============================================

class EntityType(Enum):
    """Types of entities in the knowledge graph."""
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    VARIABLE = "variable"
    MODULE = "module"
    DEPENDENCY = "dependency"
    TICKET = "ticket"
    COMMIT = "commit"
    AUTHOR = "author"
    PATTERN = "pattern"
    CONCEPT = "concept"

class RelationType(Enum):
    """Types of relationships between entities."""
    CONTAINS = "contains"
    IMPORTS = "imports"
    CALLS = "calls"
    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    USES = "uses"
    MODIFIES = "modifies"
    REFERENCES = "references"
    AUTHORED_BY = "authored_by"
    RELATED_TO = "related_to"
    DEPENDS_ON = "depends_on"

# ============================================
# Entity and Relation Models
# ============================================

@dataclass
class Entity:
    """Knowledge graph entity."""
    id: str
    type: EntityType
    name: str
    properties: Dict[str, Any]
    embeddings: Optional[List[float]] = None
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return isinstance(other, Entity) and self.id == other.id

@dataclass
class Relation:
    """Knowledge graph relation."""
    source_id: str
    target_id: str
    type: RelationType
    properties: Dict[str, Any]
    weight: float = 1.0
    
    def __hash__(self):
        return hash((self.source_id, self.target_id, self.type))

# ============================================
# Code Entity Extractors
# ============================================

class CodeEntityExtractor:
    """Extract entities and relations from code."""
    
    @staticmethod
    def extract_from_python(
        filepath: str,
        content: str
    ) -> Tuple[List[Entity], List[Relation]]:
        """
        Extract entities from Python code.
        
        Args:
            filepath: Path to the file
            content: File content
        
        Returns:
            Tuple of (entities, relations)
        """
        entities = []
        relations = []
        
        # File entity
        file_id = f"file:{filepath}"
        file_entity = Entity(
            id=file_id,
            type=EntityType.FILE,
            name=Path(filepath).name,
            properties={
                "path": filepath,
                "language": "python",
                "lines": len(content.splitlines())
            }
        )
        entities.append(file_entity)
        
        try:
            tree = ast.parse(content)
            
            # Extract classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_id = f"class:{filepath}:{node.name}"
                    class_entity = Entity(
                        id=class_id,
                        type=EntityType.CLASS,
                        name=node.name,
                        properties={
                            "file": filepath,
                            "line": node.lineno if hasattr(node, 'lineno') else 0,
                            "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                        }
                    )
                    entities.append(class_entity)
                    
                    # File contains class
                    relations.append(Relation(
                        source_id=file_id,
                        target_id=class_id,
                        type=RelationType.CONTAINS,
                        properties={}
                    ))
                    
                    # Check inheritance
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            base_id = f"class:{filepath}:{base.id}"
                            relations.append(Relation(
                                source_id=class_id,
                                target_id=base_id,
                                type=RelationType.INHERITS,
                                properties={}
                            ))
                
                elif isinstance(node, ast.FunctionDef):
                    # Skip methods (already handled in classes)
                    if not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)):
                        func_id = f"function:{filepath}:{node.name}"
                        func_entity = Entity(
                            id=func_id,
                            type=EntityType.FUNCTION,
                            name=node.name,
                            properties={
                                "file": filepath,
                                "line": node.lineno if hasattr(node, 'lineno') else 0,
                                "args": [arg.arg for arg in node.args.args]
                            }
                        )
                        entities.append(func_entity)
                        
                        relations.append(Relation(
                            source_id=file_id,
                            target_id=func_id,
                            type=RelationType.CONTAINS,
                            properties={}
                        ))
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module_id = f"module:{alias.name}"
                        module_entity = Entity(
                            id=module_id,
                            type=EntityType.MODULE,
                            name=alias.name,
                            properties={"external": True}
                        )
                        entities.append(module_entity)
                        
                        relations.append(Relation(
                            source_id=file_id,
                            target_id=module_id,
                            type=RelationType.IMPORTS,
                            properties={}
                        ))
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_id = f"module:{node.module}"
                        module_entity = Entity(
                            id=module_id,
                            type=EntityType.MODULE,
                            name=node.module,
                            properties={"external": True}
                        )
                        entities.append(module_entity)
                        
                        relations.append(Relation(
                            source_id=file_id,
                            target_id=module_id,
                            type=RelationType.IMPORTS,
                            properties={"from_import": True}
                        ))
        
        except SyntaxError:
            # If parsing fails, still return file entity
            pass
        
        return entities, relations
    
    @staticmethod
    def extract_from_javascript(
        filepath: str,
        content: str
    ) -> Tuple[List[Entity], List[Relation]]:
        """
        Extract entities from JavaScript/TypeScript code.
        
        Args:
            filepath: Path to the file
            content: File content
        
        Returns:
            Tuple of (entities, relations)
        """
        entities = []
        relations = []
        
        # File entity
        file_id = f"file:{filepath}"
        file_entity = Entity(
            id=file_id,
            type=EntityType.FILE,
            name=Path(filepath).name,
            properties={
                "path": filepath,
                "language": "javascript",
                "lines": len(content.splitlines())
            }
        )
        entities.append(file_entity)
        
        # Simple regex-based extraction for JS/TS
        # Extract classes
        class_pattern = r'(?:export\s+)?class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            class_id = f"class:{filepath}:{class_name}"
            entities.append(Entity(
                id=class_id,
                type=EntityType.CLASS,
                name=class_name,
                properties={"file": filepath}
            ))
            relations.append(Relation(
                source_id=file_id,
                target_id=class_id,
                type=RelationType.CONTAINS,
                properties={}
            ))
        
        # Extract functions
        func_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)'
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1)
            func_id = f"function:{filepath}:{func_name}"
            entities.append(Entity(
                id=func_id,
                type=EntityType.FUNCTION,
                name=func_name,
                properties={"file": filepath}
            ))
            relations.append(Relation(
                source_id=file_id,
                target_id=func_id,
                type=RelationType.CONTAINS,
                properties={}
            ))
        
        # Extract imports
        import_pattern = r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]'
        for match in re.finditer(import_pattern, content):
            module_name = match.group(1)
            module_id = f"module:{module_name}"
            entities.append(Entity(
                id=module_id,
                type=EntityType.MODULE,
                name=module_name,
                properties={"external": not module_name.startswith('.')}
            ))
            relations.append(Relation(
                source_id=file_id,
                target_id=module_id,
                type=RelationType.IMPORTS,
                properties={}
            ))
        
        return entities, relations

# ============================================
# Knowledge Graph Manager
# ============================================

class KnowledgeGraph:
    """
    Manages the knowledge graph with persistence and querying.
    """
    
    def __init__(self, db_path: str = "tmp/knowledge_graph.db"):
        self.db_path = db_path
        self.graph = nx.DiGraph()
        self._ensure_db()
        self._load_graph()
    
    def _ensure_db(self):
        """Ensure database exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Entities table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    properties TEXT,
                    embeddings TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Relations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS relations (
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    properties TEXT,
                    weight REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (source_id, target_id, type),
                    FOREIGN KEY (source_id) REFERENCES entities(id),
                    FOREIGN KEY (target_id) REFERENCES entities(id)
                )
            """)
            
            # Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entity_name ON entities(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_relation_type ON relations(type)")
            
            conn.commit()
    
    def _load_graph(self):
        """Load graph from database."""
        with sqlite3.connect(self.db_path) as conn:
            # Load entities
            cursor = conn.execute("SELECT * FROM entities")
            for row in cursor:
                entity = Entity(
                    id=row[0],
                    type=EntityType(row[1]),
                    name=row[2],
                    properties=json.loads(row[3]) if row[3] else {},
                    embeddings=json.loads(row[4]) if row[4] else None
                )
                self.graph.add_node(entity.id, entity=entity)
            
            # Load relations
            cursor = conn.execute("SELECT * FROM relations")
            for row in cursor:
                self.graph.add_edge(
                    row[0],  # source_id
                    row[1],  # target_id
                    type=RelationType(row[2]),
                    properties=json.loads(row[3]) if row[3] else {},
                    weight=row[4]
                )
    
    def add_entities(self, entities: List[Entity]):
        """Add entities to the graph."""
        with sqlite3.connect(self.db_path) as conn:
            for entity in entities:
                # Add to graph
                self.graph.add_node(entity.id, entity=entity)
                
                # Add to database
                conn.execute("""
                    INSERT OR REPLACE INTO entities
                    (id, type, name, properties, embeddings)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    entity.id,
                    entity.type.value,
                    entity.name,
                    json.dumps(entity.properties),
                    json.dumps(entity.embeddings) if entity.embeddings else None
                ))
            conn.commit()
    
    def add_relations(self, relations: List[Relation]):
        """Add relations to the graph."""
        with sqlite3.connect(self.db_path) as conn:
            for relation in relations:
                # Add to graph
                self.graph.add_edge(
                    relation.source_id,
                    relation.target_id,
                    type=relation.type,
                    properties=relation.properties,
                    weight=relation.weight
                )
                
                # Add to database
                conn.execute("""
                    INSERT OR REPLACE INTO relations
                    (source_id, target_id, type, properties, weight)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    relation.source_id,
                    relation.target_id,
                    relation.type.value,
                    json.dumps(relation.properties),
                    relation.weight
                ))
            conn.commit()
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        if entity_id in self.graph:
            return self.graph.nodes[entity_id].get('entity')
        return None
    
    def find_entities(
        self,
        entity_type: Optional[EntityType] = None,
        name_pattern: Optional[str] = None
    ) -> List[Entity]:
        """Find entities matching criteria."""
        results = []
        
        for node_id, data in self.graph.nodes(data=True):
            entity = data.get('entity')
            if not entity:
                continue
            
            # Filter by type
            if entity_type and entity.type != entity_type:
                continue
            
            # Filter by name pattern
            if name_pattern and name_pattern.lower() not in entity.name.lower():
                continue
            
            results.append(entity)
        
        return results
    
    def get_neighbors(
        self,
        entity_id: str,
        relation_type: Optional[RelationType] = None,
        direction: str = "both"
    ) -> List[Tuple[Entity, RelationType]]:
        """
        Get neighboring entities.
        
        Args:
            entity_id: Source entity ID
            relation_type: Filter by relation type
            direction: "in", "out", or "both"
        
        Returns:
            List of (entity, relation_type) tuples
        """
        results = []
        
        if entity_id not in self.graph:
            return results
        
        # Outgoing edges
        if direction in ["out", "both"]:
            for target_id in self.graph.successors(entity_id):
                edge_data = self.graph[entity_id][target_id]
                edge_type = edge_data.get('type')
                
                if relation_type and edge_type != relation_type:
                    continue
                
                target_entity = self.get_entity(target_id)
                if target_entity:
                    results.append((target_entity, edge_type))
        
        # Incoming edges
        if direction in ["in", "both"]:
            for source_id in self.graph.predecessors(entity_id):
                edge_data = self.graph[source_id][entity_id]
                edge_type = edge_data.get('type')
                
                if relation_type and edge_type != relation_type:
                    continue
                
                source_entity = self.get_entity(source_id)
                if source_entity:
                    results.append((source_entity, edge_type))
        
        return results
    
    def multi_hop_query(
        self,
        start_entity_id: str,
        max_hops: int = 3,
        relation_types: Optional[List[RelationType]] = None
    ) -> Dict[str, Any]:
        """
        Perform multi-hop traversal from starting entity.
        
        Args:
            start_entity_id: Starting entity ID
            max_hops: Maximum number of hops
            relation_types: Allowed relation types
        
        Returns:
            Subgraph and paths
        """
        if start_entity_id not in self.graph:
            return {"entities": [], "relations": [], "paths": []}
        
        visited = set()
        entities = []
        relations = []
        paths = []
        
        # BFS traversal
        queue = [(start_entity_id, 0, [start_entity_id])]
        
        while queue:
            current_id, depth, path = queue.pop(0)
            
            if current_id in visited or depth > max_hops:
                continue
            
            visited.add(current_id)
            
            # Add entity
            entity = self.get_entity(current_id)
            if entity:
                entities.append(entity)
            
            # Explore neighbors
            for neighbor_id in self.graph.successors(current_id):
                edge_data = self.graph[current_id][neighbor_id]
                edge_type = edge_data.get('type')
                
                # Filter by relation type
                if relation_types and edge_type not in relation_types:
                    continue
                
                # Add relation
                relations.append(Relation(
                    source_id=current_id,
                    target_id=neighbor_id,
                    type=edge_type,
                    properties=edge_data.get('properties', {}),
                    weight=edge_data.get('weight', 1.0)
                ))
                
                # Add to queue
                if neighbor_id not in visited:
                    new_path = path + [neighbor_id]
                    queue.append((neighbor_id, depth + 1, new_path))
                    
                    if depth + 1 <= max_hops:
                        paths.append(new_path)
        
        return {
            "entities": entities,
            "relations": relations,
            "paths": paths
        }
    
    def find_communities(self) -> List[Set[str]]:
        """Find communities in the graph."""
        # Convert to undirected for community detection
        undirected = self.graph.to_undirected()
        
        # Find connected components as simple communities
        communities = []
        for component in nx.connected_components(undirected):
            if len(component) > 1:
                communities.append(component)
        
        return communities
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        entity_counts = defaultdict(int)
        for node_id, data in self.graph.nodes(data=True):
            entity = data.get('entity')
            if entity:
                entity_counts[entity.type.value] += 1
        
        relation_counts = defaultdict(int)
        for u, v, data in self.graph.edges(data=True):
            rel_type = data.get('type')
            if rel_type:
                relation_counts[rel_type.value] += 1
        
        return {
            "total_entities": self.graph.number_of_nodes(),
            "total_relations": self.graph.number_of_edges(),
            "entity_types": dict(entity_counts),
            "relation_types": dict(relation_counts),
            "connected_components": nx.number_weakly_connected_components(self.graph),
            "average_degree": sum(dict(self.graph.degree()).values()) / max(self.graph.number_of_nodes(), 1)
        }

# ============================================
# GraphRAG Query Engine
# ============================================

class GraphRAGEngine:
    """
    Query engine that combines graph traversal with RAG.
    """
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph
    
    def augment_context_with_graph(
        self,
        query: str,
        initial_entities: List[str],
        max_hops: int = 2,
        max_entities: int = 20
    ) -> Dict[str, Any]:
        """
        Augment query context with graph information.
        
        Args:
            query: User query
            initial_entities: Starting entity IDs
            max_hops: Maximum graph traversal hops
            max_entities: Maximum entities to include
        
        Returns:
            Augmented context with graph information
        """
        all_entities = []
        all_relations = []
        all_paths = []
        
        for entity_id in initial_entities[:5]:  # Limit starting points
            result = self.kg.multi_hop_query(entity_id, max_hops)
            all_entities.extend(result["entities"])
            all_relations.extend(result["relations"])
            all_paths.extend(result["paths"])
        
        # Deduplicate entities
        unique_entities = {}
        for entity in all_entities:
            if entity.id not in unique_entities:
                unique_entities[entity.id] = entity
        
        # Limit entities
        entities = list(unique_entities.values())[:max_entities]
        
        # Build context
        context = {
            "query": query,
            "graph_entities": [
                {
                    "id": e.id,
                    "type": e.type.value,
                    "name": e.name,
                    "properties": e.properties
                }
                for e in entities
            ],
            "graph_relations": [
                {
                    "source": r.source_id,
                    "target": r.target_id,
                    "type": r.type.value
                }
                for r in all_relations[:50]  # Limit relations
            ],
            "graph_paths": all_paths[:10]  # Limit paths
        }
        
        return context
    
    def generate_community_summaries(self) -> List[Dict[str, Any]]:
        """Generate summaries for graph communities."""
        communities = self.kg.find_communities()
        summaries = []
        
        for community in communities:
            # Get entities in community
            entities = []
            for entity_id in community:
                entity = self.kg.get_entity(entity_id)
                if entity:
                    entities.append(entity)
            
            if not entities:
                continue
            
            # Group by type
            by_type = defaultdict(list)
            for entity in entities:
                by_type[entity.type.value].append(entity.name)
            
            summary = {
                "size": len(community),
                "entity_types": dict(by_type),
                "central_entities": list(community)[:5]
            }
            summaries.append(summary)
        
        return summaries

# ============================================
# CLI Interface
# ============================================

async def main():
    """CLI for GraphRAG testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GraphRAG system")
    parser.add_argument("--index", help="Index a file or directory")
    parser.add_argument("--query", help="Query the knowledge graph")
    parser.add_argument("--stats", action="store_true", help="Show graph statistics")
    parser.add_argument("--find", help="Find entities by name")
    
    args = parser.parse_args()
    
    kg = KnowledgeGraph()
    
    if args.index:
        # Index file or directory
        path = Path(args.index)
        
        if path.is_file():
            files = [path]
        else:
            files = list(path.rglob("*.py")) + list(path.rglob("*.js"))
        
        print(f"📊 Indexing {len(files)} files...")
        
        for filepath in files:
            content = filepath.read_text()
            
            if filepath.suffix == ".py":
                entities, relations = CodeEntityExtractor.extract_from_python(
                    str(filepath),
                    content
                )
            elif filepath.suffix in [".js", ".ts"]:
                entities, relations = CodeEntityExtractor.extract_from_javascript(
                    str(filepath),
                    content
                )
            else:
                continue
            
            kg.add_entities(entities)
            kg.add_relations(relations)
        
        print(f"✅ Indexed {kg.graph.number_of_nodes()} entities")
    
    elif args.find:
        entities = kg.find_entities(name_pattern=args.find)
        print(f"\n🔍 Found {len(entities)} entities:")
        for entity in entities[:10]:
            print(f"  {entity.type.value}: {entity.name} ({entity.id})")
    
    elif args.stats:
        stats = kg.get_stats()
        print("\n📊 Knowledge Graph Statistics:")
        print(f"  Total entities: {stats['total_entities']}")
        print(f"  Total relations: {stats['total_relations']}")
        print(f"  Entity types: {stats['entity_types']}")
        print(f"  Relation types: {stats['relation_types']}")
        print(f"  Connected components: {stats['connected_components']}")
        print(f"  Average degree: {stats['average_degree']:.2f}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())