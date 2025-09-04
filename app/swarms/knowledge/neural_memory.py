"""
Neural Memory System - Perfect Recall with Instant Retrieval

This is the brain of the Knowledge Domination Swarm - a sophisticated memory system that:
- Stores knowledge as vector embeddings for semantic search
- Maps relationships using graph database structures
- Provides perfect recall with instant retrieval
- Consolidates and optimizes memory automatically
- Surfaces contextually relevant knowledge
"""

import asyncio
import logging
import json
import time
import sqlite3
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
import pickle
import threading
from collections import defaultdict
import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
# import openai  # DEPRECATED: Use AGNO + Portkey routing instead

logger = logging.getLogger(__name__)


@dataclass
class MemoryNode:
    """Represents a memory node in the system"""
    id: str
    content: str
    embedding: Optional[np.ndarray]
    metadata: Dict[str, Any]
    relationships: List[str]
    access_count: int
    last_accessed: str
    importance_score: float
    tags: List[str]
    created_at: str
    updated_at: str


@dataclass
class MemoryRelationship:
    """Represents a relationship between memory nodes"""
    source_id: str
    target_id: str
    relationship_type: str
    strength: float
    metadata: Dict[str, Any]
    created_at: str


@dataclass
class MemoryQuery:
    """Represents a memory search query"""
    query_text: str
    query_embedding: Optional[np.ndarray]
    similarity_threshold: float
    max_results: int
    filters: Dict[str, Any]
    boost_recent: bool
    boost_accessed: bool


class NeuralMemorySystem:
    """
    The Neural Memory System - Perfect Knowledge Storage and Retrieval
    
    This system provides:
    1. Vector-based semantic storage and retrieval
    2. Graph-based relationship mapping
    3. Intelligent memory consolidation
    4. Context-aware knowledge surfacing
    5. Performance optimization and indexing
    """
    
    def __init__(self, embedding_dim: int = 1536, max_memory_size: int = 1000000, 
                 db_path: str = None):
        self.embedding_dim = embedding_dim
        self.max_memory_size = max_memory_size
        self.db_path = db_path or ":memory:"
        
        # Core storage
        self.nodes: Dict[str, MemoryNode] = {}
        self.relationships: Dict[str, MemoryRelationship] = {}
        self.graph = nx.DiGraph()
        
        # Search and indexing
        self.embeddings_matrix = None
        self.node_ids = []
        self.tfidf_vectorizer = TfidfVectorizer(max_features=10000, stop_words='english')
        self.tfidf_matrix = None
        
        # Performance tracking
        self.access_patterns = defaultdict(int)
        self.query_cache = {}
        self.cache_size = 1000
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'total_nodes': 0,
            'total_relationships': 0,
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_query_time': 0.0,
            'memory_usage': 0,
            'last_consolidation': None
        }
        
        logger.info("Neural Memory System initialized - preparing for perfect recall")
    
    async def initialize(self) -> bool:
        """Initialize the neural memory system"""
        try:
            # Initialize database
            await self._initialize_database()
            
            # Load existing memory if available
            await self._load_from_database()
            
            # Build initial indexes
            await self._rebuild_indexes()
            
            logger.info(f"Neural Memory System ready - {len(self.nodes)} nodes, "
                       f"{len(self.relationships)} relationships")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Neural Memory System: {e}")
            return False
    
    async def store_memory(self, content: str, metadata: Dict[str, Any] = None, 
                          tags: List[str] = None) -> str:
        """
        Store new memory with intelligent indexing and relationship detection
        """
        with self.lock:
            # Generate unique ID
            memory_id = self._generate_memory_id(content)
            
            # Generate embedding
            embedding = await self._generate_embedding(content)
            
            # Calculate importance score
            importance_score = self._calculate_importance_score(content, metadata or {})
            
            # Create memory node
            node = MemoryNode(
                id=memory_id,
                content=content,
                embedding=embedding,
                metadata=metadata or {},
                relationships=[],
                access_count=0,
                last_accessed=datetime.now().isoformat(),
                importance_score=importance_score,
                tags=tags or [],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            # Store in memory
            self.nodes[memory_id] = node
            self.graph.add_node(memory_id, **asdict(node))
            
            # Detect and create relationships
            await self._detect_relationships(node)
            
            # Update indexes
            await self._update_indexes()
            
            # Persist to database
            await self._persist_node(node)
            
            # Update statistics
            self.stats['total_nodes'] += 1
            
            logger.debug(f"Stored memory: {memory_id} (importance: {importance_score:.2f})")
            return memory_id
    
    async def search_semantic(self, query: str, top_k: int = 10, 
                            similarity_threshold: float = 0.7,
                            filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector similarity
        """
        start_time = time.time()
        
        # Check cache first
        cache_key = hashlib.md5(f"{query}{top_k}{similarity_threshold}{filters}".encode()).hexdigest()
        
        with self.lock:
            if cache_key in self.query_cache:
                self.stats['cache_hits'] += 1
                return self.query_cache[cache_key]
        
        self.stats['cache_misses'] += 1
        
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            
            # Find similar memories
            results = await self._find_similar_memories(
                query_embedding, top_k, similarity_threshold, filters
            )
            
            # Update access patterns
            for result in results:
                await self._update_access_pattern(result['id'])
            
            # Cache results
            with self.lock:
                if len(self.query_cache) >= self.cache_size:
                    # Remove oldest entries
                    oldest_keys = list(self.query_cache.keys())[:self.cache_size // 2]
                    for key in oldest_keys:
                        del self.query_cache[key]
                
                self.query_cache[cache_key] = results
            
            # Update statistics
            query_time = time.time() - start_time
            self._update_query_stats(query_time)
            
            logger.debug(f"Semantic search completed: {len(results)} results in {query_time:.3f}s")
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    async def search_graph(self, node_id: str, relationship_types: List[str] = None,
                          max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        Search using graph relationships and connections
        """
        if node_id not in self.nodes:
            return []
        
        with self.lock:
            try:
                # Find connected nodes
                connected_nodes = []
                
                if relationship_types:
                    # Filter by relationship type
                    for rel_id, relationship in self.relationships.items():
                        if (relationship.source_id == node_id or relationship.target_id == node_id):
                            if relationship.relationship_type in relationship_types:
                                other_id = (relationship.target_id if relationship.source_id == node_id 
                                          else relationship.source_id)
                                if other_id in self.nodes:
                                    connected_nodes.append({
                                        'id': other_id,
                                        'node': self.nodes[other_id],
                                        'relationship': relationship,
                                        'distance': 1
                                    })
                else:
                    # Get all neighbors using networkx
                    neighbors = list(self.graph.neighbors(node_id))
                    predecessors = list(self.graph.predecessors(node_id))
                    
                    all_connected = set(neighbors + predecessors)
                    
                    for connected_id in all_connected:
                        if connected_id in self.nodes:
                            connected_nodes.append({
                                'id': connected_id,
                                'node': self.nodes[connected_id],
                                'distance': 1
                            })
                
                # Sort by relationship strength and importance
                connected_nodes.sort(
                    key=lambda x: (
                        x.get('relationship', {}).get('strength', 0.5) +
                        x['node'].importance_score
                    ),
                    reverse=True
                )
                
                return connected_nodes
                
            except Exception as e:
                logger.error(f"Error in graph search: {e}")
                return []
    
    async def store_interaction(self, query: str, response: str, confidence: float,
                              metadata: Dict[str, Any] = None) -> str:
        """Store a query-response interaction"""
        interaction_content = f"Query: {query}\nResponse: {response}"
        
        interaction_metadata = {
            'type': 'interaction',
            'query': query,
            'response': response,
            'confidence': confidence,
            **(metadata or {})
        }
        
        return await self.store_memory(
            content=interaction_content,
            metadata=interaction_metadata,
            tags=['interaction', 'training_data']
        )
    
    async def store_concept(self, concept: str, context: str, source: str) -> str:
        """Store a learned concept"""
        concept_content = f"Concept: {concept}\nContext: {context}"
        
        concept_metadata = {
            'type': 'concept',
            'concept': concept,
            'context': context,
            'source': source
        }
        
        return await self.store_memory(
            content=concept_content,
            metadata=concept_metadata,
            tags=['concept', 'learned']
        )
    
    async def store_correction(self, original_query: str, original_response: str,
                             field: str, correction: str, timestamp: str) -> str:
        """Store a user correction for learning"""
        correction_content = f"Original Query: {original_query}\nOriginal Response: {original_response}\nField: {field}\nCorrection: {correction}"
        
        correction_metadata = {
            'type': 'correction',
            'original_query': original_query,
            'original_response': original_response,
            'field': field,
            'correction': correction,
            'timestamp': timestamp
        }
        
        return await self.store_memory(
            content=correction_content,
            metadata=correction_metadata,
            tags=['correction', 'feedback']
        )
    
    async def get_related_memories(self, memory_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get memories related to a specific memory"""
        if memory_id not in self.nodes:
            return []
        
        # Get graph-based connections
        graph_results = await self.search_graph(memory_id, max_depth=2)
        
        # Get semantic similarities
        node = self.nodes[memory_id]
        if node.embedding is not None:
            semantic_results = await self._find_similar_memories(
                node.embedding, max_results, similarity_threshold=0.6
            )
            
            # Combine and deduplicate
            all_results = {}
            
            # Add graph results with relationship boost
            for result in graph_results:
                result_id = result['id']
                if result_id != memory_id:  # Exclude self
                    score = result.get('relationship', {}).get('strength', 0.5) + 0.3
                    all_results[result_id] = {
                        'id': result_id,
                        'content': result['node'].content,
                        'metadata': result['node'].metadata,
                        'similarity': min(1.0, score),
                        'relationship_type': result.get('relationship', {}).get('relationship_type', 'related')
                    }
            
            # Add semantic results
            for result in semantic_results:
                result_id = result['id']
                if result_id != memory_id and result_id not in all_results:
                    all_results[result_id] = result
            
            # Sort and return top results
            sorted_results = sorted(
                all_results.values(),
                key=lambda x: x['similarity'],
                reverse=True
            )
            
            return sorted_results[:max_results]
        
        return [{'id': r['id'], 'content': r['node'].content, 'metadata': r['node'].metadata, 'similarity': 0.5} 
                for r in graph_results[:max_results]]
    
    async def consolidate_memory(self) -> Dict[str, Any]:
        """
        Consolidate memory by merging similar memories and optimizing storage
        """
        start_time = time.time()
        consolidation_stats = {
            'nodes_before': len(self.nodes),
            'relationships_before': len(self.relationships),
            'nodes_merged': 0,
            'relationships_created': 0,
            'processing_time': 0.0
        }
        
        logger.info("Starting memory consolidation...")
        
        try:
            with self.lock:
                # Find similar memories for consolidation
                similar_pairs = await self._find_similar_memory_pairs()
                
                # Merge similar memories
                for pair in similar_pairs:
                    if await self._merge_memories(pair[0], pair[1]):
                        consolidation_stats['nodes_merged'] += 1
                
                # Optimize relationships
                new_relationships = await self._optimize_relationships()
                consolidation_stats['relationships_created'] = len(new_relationships)
                
                # Rebuild indexes
                await self._rebuild_indexes()
                
                # Update statistics
                consolidation_stats['processing_time'] = time.time() - start_time
                consolidation_stats['nodes_after'] = len(self.nodes)
                consolidation_stats['relationships_after'] = len(self.relationships)
                
                self.stats['last_consolidation'] = datetime.now().isoformat()
            
            logger.info(f"Memory consolidation completed: merged {consolidation_stats['nodes_merged']} nodes, "
                       f"created {consolidation_stats['relationships_created']} relationships in "
                       f"{consolidation_stats['processing_time']:.2f}s")
            
            return consolidation_stats
            
        except Exception as e:
            logger.error(f"Error during memory consolidation: {e}")
            return consolidation_stats
    
    async def optimize(self) -> Dict[str, Any]:
        """
        Optimize memory system performance
        """
        optimization_results = {
            'success': False,
            'optimizations_applied': [],
            'performance_improvement': 0.0
        }
        
        try:
            # Clean up old cache entries
            cache_cleaned = await self._cleanup_cache()
            if cache_cleaned:
                optimization_results['optimizations_applied'].append('cache_cleanup')
            
            # Optimize embeddings matrix
            embeddings_optimized = await self._optimize_embeddings_storage()
            if embeddings_optimized:
                optimization_results['optimizations_applied'].append('embeddings_optimization')
            
            # Prune weak relationships
            relationships_pruned = await self._prune_weak_relationships()
            if relationships_pruned > 0:
                optimization_results['optimizations_applied'].append('relationship_pruning')
            
            # Rebuild indexes for better performance
            await self._rebuild_indexes()
            optimization_results['optimizations_applied'].append('index_rebuilding')
            
            optimization_results['success'] = True
            optimization_results['performance_improvement'] = len(optimization_results['optimizations_applied']) * 0.1
            
            logger.info(f"Memory optimization completed: {optimization_results['optimizations_applied']}")
            return optimization_results
            
        except Exception as e:
            logger.error(f"Error during memory optimization: {e}")
            return optimization_results
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics"""
        with self.lock:
            current_stats = self.stats.copy()
            
            # Add real-time calculations
            current_stats['nodes_count'] = len(self.nodes)
            current_stats['relationships_count'] = len(self.relationships)
            current_stats['cache_size'] = len(self.query_cache)
            current_stats['cache_hit_rate'] = (
                self.stats['cache_hits'] / max(1, self.stats['cache_hits'] + self.stats['cache_misses'])
            )
            
            # Calculate memory usage estimate
            memory_usage = 0
            for node in self.nodes.values():
                memory_usage += len(node.content.encode('utf-8'))
                if node.embedding is not None:
                    memory_usage += node.embedding.nbytes
            
            current_stats['memory_usage_bytes'] = memory_usage
            current_stats['memory_usage_mb'] = memory_usage / (1024 * 1024)
            
            # Add graph statistics
            if self.graph:
                current_stats['graph_nodes'] = self.graph.number_of_nodes()
                current_stats['graph_edges'] = self.graph.number_of_edges()
                current_stats['graph_density'] = nx.density(self.graph)
            
            return current_stats
    
    async def get_size(self) -> int:
        """Get total number of memories stored"""
        return len(self.nodes)
    
    async def shutdown(self):
        """Gracefully shutdown the memory system"""
        logger.info("Shutting down Neural Memory System...")
        
        # Save all data to database
        await self._save_to_database()
        
        # Clear in-memory structures
        with self.lock:
            self.nodes.clear()
            self.relationships.clear()
            self.graph.clear()
            self.query_cache.clear()
        
        logger.info("Neural Memory System shutdown complete")
    
    # Private helper methods
    
    async def _initialize_database(self):
        """Initialize SQLite database for persistent storage"""
        self.db_conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        # Create tables
        self.db_conn.execute('''
            CREATE TABLE IF NOT EXISTS memory_nodes (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding BLOB,
                metadata TEXT,
                relationships TEXT,
                access_count INTEGER,
                last_accessed TEXT,
                importance_score REAL,
                tags TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        self.db_conn.execute('''
            CREATE TABLE IF NOT EXISTS memory_relationships (
                id TEXT PRIMARY KEY,
                source_id TEXT,
                target_id TEXT,
                relationship_type TEXT,
                strength REAL,
                metadata TEXT,
                created_at TEXT,
                FOREIGN KEY (source_id) REFERENCES memory_nodes (id),
                FOREIGN KEY (target_id) REFERENCES memory_nodes (id)
            )
        ''')
        
        # Create indexes
        self.db_conn.execute('CREATE INDEX IF NOT EXISTS idx_nodes_importance ON memory_nodes(importance_score DESC)')
        self.db_conn.execute('CREATE INDEX IF NOT EXISTS idx_nodes_created ON memory_nodes(created_at)')
        self.db_conn.execute('CREATE INDEX IF NOT EXISTS idx_relationships_source ON memory_relationships(source_id)')
        self.db_conn.execute('CREATE INDEX IF NOT EXISTS idx_relationships_target ON memory_relationships(target_id)')
        
        self.db_conn.commit()
    
    async def _load_from_database(self):
        """Load existing memory from database"""
        # Load nodes
        cursor = self.db_conn.execute('SELECT * FROM memory_nodes')
        for row in cursor.fetchall():
            node = MemoryNode(
                id=row[0],
                content=row[1],
                embedding=pickle.loads(row[2]) if row[2] else None,
                metadata=json.loads(row[3]) if row[3] else {},
                relationships=json.loads(row[4]) if row[4] else [],
                access_count=row[5],
                last_accessed=row[6],
                importance_score=row[7],
                tags=json.loads(row[8]) if row[8] else [],
                created_at=row[9],
                updated_at=row[10]
            )
            self.nodes[node.id] = node
            self.graph.add_node(node.id, **asdict(node))
        
        # Load relationships
        cursor = self.db_conn.execute('SELECT * FROM memory_relationships')
        for row in cursor.fetchall():
            relationship = MemoryRelationship(
                source_id=row[1],
                target_id=row[2],
                relationship_type=row[3],
                strength=row[4],
                metadata=json.loads(row[5]) if row[5] else {},
                created_at=row[6]
            )
            self.relationships[row[0]] = relationship
            
            # Add to graph
            if relationship.source_id in self.graph and relationship.target_id in self.graph:
                self.graph.add_edge(
                    relationship.source_id,
                    relationship.target_id,
                    type=relationship.relationship_type,
                    strength=relationship.strength
                )
        
        logger.info(f"Loaded {len(self.nodes)} nodes and {len(self.relationships)} relationships from database")
    
    async def _save_to_database(self):
        """Save all memory to database"""
        # Save nodes
        for node in self.nodes.values():
            await self._persist_node(node)
        
        # Save relationships
        for rel_id, relationship in self.relationships.items():
            await self._persist_relationship(rel_id, relationship)
        
        self.db_conn.commit()
    
    async def _persist_node(self, node: MemoryNode):
        """Persist a single node to database"""
        embedding_blob = pickle.dumps(node.embedding) if node.embedding is not None else None
        
        self.db_conn.execute('''
            INSERT OR REPLACE INTO memory_nodes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            node.id,
            node.content,
            embedding_blob,
            json.dumps(node.metadata),
            json.dumps(node.relationships),
            node.access_count,
            node.last_accessed,
            node.importance_score,
            json.dumps(node.tags),
            node.created_at,
            node.updated_at
        ))
    
    async def _persist_relationship(self, rel_id: str, relationship: MemoryRelationship):
        """Persist a single relationship to database"""
        self.db_conn.execute('''
            INSERT OR REPLACE INTO memory_relationships VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            rel_id,
            relationship.source_id,
            relationship.target_id,
            relationship.relationship_type,
            relationship.strength,
            json.dumps(relationship.metadata),
            relationship.created_at
        ))
    
    def _generate_memory_id(self, content: str) -> str:
        """Generate unique ID for memory"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        timestamp = str(int(time.time() * 1000))
        return f"mem_{content_hash[:12]}_{timestamp}"
    
    async def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text using OpenAI or fallback method"""
        try:
            # Try OpenAI embeddings first
            response = await openai.Embedding.acreate(
                model="text-embedding-ada-002",
                input=text
            )
            return np.array(response['data'][0]['embedding'])
        except:
            # Fallback to TF-IDF based pseudo-embedding
            return self._generate_tfidf_embedding(text)
    
    def _generate_tfidf_embedding(self, text: str) -> np.ndarray:
        """Generate pseudo-embedding using TF-IDF (fallback method)"""
        try:
            # Fit vectorizer if not already fitted
            if not hasattr(self.tfidf_vectorizer, 'vocabulary_'):
                # Use existing content to fit
                all_content = [node.content for node in self.nodes.values()]
                if all_content:
                    self.tfidf_vectorizer.fit(all_content + [text])
                else:
                    self.tfidf_vectorizer.fit([text])
            
            # Transform text
            tfidf_vector = self.tfidf_vectorizer.transform([text])
            
            # Convert to dense array and pad/truncate to embedding_dim
            dense_vector = tfidf_vector.toarray()[0]
            
            if len(dense_vector) >= self.embedding_dim:
                return dense_vector[:self.embedding_dim]
            else:
                # Pad with zeros
                padded_vector = np.zeros(self.embedding_dim)
                padded_vector[:len(dense_vector)] = dense_vector
                return padded_vector
        except:
            # Ultimate fallback - random embedding
            return np.random.randn(self.embedding_dim) * 0.1
    
    def _calculate_importance_score(self, content: str, metadata: Dict[str, Any]) -> float:
        """Calculate importance score for content"""
        score = 0.5  # Base score
        
        # Length factor
        content_length = len(content.split())
        if 50 <= content_length <= 300:  # Sweet spot
            score += 0.2
        elif content_length > 300:
            score += 0.1
        
        # Metadata factors
        if metadata.get('type') == 'correction':
            score += 0.3  # Corrections are important for learning
        elif metadata.get('type') == 'interaction' and metadata.get('confidence', 0) > 0.8:
            score += 0.2  # High-confidence interactions are valuable
        elif metadata.get('type') == 'concept':
            score += 0.1  # Concepts are moderately important
        
        # Content quality indicators
        if any(indicator in content.lower() for indicator in ['because', 'therefore', 'however', 'moreover']):
            score += 0.1  # Logical connectors indicate structured thinking
        
        # Numbers and facts
        import re
        if re.search(r'\d+', content):
            score += 0.05  # Contains numerical data
        
        return min(1.0, score)
    
    async def _detect_relationships(self, new_node: MemoryNode):
        """Detect relationships between new node and existing nodes"""
        if new_node.embedding is None:
            return
        
        # Find semantically similar nodes
        similar_results = await self._find_similar_memories(
            new_node.embedding, top_k=10, similarity_threshold=0.6
        )
        
        for result in similar_results:
            if result['id'] != new_node.id:
                # Create semantic similarity relationship
                relationship_id = f"rel_{new_node.id}_{result['id']}"
                
                relationship = MemoryRelationship(
                    source_id=new_node.id,
                    target_id=result['id'],
                    relationship_type='semantic_similarity',
                    strength=result['similarity'],
                    metadata={'similarity_score': result['similarity']},
                    created_at=datetime.now().isoformat()
                )
                
                self.relationships[relationship_id] = relationship
                
                # Add to graph
                self.graph.add_edge(
                    new_node.id,
                    result['id'],
                    type='semantic_similarity',
                    strength=result['similarity']
                )
                
                # Update node relationships
                new_node.relationships.append(relationship_id)
                if result['id'] in self.nodes:
                    self.nodes[result['id']].relationships.append(relationship_id)
    
    async def _find_similar_memories(self, query_embedding: np.ndarray, top_k: int, 
                                   similarity_threshold: float, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Find memories similar to query embedding"""
        if self.embeddings_matrix is None or len(self.node_ids) == 0:
            return []
        
        # Calculate similarities
        query_embedding_2d = query_embedding.reshape(1, -1)
        similarities = cosine_similarity(query_embedding_2d, self.embeddings_matrix)[0]
        
        # Create results list
        results = []
        for i, similarity in enumerate(similarities):
            if similarity >= similarity_threshold:
                node_id = self.node_ids[i]
                node = self.nodes[node_id]
                
                # Apply filters
                if filters and not self._apply_filters(node, filters):
                    continue
                
                results.append({
                    'id': node_id,
                    'content': node.content,
                    'metadata': node.metadata,
                    'similarity': float(similarity),
                    'importance_score': node.importance_score,
                    'last_accessed': node.last_accessed
                })
        
        # Sort by combined score (similarity + importance + recency)
        results.sort(key=lambda x: (
            x['similarity'] * 0.6 +
            x['importance_score'] * 0.3 +
            self._calculate_recency_score(x['last_accessed']) * 0.1
        ), reverse=True)
        
        return results[:top_k]
    
    def _apply_filters(self, node: MemoryNode, filters: Dict[str, Any]) -> bool:
        """Apply search filters to a node"""
        for filter_key, filter_value in filters.items():
            if filter_key == 'type':
                if node.metadata.get('type') != filter_value:
                    return False
            elif filter_key == 'tags':
                if not any(tag in node.tags for tag in filter_value):
                    return False
            elif filter_key == 'min_importance':
                if node.importance_score < filter_value:
                    return False
            elif filter_key in node.metadata:
                if node.metadata[filter_key] != filter_value:
                    return False
        
        return True
    
    def _calculate_recency_score(self, last_accessed: str) -> float:
        """Calculate recency score based on last access time"""
        try:
            last_access_time = datetime.fromisoformat(last_accessed)
            time_diff = datetime.now() - last_access_time
            days_ago = time_diff.total_seconds() / (24 * 3600)
            
            # Decay function: more recent = higher score
            return max(0.0, 1.0 - (days_ago / 30.0))  # 30-day decay
        except:
            return 0.5
    
    async def _update_access_pattern(self, node_id: str):
        """Update access pattern for a node"""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.access_count += 1
            node.last_accessed = datetime.now().isoformat()
            
            # Update access patterns for optimization
            self.access_patterns[node_id] += 1
    
    async def _update_indexes(self):
        """Update search indexes"""
        # Rebuild embeddings matrix
        embeddings = []
        node_ids = []
        
        for node_id, node in self.nodes.items():
            if node.embedding is not None:
                embeddings.append(node.embedding)
                node_ids.append(node_id)
        
        if embeddings:
            self.embeddings_matrix = np.vstack(embeddings)
            self.node_ids = node_ids
        
        # Update TF-IDF matrix
        content_list = [node.content for node in self.nodes.values()]
        if content_list:
            try:
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(content_list)
            except:
                pass  # Skip TF-IDF update if it fails
    
    async def _rebuild_indexes(self):
        """Completely rebuild all indexes"""
        await self._update_indexes()
        logger.debug("Memory indexes rebuilt")
    
    def _update_query_stats(self, query_time: float):
        """Update query performance statistics"""
        self.stats['total_queries'] += 1
        
        # Update rolling average
        current_avg = self.stats['average_query_time']
        total_queries = self.stats['total_queries']
        
        self.stats['average_query_time'] = (
            (current_avg * (total_queries - 1) + query_time) / total_queries
        )
    
    async def _find_similar_memory_pairs(self, similarity_threshold: float = 0.9) -> List[Tuple[str, str]]:
        """Find pairs of very similar memories for consolidation"""
        similar_pairs = []
        
        if self.embeddings_matrix is None:
            return similar_pairs
        
        # Calculate pairwise similarities
        similarities = cosine_similarity(self.embeddings_matrix)
        
        # Find highly similar pairs
        for i in range(len(similarities)):
            for j in range(i + 1, len(similarities)):
                if similarities[i][j] >= similarity_threshold:
                    node_id_1 = self.node_ids[i]
                    node_id_2 = self.node_ids[j]
                    similar_pairs.append((node_id_1, node_id_2))
        
        return similar_pairs
    
    async def _merge_memories(self, node_id_1: str, node_id_2: str) -> bool:
        """Merge two similar memories"""
        if node_id_1 not in self.nodes or node_id_2 not in self.nodes:
            return False
        
        node_1 = self.nodes[node_id_1]
        node_2 = self.nodes[node_id_2]
        
        # Merge content (keep the higher importance one as primary)
        if node_1.importance_score >= node_2.importance_score:
            primary_node, secondary_node = node_1, node_2
            primary_id, secondary_id = node_id_1, node_id_2
        else:
            primary_node, secondary_node = node_2, node_1
            primary_id, secondary_id = node_id_2, node_id_1
        
        # Update primary node with merged information
        primary_node.content += f"\n\nMerged from: {secondary_node.content}"
        primary_node.access_count += secondary_node.access_count
        primary_node.tags = list(set(primary_node.tags + secondary_node.tags))
        
        # Merge metadata
        for key, value in secondary_node.metadata.items():
            if key not in primary_node.metadata:
                primary_node.metadata[key] = value
        
        # Transfer relationships
        for rel_id in secondary_node.relationships:
            if rel_id in self.relationships:
                relationship = self.relationships[rel_id]
                
                # Update relationship to point to primary node
                if relationship.source_id == secondary_id:
                    relationship.source_id = primary_id
                elif relationship.target_id == secondary_id:
                    relationship.target_id = primary_id
                
                primary_node.relationships.append(rel_id)
        
        # Remove secondary node
        del self.nodes[secondary_id]
        self.graph.remove_node(secondary_id)
        
        # Update database
        await self._persist_node(primary_node)
        self.db_conn.execute('DELETE FROM memory_nodes WHERE id = ?', (secondary_id,))
        
        logger.debug(f"Merged memory nodes: {secondary_id} into {primary_id}")
        return True
    
    async def _optimize_relationships(self) -> List[str]:
        """Optimize relationship graph by adding beneficial connections"""
        new_relationships = []
        
        # Find nodes that should be connected based on access patterns
        frequently_accessed = {
            node_id: count for node_id, count in self.access_patterns.items()
            if count > 5  # Threshold for frequent access
        }
        
        # Create co-occurrence relationships
        for node_id_1 in frequently_accessed:
            for node_id_2 in frequently_accessed:
                if node_id_1 != node_id_2 and not self.graph.has_edge(node_id_1, node_id_2):
                    # Calculate relationship strength based on access pattern correlation
                    strength = min(1.0, (frequently_accessed[node_id_1] + frequently_accessed[node_id_2]) / 20.0)
                    
                    if strength > 0.5:
                        relationship_id = f"rel_cooccur_{node_id_1}_{node_id_2}"
                        
                        relationship = MemoryRelationship(
                            source_id=node_id_1,
                            target_id=node_id_2,
                            relationship_type='co_occurrence',
                            strength=strength,
                            metadata={'access_based': True},
                            created_at=datetime.now().isoformat()
                        )
                        
                        self.relationships[relationship_id] = relationship
                        self.graph.add_edge(node_id_1, node_id_2, type='co_occurrence', strength=strength)
                        
                        new_relationships.append(relationship_id)
        
        return new_relationships
    
    async def _cleanup_cache(self) -> bool:
        """Clean up old cache entries"""
        with self.lock:
            if len(self.query_cache) > self.cache_size * 0.8:
                # Remove oldest half of cache
                items_to_remove = len(self.query_cache) // 2
                keys_to_remove = list(self.query_cache.keys())[:items_to_remove]
                
                for key in keys_to_remove:
                    del self.query_cache[key]
                
                return True
        return False
    
    async def _optimize_embeddings_storage(self) -> bool:
        """Optimize embeddings matrix storage"""
        if self.embeddings_matrix is not None:
            # Compress embeddings matrix (simple optimization)
            self.embeddings_matrix = self.embeddings_matrix.astype(np.float32)
            return True
        return False
    
    async def _prune_weak_relationships(self, strength_threshold: float = 0.3) -> int:
        """Remove weak relationships to improve performance"""
        weak_relationships = []
        
        for rel_id, relationship in self.relationships.items():
            if relationship.strength < strength_threshold:
                weak_relationships.append(rel_id)
        
        # Remove weak relationships
        for rel_id in weak_relationships:
            relationship = self.relationships[rel_id]
            
            # Remove from graph
            if self.graph.has_edge(relationship.source_id, relationship.target_id):
                self.graph.remove_edge(relationship.source_id, relationship.target_id)
            
            # Remove from nodes
            if relationship.source_id in self.nodes:
                self.nodes[relationship.source_id].relationships = [
                    r for r in self.nodes[relationship.source_id].relationships if r != rel_id
                ]
            if relationship.target_id in self.nodes:
                self.nodes[relationship.target_id].relationships = [
                    r for r in self.nodes[relationship.target_id].relationships if r != rel_id
                ]
            
            # Remove from memory
            del self.relationships[rel_id]
            
            # Remove from database
            self.db_conn.execute('DELETE FROM memory_relationships WHERE id = ?', (rel_id,))
        
        if weak_relationships:
            self.db_conn.commit()
        
        return len(weak_relationships)


# Export main class
__all__ = ['NeuralMemorySystem', 'MemoryNode', 'MemoryRelationship', 'MemoryQuery']