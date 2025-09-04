"""
Swarm orchestration package with MANDATORY parallel execution.

CORE RULE: All swarms MUST use unique virtual keys per agent for true parallelism.
This is automatically enforced on import.
"""

import logging
from app.core.super_orchestrator import get_orchestrator

# Import and enforce parallel execution
from app.swarms.core.parallel_config import ParallelEnforcer, VirtualKeyPool

logger = logging.getLogger(__name__)

# =============================================================================
# ENFORCE PARALLEL EXECUTION ON IMPORT
# =============================================================================

# Enable parallel execution globally
ParallelEnforcer.enable()
logger.info(
    "⚡ PARALLEL EXECUTION ENFORCED: All swarms will use unique virtual keys per agent"
)

# Enhanced compatibility wrapper that uses parallel execution
class SwarmOrchestrator:
    """
    Enhanced orchestrator with AUTOMATIC parallel execution.
    
    This wrapper ensures ALL swarms use unique virtual keys per agent.
    """
    def __init__(self, team=None, config=None, memory=None):
        self.team = team
        self.config = config
        self.memory = memory
        self.orchestrator = get_orchestrator()
        
        # ENFORCE parallel configuration
        agent_count = len(team.members) if hasattr(team, 'members') else 4
        self.parallel_config = ParallelEnforcer.enforce_for_swarm(
            swarm_id=f"swarm_{id(self)}",
            agent_count=agent_count
        )
        
        logger.info(
            f"✅ SwarmOrchestrator initialized with {agent_count} unique virtual keys"
        )

    async def run_debate(self, task, context=None):
        """Run debate with parallel execution"""
        from app.swarms.coding.models import DebateResult

        # Process through SuperOrchestrator with parallel config
        request = {
            "type": "swarm_execution",
            "task": task,
            "team": self.team,
            "config": self.config,
            "context": context or {},
            "parallel_config": self.parallel_config.virtual_key_allocation
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

# Log system status
all_keys = VirtualKeyPool.get_all_keys()
logger.info(
    f"🚀 SWARM SYSTEM READY: {len(all_keys)} virtual keys available for parallel execution"
)

__all__ = ["SwarmOrchestrator", "UnifiedSwarmOrchestrator", "get_orchestrator", "ParallelEnforcer"]
