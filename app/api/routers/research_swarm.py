"""
Research Swarm API Router
==========================
API endpoints for deploying and managing the orchestrator research swarm.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.artemis.agent_factory import artemis_factory
from app.swarms.orchestrator_research_swarm import (
    OrchestratorResearchSwarm,
    ResearchArea,
    deploy_orchestrator_research_swarm,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research-swarm", tags=["research_swarm"])

# Global swarm instance
research_swarm: Optional[OrchestratorResearchSwarm] = None
research_results: dict[str, Any] = {}
research_status: dict[str, Any] = {
    "deployed": False,
    "researching": False,
    "last_research": None,
    "findings_count": 0,
}


@router.post("/deploy")
async def deploy_swarm() -> dict[str, Any]:
    """
    Deploy the orchestrator research swarm
    """
    global research_swarm, research_status

    try:
        if research_swarm and research_status["deployed"]:
            return {
                "status": "already_deployed",
                "message": "Research swarm is already deployed",
                "agents": (
                    list(research_swarm.research_agents.keys())
                    if research_swarm
                    else []
                ),
            }

        logger.info("🚀 Deploying orchestrator research swarm...")
        research_swarm = await deploy_orchestrator_research_swarm()

        research_status["deployed"] = True
        research_status["deployment_time"] = datetime.now().isoformat()

        return {
            "status": "success",
            "message": "Orchestrator research swarm deployed successfully",
            "agents": list(research_swarm.research_agents.keys()),
            "capabilities": [
                "Web research on AI orchestration",
                "Pattern analysis",
                "Architecture design",
                "Implementation planning",
                "Testing strategy",
            ],
            "research_areas": [area.value for area in ResearchArea],
        }

    except Exception as e:
        logger.error(f"Failed to deploy research swarm: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to deploy research swarm: {str(e)}"
        )


@router.post("/research/start")
async def start_research(background_tasks: BackgroundTasks) -> dict[str, Any]:
    """
    Start comprehensive research on orchestrator improvements
    """
    global research_swarm, research_status

    if not research_swarm or not research_status["deployed"]:
        raise HTTPException(
            status_code=400,
            detail="Research swarm not deployed. Deploy it first with /deploy",
        )

    if research_status["researching"]:
        return {
            "status": "already_running",
            "message": "Research is already in progress",
            "started_at": research_status.get("research_started"),
        }

    # Start research in background
    research_status["researching"] = True
    research_status["research_started"] = datetime.now().isoformat()

    background_tasks.add_task(run_research_task)

    return {
        "status": "started",
        "message": "Research started in background",
        "research_areas": [area.value for area in ResearchArea],
        "estimated_time": "5-10 minutes",
        "check_status_at": "/api/research-swarm/research/status",
    }


async def run_research_task():
    """
    Background task to run research
    """
    global research_swarm, research_results, research_status

    try:
        logger.info("🔍 Starting orchestrator improvement research...")

        # Conduct research
        results = await research_swarm.conduct_research()

        # Store results
        research_results = {
            "timestamp": datetime.now().isoformat(),
            "findings": results.get("research_findings", []),
            "analysis": results.get("analysis", {}),
            "improvement_plans": results.get("improvement_plans", {}),
            "implementation": results.get("implementation", {}),
            "summary": results.get("summary", ""),
        }

        research_status["researching"] = False
        research_status["last_research"] = datetime.now().isoformat()
        research_status["findings_count"] = len(results.get("research_findings", []))
        research_status["research_completed"] = True

        logger.info(
            f"✅ Research completed with {research_status['findings_count']} findings"
        )

    except Exception as e:
        logger.error(f"Research failed: {str(e)}")
        research_status["researching"] = False
        research_status["error"] = str(e)


@router.get("/research/status")
async def get_research_status() -> dict[str, Any]:
    """
    Get current research status
    """
    global research_status, research_results

    if not research_status["deployed"]:
        return {"status": "not_deployed", "message": "Research swarm not deployed"}

    response = {
        "deployed": research_status["deployed"],
        "researching": research_status["researching"],
        "last_research": research_status.get("last_research"),
        "findings_count": research_status.get("findings_count", 0),
    }

    if research_status.get("research_completed"):
        response["completed"] = True
        response["summary"] = research_results.get("summary", "")
        response["has_results"] = True

    if research_status.get("error"):
        response["error"] = research_status["error"]

    return response


@router.get("/research/results")
async def get_research_results() -> dict[str, Any]:
    """
    Get research results
    """
    global research_results

    if not research_results:
        raise HTTPException(
            status_code=404,
            detail="No research results available. Start research first.",
        )

    return research_results


@router.get("/research/improvements/sophia")
async def get_sophia_improvements() -> dict[str, Any]:
    """
    Get proposed improvements for Sophia orchestrator
    """
    global research_results

    if not research_results:
        raise HTTPException(
            status_code=404,
            detail="No research results available. Start research first.",
        )

    sophia_plan = research_results.get("improvement_plans", {}).get("sophia")

    if not sophia_plan:
        return {
            "status": "no_plan",
            "message": "No improvement plan available for Sophia yet",
        }

    return {
        "orchestrator": "sophia",
        "plan": sophia_plan,
        "quick_wins": research_results.get("analysis", {}).get("quick_wins", []),
        "implementation": research_results.get("implementation", {}),
    }


@router.get("/research/improvements/artemis")
async def get_artemis_improvements() -> dict[str, Any]:
    """
    Get proposed improvements for Artemis orchestrator
    """
    global research_results

    if not research_results:
        raise HTTPException(
            status_code=404,
            detail="No research results available. Start research first.",
        )

    artemis_plan = research_results.get("improvement_plans", {}).get("artemis")

    if not artemis_plan:
        return {
            "status": "no_plan",
            "message": "No improvement plan available for Artemis yet",
        }

    return {
        "orchestrator": "artemis",
        "plan": artemis_plan,
        "quick_wins": research_results.get("analysis", {}).get("quick_wins", []),
        "implementation": research_results.get("implementation", {}),
    }


@router.post("/implement/approve")
async def approve_implementation(
    orchestrator: str, phase: Optional[str] = "quick_wins"
) -> dict[str, Any]:
    """
    Approve implementation of improvements

    Args:
        orchestrator: "sophia" or "artemis" or "both"
        phase: "quick_wins", "phase_1", "phase_2", or "all"
    """
    global research_swarm, research_results

    if not research_swarm:
        raise HTTPException(status_code=400, detail="Research swarm not deployed")

    if not research_results:
        raise HTTPException(
            status_code=400,
            detail="No research results available. Complete research first.",
        )

    # In a real implementation, this would trigger actual code changes
    # For now, we'll return a plan

    return {
        "status": "approval_recorded",
        "orchestrator": orchestrator,
        "phase": phase,
        "message": "Implementation approval recorded. Review implementation plan.",
        "next_steps": [
            "Review generated code changes",
            "Run tests",
            "Deploy to development",
            "Monitor performance",
            "Rollback if issues",
        ],
        "implementation_ready": True,
    }


@router.post("/test/improvements")
async def test_improvements(test_type: str = "unit") -> dict[str, Any]:
    """
    Test proposed improvements

    Args:
        test_type: "unit", "integration", "performance", or "all"
    """
    global research_results

    if not research_results:
        raise HTTPException(
            status_code=400, detail="No improvements to test. Complete research first."
        )

    # This would run actual tests
    # For now, return test plan

    testing_strategy = research_results.get("implementation", {}).get("testing", {})

    return {
        "status": "test_plan_ready",
        "test_type": test_type,
        "testing_strategy": testing_strategy,
        "test_categories": [
            "Unit tests for new components",
            "Integration tests for orchestrators",
            "Performance benchmarks",
            "A/B testing",
            "Validation metrics",
        ],
        "ready_to_test": True,
    }


@router.get("/factory/status")
async def get_factory_integration_status() -> dict[str, Any]:
    """
    Get status of factory integration
    """
    global research_swarm

    if not research_swarm:
        return {"integrated": False, "message": "Research swarm not deployed"}

    # Check if integrated with Artemis factory
    try:
        factory_swarms = await artemis_factory.list_swarms()
        integrated = any(
            s.get("name") == "Orchestrator Research Swarm" for s in factory_swarms
        )

        return {
            "integrated": integrated,
            "factory": "artemis",
            "swarm_name": "Orchestrator Research Swarm",
            "agents_available": (
                list(research_swarm.research_agents.keys()) if research_swarm else []
            ),
        }
    except Exception:return {"integrated": False, "error": "Could not check factory integration"}


@router.delete("/shutdown")
async def shutdown_swarm() -> dict[str, Any]:
    """
    Shutdown the research swarm
    """
    global research_swarm, research_status, research_results

    if not research_swarm:
        return {"status": "not_deployed", "message": "No swarm to shutdown"}

    # Clean up
    research_swarm = None
    research_status = {
        "deployed": False,
        "researching": False,
        "last_research": research_status.get("last_research"),
        "findings_count": research_status.get("findings_count", 0),
    }

    return {
        "status": "shutdown_complete",
        "message": "Research swarm shutdown successfully",
        "results_preserved": bool(research_results),
    }
