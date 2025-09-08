#!/usr/bin/env python3
"""
MCP Memory Server - Provides centralized memory and context for AI agents
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
import qdrant_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_memory")

# Initialize FastAPI app
app = FastAPI(
    title="MCP Memory Server",
    description="Provides contextualized memory for AI agents in Sophia",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis client
redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# Initialize Qdrant client
qdrant_client = qdrant_client.QdrantClient(
    url=os.environ.get("QDRANT_URL", "http://localhost:6333")
)

# Models for API
class MemoryItem(BaseModel):
    key: str
    value: Any
    ttl: Optional[int] = None  # Time to live in seconds, None for permanent storage

class MemoryQuery(BaseModel):
    query: str
    limit: int = 5
    namespace: Optional[str] = None

class VectorEmbedding(BaseModel):
    text: str
    embedding: List[float]
    metadata: Dict[str, Any] = {}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check the health of the MCP Memory Server and its dependencies"""
    status = {
        "status": "operational",
        "version": "1.0.0",
        "redis": False,
        "qdrant": False
    }

    # Check Redis connection
    try:
        redis_client.ping()
        status["redis"] = True
    except Exception as e:
        logger.error(f"Redis connection error: {str(e)}")

    # Check Qdrant connection
    try:
        qdrant_status = qdrant_client.http.health()
        status["qdrant"] = qdrant_status.get("status") == "ok"
    except Exception as e:
        logger.error(f"Qdrant connection error: {str(e)}")

    if status["redis"] and status["qdrant"]:
        return status
    else:
        status["status"] = "degraded"
        return status

# Memory storage endpoints
@app.post("/memory/store")
async def store_memory(item: MemoryItem):
    """Store an item in the memory system"""
    try:
        key = f"sophia:memory:{item.key}"
        if item.ttl:
            redis_client.setex(key, item.ttl, json.dumps(item.value))
        else:
            redis_client.set(key, json.dumps(item.value))
        return {"status": "success", "key": item.key}
    except Exception as e:
        logger.error(f"Error storing memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/{key}")
async def retrieve_memory(key: str):
    """Retrieve an item from memory by key"""
    try:
        value = redis_client.get(f"sophia:memory:{key}")
        if value is None:
            raise HTTPException(status_code=404, detail="Memory item not found")
        return {"key": key, "value": json.loads(value)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memory/{key}")
async def delete_memory(key: str):
    """Delete an item from memory"""
    try:
        result = redis_client.delete(f"sophia:memory:{key}")
        if result == 0:
            raise HTTPException(status_code=404, detail="Memory item not found")
        return {"status": "success", "key": key}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Vector search endpoints (simplified for initial implementation)
COLLECTION_NAME = "agent_memory"

@app.post("/vector/store")
async def store_vector(item: VectorEmbedding):
    """Store a vector embedding in Qdrant"""
    try:
        # Ensure collection exists
        collections = qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]

        if COLLECTION_NAME not in collection_names:
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config={"size": len(item.embedding), "distance": "Cosine"}
            )

        # Store the vector
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                {
                    "id": abs(hash(item.text)) % (10**10),  # Simple hash as ID
                    "vector": item.embedding,
                    "payload": {
                        "text": item.text,
                        **item.metadata
                    }
                }
            ]
        )

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error storing vector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vector/search")
async def search_vector(query: VectorEmbedding):
    """Search for similar vectors in Qdrant"""
    try:
        # Check if collection exists
        collections = qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]

        if COLLECTION_NAME not in collection_names:
            return {"results": []}

        # Search for similar vectors
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query.embedding,
            limit=10
        )

        results = [
            {
                "text": point.payload["text"],
                "metadata": {k: v for k, v in point.payload.items() if k != "text"},
                "score": point.score
            }
            for point in search_results
        ]

        return {"results": results}
    except Exception as e:
        logger.error(f"Error searching vectors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Context management endpoints
@app.post("/context/store")
async def store_context(request: Request):
    """Store context information from an agent"""
    try:
        data = await request.json()
        agent_id = data.get("agent_id", "unknown")
        context_type = data.get("context_type", "general")
        content = data.get("content", {})

        # Store in Redis with a compound key
        key = f"sophia:context:{agent_id}:{context_type}"
        redis_client.set(key, json.dumps(content))

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error storing context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/context/{agent_id}/{context_type}")
async def get_context(agent_id: str, context_type: str):
    """Retrieve context for a specific agent and type"""
    try:
        key = f"sophia:context:{agent_id}:{context_type}"
        value = redis_client.get(key)

        if value is None:
            return {"status": "not_found"}

        return {"status": "success", "content": json.loads(value)}
    except Exception as e:
        logger.error(f"Error retrieving context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# GitHub integration endpoints
@app.get("/github/repo/{owner}/{repo}")
async def get_github_repo(owner: str, repo: str):
    """Get GitHub repository information (placeholder for GitHub MCP)"""
    # In a full implementation, this would connect to GitHub API
    return {
        "status": "success",
        "message": "GitHub MCP integration placeholder - would connect to GitHub API"
    }

# Main entry point
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("server:app", host="${BIND_IP}", port=port, reload=True)
