"""
SOPHIA Intel Multi-Agent Swarm System
Phase 4 of V4 Mega Upgrade - Real Implementation

Multi-agent orchestration using Phidata 0.3.0+ with specialized agents
for different aspects of autonomous operations.
"""

from .swarm_coordinator import SwarmCoordinator
from .research_agent import ResearchAgent
from .coding_agent import CodingAgent
from .deployment_agent import DeploymentAgent
from .monitoring_agent import MonitoringAgent

__all__ = [
    'SwarmCoordinator',
    'ResearchAgent', 
    'CodingAgent',
    'DeploymentAgent',
    'MonitoringAgent'
]
