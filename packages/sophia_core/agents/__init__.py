"""
Agents Module

Provides base interfaces and implementations for AI agents,
including agent lifecycle, behavior, and interaction patterns.
"""

from .base import (
    BaseAgent,
    AgentState,
    AgentCapabilities,
    AgentConfig,
    AgentMessage,
    AgentResponse,
    AgentContext,
    AgentGoal,
    AgentTask,
    TaskStatus,
    ConversationalAgent,
    ReactiveTool,
    ProactiveAgent,
    AgentRegistry,
    AgentError,
    AgentInitializationError,
    AgentExecutionError
)

__all__ = [
    # Base agent interfaces
    "BaseAgent",
    "ConversationalAgent",
    "ReactiveTool", 
    "ProactiveAgent",
    
    # Agent configuration
    "AgentState",
    "AgentCapabilities",
    "AgentConfig",
    "AgentContext",
    
    # Agent communication
    "AgentMessage",
    "AgentResponse",
    
    # Task management
    "AgentGoal",
    "AgentTask",
    "TaskStatus",
    
    # Agent management
    "AgentRegistry",
    
    # Exceptions
    "AgentError",
    "AgentInitializationError",
    "AgentExecutionError"
]