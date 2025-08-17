"""
Enhanced Memory Client for SOPHIA Intel
Advanced contextual awareness with cross-backend memory sharing,
intelligent summarization, and context length optimization
"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
from loguru import logger

from libs.mcp_client.memory_client import MCPMemoryClient


class ContextWindow:
    """Manages context window with intelligent truncation and summarization"""
    
    def __init__(self, max_tokens: int = 8000, summary_threshold: int = 6000):
        self.max_tokens = max_tokens
        self.summary_threshold = summary_threshold
        self.token_estimate_ratio = 4  # Rough chars per token estimate
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text length"""
        return len(text) // self.token_estimate_ratio
    
    def needs_summarization(self, context_list: List[Dict[str, Any]]) -> bool:
        """Check if context needs summarization"""
        total_tokens = sum(
            self.estimate_tokens(item.get("content", "")) 
            for item in context_list
        )
        return total_tokens > self.summary_threshold
    
    def truncate_context(self, context_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Intelligently truncate context to fit window"""
        if not context_list:
            return []
        
        # Sort by importance (recent messages, user messages, system messages)
        sorted_context = sorted(context_list, key=self._calculate_importance, reverse=True)
        
        truncated = []
        current_tokens = 0
        
        for item in sorted_context:
            item_tokens = self.estimate_tokens(item.get("content", ""))
            
            if current_tokens + item_tokens <= self.max_tokens:
                truncated.append(item)
                current_tokens += item_tokens
            else:
                # Try to fit a truncated version
                remaining_tokens = self.max_tokens - current_tokens
                if remaining_tokens > 100:  # Only if we have reasonable space
                    truncated_content = item.get("content", "")[:remaining_tokens * self.token_estimate_ratio]
                    truncated_item = item.copy()
                    truncated_item["content"] = truncated_content + "... [truncated]"
                    truncated_item["metadata"] = item.get("metadata", {}).copy()
                    truncated_item["metadata"]["truncated"] = True
                    truncated.append(truncated_item)
                break
        
        # Restore chronological order for final context
        return sorted(truncated, key=lambda x: x.get("metadata", {}).get("timestamp", 0))
    
    def _calculate_importance(self, item: Dict[str, Any]) -> float:
        """Calculate importance score for context item"""
        metadata = item.get("metadata", {})
        score = 0.0
        
        # Recent messages are more important
        timestamp = metadata.get("timestamp", 0)
        recency_score = timestamp / 1000000  # Normalize timestamp
        score += recency_score * 0.3
        
        # User messages are important
        if metadata.get("role") == "user":
            score += 1.0
        
        # System messages are important
        if metadata.get("role") == "system":
            score += 0.8
        
        # Research context is valuable
        if metadata.get("type") == "research_context":
            score += 0.6
        
        # Error messages are important for debugging
        if "error" in item.get("content", "").lower():
            score += 0.5
        
        # Backend information is useful
        if metadata.get("backend_used"):
            score += 0.2
        
        return score


class SessionManager:
    """Manages session lifecycle and cross-backend memory sharing"""
    
    def __init__(self, memory_client: MCPMemoryClient):
        self.memory_client = memory_client
        self.active_sessions = {}
        self.session_summaries = {}
        
    async def get_session_context(
        self, 
        session_id: str, 
        max_messages: int = 50,
        include_summaries: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive session context with summaries"""
        try:
            # Get recent messages
            recent_messages = await self.memory_client.query(
                session_id=session_id,
                query="",
                top_k=max_messages,
                threshold=0.0
            )
            
            # Get session summary if available
            session_summary = None
            if include_summaries and session_id in self.session_summaries:
                session_summary = self.session_summaries[session_id]
            
            # Get session statistics
            session_stats = await self.memory_client.get_session_stats(session_id)
            
            return {
                "session_id": session_id,
                "recent_messages": recent_messages,
                "session_summary": session_summary,
                "session_stats": session_stats,
                "total_messages": len(recent_messages),
                "context_ready": True
            }
            
        except Exception as e:
            logger.error(f"Failed to get session context: {e}")
            return {
                "session_id": session_id,
                "recent_messages": [],
                "session_summary": None,
                "session_stats": {},
                "total_messages": 0,
                "context_ready": False,
                "error": str(e)
            }
    
    async def create_session_summary(
        self, 
        session_id: str, 
        max_length: int = 500
    ) -> Dict[str, Any]:
        """Create intelligent session summary"""
        try:
            # Get all session messages
            all_messages = await self.memory_client.query(
                session_id=session_id,
                query="",
                top_k=200,  # Get more messages for comprehensive summary
                threshold=0.0
            )
            
            if not all_messages:
                return {"session_id": session_id, "summary": "", "message": "No messages to summarize"}
            
            # Analyze conversation patterns
            analysis = self._analyze_conversation_patterns(all_messages)
            
            # Create structured summary
            summary_parts = []
            
            # Add conversation overview
            summary_parts.append(f"Conversation with {analysis['total_messages']} messages")
            
            # Add backend usage
            if analysis['backend_usage']:
                backend_info = ", ".join([
                    f"{backend}: {count}" 
                    for backend, count in analysis['backend_usage'].items()
                ])
                summary_parts.append(f"Used backends: {backend_info}")
            
            # Add key topics
            if analysis['key_topics']:
                topics = ", ".join(analysis['key_topics'][:3])
                summary_parts.append(f"Key topics: {topics}")
            
            # Add feature usage
            if analysis['features_used']:
                features = ", ".join(analysis['features_used'])
                summary_parts.append(f"Features used: {features}")
            
            # Create final summary
            summary = ". ".join(summary_parts)
            
            # Truncate if too long
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            
            # Store summary
            self.session_summaries[session_id] = {
                "summary": summary,
                "created_at": datetime.now().isoformat(),
                "message_count": analysis['total_messages'],
                "analysis": analysis
            }
            
            return {
                "session_id": session_id,
                "summary": summary,
                "analysis": analysis,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create session summary: {e}")
            return {"session_id": session_id, "summary": "", "error": str(e)}
    
    def _analyze_conversation_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze conversation patterns for intelligent summarization"""
        analysis = {
            "total_messages": len(messages),
            "backend_usage": {},
            "key_topics": [],
            "features_used": [],
            "user_messages": 0,
            "assistant_messages": 0,
            "error_count": 0,
            "research_queries": 0
        }
        
        topic_keywords = {}
        
        for message in messages:
            metadata = message.get("metadata", {})
            content = message.get("content", "").lower()
            
            # Count by role
            role = metadata.get("role", "unknown")
            if role == "user":
                analysis["user_messages"] += 1
            elif role == "assistant":
                analysis["assistant_messages"] += 1
            
            # Count backend usage
            backend = metadata.get("backend_used", "unknown")
            analysis["backend_usage"][backend] = analysis["backend_usage"].get(backend, 0) + 1
            
            # Count errors
            if "error" in content or metadata.get("error"):
                analysis["error_count"] += 1
            
            # Count research queries
            if metadata.get("type") == "research_context":
                analysis["research_queries"] += 1
            
            # Extract key topics (simple keyword extraction)
            words = content.split()
            for word in words:
                if len(word) > 4 and word.isalpha():  # Filter meaningful words
                    topic_keywords[word] = topic_keywords.get(word, 0) + 1
        
        # Get top topics
        analysis["key_topics"] = sorted(
            topic_keywords.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        analysis["key_topics"] = [topic[0] for topic in analysis["key_topics"]]
        
        # Detect features used
        if analysis["research_queries"] > 0:
            analysis["features_used"].append("web_research")
        if analysis["backend_usage"].get("swarm", 0) > 0:
            analysis["features_used"].append("swarm_system")
        if analysis["error_count"] > 0:
            analysis["features_used"].append("error_handling")
        
        return analysis


class EnhancedMemoryClient(MCPMemoryClient):
    """
    Enhanced memory client with advanced contextual awareness features:
    - Cross-backend memory sharing
    - Intelligent context window management
    - Session lifecycle management
    - Advanced summarization
    - Context length optimization
    """
    
    def __init__(self, base_url: str = None):
        super().__init__(base_url)
        
        # Enhanced components
        self.context_window = ContextWindow()
        self.session_manager = SessionManager(self)
        
        # Advanced caching
        self.context_cache = {}
        self.summary_cache = {}
        
        # Configuration
        self.auto_summarize_threshold = 100  # messages
        self.context_retention_days = 30
        
    async def store_with_context(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        context_type: str = "general",
        backend_used: Optional[str] = None,
        auto_summarize: bool = True
    ) -> Dict[str, Any]:
        """
        Enhanced store with automatic context management
        """
        try:
            # Enhance metadata with backend information
            enhanced_metadata = metadata or {}
            enhanced_metadata.update({
                "timestamp": asyncio.get_event_loop().time(),
                "backend_used": backend_used,
                "context_type": context_type,
                "session_id": session_id
            })
            
            # Store the content
            result = await self.store(session_id, content, enhanced_metadata, context_type)
            
            # Check if session needs summarization
            if auto_summarize:
                await self._check_auto_summarize(session_id)
            
            # Update context cache
            await self._update_context_cache(session_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced store failed: {e}")
            raise
    
    async def get_optimized_context(
        self,
        session_id: str,
        query: Optional[str] = None,
        max_tokens: int = 8000,
        include_summary: bool = True
    ) -> Dict[str, Any]:
        """
        Get optimized context that fits within token limits
        """
        try:
            # Get session context
            session_context = await self.session_manager.get_session_context(
                session_id, 
                include_summaries=include_summary
            )
            
            recent_messages = session_context.get("recent_messages", [])
            session_summary = session_context.get("session_summary")
            
            # Apply context window optimization
            if self.context_window.needs_summarization(recent_messages):
                logger.info(f"Optimizing context for session {session_id}")
                
                # Create summary if not exists
                if not session_summary and len(recent_messages) > 10:
                    summary_result = await self.session_manager.create_session_summary(session_id)
                    session_summary = summary_result.get("summary")
                
                # Truncate recent messages
                optimized_messages = self.context_window.truncate_context(recent_messages)
            else:
                optimized_messages = recent_messages
            
            # Prepare final context
            context_parts = []
            
            # Add session summary if available
            if session_summary and include_summary:
                context_parts.append({
                    "type": "session_summary",
                    "content": session_summary,
                    "metadata": {"role": "system", "type": "summary"}
                })
            
            # Add optimized messages
            context_parts.extend(optimized_messages)
            
            # Query-specific context if provided
            query_context = []
            if query:
                query_results = await self.query(
                    session_id=session_id,
                    query=query,
                    top_k=5,
                    threshold=0.6
                )
                query_context = query_results
            
            return {
                "session_id": session_id,
                "context": context_parts,
                "query_context": query_context,
                "total_items": len(context_parts),
                "estimated_tokens": sum(
                    self.context_window.estimate_tokens(item.get("content", ""))
                    for item in context_parts
                ),
                "optimized": len(optimized_messages) < len(recent_messages),
                "has_summary": bool(session_summary)
            }
            
        except Exception as e:
            logger.error(f"Failed to get optimized context: {e}")
            return {
                "session_id": session_id,
                "context": [],
                "query_context": [],
                "total_items": 0,
                "estimated_tokens": 0,
                "optimized": False,
                "has_summary": False,
                "error": str(e)
            }
    
    async def cross_backend_search(
        self,
        session_id: str,
        query: str,
        backends: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search across different backend contexts
        """
        try:
            # Get all messages for the session
            all_messages = await self.query(
                session_id=session_id,
                query="",
                top_k=200,
                threshold=0.0
            )
            
            # Filter by backends if specified
            if backends:
                filtered_messages = [
                    msg for msg in all_messages
                    if msg.get("metadata", {}).get("backend_used") in backends
                ]
            else:
                filtered_messages = all_messages
            
            # Perform semantic search within filtered messages
            relevant_messages = []
            query_lower = query.lower()
            
            for message in filtered_messages:
                content = message.get("content", "").lower()
                # Simple relevance scoring
                if query_lower in content:
                    score = content.count(query_lower) / len(content.split())
                    message["relevance_score"] = score
                    relevant_messages.append(message)
            
            # Sort by relevance
            relevant_messages.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            # Group by backend
            backend_results = {}
            for message in relevant_messages[:20]:  # Top 20 results
                backend = message.get("metadata", {}).get("backend_used", "unknown")
                if backend not in backend_results:
                    backend_results[backend] = []
                backend_results[backend].append(message)
            
            return {
                "session_id": session_id,
                "query": query,
                "total_results": len(relevant_messages),
                "backend_results": backend_results,
                "searched_backends": backends or ["all"],
                "top_results": relevant_messages[:10]
            }
            
        except Exception as e:
            logger.error(f"Cross-backend search failed: {e}")
            return {
                "session_id": session_id,
                "query": query,
                "total_results": 0,
                "backend_results": {},
                "error": str(e)
            }
    
    async def _check_auto_summarize(self, session_id: str):
        """Check if session needs automatic summarization"""
        try:
            session_stats = await self.get_session_stats(session_id)
            message_count = session_stats.get("message_count", 0)
            
            if message_count > self.auto_summarize_threshold:
                # Check if we already have a recent summary
                if session_id not in self.session_manager.session_summaries:
                    logger.info(f"Auto-summarizing session {session_id} ({message_count} messages)")
                    await self.session_manager.create_session_summary(session_id)
                    
        except Exception as e:
            logger.warning(f"Auto-summarization check failed: {e}")
    
    async def _update_context_cache(self, session_id: str):
        """Update context cache for session"""
        try:
            # Simple cache invalidation
            cache_key = f"context:{session_id}"
            if cache_key in self.context_cache:
                del self.context_cache[cache_key]
                
        except Exception as e:
            logger.warning(f"Context cache update failed: {e}")
    
    async def cleanup_old_sessions(self, days: int = None) -> Dict[str, Any]:
        """Clean up old session data"""
        try:
            cleanup_days = days or self.context_retention_days
            cutoff_time = datetime.now() - timedelta(days=cleanup_days)
            cutoff_timestamp = cutoff_time.timestamp()
            
            # This would typically involve database cleanup
            # For now, just clean local caches
            cleaned_sessions = []
            
            for session_id in list(self.session_manager.session_summaries.keys()):
                summary_data = self.session_manager.session_summaries[session_id]
                created_at = datetime.fromisoformat(summary_data.get("created_at", ""))
                
                if created_at < cutoff_time:
                    del self.session_manager.session_summaries[session_id]
                    cleaned_sessions.append(session_id)
            
            # Clean context cache
            self.context_cache.clear()
            
            return {
                "cleaned_sessions": len(cleaned_sessions),
                "cutoff_date": cutoff_time.isoformat(),
                "retention_days": cleanup_days
            }
            
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
            return {"error": str(e)}
    
    async def health_check_enhanced(self) -> Dict[str, Any]:
        """Enhanced health check with memory management info"""
        try:
            base_health = await self.health_check()
            
            enhanced_info = {
                "context_cache_size": len(self.context_cache),
                "session_summaries": len(self.session_manager.session_summaries),
                "active_sessions": len(self.session_manager.active_sessions),
                "auto_summarize_threshold": self.auto_summarize_threshold,
                "context_window_max_tokens": self.context_window.max_tokens,
                "features": {
                    "cross_backend_search": True,
                    "intelligent_summarization": True,
                    "context_optimization": True,
                    "session_management": True
                }
            }
            
            base_health.update(enhanced_info)
            return base_health
            
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

