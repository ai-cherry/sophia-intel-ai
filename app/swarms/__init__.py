"""Swarm orchestration package."""

from app.core.super_orchestrator import get_orchestrator


# Compatibility wrapper for legacy code
class SwarmOrchestrator:
    """Compatibility wrapper for SuperOrchestrator"""
    def __init__(self, team=None, config=None, memory=None):
        self.team = team
        self.config = config
        self.memory = memory
        self.orchestrator = get_orchestrator()

    async def run_debate(self, task, context=None):
        """Run debate using SuperOrchestrator"""
        from app.swarms.coding.models import DebateResult

        # Process through SuperOrchestrator
        request = {
            "type": "swarm_execution",
            "task": task,
            "team": self.team,
            "config": self.config,
            "context": context or {}
        }

        result = await self.orchestrator.process_request(request)

        # Convert to DebateResult format
        return DebateResult(
            messages=result.get("messages", []),
            runner_approved=result.get("approved", True),
            errors=result.get("errors", []),
            execution_time_ms=result.get("duration_ms", 0),
            usage_stats=result.get("usage", {}),
            memory_operations=result.get("memory_ops", 0)
        )

# Alias for compatibility
UnifiedSwarmOrchestrator = SwarmOrchestrator

__all__ = ["SwarmOrchestrator", "UnifiedSwarmOrchestrator", "get_orchestrator"]
