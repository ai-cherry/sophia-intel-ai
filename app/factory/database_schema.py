"""
Database Schema for Agent Factory System

Defines SQLAlchemy models for persisting agent blueprints, swarm configurations,
and execution history in a production database.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

from sqlalchemy import (
    Column, String, Text, DateTime, Float, Integer, Boolean, 
    ForeignKey, JSON, Table, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
from pydantic import BaseModel

Base = declarative_base()

# =============================================================================
# ASSOCIATION TABLES FOR MANY-TO-MANY RELATIONSHIPS
# =============================================================================

agent_capability_association = Table(
    'agent_capabilities',
    Base.metadata,
    Column('agent_id', UUID(as_uuid=True), ForeignKey('agent_blueprints.id'), primary_key=True),
    Column('capability', String(50), primary_key=True)
)

swarm_agent_association = Table(
    'swarm_agents',
    Base.metadata,
    Column('swarm_id', UUID(as_uuid=True), ForeignKey('swarm_instances.id'), primary_key=True),
    Column('agent_blueprint_id', UUID(as_uuid=True), ForeignKey('agent_blueprints.id'), primary_key=True),
    Column('role_in_swarm', String(50)),
    Column('execution_order', Integer, default=0),
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)

# =============================================================================
# CORE MODELS
# =============================================================================

class AgentBlueprint(Base):
    """Database model for agent blueprints"""
    __tablename__ = 'agent_blueprints'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    specialty = Column(String(50), nullable=False, index=True)
    personality = Column(String(50), nullable=False)
    
    # Versioning and authorship
    version = Column(String(20), default='1.0.0')
    author = Column(String(100), default='Sophia Intelligence')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Configuration
    system_prompt_template = Column(Text)
    task_instructions = Column(JSON)  # Dict[str, str]
    model_config = Column(JSON)  # ModelConfig as dict
    agent_config = Column(JSON)  # AgentRoleConfig as dict
    
    # Operational parameters
    max_concurrent_tasks = Column(Integer, default=5)
    rate_limit_per_hour = Column(Integer, default=100)
    memory_enabled = Column(Boolean, default=True)
    learning_enabled = Column(Boolean, default=True)
    
    # Tools and dependencies
    tools = Column(ARRAY(String))  # List of tool names
    dependencies = Column(ARRAY(String))  # Required other agents
    constraints = Column(JSON)  # Dict[str, Any]
    
    # Metadata and tags
    tags = Column(ARRAY(String))
    metadata_extra = Column(JSON)  # Additional metadata
    
    # Performance metrics
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=1.0)
    avg_response_time = Column(Float, default=0.0)
    
    # Status and lifecycle
    status = Column(String(20), default='active')  # active, deprecated, archived
    is_public = Column(Boolean, default=True)
    created_by_user_id = Column(String(100))
    
    # Relationships
    swarm_memberships = relationship(
        "SwarmInstance",
        secondary=swarm_agent_association,
        back_populates="agent_blueprints"
    )
    
    executions = relationship("AgentExecution", back_populates="blueprint")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_specialty_status', 'specialty', 'status'),
        Index('idx_created_at', 'created_at'),
        Index('idx_usage_metrics', 'usage_count', 'success_rate'),
    )

class SwarmTemplate(Base):
    """Database model for reusable swarm templates"""
    __tablename__ = 'swarm_templates'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(String(100), unique=True, nullable=False)  # Human-readable ID
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50), index=True)
    
    # Configuration
    swarm_type = Column(String(50), nullable=False)
    execution_mode = Column(String(50), nullable=False)
    pattern = Column(String(50))
    
    # Requirements
    required_specialties = Column(ARRAY(String))
    required_capabilities = Column(ARRAY(String))
    optional_specialties = Column(ARRAY(String))
    max_agents = Column(Integer, default=5)
    
    # Configuration overrides
    config_overrides = Column(JSON)
    
    # Metadata
    tags = Column(ARRAY(String))
    recommended_for = Column(ARRAY(String))  # Use cases
    
    # Versioning and authorship
    version = Column(String(20), default='1.0.0')
    author = Column(String(100), default='Sophia Intelligence')
    created_by_user_id = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Status and usage
    status = Column(String(20), default='active')
    is_public = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    
    # Relationships
    swarm_instances = relationship("SwarmInstance", back_populates="template")
    
    # Indexes
    __table_args__ = (
        Index('idx_template_category', 'template_id', 'category'),
        Index('idx_swarm_type', 'swarm_type'),
    )

class SwarmInstance(Base):
    """Database model for created swarm instances"""
    __tablename__ = 'swarm_instances'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Template relationship
    template_id = Column(UUID(as_uuid=True), ForeignKey('swarm_templates.id'), nullable=True)
    template = relationship("SwarmTemplate", back_populates="swarm_instances")
    
    # Configuration
    swarm_type = Column(String(50), nullable=False)
    execution_mode = Column(String(50), nullable=False)
    pattern = Column(String(50))
    
    # Operational settings
    memory_enabled = Column(Boolean, default=True)
    quality_threshold = Column(Float, default=0.8)
    max_execution_time = Column(Float, default=300.0)
    
    # Agent composition
    agent_count = Column(Integer, default=0)
    
    # Metadata and tags
    tags = Column(ARRAY(String))
    metadata_extra = Column(JSON)
    
    # Creation info
    created_by_user_id = Column(String(100))
    created_via = Column(String(50), default='api')  # api, ui, template, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_executed_at = Column(DateTime(timezone=True))
    
    # Status and lifecycle
    status = Column(String(20), default='active')  # active, paused, archived
    
    # Performance metrics
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    avg_execution_time = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    
    # Relationships
    agent_blueprints = relationship(
        "AgentBlueprint",
        secondary=swarm_agent_association,
        back_populates="swarm_memberships"
    )
    
    executions = relationship("SwarmExecution", back_populates="swarm_instance")
    
    # Indexes
    __table_args__ = (
        Index('idx_swarm_status', 'status', 'created_at'),
        Index('idx_swarm_type_mode', 'swarm_type', 'execution_mode'),
        Index('idx_created_by', 'created_by_user_id'),
    )

class SwarmExecution(Base):
    """Database model for swarm execution records"""
    __tablename__ = 'swarm_executions'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Swarm relationship
    swarm_id = Column(UUID(as_uuid=True), ForeignKey('swarm_instances.id'), nullable=False)
    swarm_instance = relationship("SwarmInstance", back_populates="executions")
    
    # Execution details
    task_description = Column(Text, nullable=False)
    task_context = Column(JSON)  # Input context
    result = Column(JSON)  # Execution result
    
    # Performance metrics
    execution_time = Column(Float)  # Seconds
    token_usage = Column(JSON)  # Token consumption details
    cost_estimate = Column(Float, default=0.0)
    
    # Status and outcome
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    errors = Column(JSON)  # List of errors
    
    # Agents involved
    agents_used = Column(ARRAY(String))
    patterns_used = Column(ARRAY(String))
    
    # Execution metadata
    execution_mode_used = Column(String(50))
    quality_score = Column(Float)
    user_rating = Column(Integer)  # 1-5 star rating
    
    # Timestamps
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # User context
    initiated_by_user_id = Column(String(100))
    session_id = Column(String(100))
    
    # Relationships
    agent_executions = relationship("AgentExecution", back_populates="swarm_execution")
    
    # Indexes
    __table_args__ = (
        Index('idx_execution_status', 'status', 'created_at'),
        Index('idx_swarm_performance', 'swarm_id', 'success', 'execution_time'),
        Index('idx_user_executions', 'initiated_by_user_id', 'created_at'),
    )

class AgentExecution(Base):
    """Database model for individual agent execution within swarms"""
    __tablename__ = 'agent_executions'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    swarm_execution_id = Column(UUID(as_uuid=True), ForeignKey('swarm_executions.id'), nullable=False)
    swarm_execution = relationship("SwarmExecution", back_populates="agent_executions")
    
    blueprint_id = Column(UUID(as_uuid=True), ForeignKey('agent_blueprints.id'), nullable=False)
    blueprint = relationship("AgentBlueprint", back_populates="executions")
    
    # Execution details
    agent_name = Column(String(255))
    role_in_swarm = Column(String(50))
    task_assigned = Column(Text)
    result = Column(JSON)
    
    # Performance metrics
    execution_time = Column(Float)
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    
    # Status and outcome
    status = Column(String(20), default='pending')
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    quality_score = Column(Float)
    
    # Execution context
    execution_order = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_agent_performance', 'blueprint_id', 'success', 'execution_time'),
        Index('idx_swarm_agent_exec', 'swarm_execution_id', 'execution_order'),
    )

class UserPreferences(Base):
    """Database model for user preferences and customizations"""
    __tablename__ = 'user_preferences'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Preferences
    preferred_agent_specialties = Column(ARRAY(String))
    preferred_swarm_types = Column(ARRAY(String))
    default_execution_mode = Column(String(50), default='parallel')
    
    # Customizations
    custom_agent_configurations = Column(JSON)  # Custom config overrides
    favorite_templates = Column(ARRAY(String))  # Template IDs
    
    # Usage patterns
    most_used_agents = Column(JSON)  # Agent ID -> usage count
    most_used_swarms = Column(JSON)  # Swarm type -> usage count
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# =============================================================================
# PYDANTIC MODELS FOR API RESPONSES
# =============================================================================

class AgentBlueprintResponse(BaseModel):
    """API response model for agent blueprints"""
    id: str
    name: str
    description: str
    specialty: str
    personality: str
    capabilities: List[str]
    version: str
    author: str
    created_at: datetime
    updated_at: datetime
    usage_count: int
    success_rate: float
    status: str
    tags: List[str]
    
    class Config:
        from_attributes = True

class SwarmInstanceResponse(BaseModel):
    """API response model for swarm instances"""
    id: str
    name: str
    description: str
    swarm_type: str
    execution_mode: str
    agent_count: int
    status: str
    created_at: datetime
    total_executions: int
    successful_executions: int
    success_rate: float
    avg_execution_time: float
    total_cost: float
    tags: List[str]
    
    @property
    def success_rate(self) -> float:
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions
    
    class Config:
        from_attributes = True

class SwarmExecutionResponse(BaseModel):
    """API response model for swarm executions"""
    id: str
    swarm_id: str
    task_description: str
    status: str
    success: bool
    execution_time: Optional[float]
    cost_estimate: float
    agents_used: List[str]
    quality_score: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True

# =============================================================================
# DATABASE OPERATIONS CLASS
# =============================================================================

class DatabaseManager:
    """Database operations manager for agent factory"""
    
    def __init__(self, session: Session):
        self.session = session
    
    # Agent Blueprint operations
    
    def create_agent_blueprint(self, blueprint_data: Dict[str, Any]) -> AgentBlueprint:
        """Create new agent blueprint in database"""
        blueprint = AgentBlueprint(**blueprint_data)
        self.session.add(blueprint)
        self.session.commit()
        self.session.refresh(blueprint)
        return blueprint
    
    def get_agent_blueprint(self, blueprint_id: str) -> Optional[AgentBlueprint]:
        """Get agent blueprint by ID"""
        return self.session.query(AgentBlueprint).filter(
            AgentBlueprint.id == blueprint_id
        ).first()
    
    def list_agent_blueprints(
        self, 
        specialty: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        status: str = 'active',
        limit: int = 100,
        offset: int = 0
    ) -> List[AgentBlueprint]:
        """List agent blueprints with filtering"""
        query = self.session.query(AgentBlueprint).filter(
            AgentBlueprint.status == status
        )
        
        if specialty:
            query = query.filter(AgentBlueprint.specialty == specialty)
        
        # Note: Capability filtering would require join with association table
        # For now, we'll handle this in the application layer
        
        return query.offset(offset).limit(limit).all()
    
    def update_agent_blueprint(self, blueprint_id: str, updates: Dict[str, Any]) -> bool:
        """Update agent blueprint"""
        blueprint = self.get_agent_blueprint(blueprint_id)
        if not blueprint:
            return False
        
        for key, value in updates.items():
            if hasattr(blueprint, key):
                setattr(blueprint, key, value)
        
        blueprint.updated_at = func.now()
        self.session.commit()
        return True
    
    def update_agent_metrics(self, blueprint_id: str, success: bool, response_time: float):
        """Update agent performance metrics"""
        blueprint = self.get_agent_blueprint(blueprint_id)
        if not blueprint:
            return
        
        blueprint.usage_count += 1
        
        # Update success rate (rolling average)
        if success:
            blueprint.success_rate = ((blueprint.success_rate * (blueprint.usage_count - 1)) + 1) / blueprint.usage_count
        else:
            blueprint.success_rate = (blueprint.success_rate * (blueprint.usage_count - 1)) / blueprint.usage_count
        
        # Update average response time
        blueprint.avg_response_time = ((blueprint.avg_response_time * (blueprint.usage_count - 1)) + response_time) / blueprint.usage_count
        
        self.session.commit()
    
    # Swarm operations
    
    def create_swarm_instance(self, swarm_data: Dict[str, Any]) -> SwarmInstance:
        """Create new swarm instance"""
        swarm = SwarmInstance(**swarm_data)
        self.session.add(swarm)
        self.session.commit()
        self.session.refresh(swarm)
        return swarm
    
    def get_swarm_instance(self, swarm_id: str) -> Optional[SwarmInstance]:
        """Get swarm instance by ID"""
        return self.session.query(SwarmInstance).filter(
            SwarmInstance.id == swarm_id
        ).first()
    
    def list_swarm_instances(
        self, 
        user_id: Optional[str] = None,
        status: str = 'active',
        limit: int = 100,
        offset: int = 0
    ) -> List[SwarmInstance]:
        """List swarm instances with filtering"""
        query = self.session.query(SwarmInstance).filter(
            SwarmInstance.status == status
        )
        
        if user_id:
            query = query.filter(SwarmInstance.created_by_user_id == user_id)
        
        return query.order_by(SwarmInstance.created_at.desc()).offset(offset).limit(limit).all()
    
    # Execution tracking
    
    def create_swarm_execution(self, execution_data: Dict[str, Any]) -> SwarmExecution:
        """Create swarm execution record"""
        execution = SwarmExecution(**execution_data)
        self.session.add(execution)
        self.session.commit()
        self.session.refresh(execution)
        return execution
    
    def update_swarm_execution(self, execution_id: str, updates: Dict[str, Any]) -> bool:
        """Update swarm execution with results"""
        execution = self.session.query(SwarmExecution).filter(
            SwarmExecution.id == execution_id
        ).first()
        
        if not execution:
            return False
        
        for key, value in updates.items():
            if hasattr(execution, key):
                setattr(execution, key, value)
        
        self.session.commit()
        return True
    
    def get_execution_history(
        self, 
        swarm_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[SwarmExecution]:
        """Get execution history with filtering"""
        query = self.session.query(SwarmExecution)
        
        if swarm_id:
            query = query.filter(SwarmExecution.swarm_id == swarm_id)
        
        if user_id:
            query = query.filter(SwarmExecution.initiated_by_user_id == user_id)
        
        return query.order_by(SwarmExecution.created_at.desc()).limit(limit).all()
    
    # Analytics and reporting
    
    def get_agent_performance_stats(self) -> Dict[str, Any]:
        """Get agent performance statistics"""
        stats = self.session.query(
            func.count(AgentBlueprint.id).label('total_agents'),
            func.avg(AgentBlueprint.success_rate).label('avg_success_rate'),
            func.sum(AgentBlueprint.usage_count).label('total_usage')
        ).filter(AgentBlueprint.status == 'active').first()
        
        return {
            'total_agents': stats.total_agents,
            'average_success_rate': float(stats.avg_success_rate or 0),
            'total_usage': stats.total_usage or 0
        }
    
    def get_swarm_performance_stats(self) -> Dict[str, Any]:
        """Get swarm performance statistics"""
        stats = self.session.query(
            func.count(SwarmInstance.id).label('total_swarms'),
            func.sum(SwarmInstance.total_executions).label('total_executions'),
            func.sum(SwarmInstance.successful_executions).label('successful_executions'),
            func.avg(SwarmInstance.avg_execution_time).label('avg_execution_time')
        ).filter(SwarmInstance.status == 'active').first()
        
        total_executions = stats.total_executions or 0
        successful_executions = stats.successful_executions or 0
        
        return {
            'total_swarms': stats.total_swarms,
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'overall_success_rate': successful_executions / total_executions if total_executions > 0 else 0,
            'avg_execution_time': float(stats.avg_execution_time or 0)
        }