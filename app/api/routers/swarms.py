"""
API router for Coding Swarm endpoints.

This module exposes the coding swarm functionality through REST API endpoints,
allowing clients to configure and execute swarms with full control over settings.
"""

import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.circuit_breaker import with_circuit_breaker
from app.swarms import SwarmOrchestrator
from app.swarms.coding.models import (
    DebateResult,
    PoolType,
    SwarmConfiguration,
    SwarmRequest,
)
from app.swarms.coding.team import execute_swarm_request

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/swarms", tags=["swarms"], responses={404: {"description": "Not found"}}
)


@router.post("/coding/execute", response_model=DebateResult)
async def execute_coding_swarm(
    request: SwarmRequest, background_tasks: BackgroundTasks
) -> DebateResult:
    """
    Execute a coding swarm with full configuration control.

    This endpoint allows clients to specify all aspects of the swarm execution
    including team composition, evaluation gates, and memory integration.

    Args:
        request: SwarmRequest with task and configuration
        background_tasks: FastAPI background tasks

    Returns:
        DebateResult with complete execution details

    Raises:
        HTTPException: If execution fails
    """
    try:
        logger.info(f"Executing coding swarm for task: {request.task[:50]}...")

        # Execute the swarm
        result = await execute_swarm_request(request)

        # Log metrics in background
        background_tasks.add_task(log_swarm_metrics, result, request.configuration)

        return result

    except ValueError as e:
        logger.error(f"Invalid configuration: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Swarm execution failed: {e}")
        raise HTTPException(status_code=500, detail="Swarm execution failed")


@router.post("/coding/stream")
async def stream_coding_swarm(request: SwarmRequest):
    """
    Execute a coding swarm with streaming responses.

    This endpoint streams the swarm execution progress in real-time,
    allowing clients to see intermediate results and agent interactions.

    Args:
        request: SwarmRequest with task and configuration

    Returns:
        StreamingResponse with newline-delimited JSON events
    """

    async def generate_stream():
        try:
            # Create team
            from app.swarms.coding.team_factory import TeamFactory

            team = TeamFactory.create_team(request.configuration)

            # Get memory if enabled
            memory = None
            if request.configuration.use_memory:
                memory = await get_supermemory_instance()

            # Create orchestrator
            orchestrator = SwarmOrchestrator(team, request.configuration, memory)

            # Stream events
            yield json.dumps(
                {"event": "start", "team": team.name, "task": request.task}
            ) + "\n"

            # Run debate with streaming
            # (In production, would modify orchestrator to support streaming)
            result = await orchestrator.run_debate(request.task, request.context)

            # Stream final result
            yield json.dumps(
                {"event": "complete", "result": result.model_dump()}
            ) + "\n"

        except Exception as e:
            yield json.dumps({"event": "error", "message": str(e)}) + "\n"

    return StreamingResponse(generate_stream(), media_type="application/x-ndjson")


@router.get("/coding/pools")
async def get_available_pools() -> dict[str, Any]:
    """
    Get available model pools for swarm configuration.

    Returns:
        Dictionary with pool names and their descriptions
    """
    from app.swarms.coding.pools import POOLS

    pools_info = {}
    for pool_name, models in POOLS.items():
        pools_info[pool_name] = {
            "models": models,
            "description": f"{pool_name.capitalize()} pool with {len(models)} models",
            "recommended_for": get_pool_recommendation(pool_name),
        }

    return {"pools": pools_info, "default": "balanced"}


@router.get("/coding/configuration")
async def get_default_configuration() -> SwarmConfiguration:
    """
    Get default swarm configuration with all available options.

    This endpoint returns the default configuration schema,
    helping clients understand available options.

    Returns:
        Default SwarmConfiguration
    """
    return SwarmConfiguration()


@router.post("/coding/validate")
async def validate_configuration(config: SwarmConfiguration) -> dict[str, Any]:
    """
    Validate a swarm configuration without executing.

    Args:
        config: SwarmConfiguration to validate

    Returns:
        Validation result with any warnings or suggestions
    """
    from app.swarms.coding.team_factory import TeamFactory

    result = {"valid": True, "warnings": [], "suggestions": []}

    try:
        TeamFactory.validate_configuration(config)
    except ValueError as e:
        result["valid"] = False
        result["warnings"].append(str(e))

    # Add suggestions
    if config.max_generators > 6:
        result["suggestions"].append(
            "Consider reducing max_generators for better coordination"
        )

    if config.timeout_seconds < 60:
        result["suggestions"].append(
            "Very short timeout may not allow complex tasks to complete"
        )

    if config.accuracy_threshold > 9:
        result["suggestions"].append(
            "Very high accuracy threshold may reject valid solutions"
        )

    if config.enable_file_write and not config.include_runner:
        result["warnings"].append("File write enabled but no runner agent included")

    return result


@router.get("/coding/history")
@with_circuit_breaker("database")
async def get_swarm_history(
    limit: int = Query(10, ge=1, le=100),
    session_id: Optional[str] = None,
    team_id: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Get history of swarm executions from memory.

    Args:
        limit: Maximum number of results
        session_id: Filter by session
        team_id: Filter by team

    Returns:
        List of historical swarm results
    """
    try:
        memory = await get_supermemory_instance()

        # Build search query
        query = "swarm_result"
        if session_id:
            query += f" session:{session_id}"
        if team_id:
            query += f" team:{team_id}"

        # Search memory
        entries = await memory.search_memory(query, limit=limit)

        # Format results
        history = []
        for entry in entries:
            try:
                # Parse stored result
                content = (
                    json.loads(entry.content)
                    if isinstance(entry.content, str)
                    else entry.content
                )
                history.append(
                    {
                        "timestamp": entry.created_at,
                        "task": content.get("task", "Unknown"),
                        "approved": content.get("approved", False),
                        "session_id": session_id,
                        "team_id": team_id,
                    }
                )
            except:
                continue

        return history

    except Exception as e:
        logger.warning(f"Failed to retrieve history: {e}")
        return []


@router.post("/coding/quick")
async def quick_coding_swarm(
    task: str = Query(..., description="The coding task to solve"),
    pool: str = Query("balanced", description="Model pool to use"),
    max_generators: int = Query(4, ge=1, le=10),
    enable_runner: bool = Query(False, description="Include runner agent"),
    use_memory: bool = Query(True, description="Use memory service"),
) -> DebateResult:
    """
    Quick endpoint for simple swarm execution with query parameters.

    This is a simplified interface for common use cases.

    Args:
        task: The coding task
        pool: Model pool name
        max_generators: Maximum number of generators
        enable_runner: Whether to include runner
        use_memory: Whether to use memory

    Returns:
        DebateResult
    """
    try:
        # Build configuration from parameters
        config = SwarmConfiguration(
            pool=PoolType(pool),
            max_generators=max_generators,
            include_runner=enable_runner,
            use_memory=use_memory,
        )

        # Create request
        request = SwarmRequest(task=task, configuration=config)

        # Execute
        return await execute_swarm_request(request)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Quick swarm failed: {e}")
        raise HTTPException(status_code=500, detail="Execution failed")


async def log_swarm_metrics(result: DebateResult, config: SwarmConfiguration):
    """
    Log swarm execution metrics for monitoring.

    Args:
        result: The debate result
        config: The configuration used
    """
    metrics = {
        "task_length": len(result.task),
        "execution_time_ms": result.execution_time_ms,
        "errors": len(result.errors),
        "warnings": len(result.warnings),
        "approved": result.runner_approved,
        "pool": config.pool.value,
        "generators": config.max_generators,
        "memory_used": config.use_memory,
    }

    if result.critic:
        metrics["critic_verdict"] = result.critic.verdict.value
        metrics["critic_confidence"] = result.critic.confidence_score

    if result.judge:
        metrics["judge_decision"] = result.judge.decision.value
        metrics["judge_confidence"] = result.judge.confidence_score

    if result.gate_decision:
        metrics["gate_allowed"] = result.gate_decision.allowed
        metrics["risk_level"] = result.gate_decision.risk_level.value

    logger.info(f"Swarm metrics: {json.dumps(metrics)}")


def get_pool_recommendation(pool_name: str) -> str:
    """Get recommendation for when to use a specific pool."""
    recommendations = {
        "fast": "Quick prototypes and simple tasks",
        "balanced": "Most development tasks with good quality/speed trade-off",
        "heavy": "Complex algorithms, architecture design, and critical code",
    }
    return recommendations.get(pool_name, "General purpose")


# Export router
__all__ = ["router"]
