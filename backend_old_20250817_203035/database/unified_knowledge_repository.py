"""
Unified Knowledge Repository for SOPHIA Intel
Zero-fragmentation data access layer for all knowledge operations
"""

import os
import json
import uuid
import asyncio
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import asyncpg
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, DateTime, JSON, DECIMAL, Boolean, ARRAY
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from neo4j import GraphDatabase

@dataclass
class KnowledgeContext:
    """Unified context structure for all knowledge operations"""
    user_id: str
    session_id: str
    business_domain: str = "pay_ready"
    chat_flags: Dict[str, bool] = None
    ui_context: Dict[str, Any] = None
    preferred_sources: List[str] = None
    context_depth: str = "medium"
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.chat_flags is None:
            self.chat_flags = {}
        if self.ui_context is None:
            self.ui_context = {}
        if self.preferred_sources is None:
            self.preferred_sources = []
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class UnifiedKnowledgeRepository:
    """Unified data access layer for all knowledge operations"""
    
    def __init__(self):
        self.setup_connections()
        self.setup_cache()
        self.metadata = MetaData()
        self.setup_tables()
    
    def setup_connections(self):
        """Setup all database connections"""
        # PostgreSQL for structured data
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/sophia_intel")
        self.pg_engine = create_engine(database_url)
        self.pg_session = sessionmaker(bind=self.pg_engine)
        
        # Async PostgreSQL connection
        async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        self.async_pg_engine = create_async_engine(async_database_url)
        self.async_session = async_sessionmaker(self.async_pg_engine, class_=AsyncSession)
        
        # Qdrant for vector operations
        self.qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Neo4j for graph operations (optional)
        neo4j_uri = os.getenv("NEO4J_URI")
        if neo4j_uri:
            self.neo4j_driver = GraphDatabase.driver(
                neo4j_uri,
                auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
            )
        else:
            self.neo4j_driver = None
    
    def setup_cache(self):
        """Setup Redis cache for performance optimization"""
        try:
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=int(os.getenv("REDIS_DB", 0)),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.cache_enabled = True
        except (redis.ConnectionError, redis.TimeoutError):
            print("Warning: Redis connection failed. Caching disabled.")
            self.redis_client = None
            self.cache_enabled = False
    
    def setup_tables(self):
        """Setup database table definitions"""
        # Business entities table
        self.business_entities = Table(
            'business_entities', self.metadata,
            Column('id', String, primary_key=True),
            Column('entity_name', String(255), nullable=False),
            Column('entity_type', String(100), nullable=False),
            Column('description', String),
            Column('confidence_score', DECIMAL(3,2), default=0.7),
            Column('data_sources', ARRAY(String)),
            Column('embedding_id', String(255)),
            Column('llama_context', String),
            Column('haystack_doc_id', String(255)),
            Column('graph_node_id', String(255)),
            Column('ui_display_priority', Integer, default=5),
            Column('last_accessed', DateTime),
            Column('access_count', Integer, default=0),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.utcnow),
            Column('domain', String(100), default='pay_ready')
        )
        
        # Knowledge interactions table
        self.knowledge_interactions = Table(
            'knowledge_interactions', self.metadata,
            Column('id', String, primary_key=True),
            Column('session_id', String(255), nullable=False),
            Column('user_id', String(255)),
            Column('interaction_text', String, nullable=False),
            Column('extracted_entities', JSON),
            Column('rag_sources', JSON),
            Column('chat_flags', JSON),
            Column('ui_context', JSON),
            Column('response_quality_score', DECIMAL(3,2)),
            Column('user_feedback_score', Integer),
            Column('llama_model_used', String(100)),
            Column('haystack_pipeline_used', String(100)),
            Column('orchestrator_decisions', JSON),
            Column('micro_agent_contributions', JSON),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        # Context cache table
        self.context_cache = Table(
            'context_cache', self.metadata,
            Column('id', String, primary_key=True),
            Column('cache_key', String(255), unique=True, nullable=False),
            Column('context_data', JSON, nullable=False),
            Column('entity_ids', ARRAY(String)),
            Column('ttl_expires_at', DateTime, nullable=False),
            Column('access_count', Integer, default=0),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.utcnow)
        )
        
        # Background agent tasks table
        self.agent_tasks = Table(
            'agent_tasks', self.metadata,
            Column('id', String, primary_key=True),
            Column('agent_type', String(100), nullable=False),
            Column('task_type', String(100), nullable=False),
            Column('task_data', JSON, nullable=False),
            Column('status', String(50), default='pending'),
            Column('priority', Integer, default=5),
            Column('scheduled_at', DateTime, default=datetime.utcnow),
            Column('started_at', DateTime),
            Column('completed_at', DateTime),
            Column('error_message', String),
            Column('result_data', JSON),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        # Cross-platform correlations table
        self.cross_platform_correlations = Table(
            'cross_platform_correlations', self.metadata,
            Column('id', String, primary_key=True),
            Column('source_entity_id', String),
            Column('target_entity_id', String),
            Column('correlation_type', String(100)),
            Column('correlation_strength', DECIMAL(3,2)),
            Column('evidence_sources', ARRAY(String)),
            Column('rag_evidence_docs', JSON),
            Column('llama_analysis', String),
            Column('confidence_level', DECIMAL(3,2)),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.utcnow)
        )
    
    async def initialize_database(self):
        """Initialize database schema"""
        try:
            # Create tables if they don't exist
            self.metadata.create_all(self.pg_engine)
            
            # Initialize Qdrant collections
            await self.initialize_qdrant_collections()
            
            print("✅ Database schema initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize database: {e}")
            return False
    
    async def initialize_qdrant_collections(self):
        """Initialize Qdrant vector collections"""
        try:
            collections = [
                {
                    "name": "business_entities",
                    "size": 1536,  # OpenAI embedding size
                    "distance": Distance.COSINE
                },
                {
                    "name": "knowledge_interactions",
                    "size": 1536,
                    "distance": Distance.COSINE
                },
                {
                    "name": "cross_platform_data",
                    "size": 1536,
                    "distance": Distance.COSINE
                }
            ]
            
            for collection in collections:
                try:
                    self.qdrant_client.create_collection(
                        collection_name=collection["name"],
                        vectors_config=VectorParams(
                            size=collection["size"],
                            distance=collection["distance"]
                        )
                    )
                    print(f"✅ Created Qdrant collection: {collection['name']}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print(f"ℹ️  Qdrant collection already exists: {collection['name']}")
                    else:
                        print(f"⚠️  Failed to create collection {collection['name']}: {e}")
        
        except Exception as e:
            print(f"❌ Failed to initialize Qdrant collections: {e}")
    
    async def store_business_entity(
        self, 
        entity_data: Dict[str, Any],
        context: KnowledgeContext
    ) -> str:
        """Store business entity with full integration"""
        
        entity_id = str(uuid.uuid4())
        
        try:
            async with self.async_session() as session:
                query = text("""
                    INSERT INTO business_entities 
                    (id, entity_name, entity_type, description, confidence_score, 
                     data_sources, embedding_id, llama_context, haystack_doc_id, 
                     graph_node_id, ui_display_priority, domain)
                    VALUES 
                    (:id, :name, :type, :description, :confidence, 
                     :sources, :embedding_id, :llama_context, :haystack_doc_id,
                     :graph_node_id, :priority, :domain)
                """)
                
                await session.execute(query, {
                    "id": entity_id,
                    "name": entity_data["name"],
                    "type": entity_data["type"],
                    "description": entity_data.get("description", ""),
                    "confidence": entity_data.get("confidence", 0.7),
                    "sources": entity_data.get("data_sources", []),
                    "embedding_id": entity_data.get("embedding_id"),
                    "llama_context": entity_data.get("llama_context"),
                    "haystack_doc_id": entity_data.get("haystack_doc_id"),
                    "graph_node_id": entity_data.get("graph_node_id"),
                    "priority": entity_data.get("ui_display_priority", 5),
                    "domain": context.business_domain
                })
                
                await session.commit()
            
            # Store embedding in Qdrant if provided
            if entity_data.get("embedding"):
                await self.store_entity_embedding(entity_id, entity_data["embedding"], entity_data)
            
            # Store in Neo4j if graph operations enabled
            if self.neo4j_driver and entity_data.get("create_graph_node", True):
                await self.create_graph_node(entity_id, entity_data)
            
            # Invalidate related cache entries
            await self.invalidate_entity_cache(entity_data["name"], entity_data["type"])
            
            return entity_id
            
        except Exception as e:
            print(f"❌ Failed to store business entity: {e}")
            raise
    
    async def store_entity_embedding(
        self,
        entity_id: str,
        embedding: List[float],
        entity_data: Dict[str, Any]
    ):
        """Store entity embedding in Qdrant"""
        try:
            point = PointStruct(
                id=entity_id,
                vector=embedding,
                payload={
                    "entity_name": entity_data["name"],
                    "entity_type": entity_data["type"],
                    "description": entity_data.get("description", ""),
                    "confidence": entity_data.get("confidence", 0.7),
                    "data_sources": entity_data.get("data_sources", []),
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            self.qdrant_client.upsert(
                collection_name="business_entities",
                points=[point]
            )
            
        except Exception as e:
            print(f"❌ Failed to store entity embedding: {e}")
    
    async def get_contextual_knowledge(
        self,
        query: str,
        context: KnowledgeContext,
        max_results: int = 20
    ) -> Dict[str, Any]:
        """Get contextual knowledge with unified caching"""
        
        # Generate cache key
        cache_key = self.generate_cache_key(query, context, max_results)
        
        # Check cache first
        if self.cache_enabled:
            cached_result = await self.get_cached_context(cache_key)
            if cached_result:
                return cached_result
        
        # Gather knowledge from all sources
        knowledge_result = {
            "entities": await self.get_relevant_entities(query, context),
            "relationships": await self.get_relevant_relationships(query, context),
            "cross_platform_data": await self.get_cross_platform_correlations(query, context),
            "historical_interactions": await self.get_historical_context(query, context),
            "vector_context": await self.get_vector_context(query, context),
            "graph_context": await self.get_graph_context(query, context) if self.neo4j_driver else {}
        }
        
        # Cache the result
        if self.cache_enabled:
            await self.cache_context(cache_key, knowledge_result, context)
        
        return knowledge_result
    
    async def get_relevant_entities(
        self,
        query: str,
        context: KnowledgeContext,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get relevant business entities for the query"""
        try:
            async with self.async_session() as session:
                # Simple text search for now - can be enhanced with vector search
                search_query = text("""
                    SELECT id, entity_name, entity_type, description, confidence_score, 
                           data_sources, created_at
                    FROM business_entities 
                    WHERE domain = :domain 
                    AND (
                        LOWER(entity_name) LIKE LOWER(:query) 
                        OR LOWER(description) LIKE LOWER(:query)
                        OR LOWER(entity_type) LIKE LOWER(:query)
                    )
                    ORDER BY confidence_score DESC, access_count DESC
                    LIMIT :limit
                """)
                
                result = await session.execute(search_query, {
                    "domain": context.business_domain,
                    "query": f"%{query}%",
                    "limit": limit
                })
                
                entities = []
                for row in result:
                    entities.append({
                        "id": row.id,
                        "name": row.entity_name,
                        "type": row.entity_type,
                        "description": row.description,
                        "confidence": float(row.confidence_score) if row.confidence_score else 0.0,
                        "data_sources": row.data_sources or [],
                        "created_at": row.created_at.isoformat() if row.created_at else None
                    })
                
                return entities
                
        except Exception as e:
            print(f"❌ Failed to get relevant entities: {e}")
            return []
    
    def generate_cache_key(
        self,
        query: str,
        context: KnowledgeContext,
        max_results: int
    ) -> str:
        """Generate cache key for context queries"""
        key_data = {
            "query": query.lower().strip(),
            "domain": context.business_domain,
            "flags": sorted(context.chat_flags.items()),
            "sources": sorted(context.preferred_sources),
            "depth": context.context_depth,
            "max_results": max_results
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return f"context:{hash(key_string)}"
    
    async def get_cached_context(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached context if available and not expired"""
        if not self.cache_enabled:
            return None
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                context_data = json.loads(cached_data)
                
                # Check if cache is still valid
                expires_at = datetime.fromisoformat(context_data.get("expires_at", ""))
                if datetime.utcnow() < expires_at:
                    # Update access count
                    self.redis_client.incr(f"{cache_key}:access_count")
                    return context_data.get("data")
                else:
                    # Cache expired, delete it
                    self.redis_client.delete(cache_key)
            
            return None
            
        except Exception as e:
            print(f"⚠️  Cache retrieval error: {e}")
            return None
    
    async def cache_context(
        self,
        cache_key: str,
        context_data: Dict[str, Any],
        context: KnowledgeContext,
        ttl_minutes: int = 60
    ):
        """Cache context data with TTL"""
        if not self.cache_enabled:
            return
        
        try:
            expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
            
            cache_payload = {
                "data": context_data,
                "expires_at": expires_at.isoformat(),
                "cached_at": datetime.utcnow().isoformat(),
                "context_summary": {
                    "user_id": context.user_id,
                    "domain": context.business_domain,
                    "flags": context.chat_flags
                }
            }
            
            self.redis_client.setex(
                cache_key,
                ttl_minutes * 60,
                json.dumps(cache_payload)
            )
            
        except Exception as e:
            print(f"⚠️  Cache storage error: {e}")
    
    async def invalidate_entity_cache(self, entity_name: str, entity_type: str):
        """Invalidate cache entries related to an entity"""
        if not self.cache_enabled:
            return
        
        try:
            # Find and delete related cache entries
            pattern = f"context:*"
            for key in self.redis_client.scan_iter(match=pattern):
                # This is a simple approach - in production, you might want more sophisticated cache invalidation
                self.redis_client.delete(key)
                
        except Exception as e:
            print(f"⚠️  Cache invalidation error: {e}")
    
    # Placeholder methods for additional functionality
    async def get_relevant_relationships(self, query: str, context: KnowledgeContext) -> List[Dict[str, Any]]:
        """Get relevant relationships - to be implemented"""
        return []
    
    async def get_cross_platform_correlations(self, query: str, context: KnowledgeContext) -> List[Dict[str, Any]]:
        """Get cross-platform correlations - to be implemented"""
        return []
    
    async def get_historical_context(self, query: str, context: KnowledgeContext) -> List[Dict[str, Any]]:
        """Get historical context - to be implemented"""
        return []
    
    async def get_vector_context(self, query: str, context: KnowledgeContext) -> Dict[str, Any]:
        """Get vector context from Qdrant - to be implemented"""
        return {}
    
    async def get_graph_context(self, query: str, context: KnowledgeContext) -> Dict[str, Any]:
        """Get graph context from Neo4j - to be implemented"""
        return {}
    
    async def create_graph_node(self, entity_id: str, entity_data: Dict[str, Any]):
        """Create graph node in Neo4j - to be implemented"""
        pass
    
    async def close_connections(self):
        """Close all database connections"""
        try:
            if hasattr(self, 'async_pg_engine'):
                await self.async_pg_engine.dispose()
            
            if self.neo4j_driver:
                self.neo4j_driver.close()
            
            if self.redis_client:
                self.redis_client.close()
                
            print("✅ Database connections closed")
            
        except Exception as e:
            print(f"⚠️  Error closing connections: {e}")

# Global repository instance
_repository_instance = None

def get_knowledge_repository() -> UnifiedKnowledgeRepository:
    """Get global knowledge repository instance"""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = UnifiedKnowledgeRepository()
    return _repository_instance

async def initialize_knowledge_system():
    """Initialize the knowledge system"""
    repository = get_knowledge_repository()
    success = await repository.initialize_database()
    return success

