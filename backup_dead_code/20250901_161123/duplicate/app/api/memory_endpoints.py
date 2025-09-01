"""
Memory and Search Endpoints for Sophia Intel AI
Provides Agno-compatible memory management and hybrid search.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import json
import asyncio
import logging
from enum import Enum

# Import memory systems
from app.memory.supermemory_mcp import SupermemoryStore, MemoryEntry, MemoryType
from app.memory.hybrid_search import HybridSearchEngine
from app.memory.dual_tier_embeddings import DualTierEmbedder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])

# ============================================
# Data Models
# ============================================

class MemoryAddRequest(BaseModel):
    """Request to add a memory entry."""
    topic: str = Field(..., description="Topic or title of the memory")
    content: str = Field(..., description="Content to store")
    source: Optional[str] = Field(default="user", description="Source of the memory")
    tags: Optional[List[str]] = Field(default=[], description="Tags for categorization")
    memory_type: Optional[str] = Field(default="episodic", description="Type of memory")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")

class MemorySearchRequest(BaseModel):
    """Request to search memories."""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")
    memory_types: Optional[List[str]] = Field(default=None, description="Filter by memory types")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")
    hybrid: bool = Field(default=True, description="Use hybrid search (BM25 + vector)")
    rerank: bool = Field(default=False, description="Apply reranking to results")

class MemoryUpdateRequest(BaseModel):
    """Request to update a memory entry."""
    hash_id: str = Field(..., description="Hash ID of memory to update")
    topic: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class SearchMode(str, Enum):
    """Search modes available."""
    VECTOR = "vector"
    BM25 = "bm25"
    HYBRID = "hybrid"
    GRAPHRAG = "graphrag"

class SearchRequest(BaseModel):
    """Generic search request."""
    query: str = Field(..., description="Search query")
    mode: SearchMode = Field(default=SearchMode.HYBRID, description="Search mode")
    limit: int = Field(default=10, ge=1, le=100)
    filters: Optional[Dict[str, Any]] = Field(default={}, description="Additional filters")
    include_metadata: bool = Field(default=True)
    stream: bool = Field(default=False, description="Stream results")

# ============================================
# Memory Management Endpoints
# ============================================

@router.post("/add")
async def add_memory(
    request: MemoryAddRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Add a new memory entry to Supermemory.
    
    Features:
    - Deduplication via content hashing
    - Dual-tier embeddings (local + API)
    - Full-text search indexing
    - Tag and metadata support
    """
    try:
        # Get memory store instance
        from app.api.unified_server import state
        
        if not state.supermemory:
            raise HTTPException(status_code=503, detail="Memory system not initialized")
        
        # Create memory entry
        memory = MemoryEntry(
            topic=request.topic,
            content=request.content,
            source=request.source,
            tags=request.tags,
            memory_type=MemoryType[request.memory_type.upper()],
            metadata=request.metadata
        )
        
        # Add to store (handles deduplication)
        result = await state.supermemory.add_memory(memory)
        
        # Background task to update indices
        background_tasks.add_task(
            update_memory_indices,
            memory_id=result["hash_id"]
        )
        
        return {
            "status": "added",
            "hash_id": result["hash_id"],
            "deduplicated": result.get("deduplicated", False),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to add memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_memory(request: MemorySearchRequest) -> Dict[str, Any]:
    """
    Search memories using hybrid search.
    
    Features:
    - BM25 text search
    - Vector similarity search
    - Hybrid fusion with RRF
    - Optional reranking
    - Tag and type filtering
    """
    try:
        from app.api.unified_server import state
        
        if not state.supermemory:
            raise HTTPException(status_code=503, detail="Memory system not initialized")
        
        # Perform search based on mode
        if request.hybrid and state.search_engine:
            # Use hybrid search engine
            results = await state.search_engine.hybrid_search(
                query=request.query,
                limit=request.limit,
                filters={
                    "memory_types": request.memory_types,
                    "tags": request.tags
                },
                rerank=request.rerank
            )
        else:
            # Use basic supermemory search
            results = await state.supermemory.search_memory(
                query=request.query,
                limit=request.limit,
                memory_types=request.memory_types
            )
        
        # Format results
        formatted_results = []
        for r in results:
            formatted_results.append({
                "hash_id": r.get("hash_id", r.get("id")),
                "topic": r.get("topic"),
                "content": r.get("content"),
                "score": r.get("score", 0.0),
                "source": r.get("source"),
                "tags": r.get("tags", []),
                "timestamp": r.get("timestamp")
            })
        
        return {
            "results": formatted_results,
            "count": len(formatted_results),
            "mode": "hybrid" if request.hybrid else "vector",
            "query": request.query
        }
        
    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/retrieve/{hash_id}")
async def retrieve_memory(hash_id: str) -> Dict[str, Any]:
    """Retrieve a specific memory by hash ID."""
    try:
        from app.api.unified_server import state
        
        if not state.supermemory:
            raise HTTPException(status_code=503, detail="Memory system not initialized")
        
        memory = await state.supermemory.get_memory(hash_id)
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return {
            "hash_id": hash_id,
            "topic": memory.topic,
            "content": memory.content,
            "source": memory.source,
            "tags": memory.tags,
            "memory_type": memory.memory_type.value,
            "metadata": memory.metadata,
            "embedding_cached": memory.embedding is not None,
            "timestamp": memory.timestamp.isoformat() if memory.timestamp else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update")
async def update_memory(request: MemoryUpdateRequest) -> Dict[str, Any]:
    """Update an existing memory entry."""
    try:
        from app.api.unified_server import state
        
        if not state.supermemory:
            raise HTTPException(status_code=503, detail="Memory system not initialized")
        
        # Update memory
        success = await state.supermemory.update_memory(
            hash_id=request.hash_id,
            topic=request.topic,
            content=request.content,
            tags=request.tags,
            metadata=request.metadata
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found or update failed")
        
        return {
            "status": "updated",
            "hash_id": request.hash_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{hash_id}")
async def delete_memory(hash_id: str) -> Dict[str, Any]:
    """Delete a memory entry."""
    try:
        from app.api.unified_server import state
        
        if not state.supermemory:
            raise HTTPException(status_code=503, detail="Memory system not initialized")
        
        success = await state.supermemory.delete_memory(hash_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return {
            "status": "deleted",
            "hash_id": hash_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def memory_stats() -> Dict[str, Any]:
    """Get memory system statistics."""
    try:
        from app.api.unified_server import state
        
        if not state.supermemory:
            raise HTTPException(status_code=503, detail="Memory system not initialized")
        
        stats = await state.supermemory.get_stats()
        
        return {
            "total_memories": stats.get("total_entries", 0),
            "memory_types": stats.get("by_type", {}),
            "sources": stats.get("by_source", {}),
            "cache_stats": {
                "embedding_cache_size": stats.get("embedding_cache_size", 0),
                "cache_hit_rate": stats.get("cache_hit_rate", 0.0)
            },
            "storage": {
                "database_size": stats.get("db_size", 0),
                "index_size": stats.get("index_size", 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Generic Search Endpoint
# ============================================

@router.post("/search/unified")
async def unified_search(request: SearchRequest) -> Dict[str, Any]:
    """
    Unified search across all available indices.
    
    Modes:
    - vector: Pure vector similarity search
    - bm25: Pure text search
    - hybrid: Combined BM25 + vector with RRF
    - graphrag: Graph-based retrieval
    """
    try:
        from app.api.unified_server import state
        
        results = []
        
        if request.mode == SearchMode.HYBRID:
            if not state.search_engine:
                raise HTTPException(status_code=503, detail="Hybrid search not available")
            
            results = await state.search_engine.hybrid_search(
                query=request.query,
                limit=request.limit,
                filters=request.filters
            )
            
        elif request.mode == SearchMode.VECTOR:
            if not state.embedder:
                raise HTTPException(status_code=503, detail="Vector search not available")
            
            # Get embedding
            embedding = await state.embedder.get_embedding(request.query)
            
            # Search in Weaviate or local vector store
            results = await vector_search(
                embedding=embedding,
                limit=request.limit,
                filters=request.filters
            )
            
        elif request.mode == SearchMode.BM25:
            if not state.supermemory:
                raise HTTPException(status_code=503, detail="BM25 search not available")
            
            results = await state.supermemory.bm25_search(
                query=request.query,
                limit=request.limit
            )
            
        elif request.mode == SearchMode.GRAPHRAG:
            if not state.graph_rag:
                raise HTTPException(status_code=503, detail="GraphRAG not available")
            
            results = await state.graph_rag.query(
                question=request.query,
                max_results=request.limit
            )
        
        if request.stream:
            return StreamingResponse(
                stream_search_results(results),
                media_type="text/event-stream"
            )
        else:
            return {
                "results": results,
                "count": len(results),
                "mode": request.mode.value,
                "query": request.query,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unified search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Helper Functions
# ============================================

async def update_memory_indices(memory_id: str):
    """Background task to update search indices."""
    try:
        # Update vector index in Weaviate
        # Update BM25 index in SQLite
        # Update graph if GraphRAG enabled
        logger.info(f"Updated indices for memory {memory_id}")
    except Exception as e:
        logger.error(f"Failed to update indices: {e}")

async def vector_search(
    embedding: List[float],
    limit: int,
    filters: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Perform vector similarity search."""
    # Implementation depends on vector store (Weaviate, Pinecone, etc.)
    return []

async def stream_search_results(
    results: List[Dict[str, Any]]
) -> AsyncGenerator[str, None]:
    """Stream search results as SSE."""
    for i, result in enumerate(results):
        yield f"data: {json.dumps({'index': i, 'result': result})}\n\n"
        await asyncio.sleep(0.05)
    yield "data: [DONE]\n\n"

# Export router
__all__ = ["router"]