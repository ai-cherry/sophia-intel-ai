#!/usr/bin/env python3
"""
Base Memory Service for RAG Implementation
Shared by both Sophia and Artemis domains
Zero-conflict architecture with existing MCP services
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis

# Optional Weaviate support
try:
    from weaviate import Client as WeaviateClient
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False
    WeaviateClient = None

class MemoryQuery(BaseModel):
    """Query model for memory service"""
    query: str
    domain: Optional[str] = None
    limit: int = 10
    include_context: bool = True
    filters: Optional[Dict[str, Any]] = None

class MemoryResponse(BaseModel):
    """Response model for memory queries"""
    results: List[Dict[str, Any]]
    domain: str
    timestamp: datetime
    context_used: bool
    total_results: int

class IndexRequest(BaseModel):
    """Request model for indexing documents"""
    content: str
    metadata: Optional[Dict[str, Any]] = {}
    source: Optional[str] = None
    type: Optional[str] = None
    id: Optional[str] = None

class BaseMemoryService(ABC):
    """
    Base class for domain-specific memory services
    Provides common functionality for both Sophia and Artemis
    """
    
    def __init__(self, domain: str, port: int):
        self.domain = domain
        self.port = port
        self.app = FastAPI(
            title=f"{domain.title()} Memory Service",
            description=f"RAG memory service for {domain} domain",
            version="1.0.0"
        )
        
        # Initialize Redis (required)
        try:
            self.redis_client = redis.Redis(
                host='localhost', 
                port=6379, 
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            self.redis_available = True
        except:
            print(f"⚠️  Redis not available, using in-memory cache")
            self.redis_available = False
            self.memory_cache = {}
        
        # Initialize Weaviate (optional)
        self.weaviate_client = None
        if WEAVIATE_AVAILABLE:
            try:
                self.weaviate_client = WeaviateClient("http://localhost:8080")
                self.weaviate_client.is_ready()
                print(f"✅ Weaviate connected for {domain}")
            except:
                print(f"⚠️  Weaviate not available for {domain}, using Redis only")
                self.weaviate_client = None
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            return {
                "service": f"{self.domain.title()} Memory Service",
                "status": "running",
                "redis": self.redis_available,
                "weaviate": self.weaviate_client is not None
            }
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "domain": self.domain,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/query", response_model=MemoryResponse)
        async def query_memory(request: MemoryQuery):
            """Query memory with optional context enrichment"""
            try:
                results = await self.search(
                    request.query, 
                    request.limit,
                    request.filters
                )
                
                if request.include_context:
                    results = await self.enrich_with_context(results)
                
                return MemoryResponse(
                    results=results[:request.limit],
                    domain=self.domain,
                    timestamp=datetime.now(),
                    context_used=request.include_context,
                    total_results=len(results)
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/index")
        async def index_document(request: IndexRequest):
            """Index a document into memory"""
            try:
                document = {
                    "content": request.content,
                    "metadata": request.metadata,
                    "source": request.source,
                    "type": request.type,
                    "domain": self.domain,
                    "timestamp": datetime.now().isoformat()
                }
                
                if request.id:
                    document["id"] = request.id
                
                success = await self.index(document)
                
                return {
                    "success": success,
                    "domain": self.domain,
                    "document_id": document.get("id", "auto-generated")
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/clear")
        async def clear_memory():
            """Clear all memory (use with caution)"""
            try:
                if self.redis_available:
                    pattern = f"{self.domain}:*"
                    for key in self.redis_client.scan_iter(match=pattern):
                        self.redis_client.delete(key)
                else:
                    self.memory_cache.clear()
                
                return {"success": True, "message": f"Cleared {self.domain} memory"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/stats")
        async def get_stats():
            """Get memory statistics"""
            try:
                if self.redis_available:
                    pattern = f"{self.domain}:*"
                    total_keys = len(list(self.redis_client.scan_iter(match=pattern, count=1000)))
                    memory_info = self.redis_client.memory_stats()
                    
                    return {
                        "domain": self.domain,
                        "total_documents": total_keys,
                        "memory_used_mb": round(memory_info.get("total.allocated", 0) / 1024 / 1024, 2),
                        "backend": "redis+weaviate" if self.weaviate_client else "redis"
                    }
                else:
                    return {
                        "domain": self.domain,
                        "total_documents": len(self.memory_cache),
                        "backend": "in-memory"
                    }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        # Limit key length and make it safe
        safe_query = query[:100].replace(" ", "_").lower()
        return f"{self.domain}:cache:{safe_query}"
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache (Redis or memory)"""
        if self.redis_available:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        else:
            return self.memory_cache.get(key)
    
    def _set_cache(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        if self.redis_available:
            self.redis_client.setex(key, ttl, json.dumps(value))
        else:
            self.memory_cache[key] = value
    
    @abstractmethod
    async def search(self, query: str, limit: int, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Domain-specific search implementation"""
        pass
    
    @abstractmethod
    async def index(self, document: Dict[str, Any]) -> bool:
        """Domain-specific indexing implementation"""
        pass
    
    @abstractmethod
    async def enrich_with_context(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add domain-specific context to results"""
        pass
    
    def run(self):
        """Start the memory service"""
        import uvicorn
        print(f"🚀 Starting {self.domain.title()} Memory Service on port {self.port}")
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)