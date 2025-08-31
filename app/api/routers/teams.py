"""
Teams API Router
Handles all team-related endpoints with proper typing and documentation.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import logging

from app.core.config import settings
from app.core.middleware import with_retry, with_timeout
from app.core.observability import track_swarm_execution
from app.api.dependencies import get_orchestrator, get_state
from app.models.schemas import TeamInfo, RunRequest, RunResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["teams"])

# ============================================
# Request/Response Models with Full Typing
# ============================================

class TeamListResponse(BaseModel):
    """Response model for team listing."""
    teams: List[TeamInfo]
    count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TeamRunRequest(BaseModel):
    """Request model for team execution with validation."""
    team_id: str = Field(..., min_length=1, max_length=100, description="Team identifier")
    message: str = Field(..., min_length=1, max_length=10000, description="Task message")
    stream: bool = Field(default=True, description="Enable streaming response")
    use_memory: bool = Field(default=True, description="Use memory context")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    timeout: Optional[int] = Field(default=300, ge=1, le=3600, description="Timeout in seconds")
    
    @validator('team_id')
    def validate_team_id(cls, v: str) -> str:
        """Validate team ID format."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Team ID must be alphanumeric with hyphens/underscores")
        return v

class TeamExecutionResponse(BaseModel):
    """Response model for team execution."""
    task_id: str = Field(..., description="Execution task ID")
    team_id: str = Field(..., description="Team that executed")
    status: str = Field(..., description="Execution status")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Execution result")
    duration_ms: Optional[int] = Field(default=None, description="Execution time in ms")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ============================================
# Endpoints with Proper Error Handling
# ============================================

@router.get("", response_model=TeamListResponse, summary="List available teams")
async def list_teams(
    include_inactive: bool = False,
    state = Depends(get_state)
) -> TeamListResponse:
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
                active=True
            ),
            TeamInfo(
                id="development-swarm",
                name="Development & Implementation Swarm",
                description="Core development swarm for coding and implementation",
                members=["Lead Developer", "Senior Engineers", "DevOps Engineer"],
                model_pool="balanced",
                active=True
            ),
            TeamInfo(
                id="security-swarm",
                name="Security & Quality Assurance Swarm",
                description="Security analysis, testing, and quality assurance",
                members=["Security Architect", "Penetration Tester", "QA Engineer"],
                model_pool="premium",
                active=True
            ),
            TeamInfo(
                id="research-swarm",
                name="Research & Innovation Swarm",
                description="Research, experimentation, and emerging technology",
                members=["Research Scientist", "AI/ML Engineer", "Data Scientist"],
                model_pool="premium",
                active=True
            )
        ]
        
        if not include_inactive:
            teams = [t for t in teams if t.active]
        
        return TeamListResponse(
            teams=teams,
            count=len(teams)
        )
        
    except Exception as e:
        logger.error(f"Failed to list teams: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve teams: {str(e)}"
        )

@router.get("/{team_id}", response_model=TeamInfo, summary="Get team details")
async def get_team(
    team_id: str,
    state = Depends(get_state)
) -> TeamInfo:
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
        
        raise HTTPException(
            status_code=404,
            detail=f"Team '{team_id}' not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team {team_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve team: {str(e)}"
        )

@router.post("/run", response_model=TeamExecutionResponse, summary="Execute team")
@with_timeout(seconds=600)
@track_swarm_execution(team_id="dynamic")
async def run_team(
    request: TeamRunRequest,
    background_tasks: BackgroundTasks,
    orchestrator = Depends(get_orchestrator),
    state = Depends(get_state)
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
            raise HTTPException(
                status_code=400,
                detail=f"Team '{request.team_id}' is not active"
            )
        
        # Execute with streaming if requested
        if request.stream:
            async def stream_execution() -> AsyncGenerator[str, None]:
                """Stream execution results."""
                try:
                    async for chunk in orchestrator.execute_team_stream(
                        team_id=request.team_id,
                        message=request.message,
                        context=request.context,
                        use_memory=request.use_memory
                    ):
                        yield chunk
                except Exception as e:
                    yield f"data: {{'error': '{str(e)}'}}\n\n"
                    yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                stream_execution(),
                media_type="text/event-stream"
            )
        
        # Non-streaming execution
        result = await orchestrator.execute_team(
            team_id=request.team_id,
            message=request.message,
            context=request.context,
            use_memory=request.use_memory,
            timeout=request.timeout
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Schedule cleanup in background
        background_tasks.add_task(
            cleanup_execution_artifacts,
            team_id=request.team_id,
            task_id=result.get("task_id")
        )
        
        return TeamExecutionResponse(
            task_id=result.get("task_id", "unknown"),
            team_id=request.team_id,
            status="completed",
            result=result,
            duration_ms=duration_ms
        )
        
    except HTTPException:
        raise
    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Team execution timed out after {request.timeout} seconds"
        )
    except Exception as e:
        logger.error(f"Team execution failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Team execution failed: {str(e)}"
        )

@router.post("/{team_id}/run", response_model=TeamExecutionResponse, summary="Execute specific team")
async def run_specific_team(
    team_id: str,
    request: TeamRunRequest,
    background_tasks: BackgroundTasks,
    orchestrator = Depends(get_orchestrator),
    state = Depends(get_state)
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
async def list_agents_compat(state = Depends(get_state)) -> TeamListResponse:
    """Agno-compatible alias for team listing."""
    return await list_teams(state=state)

@router.post("/run/team", response_model=TeamExecutionResponse, include_in_schema=False)
async def run_team_compat(
    request: TeamRunRequest,
    background_tasks: BackgroundTasks,
    orchestrator = Depends(get_orchestrator),
    state = Depends(get_state)
) -> TeamExecutionResponse:
    """Agno-compatible alias for team execution."""
    return await run_team(request, background_tasks, orchestrator, state)