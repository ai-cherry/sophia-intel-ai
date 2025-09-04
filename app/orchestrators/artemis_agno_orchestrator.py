"""
Artemis AGNO Universal Orchestrator
Enhanced technical orchestrator using AGNO Teams for specialized technical operations
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
from app.swarms.artemis_agno_teams import (
    ArtemisAGNOTeamFactory,
    ArtemisCodeAnalysisTeam,
    ArtemisSecurityTeam,
    ArtemisArchitectureTeam,
    ArtemisPerformanceTeam,
    TechnicalDomain
)

# Import base orchestrator components
from app.orchestrators.artemis_universal_orchestrator import (
    TechnicalContext,
    TechnicalResponse,
    TechnicalCommandType,
    ArtemisPersonality
)

logger = logging.getLogger(__name__)


class AGNOTechnicalCommandType(Enum):
    """Enhanced technical commands using AGNO Teams"""
    # Code analysis operations
    CODE_ANALYSIS = "code_analysis"
    CODE_REVIEW = "code_review"
    CODEBASE_ASSESSMENT = "codebase_assessment"
    REFACTORING_ANALYSIS = "refactoring_analysis"
    
    # Security operations
    SECURITY_AUDIT = "security_audit"
    VULNERABILITY_ASSESSMENT = "vulnerability_assessment"
    PENETRATION_TESTING = "penetration_testing"
    COMPLIANCE_REVIEW = "compliance_review"
    
    # Architecture operations
    ARCHITECTURE_REVIEW = "architecture_review"
    SYSTEM_DESIGN = "system_design"
    SCALABILITY_ANALYSIS = "scalability_analysis"
    INTEGRATION_ANALYSIS = "integration_analysis"
    
    # Performance operations
    PERFORMANCE_ANALYSIS = "performance_analysis"
    OPTIMIZATION_STRATEGY = "optimization_strategy"
    LOAD_TESTING = "load_testing"
    MONITORING_STRATEGY = "monitoring_strategy"
    
    # Multi-team operations
    COMPREHENSIVE_AUDIT = "comprehensive_audit"
    TECHNICAL_ASSESSMENT = "technical_assessment"
    SYSTEM_HEALTH_CHECK = "system_health_check"


@dataclass
class AGNOTechnicalResponse(TechnicalResponse):
    """Enhanced technical response with AGNO team insights"""
    agno_teams_used: List[str] = field(default_factory=list)
    team_specific_findings: Dict[str, Any] = field(default_factory=dict)
    cross_team_synthesis: Optional[str] = None
    tactical_implications: List[str] = field(default_factory=list)


class ArtemisAGNOOrchestrator(EnhancedOrchestratorMixin):
    """
    Artemis AGNO Universal Technical Orchestrator
    
    Enhanced orchestrator that uses specialized AGNO Teams for technical operations:
    - Code Analysis Team: Code review, quality assessment, refactoring
    - Security Team: Vulnerability assessment, penetration testing, compliance
    - Architecture Team: System design, scalability analysis, patterns
    - Performance Team: Optimization, monitoring, load testing
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        
        # AGNO Teams (initialized later)
        self.code_analysis_team: Optional[ArtemisCodeAnalysisTeam] = None
        self.security_team: Optional[ArtemisSecurityTeam] = None
        self.architecture_team: Optional[ArtemisArchitectureTeam] = None
        self.performance_team: Optional[ArtemisPerformanceTeam] = None
        
        # Team registry
        self.agno_teams: Dict[str, Any] = {}
        
        # Session management
        self.active_sessions = {}
        
        # Enhanced intelligence components
        self.command_recognizer = EnhancedCommandRecognizer()
        self.tool_registry = tool_registry  # Shared registry
        self.initialized_tools = set()
        self.system_context_cache = {}
        self.personality = ArtemisPersonality()
        
        # Technical domains under AGNO control
        self.controlled_domains = [
            "code_analysis",
            "security_auditing",
            "system_architecture",
            "performance_optimization", 
            "technical_debt_management",
            "infrastructure_management",
            "testing_strategies",
            "monitoring_systems"
        ]
        
        logger.info("⚔️ Artemis AGNO Orchestrator initialized - preparing technical AGNO Teams")
    
    async def initialize(self) -> bool:
        """Initialize all AGNO Teams and orchestration capabilities"""
        try:
            logger.info("🚀 Initializing Artemis AGNO Teams...")
            
            # Initialize all AGNO teams concurrently
            team_initialization_tasks = [
                self._initialize_code_analysis_team(),
                self._initialize_security_team(),
                self._initialize_architecture_team(),
                self._initialize_performance_team()
            ]
            
            await asyncio.gather(*team_initialization_tasks)
            
            # Register teams
            self.agno_teams = {
                "code_analysis": self.code_analysis_team,
                "security": self.security_team,
                "architecture": self.architecture_team,
                "performance": self.performance_team
            }
            
            
            # Initialize memory system for contextual intelligence
            try:
                project_path = "/Users/lynnmusil/sophia-intel-ai"  # Could be configurable
                await self.initialize_memory("artemis-global", project_path)
                logger.info("🧠 Memory system initialized for contextual intelligence")
            except Exception as e:
                logger.warning(f"Memory system initialization failed: {e}")
                
            logger.info(f"✅ Artemis AGNO Orchestrator fully operational with {len(self.agno_teams)} specialized teams")
            return True
            
        except Exception as e:
            logger.error(f"Artemis AGNO initialization failed: {str(e)}")
            return False
    
    async def _initialize_code_analysis_team(self):
        """Initialize Code Analysis AGNO Team"""
        try:
            self.code_analysis_team = await ArtemisAGNOTeamFactory.create_code_analysis_team()
            logger.info("⚔️ Code Analysis Team ready")
        except Exception as e:
            logger.warning(f"Code Analysis Team initialization failed: {e}")
    
    async def _initialize_security_team(self):
        """Initialize Security AGNO Team"""
        try:
            self.security_team = await ArtemisAGNOTeamFactory.create_security_team()
            logger.info("⚔️ Security Team ready")
        except Exception as e:
            logger.warning(f"Security Team initialization failed: {e}")
    
    async def _initialize_architecture_team(self):
        """Initialize Architecture AGNO Team"""
        try:
            self.architecture_team = await ArtemisAGNOTeamFactory.create_architecture_team()
            logger.info("⚔️ Architecture Team ready")
        except Exception as e:
            logger.warning(f"Architecture Team initialization failed: {e}")
    
    async def _initialize_performance_team(self):
        """Initialize Performance AGNO Team"""
        try:
            self.performance_team = await ArtemisAGNOTeamFactory.create_performance_team()
            logger.info("⚔️ Performance Team ready")
        except Exception as e:
            logger.warning(f"Performance Team initialization failed: {e}")
    
    async def process_technical_request(
        self, 
        request: str, 
        context: Optional[TechnicalContext] = None
    ) -> AGNOTechnicalResponse:
        """
        Process technical request using specialized AGNO Teams
        
        Main entry point that routes requests to appropriate AGNO Teams
        and synthesizes cross-team insights
        """
        start_time = asyncio.get_event_loop().time()
        context = context or TechnicalContext()
        
        try:
            logger.info(f"⚔️ Artemis AGNO processing technical request: {request[:100]}...")
            
            # Initialize session-specific memory if needed
            session_id = context.session_id if context else f"artemis-{int(start_time)}"
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
            
            # Classify request for AGNO routing (now with memory context)
            command_type = await self._classify_agno_technical_request(request)
            
            # Route to appropriate AGNO Teams
            team_results = await self._execute_agno_technical_command(request, command_type, context)
            
            # Synthesize cross-team insights
            synthesized_response = await self._synthesize_team_results(
                team_results, command_type, request, context
            )
            
            # Add contextual intelligence if memory is available
            if self._memory_initialized:
                try:
                    contextual_intro = await self.get_contextual_response(request)
                    if contextual_intro and contextual_intro != self._get_default_response(request):
                        synthesized_response.content = f"🧠 {contextual_intro}\n\n{synthesized_response.content}"
                        
                    # Learn from interaction outcome  
                    await self.memory_system.learn_from_outcome(
                        action=f"technical_{command_type.value}",
                        outcome={"success": synthesized_response.success, "teams_used": len(team_results)},
                        success=synthesized_response.success
                    )
                except Exception as e:
                    logger.debug(f"Memory enhancement failed: {e}")
            
            # Add tactical personality flair
            synthesized_response.content = self.personality.add_personality_flair(
                synthesized_response.content
            )
            
            synthesized_response.execution_time = asyncio.get_event_loop().time() - start_time
            
            logger.info(f"✅ Artemis AGNO completed request in {synthesized_response.execution_time:.2f}s using {len(synthesized_response.agno_teams_used)} teams")
            return synthesized_response
            
        except Exception as e:
            logger.error(f"AGNO technical request processing failed: {str(e)}")
            return AGNOTechnicalResponse(
                success=False,
                content=f"Well, shit. Hit a technical snag while coordinating my tactical teams: {str(e)}. Let me recalibrate and take another approach.",
                command_type="error",
                metadata={"error": str(e)},
                execution_time=asyncio.get_event_loop().time() - start_time
            )
    
    async def _classify_agno_technical_request(self, request: str) -> AGNOTechnicalCommandType:
        """Classify technical request for AGNO Team routing"""
        request_lower = request.lower()
        
        # Code analysis patterns
        if any(keyword in request_lower for keyword in [
            "code review", "analyze code", "quality", "refactor", "technical debt", "static analysis"
        ]):
            if "refactor" in request_lower:
                return AGNOTechnicalCommandType.REFACTORING_ANALYSIS
            elif "review" in request_lower:
                return AGNOTechnicalCommandType.CODE_REVIEW
            elif "codebase" in request_lower:
                return AGNOTechnicalCommandType.CODEBASE_ASSESSMENT
            else:
                return AGNOTechnicalCommandType.CODE_ANALYSIS
        
        # Security patterns
        elif any(keyword in request_lower for keyword in [
            "security", "vulnerability", "audit", "penetration", "compliance", "threat"
        ]):
            if "vulnerability" in request_lower:
                return AGNOTechnicalCommandType.VULNERABILITY_ASSESSMENT
            elif "penetration" in request_lower or "pentest" in request_lower:
                return AGNOTechnicalCommandType.PENETRATION_TESTING
            elif "compliance" in request_lower:
                return AGNOTechnicalCommandType.COMPLIANCE_REVIEW
            else:
                return AGNOTechnicalCommandType.SECURITY_AUDIT
        
        # Architecture patterns
        elif any(keyword in request_lower for keyword in [
            "architecture", "design", "scalability", "system design", "integration", "patterns"
        ]):
            if "scalability" in request_lower or "scale" in request_lower:
                return AGNOTechnicalCommandType.SCALABILITY_ANALYSIS
            elif "integration" in request_lower:
                return AGNOTechnicalCommandType.INTEGRATION_ANALYSIS
            elif "design" in request_lower:
                return AGNOTechnicalCommandType.SYSTEM_DESIGN
            else:
                return AGNOTechnicalCommandType.ARCHITECTURE_REVIEW
        
        # Performance patterns
        elif any(keyword in request_lower for keyword in [
            "performance", "optimization", "benchmark", "load test", "monitoring", "latency"
        ]):
            if "optimization" in request_lower or "optimize" in request_lower:
                return AGNOTechnicalCommandType.OPTIMIZATION_STRATEGY
            elif "load test" in request_lower or "benchmark" in request_lower:
                return AGNOTechnicalCommandType.LOAD_TESTING
            elif "monitoring" in request_lower:
                return AGNOTechnicalCommandType.MONITORING_STRATEGY
            else:
                return AGNOTechnicalCommandType.PERFORMANCE_ANALYSIS
        
        # Multi-team comprehensive operations
        elif any(keyword in request_lower for keyword in [
            "comprehensive", "complete", "full assessment", "system health", "technical audit"
        ]):
            if "audit" in request_lower:
                return AGNOTechnicalCommandType.COMPREHENSIVE_AUDIT
            elif "health" in request_lower:
                return AGNOTechnicalCommandType.SYSTEM_HEALTH_CHECK
            else:
                return AGNOTechnicalCommandType.TECHNICAL_ASSESSMENT
        
        # Default to code analysis
        else:
            return AGNOTechnicalCommandType.CODE_ANALYSIS
    
    async def _execute_agno_technical_command(
        self, 
        request: str, 
        command_type: AGNOTechnicalCommandType, 
        context: TechnicalContext
    ) -> Dict[str, Any]:
        """Execute technical command using appropriate AGNO Teams"""
        
        team_results = {}
        
        try:
            # Route to specific teams based on command type
            if command_type in [
                AGNOTechnicalCommandType.CODE_ANALYSIS,
                AGNOTechnicalCommandType.CODE_REVIEW,
                AGNOTechnicalCommandType.CODEBASE_ASSESSMENT,
                AGNOTechnicalCommandType.REFACTORING_ANALYSIS
            ]:
                if self.code_analysis_team:
                    result = await self._execute_code_analysis(request, command_type, context)
                    team_results["code_analysis"] = result
            
            elif command_type in [
                AGNOTechnicalCommandType.SECURITY_AUDIT,
                AGNOTechnicalCommandType.VULNERABILITY_ASSESSMENT,
                AGNOTechnicalCommandType.PENETRATION_TESTING,
                AGNOTechnicalCommandType.COMPLIANCE_REVIEW
            ]:
                if self.security_team:
                    result = await self._execute_security(request, command_type, context)
                    team_results["security"] = result
            
            elif command_type in [
                AGNOTechnicalCommandType.ARCHITECTURE_REVIEW,
                AGNOTechnicalCommandType.SYSTEM_DESIGN,
                AGNOTechnicalCommandType.SCALABILITY_ANALYSIS,
                AGNOTechnicalCommandType.INTEGRATION_ANALYSIS
            ]:
                if self.architecture_team:
                    result = await self._execute_architecture(request, command_type, context)
                    team_results["architecture"] = result
            
            elif command_type in [
                AGNOTechnicalCommandType.PERFORMANCE_ANALYSIS,
                AGNOTechnicalCommandType.OPTIMIZATION_STRATEGY,
                AGNOTechnicalCommandType.LOAD_TESTING,
                AGNOTechnicalCommandType.MONITORING_STRATEGY
            ]:
                if self.performance_team:
                    result = await self._execute_performance(request, command_type, context)
                    team_results["performance"] = result
            
            # Multi-team operations
            elif command_type in [
                AGNOTechnicalCommandType.COMPREHENSIVE_AUDIT,
                AGNOTechnicalCommandType.TECHNICAL_ASSESSMENT,
                AGNOTechnicalCommandType.SYSTEM_HEALTH_CHECK
            ]:
                # Execute multiple teams in parallel
                tasks = []
                if self.code_analysis_team:
                    tasks.append(self._execute_code_analysis(request, command_type, context))
                if self.security_team:
                    tasks.append(self._execute_security(request, command_type, context))
                if self.architecture_team:
                    tasks.append(self._execute_architecture(request, command_type, context))
                if self.performance_team:
                    tasks.append(self._execute_performance(request, command_type, context))
                
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    team_names = ["code_analysis", "security", "architecture", "performance"][:len(results)]
                    for team_name, result in zip(team_names, results):
                        if not isinstance(result, Exception):
                            team_results[team_name] = result
        
        except Exception as e:
            logger.error(f"AGNO technical team execution failed: {str(e)}")
            team_results["error"] = {"message": str(e), "type": "execution_error"}
        
        return team_results
    
    async def _execute_code_analysis(
        self, 
        request: str, 
        command_type: AGNOTechnicalCommandType, 
        context: TechnicalContext
    ) -> Dict[str, Any]:
        """Execute code analysis operations"""
        
        try:
            codebase_data = context.repository_context or {"request": request}
            
            if command_type == AGNOTechnicalCommandType.CODEBASE_ASSESSMENT:
                return await self.code_analysis_team.analyze_codebase(codebase_data)
            elif command_type == AGNOTechnicalCommandType.CODE_REVIEW:
                diff_data = context.system_context.get("diff_data", codebase_data) if context.system_context else codebase_data
                return await self.code_analysis_team.review_code_changes(diff_data)
            elif command_type == AGNOTechnicalCommandType.REFACTORING_ANALYSIS:
                legacy_code = context.repository_context.get("legacy_code", codebase_data) if context.repository_context else codebase_data
                return await self.code_analysis_team.identify_refactoring_opportunities(legacy_code)
            else:
                # General code analysis
                return await self.code_analysis_team.execute_task(
                    request,
                    context={"request_type": "general_code_analysis", "user_context": context.__dict__}
                )
        except Exception as e:
            logger.error(f"Code analysis execution failed: {e}")
            return {"success": False, "error": str(e), "team": "code_analysis"}
    
    async def _execute_security(
        self, 
        request: str, 
        command_type: AGNOTechnicalCommandType, 
        context: TechnicalContext
    ) -> Dict[str, Any]:
        """Execute security operations"""
        
        try:
            system_data = context.system_context or {"request": request}
            
            if command_type == AGNOTechnicalCommandType.VULNERABILITY_ASSESSMENT:
                vulnerability_data = system_data.get("vulnerability_data", system_data)
                return await self.security_team.assess_vulnerabilities(vulnerability_data)
            else:
                # General security audit
                return await self.security_team.conduct_security_audit(system_data)
        except Exception as e:
            logger.error(f"Security execution failed: {e}")
            return {"success": False, "error": str(e), "team": "security"}
    
    async def _execute_architecture(
        self, 
        request: str, 
        command_type: AGNOTechnicalCommandType, 
        context: TechnicalContext
    ) -> Dict[str, Any]:
        """Execute architecture operations"""
        
        try:
            if command_type == AGNOTechnicalCommandType.SCALABILITY_ANALYSIS:
                scalability_data = context.system_context.get("scalability_data", {"request": request}) if context.system_context else {"request": request}
                return await self.architecture_team.analyze_scalability(scalability_data)
            else:
                # General architecture review
                architecture_data = context.system_context or {"request": request}
                return await self.architecture_team.review_system_architecture(architecture_data)
        except Exception as e:
            logger.error(f"Architecture execution failed: {e}")
            return {"success": False, "error": str(e), "team": "architecture"}
    
    async def _execute_performance(
        self, 
        request: str, 
        command_type: AGNOTechnicalCommandType, 
        context: TechnicalContext
    ) -> Dict[str, Any]:
        """Execute performance operations"""
        
        try:
            if command_type == AGNOTechnicalCommandType.OPTIMIZATION_STRATEGY:
                optimization_target = context.system_context.get("optimization_target", {"request": request}) if context.system_context else {"request": request}
                return await self.performance_team.optimize_system(optimization_target)
            else:
                # General performance analysis
                performance_data = context.system_context or {"request": request}
                return await self.performance_team.analyze_performance(performance_data)
        except Exception as e:
            logger.error(f"Performance execution failed: {e}")
            return {"success": False, "error": str(e), "team": "performance"}
    
    async def _synthesize_team_results(
        self, 
        team_results: Dict[str, Any],
        command_type: AGNOTechnicalCommandType,
        original_request: str,
        context: TechnicalContext
    ) -> AGNOTechnicalResponse:
        """Synthesize results from multiple AGNO teams into comprehensive response"""
        
        if not team_results:
            return AGNOTechnicalResponse(
                success=False,
                content="No AGNO teams were able to process this request. The tactical coordination system needs attention.",
                command_type=command_type.value
            )
        
        # Extract successful results
        successful_teams = []
        team_findings = {}
        all_findings = []
        all_recommendations = []
        all_action_items = []
        all_code_snippets = []
        
        for team_name, result in team_results.items():
            if result.get("success", False):
                successful_teams.append(team_name)
                team_findings[team_name] = result
                
                # Aggregate findings
                if "tactical_insights" in result:
                    all_findings.extend(result["tactical_insights"])
                if "recommendations" in result:
                    all_recommendations.extend(result["recommendations"])
                if "action_items" in result:
                    all_action_items.extend(result["action_items"])
                if "code_snippets" in result:
                    all_code_snippets.extend(result["code_snippets"])
        
        # Generate synthesized content
        content = self._generate_synthesized_content(
            team_results, successful_teams, original_request, command_type
        )
        
        # Generate cross-team synthesis
        cross_team_synthesis = self._generate_cross_team_synthesis(
            successful_teams, team_findings, command_type
        )
        
        # Generate tactical implications
        tactical_implications = self._generate_tactical_implications(
            team_findings, command_type
        )
        
        return AGNOTechnicalResponse(
            success=len(successful_teams) > 0,
            content=content,
            command_type=command_type.value,
            findings=list(set(all_findings))[:5],  # Top 5 unique findings
            recommendations=list(set(all_recommendations))[:5],  # Top 5 unique recommendations
            action_items=list(set(all_action_items))[:5],  # Top 5 unique actions
            code_snippets=all_code_snippets[:3],  # Top 3 code examples
            agno_teams_used=successful_teams,
            team_specific_findings=team_findings,
            cross_team_synthesis=cross_team_synthesis,
            tactical_implications=tactical_implications,
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
        command_type: AGNOTechnicalCommandType
    ) -> str:
        """Generate synthesized content from team results"""
        
        if not successful_teams:
            return f"My tactical intelligence teams hit a snag processing your request: '{original_request}'. Let me recalibrate and try a different approach."
        
        # Build synthesized response
        content_parts = []
        
        # Header based on teams used
        if len(successful_teams) == 1:
            team_name = successful_teams[0].replace("_", " ").title()
            content_parts.append(f"⚔️ **{team_name} Technical Analysis:**\n")
        else:
            content_parts.append(f"🎯 **Multi-Team Tactical Intelligence** ({len(successful_teams)} teams coordinated):\n")
        
        # Add team-specific findings
        for team_name in successful_teams:
            team_result = team_results.get(team_name, {})
            if team_result.get("result", {}).get("content"):
                team_display_name = team_name.replace("_", " ").title()
                content_parts.append(f"**{team_display_name} Findings:**")
                content_parts.append(team_result["result"]["content"][:500] + "...\n" if len(team_result["result"]["content"]) > 500 else team_result["result"]["content"] + "\n")
        
        # Add tactical synthesis if multiple teams
        if len(successful_teams) > 1:
            content_parts.append("\n🔗 **Tactical Intelligence Synthesis:**")
            content_parts.append("Multiple technical intelligence streams have been analyzed and coordinated to provide comprehensive system insights. The tactical analysis reveals optimization opportunities and technical recommendations for immediate implementation.")
        
        return "\n".join(content_parts)
    
    def _generate_cross_team_synthesis(
        self, 
        successful_teams: List[str],
        team_findings: Dict[str, Any],
        command_type: AGNOTechnicalCommandType
    ) -> Optional[str]:
        """Generate cross-team synthesis insights"""
        
        if len(successful_teams) <= 1:
            return None
        
        synthesis_templates = {
            "code_analysis,security": "Code analysis combined with security assessment reveals implementation vulnerabilities requiring tactical remediation.",
            "code_analysis,architecture": "Code and architecture analysis integration enables comprehensive system quality assessment and strategic improvements.",
            "security,architecture": "Security and architecture convergence provides robust system hardening strategies and defensive design patterns.",
            "performance,architecture": "Performance and architecture analysis creates scalable optimization strategies aligned with system design principles.",
            "code_analysis,performance": "Code quality and performance analysis integration identifies optimization opportunities in implementation patterns.",
            "security,performance": "Security and performance analysis balance reveals tactical approaches to secure high-performance systems."
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
            synthesis = f"Tactical coordination across {len(successful_teams)} specialized teams provides comprehensive technical intelligence with cross-functional implementation insights."
        
        return synthesis
    
    def _generate_tactical_implications(
        self, 
        team_findings: Dict[str, Any],
        command_type: AGNOTechnicalCommandType
    ) -> List[str]:
        """Generate tactical implications from team findings"""
        
        implications = []
        
        # Extract implications from team results
        for team_name, findings in team_findings.items():
            if "tactical_insights" in findings:
                implications.extend(findings["tactical_insights"])
            
            # Add team-specific tactical context
            team_implications = {
                "code_analysis": "Code quality directly impacts system reliability, maintenance velocity, and technical debt accumulation.",
                "security": "Security vulnerabilities represent immediate business risk requiring tactical remediation and defensive measures.",
                "architecture": "Architectural decisions determine system scalability limits and operational complexity for years to come.",
                "performance": "Performance bottlenecks multiply under load and directly impact user experience and operational costs."
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
            "orchestrator": "Artemis AGNO Universal Technical Orchestrator",
            "status": "operational",
            "personality": "tactical_technical_intelligence_with_agno_teams",
            "agno_teams": team_status,
            "controlled_domains": self.controlled_domains,
            "capabilities": [
                "multi_team_coordination",
                "specialized_technical_intelligence",
                "cross_team_synthesis",
                "tactical_implications_analysis",
                "code_analysis_operations",
                "security_audit_operations",
                "architecture_review_operations",
                "performance_optimization_operations"
            ],
            "active_sessions": len(self.active_sessions),
            "system_context_cache": len(self.system_context_cache),
            "last_updated": datetime.now().isoformat()
        }
    
    async def get_technical_insights_summary(self) -> Dict[str, Any]:
        """Get consolidated technical insights from all AGNO teams"""
        
        insights_summary = {
            "executive_summary": {
                "orchestration_model": "AGNO Multi-Team Tactical Coordination",
                "intelligence_coverage": "Comprehensive technical intelligence across all domains",
                "team_coordination": f"{len([t for t in self.agno_teams.values() if t])} specialized teams operational",
                "tactical_capability": "Enhanced with cross-team synthesis and tactical implications"
            },
            "team_capabilities": {},
            "tactical_advantages": [
                "Specialized technical teams for domain expertise",
                "Cross-team synthesis for comprehensive technical insights", 
                "Tactical implications analysis for implementation decisions",
                "Scalable team coordination for complex technical challenges"
            ],
            "coordination_benefits": [
                "Technical expertise through specialized AGNO teams",
                "Comprehensive coverage through multi-team operations",
                "Tactical synthesis through cross-team technical intelligence coordination",
                "Actionable insights through personality-driven technical intelligence"
            ]
        }
        
        # Add team-specific capabilities
        for team_name, team in self.agno_teams.items():
            if team:
                insights_summary["team_capabilities"][team_name] = {
                    "domain": getattr(team, 'domain', {}).value if hasattr(team, 'domain') else "technical_operations",
                    "specialization": team_name.replace("_", " ").title(),
                    "agent_count": len(team.team.agents) if hasattr(team, 'team') and team.team else 0,
                    "status": "operational"
                }
        
        return insights_summary