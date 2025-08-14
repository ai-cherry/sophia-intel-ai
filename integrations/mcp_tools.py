"""
MCP Tools Integration Layer
Provides backward-compatible interface while supporting new MCP architecture
"""
from __future__ import annotations
import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger

# Environment configuration
USE_MCP = os.getenv("USE_MCP", "1") == "1"
USE_NEW_MCP = os.getenv("USE_NEW_MCP", "1") == "1"
SESSION_DIR = Path(os.getenv("MCP_SESSION_DIR", ".sophia_sessions"))
SESSION_DIR.mkdir(parents=True, exist_ok=True)


def _noop(*args, **kwargs):
    return [] if "search" in kwargs or (args and isinstance(args[0], str)) else {}

# Default no-op implementations (will be replaced if MCP is available)
# Function implementations are defined below after MCP system initialization


# Global variables for MCP clients
_legacy_available = False
_new_available = False
_client_manager = None
_legacy_components = {}

# Initialize legacy MCP system if available
if USE_MCP:
    try:
        # Try to import legacy components first for backward compatibility
        from libs.mcp_client.sophia_client import SophiaClient
        from libs.mcp_client.session_manager import SessionManager
        from libs.mcp_client.repo_intelligence import RepoIntelligence
        from libs.mcp_client.context_tools import ContextTools
        from libs.mcp_client.predictive_assistant import PredictiveAssistant
        try:
            from libs.mcp_client.performance_monitor import PerfMonitor
        except ImportError:
            PerfMonitor = None

        # Initialize legacy system
        _mgr = SessionManager(session_dir=str(SESSION_DIR))
        _sess = _mgr.start_or_resume()
        _cli = SophiaClient(
            code_context_transport=os.getenv("MCP_CODE_CONTEXT", "stdio"),
            http_url=os.getenv("MCP_HTTP_URL", "")
        )
        _repo = RepoIntelligence(client=_cli, session=_sess)
        _ctx = ContextTools(client=_cli, session=_sess)
        # Use correct parameter name
        _pred = PredictiveAssistant(mcp_client=_cli)
        _perf = PerfMonitor(
            client=_cli, session=_sess) if PerfMonitor else None

        _legacy_components = {
            'manager': _mgr,
            'session': _sess,
            'client': _cli,
            'repo': _repo,
            'context': _ctx,
            'predictor': _pred,
            'performance': _perf
        }
        _legacy_available = True
        logger.info("Legacy MCP system initialized successfully")

    except ImportError as e:
        logger.info(f"Legacy MCP components not available: {e}")
    except Exception as e:
        logger.warning(f"Failed to initialize legacy MCP system: {e}")

# Initialize new MCP system if available and enabled
if USE_NEW_MCP:
    try:
        from libs.mcp_client.base_client import get_client_manager, SearchResult
        _new_available = True
        logger.info("New MCP system available")
    except ImportError:
        logger.info("New MCP system not available")
    except Exception as e:
        logger.warning(f"Failed to import new MCP system: {e}")


async def _get_client_manager():
    """Get the new MCP client manager"""
    global _client_manager
    if _client_manager is None and _new_available:
        try:
            _client_manager = await get_client_manager()
        except Exception as e:
            logger.error(f"Failed to get client manager: {e}")
    return _client_manager


def _run_async(coro):
    """Run async function in sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, we can't use run_until_complete
            # Create a task instead
            task = asyncio.create_task(coro)
            return None  # Return None for now, could implement proper async handling later
        else:
            return loop.run_until_complete(coro)
    except Exception:
        try:
            return asyncio.run(coro)
        except Exception:
            return None

# Enhanced MCP functions with new architecture support


def mcp_semantic_search(query: str, k: int = 8, swarm_stage: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Semantic search with support for both legacy and new MCP systems

    Args:
        query: Search query
        k: Number of results to return  
        swarm_stage: Current Swarm stage for context-aware routing

    Returns:
        List of search results in standardized format
    """
    results = []

    # Try new MCP system first if available
    if _new_available and USE_NEW_MCP:
        try:
            async def _search_new():
                manager = await _get_client_manager()
                if manager:
                    search_results = await manager.search_all(query, k, swarm_stage)
                    return [
                        {
                            "id": result.id,
                            "content": result.content,
                            "score": result.score,
                            "source": result.service,
                            "metadata": result.metadata,
                            "path": result.metadata.get("path", ""),
                            "timestamp": result.timestamp
                        }
                        for result in search_results
                    ]
                return []

            new_results = _run_async(_search_new())
            if new_results:
                logger.debug(f"New MCP returned {len(new_results)} results")
                return new_results

        except Exception as e:
            logger.warning(f"New MCP search failed: {e}")

    # Fall back to legacy system
    if _legacy_available and _legacy_components.get('repo'):
        try:
            legacy_results = _legacy_components['repo'].semantic_search(
                query=query, k=k) or []
            # Convert to standardized format
            results = []
            for result in legacy_results:
                standardized = {
                    "id": result.get("id", f"legacy_{hash(result.get('content', ''))}"),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.5),
                    "source": "legacy_mcp",
                    "metadata": result.get("metadata", {}),
                    "path": result.get("path", ""),
                    "timestamp": result.get("timestamp", 0)
                }
                results.append(standardized)

            logger.debug(f"Legacy MCP returned {len(results)} results")
            return results

        except Exception as e:
            logger.warning(f"Legacy MCP search failed: {e}")

    return []


def mcp_file_map(paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get file mapping from MCP system"""
    if _legacy_available and _legacy_components.get('repo'):
        try:
            return _legacy_components['repo'].code_map(paths or [])
        except Exception as e:
            logger.warning(f"Legacy file mapping failed: {e}")

    return {}


def mcp_smart_hints(tool_name: str, context: str = "", swarm_stage: Optional[str] = None) -> Dict[str, Any]:
    """Get smart hints for next actions"""
    if _legacy_available and _legacy_components.get('predictor'):
        try:
            # Use the correct method name based on the actual implementation
            if hasattr(_legacy_components['predictor'], 'next_actions'):
                return _legacy_components['predictor'].next_actions(tool_name=tool_name, context=context) or {}
            elif hasattr(_legacy_components['predictor'], 'predict'):
                return _legacy_components['predictor'].predict(tool_name=tool_name, context=context) or {}
            else:
                logger.warning("Predictor doesn't have expected methods")
        except Exception as e:
            logger.warning(f"Smart hints failed: {e}")

    # Return basic hints based on tool name and stage
    hints = {
        "suggestions": [],
        "context": f"tool={tool_name}, stage={swarm_stage}",
        "confidence": 0.5
    }

    # Add stage-specific hints
    if swarm_stage == "architect":
        hints["suggestions"] = [
            "Analyze requirements and constraints",
            "Design system architecture",
            "Create technical specifications"
        ]
    elif swarm_stage == "builder":
        hints["suggestions"] = [
            "Implement core functionality",
            "Write comprehensive tests",
            "Optimize performance"
        ]
    elif swarm_stage == "tester":
        hints["suggestions"] = [
            "Run test suites",
            "Validate functionality",
            "Report issues and bugs"
        ]
    elif swarm_stage == "operator":
        hints["suggestions"] = [
            "Deploy to production",
            "Monitor system health",
            "Handle operational issues"
        ]
    else:
        hints["suggestions"] = [
            "Analyze current context",
            "Determine next steps",
            "Execute appropriate actions"
        ]

    return hints


def mcp_learn(event: Dict[str, Any]) -> None:
    """Learn from events across both MCP systems"""
    # Learn with legacy system
    if _legacy_available:
        try:
            if _legacy_components.get('context'):
                _legacy_components['context'].learn(event)
            if _legacy_components.get('performance'):
                _legacy_components['performance'].record(event)
        except Exception as e:
            logger.warning(f"Legacy learning failed: {e}")

    # Learn with new system (async)
    if _new_available:
        try:
            async def _learn_new():
                manager = await _get_client_manager()
                if manager:
                    for client in manager.clients.values():
                        try:
                            client.learn(event)
                        except Exception as e:
                            logger.debug(
                                f"Learning failed for {client.service_name}: {e}")

            _run_async(_learn_new())
        except Exception as e:
            logger.warning(f"New MCP learning failed: {e}")

# Enhanced functions for new MCP architecture


async def mcp_multi_service_search(
    query: str,
    k: int = 8,
    services: Optional[List[str]] = None,
    swarm_stage: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Advanced multi-service search using new MCP architecture

    Args:
        query: Search query
        k: Number of results to return
        services: Specific services to search (None = all available)
        swarm_stage: Current Swarm stage

    Returns:
        List of search results from multiple services
    """
    if not _new_available:
        # Fall back to regular search
        return mcp_semantic_search(query, k, swarm_stage)

    try:
        manager = await _get_client_manager()
        if not manager:
            return mcp_semantic_search(query, k, swarm_stage)

        if services:
            # Search specific services
            all_results = []
            for service_name in services:
                client = await manager.get_client(service_name)
                if client:
                    results = await client.semantic_search(query, k, swarm_stage)
                    all_results.extend(results)

            # Sort and limit results
            all_results.sort(key=lambda x: x.score, reverse=True)
            return [
                {
                    "id": result.id,
                    "content": result.content,
                    "score": result.score,
                    "source": result.service,
                    "metadata": result.metadata,
                    "path": result.metadata.get("path", ""),
                    "timestamp": result.timestamp
                }
                for result in all_results[:k]
            ]
        else:
            # Search all services
            search_results = await manager.search_all(query, k, swarm_stage)
            return [
                {
                    "id": result.id,
                    "content": result.content,
                    "score": result.score,
                    "source": result.service,
                    "metadata": result.metadata,
                    "path": result.metadata.get("path", ""),
                    "timestamp": result.timestamp
                }
                for result in search_results
            ]

    except Exception as e:
        logger.error(f"Multi-service search failed: {e}")
        return mcp_semantic_search(query, k, swarm_stage)


def get_mcp_status() -> Dict[str, Any]:
    """Get status of MCP systems"""
    status = {
        "legacy_available": _legacy_available,
        "new_available": _new_available,
        "use_mcp": USE_MCP,
        "use_new_mcp": USE_NEW_MCP,
        "session_dir": str(SESSION_DIR)
    }

    if _legacy_available:
        status["legacy_components"] = list(_legacy_components.keys())

    if _new_available:
        async def _get_new_status():
            manager = await _get_client_manager()
            if manager:
                return {
                    "available_services": manager.get_available_services(),
                    "metrics": manager.get_all_metrics()
                }
            return {}

        new_status = _run_async(_get_new_status())
        if new_status:
            status["new_mcp"] = new_status

    return status

# Backward compatibility aliases


def semantic_search(query: str, k: int = 8) -> List[Dict[str, Any]]:
    """Backward compatibility alias"""
    return mcp_semantic_search(query, k)


def file_map(paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """Backward compatibility alias"""
    return mcp_file_map(paths)


def smart_hints(tool_name: str, context: str = "") -> Dict[str, Any]:
    """Backward compatibility alias"""
    return mcp_smart_hints(tool_name, context)


def learn(event: Dict[str, Any]) -> None:
    """Backward compatibility alias"""
    mcp_learn(event)


# Export main functions
__all__ = [
    'mcp_semantic_search',
    'mcp_file_map',
    'mcp_smart_hints',
    'mcp_learn',
    'mcp_multi_service_search',
    'get_mcp_status',
    'semantic_search',
    'file_map',
    'smart_hints',
    'learn'
]
