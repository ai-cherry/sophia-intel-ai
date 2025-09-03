import json
from typing import Optional

import httpx
import redis.asyncio as redis


class UnifiedMemoryAdapter:
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        mcp_url: str = "http://localhost:8001",
        ttl: int = 86400,
        max_context_size: int = 10000
    ):
        self.redis = redis.Redis.from_url(redis_url)
        self.mcp_url = mcp_url
        self.ttl = ttl
        self.max_context_size = max_context_size

    async def store_conversation(
        self,
        session_id: str,
        messages: list[dict],
        metadata: Optional[dict] = None
    ) -> dict:
        try:
            # Validate session_id format
            if not re.match(r"^[a-zA-Z0-9_-]{1,100}$", session_id):
                raise ValueError("Invalid session ID format")

            # Serialize messages
            serialized = json.dumps(messages)

            # Store in Redis
            key = f"memory:session:{session_id}"
            await self.redis.setex(key, self.ttl, serialized)

            # Send to MCP server
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.mcp_url}/memory/store",
                    json={
                        "session_id": session_id,
                        "messages": messages,
                        "metadata": metadata
                    }
                )
                response.raise_for_status()

            return {
                "success": True,
                "memory_id": session_id,
                "storage": "redis+mcp"
            }
        except Exception as e:
            # Fallback to Redis only on MCP failure
            if "MCP server" in str(e):
                await self.redis.setex(key, self.ttl, serialized)
                return {
                    "success": True,
                    "memory_id": session_id,
                    "storage": "redis"
                }
            raise

    async def retrieve_context(
        self,
        session_id: str,
        last_n: int = 10,
        include_system: bool = False
    ) -> dict:
        # Check Redis cache first
        key = f"memory:session:{session_id}"
        cached = await self.redis.get(key)
        if cached:
            messages = json.loads(cached)
            # Filter by last_n
            filtered = messages[-last_n:] if last_n > 0 else messages
            return {
                "messages": filtered,
                "metadata": {},
                "token_count": len(json.dumps(filtered))
            }

        # Fallback to MCP server
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.mcp_url}/memory/retrieve/{session_id}",
                json={"last_n": last_n, "include_system": include_system}
            )
            response.raise_for_status()
            return response.json()
