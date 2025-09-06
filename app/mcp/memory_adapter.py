"""
Memory Adapter for MCP Integration
Provides unified memory storage and retrieval capabilities
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class UnifiedMemoryAdapter:
    """
    Unified Memory Adapter for managing conversation and context memory
    """

    def __init__(self):
        """Initialize the memory adapter"""
        self.memory_store: Dict[str, List[Dict[str, Any]]] = {}
        self.metadata_store: Dict[str, Dict[str, Any]] = {}
        self.context_cache: Dict[str, Any] = {}
        logger.info("UnifiedMemoryAdapter initialized")

    async def store_conversation(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Store conversation messages with optional metadata

        Args:
            session_id: Unique identifier for the conversation session
            messages: List of message dictionaries
            metadata: Optional metadata for the conversation

        Returns:
            Dictionary with storage status and details
        """
        try:
            if session_id not in self.memory_store:
                self.memory_store[session_id] = []

            # Add timestamp to each message if not present
            for message in messages:
                if "timestamp" not in message:
                    message["timestamp"] = datetime.now().isoformat()

            # Store messages
            self.memory_store[session_id].extend(messages)

            # Store metadata if provided
            if metadata:
                if session_id not in self.metadata_store:
                    self.metadata_store[session_id] = {}
                self.metadata_store[session_id].update(metadata)

            return {
                "success": True,
                "session_id": session_id,
                "messages_stored": len(messages),
                "total_messages": len(self.memory_store[session_id]),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
            return {"success": False, "error": str(e), "session_id": session_id}

    async def retrieve_context(
        self, session_id: str, last_n: int = 10, include_system: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieve conversation context for a session

        Args:
            session_id: Unique identifier for the conversation session
            last_n: Number of recent messages to retrieve
            include_system: Whether to include system messages

        Returns:
            Dictionary with retrieved messages and metadata
        """
        try:
            if session_id not in self.memory_store:
                return {
                    "success": True,
                    "session_id": session_id,
                    "messages": [],
                    "metadata": {},
                    "message": "No messages found for this session",
                }

            messages = self.memory_store[session_id]

            # Filter out system messages if requested
            if not include_system:
                messages = [m for m in messages if m.get("role") != "system"]

            # Get last N messages
            recent_messages = messages[-last_n:] if last_n > 0 else messages

            # Get metadata
            metadata = self.metadata_store.get(session_id, {})

            return {
                "success": True,
                "session_id": session_id,
                "messages": recent_messages,
                "metadata": metadata,
                "total_messages": len(messages),
                "retrieved_count": len(recent_messages),
            }

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return {"success": False, "error": str(e), "session_id": session_id}

    async def search_memories(
        self, query: str, session_id: Optional[str] = None, limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search through stored memories

        Args:
            query: Search query string
            session_id: Optional session ID to limit search
            limit: Maximum number of results to return

        Returns:
            Dictionary with search results
        """
        try:
            results = []
            sessions_to_search = [session_id] if session_id else self.memory_store.keys()

            for sid in sessions_to_search:
                if sid in self.memory_store:
                    for message in self.memory_store[sid]:
                        content = message.get("content", "")
                        if query.lower() in content.lower():
                            results.append(
                                {
                                    "session_id": sid,
                                    "message": message,
                                    "metadata": self.metadata_store.get(sid, {}),
                                }
                            )
                            if len(results) >= limit:
                                break

            return {
                "success": True,
                "query": query,
                "results": results[:limit],
                "total_found": len(results),
            }

        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return {"success": False, "error": str(e), "query": query}

    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        Delete all memories for a session

        Args:
            session_id: Session ID to delete

        Returns:
            Dictionary with deletion status
        """
        try:
            messages_deleted = 0

            if session_id in self.memory_store:
                messages_deleted = len(self.memory_store[session_id])
                del self.memory_store[session_id]

            if session_id in self.metadata_store:
                del self.metadata_store[session_id]

            if session_id in self.context_cache:
                del self.context_cache[session_id]

            return {
                "success": True,
                "session_id": session_id,
                "messages_deleted": messages_deleted,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return {"success": False, "error": str(e), "session_id": session_id}

    async def export_session(self, session_id: str) -> Dict[str, Any]:
        """
        Export session data as JSON

        Args:
            session_id: Session ID to export

        Returns:
            Dictionary with exported data
        """
        try:
            if session_id not in self.memory_store:
                return {"success": False, "error": "Session not found", "session_id": session_id}

            export_data = {
                "session_id": session_id,
                "messages": self.memory_store[session_id],
                "metadata": self.metadata_store.get(session_id, {}),
                "export_timestamp": datetime.now().isoformat(),
            }

            return {"success": True, "session_id": session_id, "data": export_data}

        except Exception as e:
            logger.error(f"Error exporting session: {e}")
            return {"success": False, "error": str(e), "session_id": session_id}

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get memory adapter statistics

        Returns:
            Dictionary with statistics
        """
        try:
            total_messages = sum(len(messages) for messages in self.memory_store.values())

            return {
                "success": True,
                "statistics": {
                    "total_sessions": len(self.memory_store),
                    "total_messages": total_messages,
                    "average_messages_per_session": total_messages / max(len(self.memory_store), 1),
                    "sessions_with_metadata": len(self.metadata_store),
                    "cached_contexts": len(self.context_cache),
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"success": False, "error": str(e)}


# Export the adapter
__all__ = ["UnifiedMemoryAdapter"]
