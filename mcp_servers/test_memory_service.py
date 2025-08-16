"""
Test Memory Service - In-memory implementation for testing
Provides basic memory functionality without external dependencies
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger


class TestMemoryService:
    """
    Test implementation of memory service using in-memory storage
    """

    def __init__(self):
        self.storage = {}  # session_id -> list of contexts
        self.context_counter = 0
        logger.info("Test Memory Service initialized")

    async def store_context(
        self, session_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store context in memory"""
        try:
            self.context_counter += 1
            context_id = f"ctx_{self.context_counter}"

            context_entry = {
                "id": context_id,
                "session_id": session_id,
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat(),
                "created_at": time.time(),
            }

            if session_id not in self.storage:
                self.storage[session_id] = []

            self.storage[session_id].append(context_entry)

            logger.info(f"Stored context {context_id} for session {session_id}")

            return {"id": context_id, "success": True}

        except Exception as e:
            logger.error(f"Failed to store context: {e}")
            raise

    async def query_context(
        self, session_id: str, query: str, top_k: int = 5, global_search: bool = False, threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Query context from memory"""
        try:
            results = []

            # Simple keyword-based search for testing
            query_words = set(query.lower().split())

            sessions_to_search = [session_id]
            if global_search:
                sessions_to_search = list(self.storage.keys())

            for sid in sessions_to_search:
                if sid not in self.storage:
                    continue

                for context in self.storage[sid]:
                    content_words = set(context["content"].lower().split())

                    # Simple similarity based on word overlap
                    overlap = len(query_words.intersection(content_words))
                    total_words = len(query_words.union(content_words))

                    if total_words > 0:
                        similarity = overlap / total_words

                        if similarity >= threshold:
                            result = {
                                "id": context["id"],
                                "content": context["content"],
                                "metadata": context["metadata"],
                                "score": similarity,
                                "session_id": context["session_id"],
                                "timestamp": context["timestamp"],
                            }
                            results.append(result)

            # Sort by score and return top_k
            results.sort(key=lambda x: x["score"], reverse=True)
            results = results[:top_k]

            logger.info(f"Query '{query}' returned {len(results)} results")

            return results

        except Exception as e:
            logger.error(f"Failed to query context: {e}")
            raise

    async def clear_session(self, session_id: str) -> Dict[str, Any]:
        """Clear all context for a session"""
        try:
            deleted_count = 0
            if session_id in self.storage:
                deleted_count = len(self.storage[session_id])
                del self.storage[session_id]

            logger.info(f"Cleared {deleted_count} contexts for session {session_id}")

            return {"deleted_count": deleted_count}

        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            raise

    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        try:
            if session_id not in self.storage:
                return {
                    "session_id": session_id,
                    "context_count": 0,
                    "total_size": 0,
                    "oldest_context": None,
                    "newest_context": None,
                }

            contexts = self.storage[session_id]
            total_size = sum(len(ctx["content"]) for ctx in contexts)

            timestamps = [ctx["created_at"] for ctx in contexts]
            oldest = min(timestamps) if timestamps else None
            newest = max(timestamps) if timestamps else None

            return {
                "session_id": session_id,
                "context_count": len(contexts),
                "total_size": total_size,
                "oldest_context": datetime.fromtimestamp(oldest).isoformat() if oldest else None,
                "newest_context": datetime.fromtimestamp(newest).isoformat() if newest else None,
            }

        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """Get overall memory service statistics"""
        try:
            total_sessions = len(self.storage)
            total_contexts = sum(len(contexts) for contexts in self.storage.values())
            total_size = sum(sum(len(ctx["content"]) for ctx in contexts) for contexts in self.storage.values())

            return {
                "total_sessions": total_sessions,
                "total_contexts": total_contexts,
                "total_size_bytes": total_size,
                "avg_contexts_per_session": total_contexts / total_sessions if total_sessions > 0 else 0,
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Health check for memory service"""
        return {
            "status": "healthy",
            "service": "test-memory-service",
            "storage_sessions": len(self.storage),
            "total_contexts": sum(len(contexts) for contexts in self.storage.values()),
        }
