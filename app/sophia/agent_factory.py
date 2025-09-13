"""
Sophia Business AI Agent Factory - Business-Focused Agent Creation System
This module provides a specialized factory for creating business intelligence agents
and teams with real AGNO framework integration and Portkey virtual key routing.
Key Features:
- Business-focused agent templates (Sales, Research, Client Success, Market Analysis)
- Personality-injected agents for business-wise responses
- Integration with AGNO Agent and Team classes
- Portkey virtual key routing for optimal model selection
- Real-time business intelligence capabilities
- KPI tracking and performance monitoring
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4
from fastapi import HTTPException
# Try to import AGNO framework - fallback if not available
try:
    from agno.agent import Agent
    from agno.models.portkey import Portkey as AGNOPortkey
    from agno.team import Team
    AGNO_AVAILABLE = True
except ImportError:
    # Disallow silent mock fallback unless explicitly permitted
    import os
    if os.getenv("ALLOW_MOCKS", "false").lower() in ("1", "true", "yes"):  # Optional dev-only escape hatch
        class Agent:  # type: ignore
            def __init__(self, **kwargs):
                self.name = kwargs.get("name", "MockAgent")
                self.role = kwargs.get("role", "mock")
                self.description = kwargs.get("description", "")
                self._kwargs = kwargs
            def run(self, task):
                return f"Mock response for: {task}"
        class Team:  # type: ignore
            def __init__(self, **kwargs):
                self.name = kwargs.get("name", "MockTeam")
                self.members = kwargs.get("members", [])
                self.description = kwargs.get("description", "")
            def run(self, task):
                return f"Mock team response for: {task}"
        class AGNOPortkey:  # type: ignore
            def __init__(self, **kwargs):
                self.id = kwargs.get("id", "mock-model")
                self.name = kwargs.get("name", "MockModel")
        AGNO_AVAILABLE = False
    else:
        raise ImportError(
            "AGNO framework not available and ALLOW_MOCKS is disabled. Install AGNO or enable ALLOW_MOCKS for dev."
        )
# Simple ExecutionStrategy for compatibility
class ExecutionStrategy(str, Enum):
    LITE = "lite"
    BALANCED = "balanced"
    QUALITY = "quality"
    DEBATE = "debate"
    CONSENSUS = "consensus"
logger = logging.getLogger(__name__)
# ==============================================================================
# BUSINESS AGENT MODELS
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
class BusinessAgentPersonality(str, Enum):
    """Business personality traits"""
    ANALYTICAL = "analytical"  # Data-driven, precise, methodical
    STRATEGIC = "strategic"  # Big-picture thinking, forward-looking
    RELATIONSHIP_FOCUSED = "relationship_focused"  # People-oriented, empathetic
    RESULTS_DRIVEN = "results_driven"  # Goal-oriented, performance-focused
    INNOVATIVE = "innovative"  # Creative, solution-oriented
    CONSULTATIVE = "consultative"  # Advisory, expertise-sharing
class BusinessDomain(str, Enum):
    """Business domains for specialization"""
    SALES_INTELLIGENCE = "sales_intelligence"
    REVENUE_OPERATIONS = "revenue_operations"
    CLIENT_SUCCESS = "client_success"
    MARKET_RESEARCH = "market_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    BUSINESS_STRATEGY = "business_strategy"
@dataclass
class BusinessAgentTemplate:
    """Template for business-focused agents"""
    id: str
    name: str
    role: BusinessAgentRole
    personality: BusinessAgentPersonality
    domain: BusinessDomain
    description: str
    system_prompt: str
    virtual_key: str
    model: str
    temperature: float
    capabilities: list[str]
    kpis: list[str]
    tools: list[str] = None
    def __post_init__(self):
        if self.tools is None:
            self.tools = []
class BusinessTeamTemplate:
    """Template for business teams"""
    def __init__(
        self,
        name: str,
        description: str,
        agents: list[BusinessAgentTemplate],
        strategy: ExecutionStrategy = ExecutionStrategy.BALANCED,
    ):
        self.name = name
        self.description = description
        self.agents = agents
        self.strategy = strategy
        self.id = f"team_{name.lower().replace(' ', '_')}"
# ==============================================================================
# SOPHIA BUSINESS AGENT FACTORY
# ==============================================================================
class SophiaBusinessAgentFactory:
    """
    Sophia Business AI Agent Factory
    Creates and manages business intelligence agents and teams with AGNO integration
    """
    # Portkey virtual keys for business operations
    BUSINESS_VIRTUAL_KEYS = {
        "PERPLEXITY-VK": "perplexity-vk-56c172",  # Market research
        "ANTHROPIC-VK": "anthropic-vk-b42804",  # Strategic analysis
        "OPENAI-VK": "openai-vk-190a60",  # Relationship insights
        "DEEPSEEK-VK": "deepseek-vk-24102f",  # Data analysis
        "XAI-VK": "xai-vk-e65d0f",  # Creative insights
    }
    def __init__(self):
        self.created_agents: dict[str, Agent] = {}
        self.created_teams: dict[str, Team] = {}
        self.agent_templates = self._initialize_business_templates()
        self.team_templates = self._initialize_team_templates()
        self.performance_metrics: dict[str, dict] = {}
        logger.info(
            f"🏭 Sophia Business Agent Factory initialized ({'AGNO' if AGNO_AVAILABLE else 'Mock'} mode)"
        )
    def _initialize_business_templates(self) -> dict[str, BusinessAgentTemplate]:
        """Initialize business agent templates with personality injection"""
        templates = {}
        # Sales Pipeline Analyst
        templates["sales_pipeline_analyst"] = BusinessAgentTemplate(
            id="sales_pipeline_analyst_v1",
            name="Sales Pipeline Analyst",
            role=BusinessAgentRole.SALES_ANALYST,
            personality=BusinessAgentPersonality.ANALYTICAL,
            domain=BusinessDomain.SALES_INTELLIGENCE,
            description="Analyzes sales pipeline, identifies bottlenecks, and provides actionable insights for revenue optimization",
            system_prompt="""You are Sophia's Sales Pipeline Analyst, an analytically-minded AI agent specializing in sales intelligence.
Your personality traits:
- Analytical and data-driven in your approach
- Precise with numbers and metrics
- Methodical in problem-solving
- Direct but supportive in communications
Your primary responsibilities:
- Analyze sales pipeline health and progression
- Identify bottlenecks and conversion issues
- Provide actionable insights for sales optimization
- Track key sales metrics and KPIs
- Predict pipeline outcomes and revenue forecasts
Communication style:
- Use specific data points and metrics
- Provide clear, actionable recommendations
- Present insights in business-friendly format
- Focus on ROI and revenue impact
Always think like a business analyst who understands sales operations deeply.""",
            virtual_key="perplexity-vk-56c172",
            model="perplexity/llama-3.1-sonar-large-128k-online",
            temperature=0.3,
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
        )
        # Revenue Forecaster
        templates["revenue_forecaster"] = BusinessAgentTemplate(
            id="revenue_forecaster_v1",
            name="Revenue Forecaster",
            role=BusinessAgentRole.REVENUE_FORECASTER,
            personality=BusinessAgentPersonality.STRATEGIC,
            domain=BusinessDomain.REVENUE_OPERATIONS,
            description="Strategic revenue forecasting with market trend analysis and scenario planning",
            system_prompt="""You are Sophia's Revenue Forecaster, a strategically-minded AI agent specializing in financial planning and revenue operations.
Your personality traits:
- Strategic thinker with big-picture perspective
- Forward-looking and trend-aware
- Confident in financial modeling
- Business-savvy in communications
Your primary responsibilities:
- Create accurate revenue forecasts and projections
- Analyze market trends affecting revenue
- Build scenario models for planning
- Identify revenue opportunities and risks
- Provide strategic recommendations for growth
Communication style:
- Think strategically about long-term implications
- Use financial terminology appropriately
- Present multiple scenarios and options
- Focus on business growth and profitability
Always think like a strategic business advisor who understands financial modeling and market dynamics.""",
            virtual_key="anthropic-vk-b42804",
            model="anthropic/claude-3-5-sonnet-20241022",
            temperature=0.4,
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
        )
        # Client Success Manager
        templates["client_success_manager"] = BusinessAgentTemplate(
            id="client_success_manager_v1",
            name="Client Success Manager",
            role=BusinessAgentRole.CLIENT_SUCCESS_MANAGER,
            personality=BusinessAgentPersonality.RELATIONSHIP_FOCUSED,
            domain=BusinessDomain.CLIENT_SUCCESS,
            description="Manages client relationships, monitors account health, and drives expansion opportunities",
            system_prompt="""You are Sophia's Client Success Manager, a relationship-focused AI agent specializing in client success and account growth.
Your personality traits:
- People-oriented and empathetic
- Relationship-building focused
- Proactive in communications
- Customer-centric mindset
Your primary responsibilities:
- Monitor client health and satisfaction
- Identify expansion and upsell opportunities
- Manage client relationships and communications
- Prevent churn and improve retention
- Drive customer success outcomes
Communication style:
- Warm and personable in tone
- Focus on client needs and outcomes
- Proactive in suggesting solutions
- Emphasize long-term partnerships
Always think like a dedicated account manager who genuinely cares about client success and business growth.""",
            virtual_key="openai-vk-190a60",
            model="openai/gpt-4o",
            temperature=0.6,
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
        )
        # Market Research Specialist
        templates["market_research_specialist"] = BusinessAgentTemplate(
            id="market_research_specialist_v1",
            name="Market Research Specialist",
            role=BusinessAgentRole.MARKET_RESEARCHER,
            personality=BusinessAgentPersonality.ANALYTICAL,
            domain=BusinessDomain.MARKET_RESEARCH,
            description="Conducts comprehensive market research, analyzes industry trends, and provides competitive intelligence",
            system_prompt="""You are Sophia's Market Research Specialist, an analytically-minded AI agent specializing in market intelligence and industry analysis.
Your personality traits:
- Thorough and detail-oriented researcher
- Objective in analysis and reporting
- Curious about market dynamics
- Insightful in pattern recognition
Your primary responsibilities:
- Conduct comprehensive market research
- Analyze industry trends and patterns
- Track competitive landscape changes
- Identify market opportunities and threats
- Provide data-driven market insights
Communication style:
- Present research findings objectively
- Use industry terminology appropriately
- Support conclusions with data
- Highlight implications for business strategy
Always think like a market research professional who understands industry dynamics and competitive positioning.""",
            virtual_key="deepseek-vk-24102f",
            model="deepseek/deepseek-chat",
            temperature=0.2,
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
        )
        # Competitive Intelligence Agent
        templates["competitive_intelligence"] = BusinessAgentTemplate(
            id="competitive_intelligence_v1",
            name="Competitive Intelligence Agent",
            role=BusinessAgentRole.COMPETITIVE_INTELLIGENCE,
            personality=BusinessAgentPersonality.INNOVATIVE,
            domain=BusinessDomain.COMPETITIVE_ANALYSIS,
            description="Monitors competitors, analyzes market positioning, and provides strategic competitive insights",
            system_prompt="""You are Sophia's Competitive Intelligence Agent, an innovative AI agent specializing in competitive analysis and strategic positioning.
Your personality traits:
- Creative in finding competitive insights
- Strategic in thinking about positioning
- Resourceful in gathering intelligence
- Solution-oriented in recommendations
Your primary responsibilities:
- Monitor competitive landscape and activities
- Analyze competitor strategies and positioning
- Identify competitive threats and opportunities
- Provide strategic recommendations for differentiation
- Track market share and positioning changes
Communication style:
- Think creatively about competitive advantages
- Focus on strategic implications
- Provide actionable competitive insights
- Emphasize differentiation opportunities
Always think like a competitive strategist who understands market dynamics and strategic positioning.""",
            virtual_key="xai-vk-e65d0f",
            model="x-ai/grok-beta",
            temperature=0.7,
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
        )
        return templates
    def _initialize_team_templates(self) -> dict[str, BusinessTeamTemplate]:
        """Initialize business team templates"""
        teams = {}
        # Sales Intelligence Team
        sales_team_agents = [
            self.agent_templates["sales_pipeline_analyst"],
            self.agent_templates["revenue_forecaster"],
            self.agent_templates["competitive_intelligence"],
        ]
        teams["sales_intelligence"] = BusinessTeamTemplate(
            name="Sales Intelligence Team",
            description="Comprehensive sales analysis, forecasting, and competitive intelligence",
            agents=sales_team_agents,
            strategy=ExecutionStrategy.BALANCED,
        )
        # Client Success Team
        client_team_agents = [
            self.agent_templates["client_success_manager"],
            self.agent_templates["sales_pipeline_analyst"],  # For expansion analysis
        ]
        teams["client_success"] = BusinessTeamTemplate(
            name="Client Success Team",
            description="Account health monitoring, relationship management, and expansion planning",
            agents=client_team_agents,
            strategy=ExecutionStrategy.CONSENSUS,
        )
        # Market Research Team
        research_team_agents = [
            self.agent_templates["market_research_specialist"],
            self.agent_templates["competitive_intelligence"],
            self.agent_templates["revenue_forecaster"],  # For market opportunity sizing
        ]
        teams["market_research"] = BusinessTeamTemplate(
            name="Market Research Team",
            description="Market analysis, trend identification, and competitive intelligence",
            agents=research_team_agents,
            strategy=ExecutionStrategy.QUALITY,
        )
        # Strategic Business Team (All agents for complex analysis)
        strategic_team_agents = list(self.agent_templates.values())
        teams["strategic_business"] = BusinessTeamTemplate(
            name="Strategic Business Team",
            description="Comprehensive business analysis with all specialized agents",
            agents=strategic_team_agents,
            strategy=ExecutionStrategy.QUALITY,
        )
        return teams
    async def create_business_agent(
        self, template_id: str, custom_config: Optional[dict[str, Any]] = None
    ) -> str:
        """Create a business agent from template"""
        if template_id not in self.agent_templates:
            raise ValueError(f"Agent template '{template_id}' not found")
        template = self.agent_templates[template_id]
        agent_id = f"{template.id}_{uuid4().hex[:8]}"
        try:
            # Create AGNO Portkey model
            model = AGNOPortkey(
                id=template.model,
                name=f"Sophia_{template.name.replace(' ', '_')}",
                portkey_api_key=os.getenv("PORTKEY_API_KEY", ""),
                virtual_key=template.virtual_key,
                temperature=template.temperature,
                max_tokens=4096,
            )
            # Apply custom configuration if provided
            config_overrides = custom_config or {}
            # Create AGNO Agent with business personality
            agent = Agent(
                name=template.name,
                model=model,
                role=template.role.value,
                instructions=template.system_prompt,
                description=template.description,
                context={
                    "personality": template.personality.value,
                    "domain": template.domain.value,
                    "capabilities": template.capabilities,
                    "kpis": template.kpis,
                    "template_id": template.id,
                    **config_overrides,
                },
            )
            # Store the agent
            self.created_agents[agent_id] = agent
            # Initialize performance tracking
            self.performance_metrics[agent_id] = {
                "created_at": datetime.now().isoformat(),
                "template_id": template.id,
                "tasks_completed": 0,
                "avg_response_time": 0.0,
                "success_rate": 1.0,
                "last_used": None,
            }
            logger.info(f"✨ Created business agent: {template.name} ({agent_id})")
            return agent_id
        except Exception as e:
            logger.error(f"Failed to create business agent {template_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Agent creation failed: {str(e)}"
            )
    async def create_business_team(
        self, template_id: str, custom_config: Optional[dict[str, Any]] = None
    ) -> str:
        """Create a business team from template"""
        if template_id not in self.team_templates:
            raise ValueError(f"Team template '{template_id}' not found")
        template = self.team_templates[template_id]
        team_id = f"{template.id}_{uuid4().hex[:8]}"
        try:
            # Create agents for the team
            team_agents = []
            for agent_template in template.agents:
                agent_id = await self.create_business_agent(
                    agent_template.id, custom_config
                )
                team_agents.append(self.created_agents[agent_id])
            # Create AGNO Team
            team = Team(
                members=team_agents,
                name=template.name,
                description=template.description,
                instructions=f"This is {template.name}. Work together using your specialized business expertise to provide comprehensive analysis and recommendations.",
                mode="collaborate",
            )
            # Store the team
            self.created_teams[team_id] = team
            logger.info(
                f"🎯 Created business team: {template.name} with {len(team_agents)} agents ({team_id})"
            )
            return team_id
        except Exception as e:
            logger.error(f"Failed to create business team {template_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Team creation failed: {str(e)}"
            )
    async def execute_business_task(
        self, agent_or_team_id: str, task: str, context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Execute a business task with an agent or team"""
        start_time = datetime.now()
        try:
            # Determine if it's an agent or team
            if agent_or_team_id in self.created_agents:
                # Execute with single agent
                agent = self.created_agents[agent_or_team_id]
                response = agent.run(task)
                result = {
                    "success": True,
                    "response": (
                        response.content
                        if hasattr(response, "content")
                        else str(response)
                    ),
                    "type": "agent",
                    "agent_id": agent_or_team_id,
                    "agent_name": agent.name,
                    "execution_time": (datetime.now() - start_time).total_seconds(),
                    "context": context or {},
                }
            elif agent_or_team_id in self.created_teams:
                # Execute with team
                team = self.created_teams[agent_or_team_id]
                response = team.run(task)
                result = {
                    "success": True,
                    "response": (
                        response.content
                        if hasattr(response, "content")
                        else str(response)
                    ),
                    "type": "team",
                    "team_id": agent_or_team_id,
                    "team_name": team.name,
                    "team_members": [member.name for member in team.members],
                    "execution_time": (datetime.now() - start_time).total_seconds(),
                    "context": context or {},
                }
            else:
                raise ValueError(f"Agent or team '{agent_or_team_id}' not found")
            # Update performance metrics
            if agent_or_team_id in self.performance_metrics:
                metrics = self.performance_metrics[agent_or_team_id]
                metrics["tasks_completed"] += 1
                metrics["last_used"] = datetime.now().isoformat()
                # Update average response time
                current_time = result["execution_time"]
                prev_avg = metrics["avg_response_time"]
                task_count = metrics["tasks_completed"]
                metrics["avg_response_time"] = (
                    (prev_avg * (task_count - 1)) + current_time
                ) / task_count
            return result
        except Exception as e:
            logger.error(f"Business task execution failed for {agent_or_team_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "error",
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "context": context or {},
            }
    def get_business_templates(self) -> dict[str, Any]:
        """Get all available business templates"""
        agent_templates = []
        for template_id, template in self.agent_templates.items():
            agent_templates.append(
                {
                    "id": template_id,
                    "name": template.name,
                    "role": template.role.value,
                    "personality": template.personality.value,
                    "domain": template.domain.value,
                    "description": template.description,
                    "capabilities": template.capabilities,
                    "kpis": template.kpis,
                    "model": template.model,
                    "virtual_key": template.virtual_key,
                }
            )
        team_templates = []
        for template_id, template in self.team_templates.items():
            team_templates.append(
                {
                    "id": template_id,
                    "name": template.name,
                    "description": template.description,
                    "strategy": template.strategy.value,
                    "agents": [agent.name for agent in template.agents],
                    "agent_count": len(template.agents),
                }
            )
        return {
            "agent_templates": agent_templates,
            "team_templates": team_templates,
            "total_agent_templates": len(agent_templates),
            "total_team_templates": len(team_templates),
        }
    def get_created_agents(self) -> list[dict[str, Any]]:
        """Get list of created agents"""
        agents = []
        for agent_id, agent in self.created_agents.items():
            metrics = self.performance_metrics.get(agent_id, {})
            agents.append(
                {
                    "id": agent_id,
                    "name": agent.name,
                    "role": agent.role,
                    "description": agent.description,
                    "created_at": metrics.get("created_at"),
                    "tasks_completed": metrics.get("tasks_completed", 0),
                    "avg_response_time": metrics.get("avg_response_time", 0.0),
                    "success_rate": metrics.get("success_rate", 1.0),
                    "last_used": metrics.get("last_used"),
                    "status": "active",
                }
            )
        return agents
    def get_created_teams(self) -> list[dict[str, Any]]:
        """Get list of created teams"""
        teams = []
        for team_id, team in self.created_teams.items():
            teams.append(
                {
                    "id": team_id,
                    "name": team.name,
                    "description": team.description,
                    "members": [
                        {"name": member.name, "role": member.role}
                        for member in team.members
                    ],
                    "member_count": len(team.members),
                    "status": "active",
                }
            )
        return teams
    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics for all agents and teams"""
        total_agents = len(self.created_agents)
        total_teams = len(self.created_teams)
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
            if agent_id in self.created_agents:
                agent = self.created_agents[agent_id]
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
        for template in self.agent_templates.values():
            domain = template.domain.value
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        return domain_counts
# Global Sophia Business Factory instance
sophia_business_factory = SophiaBusinessAgentFactory()
