"""
API Dependencies
Provides dependency injection for FastAPI endpoints using REAL services.
NO MOCKS - Production ready implementations only.
"""

from typing import Any, Optional
from fastapi import Depends, HTTPException
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

logger = logging.getLogger(__name__)

class GlobalState:
    """Real global state for dependency injection with actual service connections."""
    
    def __init__(self):
        self.orchestrator = None
        self.supermemory = None
        self.embedder = None
        self.search_engine = None
        self.knowledge_graph = None
        self.graph_rag = None
        self.gate_manager = None
        self.redis_client = None
        self.weaviate_client = None
        self.initialized = False
        
        # Validate required environment variables
        self._validate_environment()
    
    def _validate_environment(self):
        """Validate that all required environment variables are set."""
        required_vars = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "REDIS_URL",
            "QDRANT_URL",
            "QDRANT_API_KEY"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Create a singleton instance
_global_state = GlobalState()

def get_state() -> GlobalState:
    """Get the global application state."""
    return _global_state

def get_orchestrator(state: GlobalState = Depends(get_state)) -> Any:
    """Get the swarm orchestrator - REAL implementation only."""
    if not state.orchestrator:
        try:
            # Import the consolidated unified orchestrator
            from pulumi.agent_orchestrator.src.unified_orchestrator import UnifiedSwarmOrchestrator
            state.orchestrator = UnifiedSwarmOrchestrator()
            logger.info("✅ Real UnifiedSwarmOrchestrator initialized")
        except ImportError as e:
            logger.error(f"❌ Failed to import UnifiedSwarmOrchestrator: {e}")
            if os.getenv("FAIL_ON_MOCK_FALLBACK", "false").lower() == "true":
                raise HTTPException(status_code=503, detail=f"Orchestrator service unavailable: {e}")
            raise ImportError(f"UnifiedSwarmOrchestrator not available: {e}")
    
    return state.orchestrator

def get_memory_store(state: GlobalState = Depends(get_state)) -> Any:
    """Get the memory store - REAL unified implementation."""
    if not state.supermemory:
        try:
            # Use the consolidated unified memory system
            from pulumi.mcp_server.src.unified_memory import UnifiedMemorySystem
            state.supermemory = UnifiedMemorySystem()
            logger.info("✅ Real UnifiedMemorySystem initialized")
        except ImportError as e:
            logger.error(f"❌ Failed to import UnifiedMemorySystem: {e}")
            if os.getenv("FAIL_ON_MOCK_FALLBACK", "false").lower() == "true":
                raise HTTPException(status_code=503, detail=f"Memory service unavailable: {e}")
            raise ImportError(f"UnifiedMemorySystem not available: {e}")
    
    return state.supermemory

def get_search_engine(state: GlobalState = Depends(get_state)) -> Any:
    """Get the search engine - REAL implementation."""
    if not state.search_engine:
        try:
            # Use the consolidated embedding system for search
            from pulumi.vector_store.src.modern_embeddings import ModernEmbeddingSystem
            state.search_engine = ModernEmbeddingSystem()
            logger.info("✅ Real ModernEmbeddingSystem initialized")
        except ImportError as e:
            logger.error(f"❌ Failed to import ModernEmbeddingSystem: {e}")
            if os.getenv("FAIL_ON_MOCK_FALLBACK", "false").lower() == "true":
                raise HTTPException(status_code=503, detail=f"Search service unavailable: {e}")
            raise ImportError(f"ModernEmbeddingSystem not available: {e}")
    
    return state.search_engine

def get_gate_manager(state: GlobalState = Depends(get_state)) -> Any:
    """Get the evaluation gate manager - REAL implementation."""
    if not state.gate_manager:
        try:
            from app.evaluation.gates import EvaluationGateManager
            state.gate_manager = EvaluationGateManager()
            logger.info("✅ Real EvaluationGateManager initialized")
        except ImportError as e:
            logger.warning(f"EvaluationGateManager not available: {e}")
            # This is optional, so we can proceed without it
            state.gate_manager = None
    
    return state.gate_manager

def get_redis_client(state: GlobalState = Depends(get_state)):
    """Get Redis client - REAL connection."""
    if not state.redis_client:
        try:
            import redis
            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                raise ValueError("REDIS_URL environment variable not set")
                
            state.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            state.redis_client.ping()
            logger.info("✅ Real Redis connection established")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            if os.getenv("FAIL_ON_MOCK_FALLBACK", "false").lower() == "true":
                raise HTTPException(status_code=503, detail=f"Redis unavailable: {e}")
            raise ConnectionError(f"Redis connection failed: {e}")
    
    return state.redis_client

def get_weaviate_client(state: GlobalState = Depends(get_state)):
    """Get Weaviate client - REAL connection with v1.32+ features."""
    if not state.weaviate_client:
        try:
            import weaviate
            from weaviate.classes.init import Auth
            
            weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
            weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
            
            # Use local Weaviate for development, cloud for production
            if "localhost" in weaviate_url:
                state.weaviate_client = weaviate.connect_to_local(
                    host=weaviate_url.replace("http://", "").replace(":8080", ""),
                    port=8080
                )
            else:
                if not weaviate_api_key:
                    raise ValueError("WEAVIATE_API_KEY required for cloud connection")
                state.weaviate_client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=weaviate_url,
                    auth_credentials=Auth.api_key(weaviate_api_key)
                )
            
            # Test connection
            state.weaviate_client.collections.list_all()
            logger.info("✅ Real Weaviate v1.32+ connection established")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Weaviate: {e}")
            if os.getenv("FAIL_ON_MOCK_FALLBACK", "false").lower() == "true":
                raise HTTPException(status_code=503, detail=f"Weaviate unavailable: {e}")
            raise ConnectionError(f"Weaviate connection failed: {e}")
    
    return state.weaviate_client

def initialize_dependencies(unified_state=None):
    """Initialize dependencies with REAL service connections."""
    global _global_state
    if unified_state:
        _global_state = unified_state
        logger.info("✅ Dependencies initialized with real unified server state")
    else:
        logger.info("✅ Dependencies initialized with real service connections")
    
    # Pre-validate all critical services
    try:
        redis_client = get_redis_client(Depends(get_state))
        weaviate_client = get_weaviate_client(Depends(get_state))
        logger.info("✅ All critical dependencies validated successfully")
        _global_state.initialized = True
    except Exception as e:
        logger.error(f"❌ Dependency initialization failed: {e}")
        if os.getenv("FAIL_ON_MOCK_FALLBACK", "false").lower() == "true":
            raise Exception(f"Critical services unavailable: {e}")