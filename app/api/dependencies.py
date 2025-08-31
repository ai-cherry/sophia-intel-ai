"""
API Dependencies
Provides dependency injection for FastAPI endpoints.
"""

from typing import Any, Optional
from fastapi import Depends, HTTPException
import logging

logger = logging.getLogger(__name__)

# Mock global state for now - this would normally come from the unified server
class GlobalState:
    """Mock global state for dependency injection."""
    
    def __init__(self):
        self.orchestrator = None
        self.supermemory = None
        self.embedder = None
        self.search_engine = None
        self.knowledge_graph = None
        self.graph_rag = None
        self.gate_manager = None
        self.initialized = False

# Create a singleton instance
_global_state = GlobalState()

def get_state() -> GlobalState:
    """Get the global application state."""
    return _global_state

def get_orchestrator(state: GlobalState = Depends(get_state)) -> Any:
    """Get the swarm orchestrator."""
    if not state.orchestrator:
        # Try to create a basic orchestrator
        try:
            from app.swarms.unified_enhanced_orchestrator import UnifiedSwarmOrchestrator
            state.orchestrator = UnifiedSwarmOrchestrator()
        except ImportError:
            logger.warning("Could not import UnifiedSwarmOrchestrator, using mock")
            state.orchestrator = MockOrchestrator()
    
    return state.orchestrator

def get_memory_store(state: GlobalState = Depends(get_state)) -> Any:
    """Get the memory store."""
    if not state.supermemory:
        try:
            from app.memory.supermemory_mcp import SupermemoryStore
            state.supermemory = SupermemoryStore()
        except ImportError:
            logger.warning("Could not import SupermemoryStore, using mock")
            state.supermemory = None
    
    return state.supermemory

def get_search_engine(state: GlobalState = Depends(get_state)) -> Any:
    """Get the search engine."""
    if not state.search_engine:
        try:
            from app.memory.hybrid_search import HybridSearchEngine
            state.search_engine = HybridSearchEngine()
        except ImportError:
            logger.warning("Could not import HybridSearchEngine, using mock")
            state.search_engine = None
    
    return state.search_engine

def get_gate_manager(state: GlobalState = Depends(get_state)) -> Any:
    """Get the evaluation gate manager."""
    if not state.gate_manager:
        try:
            from app.evaluation.gates import EvaluationGateManager
            state.gate_manager = EvaluationGateManager()
        except ImportError:
            logger.warning("Could not import EvaluationGateManager, using mock")
            state.gate_manager = None
    
    return state.gate_manager

# Mock classes for when imports fail
class MockOrchestrator:
    """Mock orchestrator for when real one is unavailable."""
    
    async def execute_swarm_request(self, request):
        """Mock execution."""
        return {
            "status": "mock_success",
            "message": "Mock orchestrator response",
            "timestamp": "2025-01-01T00:00:00Z"
        }

class MockMemoryStore:
    """Mock memory store."""
    
    async def search_memory(self, query: str, limit: int = 10):
        """Mock memory search."""
        return []
    
    async def add_to_memory(self, entry):
        """Mock memory addition."""
        return {"status": "mock_added"}

class MockSearchEngine:
    """Mock search engine."""
    
    async def search(self, query: str, **kwargs):
        """Mock search."""
        return []

# Initialize state function for unified server integration
def initialize_dependencies(unified_state=None):
    """Initialize dependencies with state from unified server."""
    global _global_state
    if unified_state:
        _global_state = unified_state
        logger.info("Dependencies initialized with unified server state")
    else:
        logger.info("Dependencies initialized with mock state")