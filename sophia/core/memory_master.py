"""
SOPHIA Memory Master
Orchestrates memory operations, embeddings, and knowledge management.
"""

import os
import logging
from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime, timezone

from .api_manager import SOPHIAAPIManager
from .ultimate_model_router import UltimateModelRouter
from .mcp_client import SOPHIAMCPClient

logger = logging.getLogger(__name__)

class SOPHIAMemoryMaster:
    """
    Master class for memory and knowledge management.
    Orchestrates embeddings, vector storage, and semantic retrieval.
    """
    
    def __init__(self):
        """Initialize memory master with required components."""
        self.api_manager = SOPHIAAPIManager()
        self.model_router = UltimateModelRouter()
        self.mcp_client = None  # Will be initialized when needed
        
        # Memory configuration
        self.default_collection = "default"
        self.memory_types = [
            "conversation", "fact", "procedure", "insight", 
            "research", "customer", "code", "business"
        ]
        
        logger.info("Initialized SOPHIAMemoryMaster")
    
    async def _get_mcp_client(self) -> SOPHIAMCPClient:
        """Get or create MCP client."""
        if self.mcp_client is None:
            self.mcp_client = SOPHIAMCPClient()
        return self.mcp_client
    
    async def store_knowledge(
        self,
        content: str,
        knowledge_type: str = "fact",
        metadata: Optional[Dict[str, Any]] = None,
        collection: str = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store knowledge with automatic embedding generation.
        
        Args:
            content: Content to store
            knowledge_type: Type of knowledge (fact, procedure, insight, etc.)
            metadata: Additional metadata
            collection: Vector collection name
            session_id: Associated session ID
            
        Returns:
            Storage result with memory and embedding IDs
        """
        try:
            logger.info(f"Storing knowledge of type: {knowledge_type}")
            
            mcp_client = await self._get_mcp_client()
            collection = collection or self.default_collection
            
            # Store as memory
            memory_result = await mcp_client.store_memory(
                content=content,
                memory_type=knowledge_type,
                session_id=session_id,
                metadata=metadata
            )
            
            # Store as embedding
            embedding_metadata = metadata or {}
            embedding_metadata.update({
                "memory_id": memory_result.get("memory_id"),
                "knowledge_type": knowledge_type,
                "session_id": session_id,
                "stored_at": datetime.now(timezone.utc).isoformat()
            })
            
            embedding_result = await mcp_client.store_embedding(
                text=content,
                metadata=embedding_metadata,
                collection_name=collection
            )
            
            result = {
                "memory_id": memory_result.get("memory_id"),
                "embedding_id": embedding_result.get("embedding_id"),
                "vector_id": embedding_result.get("vector_id"),
                "knowledge_type": knowledge_type,
                "collection": collection,
                "status": "stored"
            }
            
            logger.info(f"Successfully stored knowledge: {result['memory_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Knowledge storage failed: {e}")
            raise
    
    async def retrieve_knowledge(
        self,
        query: str,
        knowledge_types: Optional[List[str]] = None,
        collection: str = None,
        limit: int = 10,
        score_threshold: float = 0.7,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve knowledge using semantic search.
        
        Args:
            query: Search query
            knowledge_types: Filter by knowledge types
            collection: Vector collection to search
            limit: Maximum results to return
            score_threshold: Minimum similarity score
            session_id: Filter by session ID
            
        Returns:
            Retrieved knowledge with relevance scores
        """
        try:
            logger.info(f"Retrieving knowledge for query: {query}")
            
            mcp_client = await self._get_mcp_client()
            collection = collection or self.default_collection
            
            # Search embeddings for semantic similarity
            embedding_results = await mcp_client.search_embeddings(
                query=query,
                collection_name=collection,
                top_k=limit,
                score_threshold=score_threshold
            )
            
            # Also search memories for additional context
            memory_results_tasks = []
            if knowledge_types:
                for knowledge_type in knowledge_types:
                    memory_results_tasks.append(
                        mcp_client.retrieve_memories(
                            query=query,
                            memory_type=knowledge_type,
                            session_id=session_id,
                            limit=limit // len(knowledge_types) if len(knowledge_types) > 1 else limit
                        )
                    )
            else:
                memory_results_tasks.append(
                    mcp_client.retrieve_memories(
                        query=query,
                        session_id=session_id,
                        limit=limit
                    )
                )
            
            # Execute memory searches concurrently
            memory_results_list = await asyncio.gather(*memory_results_tasks, return_exceptions=True)
            
            # Combine and deduplicate results
            all_memories = []
            for memory_result in memory_results_list:
                if isinstance(memory_result, dict) and "memories" in memory_result:
                    all_memories.extend(memory_result["memories"])
                elif isinstance(memory_result, Exception):
                    logger.error(f"Memory search failed: {memory_result}")
            
            # Merge embedding and memory results
            combined_results = self._merge_search_results(
                embedding_results.get("results", []),
                all_memories,
                query
            )
            
            result = {
                "query": query,
                "results": combined_results[:limit],
                "total_found": len(combined_results),
                "search_types": ["embeddings", "memories"],
                "knowledge_types": knowledge_types,
                "collection": collection
            }
            
            logger.info(f"Retrieved {len(combined_results)} knowledge items")
            return result
            
        except Exception as e:
            logger.error(f"Knowledge retrieval failed: {e}")
            raise
    
    async def store_conversation(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store conversation with automatic knowledge extraction.
        
        Args:
            session_id: Session identifier
            messages: List of conversation messages
            metadata: Additional metadata
            
        Returns:
            Storage result with extracted knowledge
        """
        try:
            logger.info(f"Storing conversation for session: {session_id}")
            
            mcp_client = await self._get_mcp_client()
            
            # Store individual messages
            stored_messages = []
            for message in messages:
                try:
                    result = await mcp_client.add_message(
                        session_id=session_id,
                        role=message.get("role", "user"),
                        content=message.get("content", ""),
                        metadata=message.get("metadata")
                    )
                    stored_messages.append(result)
                except Exception as e:
                    logger.error(f"Failed to store message: {e}")
            
            # Extract and store key insights from conversation
            insights = await self._extract_conversation_insights(messages)
            stored_insights = []
            
            for insight in insights:
                try:
                    insight_result = await self.store_knowledge(
                        content=insight["content"],
                        knowledge_type="insight",
                        metadata={
                            "session_id": session_id,
                            "insight_type": insight["type"],
                            "confidence": insight.get("confidence", 0.8),
                            **(metadata or {})
                        },
                        session_id=session_id
                    )
                    stored_insights.append(insight_result)
                except Exception as e:
                    logger.error(f"Failed to store insight: {e}")
            
            result = {
                "session_id": session_id,
                "messages_stored": len(stored_messages),
                "insights_extracted": len(stored_insights),
                "insights": stored_insights,
                "status": "stored"
            }
            
            logger.info(f"Stored conversation with {len(stored_insights)} insights")
            return result
            
        except Exception as e:
            logger.error(f"Conversation storage failed: {e}")
            raise
    
    async def get_contextual_memory(
        self,
        query: str,
        session_id: Optional[str] = None,
        context_window: int = 10,
        include_related: bool = True
    ) -> Dict[str, Any]:
        """
        Get contextually relevant memory for a query.
        
        Args:
            query: Current query or context
            session_id: Current session ID
            context_window: Number of recent items to include
            include_related: Include semantically related memories
            
        Returns:
            Contextual memory with relevance ranking
        """
        try:
            logger.info(f"Getting contextual memory for query: {query}")
            
            mcp_client = await self._get_mcp_client()
            
            # Get recent session context if session_id provided
            session_context = []
            if session_id:
                try:
                    session_result = await mcp_client.get_session_context(
                        session_id=session_id,
                        limit=context_window
                    )
                    session_context = session_result.get("messages", [])
                except Exception as e:
                    logger.error(f"Failed to get session context: {e}")
            
            # Get semantically related memories
            related_memories = []
            if include_related:
                try:
                    memory_result = await self.retrieve_knowledge(
                        query=query,
                        limit=context_window,
                        score_threshold=0.6
                    )
                    related_memories = memory_result.get("results", [])
                except Exception as e:
                    logger.error(f"Failed to get related memories: {e}")
            
            # Rank and combine context
            contextual_items = self._rank_contextual_relevance(
                query, session_context, related_memories
            )
            
            result = {
                "query": query,
                "session_id": session_id,
                "contextual_items": contextual_items[:context_window],
                "session_context_count": len(session_context),
                "related_memories_count": len(related_memories),
                "total_context_items": len(contextual_items)
            }
            
            logger.info(f"Retrieved {len(contextual_items)} contextual items")
            return result
            
        except Exception as e:
            logger.error(f"Contextual memory retrieval failed: {e}")
            raise
    
    async def create_knowledge_graph(
        self,
        entities: List[str],
        relationships: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create knowledge graph from entities and relationships.
        
        Args:
            entities: List of entity names
            relationships: List of relationship definitions
            metadata: Additional metadata
            
        Returns:
            Knowledge graph creation result
        """
        try:
            logger.info(f"Creating knowledge graph with {len(entities)} entities")
            
            # Store entities as knowledge
            stored_entities = []
            for entity in entities:
                try:
                    entity_result = await self.store_knowledge(
                        content=f"Entity: {entity}",
                        knowledge_type="entity",
                        metadata={
                            "entity_name": entity,
                            "graph_id": self._generate_graph_id(),
                            **(metadata or {})
                        }
                    )
                    stored_entities.append(entity_result)
                except Exception as e:
                    logger.error(f"Failed to store entity {entity}: {e}")
            
            # Store relationships
            stored_relationships = []
            if relationships:
                for relationship in relationships:
                    try:
                        rel_content = f"Relationship: {relationship.get('source')} -> {relationship.get('target')} ({relationship.get('type', 'related')})"
                        rel_result = await self.store_knowledge(
                            content=rel_content,
                            knowledge_type="relationship",
                            metadata={
                                "source_entity": relationship.get("source"),
                                "target_entity": relationship.get("target"),
                                "relationship_type": relationship.get("type", "related"),
                                "graph_id": self._generate_graph_id(),
                                **(metadata or {})
                            }
                        )
                        stored_relationships.append(rel_result)
                    except Exception as e:
                        logger.error(f"Failed to store relationship: {e}")
            
            result = {
                "entities_stored": len(stored_entities),
                "relationships_stored": len(stored_relationships),
                "graph_id": self._generate_graph_id(),
                "status": "created"
            }
            
            logger.info(f"Created knowledge graph: {result['graph_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Knowledge graph creation failed: {e}")
            raise
    
    async def _extract_conversation_insights(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract key insights from conversation messages."""
        try:
            if not messages:
                return []
            
            # Prepare conversation text
            conversation_text = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in messages[-10:]  # Last 10 messages
            ])
            
            model_config = self.model_router.select_model("analysis")
            
            insights_prompt = f"""
Analyze the following conversation and extract key insights, facts, and actionable items:

{conversation_text}

Please identify:
1. Important facts or information shared
2. Decisions made or conclusions reached
3. Action items or next steps
4. Key insights or learnings
5. Important context or background information

Format each insight as:
Type: [fact/decision/action/insight/context]
Content: [the actual insight]
Confidence: [0.0-1.0]

Insights:
"""
            
            response = await self.model_router.call_model(
                model_config,
                insights_prompt,
                temperature=0.3,
                max_tokens=1024
            )
            
            # Parse insights from response
            insights = []
            current_insight = {}
            
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('Type:'):
                    if current_insight:
                        insights.append(current_insight)
                    current_insight = {"type": line.replace('Type:', '').strip()}
                elif line.startswith('Content:'):
                    current_insight["content"] = line.replace('Content:', '').strip()
                elif line.startswith('Confidence:'):
                    try:
                        confidence = float(line.replace('Confidence:', '').strip())
                        current_insight["confidence"] = confidence
                    except ValueError:
                        current_insight["confidence"] = 0.8
            
            # Add the last insight
            if current_insight and "content" in current_insight:
                insights.append(current_insight)
            
            return insights[:5]  # Limit to top 5 insights
            
        except Exception as e:
            logger.error(f"Insight extraction failed: {e}")
            return []
    
    def _merge_search_results(
        self,
        embedding_results: List[Dict[str, Any]],
        memory_results: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """Merge and deduplicate search results from different sources."""
        try:
            combined = []
            seen_content = set()
            
            # Add embedding results
            for result in embedding_results:
                content = result.get("text", "")
                if content and content not in seen_content:
                    seen_content.add(content)
                    combined.append({
                        "content": content,
                        "score": result.get("score", 0.0),
                        "source": "embedding",
                        "metadata": result.get("metadata", {}),
                        "id": result.get("id")
                    })
            
            # Add memory results
            for result in memory_results:
                content = result.get("content", "")
                if content and content not in seen_content:
                    seen_content.add(content)
                    combined.append({
                        "content": content,
                        "score": result.get("relevance_score", 0.0),
                        "source": "memory",
                        "metadata": result.get("metadata", {}),
                        "memory_type": result.get("memory_type"),
                        "id": result.get("memory_id")
                    })
            
            # Sort by score descending
            combined.sort(key=lambda x: x.get("score", 0.0), reverse=True)
            
            return combined
            
        except Exception as e:
            logger.error(f"Result merging failed: {e}")
            return []
    
    def _rank_contextual_relevance(
        self,
        query: str,
        session_context: List[Dict[str, Any]],
        related_memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rank contextual items by relevance to current query."""
        try:
            contextual_items = []
            
            # Add session context with recency boost
            for i, item in enumerate(reversed(session_context[-10:])):  # Most recent first
                recency_boost = 1.0 - (i * 0.1)  # Boost recent items
                contextual_items.append({
                    "content": item.get("content", ""),
                    "type": "session_message",
                    "role": item.get("role"),
                    "relevance_score": 0.5 + recency_boost,  # Base score + recency
                    "source": "session",
                    "timestamp": item.get("timestamp")
                })
            
            # Add related memories
            for item in related_memories:
                contextual_items.append({
                    "content": item.get("content", ""),
                    "type": "memory",
                    "memory_type": item.get("memory_type"),
                    "relevance_score": item.get("score", 0.0),
                    "source": "memory",
                    "metadata": item.get("metadata", {})
                })
            
            # Sort by relevance score
            contextual_items.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
            
            return contextual_items
            
        except Exception as e:
            logger.error(f"Contextual ranking failed: {e}")
            return []
    
    def _generate_graph_id(self) -> str:
        """Generate unique graph ID."""
        import uuid
        return str(uuid.uuid4())
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory storage statistics."""
        try:
            mcp_client = await self._get_mcp_client()
            
            # Get stats from MCP server
            try:
                response = await mcp_client.client.get(f"{mcp_client.base_url}/memory/stats")
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"Failed to get MCP memory stats: {e}")
            
            # Fallback to basic stats
            return {
                "status": "basic_stats_only",
                "collections": ["default", "memories", "code", "research"],
                "memory_types": self.memory_types
            }
            
        except Exception as e:
            logger.error(f"Memory statistics failed: {e}")
            raise
    
    async def close(self):
        """Close connections."""
        if self.mcp_client:
            await self.mcp_client.close()

