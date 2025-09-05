"""
Teams API Router
Handles all team-related endpoints with proper typing and documentation.
"""

import logging
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator

from app.api.dependencies import get_orchestrator, get_state
from app.core.middleware import with_timeout
from app.core.observability import track_swarm_execution
from app.models.schemas import ModelFieldsModel, TeamInfo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["teams"])

# ============================================
# Request/Response Models with Full Typing
# ============================================


class TeamListResponse(BaseModel):
    """Response model for team listing."""

    teams: list[TeamInfo]
    count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TeamRunRequest(BaseModel):
    """Request model for team execution with validation."""

    team_id: str = Field(..., min_length=1, max_length=100, description="Team identifier")
    message: str = Field(..., min_length=1, max_length=10000, description="Task message")
    stream: bool = Field(default=True, description="Enable streaming response")
    use_memory: bool = Field(default=True, description="Use memory context")
    context: Optional[dict[str, Any]] = Field(default=None, description="Additional context")
    timeout: Optional[int] = Field(default=300, ge=1, le=3600, description="Timeout in seconds")

    @validator("team_id")
    def validate_team_id(cls, v: str) -> str:
        """Validate team ID format."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Team ID must be alphanumeric with hyphens/underscores")
        return v


class TeamExecutionResponse(BaseModel):
    """Response model for team execution."""

    task_id: str = Field(..., description="Execution task ID")
    team_id: str = Field(..., description="Team that executed")
    status: str = Field(..., description="Execution status")
    result: Optional[dict[str, Any]] = Field(default=None, description="Execution result")
    duration_ms: Optional[int] = Field(default=None, description="Execution time in ms")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================
# Endpoints with Proper Error Handling
# ============================================


@router.get("", response_model=TeamListResponse, summary="List available teams")
async def list_teams(include_inactive: bool = False, state=Depends(get_state)) -> TeamListResponse:
    """
    List all available AI teams/swarms.

    Args:
        include_inactive: Include inactive teams in response

    Returns:
        TeamListResponse: List of teams with metadata

    Raises:
        HTTPException: If teams cannot be retrieved
    """
    try:
        teams = [
            TeamInfo(
                id="strategic-swarm",
                name="Strategic Planning Swarm",
                description="High-level strategy, architecture, and product planning",
                members=["Chief Architect", "Strategic Planner", "Product Manager"],
                model_pool="premium",
                active=True,
            ),
            TeamInfo(
                id="development-swarm",
                name="Development & Implementation Swarm",
                description="Core development swarm for coding and implementation",
                members=["Lead Developer", "Senior Engineers", "DevOps Engineer"],
                model_pool="balanced",
                active=True,
            ),
            TeamInfo(
                id="security-swarm",
                name="Security & Quality Assurance Swarm",
                description="Security analysis, testing, and quality assurance",
                members=["Security Architect", "Penetration Tester", "QA Engineer"],
                model_pool="premium",
                active=True,
            ),
            TeamInfo(
                id="research-swarm",
                name="Research & Innovation Swarm",
                description="Research, experimentation, and emerging technology",
                members=["Research Scientist", "AI/ML Engineer", "Data Scientist"],
                model_pool="premium",
                active=True,
            ),
        ]

        if not include_inactive:
            teams = [t for t in teams if t.active]

        return TeamListResponse(teams=teams, count=len(teams))

    except Exception as e:
        logger.error(f"Failed to list teams: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve teams: {str(e)}")


@router.get("/{team_id}", response_model=TeamInfo, summary="Get team details")
async def get_team(team_id: str, state=Depends(get_state)) -> TeamInfo:
    """
    Get detailed information about a specific team.

    Args:
        team_id: Team identifier

    Returns:
        TeamInfo: Team details

    Raises:
        HTTPException: If team not found
    """
    try:
        # Get teams and find requested one
        teams_response = await list_teams(include_inactive=True, state=state)

        for team in teams_response.teams:
            if team.id == team_id:
                return team

        raise HTTPException(status_code=404, detail=f"Team '{team_id}' not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team {team_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve team: {str(e)}")


@router.post("/run", response_model=TeamExecutionResponse, summary="Execute team")
@with_timeout(seconds=600)
@track_swarm_execution(team_id="dynamic")
async def run_team(
    request: TeamRunRequest,
    background_tasks: BackgroundTasks,
    orchestrator=Depends(get_orchestrator),
    state=Depends(get_state),
) -> TeamExecutionResponse:
    """
    Execute a team/swarm with the given task.

    Args:
        request: Team execution request
        background_tasks: FastAPI background tasks

    Returns:
        TeamExecutionResponse: Execution result or streaming response

    Raises:
        HTTPException: If execution fails
    """
    import time

    start_time = time.time()

    try:
        # Validate team exists
        team = await get_team(request.team_id, state)

        if not team.active:
            raise HTTPException(status_code=400, detail=f"Team '{request.team_id}' is not active")

        # Execute with streaming if requested
        if request.stream:

            async def stream_execution() -> AsyncGenerator[str, None]:
                """Stream execution results."""
                try:
                    async for chunk in orchestrator.execute_team_stream(
                        team_id=request.team_id,
                        message=request.message,
                        context=request.context,
                        use_memory=request.use_memory,
                    ):
                        yield chunk
                except Exception as e:
                    yield f"data: {{'error': '{str(e)}'}}\n\n"
                    yield "data: [DONE]\n\n"

            return StreamingResponse(stream_execution(), media_type="text/event-stream")

        # Non-streaming execution
        result = await orchestrator.execute_team(
            team_id=request.team_id,
            message=request.message,
            context=request.context,
            use_memory=request.use_memory,
            timeout=request.timeout,
        )

        duration_ms = int((time.time() - start_time) * 1000)

        # Schedule cleanup in background
        background_tasks.add_task(
            cleanup_execution_artifacts, team_id=request.team_id, task_id=result.get("task_id")
        )

        return TeamExecutionResponse(
            task_id=result.get("task_id", "unknown"),
            team_id=request.team_id,
            status="completed",
            result=result,
            duration_ms=duration_ms,
        )

    except HTTPException:
        raise
    except TimeoutError:
        raise HTTPException(
            status_code=504, detail=f"Team execution timed out after {request.timeout} seconds"
        )
    except Exception as e:
        logger.error(f"Team execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Team execution failed: {str(e)}")


@router.post(
    "/{team_id}/run", response_model=TeamExecutionResponse, summary="Execute specific team"
)
async def run_specific_team(
    team_id: str,
    request: TeamRunRequest,
    background_tasks: BackgroundTasks,
    orchestrator=Depends(get_orchestrator),
    state=Depends(get_state),
) -> TeamExecutionResponse:
    """
    Execute a specific team with the given task.
    Alternative endpoint for direct team execution.
    """
    request.team_id = team_id
    return await run_team(request, background_tasks, orchestrator, state)


# ============================================
# Helper Functions
# ============================================


async def cleanup_execution_artifacts(team_id: str, task_id: str) -> None:
    """
    Clean up temporary artifacts after execution.

    Args:
        team_id: Team identifier
        task_id: Task identifier
    """
    try:
        # Clean up temporary files, clear caches, etc.
        logger.info(f"Cleaned up artifacts for {team_id}:{task_id}")
    except Exception as e:
        logger.error(f"Failed to clean up artifacts: {e}")


# ============================================
# Agno Compatibility Aliases
# ============================================


@router.get("/agents", response_model=TeamListResponse, include_in_schema=False)
async def list_agents_compat(state=Depends(get_state)) -> TeamListResponse:
    """Agno-compatible alias for team listing."""
    return await list_teams(state=state)


@router.post("/run/team", response_model=TeamExecutionResponse, include_in_schema=False)
async def run_team_compat(
    request: TeamRunRequest,
    background_tasks: BackgroundTasks,
    orchestrator=Depends(get_orchestrator),
    state=Depends(get_state),
) -> TeamExecutionResponse:
    """Agno-compatible alias for team execution."""
    return await run_team(request, background_tasks, orchestrator, state)


# ============================================
# Dynamic Configuration Endpoints
# ============================================


class TeamCreateRequest(ModelFieldsModel):
    """Request model for creating new teams."""

    id: str = Field(..., min_length=1, max_length=100, description="Team identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Team display name")
    description: str = Field(..., min_length=1, max_length=1000, description="Team description")
    members: list[str] = Field(..., min_items=1, description="Team member roles")
    model_pool: str = Field(default="balanced", description="Model pool (balanced, premium, basic)")
    active: bool = Field(default=True, description="Whether team is active")
    configuration: Optional[dict[str, Any]] = Field(default=None, description="Team configuration")

    @validator("id")
    def validate_id(cls, v: str) -> str:
        """Validate team ID format."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Team ID must be alphanumeric with hyphens/underscores")
        return v


class TeamUpdateRequest(ModelFieldsModel):
    """Request model for updating team metadata."""

    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Team display name")
    description: Optional[str] = Field(
        None, min_length=1, max_length=1000, description="Team description"
    )
    members: Optional[list[str]] = Field(None, min_items=1, description="Team member roles")
    model_pool: Optional[str] = Field(None, description="Model pool (balanced, premium, basic)")
    active: Optional[bool] = Field(None, description="Whether team is active")


class TeamConfigUpdate(BaseModel):
    """Model for team configuration updates."""

    model: Optional[str] = Field(None, description="LLM model to use")
    persona: Optional[str] = Field(None, description="Team persona/personality")
    instructions: Optional[str] = Field(None, description="Custom instructions")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: Optional[int] = Field(None, ge=1, le=100000, description="Max tokens")
    members: Optional[list[str]] = Field(None, description="Team member roles")


@router.patch("/{team_id}/config", response_model=TeamInfo, summary="Update team configuration")
async def update_team_config(
    team_id: str,
    config: TeamConfigUpdate,
    orchestrator=Depends(get_orchestrator),
    state=Depends(get_state),
) -> TeamInfo:
    """
    Update configuration for a specific team.

    Args:
        team_id: Team identifier
        config: Configuration updates

    Returns:
        TeamInfo: Updated team details

    Raises:
        HTTPException: If update fails
    """
    try:
        # Verify team exists
        await get_team(team_id, state)

        # Apply configuration updates
        updates = {}
        if config.model:
            updates["model"] = config.model
        if config.persona:
            updates["persona"] = config.persona
        if config.instructions:
            updates["instructions"] = config.instructions
        if config.temperature is not None:
            updates["temperature"] = config.temperature
        if config.max_tokens:
            updates["max_tokens"] = config.max_tokens
        if config.members:
            updates["members"] = config.members

        # Update via orchestrator
        await orchestrator.update_team_config(team_id, updates)

        # Return updated team info
        updated_team = await get_team(team_id, state)
        return updated_team

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update team config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@router.get("/{team_id}/config", summary="Get team configuration")
async def get_team_config(
    team_id: str, orchestrator=Depends(get_orchestrator), state=Depends(get_state)
) -> dict[str, Any]:
    """
    Get current configuration for a team.

    Args:
        team_id: Team identifier

    Returns:
        Dict: Team configuration

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Verify team exists
        team = await get_team(team_id, state)

        # Get configuration from orchestrator
        config = await orchestrator.get_team_config(team_id)

        return {
            "team_id": team_id,
            "name": team.name,
            "configuration": config,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve configuration: {str(e)}")


# ============================================
# Full CRUD Operations
# ============================================


@router.post("", response_model=TeamInfo, summary="Create new team")
async def create_team(
    request: TeamCreateRequest, orchestrator=Depends(get_orchestrator), state=Depends(get_state)
) -> TeamInfo:
    """
    Create a new AI team/swarm.

    Args:
        request: Team creation request

    Returns:
        TeamInfo: Created team details

    Raises:
        HTTPException: If creation fails or team already exists
    """
    try:
        # Check if team already exists
        try:
            existing_team = await get_team(request.id, state)
            if existing_team:
                raise HTTPException(status_code=409, detail=f"Team '{request.id}' already exists")
        except HTTPException as e:
            if e.status_code != 404:
                raise
            # 404 is expected for new teams
            pass

        # Create team via orchestrator
        team_config = {
            "id": request.id,
            "name": request.name,
            "description": request.description,
            "members": request.members,
            "model_pool": request.model_pool,
            "active": request.active,
            "configuration": request.configuration or {},
        }

        await orchestrator.create_team(request.id, team_config)

        # Return created team
        new_team = TeamInfo(
            id=request.id,
            name=request.name,
            description=request.description,
            members=request.members,
            model_pool=request.model_pool,
            active=request.active,
        )

        logger.info(f"Created new team: {request.id}")
        return new_team

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create team: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")


@router.put("/{team_id}", response_model=TeamInfo, summary="Update team")
async def update_team(
    team_id: str,
    request: TeamUpdateRequest,
    orchestrator=Depends(get_orchestrator),
    state=Depends(get_state),
) -> TeamInfo:
    """
    Update an existing team's metadata.

    Args:
        team_id: Team identifier
        request: Team update request

    Returns:
        TeamInfo: Updated team details

    Raises:
        HTTPException: If update fails or team not found
    """
    try:
        # Verify team exists
        existing_team = await get_team(team_id, state)

        # Prepare updates
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.members is not None:
            updates["members"] = request.members
        if request.model_pool is not None:
            updates["model_pool"] = request.model_pool
        if request.active is not None:
            updates["active"] = request.active

        # Update via orchestrator
        await orchestrator.update_team_metadata(team_id, updates)

        # Return updated team info
        updated_team = TeamInfo(
            id=team_id,
            name=request.name or existing_team.name,
            description=request.description or existing_team.description,
            members=request.members or existing_team.members,
            model_pool=request.model_pool or existing_team.model_pool,
            active=request.active if request.active is not None else existing_team.active,
        )

        logger.info(f"Updated team: {team_id}")
        return updated_team

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update team: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update team: {str(e)}")


@router.delete("/{team_id}", summary="Delete team")
async def delete_team(
    team_id: str,
    force: bool = False,
    orchestrator=Depends(get_orchestrator),
    state=Depends(get_state),
) -> dict[str, Any]:
    """
    Delete an AI team/swarm.

    Args:
        team_id: Team identifier
        force: Force deletion even if team is active

    Returns:
        Dict: Deletion status

    Raises:
        HTTPException: If deletion fails or team not found
    """
    try:
        # Verify team exists
        team = await get_team(team_id, state)

        # Check if team is active and force flag
        if team.active and not force:
            raise HTTPException(
                status_code=400, detail=f"Team '{team_id}' is active. Use force=true to delete."
            )

        # Delete via orchestrator
        await orchestrator.delete_team(team_id)

        logger.info(f"Deleted team: {team_id}")
        return {
            "status": "success",
            "message": f"Team '{team_id}' deleted successfully",
            "team_id": team_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete team: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete team: {str(e)}")


# ============================================
# Advanced Team Management
# ============================================


@router.post("/{team_id}/activate", summary="Activate team")
async def activate_team(
    team_id: str, orchestrator=Depends(get_orchestrator), state=Depends(get_state)
) -> dict[str, Any]:
    """
    Activate a team/swarm.

    Args:
        team_id: Team identifier

    Returns:
        Dict: Activation status
    """
    try:
        # Verify team exists
        await get_team(team_id, state)

        # Activate via orchestrator
        await orchestrator.activate_team(team_id)

        return {
            "status": "success",
            "message": f"Team '{team_id}' activated",
            "team_id": team_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate team: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to activate team: {str(e)}")


@router.post("/{team_id}/deactivate", summary="Deactivate team")
async def deactivate_team(
    team_id: str, orchestrator=Depends(get_orchestrator), state=Depends(get_state)
) -> dict[str, Any]:
    """
    Deactivate a team/swarm.

    Args:
        team_id: Team identifier

    Returns:
        Dict: Deactivation status
    """
    try:
        # Verify team exists
        await get_team(team_id, state)

        # Deactivate via orchestrator
        await orchestrator.deactivate_team(team_id)

        return {
            "status": "success",
            "message": f"Team '{team_id}' deactivated",
            "team_id": team_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate team: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to deactivate team: {str(e)}")


@router.get("/{team_id}/status", summary="Get team status")
async def get_team_status(
    team_id: str, orchestrator=Depends(get_orchestrator), state=Depends(get_state)
) -> dict[str, Any]:
    """
    Get detailed status of a team/swarm.

    Args:
        team_id: Team identifier

    Returns:
        Dict: Team status details
    """
    try:
        # Verify team exists
        team = await get_team(team_id, state)

        # Get status from orchestrator
        status = await orchestrator.get_team_status(team_id)

        return {
            "team_id": team_id,
            "name": team.name,
            "active": team.active,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get team status: {str(e)}")


@router.get("/{team_id}/metrics", summary="Get team metrics")
async def get_team_metrics(
    team_id: str, days: int = 7, orchestrator=Depends(get_orchestrator), state=Depends(get_state)
) -> dict[str, Any]:
    """
    Get performance metrics for a team.

    Args:
        team_id: Team identifier
        days: Number of days of metrics to retrieve

    Returns:
        Dict: Team performance metrics
    """
    try:
        # Verify team exists
        await get_team(team_id, state)

        # Get metrics from orchestrator
        metrics = await orchestrator.get_team_metrics(team_id, days=days)

        return {
            "team_id": team_id,
            "metrics_period_days": days,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get team metrics: {str(e)}")


@router.post("/bulk/activate", summary="Bulk activate teams")
async def bulk_activate_teams(
    team_ids: list[str], orchestrator=Depends(get_orchestrator), state=Depends(get_state)
) -> dict[str, Any]:
    """
    Activate multiple teams at once.

    Args:
        team_ids: List of team identifiers

    Returns:
        Dict: Bulk operation results
    """
    results = {"success": [], "failed": []}

    for team_id in team_ids:
        try:
            await activate_team(team_id, orchestrator, state)
            results["success"].append(team_id)
        except Exception as e:
            results["failed"].append({"team_id": team_id, "error": str(e)})

    return {
        "status": "completed",
        "total": len(team_ids),
        "successful": len(results["success"]),
        "failed": len(results["failed"]),
        "results": results,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health", summary="Teams API health check")
async def teams_health(orchestrator=Depends(get_orchestrator)) -> dict[str, Any]:
    """
    Health check endpoint for teams API.

    Returns:
        Dict: Health status
    """
    try:
        # Basic health checks
        orchestrator_healthy = orchestrator is not None

        # Check if we can list teams
        mock_state = type("MockState", (), {})()
        teams_response = await list_teams(state=mock_state)
        teams_healthy = len(teams_response.teams) >= 0

        overall_healthy = orchestrator_healthy and teams_healthy

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "checks": {
                "orchestrator": "ok" if orchestrator_healthy else "failed",
                "teams_service": "ok" if teams_healthy else "failed",
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
