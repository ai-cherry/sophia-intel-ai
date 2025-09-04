"""
Sophia AGNO Universal Orchestrator
Enhanced business orchestrator using AGNO Teams for specialized intelligence operations
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json

# Import enhanced components for smarter orchestration
from app.orchestrators.enhanced_command_recognition import (
    EnhancedCommandRecognizer,
    CommandIntent,
    ParsedCommand
)
from app.orchestrators.dynamic_tool_integration import (
    tool_registry,
    handle_api_test_command,
    ToolStatus
)
from app.orchestrators.enhanced_orchestrator_mixin import (
    EnhancedOrchestratorMixin,
    ProactiveAssistant
)

# Import AGNO Teams
from app.swarms.sophia_agno_teams import (
    SophiaAGNOTeamFactory,
    SophiaSalesIntelligenceTeam,
    SophiaResearchTeam,
    SophiaClientSuccessTeam,
    SophiaMarketAnalysisTeam,
    BusinessDomain
)

# Import base orchestrator components
from app.orchestrators.sophia_universal_orchestrator import (
    BusinessContext,
    BusinessResponse,
    BusinessCommandType,
    SophiaPersonality
)

logger = logging.getLogger(__name__)


class AGNOBusinessCommandType(Enum):
    """Enhanced business commands using AGNO Teams"""
    # Core business operations
    SALES_INTELLIGENCE = "sales_intelligence"
    PIPELINE_ANALYSIS = "pipeline_analysis" 
    DEAL_STRATEGY = "deal_strategy"
    REVENUE_FORECAST = "revenue_forecast"
    
    # Research operations
    MARKET_RESEARCH = "market_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    INDUSTRY_ANALYSIS = "industry_analysis"
    
    # Client success operations
    CLIENT_HEALTH = "client_health"
    RETENTION_STRATEGY = "retention_strategy"
    EXPANSION_OPPORTUNITIES = "expansion_opportunities"
    
    # Market analysis operations
    TREND_ANALYSIS = "trend_analysis"
    OPPORTUNITY_IDENTIFICATION = "opportunity_identification"
    MARKET_POSITIONING = "market_positioning"
    
    # Multi-team operations
    STRATEGIC_ANALYSIS = "strategic_analysis"
    BUSINESS_INTELLIGENCE = "business_intelligence"
    COMPREHENSIVE_ASSESSMENT = "comprehensive_assessment"


@dataclass
class AGNOBusinessResponse(BusinessResponse):
    """Enhanced business response with AGNO team insights"""
    agno_teams_used: List[str] = field(default_factory=list)
    team_specific_insights: Dict[str, Any] = field(default_factory=dict)
    cross_team_synthesis: Optional[str] = None
    strategic_implications: List[str] = field(default_factory=list)


class SophiaAGNOOrchestrator(EnhancedOrchestratorMixin):
    """
    Sophia AGNO Universal Business Orchestrator
    
    Enhanced orchestrator that uses specialized AGNO Teams for business intelligence:
    - Sales Intelligence Team: Pipeline, deals, revenue operations
    - Research Team: Market research, competitive intelligence
    - Client Success Team: Customer health, retention, expansion
    - Market Analysis Team: Trends, opportunities, positioning
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        
        # AGNO Teams (initialized later)
        self.sales_intelligence_team: Optional[SophiaSalesIntelligenceTeam] = None
        self.research_team: Optional[SophiaResearchTeam] = None
        self.client_success_team: Optional[SophiaClientSuccessTeam] = None
        self.market_analysis_team: Optional[SophiaMarketAnalysisTeam] = None
        
        # Team registry
        self.agno_teams: Dict[str, Any] = {}
        
        # Session management
        self.active_sessions = {}
        self.business_context_cache = {}
        self.personality = SophiaPersonality()
        
        # Enhanced intelligence components
        self.command_recognizer = EnhancedCommandRecognizer()
        self.tool_registry = tool_registry  # Use global registry
        self.initialized_tools = set()
        
        # Business domains under AGNO control
        self.controlled_domains = [
            "sales_intelligence",
            "pipeline_management", 
            "client_success",
            "market_research",
            "competitive_intelligence",
            "strategic_analysis",
            "revenue_operations",
            "business_analytics"
        ]
        
        logger.info("💎 Sophia AGNO Orchestrator initialized - preparing AGNO Teams")
    
    async def initialize(self) -> bool:
        """Initialize all AGNO Teams and orchestration capabilities"""
        try:
            logger.info("🚀 Initializing Sophia AGNO Teams...")
            
            # Initialize all AGNO teams concurrently
            team_initialization_tasks = [
                self._initialize_sales_intelligence_team(),
                self._initialize_research_team(),
                self._initialize_client_success_team(),
                self._initialize_market_analysis_team()
            ]
            
            await asyncio.gather(*team_initialization_tasks)
            
            # Initialize enhanced components for smarter orchestration
            logger.info("🎆 Initializing dynamic tool integration for API testing...")
            
            # Initialize critical business tools
            business_tools = ["gong", "hubspot", "salesforce"]
            tool_init_results = await self.tool_registry.initialize(business_tools)
            
            for tool, success in tool_init_results.items():
                if success:
                    self.initialized_tools.add(tool)
                    logger.info(f"  ✅ {tool.title()} connector ready")
                else:
                    logger.info(f"  ⚠️ {tool.title()} connector unavailable (check credentials)")
            
            # Register teams
            self.agno_teams = {
                "sales_intelligence": self.sales_intelligence_team,
                "research": self.research_team,
                "client_success": self.client_success_team,
                "market_analysis": self.market_analysis_team
            }
            
            
            # Initialize memory system for contextual intelligence
            try:
                project_path = "/Users/lynnmusil/sophia-intel-ai"  # Could be configurable
                await self.initialize_memory("sophia-global", project_path)
                logger.info("🧠 Memory system initialized for contextual intelligence")
            except Exception as e:
                logger.warning(f"Memory system initialization failed: {e}")
                
            logger.info(f"✅ Sophia AGNO Orchestrator fully operational with {len(self.agno_teams)} specialized teams")
            return True
            
        except Exception as e:
            logger.error(f"Sophia AGNO initialization failed: {str(e)}")
            return False
    
    async def _initialize_sales_intelligence_team(self):
        """Initialize Sales Intelligence AGNO Team"""
        try:
            self.sales_intelligence_team = await SophiaAGNOTeamFactory.create_sales_intelligence_team()
            logger.info("💎 Sales Intelligence Team ready")
        except Exception as e:
            logger.warning(f"Sales Intelligence Team initialization failed: {e}")
    
    async def _initialize_research_team(self):
        """Initialize Research AGNO Team"""
        try:
            self.research_team = await SophiaAGNOTeamFactory.create_research_team()
            logger.info("💎 Research Team ready")
        except Exception as e:
            logger.warning(f"Research Team initialization failed: {e}")
    
    async def _initialize_client_success_team(self):
        """Initialize Client Success AGNO Team"""
        try:
            self.client_success_team = await SophiaAGNOTeamFactory.create_client_success_team()
            logger.info("💎 Client Success Team ready")
        except Exception as e:
            logger.warning(f"Client Success Team initialization failed: {e}")
    
    async def _initialize_market_analysis_team(self):
        """Initialize Market Analysis AGNO Team"""
        try:
            self.market_analysis_team = await SophiaAGNOTeamFactory.create_market_analysis_team()
            logger.info("💎 Market Analysis Team ready")
        except Exception as e:
            logger.warning(f"Market Analysis Team initialization failed: {e}")
    
    async def process_business_request(
        self, 
        request: str, 
        context: Optional[BusinessContext] = None
    ) -> AGNOBusinessResponse:
        """
        Process business request using specialized AGNO Teams
        
        Main entry point that routes requests to appropriate AGNO Teams
        and synthesizes cross-team insights
        """
        start_time = asyncio.get_event_loop().time()
        context = context or BusinessContext()
        
        try:
            logger.info(f"💎 Sophia AGNO processing business request: {request[:100]}...")
            
            # Initialize session-specific memory if needed
            session_id = context.session_id if context else f"sophia-{int(start_time)}"
            if not self._memory_initialized:
                try:
                    await self.initialize_memory(session_id, "/Users/lynnmusil/sophia-intel-ai")
                    logger.info(f"🧠 Session memory initialized: {session_id}")
                except Exception as e:
                    logger.warning(f"Session memory initialization failed: {e}")
            
            # Add interaction to memory
            memory_context = None
            if self._memory_initialized:
                try:
                    memory_context = await self.process_with_memory(request, "user", {"context": context.__dict__ if context else {}})
                    logger.debug(f"💭 Memory context: {len(memory_context.get('working_memory', {}).get('messages', []))} messages")
                except Exception as e:
                    logger.warning(f"Memory processing failed: {e}")
            
            # First use enhanced command recognition (now with memory context)
            context_dict = context.__dict__ if context else {}
            if memory_context:
                context_dict.update(memory_context)
            parsed_command = await self.command_recognizer.classify_intent(request, context_dict)
            
            # Handle API testing commands with the dynamic tool integration
            if parsed_command.intent in [CommandIntent.API_TEST, CommandIntent.API_CONNECT, CommandIntent.API_STATUS]:
                return await self._handle_api_command(parsed_command, context)
            
            # Classify request for AGNO routing
            command_type = await self._classify_agno_business_request(request)
            
            # Route to appropriate AGNO Teams
            team_results = await self._execute_agno_business_command(request, command_type, context)
            
            # Synthesize cross-team insights
            synthesized_response = await self._synthesize_team_results(
                team_results, command_type, request, context
            )
            
            # Add personality flair
            synthesized_response.content = self.personality.add_personality_flair(
                synthesized_response.content
            )
            
            synthesized_response.execution_time = asyncio.get_event_loop().time() - start_time
            
            logger.info(f"✅ Sophia AGNO completed request in {synthesized_response.execution_time:.2f}s using {len(synthesized_response.agno_teams_used)} teams")
            return synthesized_response
            
        except Exception as e:
            logger.error(f"AGNO business request processing failed: {str(e)}")
            return AGNOBusinessResponse(
                success=False,
                content=f"I encountered a strategic challenge while coordinating my intelligence teams: {str(e)}. Let me recalibrate our approach.",
                command_type="error",
                metadata={"error": str(e)},
                execution_time=asyncio.get_event_loop().time() - start_time
            )
    
    async def _classify_agno_business_request(self, request: str) -> AGNOBusinessCommandType:
        """Classify business request for AGNO Team routing using enhanced recognition"""
        # First use the enhanced command recognizer for better accuracy
        parsed_command = await self.command_recognizer.classify_intent(request)
        
        # Handle API testing commands specifically
        if parsed_command.intent in [
            CommandIntent.API_TEST,
            CommandIntent.API_CONNECT,
            CommandIntent.API_STATUS
        ]:
            # This is an API testing command, not a business intelligence query
            return AGNOBusinessCommandType.BUSINESS_INTELLIGENCE  # Will be handled specially
        
        request_lower = request.lower()
        
        # Sales intelligence patterns
        if any(keyword in request_lower for keyword in [
            "pipeline", "deals", "sales", "revenue", "quota", "forecast", "conversion", "close"
        ]):
            if "pipeline" in request_lower:
                return AGNOBusinessCommandType.PIPELINE_ANALYSIS
            elif "deal" in request_lower and ("strategy" in request_lower or "coach" in request_lower):
                return AGNOBusinessCommandType.DEAL_STRATEGY
            elif "forecast" in request_lower or "revenue" in request_lower:
                return AGNOBusinessCommandType.REVENUE_FORECAST
            else:
                return AGNOBusinessCommandType.SALES_INTELLIGENCE
        
        # Research patterns
        elif any(keyword in request_lower for keyword in [
            "research", "market", "industry", "competitive", "competitor", "analyze"
        ]):
            if "competitive" in request_lower or "competitor" in request_lower:
                return AGNOBusinessCommandType.COMPETITIVE_ANALYSIS
            elif "industry" in request_lower:
                return AGNOBusinessCommandType.INDUSTRY_ANALYSIS
            else:
                return AGNOBusinessCommandType.MARKET_RESEARCH
        
        # Client success patterns
        elif any(keyword in request_lower for keyword in [
            "client", "customer", "account", "churn", "retention", "health", "expansion", "upsell"
        ]):
            if "expansion" in request_lower or "upsell" in request_lower or "cross-sell" in request_lower:
                return AGNOBusinessCommandType.EXPANSION_OPPORTUNITIES
            elif "retention" in request_lower or "churn" in request_lower:
                return AGNOBusinessCommandType.RETENTION_STRATEGY
            else:
                return AGNOBusinessCommandType.CLIENT_HEALTH
        
        # Market analysis patterns
        elif any(keyword in request_lower for keyword in [
            "trend", "opportunity", "positioning", "market analysis", "strategic"
        ]):
            if "trend" in request_lower:
                return AGNOBusinessCommandType.TREND_ANALYSIS
            elif "opportunity" in request_lower:
                return AGNOBusinessCommandType.OPPORTUNITY_IDENTIFICATION
            elif "positioning" in request_lower:
                return AGNOBusinessCommandType.MARKET_POSITIONING
            else:
                return AGNOBusinessCommandType.STRATEGIC_ANALYSIS
        
        # Multi-team strategic operations
        elif any(keyword in request_lower for keyword in [
            "comprehensive", "complete analysis", "full assessment", "strategic overview"
        ]):
            return AGNOBusinessCommandType.COMPREHENSIVE_ASSESSMENT
        
        # Default to business intelligence
        else:
            return AGNOBusinessCommandType.BUSINESS_INTELLIGENCE
    
    async def _execute_agno_business_command(
        self, 
        request: str, 
        command_type: AGNOBusinessCommandType, 
        context: BusinessContext
    ) -> Dict[str, Any]:
        """Execute business command using appropriate AGNO Teams"""
        
        team_results = {}
        
        try:
            # Route to specific teams based on command type
            if command_type in [
                AGNOBusinessCommandType.SALES_INTELLIGENCE,
                AGNOBusinessCommandType.PIPELINE_ANALYSIS,
                AGNOBusinessCommandType.DEAL_STRATEGY,
                AGNOBusinessCommandType.REVENUE_FORECAST
            ]:
                if self.sales_intelligence_team:
                    result = await self._execute_sales_intelligence(request, command_type, context)
                    team_results["sales_intelligence"] = result
            
            elif command_type in [
                AGNOBusinessCommandType.MARKET_RESEARCH,
                AGNOBusinessCommandType.COMPETITIVE_ANALYSIS,
                AGNOBusinessCommandType.INDUSTRY_ANALYSIS
            ]:
                if self.research_team:
                    result = await self._execute_research(request, command_type, context)
                    team_results["research"] = result
            
            elif command_type in [
                AGNOBusinessCommandType.CLIENT_HEALTH,
                AGNOBusinessCommandType.RETENTION_STRATEGY,
                AGNOBusinessCommandType.EXPANSION_OPPORTUNITIES
            ]:
                if self.client_success_team:
                    result = await self._execute_client_success(request, command_type, context)
                    team_results["client_success"] = result
            
            elif command_type in [
                AGNOBusinessCommandType.TREND_ANALYSIS,
                AGNOBusinessCommandType.OPPORTUNITY_IDENTIFICATION,
                AGNOBusinessCommandType.MARKET_POSITIONING
            ]:
                if self.market_analysis_team:
                    result = await self._execute_market_analysis(request, command_type, context)
                    team_results["market_analysis"] = result
            
            # Multi-team operations
            elif command_type in [
                AGNOBusinessCommandType.STRATEGIC_ANALYSIS,
                AGNOBusinessCommandType.COMPREHENSIVE_ASSESSMENT
            ]:
                # Execute multiple teams in parallel
                tasks = []
                if self.sales_intelligence_team:
                    tasks.append(self._execute_sales_intelligence(request, command_type, context))
                if self.research_team:
                    tasks.append(self._execute_research(request, command_type, context))
                if self.client_success_team:
                    tasks.append(self._execute_client_success(request, command_type, context))
                if self.market_analysis_team:
                    tasks.append(self._execute_market_analysis(request, command_type, context))
                
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    team_names = ["sales_intelligence", "research", "client_success", "market_analysis"][:len(results)]
                    for team_name, result in zip(team_names, results):
                        if not isinstance(result, Exception):
                            team_results[team_name] = result
            
            # Default business intelligence
            else:
                # Use sales intelligence team as primary for general business questions
                if self.sales_intelligence_team:
                    result = await self._execute_sales_intelligence(request, AGNOBusinessCommandType.BUSINESS_INTELLIGENCE, context)
                    team_results["sales_intelligence"] = result
        
        except Exception as e:
            logger.error(f"AGNO team execution failed: {str(e)}")
            team_results["error"] = {"message": str(e), "type": "execution_error"}
        
        return team_results
    
    async def _execute_sales_intelligence(
        self, 
        request: str, 
        command_type: AGNOBusinessCommandType, 
        context: BusinessContext
    ) -> Dict[str, Any]:
        """Execute sales intelligence operations"""
        
        # Extract relevant data from context
        pipeline_data = context.company_context.get("pipeline_data", {}) if context.company_context else {}
        deal_data = context.company_context.get("deal_data", {}) if context.company_context else {}
        
        try:
            if command_type == AGNOBusinessCommandType.PIPELINE_ANALYSIS:
                return await self.sales_intelligence_team.analyze_pipeline_health(
                    pipeline_data or {"request": request}
                )
            elif command_type == AGNOBusinessCommandType.DEAL_STRATEGY:
                return await self.sales_intelligence_team.analyze_deal_strategy(
                    deal_data or {"request": request}
                )
            elif command_type == AGNOBusinessCommandType.REVENUE_FORECAST:
                return await self.sales_intelligence_team.forecast_revenue(
                    pipeline_data or {"request": request}, 
                    "quarterly"
                )
            else:
                # General sales intelligence
                return await self.sales_intelligence_team.execute_task(
                    request,
                    context={"request_type": "general_sales_intelligence", "user_context": context.__dict__}
                )
        except Exception as e:
            logger.error(f"Sales intelligence execution failed: {e}")
            return {"success": False, "error": str(e), "team": "sales_intelligence"}
    
    async def _execute_research(
        self, 
        request: str, 
        command_type: AGNOBusinessCommandType, 
        context: BusinessContext
    ) -> Dict[str, Any]:
        """Execute research operations"""
        
        try:
            if command_type == AGNOBusinessCommandType.COMPETITIVE_ANALYSIS:
                competitor_data = context.company_context.get("competitor_data", {"request": request}) if context.company_context else {"request": request}
                return await self.research_team.analyze_competitive_landscape(competitor_data)
            else:
                # General market research
                research_scope = context.company_context.get("research_scope", {"request": request}) if context.company_context else {"request": request}
                return await self.research_team.conduct_market_research(research_scope)
        except Exception as e:
            logger.error(f"Research execution failed: {e}")
            return {"success": False, "error": str(e), "team": "research"}
    
    async def _execute_client_success(
        self, 
        request: str, 
        command_type: AGNOBusinessCommandType, 
        context: BusinessContext
    ) -> Dict[str, Any]:
        """Execute client success operations"""
        
        try:
            if command_type == AGNOBusinessCommandType.EXPANSION_OPPORTUNITIES:
                account_data = context.company_context.get("account_data", {"request": request}) if context.company_context else {"request": request}
                return await self.client_success_team.identify_expansion_opportunities(account_data)
            else:
                # General client health assessment
                client_data = context.company_context.get("client_data", {"request": request}) if context.company_context else {"request": request}
                return await self.client_success_team.assess_client_health(client_data)
        except Exception as e:
            logger.error(f"Client success execution failed: {e}")
            return {"success": False, "error": str(e), "team": "client_success"}
    
    async def _execute_market_analysis(
        self, 
        request: str, 
        command_type: AGNOBusinessCommandType, 
        context: BusinessContext
    ) -> Dict[str, Any]:
        """Execute market analysis operations"""
        
        try:
            if command_type == AGNOBusinessCommandType.TREND_ANALYSIS:
                trend_data = context.company_context.get("trend_data", {"request": request}) if context.company_context else {"request": request}
                return await self.market_analysis_team.analyze_market_trends(trend_data)
            elif command_type == AGNOBusinessCommandType.OPPORTUNITY_IDENTIFICATION:
                market_data = context.company_context.get("market_data", {"request": request}) if context.company_context else {"request": request}
                return await self.market_analysis_team.identify_market_opportunities(market_data)
            else:
                # General market analysis
                return await self.market_analysis_team.execute_task(
                    request,
                    context={"request_type": "general_market_analysis", "user_context": context.__dict__}
                )
        except Exception as e:
            logger.error(f"Market analysis execution failed: {e}")
            return {"success": False, "error": str(e), "team": "market_analysis"}
    
    async def _synthesize_team_results(
        self, 
        team_results: Dict[str, Any],
        command_type: AGNOBusinessCommandType,
        original_request: str,
        context: BusinessContext
    ) -> AGNOBusinessResponse:
        """Synthesize results from multiple AGNO teams into comprehensive response"""
        
        if not team_results:
            return AGNOBusinessResponse(
                success=False,
                content="No AGNO teams were able to process this request. The intelligence coordination system needs attention.",
                command_type=command_type.value
            )
        
        # Extract successful results
        successful_teams = []
        team_insights = {}
        all_insights = []
        all_recommendations = []
        all_next_actions = []
        
        for team_name, result in team_results.items():
            if result.get("success", False):
                successful_teams.append(team_name)
                team_insights[team_name] = result
                
                # Aggregate insights
                if "strategic_insights" in result:
                    all_insights.extend(result["strategic_insights"])
                if "recommendations" in result:
                    all_recommendations.extend(result["recommendations"])
                if "next_actions" in result:
                    all_next_actions.extend(result["next_actions"])
        
        # Generate synthesized content
        content = self._generate_synthesized_content(
            team_results, successful_teams, original_request, command_type
        )
        
        # Generate cross-team synthesis
        cross_team_synthesis = self._generate_cross_team_synthesis(
            successful_teams, team_insights, command_type
        )
        
        # Generate strategic implications
        strategic_implications = self._generate_strategic_implications(
            team_insights, command_type
        )
        
        return AGNOBusinessResponse(
            success=len(successful_teams) > 0,
            content=content,
            command_type=command_type.value,
            insights=list(set(all_insights))[:5],  # Top 5 unique insights
            recommendations=list(set(all_recommendations))[:5],  # Top 5 unique recommendations
            next_actions=list(set(all_next_actions))[:5],  # Top 5 unique actions
            agno_teams_used=successful_teams,
            team_specific_insights=team_insights,
            cross_team_synthesis=cross_team_synthesis,
            strategic_implications=strategic_implications,
            metadata={
                "teams_attempted": len(team_results),
                "teams_successful": len(successful_teams),
                "coordination_type": "agno_multi_team" if len(successful_teams) > 1 else "agno_single_team"
            }
        )
    
    def _generate_synthesized_content(
        self, 
        team_results: Dict[str, Any],
        successful_teams: List[str],
        original_request: str,
        command_type: AGNOBusinessCommandType
    ) -> str:
        """Generate synthesized content from team results"""
        
        if not successful_teams:
            # Check if this looks like an API/integration command that wasn't properly routed
            api_keywords = ['api', 'integration', 'connection', 'audit', 'test', 'check', 'github', 'gong', 'hubspot', 'salesforce']
            if any(keyword in original_request.lower() for keyword in api_keywords):
                return f"Let me help you with that integration request. It seems the API testing system needs to be invoked. Try being more specific: 'test github api connection' or 'check github integration status'."
            
            # Default fallback message
            return f"No AGNO teams were able to process this request. The intelligence coordination system needs attention. - This is the kind of insight that moves needles."
        
        # Build synthesized response
        content_parts = []
        
        # Header based on teams used
        if len(successful_teams) == 1:
            team_name = successful_teams[0].replace("_", " ").title()
            content_parts.append(f"📊 **{team_name} Intelligence Analysis:**\n")
        else:
            content_parts.append(f"🎯 **Multi-Team Strategic Intelligence** ({len(successful_teams)} teams coordinated):\n")
        
        # Add team-specific findings
        for team_name in successful_teams:
            team_result = team_results.get(team_name, {})
            if team_result.get("result", {}).get("content"):
                team_display_name = team_name.replace("_", " ").title()
                content_parts.append(f"**{team_display_name} Findings:**")
                content_parts.append(team_result["result"]["content"][:500] + "...\n" if len(team_result["result"]["content"]) > 500 else team_result["result"]["content"] + "\n")
        
        # Add strategic synthesis if multiple teams
        if len(successful_teams) > 1:
            content_parts.append("\n🔗 **Strategic Intelligence Synthesis:**")
            content_parts.append("Multiple intelligence streams have been analyzed and coordinated to provide comprehensive business insights. The convergent analysis reveals strategic opportunities and tactical recommendations for immediate implementation.")
        
        return "\n".join(content_parts)
    
    def _generate_cross_team_synthesis(
        self, 
        successful_teams: List[str],
        team_insights: Dict[str, Any],
        command_type: AGNOBusinessCommandType
    ) -> Optional[str]:
        """Generate cross-team synthesis insights"""
        
        if len(successful_teams) <= 1:
            return None
        
        synthesis_templates = {
            "sales_intelligence,research": "Sales intelligence combined with market research reveals strategic opportunities for revenue acceleration through market-informed positioning.",
            "sales_intelligence,client_success": "Sales and client success intelligence integration enables comprehensive customer lifecycle optimization from acquisition through expansion.",
            "research,market_analysis": "Research and market analysis convergence provides deep market understanding for strategic positioning and opportunity identification.",
            "client_success,market_analysis": "Client success insights combined with market analysis creates expansion strategies aligned with market opportunities.",
        }
        
        # Create team combination key
        teams_key = ",".join(sorted(successful_teams))
        
        # Try exact match first, then partial matches
        synthesis = synthesis_templates.get(teams_key)
        if not synthesis:
            for template_key, template_text in synthesis_templates.items():
                if all(team in successful_teams for team in template_key.split(",")):
                    synthesis = template_text
                    break
        
        if not synthesis:
            synthesis = f"Intelligence coordination across {len(successful_teams)} specialized teams provides comprehensive business insights with cross-functional strategic implications."
        
        return synthesis
    
    async def _handle_api_command(
        self,
        parsed_command: ParsedCommand,
        context: Optional[BusinessContext] = None
    ) -> AGNOBusinessResponse:
        """Handle API testing and integration commands using dynamic tool integration"""
        
        try:
            # Extract service name from parsed command
            service = parsed_command.parameters.get("service")
            
            if not service:
                # Try to extract from the original message
                for tool in ["gong", "hubspot", "salesforce", "github", "slack"]:
                    if tool in parsed_command.original_message.lower():
                        service = tool
                        break
            
            if not service:
                return AGNOBusinessResponse(
                    success=False,
                    content="I need to know which service you want to test. Try: 'test gong api connection' or 'test hubspot connection'",
                    command_type="api_test",
                    metadata={"available_services": ["gong", "hubspot", "salesforce", "github"]}
                )
            
            # Initialize the tool if needed
            if service not in self.initialized_tools:
                logger.info(f"Initializing {service} connector for the first time...")
                init_result = await self.tool_registry.initialize([service])
                
                if init_result.get(service):
                    self.initialized_tools.add(service)
                    logger.info(f"✅ {service} connector initialized successfully")
                else:
                    logger.warning(f"⚠️ Failed to initialize {service} connector")
            
            # Handle different API command intents
            if parsed_command.intent == CommandIntent.API_TEST:
                # Test the API connection
                result = await handle_api_test_command(service, context.__dict__ if context else None)
                
                # Format response with personality
                if result["success"]:
                    # Add contextual intelligence if memory is available
                    contextual_intro = ""
                    if self._memory_initialized:
                        try:
                            contextual_intro = await self.get_contextual_response(f"test {service} api")
                            if contextual_intro and contextual_intro != self._get_default_response(f"test {service} api"):
                                contextual_intro = f"🧠 {contextual_intro}\n\n"
                            else:
                                contextual_intro = ""
                        except Exception:
                            contextual_intro = ""
                    
                    response_text = (
                        f"{contextual_intro}"
                        f"🎆 Boom! Successfully connected to {service.title()} API! ✨\n\n"
                        f"💎 **Connection Status**: {result['status']}\n"
                        f"🎯 **Latency**: {result.get('latency_ms', 0):.1f}ms\n"
                        f"🚀 **Capabilities**: {', '.join(result.get('capabilities', [])[:5])}\n\n"
                    )
                    
                    if result.get('details'):
                        response_text += "**Connection Details:**\n"
                        for key, value in result['details'].items():
                            response_text += f"  • {key}: {value}\n"
                    
                    if result.get('suggestions'):
                        response_text += f"\n**Next Steps:**\n"
                        for suggestion in result['suggestions']:
                            response_text += f"  👉 {suggestion}\n"
                    
                    response_text = self.personality.add_personality_flair(response_text)
                    
                else:
                    response_text = (
                        f"😕 Couldn't connect to {service.title()} API.\n\n"
                        f"**Error**: {result.get('message', 'Connection failed')}\n\n"
                    )
                    
                    if result.get('troubleshooting'):
                        response_text += "**Troubleshooting Steps:**\n"
                        for step in result['troubleshooting']:
                            response_text += f"  🔧 {step}\n"
                    
                    response_text += "\nLet me know if you need help with the configuration!"
                
                # Learn from API testing outcome
                if self._memory_initialized:
                    try:
                        await self.memory_system.learn_from_outcome(
                            action=f"api_test_{service}",
                            outcome=result,
                            success=result["success"]
                        )
                        # Track API testing frequency for suggestions
                        if self.memory_system.working.current_task != f"api_testing_{service}":
                            self.memory_system.working.set_task(f"api_testing_{service}")
                    except Exception as e:
                        logger.debug(f"Memory learning failed: {e}")
                
                return AGNOBusinessResponse(
                    success=result["success"],
                    content=response_text,
                    command_type="api_test",
                    data=result,
                    metadata={
                        "service": service,
                        "intent": parsed_command.intent.value,
                        "confidence": parsed_command.confidence
                    },
                    agno_teams_used=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            elif parsed_command.intent == CommandIntent.API_STATUS:
                # Check API status
                status = await self.tool_registry.get_tool_status(service)
                
                response_text = (
                    f"📊 **{service.title()} API Status**:\n\n"
                    f"Status: {status.get('status', 'unknown')}\n"
                    f"Priority: {status.get('priority', 'normal')}\n"
                )
                
                if status.get('capabilities'):
                    response_text += f"Available Operations: {', '.join(status['capabilities'][:5])}\n"
                
                return AGNOBusinessResponse(
                    success=True,
                    content=self.personality.add_personality_flair(response_text),
                    command_type="api_status",
                    data=status,
                    metadata={"service": service},
                    agno_teams_used=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            elif parsed_command.intent == CommandIntent.API_CONNECT:
                # Initialize and connect to API
                init_result = await self.tool_registry.initialize([service])
                success = init_result.get(service, False)
                
                if success:
                    self.initialized_tools.add(service)
                    response_text = f"✅ Successfully initialized and connected to {service.title()} API! Ready for operations."
                else:
                    response_text = f"❌ Failed to connect to {service.title()} API. Please check your credentials."
                
                return AGNOBusinessResponse(
                    success=success,
                    content=self.personality.add_personality_flair(response_text),
                    command_type="api_connect",
                    metadata={"service": service},
                    agno_teams_used=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            else:
                # Unknown API command
                return AGNOBusinessResponse(
                    success=False,
                    content=f"I'm not sure how to handle that API command. Try 'test {service} api' or 'check {service} status'",
                    command_type="api_unknown",
                    metadata={"service": service, "intent": parsed_command.intent.value},
                    agno_teams_used=[],
                    timestamp=datetime.utcnow().isoformat()
                )
                
        except Exception as e:
            logger.error(f"Error handling API command: {str(e)}")
            return AGNOBusinessResponse(
                success=False,
                content=f"Encountered an error while handling the API command: {str(e)}",
                command_type="api_error",
                metadata={"error": str(e)},
                agno_teams_used=[],
                timestamp=datetime.utcnow().isoformat()
            )
    
    def _generate_strategic_implications(
        self, 
        team_insights: Dict[str, Any],
        command_type: AGNOBusinessCommandType
    ) -> List[str]:
        """Generate strategic implications from team insights"""
        
        implications = []
        
        # Extract implications from team results
        for team_name, insights in team_insights.items():
            if "strategic_insights" in insights:
                implications.extend(insights["strategic_insights"])
            
            # Add team-specific strategic context
            team_implications = {
                "sales_intelligence": "Sales intelligence directly impacts revenue predictability and growth acceleration.",
                "research": "Market research insights inform strategic positioning and competitive advantage.",
                "client_success": "Client success intelligence drives sustainable growth and customer lifetime value.",
                "market_analysis": "Market analysis provides strategic context for business expansion and positioning."
            }
            
            if team_name in team_implications:
                implications.append(team_implications[team_name])
        
        # Remove duplicates and limit to top implications
        return list(set(implications))[:3]
    
    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get AGNO orchestrator status and team readiness"""
        
        team_status = {}
        for team_name, team in self.agno_teams.items():
            if team:
                team_status[team_name] = {
                    "status": "operational",
                    "agents": len(team.team.agents) if hasattr(team, 'team') and team.team else 0,
                    "domain": getattr(team, 'domain', {}).value if hasattr(team, 'domain') else "unknown"
                }
            else:
                team_status[team_name] = {"status": "not_initialized", "agents": 0}
        
        return {
            "orchestrator": "Sophia AGNO Universal Business Orchestrator",
            "status": "operational",
            "personality": "strategic_business_intelligence_with_agno_teams",
            "agno_teams": team_status,
            "controlled_domains": self.controlled_domains,
            "capabilities": [
                "multi_team_coordination",
                "specialized_business_intelligence",
                "cross_team_synthesis",
                "strategic_implications_analysis",
                "sales_intelligence_operations",
                "market_research_operations",
                "client_success_operations",
                "market_analysis_operations"
            ],
            "active_sessions": len(self.active_sessions),
            "business_context_cache": len(self.business_context_cache),
            "last_updated": datetime.now().isoformat()
        }
    
    async def get_business_insights_summary(self) -> Dict[str, Any]:
        """Get consolidated business insights from all AGNO teams"""
        
        insights_summary = {
            "executive_summary": {
                "orchestration_model": "AGNO Multi-Team Coordination",
                "intelligence_coverage": "Comprehensive business intelligence across all domains",
                "team_coordination": f"{len([t for t in self.agno_teams.values() if t])} specialized teams operational",
                "strategic_capability": "Enhanced with cross-team synthesis and strategic implications"
            },
            "team_capabilities": {},
            "strategic_advantages": [
                "Specialized intelligence teams for domain expertise",
                "Cross-team synthesis for comprehensive insights", 
                "Strategic implications analysis for executive decision-making",
                "Scalable team coordination for complex business challenges"
            ],
            "coordination_benefits": [
                "Domain expertise through specialized AGNO teams",
                "Comprehensive coverage through multi-team operations",
                "Strategic synthesis through cross-team intelligence coordination",
                "Actionable insights through personality-driven business intelligence"
            ]
        }
        
        # Add team-specific capabilities
        for team_name, team in self.agno_teams.items():
            if team:
                insights_summary["team_capabilities"][team_name] = {
                    "domain": getattr(team, 'domain', {}).value if hasattr(team, 'domain') else "business_intelligence",
                    "specialization": team_name.replace("_", " ").title(),
                    "agent_count": len(team.team.agents) if hasattr(team, 'team') and team.team else 0,
                    "status": "operational"
                }
        
        return insights_summary