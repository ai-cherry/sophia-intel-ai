"""
Database Models for Agent Factory System

SQLAlchemy models for managing agents, swarms, blueprints, and metrics.
Integrated with existing Sophia Intel AI architecture.
"""

import json
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.agent_config import ModelConfig

Base = declarative_base()


class AgentStatus(PyEnum):
    """Agent operational status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    FAILED = "failed"


class SwarmStatus(PyEnum):
    """Swarm operational status"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    COMPLETED = "completed"


class AgentTier(PyEnum):
    """Agent capability tiers"""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class TaskType(PyEnum):
    """Task types for agent specialization"""
    GENERAL = "general"
    CODING = "coding"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    SECURITY = "security"
    TESTING = "testing"
    PLANNING = "planning"
    REVIEW = "review"
    ORCHESTRATION = "orchestration"


# =============================================================================
# Core Agent Models
# =============================================================================

class AgentBlueprint(Base):
    """
    Agent blueprint defines agent capabilities and configuration templates.
    Used as templates for creating agent instances.
    """
    __tablename__ = "agent_blueprints"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Agent categorization
    category = Column(String(50), nullable=False, index=True)
    tier = Column(Enum(AgentTier), default=AgentTier.STANDARD, index=True)
    task_types = Column(JSON, nullable=False)  # List[TaskType]
    
    # Capabilities and configuration
    capabilities = Column(JSON, nullable=False)  # Dict of capabilities
    tools = Column(JSON, default=list)  # List of tool names
    guardrails = Column(JSON, default=list)  # List of safety rules
    
    # Model configuration
    model_config = Column(JSON, nullable=False)  # ModelConfig serialized
    system_prompt_template = Column(Text)
    
    # Resource requirements
    memory_mb = Column(Integer, default=512)
    cpu_cores = Column(Float, default=0.5)
    gpu_required = Column(Boolean, default=False)
    
    # Performance characteristics
    avg_response_time_ms = Column(Integer, default=1000)
    cost_per_1k_tokens = Column(Float, default=0.01)
    quality_score = Column(Float, default=7.5)  # 0-10 scale
    
    # Metadata
    version = Column(String(20), default="1.0.0")
    author = Column(String(100))
    tags = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=1.0)
    
    # Relationships
    instances = relationship("AgentInstance", back_populates="blueprint", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AgentBlueprint(name='{self.name}', tier='{self.tier}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "tier": self.tier.value,
            "task_types": self.task_types,
            "capabilities": self.capabilities,
            "tools": self.tools,
            "guardrails": self.guardrails,
            "model_config": self.model_config,
            "system_prompt_template": self.system_prompt_template,
            "version": self.version,
            "tags": self.tags,
            "performance": {
                "avg_response_time_ms": self.avg_response_time_ms,
                "cost_per_1k_tokens": self.cost_per_1k_tokens,
                "quality_score": self.quality_score,
                "success_rate": self.success_rate
            },
            "resources": {
                "memory_mb": self.memory_mb,
                "cpu_cores": self.cpu_cores,
                "gpu_required": self.gpu_required
            },
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class AgentInstance(Base):
    """
    Active agent instance created from a blueprint.
    Tracks runtime state and performance.
    """
    __tablename__ = "agent_instances"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    
    # Blueprint reference
    blueprint_id = Column(Integer, ForeignKey("agent_blueprints.id"), nullable=False)
    blueprint = relationship("AgentBlueprint", back_populates="instances")
    
    # Runtime state
    status = Column(Enum(AgentStatus), default=AgentStatus.ACTIVE, index=True)
    current_task_id = Column(String(100), index=True)
    
    # Configuration overrides
    config_overrides = Column(JSON, default=dict)  # Runtime configuration changes
    context = Column(JSON, default=dict)  # Agent context/memory
    
    # Performance tracking
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    avg_response_time_ms = Column(Integer, default=1000)
    
    # Resource usage
    cpu_usage_percent = Column(Float, default=0.0)
    memory_usage_mb = Column(Integer, default=0)
    last_heartbeat = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_active = Column(DateTime, default=func.now())
    
    # Relationships
    swarm_memberships = relationship("SwarmMembership", back_populates="agent")
    metrics = relationship("AgentMetrics", back_populates="agent", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AgentInstance(id='{self.instance_id}', status='{self.status}')>"
    
    @property
    def success_rate(self) -> float:
        """Calculate current success rate"""
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks == 0:
            return 1.0
        return self.tasks_completed / total_tasks
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "instance_id": self.instance_id,
            "name": self.name,
            "blueprint_id": self.blueprint_id,
            "status": self.status.value,
            "current_task_id": self.current_task_id,
            "config_overrides": self.config_overrides,
            "performance": {
                "tasks_completed": self.tasks_completed,
                "tasks_failed": self.tasks_failed,
                "success_rate": self.success_rate,
                "total_tokens_used": self.total_tokens_used,
                "total_cost": self.total_cost,
                "avg_response_time_ms": self.avg_response_time_ms
            },
            "resources": {
                "cpu_usage_percent": self.cpu_usage_percent,
                "memory_usage_mb": self.memory_usage_mb
            },
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }


# =============================================================================
# Swarm Models
# =============================================================================

class SwarmConfiguration(Base):
    """
    Swarm configuration template defining agent compositions and workflows.
    Used for creating standardized multi-agent setups.
    """
    __tablename__ = "swarm_configurations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Configuration details
    category = Column(String(50), nullable=False, index=True)
    use_case = Column(String(100), nullable=False)  # e.g., "software_development", "research"
    complexity_level = Column(String(20), default="medium")  # basic, medium, advanced
    
    # Agent composition
    agent_blueprints = Column(JSON, nullable=False)  # List of blueprint requirements
    min_agents = Column(Integer, default=2)
    max_agents = Column(Integer, default=10)
    
    # Workflow definition
    workflow_steps = Column(JSON, default=list)  # Workflow definition
    communication_pattern = Column(String(50), default="broadcast")  # broadcast, chain, mesh
    
    # Orchestration settings
    orchestration_model = Column(String(100))  # Model for orchestrator
    decision_strategy = Column(String(50), default="consensus")  # consensus, majority, leader
    
    # Performance characteristics
    estimated_duration_minutes = Column(Integer, default=30)
    estimated_cost = Column(Float, default=1.0)
    
    # Metadata
    version = Column(String(20), default="1.0.0")
    author = Column(String(100))
    tags = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=1.0)
    
    # Relationships
    instances = relationship("SwarmInstance", back_populates="configuration", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SwarmConfiguration(name='{self.name}', category='{self.category}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "use_case": self.use_case,
            "complexity_level": self.complexity_level,
            "agent_composition": {
                "agent_blueprints": self.agent_blueprints,
                "min_agents": self.min_agents,
                "max_agents": self.max_agents
            },
            "workflow": {
                "steps": self.workflow_steps,
                "communication_pattern": self.communication_pattern,
                "orchestration_model": self.orchestration_model,
                "decision_strategy": self.decision_strategy
            },
            "estimates": {
                "duration_minutes": self.estimated_duration_minutes,
                "cost": self.estimated_cost
            },
            "version": self.version,
            "tags": self.tags,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class SwarmInstance(Base):
    """
    Active swarm instance created from a configuration.
    Manages multiple agent instances working together.
    """
    __tablename__ = "swarm_instances"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    
    # Configuration reference
    configuration_id = Column(Integer, ForeignKey("swarm_configurations.id"), nullable=False)
    configuration = relationship("SwarmConfiguration", back_populates="instances")
    
    # Runtime state
    status = Column(Enum(SwarmStatus), default=SwarmStatus.INITIALIZING, index=True)
    current_task = Column(Text)
    progress_percent = Column(Float, default=0.0)
    
    # Execution context
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    intermediate_results = Column(JSON, default=dict)
    
    # Performance tracking
    tasks_completed = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    execution_time_seconds = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    last_activity = Column(DateTime, default=func.now())
    
    # Relationships
    memberships = relationship("SwarmMembership", back_populates="swarm", cascade="all, delete-orphan")
    metrics = relationship("SwarmMetrics", back_populates="swarm", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SwarmInstance(id='{self.instance_id}', status='{self.status}')>"
    
    @property
    def agent_count(self) -> int:
        """Get current number of agents in swarm"""
        return len(self.memberships)
    
    @property
    def active_agents(self) -> int:
        """Get number of currently active agents"""
        return sum(1 for m in self.memberships if m.agent.status == AgentStatus.ACTIVE)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "instance_id": self.instance_id,
            "name": self.name,
            "configuration_id": self.configuration_id,
            "status": self.status.value,
            "current_task": self.current_task,
            "progress_percent": self.progress_percent,
            "agents": {
                "total": self.agent_count,
                "active": self.active_agents
            },
            "performance": {
                "tasks_completed": self.tasks_completed,
                "total_tokens_used": self.total_tokens_used,
                "total_cost": self.total_cost,
                "execution_time_seconds": self.execution_time_seconds
            },
            "timestamps": {
                "created_at": self.created_at.isoformat(),
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "last_activity": self.last_activity.isoformat()
            },
            "data": {
                "input": self.input_data,
                "output": self.output_data,
                "intermediate": self.intermediate_results
            }
        }


class SwarmMembership(Base):
    """
    Junction table for swarm-agent relationships with role definitions.
    """
    __tablename__ = "swarm_memberships"
    __table_args__ = (
        UniqueConstraint("swarm_id", "agent_id", name="unique_swarm_agent"),
    )

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    swarm_id = Column(Integer, ForeignKey("swarm_instances.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agent_instances.id"), nullable=False)
    
    # Role in swarm
    role = Column(String(100), nullable=False)  # orchestrator, worker, reviewer, etc.
    priority = Column(Integer, default=1)  # execution priority
    
    # State
    joined_at = Column(DateTime, default=func.now(), nullable=False)
    left_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Performance within swarm
    tasks_assigned = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    contribution_score = Column(Float, default=0.0)
    
    # Relationships
    swarm = relationship("SwarmInstance", back_populates="memberships")
    agent = relationship("AgentInstance", back_populates="swarm_memberships")
    
    def __repr__(self):
        return f"<SwarmMembership(swarm={self.swarm_id}, agent={self.agent_id}, role='{self.role}')>"


# =============================================================================
# Metrics and Analytics
# =============================================================================

class AgentMetrics(Base):
    """
    Detailed performance metrics for agents over time.
    Used for analytics and optimization.
    """
    __tablename__ = "agent_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    agent_id = Column(Integer, ForeignKey("agent_instances.id"), nullable=False)
    agent = relationship("AgentInstance", back_populates="metrics")
    
    # Time period
    recorded_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Performance metrics
    requests_handled = Column(Integer, default=0)
    requests_failed = Column(Integer, default=0)
    avg_response_time_ms = Column(Integer, default=0)
    total_tokens_input = Column(Integer, default=0)
    total_tokens_output = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Quality metrics
    quality_score = Column(Float, default=0.0)  # 0-10 rating
    user_satisfaction = Column(Float, default=0.0)  # 0-10 rating
    error_rate = Column(Float, default=0.0)  # percentage
    
    # Resource metrics
    avg_cpu_usage = Column(Float, default=0.0)
    avg_memory_usage = Column(Integer, default=0)
    peak_memory_usage = Column(Integer, default=0)
    
    # Additional metrics
    custom_metrics = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<AgentMetrics(agent={self.agent_id}, period={self.period_start}-{self.period_end})>"


class SwarmMetrics(Base):
    """
    Performance metrics for swarm instances.
    """
    __tablename__ = "swarm_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    swarm_id = Column(Integer, ForeignKey("swarm_instances.id"), nullable=False)
    swarm = relationship("SwarmInstance", back_populates="metrics")
    
    # Time period
    recorded_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Execution metrics
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    avg_execution_time_seconds = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Collaboration metrics
    agent_interactions = Column(Integer, default=0)
    consensus_achieved = Column(Integer, default=0)
    conflicts_resolved = Column(Integer, default=0)
    
    # Quality metrics
    output_quality_score = Column(Float, default=0.0)
    stakeholder_satisfaction = Column(Float, default=0.0)
    
    # Efficiency metrics
    resource_utilization = Column(Float, default=0.0)
    coordination_overhead = Column(Float, default=0.0)
    
    def __repr__(self):
        return f"<SwarmMetrics(swarm={self.swarm_id}, period={self.period_start}-{self.period_end})>"


# =============================================================================
# Factory Usage Tracking
# =============================================================================

class FactoryUsage(Base):
    """
    Track usage of the Agent Factory for analytics and billing.
    """
    __tablename__ = "factory_usage"

    id = Column(Integer, primary_key=True, index=True)
    
    # User/session identification
    user_id = Column(String(100), index=True)
    session_id = Column(String(100), index=True)
    
    # Operation details
    operation_type = Column(String(50), nullable=False)  # create_agent, create_swarm, etc.
    resource_type = Column(String(50), nullable=False)  # agent, swarm, blueprint
    resource_id = Column(String(100))
    
    # Context
    parameters = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    
    # Timing
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer, default=0)
    
    # Cost tracking
    compute_cost = Column(Float, default=0.0)
    api_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    
    # Status
    status = Column(String(20), default="completed")  # completed, failed, cancelled
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<FactoryUsage(operation='{self.operation_type}', user='{self.user_id}')>"


# =============================================================================
# Helper Functions
# =============================================================================

def create_tables(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)


def get_model_config_dict(model_config: ModelConfig) -> Dict[str, Any]:
    """Convert ModelConfig to dictionary for storage"""
    return {
        "temperature": model_config.temperature,
        "max_tokens": model_config.max_tokens,
        "top_p": model_config.top_p,
        "frequency_penalty": model_config.frequency_penalty,
        "presence_penalty": model_config.presence_penalty,
        "cost_limit_per_request": model_config.cost_limit_per_request,
        "timeout_seconds": model_config.timeout_seconds,
        "retry_attempts": model_config.retry_attempts,
        "enable_fallback": model_config.enable_fallback,
        "enable_emergency_fallback": model_config.enable_emergency_fallback
    }


def dict_to_model_config(config_dict: Dict[str, Any]) -> ModelConfig:
    """Convert dictionary to ModelConfig object"""
    return ModelConfig(**config_dict)


# Export all models
__all__ = [
    "Base",
    "AgentStatus",
    "SwarmStatus", 
    "AgentTier",
    "TaskType",
    "AgentBlueprint",
    "AgentInstance",
    "SwarmConfiguration",
    "SwarmInstance",
    "SwarmMembership",
    "AgentMetrics",
    "SwarmMetrics",
    "FactoryUsage",
    "create_tables",
    "get_model_config_dict",
    "dict_to_model_config"
]