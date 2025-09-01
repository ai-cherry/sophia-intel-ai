"""
Weaviate v1.32+ Vector Store Implementation for Sophia Intel AI
Replaces Qdrant with Weaviate for 75% memory reduction and improved performance
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import weaviate
from weaviate.classes.config import Configure, Property, DataType, VectorDistances
from weaviate.classes.query import MetadataQuery, Filter
from weaviate.classes.tenants import Tenant
from dotenv import load_dotenv
import logging
from uuid import uuid4

# Load environment variables
load_dotenv('.env.local')

logger = logging.getLogger(__name__)

class WeaviateStore:
    """
    Weaviate vector store implementation with multi-tenancy support.
    Provides 75% memory reduction with RQ compression and hybrid search capabilities.
    """
    
    def __init__(self, tenant_name: str = "strategic_swarm"):
        """
        Initialize Weaviate store for a specific agent swarm.
        
        Args:
            tenant_name: One of 'strategic_swarm', 'development_swarm', 
                        'security_swarm', or 'research_swarm'
        """
        self.tenant_name = tenant_name
        self.client = None
        self.collections = {}
        self._connect()
        
    def _connect(self):
        """Connect to Weaviate instance."""
        try:
            self.client = weaviate.connect_to_local(
                host="localhost",
                port=8080,
                grpc_port=50051,
                headers={
                    "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")
                }
            )
            logger.info(f"✅ Connected to Weaviate for tenant: {self.tenant_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Weaviate: {e}")
            raise
    
    def get_collection(self, collection_name: str):
        """Get a collection with tenant context."""
        if collection_name not in self.collections:
            collection = self.client.collections.get(collection_name)
            # Set tenant context for multi-tenancy
            self.collections[collection_name] = collection.with_tenant(self.tenant_name)
        return self.collections[collection_name]
    
    async def store_memory(self, agent_id: str, session_id: str, message: str, 
                          role: str = "user", metadata: Optional[Dict] = None) -> str:
        """
        Store agent memory in Weaviate.
        
        Args:
            agent_id: Unique identifier for the agent
            session_id: Current session identifier
            message: The message content
            role: Role (user/assistant/system)
            metadata: Additional metadata
            
        Returns:
            UUID of the stored memory
        """
        try:
            collection = self.get_collection("AgentMemory")
            
            memory_id = str(uuid4())
            data = {
                "agent_id": agent_id,
                "session_id": session_id,
                "message": message,
                "role": role,
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),  # RFC3339 format
                "metadata": json.dumps(metadata or {})
            }
            
            # Store with automatic vectorization
            collection.data.insert(
                properties=data,
                uuid=memory_id
            )
            
            logger.info(f"✅ Stored memory for agent {agent_id}: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store memory: {e}")
            raise
    
    async def search_memories(self, query: str, agent_id: Optional[str] = None, 
                             limit: int = 10) -> List[Dict]:
        """
        Search agent memories using hybrid search (BM25 + vector).
        
        Args:
            query: Search query
            agent_id: Filter by specific agent
            limit: Maximum results to return
            
        Returns:
            List of relevant memories
        """
        try:
            collection = self.get_collection("AgentMemory")
            
            # Build filter if agent_id provided
            where_filter = None
            if agent_id:
                where_filter = Filter.by_property("agent_id").equal(agent_id)
            
            # Perform hybrid search (combines BM25 and vector search)
            query_builder = collection.query.hybrid(
                query=query,
                limit=limit,
                return_metadata=MetadataQuery(
                    distance=True,
                    certainty=True,
                    score=True
                )
            )
            
            # Apply filter if provided
            if where_filter:
                query_builder = query_builder.where(where_filter)
                
            results = query_builder  # The query builder returns results directly
            
            memories = []
            for obj in results.objects:
                memory = {
                    "id": str(obj.uuid),
                    "agent_id": obj.properties.get("agent_id"),
                    "message": obj.properties.get("message"),
                    "role": obj.properties.get("role"),
                    "timestamp": obj.properties.get("timestamp"),
                    "metadata": json.loads(obj.properties.get("metadata", "{}")),
                    "score": obj.metadata.score if hasattr(obj.metadata, 'score') else None
                }
                memories.append(memory)
            
            logger.info(f"✅ Found {len(memories)} memories for query: {query[:50]}...")
            return memories
            
        except Exception as e:
            logger.error(f"❌ Failed to search memories: {e}")
            return []
    
    async def store_document(self, collection_name: str, document: Dict) -> str:
        """
        Store a document in any collection.
        
        Args:
            collection_name: Name of the collection
            document: Document data to store
            
        Returns:
            UUID of the stored document
        """
        try:
            collection = self.get_collection(collection_name)
            
            doc_id = str(uuid4())
            
            # Convert any dict/object fields to JSON strings
            # But keep arrays as arrays for text[] fields
            processed_doc = {}
            for key, value in document.items():
                if isinstance(value, dict):
                    processed_doc[key] = json.dumps(value)
                elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    processed_doc[key] = json.dumps(value)
                else:
                    processed_doc[key] = value
            
            # Store with automatic vectorization
            collection.data.insert(
                properties=processed_doc,
                uuid=doc_id
            )
            
            logger.info(f"✅ Stored document in {collection_name}: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store document: {e}")
            raise
    
    async def search_documents(self, collection_name: str, query: str, 
                              filters: Optional[Dict] = None, limit: int = 10) -> List[Dict]:
        """
        Search documents in any collection using hybrid search.
        
        Args:
            collection_name: Name of the collection
            query: Search query
            filters: Optional filters to apply
            limit: Maximum results to return
            
        Returns:
            List of relevant documents
        """
        try:
            collection = self.get_collection(collection_name)
            
            # Build filters if provided
            where_filter = None
            if filters:
                # Simple example - extend as needed
                for prop, value in filters.items():
                    where_filter = Filter.by_property(prop).equal(value)
                    break  # Simple single filter for now
            
            # Perform hybrid search
            query_builder = collection.query.hybrid(
                query=query,
                limit=limit,
                return_metadata=MetadataQuery(
                    distance=True,
                    certainty=True,
                    score=True
                )
            )
            
            # Apply filter if provided
            if where_filter:
                query_builder = query_builder.where(where_filter)
                
            results = query_builder  # The query builder returns results directly
            
            documents = []
            for obj in results.objects:
                doc = {
                    "id": str(obj.uuid),
                    **obj.properties,
                    "_score": obj.metadata.score if hasattr(obj.metadata, 'score') else None
                }
                documents.append(doc)
            
            logger.info(f"✅ Found {len(documents)} documents in {collection_name}")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Failed to search documents: {e}")
            return []
    
    async def store_code(self, filename: str, content: str, language: str, 
                        project: str, dependencies: List[str] = None) -> str:
        """
        Store code in the CodeRepository collection.
        
        Args:
            filename: Name of the file
            content: Code content
            language: Programming language
            project: Project name
            dependencies: List of dependencies
            
        Returns:
            UUID of the stored code
        """
        document = {
            "filename": filename,
            "content": content,
            "language": language,
            "project": project,
            "last_modified": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),  # RFC3339 format
            "dependencies": dependencies or []
        }
        
        return await self.store_document("CodeRepository", document)
    
    async def search_code(self, query: str, language: Optional[str] = None, 
                         project: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Search code in the CodeRepository.
        
        Args:
            query: Search query
            language: Filter by language
            project: Filter by project
            limit: Maximum results
            
        Returns:
            List of relevant code files
        """
        filters = {}
        if language:
            filters["language"] = language
        if project:
            filters["project"] = project
            
        return await self.search_documents("CodeRepository", query, filters, limit)
    
    async def store_research(self, title: str, content: str, source: str, 
                           authors: List[str], tags: List[str] = None) -> str:
        """
        Store research document in ResearchDocuments collection.
        
        Args:
            title: Document title
            content: Document content
            source: Source URL or reference
            authors: List of authors
            tags: Optional tags
            
        Returns:
            UUID of the stored document
        """
        document = {
            "title": title,
            "content": content,
            "source": source,
            "authors": authors,
            "published_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),  # RFC3339 format
            "tags": tags or []
        }
        
        return await self.store_document("ResearchDocuments", document)
    
    async def search_research(self, query: str, tags: Optional[List[str]] = None, 
                            limit: int = 10) -> List[Dict]:
        """
        Search research documents.
        
        Args:
            query: Search query
            tags: Filter by tags
            limit: Maximum results
            
        Returns:
            List of relevant research documents
        """
        # For tag filtering, we'd need more complex filter logic
        # This is a simplified version
        return await self.search_documents("ResearchDocuments", query, None, limit)
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about stored data.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            stats = {}
            collections = self.client.collections.list_all()
            
            for collection_name in collections:
                collection = self.get_collection(collection_name)
                # Get count for this tenant
                aggregate = collection.aggregate.over_all()
                stats[collection_name] = {
                    "count": aggregate.total_count if hasattr(aggregate, 'total_count') else 0,
                    "tenant": self.tenant_name
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return {}
    
    def close(self):
        """Close Weaviate connection."""
        if self.client:
            self.client.close()
            logger.info("👋 Closed Weaviate connection")


# Singleton instances for each swarm
_stores = {}

def get_weaviate_store(tenant_name: str = "strategic_swarm") -> WeaviateStore:
    """
    Get or create a Weaviate store instance for a specific tenant.
    
    Args:
        tenant_name: Tenant/swarm name
        
    Returns:
        WeaviateStore instance
    """
    if tenant_name not in _stores:
        _stores[tenant_name] = WeaviateStore(tenant_name)
    return _stores[tenant_name]


# Example usage
async def example_usage():
    """Example of using the Weaviate store."""
    
    # Get store for strategic swarm
    store = get_weaviate_store("strategic_swarm")
    
    # Store a memory
    memory_id = await store.store_memory(
        agent_id="strategic_agent_1",
        session_id="session_123",
        message="The Q3 roadmap focuses on scaling infrastructure",
        role="assistant",
        metadata={"topic": "planning", "priority": "high"}
    )
    print(f"Stored memory: {memory_id}")
    
    # Search memories
    memories = await store.search_memories(
        query="infrastructure scaling",
        agent_id="strategic_agent_1"
    )
    print(f"Found {len(memories)} relevant memories")
    
    # Store code
    code_id = await store.store_code(
        filename="weaviate_store.py",
        content="# Weaviate integration code...",
        language="python",
        project="sophia-intel-ai",
        dependencies=["weaviate-client", "pydantic"]
    )
    print(f"Stored code: {code_id}")
    
    # Search code
    code_results = await store.search_code(
        query="vector store implementation",
        language="python"
    )
    print(f"Found {len(code_results)} code files")
    
    # Get statistics
    stats = store.get_statistics()
    print(f"Statistics: {stats}")
    
    # Clean up
    store.close()


if __name__ == "__main__":
    asyncio.run(example_usage())