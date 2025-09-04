"""
Sophia Intel AI Agent Factory System

A comprehensive agent and swarm management system providing:
- Pre-built specialized agent blueprints
- Dynamic swarm orchestration  
- Performance tracking and analytics
- Integration with Portkey and existing infrastructure
- Production-ready agent lifecycle management

Usage:
    from app.agents import get_factory, create_quick_agent, create_quick_swarm
    
    # Get factory instance
    factory = await get_factory()
    
    # Create an agent
    agent = await create_quick_agent("senior_developer")
    
    # Execute a task
    result = await factory.execute_agent_task(
        agent.instance_id,
        "Write a Python function to calculate fibonacci numbers"
    )
    
    # Create a swarm for complex tasks
    swarm = await create_quick_swarm("software_development")
    result = await factory.execute_swarm_task(
        swarm.instance_id, 
        "Build a REST API for user management"
    )
"""

from .agent_factory import (
    AgentFactory,
    AgentFactoryError,
    AgentCreationError,
    SwarmCreationError,
    ResourceLimitError,
    get_factory,
    create_quick_agent,
    create_quick_swarm,
    execute_quick_task
)

from .agent_catalog import (
    AgentCatalog,
    get_catalog,
    get_blueprint,
    get_swarm_config,
    list_blueprints,
    list_swarm_configs
)

from .models import (
    # Enums
    AgentStatus,
    SwarmStatus,
    AgentTier,
    TaskType,
    
    # Core Models
    AgentBlueprint,
    AgentInstance,
    SwarmConfiguration,
    SwarmInstance,
    SwarmMembership,
    
    # Metrics
    AgentMetrics,
    SwarmMetrics,
    FactoryUsage,
    
    # Utilities
    create_tables,
    get_model_config_dict,
    dict_to_model_config
)

__version__ = "2.1.0"

__all__ = [
    # Factory classes
    "AgentFactory",
    "AgentCatalog",
    
    # Exceptions
    "AgentFactoryError",
    "AgentCreationError", 
    "SwarmCreationError",
    "ResourceLimitError",
    
    # Factory functions
    "get_factory",
    "create_quick_agent",
    "create_quick_swarm", 
    "execute_quick_task",
    
    # Catalog functions
    "get_catalog",
    "get_blueprint",
    "get_swarm_config",
    "list_blueprints",
    "list_swarm_configs",
    
    # Enums
    "AgentStatus",
    "SwarmStatus",
    "AgentTier",
    "TaskType",
    
    # Models
    "AgentBlueprint",
    "AgentInstance",
    "SwarmConfiguration",
    "SwarmInstance",
    "SwarmMembership",
    "AgentMetrics",
    "SwarmMetrics",
    "FactoryUsage",
    
    # Utilities
    "create_tables",
    "get_model_config_dict",
    "dict_to_model_config"
]

# Module metadata
__author__ = "Sophia Intel AI"
__description__ = "Production-ready AI Agent Factory and Swarm Orchestration System"
__license__ = "MIT"