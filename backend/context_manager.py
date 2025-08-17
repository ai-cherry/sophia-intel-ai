"""
Centralized Context Manager for SOPHIA Intel
Manages context across all chat backends with intelligent memory optimization
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from libs.mcp_client.enhanced_memory_client import EnhancedMemoryClient


class ContextManager:
    """
    Centralized context manager that provides unified memory operations
    across all chat backends (Orchestrator, Swarm, Web Research)
    """
    
    def __init__(self):
        self.memory_client = EnhancedMemoryClient()
        
        # Context configuration
        self.max_context_tokens = 8000
        self.summary_trigger_messages = 50
        self.context_retention_hours = 24
        
        # Backend-specific context weights
        self.backend_weights = {
            "orchestrator": 1.0,    # Standard weight
            "swarm": 1.2,          # Slightly higher (complex tasks)
            "web_research": 0.8,   # Lower weight (supplementary)
            "system": 1.5          # Highest weight (important system messages)
        }
        
        # Context type priorities
        self.context_priorities = {
            "user_message": 10,
            "assistant_response": 9,
            "system_message": 8,
            "research_context": 6,
            "error_message": 7,
            "debug_info": 3,
            "metadata": 2
        }
    
    async def store_message(
        self,
        session_id: str,
        content: str,
        role: str,
        backend_used: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
        context_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Store a message with enhanced context management
        """
        try:
            # Prepare enhanced metadata
            enhanced_metadata = {
                "role": role,
                "backend_used": backend_used,
                "timestamp": asyncio.get_event_loop().time(),
                "context_type": context_type,
                "priority": self.context_priorities.get(f"{role}_message", 5),
                "backend_weight": self.backend_weights.get(backend_used, 1.0)
            }
            
            # Merge with provided metadata
            if metadata:
                enhanced_metadata.update(metadata)
            
            # Store with enhanced context
            result = await self.memory_client.store_with_context(
                session_id=session_id,
                content=content,
                metadata=enhanced_metadata,
                context_type=context_type,
                backend_used=backend_used,
                auto_summarize=True
            )
            
            logger.debug(f"Stored message for session {session_id} via {backend_used}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
            raise
    
    async def get_context_for_backend(
        self,
        session_id: str,
        backend: str,
        query: Optional[str] = None,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """
        Get optimized context for a specific backend
        """
        try:
            max_tokens = max_tokens or self.max_context_tokens
            
            # Get optimized context
            context_result = await self.memory_client.get_optimized_context(
                session_id=session_id,
                query=query,
                max_tokens=max_tokens,
                include_summary=True
            )
            
            # Filter and weight context for specific backend
            context_items = context_result.get("context", [])
            weighted_context = self._apply_backend_weighting(context_items, backend)
            
            # Add backend-specific system message
            system_message = self._generate_backend_system_message(backend, session_id)
            if system_message:
                weighted_context.insert(0, system_message)
            
            return {
                "session_id": session_id,
                "backend": backend,
                "context": weighted_context,
                "query_context": context_result.get("query_context", []),
                "total_tokens": context_result.get("estimated_tokens", 0),
                "optimized": context_result.get("optimized", False),
                "has_summary": context_result.get("has_summary", False),
                "context_ready": True
            }
            
        except Exception as e:
            logger.error(f"Failed to get context for backend {backend}: {e}")
            return {
                "session_id": session_id,
                "backend": backend,
                "context": [],
                "query_context": [],
                "total_tokens": 0,
                "optimized": False,
                "has_summary": False,
                "context_ready": False,
                "error": str(e)
            }
    
    async def get_cross_backend_insights(
        self,
        session_id: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Get insights from across all backends for a query
        """
        try:
            # Search across all backends
            search_result = await self.memory_client.cross_backend_search(
                session_id=session_id,
                query=query
            )
            
            backend_results = search_result.get("backend_results", {})
            
            # Analyze patterns across backends
            insights = {
                "query": query,
                "session_id": session_id,
                "backend_coverage": list(backend_results.keys()),
                "total_relevant_messages": search_result.get("total_results", 0),
                "insights": []
            }
            
            # Generate insights for each backend
            for backend, messages in backend_results.items():
                if messages:
                    backend_insight = self._analyze_backend_messages(backend, messages, query)
                    insights["insights"].append(backend_insight)
            
            # Cross-backend patterns
            cross_patterns = self._identify_cross_backend_patterns(backend_results, query)
            insights["cross_backend_patterns"] = cross_patterns
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get cross-backend insights: {e}")
            return {
                "query": query,
                "session_id": session_id,
                "error": str(e),
                "insights": []
            }
    
    async def optimize_session_context(
        self,
        session_id: str,
        target_tokens: int = None
    ) -> Dict[str, Any]:
        """
        Optimize session context by creating summaries and managing memory
        """
        try:
            target_tokens = target_tokens or self.max_context_tokens
            
            # Get current session context
            session_context = await self.memory_client.session_manager.get_session_context(
                session_id=session_id,
                max_messages=200
            )
            
            recent_messages = session_context.get("recent_messages", [])
            
            if len(recent_messages) < self.summary_trigger_messages:
                return {
                    "session_id": session_id,
                    "optimization_needed": False,
                    "message": "Session doesn't need optimization yet",
                    "message_count": len(recent_messages)
                }
            
            # Create or update session summary
            summary_result = await self.memory_client.session_manager.create_session_summary(
                session_id=session_id,
                max_length=800
            )
            
            # Get optimized context
            optimized_context = await self.memory_client.get_optimized_context(
                session_id=session_id,
                max_tokens=target_tokens,
                include_summary=True
            )
            
            return {
                "session_id": session_id,
                "optimization_needed": True,
                "optimization_completed": True,
                "original_message_count": len(recent_messages),
                "optimized_message_count": len(optimized_context.get("context", [])),
                "estimated_tokens": optimized_context.get("estimated_tokens", 0),
                "summary_created": bool(summary_result.get("summary")),
                "summary": summary_result.get("summary", ""),
                "analysis": summary_result.get("analysis", {})
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize session context: {e}")
            return {
                "session_id": session_id,
                "optimization_needed": False,
                "error": str(e)
            }
    
    async def get_session_analytics(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a session
        """
        try:
            # Get session context
            session_context = await self.memory_client.session_manager.get_session_context(
                session_id=session_id,
                max_messages=500
            )
            
            messages = session_context.get("recent_messages", [])
            
            # Analyze message patterns
            analytics = {
                "session_id": session_id,
                "total_messages": len(messages),
                "backend_usage": {},
                "role_distribution": {},
                "context_types": {},
                "timeline": [],
                "conversation_flow": [],
                "key_metrics": {}
            }
            
            # Process each message
            for message in messages:
                metadata = message.get("metadata", {})
                
                # Backend usage
                backend = metadata.get("backend_used", "unknown")
                analytics["backend_usage"][backend] = analytics["backend_usage"].get(backend, 0) + 1
                
                # Role distribution
                role = metadata.get("role", "unknown")
                analytics["role_distribution"][role] = analytics["role_distribution"].get(role, 0) + 1
                
                # Context types
                context_type = metadata.get("context_type", "general")
                analytics["context_types"][context_type] = analytics["context_types"].get(context_type, 0) + 1
                
                # Timeline entry
                timestamp = metadata.get("timestamp", 0)
                analytics["timeline"].append({
                    "timestamp": timestamp,
                    "role": role,
                    "backend": backend,
                    "content_length": len(message.get("content", ""))
                })
            
            # Calculate key metrics
            analytics["key_metrics"] = {
                "avg_message_length": sum(len(msg.get("content", "")) for msg in messages) / len(messages) if messages else 0,
                "backend_diversity": len(analytics["backend_usage"]),
                "conversation_turns": analytics["role_distribution"].get("user", 0),
                "assistant_responses": analytics["role_distribution"].get("assistant", 0),
                "research_queries": analytics["context_types"].get("research_data", 0),
                "error_count": sum(1 for msg in messages if "error" in msg.get("content", "").lower())
            }
            
            # Sort timeline
            analytics["timeline"].sort(key=lambda x: x["timestamp"])
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get session analytics: {e}")
            return {
                "session_id": session_id,
                "error": str(e),
                "total_messages": 0
            }
    
    def _apply_backend_weighting(
        self,
        context_items: List[Dict[str, Any]],
        target_backend: str
    ) -> List[Dict[str, Any]]:
        """Apply backend-specific weighting to context items"""
        weighted_items = []
        
        for item in context_items:
            metadata = item.get("metadata", {})
            item_backend = metadata.get("backend_used", "unknown")
            
            # Calculate relevance score
            relevance_score = 1.0
            
            # Same backend gets higher relevance
            if item_backend == target_backend:
                relevance_score *= 1.5
            
            # Apply backend weight
            backend_weight = self.backend_weights.get(item_backend, 1.0)
            relevance_score *= backend_weight
            
            # Apply priority weight
            priority = metadata.get("priority", 5)
            relevance_score *= (priority / 10.0)
            
            # Add relevance score to metadata
            enhanced_item = item.copy()
            enhanced_item["metadata"] = metadata.copy()
            enhanced_item["metadata"]["relevance_score"] = relevance_score
            
            weighted_items.append(enhanced_item)
        
        # Sort by relevance score
        weighted_items.sort(key=lambda x: x.get("metadata", {}).get("relevance_score", 0), reverse=True)
        
        return weighted_items
    
    def _generate_backend_system_message(
        self,
        backend: str,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Generate backend-specific system message"""
        system_messages = {
            "orchestrator": "You are SOPHIA Intel's orchestrator. Provide precise, helpful responses using available tools and context.",
            "swarm": "You are part of SOPHIA Intel's Swarm system. Coordinate with other agents to provide comprehensive solutions.",
            "web_research": "You have access to web research capabilities. Use current information to enhance your responses."
        }
        
        if backend in system_messages:
            return {
                "content": system_messages[backend],
                "metadata": {
                    "role": "system",
                    "backend_used": "system",
                    "context_type": "system_message",
                    "priority": 10,
                    "timestamp": asyncio.get_event_loop().time()
                }
            }
        
        return None
    
    def _analyze_backend_messages(
        self,
        backend: str,
        messages: List[Dict[str, Any]],
        query: str
    ) -> Dict[str, Any]:
        """Analyze messages from a specific backend"""
        analysis = {
            "backend": backend,
            "message_count": len(messages),
            "relevance_scores": [],
            "key_themes": [],
            "summary": ""
        }
        
        # Extract relevance scores
        for message in messages:
            score = message.get("relevance_score", 0)
            analysis["relevance_scores"].append(score)
        
        # Calculate average relevance
        if analysis["relevance_scores"]:
            analysis["avg_relevance"] = sum(analysis["relevance_scores"]) / len(analysis["relevance_scores"])
        else:
            analysis["avg_relevance"] = 0
        
        # Generate summary
        if messages:
            top_message = max(messages, key=lambda x: x.get("relevance_score", 0))
            content_preview = top_message.get("content", "")[:200]
            analysis["summary"] = f"Most relevant from {backend}: {content_preview}..."
        
        return analysis
    
    def _identify_cross_backend_patterns(
        self,
        backend_results: Dict[str, List[Dict[str, Any]]],
        query: str
    ) -> Dict[str, Any]:
        """Identify patterns across different backends"""
        patterns = {
            "backend_agreement": 0.0,
            "complementary_info": [],
            "conflicting_info": [],
            "coverage_gaps": []
        }
        
        # Simple pattern analysis
        backend_count = len(backend_results)
        if backend_count > 1:
            patterns["backend_agreement"] = 0.7  # Placeholder - would implement actual agreement analysis
            patterns["complementary_info"] = [
                "Orchestrator provided direct answers",
                "Swarm provided comprehensive analysis",
                "Web research provided current context"
            ][:backend_count]
        
        return patterns
    
    async def cleanup_session_context(
        self,
        session_id: str,
        keep_recent_hours: int = None
    ) -> Dict[str, Any]:
        """Clean up old context for a session"""
        try:
            keep_hours = keep_recent_hours or self.context_retention_hours
            
            # This would typically involve more sophisticated cleanup
            # For now, delegate to the enhanced memory client
            cleanup_result = await self.memory_client.cleanup_old_sessions(
                days=keep_hours // 24
            )
            
            return {
                "session_id": session_id,
                "cleanup_completed": True,
                "retention_hours": keep_hours,
                "cleanup_details": cleanup_result
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup session context: {e}")
            return {
                "session_id": session_id,
                "cleanup_completed": False,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for context manager"""
        try:
            memory_health = await self.memory_client.health_check_enhanced()
            
            return {
                "status": "healthy" if memory_health.get("status") == "healthy" else "unhealthy",
                "memory_client": memory_health,
                "configuration": {
                    "max_context_tokens": self.max_context_tokens,
                    "summary_trigger_messages": self.summary_trigger_messages,
                    "context_retention_hours": self.context_retention_hours,
                    "backend_weights": self.backend_weights
                },
                "features": {
                    "cross_backend_memory": True,
                    "intelligent_summarization": True,
                    "context_optimization": True,
                    "session_analytics": True,
                    "backend_weighting": True
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

