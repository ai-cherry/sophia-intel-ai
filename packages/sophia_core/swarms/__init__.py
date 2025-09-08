"""
Swarms Module

Provides base interfaces and implementations for AI agent swarms,
including swarm coordination, task distribution, and collective intelligence.
"""

from .base import (
    BaseSwarm,
    SwarmState,
    SwarmConfig,
    SwarmTopology,
    SwarmRole,
    SwarmMember,
    SwarmTask,
    SwarmMessage,
    SwarmCoordinator,
    SwarmExecutor,
    HierarchicalSwarm,
    PeerToPeerSwarm,
    SwarmRegistry,
    SwarmError,
    SwarmInitializationError,
    SwarmCoordinationError
)

__all__ = [
    # Base swarm interfaces
    "BaseSwarm",
    "SwarmCoordinator",
    "SwarmExecutor",
    
    # Swarm types
    "HierarchicalSwarm",
    "PeerToPeerSwarm",
    
    # Swarm configuration
    "SwarmState",
    "SwarmConfig", 
    "SwarmTopology",
    "SwarmRole",
    
    # Swarm components
    "SwarmMember",
    "SwarmTask",
    "SwarmMessage",
    
    # Swarm management
    "SwarmRegistry",
    
    # Exceptions
    "SwarmError",
    "SwarmInitializationError",
    "SwarmCoordinationError"
]