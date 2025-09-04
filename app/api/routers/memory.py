"""
Memory API Router - Provides memory operations across vector stores
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Optional, Union

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# DEPRECATED: LangChain imports replaced by AGNO
# from app.infrastructure.langgraph.knowledge_nodes import Document
# from app.infrastructure.langgraph.rag_pipeline import KnowledgeNodeType, LangGraphRAGPipeline
# TODO: Replace with AGNO-based memory infrastructure

# Import memory systems
# from app.memory.enhanced_memory_integration import EnhancedMemoryIntegration  # Module not yet implemented
from app.memory.memory_integration import MemoryIntegration

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])

class MemorySearchRequest(BaseModel):
    """Request model for memory search"""
    query: str = Field(..., description="Search query")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results")
    filters: Optional[dict[str, Any]] = Field(default=None, description="Filter criteria")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Similarity threshold")
    knowledge_types: Optional[list[str]] = Field(default=None, description="Knowledge node types to search")
    use_rag: bool = Field(default=True, description="Use RAG pipeline for enhanced search")

class MemoryWriteRequest(BaseModel):
    """Request model for writing to memory"""
    content: str = Field(..., description="Content to store")
    metadata: dict[str, Any] = Field(default={}, description="Associated metadata")
    category: str = Field(default="general", description="Memory category")
    tags: list[str] = Field(default=[], description="Tags for organization")
    ttl: Optional[int] = Field(default=None, description="Time-to-live in seconds")

class MemoryEntry(BaseModel):
    """Model for a memory entry"""
    id: str
    content: str
    metadata: dict[str, Any]
    category: str
    tags: list[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    similarity_score: Optional[float] = None

class MemoryManager:
    """Manages memory operations with RAG integration"""

    def __init__(self):
        # self.enhanced_memory = EnhancedMemoryIntegration()  # Module not yet implemented
        self.enhanced_memory = None
        self.basic_memory = MemoryIntegration()
        self.rag_pipeline = LangGraphRAGPipeline()
        self.entries: dict[str, MemoryEntry] = {}
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure RAG pipeline is initialized"""
        if not self._initialized:
            await self.rag_pipeline.initialize()
            self._initialized = True

    async def search(self, request: MemorySearchRequest) -> list[MemoryEntry]:
        """Search memory for relevant entries with RAG integration"""
        try:
            await self._ensure_initialized()
            entries = []

            # Use RAG pipeline if enabled
            if request.use_rag:
                try:
                    # Search through knowledge nodes
                    knowledge_types = request.knowledge_types or ["memory", "codebase", "logs"]
                    for kt in knowledge_types:
                        if hasattr(KnowledgeNodeType, kt.upper()):
                            node_type = getattr(KnowledgeNodeType, kt.upper())
                            docs = await self.rag_pipeline.retrieve(
                                query=request.query,
                                node_type=node_type,
                                k=request.top_k // len(knowledge_types)
                            )

                            for doc in docs:
                                if doc.metadata.get("similarity_score", 0.0) >= request.similarity_threshold:
                                    entry = MemoryEntry(
                                        id=doc.metadata.get("id", str(uuid.uuid4())),
                                        content=doc.page_content,
                                        metadata=doc.metadata,
                                        category=doc.metadata.get("category", kt),
                                        tags=doc.metadata.get("tags", [kt]),
                                        created_at=datetime.fromisoformat(
                                            doc.metadata.get("created_at", datetime.utcnow().isoformat())
                                        ),
                                        similarity_score=doc.metadata.get("similarity_score")
                                    )
                                    entries.append(entry)
                except Exception as rag_error:
                    logger.warning(f"RAG search failed, falling back to enhanced memory: {rag_error}")

            # Fallback or supplement with enhanced memory search
            try:
                results = await self.enhanced_memory.semantic_search(
                    query=request.query,
                    top_k=request.top_k,
                    filters=request.filters,
                    threshold=request.similarity_threshold
                )

                for result in results:
                    entry = MemoryEntry(
                        id=result.get("id", str(uuid.uuid4())),
                        content=result.get("content", ""),
                        metadata=result.get("metadata", {}),
                        category=result.get("category", "general"),
                        tags=result.get("tags", []),
                        created_at=datetime.fromisoformat(
                            result.get("created_at", datetime.utcnow().isoformat())
                        ),
                        similarity_score=result.get("score", 0.0)
                    )
                    entries.append(entry)
            except Exception as memory_error:
                logger.error(f"Enhanced memory search failed: {memory_error}")
                if not entries:  # Only raise if we have no results from RAG
                    raise

            # Sort by similarity score and deduplicate
            entries = sorted(entries, key=lambda x: x.similarity_score or 0.0, reverse=True)
            seen_ids = set()
            unique_entries = []
            for entry in entries:
                if entry.id not in seen_ids:
                    seen_ids.add(entry.id)
                    unique_entries.append(entry)

            return unique_entries[:request.top_k]

        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            raise

    async def write(self, request: MemoryWriteRequest) -> MemoryEntry:
        """Write a new entry to memory with RAG integration"""
        try:
            await self._ensure_initialized()
            memory_id = str(uuid.uuid4())

            # Create memory entry
            entry = MemoryEntry(
                id=memory_id,
                content=request.content,
                metadata=request.metadata,
                category=request.category,
                tags=request.tags,
                created_at=datetime.utcnow()
            )

            # Store in enhanced memory
            await self.enhanced_memory.store(
                content=request.content,
                metadata={
                    **request.metadata,
                    "category": request.category,
                    "tags": request.tags,
                    "ttl": request.ttl,
                    "id": memory_id,
                    "created_at": entry.created_at.isoformat()
                },
                memory_id=memory_id
            )

            # Store in RAG pipeline for enhanced retrieval
            try:
                document = Document(
                    page_content=request.content,
                    metadata={
                        "id": memory_id,
                        "category": request.category,
                        "tags": request.tags,
                        "created_at": entry.created_at.isoformat(),
                        **request.metadata
                    }
                )
                await self.rag_pipeline.add_documents([document], KnowledgeNodeType.MEMORY)
            except Exception as rag_error:
                logger.warning(f"Failed to add to RAG pipeline: {rag_error}")

            # Store locally for quick access
            self.entries[memory_id] = entry

            return entry

        except Exception as e:
            logger.error(f"Memory write failed: {e}")
            raise

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory entry"""
        try:
            # Delete from enhanced memory
            await self.enhanced_memory.delete(memory_id)

            # Delete from local storage
            if memory_id in self.entries:
                del self.entries[memory_id]

            return True

        except Exception as e:
            logger.error(f"Memory deletion failed: {e}")
            raise

    async def get(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get a specific memory entry"""
        # Check local storage first
        if memory_id in self.entries:
            return self.entries[memory_id]

        # Try to fetch from enhanced memory
        try:
            result = await self.enhanced_memory.get(memory_id)
            if result:
                entry = MemoryEntry(
                    id=memory_id,
                    content=result.get("content", ""),
                    metadata=result.get("metadata", {}),
                    category=result.get("category", "general"),
                    tags=result.get("tags", []),
                    created_at=datetime.fromisoformat(result.get("created_at", datetime.utcnow().isoformat()))
                )
                self.entries[memory_id] = entry
                return entry

        except Exception as e:
            logger.error(f"Failed to get memory entry: {e}")

        return None

# Global manager instance
memory_manager = MemoryManager()

@router.post("/search", response_model=list[MemoryEntry])
async def search_memory(request: MemorySearchRequest):
    """
    Search memory for relevant entries
    
    Args:
        request: Search parameters
        
    Returns:
        List of matching memory entries
    """
    try:
        results = await memory_manager.search(request)
        return results

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Memory search failed: {str(e)}"
        )

@router.post("/write", response_model=MemoryEntry)
async def write_memory(request: MemoryWriteRequest):
    """
    Write a new entry to memory
    
    Args:
        request: Memory content and metadata
        
    Returns:
        Created memory entry
    """
    try:
        entry = await memory_manager.write(request)
        return entry

    except Exception as e:
        logger.error(f"Write failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Memory write failed: {str(e)}"
        )

@router.delete("/delete/{memory_id}")
async def delete_memory(memory_id: str):
    """
    Delete a memory entry
    
    Args:
        memory_id: ID of memory to delete
        
    Returns:
        Success status
    """
    try:
        success = await memory_manager.delete(memory_id)
        if success:
            return {"status": "success", "message": f"Memory {memory_id} deleted"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Memory entry {memory_id} not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deletion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Memory deletion failed: {str(e)}"
        )

@router.get("/{memory_id}", response_model=MemoryEntry)
async def get_memory(memory_id: str):
    """
    Get a specific memory entry
    
    Args:
        memory_id: ID of memory to retrieve
        
    Returns:
        Memory entry
    """
    try:
        entry = await memory_manager.get(memory_id)
        if entry:
            return entry
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Memory entry {memory_id} not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve memory: {str(e)}"
        )

@router.get("/categories/list")
async def list_categories():
    """
    List all memory categories
    
    Returns:
        List of categories with counts
    """
    try:
        categories = {}
        for entry in memory_manager.entries.values():
            cat = entry.category
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1

        return {
            "categories": [
                {"name": cat, "count": count}
                for cat, count in categories.items()
            ],
            "total": sum(categories.values())
        }

    except Exception as e:
        logger.error(f"Failed to list categories: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list categories: {str(e)}"
        )

@router.get("/tags/list")
async def list_tags():
    """
    List all memory tags
    
    Returns:
        List of tags with usage counts
    """
    try:
        tags = {}
        for entry in memory_manager.entries.values():
            for tag in entry.tags:
                if tag not in tags:
                    tags[tag] = 0
                tags[tag] += 1

        return {
            "tags": [
                {"name": tag, "count": count}
                for tag, count in sorted(tags.items(), key=lambda x: x[1], reverse=True)
            ],
            "total": len(tags)
        }

    except Exception as e:
        logger.error(f"Failed to list tags: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list tags: {str(e)}"
        )

@router.post("/bulk/write")
async def bulk_write(entries: list[MemoryWriteRequest]):
    """
    Write multiple memory entries at once
    
    Args:
        entries: List of memory entries to write
        
    Returns:
        List of created entries
    """
    try:
        created = []
        for entry_request in entries:
            entry = await memory_manager.write(entry_request)
            created.append(entry)

        return {
            "status": "success",
            "created": len(created),
            "entries": created
        }

    except Exception as e:
        logger.error(f"Bulk write failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Bulk write failed: {str(e)}"
        )

@router.post("/bulk/delete")
async def bulk_delete(memory_ids: list[str]):
    """
    Delete multiple memory entries at once
    
    Args:
        memory_ids: List of memory IDs to delete
        
    Returns:
        Deletion status
    """
    try:
        deleted = []
        failed = []

        for memory_id in memory_ids:
            try:
                success = await memory_manager.delete(memory_id)
                if success:
                    deleted.append(memory_id)
                else:
                    failed.append(memory_id)
            except:
                failed.append(memory_id)

        return {
            "status": "partial" if failed else "success",
            "deleted": deleted,
            "failed": failed,
            "total_deleted": len(deleted),
            "total_failed": len(failed)
        }

    except Exception as e:
        logger.error(f"Bulk delete failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Bulk delete failed: {str(e)}"
        )

@router.post("/consolidate")
async def consolidate_memories(
    similarity_threshold: float = Query(default=0.85, description="Threshold for similar memories"),
    max_consolidations: int = Query(default=50, description="Maximum consolidations per run")
):
    """
    Consolidate similar memory entries to reduce redundancy
    
    Args:
        similarity_threshold: Minimum similarity to consider for consolidation
        max_consolidations: Maximum number of consolidations to perform
        
    Returns:
        Consolidation results
    """
    try:
        await memory_manager._ensure_initialized()

        # Get all memory entries
        all_entries = list(memory_manager.entries.values())
        consolidations = []
        consolidated_ids = set()

        for i, entry1 in enumerate(all_entries):
            if entry1.id in consolidated_ids or len(consolidations) >= max_consolidations:
                continue

            similar_entries = []
            for j, entry2 in enumerate(all_entries[i+1:], i+1):
                if entry2.id in consolidated_ids:
                    continue

                # Search for similarity using RAG pipeline
                search_results = await memory_manager.rag_pipeline.retrieve(
                    query=entry1.content,
                    node_type=KnowledgeNodeType.MEMORY,
                    k=1
                )

                if search_results and search_results[0].metadata.get("id") == entry2.id:
                    similarity = search_results[0].metadata.get("similarity_score", 0.0)
                    if similarity >= similarity_threshold:
                        similar_entries.append((entry2, similarity))

            if similar_entries:
                # Consolidate entries
                combined_content = entry1.content
                combined_metadata = entry1.metadata.copy()
                combined_tags = set(entry1.tags)

                for similar_entry, score in similar_entries:
                    combined_content += f"\n\n--- Consolidated from {similar_entry.id} ---\n{similar_entry.content}"
                    combined_metadata.update(similar_entry.metadata)
                    combined_tags.update(similar_entry.tags)
                    consolidated_ids.add(similar_entry.id)

                # Update the primary entry
                entry1.content = combined_content
                entry1.metadata = combined_metadata
                entry1.tags = list(combined_tags)
                entry1.updated_at = datetime.utcnow()

                consolidations.append({
                    "primary_id": entry1.id,
                    "consolidated_ids": [e[0].id for e in similar_entries],
                    "similarity_scores": [e[1] for e in similar_entries]
                })

        # Remove consolidated entries
        for entry_id in consolidated_ids:
            await memory_manager.delete(entry_id)

        return {
            "status": "success",
            "consolidations_performed": len(consolidations),
            "entries_removed": len(consolidated_ids),
            "details": consolidations
        }

    except Exception as e:
        logger.error(f"Memory consolidation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Consolidation failed: {str(e)}"
        )

@router.post("/context-search")
async def context_aware_search(
    query: str,
    context: Optional[str] = None,
    conversation_history: Optional[list[str]] = None,
    top_k: int = Query(default=10, ge=1, le=50)
):
    """
    Perform context-aware memory search
    
    Args:
        query: Search query
        context: Current context or situation
        conversation_history: Recent conversation messages
        top_k: Number of results
        
    Returns:
        Context-aware search results
    """
    try:
        await memory_manager._ensure_initialized()

        # Enhance query with context
        enhanced_query = query
        if context:
            enhanced_query += f" Context: {context}"

        if conversation_history:
            recent_context = " ".join(conversation_history[-3:])  # Last 3 messages
            enhanced_query += f" Recent conversation: {recent_context}"

        # Perform enhanced search
        search_request = MemorySearchRequest(
            query=enhanced_query,
            top_k=top_k,
            use_rag=True,
            knowledge_types=["memory", "codebase", "logs"]
        )

        results = await memory_manager.search(search_request)

        # Re-rank results based on context relevance
        if context or conversation_history:
            for result in results:
                context_score = 0.0

                # Check context relevance
                if context and context.lower() in result.content.lower():
                    context_score += 0.2

                # Check conversation history relevance
                if conversation_history:
                    for msg in conversation_history[-2:]:
                        if any(word in result.content.lower() for word in msg.lower().split()[:5]):
                            context_score += 0.1

                # Adjust similarity score
                if result.similarity_score:
                    result.similarity_score = (result.similarity_score * 0.8) + (context_score * 0.2)

            # Re-sort by adjusted scores
            results.sort(key=lambda x: x.similarity_score or 0.0, reverse=True)

        return {
            "query": query,
            "enhanced_query": enhanced_query,
            "results": results,
            "total_found": len(results)
        }

    except Exception as e:
        logger.error(f"Context-aware search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Context search failed: {str(e)}"
        )

@router.get("/knowledge-graph")
async def get_knowledge_graph(
    center_id: Optional[str] = None,
    max_depth: int = Query(default=2, ge=1, le=4),
    min_similarity: float = Query(default=0.6, ge=0.1, le=1.0)
):
    """
    Get knowledge graph representation of memory connections
    
    Args:
        center_id: Central memory ID to build graph around
        max_depth: Maximum depth for connections
        min_similarity: Minimum similarity for connections
        
    Returns:
        Knowledge graph data
    """
    try:
        await memory_manager._ensure_initialized()

        nodes = []
        edges = []
        processed = set()

        # Start with center node or all entries
        if center_id and center_id in memory_manager.entries:
            start_entries = [memory_manager.entries[center_id]]
        else:
            start_entries = list(memory_manager.entries.values())[:20]  # Limit for performance

        # Build graph
        for entry in start_entries:
            if entry.id in processed:
                continue

            nodes.append({
                "id": entry.id,
                "content": entry.content[:200] + "..." if len(entry.content) > 200 else entry.content,
                "category": entry.category,
                "tags": entry.tags,
                "created_at": entry.created_at.isoformat(),
                "size": len(entry.content)
            })
            processed.add(entry.id)

            # Find connected entries
            search_request = MemorySearchRequest(
                query=entry.content,
                top_k=10,
                similarity_threshold=min_similarity,
                use_rag=True
            )

            related = await memory_manager.search(search_request)

            for related_entry in related:
                if related_entry.id != entry.id and related_entry.id not in processed:
                    nodes.append({
                        "id": related_entry.id,
                        "content": related_entry.content[:200] + "..." if len(related_entry.content) > 200 else related_entry.content,
                        "category": related_entry.category,
                        "tags": related_entry.tags,
                        "created_at": related_entry.created_at.isoformat(),
                        "size": len(related_entry.content)
                    })
                    processed.add(related_entry.id)

                # Add edge
                if related_entry.similarity_score and related_entry.similarity_score >= min_similarity:
                    edges.append({
                        "source": entry.id,
                        "target": related_entry.id,
                        "similarity": related_entry.similarity_score,
                        "weight": related_entry.similarity_score
                    })

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "center_id": center_id,
                "max_depth": max_depth,
                "min_similarity": min_similarity
            }
        }

    except Exception as e:
        logger.error(f"Knowledge graph generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Knowledge graph failed: {str(e)}"
        )

@router.get("/stats/overview")
async def get_memory_stats():
    """
    Get memory system statistics
    
    Returns:
        Memory usage statistics
    """
    try:
        total_entries = len(memory_manager.entries)
        categories = {}
        total_size = 0

        for entry in memory_manager.entries.values():
            cat = entry.category
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1
            total_size += len(entry.content)

        return {
            "statistics": {
                "total_entries": total_entries,
                "total_size_bytes": total_size,
                "average_entry_size": total_size / total_entries if total_entries > 0 else 0,
                "categories": len(categories),
                "last_updated": datetime.utcnow().isoformat()
            },
            "breakdown": {
                "by_category": categories
            },
            "rag_status": {
                "initialized": memory_manager._initialized,
                "vector_store_size": len(memory_manager.entries) if memory_manager._initialized else 0
            }
        }

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )
