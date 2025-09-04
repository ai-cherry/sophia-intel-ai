"""
Artemis AGNO Teams Implementation
Technical Operations Teams using AGNO framework with tactical personality-driven responses
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
from app.swarms.shared_resources import (
    PersonalityAGNOTeam,
    PersonalityType,
    shared_resources
)
from agno.agent import Agent
from agno.team import Team

logger = logging.getLogger(__name__)


# Base class extensions for specialized agent creation
class ArtemisAGNOTeamBase(SophiaAGNOTeam):
    """Extended base class with technical personality integration for Artemis teams"""
    
    async def _create_specialized_agent(self, role: str, config: Dict[str, Any]) -> Agent:
        """Create specialized agent with tactical technical personality"""
        
        # Enhance instructions with Artemis's tactical personality
        personality_context = f"""
        You are part of Artemis's tactical technical intelligence team with these personality traits:
        - Communication: {getattr(self, 'personality', TechnicalPersonality()).communication_style}
        - Expertise: {getattr(self, 'personality', TechnicalPersonality()).expertise_level} 
        - Tone: {getattr(self, 'personality', TechnicalPersonality()).response_tone}
        - Focus: {getattr(self, 'personality', TechnicalPersonality()).technical_focus}
        
        You can use direct, tactical language when appropriate. Don't sugarcoat technical issues.
        Be passionate about technical excellence and system integrity. Call out problems directly and provide actionable solutions.
        Think like a senior engineer who's seen systems fail and knows how to make them bulletproof.
        """
        
        enhanced_instructions = f"{config['instructions']}\n\n{personality_context}"
        
        agent = Agent(
            name=config['role'],
            model=config['model'],
            instructions=enhanced_instructions
        )
        
        # Configure Portkey routing
        agent._llm = self.portkey.completions if hasattr(self, 'portkey') else None
        
        return agent
    
    def _enhance_with_technical_personality(self, result: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Enhance result with Artemis's tactical technical personality"""
        
        # Add tactical technical insights
        tactical_insights = {
            "codebase_analysis": [
                "Code quality directly impacts system reliability and maintenance costs",
                "Technical debt compounds over time - address it aggressively or pay later",
                "Architectural decisions made today determine scalability limits tomorrow"
            ],
            "code_review": [
                "Every line of code is a potential point of failure",
                "Consistent patterns make systems maintainable, inconsistency creates chaos",
                "Security vulnerabilities in code are business risk vulnerabilities"
            ],
            "refactoring_opportunities": [
                "Legacy code is expensive code - refactor strategically or replace tactically",
                "Clean code isn't just nice to have - it's a competitive advantage",
                "Technical debt reduction has measurable ROI in development velocity"
            ],
            "security_audit": [
                "Every system is under attack - build like you're at war",
                "Security isn't a feature, it's the foundation everything else depends on",
                "Compliance violations can kill businesses - take them seriously"
            ],
            "vulnerability_assessment": [
                "Unpatched vulnerabilities are ticking time bombs",
                "Security testing isn't paranoia - it's professional responsibility",
                "Zero-day exploits target the unprepared - be prepared"
            ],
            "architecture_review": [
                "Architecture decisions have long-term consequences - choose wisely",
                "Scalability problems are expensive to fix after the fact",
                "System architecture should support business objectives, not constrain them"
            ],
            "scalability_analysis": [
                "Build for the scale you need tomorrow, not just today",
                "Horizontal scaling beats vertical scaling for resilience",
                "Bottlenecks multiply under load - identify and eliminate them early"
            ],
            "performance_analysis": [
                "Performance problems lose customers and revenue - fix them aggressively",
                "Every millisecond of latency has business impact",
                "Performance monitoring is early warning for system failure"
            ],
            "performance_optimization": [
                "Optimize the critical path first - measure twice, optimize once",
                "Premature optimization is evil, but late optimization is expensive",
                "Performance improvements compound across user interactions"
            ]
        }
        
        # Enhance the result with tactical personality-driven additions
        if analysis_type in tactical_insights:
            result["tactical_insights"] = tactical_insights[analysis_type]
            
        result["artemis_personality"] = {
            "communication_style": getattr(self, 'personality', TechnicalPersonality()).communication_style,
            "technical_philosophy": "Build systems that kick ass and scale like beasts - no compromises on technical excellence",
            "tactical_summary": self._generate_tactical_summary(result, analysis_type)
        }
        
        return result
    
    def _generate_tactical_summary(self, result: Dict[str, Any], analysis_type: str) -> str:
        """Generate tactical summary with Artemis's voice"""
        
        tactical_templates = {
            "codebase_analysis": "Codebase assessment reveals tactical opportunities for system hardening and performance optimization.",
            "code_review": "Code review identifies critical issues requiring immediate tactical attention and long-term strategic fixes.",
            "refactoring_opportunities": "Refactoring analysis exposes technical debt that's costing development velocity and system reliability.",
            "security_audit": "Security audit reveals defensive gaps that could compromise system integrity and business continuity.",
            "vulnerability_assessment": "Vulnerability assessment identifies attack vectors requiring immediate tactical remediation.",
            "architecture_review": "Architecture analysis reveals structural opportunities for enhanced scalability and system resilience.",
            "scalability_analysis": "Scalability assessment identifies growth bottlenecks requiring tactical architecture improvements.",
            "performance_analysis": "Performance analysis reveals optimization opportunities for enhanced system efficiency and user experience.",
            "performance_optimization": "Optimization strategy provides tactical improvements for measurable performance gains."
        }
        
        base_summary = tactical_templates.get(analysis_type, "Technical analysis provides actionable insights for system improvement.")
        
        if result.get('success'):
            return f"✅ {base_summary} Tactical recommendations ready for immediate implementation."
        else:
            return f"⚠️ {base_summary} Additional analysis required to optimize tactical outcomes."


class TechnicalDomain(Enum):
    """Technical domain specializations"""
    CODE_ANALYSIS = "code_analysis"
    SECURITY = "security"
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"


@dataclass
class TechnicalPersonality:
    """Artemis's tactical technical personality traits"""
    communication_style: str = "tactical_direct"
    expertise_level: str = "senior_architect"
    response_tone: str = "confident_passionate_with_edge"
    technical_focus: str = "system_optimization"
    allows_tactical_language: bool = True


class ArtemisCodeAnalysisTeam(ArtemisAGNOTeamBase, PersonalityAGNOTeam):
    """
    Code Analysis AGNO Team
    Specialized in code review, quality assessment, and technical debt analysis
    """
    
    def __init__(self, config: Optional[AGNOTeamConfig] = None):
        if not config:
            config = AGNOTeamConfig(
                name="artemis_code_analysis",
                strategy=ExecutionStrategy.QUALITY,
                max_agents=5,
                timeout=45,
                enable_memory=True,
                auto_tag=True
            )
        SophiaAGNOTeam.__init__(self, config)
        PersonalityAGNOTeam.__init__(self, PersonalityType.ARTEMIS_TACTICAL)
        self.domain = TechnicalDomain.CODE_ANALYSIS
        self.personality = TechnicalPersonality(
            communication_style="tactical_code_focused",
            expertise_level="principal_engineer",
            response_tone="direct_passionate_technical",
            technical_focus="code_excellence"
        )
    
    async def initialize(self):
        """Initialize with code analysis focused agents"""
        await super().initialize()
        
        code_agents = {
            "static_analyzer": {
                "role": "static_analyzer",
                "model": self.APPROVED_MODELS["critic"],
                "instructions": """You are Artemis's Static Code Analyzer. Perform deep static analysis of code quality, patterns, and potential issues.
                Be tactical and direct in identifying problems - don't sugarcoat issues that could bite us later. Focus on maintainability, performance, and technical debt.""",
                "temperature": 0.2
            },
            "code_reviewer": {
                "role": "code_reviewer", 
                "model": self.APPROVED_MODELS["judge"],
                "instructions": """You are Artemis's Code Review Specialist. Conduct thorough code reviews with focus on best practices, security, and maintainability.
                Be passionate about code quality - call out shortcuts and technical debt. Provide actionable feedback that makes the codebase bulletproof.""",
                "temperature": 0.3
            },
            "refactoring_expert": {
                "role": "refactoring_expert",
                "model": self.APPROVED_MODELS["refactorer"],
                "instructions": """You are Artemis's Refactoring Expert. Identify refactoring opportunities and provide tactical improvement strategies.
                Don't hold back - if code sucks, say it sucks and explain exactly how to make it not suck. Focus on practical, high-impact refactoring.""",
                "temperature": 0.4
            },
            "architecture_critic": {
                "role": "architecture_critic",
                "model": self.APPROVED_MODELS["architect"],
                "instructions": """You are Artemis's Architecture Critic. Analyze code structure, design patterns, and architectural decisions.
                Be brutally honest about architectural flaws and provide tactical solutions. Focus on scalability, maintainability, and system integrity.""",
                "temperature": 0.3
            },
            "performance_auditor": {
                "role": "performance_auditor",
                "model": self.APPROVED_MODELS["performance"],
                "instructions": """You are Artemis's Performance Code Auditor. Identify performance bottlenecks and optimization opportunities in code.
                Be direct about performance issues - slow code costs money. Provide specific, actionable performance improvements with measurable impact.""",
                "temperature": 0.2
            }
        }
        
        for role, config in code_agents.items():
            agent = await self._create_specialized_agent(role, config)
            self.agents.append(agent)
            
        logger.info(f"⚔️ Artemis Code Analysis Team initialized with {len(code_agents)} specialized agents")
    
    async def analyze_codebase(self, codebase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze entire codebase for quality, architecture, and performance"""
        
        result = await self.execute_task(
            f"Conduct comprehensive codebase analysis focusing on quality, architecture, and performance: {json.dumps(codebase_data, indent=2)}",
            context={"codebase_data": codebase_data, "analysis_type": "comprehensive_analysis"}
        )
        
        return self._enhance_with_technical_personality(result, "codebase_analysis")
    
    async def review_code_changes(self, diff_data: Dict[str, Any]) -> Dict[str, Any]:
        """Review code changes and provide tactical feedback"""
        
        result = await self.execute_task(
            f"Review code changes and provide technical feedback: {json.dumps(diff_data, indent=2)}",
            context={"diff_data": diff_data, "analysis_type": "code_review"}
        )
        
        return self._enhance_with_technical_personality(result, "code_review")
    
    async def identify_refactoring_opportunities(self, legacy_code: Dict[str, Any]) -> Dict[str, Any]:
        """Identify and prioritize refactoring opportunities"""
        
        result = await self.execute_task(
            f"Identify refactoring opportunities and create tactical improvement plan: {json.dumps(legacy_code, indent=2)}",
            context={"legacy_code": legacy_code, "analysis_type": "refactoring_analysis"}
        )
        
        return self._enhance_with_technical_personality(result, "refactoring_opportunities")


class ArtemisSecurityTeam(ArtemisAGNOTeamBase):
    """
    Security AGNO Team
    Specialized in security auditing, vulnerability assessment, and threat analysis
    """
    
    def __init__(self, config: Optional[AGNOTeamConfig] = None):
        if not config:
            config = AGNOTeamConfig(
                name="artemis_security",
                strategy=ExecutionStrategy.CONSENSUS,
                max_agents=4,
                timeout=60,
                enable_memory=True,
                auto_tag=True
            )
        super().__init__(config)
        self.domain = TechnicalDomain.SECURITY
        self.personality = TechnicalPersonality(
            communication_style="security_focused_direct",
            expertise_level="security_architect",
            response_tone="urgent_passionate_protective",
            technical_focus="system_security"
        )
    
    async def initialize(self):
        """Initialize with security focused agents"""
        await super().initialize()
        
        security_agents = {
            "vulnerability_scanner": {
                "role": "vulnerability_scanner",
                "model": self.APPROVED_MODELS["security"],
                "instructions": """You are Artemis's Vulnerability Scanner. Identify security vulnerabilities, attack vectors, and potential threats.
                Don't mess around with security - be aggressive in identifying issues. Every vulnerability is a potential breach waiting to happen.""",
                "temperature": 0.1
            },
            "penetration_tester": {
                "role": "penetration_tester",
                "model": self.APPROVED_MODELS["critic"],
                "instructions": """You are Artemis's Penetration Testing Specialist. Think like an attacker and find ways to exploit weaknesses.
                Be relentless in finding security holes. If there's a way to break it, find it before the bad guys do. No mercy for weak security.""",
                "temperature": 0.3
            },
            "security_architect": {
                "role": "security_architect",
                "model": self.APPROVED_MODELS["architect"],
                "instructions": """You are Artemis's Security Architect. Design security controls, policies, and defensive strategies.
                Build security like your life depends on it - because the business does. Focus on defense in depth and assume everything will be attacked.""",
                "temperature": 0.2
            },
            "compliance_auditor": {
                "role": "compliance_auditor",
                "model": self.APPROVED_MODELS["judge"],
                "instructions": """You are Artemis's Compliance Auditor. Audit systems for regulatory compliance and security standards adherence.
                Compliance isn't optional - it's survival. Be thorough and uncompromising in identifying compliance gaps and risks.""",
                "temperature": 0.2
            }
        }
        
        for role, config in security_agents.items():
            agent = await self._create_specialized_agent(role, config)
            self.agents.append(agent)
            
        logger.info(f"⚔️ Artemis Security Team initialized with {len(security_agents)} specialized agents")
    
    async def conduct_security_audit(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct comprehensive security audit"""
        
        result = await self.execute_task(
            f"Conduct comprehensive security audit and threat assessment: {json.dumps(system_data, indent=2)}",
            context={"system_data": system_data, "analysis_type": "security_audit"}
        )
        
        return self._enhance_with_technical_personality(result, "security_audit")
    
    async def assess_vulnerabilities(self, vulnerability_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess vulnerabilities and provide remediation strategies"""
        
        result = await self.execute_task(
            f"Assess vulnerabilities and create remediation plan: {json.dumps(vulnerability_data, indent=2)}",
            context={"vulnerability_data": vulnerability_data, "analysis_type": "vulnerability_assessment"}
        )
        
        return self._enhance_with_technical_personality(result, "vulnerability_assessment")


class ArtemisArchitectureTeam(ArtemisAGNOTeamBase):
    """
    Architecture AGNO Team  
    Specialized in system architecture review, design patterns, and scalability analysis
    """
    
    def __init__(self, config: Optional[AGNOTeamConfig] = None):
        if not config:
            config = AGNOTeamConfig(
                name="artemis_architecture",
                strategy=ExecutionStrategy.BALANCED,
                max_agents=4,
                timeout=50,
                enable_memory=True,
                auto_tag=True
            )
        super().__init__(config)
        self.domain = TechnicalDomain.ARCHITECTURE
        self.personality = TechnicalPersonality(
            communication_style="architectural_strategic",
            expertise_level="solutions_architect",
            response_tone="confident_systematic",
            technical_focus="system_design"
        )
    
    async def initialize(self):
        """Initialize with architecture focused agents"""
        await super().initialize()
        
        architecture_agents = {
            "system_architect": {
                "role": "system_architect",
                "model": self.APPROVED_MODELS["architect"],
                "instructions": """You are Artemis's System Architect. Analyze system architecture, design patterns, and structural integrity.
                Build systems that don't just work - build systems that kick ass and scale like beasts. No compromises on architectural excellence.""",
                "temperature": 0.3
            },
            "scalability_expert": {
                "role": "scalability_expert",
                "model": self.APPROVED_MODELS["performance"],
                "instructions": """You are Artemis's Scalability Expert. Analyze scalability patterns, bottlenecks, and growth strategies.
                Scale or fail - there's no middle ground. Design for massive scale from day one, because rewriting later sucks and costs a fortune.""",
                "temperature": 0.4
            },
            "pattern_specialist": {
                "role": "pattern_specialist",
                "model": self.APPROVED_MODELS["generator"],
                "instructions": """You are Artemis's Design Pattern Specialist. Analyze and recommend design patterns for optimal system design.
                Use patterns that solve real problems, not academic masturbation. Focus on patterns that make systems maintainable and extensible.""",
                "temperature": 0.5
            },
            "integration_architect": {
                "role": "integration_architect",
                "model": self.APPROVED_MODELS["lead"],
                "instructions": """You are Artemis's Integration Architect. Design system integrations, APIs, and inter-service communication.
                Integration points are where systems break - make them bulletproof. Focus on resilience, monitoring, and graceful failure handling.""",
                "temperature": 0.3
            }
        }
        
        for role, config in architecture_agents.items():
            agent = await self._create_specialized_agent(role, config)
            self.agents.append(agent)
            
        logger.info(f"⚔️ Artemis Architecture Team initialized with {len(architecture_agents)} specialized agents")
    
    async def review_system_architecture(self, architecture_data: Dict[str, Any]) -> Dict[str, Any]:
        """Review system architecture and provide improvement recommendations"""
        
        result = await self.execute_task(
            f"Review system architecture and provide tactical improvements: {json.dumps(architecture_data, indent=2)}",
            context={"architecture_data": architecture_data, "analysis_type": "architecture_review"}
        )
        
        return self._enhance_with_technical_personality(result, "architecture_review")
    
    async def analyze_scalability(self, scalability_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system scalability and growth potential"""
        
        result = await self.execute_task(
            f"Analyze scalability patterns and growth potential: {json.dumps(scalability_data, indent=2)}",
            context={"scalability_data": scalability_data, "analysis_type": "scalability_analysis"}
        )
        
        return self._enhance_with_technical_personality(result, "scalability_analysis")


class ArtemisPerformanceTeam(ArtemisAGNOTeamBase):
    """
    Performance AGNO Team
    Specialized in performance optimization, monitoring, and system efficiency
    """
    
    def __init__(self, config: Optional[AGNOTeamConfig] = None):
        if not config:
            config = AGNOTeamConfig(
                name="artemis_performance",
                strategy=ExecutionStrategy.QUALITY,
                max_agents=4,
                timeout=40,
                enable_memory=True,
                auto_tag=True
            )
        super().__init__(config)
        self.domain = TechnicalDomain.PERFORMANCE
        self.personality = TechnicalPersonality(
            communication_style="performance_obsessed",
            expertise_level="performance_engineer",
            response_tone="intense_results_driven",
            technical_focus="system_optimization"
        )
    
    async def initialize(self):
        """Initialize with performance focused agents"""
        await super().initialize()
        
        performance_agents = {
            "performance_analyzer": {
                "role": "performance_analyzer",
                "model": self.APPROVED_MODELS["performance"],
                "instructions": """You are Artemis's Performance Analyzer. Analyze system performance, identify bottlenecks, and optimize efficiency.
                Performance isn't optional - it's survival. Slow systems lose customers and money. Be ruthless in identifying and fixing performance issues.""",
                "temperature": 0.2
            },
            "optimization_expert": {
                "role": "optimization_expert",
                "model": self.APPROVED_MODELS["refactorer"],
                "instructions": """You are Artemis's Optimization Expert. Find and implement performance optimizations across all system layers.
                Optimize like your job depends on it. Every millisecond matters. Focus on high-impact optimizations that deliver measurable results.""",
                "temperature": 0.3
            },
            "monitoring_specialist": {
                "role": "monitoring_specialist",
                "model": self.APPROVED_MODELS["runner"],
                "instructions": """You are Artemis's Performance Monitoring Specialist. Design monitoring strategies and performance measurement systems.
                You can't optimize what you can't measure. Build monitoring that catches performance issues before users do.""",
                "temperature": 0.4
            },
            "load_testing_engineer": {
                "role": "load_testing_engineer",
                "model": self.APPROVED_MODELS["testing"],
                "instructions": """You are Artemis's Load Testing Engineer. Design and execute performance testing strategies under realistic load.
                Test until it breaks, then make it stronger. Focus on realistic load scenarios that expose real-world performance issues.""",
                "temperature": 0.3
            }
        }
        
        for role, config in performance_agents.items():
            agent = await self._create_specialized_agent(role, config)
            self.agents.append(agent)
            
        logger.info(f"⚔️ Artemis Performance Team initialized with {len(performance_agents)} specialized agents")
    
    async def analyze_performance(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system performance and identify optimization opportunities"""
        
        result = await self.execute_task(
            f"Analyze system performance and identify optimization opportunities: {json.dumps(performance_data, indent=2)}",
            context={"performance_data": performance_data, "analysis_type": "performance_analysis"}
        )
        
        return self._enhance_with_technical_personality(result, "performance_analysis")
    
    async def optimize_system(self, optimization_target: Dict[str, Any]) -> Dict[str, Any]:
        """Provide tactical optimization strategies"""
        
        result = await self.execute_task(
            f"Create tactical optimization plan for performance improvement: {json.dumps(optimization_target, indent=2)}",
            context={"optimization_target": optimization_target, "analysis_type": "optimization_strategy"}
        )
        
        return self._enhance_with_technical_personality(result, "performance_optimization")


# Team Factory for easy instantiation
class ArtemisAGNOTeamFactory:
    """Factory for creating Artemis AGNO Teams"""
    
    @staticmethod
    async def create_code_analysis_team(custom_config: Optional[AGNOTeamConfig] = None) -> ArtemisCodeAnalysisTeam:
        """Create and initialize Code Analysis Team"""
        team = ArtemisCodeAnalysisTeam(custom_config)
        await team.initialize()
        return team
    
    @staticmethod
    async def create_security_team(custom_config: Optional[AGNOTeamConfig] = None) -> ArtemisSecurityTeam:
        """Create and initialize Security Team"""
        team = ArtemisSecurityTeam(custom_config)
        await team.initialize()
        return team
    
    @staticmethod
    async def create_architecture_team(custom_config: Optional[AGNOTeamConfig] = None) -> ArtemisArchitectureTeam:
        """Create and initialize Architecture Team"""
        team = ArtemisArchitectureTeam(custom_config)
        await team.initialize()
        return team
    
    @staticmethod
    async def create_performance_team(custom_config: Optional[AGNOTeamConfig] = None) -> ArtemisPerformanceTeam:
        """Create and initialize Performance Team"""
        team = ArtemisPerformanceTeam(custom_config)
        await team.initialize()
        return team
    
    @staticmethod
    async def create_all_teams() -> Dict[str, SophiaAGNOTeam]:
        """Create all Artemis AGNO Teams"""
        teams = {
            "code_analysis": await ArtemisAGNOTeamFactory.create_code_analysis_team(),
            "security": await ArtemisAGNOTeamFactory.create_security_team(),
            "architecture": await ArtemisAGNOTeamFactory.create_architecture_team(),
            "performance": await ArtemisAGNOTeamFactory.create_performance_team()
        }
        
        logger.info(f"⚔️ All Artemis AGNO Teams initialized: {list(teams.keys())}")
        return teams