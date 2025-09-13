#!/usr/bin/env python3
"""
Base Memory Service for RAG Implementation
Shared by both Sophia and  domains
Zero-conflict architecture with existing MCP services
"""
import json
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import redis
from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, validator
from redis.exceptions import ConnectionError, RedisError, TimeoutError
# Optional Weaviate support
try:
    from weaviate import Client as WeaviateClient
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False
    WeaviateClient = None
class MemoryQuery(BaseModel):
    """Query model for memory service"""
    query: str = Field(..., min_length=1, max_length=1000)
    domain: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    include_context: bool = True
    filters: Optional[Dict[str, Any]] = None
    @validator("query")
    def sanitize_query(cls, v):
        """Sanitize query input"""
        # Remove potential injection attempts
        dangerous_chars = ["<", ">", '"', "'", "\\", "\0", "\n", "\r", "\t"]
        for char in dangerous_chars:
            v = v.replace(char, "")
        return v.strip()
class MemoryResponse(BaseModel):
    """Response model for memory queries"""
    results: List[Dict[str, Any]]
    domain: str
    timestamp: datetime
    context_used: bool
    total_results: int
class IndexRequest(BaseModel):
    """Request model for indexing documents"""
    content: str = Field(..., min_length=1, max_length=100000)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    source: Optional[str] = Field(None, max_length=100)
    type: Optional[str] = Field(None, max_length=50)
    id: Optional[str] = Field(None, max_length=100)
    @validator("content")
    def validate_content_size(cls, v):
        """Validate content size"""
        if len(v.encode("utf-8")) > 100000:  # 100KB limit
            raise ValueError("Content too large (max 100KB)")
        return v
class BaseMemoryService(ABC):
    """
    Base class for domain-specific memory services
    Provides common functionality for both Sophia and 
    """
    def __init__(self, domain: str, port: int):
        self.domain = domain
        self.port = port
        # Setup logging
        self.logger = logging.getLogger(f"{domain}_memory")
        self.logger.setLevel(os.getenv("MEMORY_LOG_LEVEL", "INFO"))
        # Load configuration
        from app.memory.config import get_config
        self.config = get_config()
        self.app = FastAPI(
            title=f"{domain.title()} Memory Service",
            description=f"RAG memory service for {domain} domain",
            version="1.0.0",
        )
        # Security setup (optional)
        self.security = (
            HTTPBearer(auto_error=False) if self.config.enable_auth else None
        )
        # Simple Redis-backed rate limiter (optional)
        async def rate_limit_dep(request=None):
            if not self.config.rate_limit_enabled or not self.redis_available:
                return None
            try:
                # Derive a basic client key (IP-less fallback)
                client_id = "anon"
                # Increment counter with TTL window
                key = f"rl:{self.domain}:{client_id}:{self.config.rate_limit_period}"
                count = self.redis_client.incr(key)
                if count == 1:
                    self.redis_client.expire(key, self.config.rate_limit_period)
                if count > self.config.rate_limit_requests:
                    # Compute remaining seconds in the window for Retry-After header
                    try:
                        ttl = self.redis_client.ttl(key)
                        retry_after = (
                            max(int(ttl), 1)
                            if ttl and ttl > 0
                            else self.config.rate_limit_period
                        )
                    except Exception:
                        retry_after = self.config.rate_limit_period
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded",
                        headers={"Retry-After": str(retry_after)},
                    )
            except Exception:
                # Fail-open on limiter errors
                return None
            return None
        self._rate_limit_dep = rate_limit_dep
        # Initialize storage backends with proper fallback
        self._init_redis()
        self._init_weaviate()
        self._init_fallback_storage()
        # Compute version metadata
        try:
            self._version = self._compute_version()
        except Exception:
            self._version = "unknown"
        self._setup_routes()
        self._setup_error_handlers()
        self._setup_openapi_security()
    def _init_redis(self):
        """Initialize Redis with proper error handling"""
        self.redis_client = None
        self.redis_available = False
        if not self.config.enable_redis:
            self.logger.info("Redis disabled by configuration")
            return
        try:
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=True,
                socket_connect_timeout=self.config.redis_timeout,
                retry_on_timeout=True,
                retry_on_error=[ConnectionError, TimeoutError],
            )
            # Test connection
            self.redis_client.ping()
            self.redis_available = True
            self.logger.info(f"✅ Redis connected for {self.domain}")
        except (ConnectionError, TimeoutError, RedisError) as e:
            self.logger.warning(f"⚠️  Redis not available for {self.domain}: {e}")
            self.redis_client = None
            self.redis_available = False
    def _init_weaviate(self):
        """Initialize Weaviate with proper error handling"""
        self.weaviate_client = None
        if not self.config.enable_weaviate or not WEAVIATE_AVAILABLE:
            self.logger.info("Weaviate disabled or not available")
            return
        try:
            self.weaviate_client = WeaviateClient(
                url=self.config.weaviate_url,
                auth_client_secret=self.config.weaviate_api_key,
                timeout=(self.config.weaviate_timeout, self.config.weaviate_timeout),
            )
            if self.weaviate_client.is_ready():
                self.logger.info(f"✅ Weaviate connected for {self.domain}")
                # Ensure class schema exists
                try:
                    schema = self.weaviate_client.schema.get()
                    class_names = {c.get("class") for c in schema.get("classes", [])}
                    need_class = getattr(self, "collection_name", None)
                    if need_class and need_class not in class_names:
                        class_obj = {
                            "class": need_class,
                            "vectorizer": "text2vec-openai",
                            "properties": [
                                {"name": "content", "dataType": ["text"]},
                                {"name": "metadata", "dataType": ["text"]},
                                {"name": "source", "dataType": ["text"]},
                                {"name": "type", "dataType": ["text"]},
                                {"name": "timestamp", "dataType": ["date"]},
                                {"name": "code", "dataType": ["text"]},
                                {"name": "filepath", "dataType": ["text"]},
                                {"name": "language", "dataType": ["text"]},
                                {"name": "description", "dataType": ["text"]},
                            ],
                        }
                        self.weaviate_client.schema.create_class(class_obj)
                        self.logger.info(f"🧱 Created Weaviate class: {need_class}")
                except Exception as se:
                    self.logger.warning(f"Weaviate schema check/create failed: {se}")
            else:
                raise Exception("Weaviate not ready")
        except Exception as e:
            self.logger.warning(f"⚠️  Weaviate not available for {self.domain}: {e}")
            self.weaviate_client = None
    def _init_fallback_storage(self):
        """Initialize fallback storage mechanisms"""
        # In-memory cache (always available)
        self.memory_cache = {}
        self.memory_cache_size = 0
        # File-based persistence (optional)
        if self.config.enable_persistence:
            self.persistence_dir = Path(f"/tmp/{self.domain}_memory")
            self.persistence_dir.mkdir(parents=True, exist_ok=True)
            (self.persistence_dir / "docs").mkdir(parents=True, exist_ok=True)
            self.logger.info(f"📁 Persistence enabled at {self.persistence_dir}")
        else:
            self.persistence_dir = None
    def _validate_auth(self, credentials: HTTPAuthorizationCredentials = None) -> bool:
        """Validate authentication if enabled"""
        if not self.config.enable_auth:
            return True
        if not credentials or not credentials.credentials:
            return False
        return credentials.credentials == self.config.api_key
    def _get_auth_dependency(self):
        """Get authentication dependency for routes"""
        if self.config.enable_auth:
            async def verify_auth(
                credentials: HTTPAuthorizationCredentials = Security(self.security),
            ):
                if not self._validate_auth(credentials):
                    # Ensure clients see a WWW-Authenticate challenge per RFC 6750
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid authentication",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                return credentials
            return verify_auth
        else:
            async def no_auth():
                return None
            return no_auth
    def _setup_routes(self):
        """Setup FastAPI routes with optional authentication"""
        # Create auth dependency
        auth_dep = self._get_auth_dependency()
        @self.app.get("/")
        async def root():
            return {
                "service": f"{self.domain.title()} Memory Service",
                "status": "running",
                "redis": self.redis_available,
                "weaviate": self.weaviate_client is not None,
                "auth_required": self.config.enable_auth,
            }
        @self.app.get("/health")
        async def health():
            """Health check endpoint"""
            # Build health status
            health_status = "healthy"
            warnings = []
            if not self.redis_available and not self.weaviate_client:
                health_status = "degraded"
                warnings.append("No vector storage available")
            return {
                "status": health_status,
                "domain": self.domain,
                "timestamp": datetime.now().isoformat(),
                "backends": {
                    "redis": self.redis_available,
                    "weaviate": self.weaviate_client is not None,
                    "memory": True,
                    "persistence": self.persistence_dir is not None,
                },
                "warnings": warnings,
            }
        @self.app.get("/ready")
        async def ready():
            return {"status": "ready", "domain": self.domain}
        @self.app.get("/live")
        async def live():
            return {"status": "alive", "domain": self.domain}
        @self.app.get("/version")
        async def version():
            return {
                "version": getattr(self, "_version", "unknown"),
                "service": f"{self.domain}-memory",
            }
        @self.app.post(
            "/query",
            response_model=MemoryResponse,
            dependencies=[Depends(auth_dep), Depends(self._rate_limit_dep)],
        )
        async def query_memory(request: MemoryQuery):
            """Query memory with optional context enrichment"""
            try:
                # Validate request limits
                if request.limit > self.config.max_search_limit:
                    request.limit = self.config.max_search_limit
                results = await self.search(
                    request.query, request.limit, request.filters
                )
                if request.include_context:
                    results = await self.enrich_with_context(results)
                return MemoryResponse(
                    results=results[: request.limit],
                    domain=self.domain,
                    timestamp=datetime.now(),
                    context_used=request.include_context,
                    total_results=len(results),
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error(f"Query error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        @self.app.post(
            "/index", dependencies=[Depends(auth_dep), Depends(self._rate_limit_dep)]
        )
        async def index_document(request: IndexRequest):
            """Index a document into memory"""
            try:
                # Validate content size
                if len(request.content.encode("utf-8")) > self.config.max_entry_size:
                    raise HTTPException(status_code=413, detail="Content too large")
                document = {
                    "content": request.content,
                    "metadata": request.metadata,
                    "source": request.source,
                    "type": request.type,
                    "domain": self.domain,
                    "timestamp": datetime.now().isoformat(),
                }
                if request.id:
                    document["id"] = request.id
                success = await self.index(document)
                return {
                    "success": success,
                    "domain": self.domain,
                    "document_id": document.get("id", "auto-generated"),
                }
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error(f"Index error: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
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
                    total_keys = len(
                        list(self.redis_client.scan_iter(match=pattern, count=1000))
                    )
                    memory_info = self.redis_client.memory_stats()
                    return {
                        "domain": self.domain,
                        "total_documents": total_keys,
                        "memory_used_mb": round(
                            memory_info.get("total.allocated", 0) / 1024 / 1024, 2
                        ),
                        "backend": (
                            "redis+weaviate" if self.weaviate_client else "redis"
                        ),
                    }
                else:
                    return {
                        "domain": self.domain,
                        "total_documents": len(self.memory_cache),
                        "backend": "in-memory",
                    }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        # Limit key length and make it safe
        safe_query = query[:100].replace(" ", "_").lower()
        return f"{self.domain}:cache:{safe_query}"
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback chain"""
        # Try Redis first
        if self.redis_available and self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value) if isinstance(value, str) else value
            except (ConnectionError, TimeoutError, RedisError) as e:
                self.logger.warning(f"Redis read failed, falling back: {e}")
        # Fallback to memory cache
        value = self.memory_cache.get(key)
        if value:
            return value
        # Fallback to file persistence
        if self.persistence_dir:
            try:
                file_path = self.persistence_dir / f"{key}.json"
                if file_path.exists():
                    with open(file_path) as f:
                        return json.load(f)
            except Exception as e:
                self.logger.warning(f"File read failed: {e}")
        return None
    def _set_cache(self, key: str, value: Any, ttl: int = None):
        """Set value in cache with fallback chain"""
        if ttl is None:
            ttl = self.config.cache_ttl
        success = False
        # Try Redis first
        if self.redis_available and self.redis_client:
            try:
                self.redis_client.setex(key, ttl, json.dumps(value))
                success = True
            except (ConnectionError, TimeoutError, RedisError) as e:
                self.logger.warning(f"Redis write failed, using fallback: {e}")
        # Always update memory cache
        self.memory_cache[key] = value
        # Enforce memory limits
        if len(self.memory_cache) > self.config.max_memory_entries:
            # Remove oldest entries (simple FIFO)
            oldest_keys = list(self.memory_cache.keys())[:100]
            for old_key in oldest_keys:
                del self.memory_cache[old_key]
        # Persist to file if enabled
        if self.persistence_dir:
            try:
                file_path = self.persistence_dir / f"{key}.json"
                with open(file_path, "w") as f:
                    json.dump(value, f)
            except Exception as e:
                self.logger.warning(f"File write failed: {e}")
        return success
    def _compute_version(self) -> str:
        try:
            out = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
            )
            return out.decode().strip()
        except Exception:
            return "unknown"
    def _setup_error_handlers(self):
        """Standardized JSON error envelope and header propagation."""
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            # Build standardized error envelope
            err_type = (
                "rate_limit"
                if exc.status_code == 429
                else (
                    "auth"
                    if exc.status_code in (401, 403)
                    else "validation" if exc.status_code in (400, 404) else "server"
                )
            )
            payload = {
                "error": {
                    "code": exc.status_code,
                    "type": err_type,
                    "message": (
                        exc.detail if isinstance(exc.detail, str) else str(exc.detail)
                    ),
                }
            }
            headers = getattr(exc, "headers", None) or {}
            return JSONResponse(
                status_code=exc.status_code, content=payload, headers=headers
            )
        @self.app.exception_handler(Exception)
        async def unhandled_exception_handler(request: Request, exc: Exception):
            payload = {
                "error": {
                    "code": 500,
                    "type": "server",
                    "message": "Internal server error",
                }
            }
            return JSONResponse(status_code=500, content=payload)
    def _setup_openapi_security(self):
        """Attach Bearer security scheme to OpenAPI when auth is enabled."""
        if not getattr(self.config, "enable_auth", False):
            return
        def custom_openapi():
            if self.app.openapi_schema:
                return self.app.openapi_schema
            openapi_schema = get_openapi(
                title=self.app.title,
                version=self.app.version,
                description=self.app.description,
                routes=self.app.routes,
            )
            security_scheme = {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Use Authorization: Bearer <token>",
                }
            }
            components = openapi_schema.setdefault("components", {})
            components.setdefault("securitySchemes", {}).update(security_scheme)
            # Apply default security requirement across endpoints
            openapi_schema["security"] = [{"BearerAuth": []}]
            self.app.openapi_schema = openapi_schema
            return self.app.openapi_schema
        self.app.openapi = custom_openapi
    @abstractmethod
    async def search(
        self, query: str, limit: int, filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Domain-specific search implementation"""
        pass
    @abstractmethod
    async def index(self, document: Dict[str, Any]) -> bool:
        """Domain-specific indexing implementation"""
        pass
    @abstractmethod
    async def enrich_with_context(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Add domain-specific context to results"""
        pass
    def run(self):
        """Start the memory service"""
        import uvicorn
        print(f"🚀 Starting {self.domain.title()} Memory Service on port {self.port}")
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)
