"""
Simple MCP Memory Server
Provides memory storage and retrieval services for AI agents
"""

import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware

from .models import MemoryRecord, MemoryQuery, MemoryResponse
import redis
from redis.exceptions import ConnectionError as RedisConnectionError

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

# Initialize FastAPI app
app = FastAPI(title="MCP Memory Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis connection
redis_url = os.getenv("REDIS_URL", "${REDIS_URL}")
redis_client = redis.Redis.from_url(redis_url, decode_responses=True)

# Initialize Qdrant if available
if QDRANT_AVAILABLE:
    try:
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_client = QdrantClient(url=qdrant_url)

        # Create collections if they don't exist
        try:
            qdrant_client.create_collection(
                collection_name="memory_vectors",
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
        except Exception:
            # Collection might already exist
            pass
    except Exception:
        QDRANT_AVAILABLE = False

# Models are defined in models.py and imported above

# Routes
@app.get("/health")
async def health_check():
    """Check the health of the MCP memory server"""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0",
        "services": {
            "redis": "connected" if check_redis_connection() else "disconnected",
            "qdrant": "available" if QDRANT_AVAILABLE else "unavailable"
        }
    }
    return health_data

@app.post("/memory/store", response_model=MemoryResponse)
async def store_memory(item: MemoryRecord):
    """Store a memory item in Redis and optionally Qdrant"""
    try:
        # Generate a unique ID for this memory
        memory_id = f"memory:{uuid.uuid4()}"

        # Prepare memory data
        memory_data = {
            "id": memory_id,
            "content": item.content,
            "metadata": json.dumps(item.metadata),
            "agent_id": item.agent_id,
            "timestamp": time.time(),
            "schema_version": item.schema_version,
        }

        if item.session_id:
            memory_data["session_id"] = item.session_id
        if item.project_id:
            memory_data["project_id"] = item.project_id

        # Store in Redis
        redis_client.hset(memory_id, mapping=memory_data)

        # Add to relevant indexes
        redis_client.sadd(f"agent:{item.agent_id}:memories", memory_id)

        if item.session_id:
            redis_client.sadd(f"session:{item.session_id}:memories", memory_id)

        if item.project_id:
            redis_client.sadd(f"project:{item.project_id}:memories", memory_id)

        # Store vector embedding if provided and Qdrant is available
        if QDRANT_AVAILABLE and item.vector_embedding:
            qdrant_client.upsert(
                collection_name="memory_vectors",
                points=[
                    {
                        "id": memory_id,
                        "vector": item.vector_embedding,
                        "payload": {
                            "content": item.content,
                            "agent_id": item.agent_id,
                            "session_id": item.session_id,
                            "project_id": item.project_id,
                            "timestamp": memory_data["timestamp"]
                        }
                    }
                ]
            )

        return MemoryResponse(
            success=True,
            message="Memory stored successfully",
            data={"id": memory_id}
        )
    except Exception as e:
        return MemoryResponse(
            success=False,
            message=f"Failed to store memory: {str(e)}"
        )

@app.post("/memory/retrieve", response_model=MemoryResponse)
async def retrieve_memory(query: MemoryQuery):
    """Retrieve memory items based on query parameters"""
    try:
        # Semantic search using Qdrant if requested
        memories: List[Dict[str, Any]] = []
        if query.semantic_search and QDRANT_AVAILABLE:
            if not query.vector_embedding:
                raise HTTPException(status_code=400, detail="vector_embedding required for semantic search")

            search_results = qdrant_client.search(
                collection_name="memory_vectors",
                query_vector=query.vector_embedding,
                limit=query.limit,
            )

            for res in search_results:
                memory_id = str(res.id)
                memory_data = redis_client.hgetall(memory_id)
                if not memory_data:
                    continue
                try:
                    metadata = json.loads(memory_data.get("metadata", "{}"))
                except json.JSONDecodeError:
                    metadata = {}
                memories.append(
                    {
                        "id": memory_id,
                        "content": memory_data.get("content"),
                        "metadata": metadata,
                        "agent_id": memory_data.get("agent_id"),
                        "session_id": memory_data.get("session_id"),
                        "project_id": memory_data.get("project_id"),
                        "timestamp": float(memory_data.get("timestamp", 0)),
                        "score": res.score,
                    }
                )
        else:
            memory_ids = set()

            # Get memories by agent ID
            if query.agent_id:
                agent_memories = redis_client.smembers(f"agent:{query.agent_id}:memories")
                memory_ids.update(agent_memories)

            # Intersect with session memories if specified
            if query.session_id and memory_ids:
                session_memories = redis_client.smembers(f"session:{query.session_id}:memories")
                memory_ids = memory_ids.intersection(session_memories)
            elif query.session_id:
                memory_ids = redis_client.smembers(f"session:{query.session_id}:memories")

            # Intersect with project memories if specified
            if query.project_id and memory_ids:
                project_memories = redis_client.smembers(f"project:{query.project_id}:memories")
                memory_ids = memory_ids.intersection(project_memories)
            elif query.project_id:
                memory_ids = redis_client.smembers(f"project:{query.project_id}:memories")

            # If no specific filters, get the most recent memories
            if not memory_ids:
                memory_ids = [key for key in redis_client.scan_iter("memory:*")]

            for memory_id in memory_ids:
                memory_data = redis_client.hgetall(memory_id)
                if not memory_data:
                    continue
                try:
                    metadata = json.loads(memory_data.get("metadata", "{}"))
                except json.JSONDecodeError:
                    metadata = {}
                if query.metadata_filter:
                    skip = False
                    for key, value in query.metadata_filter.items():
                        if key not in metadata or metadata[key] != value:
                            skip = True
                            break
                    if skip:
                        continue

                memories.append(
                    {
                        "id": memory_data.get("id"),
                        "content": memory_data.get("content"),
                        "metadata": metadata,
                        "agent_id": memory_data.get("agent_id"),
                        "session_id": memory_data.get("session_id"),
                        "project_id": memory_data.get("project_id"),
                        "timestamp": float(memory_data.get("timestamp", 0)),
                    }
                )

            # Sort by timestamp (most recent first)
            memories.sort(key=lambda x: x["timestamp"], reverse=True)

            # Limit results
            memories = memories[:query.limit]

        return MemoryResponse(
            success=True,
            message=f"Retrieved {len(memories)} memories",
            data=memories
        )
    except Exception as e:
        return MemoryResponse(
            success=False,
            message=f"Failed to retrieve memories: {str(e)}"
        )

@app.delete("/memory/{memory_id}", response_model=MemoryResponse)
async def delete_memory(memory_id: str):
    """Delete a specific memory item"""
    try:
        # Check if memory exists
        if not redis_client.exists(memory_id):
            return MemoryResponse(
                success=False,
                message=f"Memory {memory_id} not found"
            )

        # Get memory data for index removal
        memory_data = redis_client.hgetall(memory_id)

        # Remove from agent index
        if "agent_id" in memory_data:
            redis_client.srem(f"agent:{memory_data['agent_id']}:memories", memory_id)

        # Remove from session index
        if "session_id" in memory_data and memory_data["session_id"]:
            redis_client.srem(f"session:{memory_data['session_id']}:memories", memory_id)

        # Remove from project index
        if "project_id" in memory_data and memory_data["project_id"]:
            redis_client.srem(f"project:{memory_data['project_id']}:memories", memory_id)

        # Delete the memory
        redis_client.delete(memory_id)

        # Remove from Qdrant if available
        if QDRANT_AVAILABLE:
            try:
                qdrant_client.delete(
                    collection_name="memory_vectors",
                    points_selector=[memory_id]
                )
            except Exception:
                # Ignore Qdrant deletion errors
                pass

        return MemoryResponse(
            success=True,
            message=f"Memory {memory_id} deleted successfully"
        )
    except Exception as e:
        return MemoryResponse(
            success=False,
            message=f"Failed to delete memory: {str(e)}"
        )

@app.post("/memory/clear", response_model=MemoryResponse)
async def clear_memories(
    agent_id: Optional[str] = None,
    session_id: Optional[str] = None,
    project_id: Optional[str] = None
):
    """Clear memories based on filters"""
    try:
        memory_ids = set()

        # Get memories to clear based on filters
        if agent_id:
            agent_memories = redis_client.smembers(f"agent:{agent_id}:memories")
            memory_ids.update(agent_memories)

        if session_id:
            session_memories = redis_client.smembers(f"session:{session_id}:memories")
            memory_ids.update(session_memories)

        if project_id:
            project_memories = redis_client.smembers(f"project:{project_id}:memories")
            memory_ids.update(project_memories)

        # If no specific filters, don't delete anything for safety
        if not memory_ids:
            return MemoryResponse(
                success=False,
                message="No filter specified. For safety, specify at least one filter: agent_id, session_id, or project_id."
            )

        # Delete each memory
        for memory_id in memory_ids:
            # Get memory data for index removal
            memory_data = redis_client.hgetall(memory_id)

            # Remove from indexes
            if "agent_id" in memory_data:
                redis_client.srem(f"agent:{memory_data['agent_id']}:memories", memory_id)

            if "session_id" in memory_data and memory_data["session_id"]:
                redis_client.srem(f"session:{memory_data['session_id']}:memories", memory_id)

            if "project_id" in memory_data and memory_data["project_id"]:
                redis_client.srem(f"project:{memory_data['project_id']}:memories", memory_id)

            # Delete the memory
            redis_client.delete(memory_id)

        # Remove from Qdrant if available
        if QDRANT_AVAILABLE and memory_ids:
            try:
                qdrant_client.delete(
                    collection_name="memory_vectors",
                    points_selector=list(memory_ids)
                )
            except Exception:
                # Ignore Qdrant deletion errors
                pass

        return MemoryResponse(
            success=True,
            message=f"Cleared {len(memory_ids)} memories"
        )
    except Exception as e:
        return MemoryResponse(
            success=False,
            message=f"Failed to clear memories: {str(e)}"
        )

def check_redis_connection() -> bool:
    """Check if Redis is available"""
    try:
        return redis_client.ping()
    except RedisConnectionError:
        return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MCP Memory Server")
    parser.add_argument("--host", default="${BIND_IP}", help="Host to listen on")
    parser.add_argument("--port", default=8001, type=int, help="Port to listen on")

    args = parser.parse_args()

    print(f"Starting MCP Memory Server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)
