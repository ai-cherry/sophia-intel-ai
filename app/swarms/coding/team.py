"""
Coding Swarm main module.

This module provides the public interface for creating and running coding swarms,
delegating to specialized modules for team construction and orchestration.
"""

import asyncio
import logging
import warnings
from typing import Any

from agno.team import Team

from app.memory.supermemory_mcp import SupermemoryMCP

# SwarmOrchestrator removed - use SuperOrchestrator if needed
# from app.core.super_orchestrator import get_orchestrator
from app.swarms.coding.models import DebateResult, PoolType, SwarmConfiguration, SwarmRequest
from app.swarms.coding.team_factory import TeamFactory

logger = logging.getLogger(__name__)


def make_coding_swarm(
    concurrent_models: list[str] | None = None,
    include_default_pair: bool = True,
    include_runner: bool = False,
    pool: str = "balanced"
) -> Team:
    """
    Create an advanced coding swarm with concurrent generators.
    
    Args:
        concurrent_models: List of model names for additional generators
        include_default_pair: Include the default Coder-A and Coder-B
        include_runner: Include the Runner agent (with write permissions)
        pool: Model pool to use ("fast", "balanced", "heavy")
    
    Returns:
        Configured Team with concurrent execution capabilities
    """
    # Build configuration
    config = SwarmConfiguration(
        pool=PoolType(pool),
        concurrent_models=concurrent_models or [],
        include_default_pair=include_default_pair,
        include_runner=include_runner
    )

    # Validate configuration
    TeamFactory.validate_configuration(config)

    # Create team
    team = TeamFactory.create_team(config)

    logger.info(f"Created coding swarm with pool={pool}, runner={include_runner}")

    return team


async def run_coding_debate(
    team: Team,
    task: str,
    config: SwarmConfiguration | None = None,
    memory: SupermemoryMCP | None = None,
    context: dict[str, Any] | None = None
) -> DebateResult:
    """
    Run a complete debate cycle for the given task.
    
    Args:
        team: The coding swarm team
        task: The task description or ticket
        config: Optional configuration (uses defaults if not provided)
        memory: Optional memory service for persistence
        context: Optional context for the task
    
    Returns:
        DebateResult with all outputs and validation status
    """
    # Use default config if not provided
    if config is None:
        config = SwarmConfiguration()

    # Create orchestrator
    orchestrator = SwarmOrchestrator(team, config, memory)

    # Run debate
    result = await orchestrator.run_debate(task, context)

    # Log summary
    logger.info(f"Debate completed: approved={result.runner_approved}, "
               f"errors={len(result.errors)}, time={result.execution_time_ms}ms")

    return result


def run_coding_debate_sync(
    team: Team,
    task: str,
    config: SwarmConfiguration | None = None,
    memory: SupermemoryMCP | None = None,
    context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Synchronous wrapper for run_coding_debate.
    
    This function runs the async debate in a new event loop and returns
    the result as a dictionary for backward compatibility.
    
    Args:
        team: The coding swarm team
        task: The task description
        config: Optional configuration
        memory: Optional memory service
        context: Optional context
    
    Returns:
        Dictionary with debate results (for backward compatibility)
    """
    # Run async function in event loop
    result = asyncio.run(run_coding_debate(team, task, config, memory, context))

    # Convert to dictionary for backward compatibility
    return result.model_dump()


def make_coding_swarm_pool(pool: str = "fast") -> Team:
    """
    Build a Coding Swarm using a predefined model pool.
    
    Args:
        pool: Pool name ("fast", "balanced", "heavy")
    
    Returns:
        Configured Team with pool-based generators
    """
    config = SwarmConfiguration(
        pool=PoolType(pool),
        include_default_pair=False  # Use only pool models
    )

    team = TeamFactory.create_team(config)

    logger.info(f"Created pool-based coding swarm: {pool}")

    return team


async def execute_swarm_request(request: SwarmRequest) -> DebateResult:
    """
    Execute a complete swarm request with configuration.
    
    Args:
        request: SwarmRequest with task and configuration
    
    Returns:
        DebateResult with execution results
    """
    # Create team based on configuration
    team = TeamFactory.create_team(request.configuration)

    # Get memory service if enabled
    memory = None
    if request.configuration.use_memory:
        try:
            from app.memory import get_memory_service
            memory = await get_memory_service()
        except ImportError:
            logger.warning("Memory service not available")

    # Run debate
    orchestrator = SwarmOrchestrator(team, request.configuration, memory)
    result = await orchestrator.run_debate(request.task, request.context)

    # Set session and team IDs
    result.session_id = request.session_id
    result.team_id = request.team_id or team.name

    return result


# ============================================
# DEPRECATED: Legacy functions for backward compatibility
# These will be removed in the next major version
# ============================================

def create_coding_team() -> Team:
    """
    DEPRECATED: Use make_coding_swarm() instead.
    
    Legacy function for backward compatibility.
    Creates the original Coding Team configuration.
    
    This function will be removed in version 2.0.0.
    """
    warnings.warn(
        "create_coding_team() is deprecated and will be removed in v2.0.0. "
        "Use make_coding_swarm() instead.",
        DeprecationWarning,
        stacklevel=2
    )

    # Use new system with legacy-compatible settings
    config = SwarmConfiguration(
        pool=PoolType.BALANCED,
        include_default_pair=True,
        include_runner=False,
        max_generators=2
    )

    team = TeamFactory.create_team(config)
    team.name = "Coding Team"  # Keep legacy name

    return team


# Export public interface
__all__ = [
    "make_coding_swarm",
    "run_coding_debate",
    "run_coding_debate_sync",
    "make_coding_swarm_pool",
    "execute_swarm_request",
    "SwarmConfiguration",
    "SwarmRequest",
    "DebateResult",
    # Deprecated (will be removed)
    "create_coding_team"
]
