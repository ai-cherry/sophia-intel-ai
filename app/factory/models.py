"""
Core Models for Agent Factory System

Defines the fundamental data models and enums used by the agent factory system.
Separated to avoid circular imports between agent_factory and agent_catalog.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.agent_config import AgentRoleConfig


class AgentSpecialty(str, Enum):
    """Agent specialization areas"""
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    DEVOPS = "devops"
    TESTER = "tester"
    SECURITY = "security"
    ANALYST = "analyst"
    DATA_SCIENTIST = "data_scientist"
    PRODUCT_MANAGER = "product_manager"
    GENERAL = "general"


class AgentCapability(str, Enum):
    """Agent capabilities"""
    CODING = "coding"
    DEBUGGING = "debugging"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DESIGN = "design"
    DOCUMENTATION = "documentation"
    DATA_ANALYSIS = "data_analysis"
    RESEARCH = "research"
    PLANNING = "planning"
    DECISION_MAKING = "decision_making"
    OPTIMIZATION = "optimization"
    MONITORING = "monitoring"
    DEPLOYMENT = "deployment"
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    PRESENTATION = "presentation"
    COMPETITIVE_ANALYSIS = "competitive_analysis"


class AgentPersonality(str, Enum):
    """Agent personality types"""
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    DETAIL_ORIENTED = "detail_oriented"
    BIG_PICTURE = "big_picture"
    COLLABORATIVE = "collaborative"
    INDEPENDENT = "independent"
    CAUTIOUS = "cautious"
    ASSERTIVE = "assertive"


class AgentMetadata(BaseModel):
    """Metadata for agent blueprints"""
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "Factory"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = []
    usage_count: int = 0
    success_rate: float = 1.0
    avg_response_time: float = 0.0


class AgentBlueprint(BaseModel):
    """Complete blueprint for creating an agent"""
    id: str
    metadata: AgentMetadata
    specialty: AgentSpecialty
    capabilities: List[AgentCapability]
    personality: AgentPersonality
    config: AgentRoleConfig
    system_prompt_template: str
    task_instructions: Dict[str, str] = {}
    tools: List[str] = []
    dependencies: List[str] = []
    constraints: List[str] = []
    max_concurrent_tasks: int = 1
    rate_limit_per_hour: int = 100
    memory_enabled: bool = True
    learning_enabled: bool = False