# Auto-added by pre-commit hook
import sys, os
try:
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    from core.environment_enforcer import enforce_environment
    enforce_environment()
except ImportError:
    pass  # Environment enforcer not available

"""
Artemis Swarm - 5-Agent Coding Intelligence System

A revolutionary coding swarm featuring:
- Planner: Intent decomposition using Semantic Kernel v1.35.0
- Coder: Code generation with zkML proofs
- Tester: Comprehensive testing with pytest/mypy
- Deployer: Pulumi deployment to Lambda GPU clusters  
- Evolver: Self-improvement with Mem0 v2 memory graphs

Built on CrewAI v0.152.0 and LangGraph v0.6.0 for advanced orchestration.
"""

from .swarm_orchestrator import ArtemisSwarm
from .agents.planner_agent import PlannerAgent
from .agents.coder_agent import CoderAgent
from .agents.tester_agent import TesterAgent
from .agents.deployer_agent import DeployerAgent
from .agents.evolver_agent import EvolverAgent

__version__ = "2.0.0"
__all__ = [
    "ArtemisSwarm",
    "PlannerAgent", 
    "CoderAgent",
    "TesterAgent",
    "DeployerAgent",
    "EvolverAgent"
]
