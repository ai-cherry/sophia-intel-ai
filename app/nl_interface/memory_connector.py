"""
NL Memory Connector - Integration with MCP Memory System
Stores and retrieves all NL interactions for persistent context
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Optional

import aiohttp

from app.core.ai_logger import logger

logger = logging.getLogger(__name__)


@dataclass
class NLInteraction:
    """Represents a single NL interaction"""

    session_id: str
    timestamp: str
    user_input: str
    intent: str
    entities: dict[str, Any]
    confidence: float
    response: str
    workflow_id: Optional[str] = None
    execution_result: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None


class NLMemoryConnector:
    """
    Connector for NL Interface to MCP Memory System
    Provides persistent storage and retrieval of NL interactions
    """

    def __init__(
        self,
        mcp_server_url: str = "http://localhost:8004",
        collection_name: str = "nl_interactions",
        max_history_size: int = 1000,
    ):
        """
        Initialize NL Memory Connector

        Args:
            mcp_server_url: URL of the MCP memory server
            collection_name: Name of the collection for NL interactions
            max_history_size: Maximum number of interactions to keep in memory
        """
        self.mcp_server_url = mcp_server_url
        self.collection_name = collection_name
        self.max_history_size = max_history_size
        self.session = None
        self._memory_cache = {}

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

    async def connect(self):
        """Establish connection to MCP server"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            # Test connection
            async with self.session.get(f"{self.mcp_server_url}/health") as response:
                if response.status == 200:
                    logger.info(f"Connected to MCP server at {self.mcp_server_url}")
                else:
                    logger.warning(f"MCP server returned status {response.status}")

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            # Continue without MCP if unavailable

    async def disconnect(self):
        """Close connection to MCP server"""
        if self.session:
            await self.session.close()
            self.session = None

    async def store_interaction(self, interaction: NLInteraction) -> bool:
        """
        Store an NL interaction in memory

        Args:
            interaction: The NL interaction to store

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Store in local cache
            if interaction.session_id not in self._memory_cache:
                self._memory_cache[interaction.session_id] = []

            self._memory_cache[interaction.session_id].append(asdict(interaction))

            # Trim cache if too large
            if len(self._memory_cache[interaction.session_id]) > self.max_history_size:
                self._memory_cache[interaction.session_id] = self._memory_cache[
                    interaction.session_id
                ][-self.max_history_size :]

            # Store in MCP if available
            if self.session:
                data = {
                    "collection": self.collection_name,
                    "document": {
                        "id": f"{interaction.session_id}_{interaction.timestamp}",
                        "session_id": interaction.session_id,
                        "timestamp": interaction.timestamp,
                        "user_input": interaction.user_input,
                        "intent": interaction.intent,
                        "entities": interaction.entities,
                        "confidence": interaction.confidence,
                        "response": interaction.response,
                        "workflow_id": interaction.workflow_id,
                        "execution_result": interaction.execution_result,
                        "metadata": interaction.metadata,
                    },
                }

                async with self.session.post(
                    f"{self.mcp_server_url}/memory/store", json=data
                ) as response:
                    if response.status == 200:
                        logger.debug(f"Stored interaction for session {interaction.session_id}")
                        return True
                    else:
                        logger.warning(f"Failed to store in MCP: {response.status}")

            return True  # Still return True if stored in cache

        except Exception as e:
            logger.error(f"Error storing interaction: {e}")
            return False

    async def retrieve_session_history(
        self, session_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Retrieve conversation history for a session

        Args:
            session_id: The session ID to retrieve history for
            limit: Maximum number of interactions to retrieve

        Returns:
            List of interactions for the session
        """
        try:
            # First check local cache
            if session_id in self._memory_cache:
                cached = self._memory_cache[session_id]
                return cached[-limit:] if limit else cached

            # Try to retrieve from MCP
            if self.session:
                params = {
                    "collection": self.collection_name,
                    "filter": json.dumps({"session_id": session_id}),
                    "limit": limit,
                }

                async with self.session.get(
                    f"{self.mcp_server_url}/memory/query", params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        interactions = data.get("documents", [])

                        # Update cache
                        self._memory_cache[session_id] = interactions

                        return interactions
                    else:
                        logger.warning(f"Failed to retrieve from MCP: {response.status}")

            return []

        except Exception as e:
            logger.error(f"Error retrieving session history: {e}")
            return []

    async def retrieve_by_intent(self, intent: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Retrieve interactions by intent type

        Args:
            intent: The intent to filter by
            limit: Maximum number of interactions to retrieve

        Returns:
            List of interactions with the specified intent
        """
        try:
            # Search in cache first
            results = []
            for session_interactions in self._memory_cache.values():
                for interaction in session_interactions:
                    if interaction.get("intent") == intent:
                        results.append(interaction)
                        if len(results) >= limit:
                            return results

            # Try MCP if available
            if self.session:
                params = {
                    "collection": self.collection_name,
                    "filter": json.dumps({"intent": intent}),
                    "limit": limit,
                }

                async with self.session.get(
                    f"{self.mcp_server_url}/memory/query", params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("documents", [])

            return results

        except Exception as e:
            logger.error(f"Error retrieving by intent: {e}")
            return []

    async def search_interactions(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Search interactions using semantic search

        Args:
            query: The search query
            limit: Maximum number of results

        Returns:
            List of matching interactions
        """
        try:
            # Simple text search in cache
            results = []
            query_lower = query.lower()

            for session_interactions in self._memory_cache.values():
                for interaction in session_interactions:
                    if (
                        query_lower in interaction.get("user_input", "").lower()
                        or query_lower in interaction.get("response", "").lower()
                    ):
                        results.append(interaction)
                        if len(results) >= limit:
                            return results

            # Try semantic search via MCP
            if self.session:
                data = {"collection": self.collection_name, "query": query, "limit": limit}

                async with self.session.post(
                    f"{self.mcp_server_url}/memory/search", json=data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("documents", [])

            return results

        except Exception as e:
            logger.error(f"Error searching interactions: {e}")
            return []

    async def get_context_summary(
        self, session_id: str, max_interactions: int = 5
    ) -> dict[str, Any]:
        """
        Get a summary of recent context for a session

        Args:
            session_id: The session ID
            max_interactions: Maximum number of recent interactions to consider

        Returns:
            Context summary including intents, entities, and key topics
        """
        try:
            history = await self.retrieve_session_history(session_id, max_interactions)

            if not history:
                return {
                    "session_id": session_id,
                    "interaction_count": 0,
                    "recent_intents": [],
                    "entities": {},
                    "summary": "No previous interactions",
                }

            # Extract summary information
            recent_intents = []
            all_entities = {}

            for interaction in history:
                intent = interaction.get("intent")
                if intent and intent not in recent_intents:
                    recent_intents.append(intent)

                entities = interaction.get("entities", {})
                for key, value in entities.items():
                    if key not in all_entities:
                        all_entities[key] = []
                    if value not in all_entities[key]:
                        all_entities[key].append(value)

            # Generate summary text
            summary_parts = []
            if recent_intents:
                summary_parts.append(f"Recent actions: {', '.join(recent_intents)}")
            if all_entities:
                entity_str = ", ".join([f"{k}: {v[0]}" for k, v in all_entities.items()])
                summary_parts.append(f"Context: {entity_str}")

            return {
                "session_id": session_id,
                "interaction_count": len(history),
                "recent_intents": recent_intents,
                "entities": all_entities,
                "summary": (
                    ". ".join(summary_parts) if summary_parts else "Recent conversation context"
                ),
            }

        except Exception as e:
            logger.error(f"Error getting context summary: {e}")
            return {
                "session_id": session_id,
                "interaction_count": 0,
                "recent_intents": [],
                "entities": {},
                "summary": "Error retrieving context",
            }

    async def clear_session(self, session_id: str) -> bool:
        """
        Clear all interactions for a session

        Args:
            session_id: The session ID to clear

        Returns:
            True if cleared successfully
        """
        try:
            # Clear from cache
            if session_id in self._memory_cache:
                del self._memory_cache[session_id]

            # Clear from MCP if available
            if self.session:
                data = {"collection": self.collection_name, "filter": {"session_id": session_id}}

                async with self.session.delete(
                    f"{self.mcp_server_url}/memory/delete", json=data
                ) as response:
                    if response.status == 200:
                        logger.info(f"Cleared session {session_id} from memory")
                        return True
                    else:
                        logger.warning(f"Failed to clear from MCP: {response.status}")

            return True

        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            return False

    async def export_session(self, session_id: str, format: str = "json") -> Optional[str]:
        """
        Export session history in specified format

        Args:
            session_id: The session ID to export
            format: Export format (json, csv, txt)

        Returns:
            Exported data as string
        """
        try:
            history = await self.retrieve_session_history(session_id, limit=None)

            if format == "json":
                return json.dumps(history, indent=2)

            elif format == "csv":
                import csv
                import io

                output = io.StringIO()
                if history:
                    writer = csv.DictWriter(
                        output,
                        fieldnames=["timestamp", "user_input", "intent", "confidence", "response"],
                    )
                    writer.writeheader()

                    for interaction in history:
                        writer.writerow(
                            {
                                "timestamp": interaction.get("timestamp", ""),
                                "user_input": interaction.get("user_input", ""),
                                "intent": interaction.get("intent", ""),
                                "confidence": interaction.get("confidence", 0),
                                "response": interaction.get("response", ""),
                            }
                        )

                return output.getvalue()

            elif format == "txt":
                lines = []
                for interaction in history:
                    lines.append(f"[{interaction.get('timestamp', '')}]")
                    lines.append(f"User: {interaction.get('user_input', '')}")
                    lines.append(
                        f"Intent: {interaction.get('intent', '')} (confidence: {interaction.get('confidence', 0):.2f})"
                    )
                    lines.append(f"Response: {interaction.get('response', '')}")
                    lines.append("")

                return "\n".join(lines)

            else:
                logger.warning(f"Unsupported export format: {format}")
                return None

        except Exception as e:
            logger.error(f"Error exporting session: {e}")
            return None

    def get_statistics(self) -> dict[str, Any]:
        """
        Get memory statistics

        Returns:
            Statistics about stored interactions
        """
        total_interactions = sum(len(sessions) for sessions in self._memory_cache.values())
        session_count = len(self._memory_cache)

        intent_counts = {}
        for sessions in self._memory_cache.values():
            for interaction in sessions:
                intent = interaction.get("intent")
                if intent:
                    intent_counts[intent] = intent_counts.get(intent, 0) + 1

        return {
            "total_interactions": total_interactions,
            "active_sessions": session_count,
            "intent_distribution": intent_counts,
            "cache_size": total_interactions,
            "max_history_size": self.max_history_size,
        }


# Example usage
async def example_usage():
    """Example of using the NL Memory Connector"""

    async with NLMemoryConnector() as memory:
        # Store an interaction
        interaction = NLInteraction(
            session_id="test-session-123",
            timestamp=datetime.now().isoformat(),
            user_input="show system status",
            intent="system_status",
            entities={},
            confidence=0.95,
            response="System is running normally",
            workflow_id="system-status-workflow",
        )

        await memory.store_interaction(interaction)

        # Retrieve session history
        history = await memory.retrieve_session_history("test-session-123")
        logger.info(f"Session history: {history}")

        # Get context summary
        summary = await memory.get_context_summary("test-session-123")
        logger.info(f"Context summary: {summary}")

        # Search interactions
        results = await memory.search_interactions("system")
        logger.info(f"Search results: {results}")

        # Export session
        export_data = await memory.export_session("test-session-123", format="txt")
        logger.info(f"Exported data:\n{export_data}")


if __name__ == "__main__":
    asyncio.run(example_usage())
