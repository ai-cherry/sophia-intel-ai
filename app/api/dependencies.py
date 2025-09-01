"""
API Dependencies
Provides dependency injection for FastAPI endpoints using REAL services.
NO MOCKS - Production ready implementations only.

Following ADR-006: Configuration Management Standardization
- Uses enhanced EnvLoader with Pulumi ESC integration
- Single source of truth for all environment configuration
- Proper secret management and validation
"""

from typing import Any
from fastapi import Depends, HTTPException
import logging

# Import enhanced configuration system following ADR-006
from app.config.env_loader import get_env_config, validate_environment

logger = logging.getLogger(__name__)

class GlobalState:
    """Enhanced global state using ADR-006 configuration management."""
    
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
        
        # Load enhanced configuration
        self.config = None
        self.validation = None
        self._load_and_validate_config()
        
    def _load_and_validate_config(self):
        """Load and validate configuration using enhanced EnvLoader."""
        try:
            self.config = get_env_config()
            self.validation = validate_environment()
            
            logger.info(f"✅ Configuration loaded from: {self.config.loaded_from}")
            
            # Check validation status
            if self.validation.get("overall_status") == "unhealthy":
                logger.warning("⚠️  Configuration validation failed")
                for issue in self.validation.get("critical_issues", []):
                    logger.error(f"❌ {issue}")
                    
                if self.config.environment_name == "prod":
                    # Strict validation in production
                    raise ValueError("Production environment has critical configuration issues")
            
        except Exception as e:
            logger.error(f"❌ Configuration loading failed: {e}")
            # Don't fail startup, but log the issue
            self.config = None
            self.validation = None
            
    def get_config(self):
        """Get the current configuration."""
        if not self.config:
            self.config = get_env_config()
        return self.config

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
    """Get Redis client using enhanced configuration."""
    if not state.redis_client:
        try:
            import redis
            config = state.get_config()
            
            if not config.redis_url:
                raise ValueError("Redis URL not configured")
                
            state.redis_client = redis.from_url(config.redis_url, decode_responses=True)
            # Test connection
            state.redis_client.ping()
            logger.info(f"✅ Redis connection established to {config.redis_host}:{config.redis_port}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            if config and config.environment_name == "prod":
                raise HTTPException(status_code=503, detail=f"Redis unavailable: {e}")
            raise ConnectionError(f"Redis connection failed: {e}")
    
    return state.redis_client

def get_weaviate_client(state: GlobalState = Depends(get_state)):
    """Get Weaviate client using enhanced configuration."""
    if not state.weaviate_client:
        try:
            import weaviate
            from weaviate.classes.init import Auth
            
            config = state.get_config()
            
            # Use configuration values
            weaviate_url = config.weaviate_url
            weaviate_api_key = config.weaviate_api_key
            
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
            logger.info(f"✅ Weaviate v1.32+ connection established to {weaviate_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Weaviate: {e}")
            config = state.get_config()
            if config and config.environment_name == "prod":
                raise HTTPException(status_code=503, detail=f"Weaviate unavailable: {e}")
            raise ConnectionError(f"Weaviate connection failed: {e}")
    
    return state.weaviate_client

def initialize_dependencies(unified_state=None):
    """Initialize dependencies with enhanced configuration management."""
    global _global_state
    if unified_state:
        _global_state = unified_state
        logger.info("✅ Dependencies initialized with unified server state (ADR-006)")
    else:
        logger.info("✅ Dependencies initialized with enhanced configuration (ADR-006)")
    
    # Pre-validate all critical services using enhanced config
    try:
        config = _global_state.get_config()
        
        if config:
            logger.info(f"🔧 Configuration source: {config.loaded_from}")
            logger.info(f"🌍 Environment: {config.environment_name}")
            
            # Test connections based on configuration
            if config.redis_url:
                get_redis_client(_global_state)
                
            if config.weaviate_url:
                get_weaviate_client(_global_state)
                
            logger.info("✅ All critical dependencies validated successfully")
        else:
            logger.warning("⚠️  No configuration loaded - limited functionality")
            
        _global_state.initialized = True
        
    except Exception as e:
        logger.error(f"❌ Dependency initialization failed: {e}")
        config = _global_state.get_config()
        if config and config.environment_name == "prod":
            raise Exception(f"Critical services unavailable in production: {e}")
        # Allow startup in development even with some failures
        logger.warning("⚠️  Continuing with limited functionality")