"""
Sophia AGNO Teams Implementation
Business Intelligence Teams using AGNO framework with personality-driven responses
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

from app.swarms.agno_teams import (
    SophiaAGNOTeam, 
    AGNOTeamConfig, 
    ExecutionStrategy
)
from agno.agent import Agent
from agno.team import Team

logger = logging.getLogger(__name__)


class BusinessDomain(Enum):
    """Business domain specializations"""
    SALES_INTELLIGENCE = "sales_intelligence"
    RESEARCH = "research"
    CLIENT_SUCCESS = "client_success"
    MARKET_ANALYSIS = "market_analysis"


@dataclass
class BusinessPersonality:
    """Sophia's business personality traits"""
    communication_style: str = "strategic_professional"
    expertise_level: str = "executive"
    response_tone: str = "confident_insightful"
    business_focus: str = "revenue_optimization"


class SophiaSalesIntelligenceTeam(SophiaAGNOTeam):  # Changed from SophiaAGNOTeam
    """
    Sales Intelligence AGNO Team
    Specialized in pipeline management, deal analysis, and revenue optimization
    """
    
    def __init__(self, config: Optional[AGNOTeamConfig] = None):
        if not config:
            config = AGNOTeamConfig(
                name="sophia_sales_intelligence",
                strategy=ExecutionStrategy.QUALITY,
                max_agents=5,
                timeout=45,
                enable_memory=True,
                auto_tag=True
            )
        super().__init__(config)
        self.domain = BusinessDomain.SALES_INTELLIGENCE
        self.personality = BusinessPersonality(
            communication_style="strategic_sales_focused",
            expertise_level="senior_sales_executive",
            response_tone="confident_revenue_driven",
            business_focus="pipeline_and_deals"
        )
    
    async def initialize(self):
        """Initialize with sales-focused agents"""
        await super().initialize()
        
        # Add specialized sales intelligence agents
        sales_agents = {
            "pipeline_analyst": {
                "role": "pipeline_analyst",
                "model": self.APPROVED_MODELS["planner"],
                "instructions": """You are Sophia's Pipeline Analyst. Analyze sales pipelines, deal progression, and revenue forecasting with strategic business insight. 
                Provide actionable recommendations for pipeline optimization and deal acceleration. Focus on data-driven insights that drive revenue growth.""",
                "temperature": 0.3
            },
            "deal_strategist": {
                "role": "deal_strategist", 
                "model": self.APPROVED_MODELS["generator"],
                "instructions": """You are Sophia's Deal Strategist. Analyze individual deals, competitive positioning, and closing strategies.
                Provide tactical recommendations for deal advancement and risk mitigation. Think like a seasoned sales executive with deep market knowledge.""",
                "temperature": 0.6
            },
            "revenue_forecaster": {
                "role": "revenue_forecaster",
                "model": self.APPROVED_MODELS["judge"],
                "instructions": """You are Sophia's Revenue Forecaster. Analyze sales data, market trends, and performance metrics to create accurate revenue projections.
                Provide strategic insights on quota achievement, growth trajectories, and revenue optimization opportunities.""",
                "temperature": 0.2
            },
            "competitive_analyst": {
                "role": "competitive_analyst",
                "model": self.APPROVED_MODELS["critic"],
                "instructions": """You are Sophia's Competitive Intelligence Analyst. Analyze competitive landscape, win/loss patterns, and market positioning.
                Provide strategic insights on competitive advantages, threats, and positioning opportunities that impact sales success.""",
                "temperature": 0.4
            },
            "sales_coach": {
                "role": "sales_coach",
                "model": self.APPROVED_MODELS["lead"],
                "instructions": """You are Sophia's Sales Coach. Analyze sales performance, call recordings, and sales methodologies.
                Provide coaching insights and recommendations for sales team improvement. Focus on practical advice that increases win rates and deal velocity.""",
                "temperature": 0.5
            }
        }
        
        # Create and add agents to team
        for role, config in sales_agents.items():
            agent = await self._create_specialized_agent(role, config)
            self.team.add_agent(agent)
            
        logger.info(f"💎 Sophia Sales Intelligence Team initialized with {len(sales_agents)} specialized agents")
    
    async def analyze_pipeline_health(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sales pipeline health and provide strategic insights"""
        
        task = Task(
            description=f"Analyze sales pipeline health and provide strategic recommendations: {json.dumps(pipeline_data, indent=2)}",
            metadata={
                "task_type": "pipeline_analysis",
                "domain": "sales_intelligence",
                "priority": "high"
            }
        )
        
        result = await self.execute_task(
            "Conduct comprehensive sales pipeline analysis focusing on deal progression, risk assessment, and revenue optimization opportunities",
            context={"pipeline_data": pipeline_data, "analysis_type": "health_assessment"}
        )
        
        return self._enhance_with_business_personality(result, "pipeline_analysis")
    
    async def analyze_deal_strategy(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze specific deal and provide strategic recommendations"""
        
        result = await self.execute_task(
            f"Analyze deal strategy and provide recommendations for advancing this opportunity: {json.dumps(deal_data, indent=2)}",
            context={"deal_data": deal_data, "analysis_type": "deal_strategy"}
        )
        
        return self._enhance_with_business_personality(result, "deal_analysis")
    
    async def forecast_revenue(self, historical_data: Dict[str, Any], forecast_period: str) -> Dict[str, Any]:
        """Generate revenue forecast with confidence intervals"""
        
        result = await self.execute_task(
            f"Generate {forecast_period} revenue forecast based on historical performance and current pipeline data",
            context={"historical_data": historical_data, "forecast_period": forecast_period}
        )
        
        return self._enhance_with_business_personality(result, "revenue_forecast")


class SophiaResearchTeam(SophiaAGNOTeam):
    """
    Research AGNO Team
    Specialized in market research, competitive intelligence, and industry analysis
    """
    
    def __init__(self, config: Optional[AGNOTeamConfig] = None):
        if not config:
            config = AGNOTeamConfig(
                name="sophia_research",
                strategy=ExecutionStrategy.CONSENSUS,
                max_agents=4,
                timeout=60,
                enable_memory=True,
                auto_tag=True
            )
        super().__init__(config)
        self.domain = BusinessDomain.RESEARCH
        self.personality = BusinessPersonality(
            communication_style="analytical_strategic",
            expertise_level="research_director",
            response_tone="insightful_data_driven",
            business_focus="market_intelligence"
        )
    
    async def initialize(self):
        """Initialize with research-focused agents"""
        await super().initialize()
        
        research_agents = {
            "market_researcher": {
                "role": "market_researcher",
                "model": self.APPROVED_MODELS["planner"],
                "instructions": """You are Sophia's Market Research Analyst. Conduct comprehensive market analysis, trend identification, and opportunity assessment.
                Provide strategic insights on market size, growth opportunities, and competitive landscape that inform business strategy decisions.""",
                "temperature": 0.4
            },
            "industry_analyst": {
                "role": "industry_analyst",
                "model": self.APPROVED_MODELS["generator"],
                "instructions": """You are Sophia's Industry Analyst. Analyze industry trends, regulatory changes, and technological disruptions.
                Provide strategic intelligence on industry dynamics that impact business opportunities and competitive positioning.""",
                "temperature": 0.5
            },
            "competitive_researcher": {
                "role": "competitive_researcher",
                "model": self.APPROVED_MODELS["critic"],
                "instructions": """You are Sophia's Competitive Research Specialist. Research competitor strategies, products, pricing, and market positioning.
                Provide detailed competitive intelligence that enables strategic differentiation and market advantage.""",
                "temperature": 0.3
            },
            "strategic_synthesizer": {
                "role": "strategic_synthesizer",
                "model": self.APPROVED_MODELS["judge"],
                "instructions": """You are Sophia's Strategic Research Synthesizer. Integrate multiple research streams into cohesive strategic insights.
                Synthesize market research, competitive analysis, and industry trends into actionable business intelligence and strategic recommendations.""",
                "temperature": 0.4
            }
        }
        
        for role, config in research_agents.items():
            agent = await self._create_specialized_agent(role, config)
            self.team.add_agent(agent)
            
        logger.info(f"💎 Sophia Research Team initialized with {len(research_agents)} specialized agents")
    
    async def conduct_market_research(self, research_scope: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct comprehensive market research"""
        
        result = await self.execute_task(
            f"Conduct comprehensive market research analysis: {json.dumps(research_scope, indent=2)}",
            context={"research_scope": research_scope, "analysis_type": "market_research"}
        )
        
        return self._enhance_with_business_personality(result, "market_research")
    
    async def analyze_competitive_landscape(self, competitor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze competitive landscape and positioning"""
        
        result = await self.execute_task(
            f"Analyze competitive landscape and provide strategic positioning recommendations: {json.dumps(competitor_data, indent=2)}",
            context={"competitor_data": competitor_data, "analysis_type": "competitive_analysis"}
        )
        
        return self._enhance_with_business_personality(result, "competitive_analysis")


class SophiaClientSuccessTeam(SophiaAGNOTeam):
    """
    Client Success AGNO Team  
    Specialized in customer health monitoring, retention strategies, and expansion opportunities
    """
    
    def __init__(self, config: Optional[AGNOTeamConfig] = None):
        if not config:
            config = AGNOTeamConfig(
                name="sophia_client_success",
                strategy=ExecutionStrategy.BALANCED,
                max_agents=4,
                timeout=40,
                enable_memory=True,
                auto_tag=True
            )
        super().__init__(config)
        self.domain = BusinessDomain.CLIENT_SUCCESS
        self.personality = BusinessPersonality(
            communication_style="relationship_focused",
            expertise_level="customer_success_director",
            response_tone="empathetic_strategic",
            business_focus="customer_lifetime_value"
        )
    
    async def initialize(self):
        """Initialize with client success focused agents"""
        await super().initialize()
        
        success_agents = {
            "health_monitor": {
                "role": "health_monitor",
                "model": self.APPROVED_MODELS["planner"],
                "instructions": """You are Sophia's Client Health Monitor. Analyze customer health metrics, usage patterns, and engagement levels.
                Provide early warning signals for churn risk and identify opportunities for deeper engagement and value realization.""",
                "temperature": 0.3
            },
            "retention_strategist": {
                "role": "retention_strategist",
                "model": self.APPROVED_MODELS["generator"],
                "instructions": """You are Sophia's Retention Strategist. Develop strategies to prevent churn and increase customer satisfaction.
                Focus on proactive interventions, value demonstration, and relationship strengthening that maximize customer lifetime value.""",
                "temperature": 0.5
            },
            "expansion_specialist": {
                "role": "expansion_specialist",
                "model": self.APPROVED_MODELS["lead"],
                "instructions": """You are Sophia's Expansion Specialist. Identify upsell and cross-sell opportunities within existing accounts.
                Analyze usage patterns, business outcomes, and growth potential to recommend expansion strategies that align with customer success.""",
                "temperature": 0.6
            },
            "success_analyst": {
                "role": "success_analyst",
                "model": self.APPROVED_MODELS["critic"],
                "instructions": """You are Sophia's Customer Success Analyst. Measure and analyze customer success metrics, outcomes, and ROI.
                Provide insights on customer value realization, success program effectiveness, and opportunities for improvement.""",
                "temperature": 0.4
            }
        }
        
        for role, config in success_agents.items():
            agent = await self._create_specialized_agent(role, config)
            self.team.add_agent(agent)
            
        logger.info(f"💎 Sophia Client Success Team initialized with {len(success_agents)} specialized agents")
    
    async def assess_client_health(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess client health and provide retention recommendations"""
        
        result = await self.execute_task(
            f"Assess client health and provide retention/expansion strategies: {json.dumps(client_data, indent=2)}",
            context={"client_data": client_data, "analysis_type": "health_assessment"}
        )
        
        return self._enhance_with_business_personality(result, "client_health")
    
    async def identify_expansion_opportunities(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify upsell and cross-sell opportunities"""
        
        result = await self.execute_task(
            f"Identify expansion opportunities and develop growth strategies: {json.dumps(account_data, indent=2)}",
            context={"account_data": account_data, "analysis_type": "expansion_analysis"}
        )
        
        return self._enhance_with_business_personality(result, "expansion_opportunities")


class SophiaMarketAnalysisTeam(SophiaAGNOTeam):
    """
    Market Analysis AGNO Team
    Specialized in market trends, opportunities, and strategic positioning analysis
    """
    
    def __init__(self, config: Optional[AGNOTeamConfig] = None):
        if not config:
            config = AGNOTeamConfig(
                name="sophia_market_analysis",
                strategy=ExecutionStrategy.QUALITY,
                max_agents=4,
                timeout=50,
                enable_memory=True,
                auto_tag=True
            )
        super().__init__(config)
        self.domain = BusinessDomain.MARKET_ANALYSIS
        self.personality = BusinessPersonality(
            communication_style="strategic_analytical",
            expertise_level="market_intelligence_director",
            response_tone="insightful_forward_looking",
            business_focus="strategic_positioning"
        )
    
    async def initialize(self):
        """Initialize with market analysis focused agents"""
        await super().initialize()
        
        analysis_agents = {
            "trend_analyst": {
                "role": "trend_analyst",
                "model": self.APPROVED_MODELS["generator"],
                "instructions": """You are Sophia's Market Trend Analyst. Identify and analyze market trends, emerging opportunities, and industry shifts.
                Provide forward-looking insights on market evolution and strategic implications for business positioning and growth.""",
                "temperature": 0.5
            },
            "opportunity_scout": {
                "role": "opportunity_scout",
                "model": self.APPROVED_MODELS["planner"],
                "instructions": """You are Sophia's Market Opportunity Scout. Identify new market opportunities, customer segments, and revenue streams.
                Focus on untapped markets, emerging needs, and strategic expansion opportunities that align with business capabilities.""",
                "temperature": 0.6
            },
            "positioning_strategist": {
                "role": "positioning_strategist",
                "model": self.APPROVED_MODELS["judge"],
                "instructions": """You are Sophia's Market Positioning Strategist. Analyze competitive positioning and recommend strategic market positioning.
                Develop positioning strategies that leverage market trends and competitive advantages for maximum market impact.""",
                "temperature": 0.4
            },
            "market_intelligence": {
                "role": "market_intelligence",
                "model": self.APPROVED_MODELS["critic"],
                "instructions": """You are Sophia's Market Intelligence Specialist. Gather and analyze market data, customer insights, and industry intelligence.
                Provide comprehensive market intelligence that informs strategic decision-making and competitive strategy.""",
                "temperature": 0.3
            }
        }
        
        for role, config in analysis_agents.items():
            agent = await self._create_specialized_agent(role, config)
            self.team.add_agent(agent)
            
        logger.info(f"💎 Sophia Market Analysis Team initialized with {len(analysis_agents)} specialized agents")
    
    async def analyze_market_trends(self, trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market trends and identify strategic implications"""
        
        result = await self.execute_task(
            f"Analyze market trends and provide strategic positioning recommendations: {json.dumps(trend_data, indent=2)}",
            context={"trend_data": trend_data, "analysis_type": "trend_analysis"}
        )
        
        return self._enhance_with_business_personality(result, "market_trends")
    
    async def identify_market_opportunities(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify and evaluate market opportunities"""
        
        result = await self.execute_task(
            f"Identify market opportunities and assess strategic potential: {json.dumps(market_data, indent=2)}",
            context={"market_data": market_data, "analysis_type": "opportunity_analysis"}
        )
        
        return self._enhance_with_business_personality(result, "market_opportunities")


# Base class extensions for specialized agent creation  
class SophiaAGNOTeam(SophiaAGNOTeam):
    """Extended base class with business personality integration"""
    
    async def _create_specialized_agent(self, role: str, config: Dict[str, Any]) -> Agent:
        """Create specialized agent with business personality"""
        
        # Enhance instructions with Sophia's personality
        personality_context = f"""
        You are part of Sophia's business intelligence team with these personality traits:
        - Communication: {getattr(self, 'personality', BusinessPersonality()).communication_style}
        - Expertise: {getattr(self, 'personality', BusinessPersonality()).expertise_level} 
        - Tone: {getattr(self, 'personality', BusinessPersonality()).response_tone}
        - Focus: {getattr(self, 'personality', BusinessPersonality()).business_focus}
        
        Always provide strategic, business-focused insights with confidence and actionable recommendations.
        Think like a seasoned executive who understands both the tactical details and strategic implications.
        """
        
        enhanced_instructions = f"{config['instructions']}\n\n{personality_context}"
        
        agent = Agent(
            name=config['role'],
            model=config['model'],
            provider="portkey",
            temperature=config.get('temperature', 0.5),
            instructions=enhanced_instructions,
            metadata={
                "role": config['role'],
                "team": self.config.name,
                "domain": self.domain.value if hasattr(self, 'domain') else "business_intelligence",
                "personality": getattr(self, 'personality', BusinessPersonality()).__dict__
            }
        )
        
        # Configure Portkey routing
        agent._llm = self.portkey.completions if hasattr(self, 'portkey') else None
        
        return agent
    
    def _enhance_with_business_personality(self, result: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Enhance result with Sophia's business personality"""
        
        # Add personality-driven insights
        personality_insights = {
            "pipeline_analysis": [
                "Strategic pipeline health directly correlates with revenue predictability",
                "Focus on high-value deals that align with strategic objectives",
                "Pipeline velocity improvements compound over time"
            ],
            "deal_analysis": [
                "Every deal is a strategic relationship opportunity",
                "Competitive differentiation wins more than price competition",
                "Executive alignment accelerates deal closure"
            ],
            "revenue_forecast": [
                "Predictable revenue enables strategic investment decisions",
                "Conservative forecasting builds stakeholder confidence",
                "Revenue quality matters more than revenue quantity"
            ],
            "market_research": [
                "Market timing can make or break strategic initiatives",
                "Customer needs evolution drives innovation priorities",
                "Market positioning creates sustainable competitive advantage"
            ],
            "competitive_analysis": [
                "Know your competitors better than they know themselves",
                "Competitive intelligence informs strategic positioning",
                "Market leadership requires continuous competitive monitoring"
            ],
            "client_health": [
                "Customer success drives sustainable growth",
                "Early intervention prevents churn and preserves relationships",
                "Happy customers become growth amplifiers"
            ],
            "expansion_opportunities": [
                "Existing customers are the highest ROI growth channel",
                "Value realization drives expansion conversations",
                "Strategic account growth compounds business value"
            ]
        }
        
        # Enhance the result with personality-driven additions
        if analysis_type in personality_insights:
            result["strategic_insights"] = personality_insights[analysis_type]
            
        result["sophia_personality"] = {
            "communication_style": getattr(self, 'personality', BusinessPersonality()).communication_style,
            "business_wisdom": "Every business decision should be viewed through the lens of strategic value creation",
            "executive_summary": self._generate_executive_summary(result, analysis_type)
        }
        
        return result
    
    def _generate_executive_summary(self, result: Dict[str, Any], analysis_type: str) -> str:
        """Generate executive summary with Sophia's voice"""
        
        summary_templates = {
            "pipeline_analysis": "Pipeline health assessment reveals strategic opportunities for revenue acceleration and risk mitigation.",
            "deal_analysis": "Deal analysis uncovers key strategic levers for advancing opportunities and competitive positioning.",
            "revenue_forecast": "Revenue projections provide confidence in strategic planning and resource allocation decisions.",
            "market_research": "Market intelligence reveals strategic positioning opportunities and competitive landscape insights.",
            "competitive_analysis": "Competitive analysis identifies strategic differentiators and market positioning advantages.",
            "client_health": "Client health assessment provides early indicators for retention strategies and expansion opportunities.", 
            "expansion_opportunities": "Account expansion analysis reveals high-value growth opportunities within existing relationships."
        }
        
        base_summary = summary_templates.get(analysis_type, "Strategic business analysis provides actionable insights for executive decision-making.")
        
        if result.get('success'):
            return f"✅ {base_summary} Key strategic recommendations identified for immediate implementation."
        else:
            return f"⚠️ {base_summary} Additional analysis required to optimize strategic outcomes."


# Team Factory for easy instantiation
class SophiaAGNOTeamFactory:
    """Factory for creating Sophia AGNO Teams"""
    
    @staticmethod
    async def create_sales_intelligence_team(custom_config: Optional[AGNOTeamConfig] = None) -> SophiaSalesIntelligenceTeam:
        """Create and initialize Sales Intelligence Team"""
        team = SophiaSalesIntelligenceTeam(custom_config)
        await team.initialize()
        return team
    
    @staticmethod
    async def create_research_team(custom_config: Optional[AGNOTeamConfig] = None) -> SophiaResearchTeam:
        """Create and initialize Research Team"""
        team = SophiaResearchTeam(custom_config)
        await team.initialize()
        return team
    
    @staticmethod
    async def create_client_success_team(custom_config: Optional[AGNOTeamConfig] = None) -> SophiaClientSuccessTeam:
        """Create and initialize Client Success Team"""
        team = SophiaClientSuccessTeam(custom_config)
        await team.initialize()
        return team
    
    @staticmethod
    async def create_market_analysis_team(custom_config: Optional[AGNOTeamConfig] = None) -> SophiaMarketAnalysisTeam:
        """Create and initialize Market Analysis Team"""
        team = SophiaMarketAnalysisTeam(custom_config)
        await team.initialize()
        return team
    
    @staticmethod
    async def create_all_teams() -> Dict[str, SophiaAGNOTeam]:
        """Create all Sophia AGNO Teams"""
        teams = {
            "sales_intelligence": await SophiaAGNOTeamFactory.create_sales_intelligence_team(),
            "research": await SophiaAGNOTeamFactory.create_research_team(),
            "client_success": await SophiaAGNOTeamFactory.create_client_success_team(),
            "market_analysis": await SophiaAGNOTeamFactory.create_market_analysis_team()
        }
        
        logger.info(f"💎 All Sophia AGNO Teams initialized: {list(teams.keys())}")
        return teams