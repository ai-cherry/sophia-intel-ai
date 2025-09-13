"""
Agent Composer Models and Logic
Handles visual agent composition with validation and code generation
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime
import uuid
import json


class AgentType(str, Enum):
    """Supported agent types"""
    RESEARCHER = "researcher"
    CODER = "coder"
    REVIEWER = "reviewer"
    QA = "qa"
    SECURITY = "security"
    DEVOPS = "devops"
    BUSINESS_ANALYST = "business_analyst"
    PROJECT_MANAGER = "project_manager"


class TeamMode(str, Enum):
    """Team coordination modes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    COORDINATE = "coordinate"
    COLLABORATE = "collaborate"


class ModelProvider(str, Enum):
    """LLM model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MISTRAL = "mistral"
    META = "meta"


class AgentPosition(BaseModel):
    """Agent position on canvas"""
    x: float = Field(..., ge=0)
    y: float = Field(..., ge=0)


class AgentConfig(BaseModel):
    """Individual agent configuration"""
    id: str = Field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:8]}")
    name: str = Field(..., min_length=1, max_length=100)
    type: AgentType
    model: str = Field(..., description="Model ID like openai/gpt-4o-mini")
    tools: List[str] = Field(default_factory=list)
    position: AgentPosition
    description: Optional[str] = None
    max_tokens: int = Field(default=4000, ge=100, le=32000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    system_prompt: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('model')
    def validate_model(cls, v):
        """Validate model format"""
        if '/' not in v:
            raise ValueError('Model must be in format "provider/model-name"')
        provider, model = v.split('/', 1)
        valid_providers = [p.value for p in ModelProvider]
        if provider not in valid_providers:
            raise ValueError(f'Provider must be one of: {valid_providers}')
        return v
    
    @validator('tools')
    def validate_tools(cls, v):
        """Validate tool names"""
        valid_tools = {
            'web_search', 'file_read', 'file_write', 'code_editor', 
            'terminal', 'calculator', 'database', 'api_client',
            'security_scanner', 'test_runner', 'docker', 'kubernetes',
            'terraform', 'git', 'slack', 'email', 'calendar'
        }
        invalid_tools = set(v) - valid_tools
        if invalid_tools:
            raise ValueError(f'Invalid tools: {invalid_tools}')
        return v


class AgentConnection(BaseModel):
    """Connection between agents"""
    id: str = Field(default_factory=lambda: f"conn_{uuid.uuid4().hex[:8]}")
    from_agent: str = Field(..., description="Source agent ID")
    to_agent: str = Field(..., description="Target agent ID")
    condition: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TeamConfiguration(BaseModel):
    """Team configuration and metadata"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    mode: TeamMode = TeamMode.COORDINATE
    shared_memory: bool = True
    max_concurrent: int = Field(default=3, ge=1, le=10)
    timeout_seconds: int = Field(default=300, ge=30, le=3600)
    cost_limit: float = Field(default=10.0, ge=0.0)
    retry_policy: Dict[str, Any] = Field(default_factory=lambda: {
        "max_retries": 3,
        "backoff_factor": 2.0,
        "timeout_multiplier": 1.5
    })


class AgentComposition(BaseModel):
    """Complete agent team composition"""
    id: str = Field(default_factory=lambda: f"composition_{uuid.uuid4().hex[:8]}")
    name: str = Field(..., min_length=1)
    version: str = Field(default="1.0.0")
    agents: List[AgentConfig] = Field(..., min_items=1)
    connections: List[AgentConnection] = Field(default_factory=list)
    team_config: TeamConfiguration
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('agents')
    def validate_agents(cls, v):
        """Validate agent list"""
        if len(v) > 20:
            raise ValueError('Maximum 20 agents per composition')
        
        # Check for duplicate IDs
        agent_ids = [a.id for a in v]
        if len(agent_ids) != len(set(agent_ids)):
            raise ValueError('Agent IDs must be unique')
        
        # Check for duplicate names
        agent_names = [a.name for a in v]
        if len(agent_names) != len(set(agent_names)):
            raise ValueError('Agent names must be unique')
        
        return v
    
    @validator('connections')
    def validate_connections(cls, v, values):
        """Validate connections between agents"""
        if 'agents' not in values:
            return v
        
        agent_ids = {a.id for a in values['agents']}
        
        for conn in v:
            if conn.from_agent not in agent_ids:
                raise ValueError(f'Connection from unknown agent: {conn.from_agent}')
            if conn.to_agent not in agent_ids:
                raise ValueError(f'Connection to unknown agent: {conn.to_agent}')
            if conn.from_agent == conn.to_agent:
                raise ValueError('Agent cannot connect to itself')
        
        return v
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent by ID"""
        return next((a for a in self.agents if a.id == agent_id), None)
    
    def estimate_cost(self) -> float:
        """Estimate operational cost per hour"""
        base_cost_per_agent = 0.02
        model_multipliers = {
            'gpt-4o': 2.0,
            'claude-3.5-sonnet': 1.8,
            'gpt-4o-mini': 1.0,
            'claude-3.5-haiku': 0.8
        }
        
        total_cost = 0.0
        for agent in self.agents:
            model_name = agent.model.split('/')[-1]
            multiplier = model_multipliers.get(model_name, 1.0)
            total_cost += base_cost_per_agent * multiplier
        
        return round(total_cost, 2)
    
    def validate_deployment(self) -> List[str]:
        """Validate composition for deployment"""
        issues = []
        
        # Check for isolated agents (no connections)
        if len(self.agents) > 1:
            connected_agents = set()
            for conn in self.connections:
                connected_agents.add(conn.from_agent)
                connected_agents.add(conn.to_agent)
            
            isolated = {a.id for a in self.agents} - connected_agents
            if isolated:
                issues.append(f"Isolated agents (no connections): {isolated}")
        
        # Check for circular dependencies in sequential mode
        if self.team_config.mode == TeamMode.SEQUENTIAL:
            # Simple cycle detection
            graph = {}
            for agent in self.agents:
                graph[agent.id] = []
            for conn in self.connections:
                graph[conn.from_agent].append(conn.to_agent)
            
            # DFS cycle detection
            visited = set()
            rec_stack = set()
            
            def has_cycle(node):
                visited.add(node)
                rec_stack.add(node)
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True
                rec_stack.remove(node)
                return False
            
            for agent_id in graph:
                if agent_id not in visited:
                    if has_cycle(agent_id):
                        issues.append("Circular dependency detected in sequential mode")
                        break
        
        return issues


class AgentTemplate(BaseModel):
    """Predefined agent team template"""
    id: str = Field(default_factory=lambda: f"template_{uuid.uuid4().hex[:8]}")
    name: str
    description: str
    category: str
    tags: List[str] = Field(default_factory=list)
    composition: AgentComposition
    usage_count: int = Field(default=0)
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    created_by: Optional[str] = None
    is_public: bool = True
    
    @property
    def agent_count(self) -> int:
        return len(self.composition.agents)
    
    @property
    def estimated_cost(self) -> float:
        return self.composition.estimate_cost()


class SwarmScaleConfig(BaseModel):
    """Swarm scaling configuration"""
    min_agents: int = Field(default=1, ge=1, le=100)
    max_agents: int = Field(default=10, ge=1, le=100)
    scale_trigger: str = Field(default="workload", pattern="^(workload|time|manual)$")
    scale_metric: str = Field(default="queue_size")
    scale_up_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    scale_down_threshold: float = Field(default=0.2, ge=0.0, le=1.0)
    cooldown_seconds: int = Field(default=300, ge=60, le=3600)
    
    @validator('max_agents')
    def validate_max_agents(cls, v, values):
        if 'min_agents' in values and v < values['min_agents']:
            raise ValueError('max_agents must be >= min_agents')
        return v


class SimulationConfig(BaseModel):
    """Monte Carlo simulation configuration"""
    iterations: int = Field(default=1000, ge=100, le=10000)
    task_complexity: str = Field(default="medium", pattern="^(simple|medium|complex)$")
    failure_rate: float = Field(default=0.05, ge=0.0, le=0.5)
    latency_variance: float = Field(default=0.2, ge=0.0, le=1.0)
    cost_variance: float = Field(default=0.1, ge=0.0, le=0.5)


class SimulationResult(BaseModel):
    """Simulation results"""
    composition_id: str
    config: SimulationConfig
    success_rate: float = Field(..., ge=0.0, le=1.0)
    avg_completion_time: float = Field(..., ge=0.0)
    avg_cost: float = Field(..., ge=0.0)
    confidence_interval: Dict[str, float]
    risk_factors: List[Dict[str, Any]]
    recommendations: List[str]
    bottlenecks: List[str]
    simulated_at: datetime = Field(default_factory=datetime.now)


class DeploymentRequest(BaseModel):
    """Deployment request"""
    composition_id: str
    name: str = Field(..., min_length=1, max_length=100)
    environment: str = Field(default="development", pattern="^(development|staging|production)$")
    replicas: int = Field(default=1, ge=1, le=10)
    resources: Dict[str, Any] = Field(default_factory=lambda: {
        "cpu": "100m",
        "memory": "256Mi",
        "storage": "1Gi"
    })
    config_overrides: Dict[str, Any] = Field(default_factory=dict)
    auto_scale: bool = False
    monitoring: bool = True


class DeploymentStatus(BaseModel):
    """Deployment status"""
    deployment_id: str
    composition_id: str
    name: str
    environment: str
    status: str = Field(pattern="^(pending|deploying|running|stopping|stopped|failed)$")
    replicas: Dict[str, int] = Field(default_factory=lambda: {"desired": 0, "ready": 0})
    health_check: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    logs_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ApprovalRequest(BaseModel):
    """Human-in-the-loop approval request"""
    id: str = Field(default_factory=lambda: f"approval_{uuid.uuid4().hex[:8]}")
    composition_id: str
    agent_id: str
    task_id: str
    type: str = Field(pattern="^(deployment|execution|resource_access|data_access)$")
    title: str
    description: str
    context: Dict[str, Any] = Field(default_factory=dict)
    priority: str = Field(default="normal", pattern="^(low|normal|high|critical)$")
    timeout_seconds: int = Field(default=3600, ge=60, le=86400)
    approvers: List[str] = Field(default_factory=list)
    auto_approve_conditions: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


class ApprovalResponse(BaseModel):
    """Approval response"""
    approval_id: str
    approved: bool
    approver: str
    feedback: Optional[str] = None
    conditions: Dict[str, Any] = Field(default_factory=dict)
    approved_at: datetime = Field(default_factory=datetime.now)


class CodeGenerationResult(BaseModel):
    """Generated code result"""
    composition_id: str
    language: str = Field(default="python")
    framework: str = Field(default="agno")
    code: str
    tests: Optional[str] = None
    documentation: Optional[str] = None
    requirements: List[str] = Field(default_factory=list)
    deployment_config: Optional[Dict[str, Any]] = None
    estimated_tokens: int = 0
    generated_at: datetime = Field(default_factory=datetime.now)


# Code generation utilities
class AgentCodeGenerator:
    """Generates executable code from agent compositions"""
    
    @staticmethod
    def generate_agno_code(composition: AgentComposition) -> CodeGenerationResult:
        """Generate Agno framework code"""
        
        # Generate agent definitions
        agent_imports = set()
        agent_definitions = []
        
        for agent in composition.agents:
            # Determine imports based on model provider
            provider = agent.model.split('/')[0]
            if provider == 'openai':
                agent_imports.add("from agno.models.openai import OpenAIChat")
            elif provider == 'anthropic':
                agent_imports.add("from agno.models.anthropic import AnthropicChat")
            
            # Generate agent definition
            tools_str = f"[{', '.join(repr(tool) for tool in agent.tools)}]" if agent.tools else "[]"
            
            agent_def = f"""
{agent.name.lower().replace(' ', '_')} = Agent(
    name="{agent.name}",
    model="{agent.model}",
    tools={tools_str},
    description="{agent.description or f'{agent.type.value} agent'}",
    max_tokens={agent.max_tokens},
    temperature={agent.temperature}
)"""
            agent_definitions.append(agent_def)
        
        # Generate team definition
        agent_names = [agent.name.lower().replace(' ', '_') for agent in composition.agents]
        team_def = f"""
team = Team(
    agents=[{', '.join(agent_names)}],
    mode="{composition.team_config.mode.value}",
    shared_memory={composition.team_config.shared_memory},
    max_concurrent={composition.team_config.max_concurrent}
)"""
        
        # Generate full code
        imports = [
            "from agno.agent import Agent, Team",
            *sorted(agent_imports)
        ]
        
        code = f"""# Generated team: {composition.name}
# Created: {composition.created_at.isoformat()}

{chr(10).join(imports)}

# Agent definitions
{''.join(agent_definitions)}

# Team configuration
{team_def}

# Usage example
if __name__ == "__main__":
    result = team.run("Your task description here")
    print(result)
"""
        
        # Generate tests
        test_code = f"""import pytest
from unittest.mock import Mock, patch

def test_{composition.name.lower().replace(' ', '_')}_creation():
    \"\"\"Test team creation\"\"\"
    assert team is not None
    assert len(team.agents) == {len(composition.agents)}
    assert team.mode == "{composition.team_config.mode.value}"

def test_agent_configuration():
    \"\"\"Test individual agent configuration\"\"\"
    agents = team.agents
    assert len(agents) == {len(composition.agents)}
    
    # Check each agent
    {chr(10).join([f'    assert agents[{i}].name == "{agent.name}"' for i, agent in enumerate(composition.agents)])}

@patch('agno.agent.Agent.run')
def test_team_execution(mock_run):
    \"\"\"Test team execution\"\"\"
    mock_run.return_value = "Mock result"
    result = team.run("Test task")
    assert result is not None
"""
        
        # Generate requirements
        requirements = [
            "agno>=2.0.0",
            "openai>=1.0.0" if any("openai" in agent.model for agent in composition.agents) else None,
            "anthropic>=0.20.0" if any("anthropic" in agent.model for agent in composition.agents) else None,
        ]
        requirements = [req for req in requirements if req is not None]
        
        return CodeGenerationResult(
            composition_id=composition.id,
            language="python",
            framework="agno",
            code=code,
            tests=test_code,
            requirements=requirements,
            estimated_tokens=len(code.split()) * 1.3  # Rough estimate
        )
    
    @staticmethod
    def generate_docker_config(composition: AgentComposition) -> Dict[str, Any]:
        """Generate Docker deployment configuration"""
        return {
            "dockerfile": f"""FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "{composition.name.lower().replace(' ', '_')}.py"]
""",
            "docker_compose": {
                "version": "3.8",
                "services": {
                    composition.name.lower().replace(' ', '_'): {
                        "build": ".",
                        "environment": [
                            "OPENROUTER_API_KEY=${OPENROUTER_API_KEY}",
                            "LOG_LEVEL=INFO"
                        ],
                        "restart": "unless-stopped",
                        "healthcheck": {
                            "test": ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"],
                            "interval": "30s",
                            "timeout": "10s",
                            "retries": 3
                        }
                    }
                }
            }
        }


# Template library
class TemplateLibrary:
    """Predefined template library"""
    
    @staticmethod
    def get_code_review_template() -> AgentTemplate:
        """Code review team template"""
        composition = AgentComposition(
            name="Code Review Team",
            agents=[
                AgentConfig(
                    name="Requirements Analyst",
                    type=AgentType.BUSINESS_ANALYST,
                    model="openai/gpt-4o-mini",
                    tools=["file_read", "web_search"],
                    position=AgentPosition(x=100, y=100),
                    description="Analyzes requirements and specifications"
                ),
                AgentConfig(
                    name="Senior Developer",
                    type=AgentType.CODER,
                    model="anthropic/claude-3.5-sonnet",
                    tools=["code_editor", "file_write", "git"],
                    position=AgentPosition(x=350, y=100),
                    description="Primary code development"
                ),
                AgentConfig(
                    name="Code Reviewer",
                    type=AgentType.REVIEWER,
                    model="openai/gpt-4o",
                    tools=["code_editor", "file_read"],
                    position=AgentPosition(x=600, y=100),
                    description="Reviews code for quality and standards"
                ),
                AgentConfig(
                    name="QA Engineer",
                    type=AgentType.QA,
                    model="openai/gpt-4o-mini",
                    tools=["test_runner", "file_write"],
                    position=AgentPosition(x=350, y=250),
                    description="Creates and runs tests"
                ),
                AgentConfig(
                    name="Security Auditor",
                    type=AgentType.SECURITY,
                    model="anthropic/claude-3.5-sonnet",
                    tools=["security_scanner", "file_read"],
                    position=AgentPosition(x=600, y=250),
                    description="Security review and vulnerability assessment"
                )
            ],
            connections=[],  # Will be populated after agents are created
            team_config=TeamConfiguration(
                name="Code Review Team",
                description="Comprehensive code review and quality assurance",
                mode=TeamMode.COORDINATE,
                shared_memory=True
            )
        )
        
        return AgentTemplate(
            name="Code Review Team",
            description="Comprehensive code review workflow with requirements analysis, development, review, testing, and security audit",
            category="development",
            tags=["code-review", "quality", "security", "testing"],
            composition=composition,
            rating=4.8,
            is_public=True
        )
    
    @staticmethod
    def get_data_pipeline_template() -> AgentTemplate:
        """Data pipeline team template"""
        composition = AgentComposition(
            name="Data Pipeline Team",
            agents=[
                AgentConfig(
                    name="Data Architect",
                    type=AgentType.BUSINESS_ANALYST,
                    model="openai/gpt-4o",
                    tools=["database", "file_read"],
                    position=AgentPosition(x=100, y=100),
                    description="Designs data architecture and flow"
                ),
                AgentConfig(
                    name="ETL Developer",
                    type=AgentType.CODER,
                    model="anthropic/claude-3.5-sonnet",
                    tools=["database", "file_write", "api_client"],
                    position=AgentPosition(x=350, y=100),
                    description="Implements ETL processes"
                ),
                AgentConfig(
                    name="Data Validator",
                    type=AgentType.QA,
                    model="openai/gpt-4o-mini",
                    tools=["database", "calculator"],
                    position=AgentPosition(x=600, y=100),
                    description="Validates data quality and integrity"
                )
            ],
            team_config=TeamConfiguration(
                name="Data Pipeline Team",
                description="End-to-end data pipeline development",
                mode=TeamMode.SEQUENTIAL
            )
        )
        
        return AgentTemplate(
            name="Data Pipeline Team",
            description="End-to-end data pipeline with architecture design, ETL development, and validation",
            category="data",
            tags=["data-pipeline", "etl", "validation"],
            composition=composition,
            rating=4.5
        )
    
    @staticmethod
    def get_devops_template() -> AgentTemplate:
        """DevOps automation template"""
        composition = AgentComposition(
            name="DevOps Automation Team",
            agents=[
                AgentConfig(
                    name="Infrastructure Planner",
                    type=AgentType.DEVOPS,
                    model="openai/gpt-4o",
                    tools=["terraform", "kubernetes"],
                    position=AgentPosition(x=100, y=100),
                    description="Plans infrastructure and deployment"
                ),
                AgentConfig(
                    name="Config Manager",
                    type=AgentType.CODER,
                    model="anthropic/claude-3.5-sonnet",
                    tools=["file_write", "git", "kubernetes"],
                    position=AgentPosition(x=350, y=100),
                    description="Manages configuration and secrets"
                ),
                AgentConfig(
                    name="Deployment Engineer",
                    type=AgentType.DEVOPS,
                    model="openai/gpt-4o-mini",
                    tools=["docker", "kubernetes", "git"],
                    position=AgentPosition(x=600, y=100),
                    description="Executes deployments and rollbacks"
                ),
                AgentConfig(
                    name="Monitor Specialist",
                    type=AgentType.DEVOPS,
                    model="openai/gpt-4o-mini",
                    tools=["api_client", "slack"],
                    position=AgentPosition(x=350, y=250),
                    description="Sets up monitoring and alerting"
                )
            ],
            team_config=TeamConfiguration(
                name="DevOps Automation Team",
                description="Complete DevOps automation pipeline",
                mode=TeamMode.COORDINATE
            )
        )
        
        return AgentTemplate(
            name="DevOps Automation Team",
            description="Complete DevOps automation with infrastructure planning, configuration management, deployment, and monitoring",
            category="devops",
            tags=["devops", "infrastructure", "deployment", "monitoring"],
            composition=composition,
            rating=4.6
        )