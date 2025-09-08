"""
Sophia Unified Factory - Consolidated Business Intelligence Agent System
Merges SophiaBusinessAgentFactory and SophiaMythologySwarmFactory
Enforces 8 concurrent task execution limit and maintains business domain focus
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, WebSocket

# Import memory system for persistence
from app.memory.unified_memory import store_memory
from app.memory.unified_memory_router import MemoryDomain

# Import orchestrator components

logger = logging.getLogger(__name__)

# ==============================================================================
# UNIFIED CONFIGURATION
# ==============================================================================


class UnifiedSophiaConfig:
    """Unified configuration for Sophia factory"""

    def __init__(self):
        self.max_concurrent_tasks = 8  # Standardized limit as per architecture
        self.domain = MemoryDomain.SOPHIA
        self.capabilities = [
            "business_intelligence",
            "sales_analytics",
            "customer_insights",
            "market_research",
            "strategic_planning",
            "mythology_wisdom",
            "okr_tracking",
        ]
        self.enable_memory_integration = True
        self.enable_websocket_updates = True
        self.enable_mythology_agents = True
        self.enable_kpi_tracking = True


# ==============================================================================
# ENUMS AND TYPES
# ==============================================================================


class BusinessAgentRole(str, Enum):
    """Business-specific agent roles"""

    SALES_ANALYST = "sales_analyst"
    REVENUE_FORECASTER = "revenue_forecaster"
    CLIENT_SUCCESS_MANAGER = "client_success_manager"
    MARKET_RESEARCHER = "market_researcher"
    COMPETITIVE_INTELLIGENCE = "competitive_intelligence"
    PIPELINE_OPTIMIZER = "pipeline_optimizer"
    CUSTOMER_HEALTH_MONITOR = "customer_health_monitor"
    BUSINESS_STRATEGIST = "business_strategist"


class MythologyArchetype(str, Enum):
    """Mythology-based agent archetypes"""

    HERMES = "hermes"  # Market intelligence
    ASCLEPIUS = "asclepius"  # Business health
    ATHENA = "athena"  # Strategic wisdom
    ODIN = "odin"  # Visionary leadership
    MINERVA = "minerva"  # Systematic analysis


class BusinessPersonality(str, Enum):
    """Business personality traits"""

    ANALYTICAL = "analytical"
    STRATEGIC = "strategic"
    RELATIONSHIP_FOCUSED = "relationship_focused"
    RESULTS_DRIVEN = "results_driven"
    INNOVATIVE = "innovative"
    CONSULTATIVE = "consultative"
    WISDOM_BASED = "wisdom_based"


class BusinessDomain(str, Enum):
    """Business domains for specialization"""

    SALES_INTELLIGENCE = "sales_intelligence"
    REVENUE_OPERATIONS = "revenue_operations"
    CLIENT_SUCCESS = "client_success"
    MARKET_RESEARCH = "market_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    BUSINESS_STRATEGY = "business_strategy"
    DIVINE_WISDOM = "divine_wisdom"


class SwarmType(str, Enum):
    """Types of business swarms"""

    BUSINESS_TEAM = "business_team"
    MYTHOLOGY_COUNCIL = "mythology_council"
    SALES_INTELLIGENCE = "sales_intelligence"
    STRATEGIC_PLANNING = "strategic_planning"
    CUSTOMER_SUCCESS = "customer_success"
    MARKET_RESEARCH = "market_research"


# ==============================================================================
# DATA MODELS
# ==============================================================================


@dataclass
class BusinessAgentProfile:
    """Unified business agent profile"""

    id: str
    name: str
    role: str
    model: str
    description: str
    personality: Optional[str] = None
    domain: Optional[str] = None
    archetype: Optional[MythologyArchetype] = None
    capabilities: list[str] = field(default_factory=list)
    kpis: list[str] = field(default_factory=list)
    virtual_key: str = "openai-vk-190a60"
    temperature: float = 0.3
    specialized_prompts: dict[str, str] = field(default_factory=dict)
    wisdom_traits: dict[str, Any] = field(default_factory=dict)


@dataclass
class BusinessTeamConfig:
    """Configuration for business teams"""

    id: str
    name: str
    description: str
    team_type: SwarmType
    agents: list[BusinessAgentProfile]
    strategy: str = "balanced"
    consensus_threshold: float = 0.85
    enable_debate: bool = True
    okr_focus: list[str] = field(default_factory=list)


@dataclass
class OKRMetrics:
    """OKR tracking metrics"""

    total_revenue: float = 0.0
    employee_count: int = 0
    revenue_per_employee: float = 0.0
    target_revenue_per_employee: float = 500000.0
    growth_rate: float = 0.0
    efficiency_score: float = 0.0
    last_updated: str = ""


# ==============================================================================
# SOPHIA UNIFIED FACTORY CLASS
# ==============================================================================


class SophiaUnifiedFactory:
    """
    Consolidated factory combining business agents and mythology swarms
    Enforces 8 concurrent task limit and maintains business excellence
    """

    def __init__(self):
        # Unified configuration
        self.config = UnifiedSophiaConfig()

        # Agent and team management
        self.business_templates: dict[str, BusinessAgentProfile] = {}
        self.mythology_agents: dict[str, BusinessAgentProfile] = {}
        self.business_teams: dict[str, BusinessTeamConfig] = {}
        self.analytical_swarms: dict[str, Any] = {}
        self.active_agents: dict[str, BusinessAgentProfile] = {}
        self.active_teams: dict[str, Any] = {}

        # Concurrent task management
        self._concurrent_tasks = 0
        self._task_queue: list[Any] = []
        self._task_lock = asyncio.Lock()

        # Business metrics tracking
        self.okr_tracker = OKRMetrics()
        self.business_metrics = {
            "analyses_completed": 0,
            "forecasts_generated": 0,
            "insights_delivered": 0,
            "customer_health_checks": 0,
            "market_research_reports": 0,
            "strategic_plans": 0,
            "mythology_consultations": 0,
        }

        # Performance tracking
        self.performance_metrics: dict[str, dict] = {}

        # WebSocket connections for real-time updates
        self.websocket_connections: set[WebSocket] = set()

        # Portkey virtual keys for business operations
        self.virtual_keys = {
            "PERPLEXITY-VK": "perplexity-vk-56c172",  # Market research
            "ANTHROPIC-VK": "anthropic-vk-b42804",  # Strategic analysis
            "OPENAI-VK": "openai-vk-190a60",  # Relationship insights
            "DEEPSEEK-VK": "deepseek-vk-24102f",  # Data analysis
            "XAI-VK": "xai-vk-e65d0f",  # Creative insights
        }

        # Initialize templates and configurations
        self._initialize_business_templates()
        self._initialize_mythology_agents()
        self._initialize_team_templates()

        logger.info(
            f"💼 Sophia Unified Factory initialized with {self.config.max_concurrent_tasks} "
            f"concurrent task limit and business intelligence capabilities"
        )

    # ==============================================================================
    # INITIALIZATION METHODS
    # ==============================================================================

    def _initialize_business_templates(self):
        """Initialize business agent templates with personality injection"""

        # Sales Pipeline Analyst
        self.business_templates["sales_pipeline_analyst"] = BusinessAgentProfile(
            id="sales_pipeline_analyst_template",
            name="Sales Pipeline Analyst",
            role=BusinessAgentRole.SALES_ANALYST,
            model="perplexity/sonar-pro",
            description="Analyzes sales pipeline and provides actionable insights",
            personality=BusinessPersonality.ANALYTICAL,
            domain=BusinessDomain.SALES_INTELLIGENCE,
            capabilities=[
                "Pipeline Analysis",
                "Conversion Rate Optimization",
                "Revenue Forecasting",
                "Bottleneck Identification",
                "Sales Metrics Tracking",
            ],
            kpis=[
                "Pipeline Velocity",
                "Conversion Rates",
                "Deal Size Trends",
                "Sales Cycle Length",
                "Revenue Attribution",
            ],
            virtual_key="perplexity-vk-56c172",
            temperature=0.3,
        )

        # Revenue Forecaster
        self.business_templates["revenue_forecaster"] = BusinessAgentProfile(
            id="revenue_forecaster_template",
            name="Revenue Forecaster",
            role=BusinessAgentRole.REVENUE_FORECASTER,
            model="anthropic/claude-opus-4.1",
            description="Strategic revenue forecasting with market trend analysis",
            personality=BusinessPersonality.STRATEGIC,
            domain=BusinessDomain.REVENUE_OPERATIONS,
            capabilities=[
                "Revenue Forecasting",
                "Financial Modeling",
                "Market Trend Analysis",
                "Scenario Planning",
                "Growth Strategy",
            ],
            kpis=[
                "Forecast Accuracy",
                "Revenue Growth Rate",
                "Market Share Trends",
                "Seasonal Patterns",
                "Risk Assessment",
            ],
            virtual_key="anthropic-vk-b42804",
            temperature=0.4,
        )

        # Client Success Manager
        self.business_templates["client_success_manager"] = BusinessAgentProfile(
            id="client_success_manager_template",
            name="Client Success Manager",
            role=BusinessAgentRole.CLIENT_SUCCESS_MANAGER,
            model="openai/gpt-4o",
            description="Manages client relationships and drives expansion",
            personality=BusinessPersonality.RELATIONSHIP_FOCUSED,
            domain=BusinessDomain.CLIENT_SUCCESS,
            capabilities=[
                "Account Health Monitoring",
                "Relationship Management",
                "Churn Prevention",
                "Expansion Planning",
                "Customer Success Metrics",
            ],
            kpis=[
                "Customer Health Score",
                "Net Revenue Retention",
                "Churn Rate",
                "Expansion Revenue",
                "Customer Satisfaction",
            ],
            virtual_key="openai-vk-190a60",
            temperature=0.6,
        )

        # Market Research Specialist
        self.business_templates["market_research_specialist"] = BusinessAgentProfile(
            id="market_research_specialist_template",
            name="Market Research Specialist",
            role=BusinessAgentRole.MARKET_RESEARCHER,
            model="deepseek/deepseek-chat",
            description="Conducts comprehensive market research and analysis",
            personality=BusinessPersonality.ANALYTICAL,
            domain=BusinessDomain.MARKET_RESEARCH,
            capabilities=[
                "Market Analysis",
                "Industry Research",
                "Trend Identification",
                "Data Collection",
                "Market Sizing",
            ],
            kpis=[
                "Market Share Analysis",
                "Trend Accuracy",
                "Research Coverage",
                "Insight Quality",
                "Competitive Intelligence",
            ],
            virtual_key="deepseek-vk-24102f",
            temperature=0.2,
        )

        # Competitive Intelligence Agent
        self.business_templates["competitive_intelligence"] = BusinessAgentProfile(
            id="competitive_intelligence_template",
            name="Competitive Intelligence Agent",
            role=BusinessAgentRole.COMPETITIVE_INTELLIGENCE,
            model="x-ai/grok-4",
            description="Monitors competitors and provides strategic insights",
            personality=BusinessPersonality.INNOVATIVE,
            domain=BusinessDomain.COMPETITIVE_ANALYSIS,
            capabilities=[
                "Competitive Monitoring",
                "Strategic Analysis",
                "Market Positioning",
                "Threat Assessment",
                "Differentiation Strategy",
            ],
            kpis=[
                "Competitive Win Rate",
                "Market Position",
                "Threat Detection",
                "Strategic Insights",
                "Positioning Effectiveness",
            ],
            virtual_key="xai-vk-e65d0f",
            temperature=0.7,
        )

    def _initialize_mythology_agents(self):
        """Initialize mythology-based wisdom agents"""

        # Hermes - Market Intelligence
        self.mythology_agents["hermes"] = BusinessAgentProfile(
            id="hermes_agent",
            name="Hermes - Divine Messenger & Market Intelligence",
            role="mythology_analyst",
            model="gpt-4",
            description="Swift gatherer of market intelligence and business communications",
            personality=BusinessPersonality.WISDOM_BASED,
            domain=BusinessDomain.DIVINE_WISDOM,
            archetype=MythologyArchetype.HERMES,
            capabilities=[
                "market_intelligence",
                "competitive_analysis",
                "business_communications",
                "trend_identification",
                "information_synthesis",
            ],
            virtual_key="openai-vk-190a60",
            temperature=0.3,
            specialized_prompts={
                "market_analysis": """As Hermes, divine messenger and master of commerce,
                I bring swift intelligence from the market realm. My divine gifts include
                rapid information gathering, pattern recognition, and clear communication
                of insights to mortals and gods alike."""
            },
            wisdom_traits={
                "speed": "divine",
                "insight": "penetrating",
                "communication": "eloquent",
            },
        )

        # Asclepius - Business Health
        self.mythology_agents["asclepius"] = BusinessAgentProfile(
            id="asclepius_agent",
            name="Asclepius - Divine Healer & Business Diagnostician",
            role="mythology_healer",
            model="claude-3-opus",
            description="Master diagnostician of business health and organizational wellness",
            personality=BusinessPersonality.WISDOM_BASED,
            domain=BusinessDomain.DIVINE_WISDOM,
            archetype=MythologyArchetype.ASCLEPIUS,
            capabilities=[
                "business_diagnostics",
                "organizational_health",
                "performance_optimization",
                "process_improvement",
                "operational_healing",
            ],
            virtual_key="anthropic-vk-b42804",
            temperature=0.2,
            specialized_prompts={
                "business_diagnostics": """As Asclepius, divine healer and master of restoration,
                I diagnose the ailments that afflict organizations. I examine all symptoms
                of business dysfunction with divine insight and prescribe comprehensive
                healing strategies."""
            },
            wisdom_traits={
                "diagnosis": "divine",
                "healing": "comprehensive",
                "compassion": "infinite",
            },
        )

        # Athena - Strategic Wisdom
        self.mythology_agents["athena"] = BusinessAgentProfile(
            id="athena_agent",
            name="Athena - Divine Strategist & Wisdom Keeper",
            role="mythology_strategist",
            model="gpt-4",
            description="Goddess of strategic wisdom and righteous warfare",
            personality=BusinessPersonality.WISDOM_BASED,
            domain=BusinessDomain.DIVINE_WISDOM,
            archetype=MythologyArchetype.ATHENA,
            capabilities=[
                "strategic_planning",
                "competitive_strategy",
                "wisdom_based_decisions",
                "tactical_analysis",
                "long_term_vision",
            ],
            virtual_key="openai-vk-190a60",
            temperature=0.1,
            specialized_prompts={
                "strategic_planning": """As Athena, goddess of wisdom and strategic warfare,
                I craft strategies that ensure victory. My approach combines divine wisdom
                accumulated across millennia with comprehensive analysis of all strategic
                variables."""
            },
            wisdom_traits={
                "wisdom": "divine",
                "strategy": "infallible",
                "justice": "righteous",
            },
        )

        # Odin - Visionary Leadership
        self.mythology_agents["odin"] = BusinessAgentProfile(
            id="odin_agent",
            name="Odin - All-Father & Strategic Visionary",
            role="mythology_visionary",
            model="gpt-4",
            description="All-seeing strategist who sacrifices for wisdom and knowledge",
            personality=BusinessPersonality.WISDOM_BASED,
            domain=BusinessDomain.DIVINE_WISDOM,
            archetype=MythologyArchetype.ODIN,
            capabilities=[
                "high_level_strategy",
                "sacrifice_analysis",
                "leadership_decisions",
                "knowledge_gathering",
                "long_term_vision",
            ],
            virtual_key="openai-vk-190a60",
            temperature=0.15,
            specialized_prompts={
                "strategic_vision": """As Odin, All-Father who sees across all nine realms,
                I provide vision that transcends mortal limitations. I understand what must
                be sacrificed to achieve greatness and make decisions based on ultimate
                outcomes."""
            },
            wisdom_traits={
                "vision": "all-seeing",
                "sacrifice": "willing",
                "knowledge": "infinite",
            },
        )

        # Minerva - Systematic Analysis
        self.mythology_agents["minerva"] = BusinessAgentProfile(
            id="minerva_agent",
            name="Minerva - Divine Validator & Systematic Analyst",
            role="mythology_validator",
            model="claude-3-opus",
            description="Roman goddess of wisdom and systematic thought",
            personality=BusinessPersonality.WISDOM_BASED,
            domain=BusinessDomain.DIVINE_WISDOM,
            archetype=MythologyArchetype.MINERVA,
            capabilities=[
                "systematic_analysis",
                "creative_solutions",
                "strategic_validation",
                "intellectual_rigor",
                "quality_assurance",
            ],
            virtual_key="anthropic-vk-b42804",
            temperature=0.1,
            specialized_prompts={
                "strategic_validation": """As Minerva, goddess of wisdom and systematic thought,
                I validate strategies with intellectual rigor. I examine every assumption,
                test against multiple scenarios, and ensure strategies are both sound and
                implementable."""
            },
            wisdom_traits={
                "analysis": "systematic",
                "validation": "rigorous",
                "creativity": "divine",
            },
        )

    def _initialize_team_templates(self):
        """Initialize business team templates"""

        # Sales Intelligence Team
        sales_agents = [
            self.business_templates["sales_pipeline_analyst"],
            self.business_templates["revenue_forecaster"],
            self.business_templates["competitive_intelligence"],
        ]

        self.business_teams["sales_intelligence"] = BusinessTeamConfig(
            id="sales_intelligence_team",
            name="Sales Intelligence Team",
            description="Comprehensive sales analysis, forecasting, and competitive intelligence",
            team_type=SwarmType.SALES_INTELLIGENCE,
            agents=sales_agents,
            strategy="balanced",
            okr_focus=["revenue_growth", "pipeline_velocity", "win_rate"],
        )

        # Client Success Team
        client_agents = [
            self.business_templates["client_success_manager"],
            self.business_templates["sales_pipeline_analyst"],
        ]

        self.business_teams["client_success"] = BusinessTeamConfig(
            id="client_success_team",
            name="Client Success Team",
            description="Account health monitoring and expansion planning",
            team_type=SwarmType.CUSTOMER_SUCCESS,
            agents=client_agents,
            strategy="consensus",
            consensus_threshold=0.9,
            okr_focus=["net_revenue_retention", "customer_health", "expansion_revenue"],
        )

        # Mythology Council (Strategic Wisdom)
        mythology_council = [
            self.mythology_agents["athena"],
            self.mythology_agents["odin"],
            self.mythology_agents["minerva"],
        ]

        self.business_teams["mythology_council"] = BusinessTeamConfig(
            id="mythology_council",
            name="Divine Strategic Council",
            description="Divine wisdom for strategic planning and decision-making",
            team_type=SwarmType.MYTHOLOGY_COUNCIL,
            agents=mythology_council,
            strategy="debate",
            consensus_threshold=0.88,
            enable_debate=True,
            okr_focus=[
                "strategic_alignment",
                "long_term_vision",
                "wisdom_based_decisions",
            ],
        )

        # Business Intelligence Swarm
        bi_agents = [
            self.mythology_agents["hermes"],
            self.mythology_agents["athena"],
            self.mythology_agents["minerva"],
        ]

        self.business_teams["business_intelligence"] = BusinessTeamConfig(
            id="business_intelligence_swarm",
            name="Business Intelligence Swarm",
            description="Comprehensive business analysis with divine wisdom",
            team_type=SwarmType.BUSINESS_TEAM,
            agents=bi_agents,
            strategy="sequential",
            okr_focus=[
                "business_intelligence",
                "market_insights",
                "strategic_recommendations",
            ],
        )

    # ==============================================================================
    # CONCURRENT TASK MANAGEMENT
    # ==============================================================================

    async def _acquire_task_slot(self) -> bool:
        """
        Acquire a task execution slot, respecting the 8 concurrent task limit
        Returns True if slot acquired, False if at capacity
        """
        async with self._task_lock:
            if self._concurrent_tasks < self.config.max_concurrent_tasks:
                self._concurrent_tasks += 1
                logger.info(
                    f"Task slot acquired. Active tasks: {self._concurrent_tasks}/"
                    f"{self.config.max_concurrent_tasks}"
                )
                return True
            else:
                logger.warning(
                    f"Task limit reached: {self._concurrent_tasks}/"
                    f"{self.config.max_concurrent_tasks}"
                )
                return False

    async def _release_task_slot(self):
        """Release a task execution slot"""
        async with self._task_lock:
            if self._concurrent_tasks > 0:
                self._concurrent_tasks -= 1
                logger.info(
                    f"Task slot released. Active tasks: {self._concurrent_tasks}/"
                    f"{self.config.max_concurrent_tasks}"
                )

                # Process queued tasks if any
                if self._task_queue:
                    next_task = self._task_queue.pop(0)
                    logger.info(f"Processing queued task: {next_task.get('id')}")
                    # Would trigger task execution here

    async def queue_task(self, task: dict[str, Any]) -> str:
        """Queue a task for execution when a slot becomes available"""
        task_id = f"queued_{uuid4().hex[:8]}"
        task["id"] = task_id
        task["queued_at"] = datetime.now(timezone.utc).isoformat()

        async with self._task_lock:
            self._task_queue.append(task)
            logger.info(f"Task {task_id} queued. Queue length: {len(self._task_queue)}")

        return task_id

    # ==============================================================================
    # AGENT CREATION METHODS
    # ==============================================================================

    async def create_business_agent(
        self, template_name: str, custom_config: Optional[dict[str, Any]] = None
    ) -> str:
        """Create a business agent from template"""
        if not await self._acquire_task_slot():
            return await self.queue_task(
                {
                    "type": "create_agent",
                    "template": template_name,
                    "config": custom_config,
                }
            )

        try:
            # Check both business and mythology templates
            if template_name in self.business_templates:
                template = self.business_templates[template_name]
            elif template_name in self.mythology_agents:
                template = self.mythology_agents[template_name]
            else:
                raise ValueError(f"Agent template '{template_name}' not found")

            agent_id = f"sophia_{template_name}_{uuid4().hex[:8]}"

            # Create agent instance from template
            agent = BusinessAgentProfile(
                id=agent_id,
                name=template.name,
                role=template.role,
                model=template.model,
                description=template.description,
                personality=template.personality,
                domain=template.domain,
                archetype=template.archetype,
                capabilities=template.capabilities.copy(),
                kpis=template.kpis.copy() if template.kpis else [],
                virtual_key=template.virtual_key,
                temperature=template.temperature,
                specialized_prompts=template.specialized_prompts.copy(),
                wisdom_traits=template.wisdom_traits.copy(),
            )

            # Apply custom configuration if provided
            if custom_config:
                for key, value in custom_config.items():
                    if hasattr(agent, key):
                        setattr(agent, key, value)

            # Store in active agents
            self.active_agents[agent_id] = agent

            # Initialize performance tracking
            self.performance_metrics[agent_id] = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "template": template_name,
                "tasks_completed": 0,
                "avg_response_time": 0.0,
                "success_rate": 1.0,
                "last_used": None,
            }

            # Store in memory if enabled
            if self.config.enable_memory_integration:
                await store_memory(
                    content=json.dumps(
                        {
                            "agent_id": agent_id,
                            "template": template_name,
                            "config": custom_config or {},
                        }
                    ),
                    metadata={
                        "type": "agent_creation",
                        "domain": self.config.domain.value,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )

            logger.info(f"✨ Created business agent: {agent_id} ({template.name})")
            return agent_id

        finally:
            await self._release_task_slot()

    async def create_mythology_agent(
        self,
        archetype: MythologyArchetype,
        custom_config: Optional[dict[str, Any]] = None,
    ) -> str:
        """Create a mythology-based wisdom agent"""
        return await self.create_business_agent(archetype.value, custom_config)

    async def create_business_team(
        self, team_template: str, custom_config: Optional[dict[str, Any]] = None
    ) -> str:
        """Create a business team from template"""
        if not await self._acquire_task_slot():
            return await self.queue_task(
                {
                    "type": "create_team",
                    "template": team_template,
                    "config": custom_config,
                }
            )

        try:
            if team_template not in self.business_teams:
                raise ValueError(f"Team template '{team_template}' not found")

            template = self.business_teams[team_template]
            team_id = f"team_{team_template}_{uuid4().hex[:8]}"

            # Create agents for the team
            team_agents = []
            for agent_template in template.agents:
                # Create each agent
                agent_id = f"{team_id}_{agent_template.id}"
                agent = BusinessAgentProfile(
                    id=agent_id,
                    name=agent_template.name,
                    role=agent_template.role,
                    model=agent_template.model,
                    description=agent_template.description,
                    personality=agent_template.personality,
                    domain=agent_template.domain,
                    archetype=agent_template.archetype,
                    capabilities=agent_template.capabilities.copy(),
                    kpis=agent_template.kpis.copy() if agent_template.kpis else [],
                    virtual_key=agent_template.virtual_key,
                    temperature=agent_template.temperature,
                )
                team_agents.append(agent)
                self.active_agents[agent_id] = agent

            # Create team configuration
            team_config = {
                "id": team_id,
                "name": template.name,
                "description": template.description,
                "team_type": template.team_type,
                "agents": team_agents,
                "strategy": template.strategy,
                "consensus_threshold": template.consensus_threshold,
                "enable_debate": template.enable_debate,
                "okr_focus": template.okr_focus,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "operational",
            }

            # Apply custom configuration
            if custom_config:
                team_config.update(custom_config)

            self.active_teams[team_id] = team_config

            logger.info(
                f"🎯 Created business team: {team_id} ({template.name}) "
                f"with {len(team_agents)} agents"
            )
            return team_id

        finally:
            await self._release_task_slot()

    async def create_analytical_swarm(
        self, swarm_type: SwarmType, swarm_config: dict[str, Any]
    ) -> str:
        """Create an analytical swarm for business intelligence"""
        if not await self._acquire_task_slot():
            return await self.queue_task(
                {
                    "type": "create_swarm",
                    "swarm_type": swarm_type,
                    "config": swarm_config,
                }
            )

        try:
            swarm_id = f"{swarm_type.value}_{uuid4().hex[:8]}"

            swarm_instance = {
                "id": swarm_id,
                "type": swarm_type,
                "config": swarm_config,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "ready",
                "agents": [],
                "okr_metrics": {},
            }

            # Create agents based on swarm type
            if swarm_type == SwarmType.STRATEGIC_PLANNING:
                # Create strategic planning swarm with mythology agents
                for archetype in [MythologyArchetype.ATHENA, MythologyArchetype.ODIN]:
                    agent_id = await self.create_mythology_agent(archetype)
                    swarm_instance["agents"].append(agent_id)

            elif swarm_type == SwarmType.MARKET_RESEARCH:
                # Create market research swarm
                for template in [
                    "market_research_specialist",
                    "competitive_intelligence",
                ]:
                    agent_id = await self.create_business_agent(template)
                    swarm_instance["agents"].append(agent_id)

            self.analytical_swarms[swarm_id] = swarm_instance

            logger.info(f"📊 Created analytical swarm: {swarm_id} ({swarm_type.value})")
            return swarm_id

        finally:
            await self._release_task_slot()

    # ==============================================================================
    # BUSINESS EXECUTION METHODS
    # ==============================================================================

    async def execute_business_task(
        self, agent_or_team_id: str, task: str, context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Execute a business task with an agent or team"""
        if not await self._acquire_task_slot():
            return {
                "success": False,
                "reason": "Task limit reached",
                "queued": True,
                "queue_id": await self.queue_task(
                    {
                        "type": "business_task",
                        "executor": agent_or_team_id,
                        "task": task,
                        "context": context,
                    }
                ),
            }

        start_time = datetime.now(timezone.utc)

        try:
            result = {
                "success": True,
                "executor": agent_or_team_id,
                "task": task,
                "type": "agent" if agent_or_team_id in self.active_agents else "team",
            }

            if agent_or_team_id in self.active_agents:
                # Execute with single agent
                agent = self.active_agents[agent_or_team_id]
                result["agent_name"] = agent.name
                result["agent_role"] = agent.role
                result["response"] = f"Analysis by {agent.name}: {task}"

                # Track KPIs if applicable
                if agent.kpis:
                    result["kpis_tracked"] = agent.kpis

                # Apply wisdom traits if mythology agent
                if agent.archetype:
                    result["divine_wisdom"] = agent.wisdom_traits

            elif agent_or_team_id in self.active_teams:
                # Execute with team
                team = self.active_teams[agent_or_team_id]
                result["team_name"] = team["name"]
                result["team_strategy"] = team["strategy"]
                result["okr_focus"] = team["okr_focus"]
                result["response"] = f"Team analysis by {team['name']}: {task}"
                result["agents_involved"] = [a.name for a in team["agents"]]

            else:
                raise ValueError(f"Agent or team '{agent_or_team_id}' not found")

            # Calculate execution time
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            result["execution_time"] = execution_time
            result["context"] = context or {}

            # Update performance metrics
            if agent_or_team_id in self.performance_metrics:
                metrics = self.performance_metrics[agent_or_team_id]
                metrics["tasks_completed"] += 1
                metrics["last_used"] = datetime.now(timezone.utc).isoformat()

                # Update average response time
                prev_avg = metrics["avg_response_time"]
                task_count = metrics["tasks_completed"]
                metrics["avg_response_time"] = (
                    (prev_avg * (task_count - 1)) + execution_time
                ) / task_count

            # Update business metrics
            self.business_metrics["analyses_completed"] += 1

            # Broadcast update if WebSocket connected
            await self._broadcast_task_update(result)

            return result

        except Exception as e:
            logger.error(f"Business task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "executor": agent_or_team_id,
                "execution_time": (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds(),
            }

        finally:
            await self._release_task_slot()

    async def calculate_okr_metrics(
        self, financial_data: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Calculate and update OKR metrics"""
        try:
            if financial_data:
                # Update OKR tracker with new financial data
                self.okr_tracker.total_revenue = financial_data.get(
                    "total_revenue", 0.0
                )
                self.okr_tracker.employee_count = financial_data.get(
                    "employee_count", 1
                )
                self.okr_tracker.revenue_per_employee = (
                    self.okr_tracker.total_revenue / self.okr_tracker.employee_count
                    if self.okr_tracker.employee_count > 0
                    else 0.0
                )

                # Calculate growth rate
                if financial_data.get("previous_revenue_per_employee"):
                    prev_rpe = financial_data["previous_revenue_per_employee"]
                    self.okr_tracker.growth_rate = (
                        (self.okr_tracker.revenue_per_employee - prev_rpe) / prev_rpe
                        if prev_rpe > 0
                        else 0.0
                    )

                # Calculate efficiency score
                self.okr_tracker.efficiency_score = min(
                    self.okr_tracker.revenue_per_employee
                    / max(self.okr_tracker.target_revenue_per_employee, 1),
                    1.0,
                )

                self.okr_tracker.last_updated = datetime.now(timezone.utc).isoformat()

            return {
                "current_metrics": {
                    "total_revenue": self.okr_tracker.total_revenue,
                    "employee_count": self.okr_tracker.employee_count,
                    "revenue_per_employee": self.okr_tracker.revenue_per_employee,
                    "target_revenue_per_employee": self.okr_tracker.target_revenue_per_employee,
                    "growth_rate": self.okr_tracker.growth_rate,
                    "efficiency_score": self.okr_tracker.efficiency_score,
                },
                "analysis_summary": {
                    "total_analyses": self.business_metrics["analyses_completed"],
                    "mythology_consultations": self.business_metrics[
                        "mythology_consultations"
                    ],
                    "strategic_plans": self.business_metrics["strategic_plans"],
                },
                "last_updated": self.okr_tracker.last_updated,
            }

        except Exception as e:
            logger.error(f"OKR calculation failed: {e}")
            return {"success": False, "error": str(e)}

    # ==============================================================================
    # WEBSOCKET AND REAL-TIME UPDATES
    # ==============================================================================

    async def _broadcast_task_update(self, result: dict[str, Any]):
        """Broadcast task updates via WebSocket"""
        if self.websocket_connections:
            update = {
                "type": "task_update",
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "active_tasks": self._concurrent_tasks,
                "queue_length": len(self._task_queue),
            }

            disconnected = set()
            for websocket in self.websocket_connections:
                try:
                    await websocket.send_json(update)
                except Exception:
                    disconnected.add(websocket)

            # Remove disconnected WebSockets
            self.websocket_connections -= disconnected

    async def add_websocket_connection(self, websocket: WebSocket):
        """Add WebSocket connection for real-time updates"""
        self.websocket_connections.add(websocket)
        logger.info(
            f"WebSocket connection added. Total: {len(self.websocket_connections)}"
        )

    async def remove_websocket_connection(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.websocket_connections.discard(websocket)
        logger.info(
            f"WebSocket connection removed. Total: {len(self.websocket_connections)}"
        )

    # ==============================================================================
    # QUERY AND STATUS METHODS
    # ==============================================================================

    def get_business_templates(self) -> dict[str, Any]:
        """Get all available business templates"""
        return {
            "business_agents": {
                name: {
                    "name": template.name,
                    "role": template.role,
                    "personality": template.personality,
                    "domain": template.domain,
                    "capabilities": template.capabilities,
                    "kpis": template.kpis,
                    "model": template.model,
                }
                for name, template in self.business_templates.items()
            },
            "mythology_agents": {
                name: {
                    "name": agent.name,
                    "archetype": agent.archetype.value if agent.archetype else None,
                    "wisdom_traits": agent.wisdom_traits,
                    "capabilities": agent.capabilities,
                    "model": agent.model,
                }
                for name, agent in self.mythology_agents.items()
            },
        }

    def get_team_templates(self) -> dict[str, Any]:
        """Get all team templates"""
        return {
            name: {
                "name": team.name,
                "description": team.description,
                "team_type": team.team_type.value,
                "strategy": team.strategy,
                "agents_count": len(team.agents),
                "okr_focus": team.okr_focus,
            }
            for name, team in self.business_teams.items()
        }

    def get_factory_metrics(self) -> dict[str, Any]:
        """Get factory performance metrics"""
        return {
            "business_metrics": self.business_metrics,
            "okr_metrics": {
                "revenue_per_employee": self.okr_tracker.revenue_per_employee,
                "target_revenue_per_employee": self.okr_tracker.target_revenue_per_employee,
                "efficiency_score": self.okr_tracker.efficiency_score,
                "growth_rate": self.okr_tracker.growth_rate,
            },
            "active_agents": len(self.active_agents),
            "active_teams": len(self.active_teams),
            "active_swarms": len(self.analytical_swarms),
            "task_status": {
                "active_tasks": self._concurrent_tasks,
                "max_concurrent": self.config.max_concurrent_tasks,
                "queued_tasks": len(self._task_queue),
                "capacity_available": self._concurrent_tasks
                < self.config.max_concurrent_tasks,
            },
            "total_operations": sum(self.business_metrics.values()),
            "domain": self.config.domain.value,
            "capabilities": self.config.capabilities,
        }

    def list_active_agents(self) -> list[dict[str, Any]]:
        """List all active agents"""
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "personality": agent.personality,
                "domain": agent.domain,
                "archetype": agent.archetype.value if agent.archetype else None,
                "kpis": agent.kpis,
            }
            for agent in self.active_agents.values()
        ]

    def list_active_teams(self) -> list[dict[str, Any]]:
        """List all active teams"""
        return [
            {
                "id": team["id"],
                "name": team["name"],
                "team_type": (
                    team["team_type"].value
                    if isinstance(team["team_type"], Enum)
                    else team["team_type"]
                ),
                "agents_count": len(team["agents"]),
                "strategy": team["strategy"],
                "okr_focus": team["okr_focus"],
                "status": team["status"],
                "created_at": team["created_at"],
            }
            for team in self.active_teams.values()
        ]

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics for all agents and teams"""
        total_agents = len(self.active_agents)
        total_teams = len(self.active_teams)
        total_tasks = sum(
            metrics.get("tasks_completed", 0)
            for metrics in self.performance_metrics.values()
        )

        avg_response_time = 0.0
        if self.performance_metrics:
            total_time = sum(
                metrics.get("avg_response_time", 0.0)
                for metrics in self.performance_metrics.values()
            )
            avg_response_time = total_time / len(self.performance_metrics)

        return {
            "total_agents_created": total_agents,
            "total_teams_created": total_teams,
            "total_tasks_completed": total_tasks,
            "average_response_time": round(avg_response_time, 2),
            "agent_performance": self.performance_metrics,
            "most_used_agents": self._get_most_used_agents(),
            "domain_distribution": self._get_domain_distribution(),
        }

    def _get_most_used_agents(self) -> list[dict[str, Any]]:
        """Get most frequently used agents"""
        agent_usage = []
        for agent_id, metrics in self.performance_metrics.items():
            if agent_id in self.active_agents:
                agent = self.active_agents[agent_id]
                agent_usage.append(
                    {
                        "id": agent_id,
                        "name": agent.name,
                        "tasks_completed": metrics.get("tasks_completed", 0),
                        "avg_response_time": metrics.get("avg_response_time", 0.0),
                    }
                )

        # Sort by tasks completed
        agent_usage.sort(key=lambda x: x["tasks_completed"], reverse=True)
        return agent_usage[:5]  # Top 5

    def _get_domain_distribution(self) -> dict[str, int]:
        """Get distribution of agents by domain"""
        domain_counts = {}
        for agent in self.active_agents.values():
            if agent.domain:
                domain_key = (
                    agent.domain.value
                    if isinstance(agent.domain, Enum)
                    else agent.domain
                )
                domain_counts[domain_key] = domain_counts.get(domain_key, 0) + 1
        return domain_counts


# ==============================================================================
# FACTORY INSTANCE
# ==============================================================================

# Global factory instance
sophia_unified_factory = SophiaUnifiedFactory()

# ==============================================================================
# FASTAPI ROUTER
# ==============================================================================

router = APIRouter(prefix="/api/sophia/unified", tags=["sophia-unified-factory"])


@router.post("/agents/create")
async def create_agent(request: dict[str, Any]):
    """Create a business agent"""
    try:
        template = request.get("template")
        config = request.get("config", {})

        if not template:
            raise HTTPException(status_code=400, detail="Template name required")

        agent_id = await sophia_unified_factory.create_business_agent(template, config)

        return {
            "success": True,
            "agent_id": agent_id,
            "template": template,
            "status": "deployed",
        }
    except Exception as e:
        logger.error(f"Agent creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teams/create")
async def create_team(request: dict[str, Any]):
    """Create a business team"""
    try:
        template = request.get("template")
        config = request.get("config", {})

        if not template:
            raise HTTPException(status_code=400, detail="Team template required")

        team_id = await sophia_unified_factory.create_business_team(template, config)

        return {
            "success": True,
            "team_id": team_id,
            "template": template,
            "status": "operational",
        }
    except Exception as e:
        logger.error(f"Team creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/execute")
async def execute_task(request: dict[str, Any]):
    """Execute a business task"""
    try:
        executor = request.get("executor")
        task = request.get("task")
        context = request.get("context", {})

        if not executor or not task:
            raise HTTPException(status_code=400, detail="Executor and task required")

        result = await sophia_unified_factory.execute_business_task(
            executor, task, context
        )

        return result
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/okr/calculate")
async def calculate_okr(request: dict[str, Any]):
    """Calculate OKR metrics"""
    try:
        financial_data = request.get("financial_data")
        result = await sophia_unified_factory.calculate_okr_metrics(financial_data)
        return result
    except Exception as e:
        logger.error(f"OKR calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_factory_status():
    """Get factory status and metrics"""
    return sophia_unified_factory.get_factory_metrics()


@router.get("/templates")
async def get_templates():
    """Get all available templates"""
    return {
        "business_templates": sophia_unified_factory.get_business_templates(),
        "team_templates": sophia_unified_factory.get_team_templates(),
    }


@router.get("/agents")
async def list_agents():
    """List all active agents"""
    return {
        "agents": sophia_unified_factory.list_active_agents(),
        "total": len(sophia_unified_factory.active_agents),
    }


@router.get("/teams")
async def list_teams():
    """List all active teams"""
    return {
        "teams": sophia_unified_factory.list_active_teams(),
        "total": len(sophia_unified_factory.active_teams),
    }


@router.get("/performance")
async def get_performance():
    """Get performance metrics"""
    return sophia_unified_factory.get_performance_metrics()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    await sophia_unified_factory.add_websocket_connection(websocket)

    try:
        while True:
            # Keep connection alive and handle messages
            await websocket.receive_text()
            # Process commands if needed
    except Exception:
        pass
    finally:
        await sophia_unified_factory.remove_websocket_connection(websocket)
