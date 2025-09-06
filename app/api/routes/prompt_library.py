"""
FastAPI routes for Prompt Library management
Comprehensive API for prompt CRUD, version control, and A/B testing
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.prompts.mythology_prompts import (
    BusinessContext,
    MythologyAgent,
    MythologyPromptManager,
    TechnicalAgent,
)
from app.prompts.prompt_library import (
    ABTestConfig,
    ABTestResult,
    MergeStrategy,
    PromptBranch,
    PromptDiff,
    PromptLibrary,
    PromptMetadata,
    PromptStatus,
    PromptType,
    PromptVersion,
)

logger = logging.getLogger(__name__)

# Initialize global prompt library and manager
prompt_library = PromptLibrary()
mythology_manager = MythologyPromptManager(prompt_library)

router = APIRouter(prefix="/api/v1/prompts", tags=["Prompt Library"])


# Pydantic models for API requests/responses
class PromptCreateRequest(BaseModel):
    prompt_id: str = Field(..., description="Unique identifier for the prompt")
    content: str = Field(..., description="Prompt content")
    domain: str = Field(..., description="Domain (sophia, artemis)")
    agent_name: Optional[str] = Field(None, description="Agent name")
    task_type: Optional[str] = Field(None, description="Task type")
    business_context: Optional[List[str]] = Field(None, description="Business contexts")
    performance_tags: Optional[List[str]] = Field(None, description="Performance tags")
    branch: str = Field("main", description="Branch name")
    commit_message: Optional[str] = Field(None, description="Commit message")


class PromptUpdateRequest(BaseModel):
    content: str = Field(..., description="Updated prompt content")
    commit_message: Optional[str] = Field(None, description="Commit message")
    branch: str = Field("main", description="Branch name")


class BranchCreateRequest(BaseModel):
    branch_name: str = Field(..., description="New branch name")
    from_branch: str = Field("main", description="Source branch")
    description: Optional[str] = Field(None, description="Branch description")


class MergeRequest(BaseModel):
    from_branch: str = Field(..., description="Source branch")
    to_branch: str = Field("main", description="Target branch")
    strategy: MergeStrategy = Field(MergeStrategy.FAST_FORWARD, description="Merge strategy")
    commit_message: Optional[str] = Field(None, description="Commit message")


class ABTestCreateRequest(BaseModel):
    name: str = Field(..., description="A/B test name")
    description: str = Field(..., description="Test description")
    control_version: str = Field(..., description="Control version ID")
    test_versions: List[str] = Field(..., description="Test version IDs")
    traffic_split: Dict[str, float] = Field(..., description="Traffic split percentages")
    success_metrics: List[str] = Field(..., description="Success metrics to track")
    end_time: Optional[datetime] = Field(None, description="Test end time")
    minimum_sample_size: int = Field(100, description="Minimum sample size")


class ABTestResultRequest(BaseModel):
    version_id: str = Field(..., description="Version ID")
    success: bool = Field(..., description="Whether interaction was successful")
    metrics: Optional[Dict[str, float]] = Field(None, description="Additional metrics")


class SearchRequest(BaseModel):
    query: Optional[str] = Field("", description="Search query")
    domain: Optional[str] = Field(None, description="Filter by domain")
    agent_name: Optional[str] = Field(None, description="Filter by agent name")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    limit: int = Field(50, description="Maximum results")


class PromptResponse(BaseModel):
    """Response model for prompt data"""

    id: str
    prompt_id: str
    branch: str
    version: str
    content: str
    metadata: Dict[str, Any]
    status: str
    created_at: datetime
    performance_metrics: Optional[Dict[str, float]] = None
    a_b_test_data: Optional[Dict[str, Any]] = None


class BranchResponse(BaseModel):
    """Response model for branch data"""

    name: str
    base_version: str
    head_version: str
    created_at: datetime
    description: Optional[str] = None
    is_merged: bool = False
    merged_at: Optional[datetime] = None


class DiffResponse(BaseModel):
    """Response model for diff data"""

    from_version: str
    to_version: str
    content_diff: List[str]
    metadata_diff: Dict[str, Any]
    similarity_score: float
    change_summary: str


def convert_prompt_to_response(prompt: PromptVersion) -> PromptResponse:
    """Convert PromptVersion to response model"""
    return PromptResponse(
        id=prompt.id,
        prompt_id=prompt.prompt_id,
        branch=prompt.branch,
        version=prompt.version,
        content=prompt.content,
        metadata=prompt.metadata.__dict__,
        status=prompt.status.value,
        created_at=prompt.created_at,
        performance_metrics=prompt.performance_metrics,
        a_b_test_data=prompt.a_b_test_data,
    )


def convert_branch_to_response(branch: PromptBranch) -> BranchResponse:
    """Convert PromptBranch to response model"""
    return BranchResponse(
        name=branch.name,
        base_version=branch.base_version,
        head_version=branch.head_version,
        created_at=branch.created_at,
        description=branch.description,
        is_merged=branch.is_merged,
        merged_at=branch.merged_at,
    )


# CRUD Operations
@router.post("/create", response_model=PromptResponse)
async def create_prompt(request: PromptCreateRequest):
    """Create a new prompt or add version to existing prompt"""
    try:
        metadata = PromptMetadata(
            domain=request.domain,
            agent_name=request.agent_name,
            task_type=request.task_type,
            business_context=request.business_context,
            performance_tags=request.performance_tags,
            author="api_user",
        )

        prompt_version = prompt_library.create_prompt(
            prompt_id=request.prompt_id,
            content=request.content,
            metadata=metadata,
            branch=request.branch,
            commit_message=request.commit_message,
        )

        return convert_prompt_to_response(prompt_version)

    except Exception as e:
        logger.error(f"Error creating prompt: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{prompt_id}/update", response_model=PromptResponse)
async def update_prompt(prompt_id: str, request: PromptUpdateRequest):
    """Update an existing prompt (creates new version)"""
    try:
        # Get existing prompt metadata
        existing_versions = prompt_library.get_prompt_history(prompt_id)
        if not existing_versions:
            raise HTTPException(status_code=404, detail="Prompt not found")

        latest_version = existing_versions[0]

        # Create new version
        prompt_version = prompt_library.create_prompt(
            prompt_id=prompt_id,
            content=request.content,
            metadata=latest_version.metadata,
            branch=request.branch,
            commit_message=request.commit_message,
        )

        return convert_prompt_to_response(prompt_version)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating prompt: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: str, branch: str = "main", version: Optional[str] = None):
    """Get a specific prompt version"""
    try:
        versions = prompt_library.get_prompt_history(prompt_id, branch)
        if not versions:
            raise HTTPException(status_code=404, detail="Prompt not found")

        if version:
            # Find specific version
            target_version = None
            for v in versions:
                if v.version == version:
                    target_version = v
                    break

            if not target_version:
                raise HTTPException(status_code=404, detail="Version not found")
        else:
            # Get latest version
            target_version = versions[0]

        return convert_prompt_to_response(target_version)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prompt: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{prompt_id}/history", response_model=List[PromptResponse])
async def get_prompt_history(prompt_id: str, branch: Optional[str] = None):
    """Get version history for a prompt"""
    try:
        versions = prompt_library.get_prompt_history(prompt_id, branch)
        return [convert_prompt_to_response(v) for v in versions]

    except Exception as e:
        logger.error(f"Error getting prompt history: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: str):
    """Delete a prompt (marks as archived)"""
    try:
        versions = prompt_library.get_prompt_history(prompt_id)
        if not versions:
            raise HTTPException(status_code=404, detail="Prompt not found")

        # Mark all versions as archived
        for version in versions:
            version.status = PromptStatus.ARCHIVED

        prompt_library._save_to_storage()
        return {"message": f"Prompt {prompt_id} archived successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting prompt: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Branch Management
@router.post("/{prompt_id}/branches", response_model=BranchResponse)
async def create_branch(prompt_id: str, request: BranchCreateRequest):
    """Create a new branch for a prompt"""
    try:
        branch = prompt_library.create_branch(
            prompt_id=prompt_id,
            branch_name=request.branch_name,
            from_branch=request.from_branch,
            description=request.description,
        )

        return convert_branch_to_response(branch)

    except Exception as e:
        logger.error(f"Error creating branch: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{prompt_id}/branches", response_model=List[BranchResponse])
async def get_branches(prompt_id: str):
    """Get all branches for a prompt"""
    try:
        branches = prompt_library.get_branches(prompt_id)
        return [convert_branch_to_response(b) for b in branches]

    except Exception as e:
        logger.error(f"Error getting branches: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{prompt_id}/merge", response_model=PromptResponse)
async def merge_branch(prompt_id: str, request: MergeRequest):
    """Merge one branch into another"""
    try:
        merged_version = prompt_library.merge_branch(
            prompt_id=prompt_id,
            from_branch=request.from_branch,
            to_branch=request.to_branch,
            strategy=request.strategy,
            commit_message=request.commit_message,
        )

        return convert_prompt_to_response(merged_version)

    except Exception as e:
        logger.error(f"Error merging branch: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Diff Operations
@router.get("/{prompt_id}/diff", response_model=DiffResponse)
async def diff_versions(prompt_id: str, from_version: str, to_version: str):
    """Get diff between two versions"""
    try:
        diff = prompt_library.diff_versions(prompt_id, from_version, to_version)
        return DiffResponse(
            from_version=diff.from_version,
            to_version=diff.to_version,
            content_diff=diff.content_diff,
            metadata_diff=diff.metadata_diff,
            similarity_score=diff.similarity_score,
            change_summary=diff.change_summary,
        )

    except Exception as e:
        logger.error(f"Error generating diff: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Search and Discovery
@router.post("/search", response_model=List[PromptResponse])
async def search_prompts(request: SearchRequest):
    """Search prompts with filters"""
    try:
        results = prompt_library.search_prompts(
            query=request.query,
            domain=request.domain,
            agent_name=request.agent_name,
            tags=request.tags,
        )

        # Limit results
        results = results[: request.limit]

        return [convert_prompt_to_response(r) for r in results]

    except Exception as e:
        logger.error(f"Error searching prompts: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agents", response_model=Dict[str, List[str]])
async def get_available_agents():
    """Get list of available mythology and technical agents"""
    try:
        return {
            "mythology_agents": [agent.value for agent in MythologyAgent],
            "technical_agents": [agent.value for agent in TechnicalAgent],
            "business_contexts": [context.value for context in BusinessContext],
        }

    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# A/B Testing
@router.post("/ab-tests", response_model=Dict[str, str])
async def create_ab_test(request: ABTestCreateRequest):
    """Create a new A/B test"""
    try:
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        config = ABTestConfig(
            test_id=test_id,
            name=request.name,
            description=request.description,
            control_version=request.control_version,
            test_versions=request.test_versions,
            traffic_split=request.traffic_split,
            success_metrics=request.success_metrics,
            start_time=datetime.now(timezone.utc),
            end_time=request.end_time,
            minimum_sample_size=request.minimum_sample_size,
        )

        prompt_library.start_ab_test(config)
        return {"test_id": test_id, "message": "A/B test created successfully"}

    except Exception as e:
        logger.error(f"Error creating A/B test: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ab-tests/{test_id}/results")
async def record_ab_test_result(test_id: str, request: ABTestResultRequest):
    """Record an A/B test result"""
    try:
        prompt_library.record_ab_test_result(
            test_id=test_id,
            version_id=request.version_id,
            success=request.success,
            metrics=request.metrics,
        )

        return {"message": "Result recorded successfully"}

    except Exception as e:
        logger.error(f"Error recording A/B test result: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ab-tests/{test_id}/results", response_model=Dict[str, Any])
async def get_ab_test_results(test_id: str):
    """Get A/B test results"""
    try:
        results = prompt_library.get_ab_test_results(test_id)

        # Convert results to serializable format
        serializable_results = {}
        for version_id, result in results.items():
            serializable_results[version_id] = {
                "test_id": result.test_id,
                "version_id": result.version_id,
                "sample_size": result.sample_size,
                "success_rate": result.success_rate,
                "confidence_interval": result.confidence_interval,
                "metrics": result.metrics,
                "statistical_significance": result.statistical_significance,
                "winner": result.winner,
            }

        return {"test_id": test_id, "results": serializable_results}

    except Exception as e:
        logger.error(f"Error getting A/B test results: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ab-tests", response_model=List[Dict[str, Any]])
async def get_active_ab_tests():
    """Get list of active A/B tests"""
    try:
        active_tests = []
        for test_id, config in prompt_library.ab_tests.items():
            if config.status == "active":
                active_tests.append(
                    {
                        "test_id": test_id,
                        "name": config.name,
                        "description": config.description,
                        "start_time": config.start_time.isoformat(),
                        "end_time": config.end_time.isoformat() if config.end_time else None,
                        "traffic_split": config.traffic_split,
                        "success_metrics": config.success_metrics,
                    }
                )

        return active_tests

    except Exception as e:
        logger.error(f"Error getting active A/B tests: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Performance Analytics
@router.post("/{version_id}/metrics")
async def update_performance_metrics(version_id: str, metrics: Dict[str, float] = Body(...)):
    """Update performance metrics for a prompt version"""
    try:
        prompt_library.update_performance_metrics(version_id, metrics)
        return {"message": "Metrics updated successfully"}

    except Exception as e:
        logger.error(f"Error updating metrics: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/performance/leaderboard")
async def get_performance_leaderboard(
    domain: Optional[str] = Query(None, description="Filter by domain"),
    metric: str = Query("success_rate", description="Metric to rank by"),
    limit: int = Query(10, description="Number of results"),
):
    """Get performance leaderboard"""
    try:
        leaderboard = prompt_library.get_performance_leaderboard(domain, metric, limit)

        results = []
        for prompt_version, score in leaderboard:
            results.append(
                {
                    "prompt_id": prompt_version.prompt_id,
                    "version_id": prompt_version.id,
                    "agent_name": prompt_version.metadata.agent_name,
                    "domain": prompt_version.metadata.domain,
                    "task_type": prompt_version.metadata.task_type,
                    "score": score,
                    "business_contexts": prompt_version.metadata.business_context,
                    "performance_tags": prompt_version.metadata.performance_tags,
                }
            )

        return results

    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Mythology-specific endpoints
@router.get("/mythology/{agent_name}/context/{business_context}")
async def get_context_prompt(agent_name: str, business_context: str, task_type: str = Query(...)):
    """Get context-aware prompt for mythology agent"""
    try:
        context_enum = BusinessContext(business_context)
        prompt_content = mythology_manager.get_prompt_for_context(
            agent_name=agent_name, task_type=task_type, business_context=context_enum
        )

        if not prompt_content:
            raise HTTPException(status_code=404, detail="Prompt not found for context")

        return {
            "agent_name": agent_name,
            "business_context": business_context,
            "task_type": task_type,
            "prompt_content": prompt_content,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid business context: {business_context}")
    except Exception as e:
        logger.error(f"Error getting context prompt: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mythology/{prompt_id}/context-variant")
async def create_context_variant(
    prompt_id: str,
    business_context: str = Body(...),
    context_modifications: str = Body(...),
    commit_message: Optional[str] = Body(None),
):
    """Create business context-specific variant"""
    try:
        context_enum = BusinessContext(business_context)
        variant_id = mythology_manager.create_business_context_variant(
            base_prompt_id=prompt_id,
            business_context=context_enum,
            context_modifications=context_modifications,
            commit_message=commit_message,
        )

        return {
            "variant_id": variant_id,
            "message": f"Context variant created for {business_context}",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid business context: {business_context}")
    except Exception as e:
        logger.error(f"Error creating context variant: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/mythology/performance/{agent_name}")
async def get_mythology_performance(agent_name: Optional[str] = None):
    """Get performance insights for mythology agents"""
    try:
        insights = mythology_manager.get_performance_insights(agent_name)
        return insights

    except Exception as e:
        logger.error(f"Error getting performance insights: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/mythology/{prompt_id}/suggestions")
async def get_optimization_suggestions(prompt_id: str):
    """Get optimization suggestions for a prompt"""
    try:
        suggestions = mythology_manager.suggest_optimizations(prompt_id)
        return {"prompt_id": prompt_id, "suggestions": suggestions}

    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Export/Import
@router.get("/export")
async def export_prompts(prompt_ids: Optional[List[str]] = Query(None)):
    """Export prompts to portable format"""
    try:
        export_data = prompt_library.export_prompts(prompt_ids)
        return export_data

    except Exception as e:
        logger.error(f"Error exporting prompts: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import")
async def import_prompts(import_data: Dict[str, Any] = Body(...), overwrite: bool = Body(False)):
    """Import prompts from exported data"""
    try:
        prompt_library.import_prompts(import_data, overwrite)
        return {"message": "Prompts imported successfully"}

    except Exception as e:
        logger.error(f"Error importing prompts: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Health Check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        prompt_count = sum(len(versions) for versions in prompt_library.prompts.values())
        branch_count = sum(len(branches) for branches in prompt_library.branches.values())
        ab_test_count = len(prompt_library.ab_tests)

        return {
            "status": "healthy",
            "prompt_versions": prompt_count,
            "branches": branch_count,
            "active_ab_tests": ab_test_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")
