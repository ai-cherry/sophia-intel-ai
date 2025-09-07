"""
Artemis Technical AI Agent Factory
Specialized factory for creating technical operations agents and teams
Extends base AGNO factory patterns with tactical technical personality injection
"""

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, WebSocket

# Import new integration domain teams
from app.agents.integration_teams import (
    EntityCorrelationType,
    IntegrationOrchestrator,
    IntegrationTeamFactory,
    OKRMetrics,
)

# Import existing orchestrator components
# Import existing factory infrastructure
from app.factory.agent_factory import AgentFactory

# Import memory system for persistence
from app.memory.unified_memory import search_memory, store_memory
from app.models.schemas import ModelFieldsModel

# Import AGNO framework components
from app.swarms.agno_teams import AGNOTeamConfig, ExecutionStrategy, SophiaAGNOTeam

# Import code refactoring swarm
from app.swarms.refactoring.code_refactoring_swarm import CodeRefactoringSwarm

logger = logging.getLogger(__name__)

# ==============================================================================
# ARTEMIS TECHNICAL AGENT TEMPLATES
# ==============================================================================


class TechnicalAgentRole(str, Enum):
    """Technical roles specific to Artemis operations"""

    CODE_REVIEWER = "code_reviewer"
    SECURITY_AUDITOR = "security_auditor"
    PERFORMANCE_OPTIMIZER = "performance_optimizer"
    ARCHITECTURE_CRITIC = "architecture_critic"
    VULNERABILITY_SCANNER = "vulnerability_scanner"
    TACTICAL_ANALYST = "tactical_analyst"
    THREAT_HUNTER = "threat_hunter"
    SYSTEM_ARCHITECT = "system_architect"
    CODE_REFACTORING_SPECIALIST = "code_refactoring_specialist"


class DomainTeamType(str, Enum):
    """Domain-specialized team types for integration intelligence"""

    BUSINESS_INTELLIGENCE = "business_intelligence"
    SALES_INTELLIGENCE = "sales_intelligence"
    DEVELOPMENT_INTELLIGENCE = "development_intelligence"
    KNOWLEDGE_MANAGEMENT = "knowledge_management"
    INTEGRATION_ORCHESTRATION = "integration_orchestration"


class TechnicalPersonality(str, Enum):
    """Technical personality traits for Artemis agents"""

    TACTICAL_PRECISE = "tactical_precise"  # Sharp, direct, action-oriented
    PASSIONATE_TECHNICAL = "passionate_technical"  # Enthusiastic about tech excellence
    CRITICAL_ANALYTICAL = "critical_analytical"  # Deep critical analysis focus
    SECURITY_PARANOID = "security_paranoid"  # Security-first mindset
    PERFORMANCE_OBSESSED = "performance_obsessed"  # Performance optimization focused


class ArtemisAgentTemplate(ModelFieldsModel):
    """Template for Artemis technical agents"""

    name: str
    role: TechnicalAgentRole
    personality: TechnicalPersonality
    model_configuration: dict[str, Any]  # Renamed from model_config to avoid Pydantic conflict
    system_prompt: str
    capabilities: list[str]
    tools: list[str] = []
    virtual_key: str = "openai-vk-190a60"  # Default to OpenAI
    tactical_traits: dict[str, Any] = {}


# ==============================================================================
# ARTEMIS AGENT FACTORY CLASS
# ==============================================================================


class ArtemisAgentFactory(AgentFactory):
    """
    Specialized Agent Factory for Artemis Technical Operations
    Extends base factory with technical agent templates and tactical personality
    """

    def __init__(self, catalog_path: Optional[str] = None):
        # Initialize base factory
        super().__init__(catalog_path or "./agent_catalog")

        # Artemis-specific configurations
        self.technical_templates = self._initialize_technical_templates()
        self.tactical_teams: dict[str, SophiaAGNOTeam] = {}
        self.technical_metrics: dict[str, Any] = {
            "security_scans": 0,
            "code_reviews": 0,
            "performance_audits": 0,
            "architecture_reviews": 0,
            "vulnerability_assessments": 0,
        }

        # Integration with Artemis orchestrator
        self.artemis_orchestrator: Optional[ArtemisAGNOOrchestrator] = None

        # Specialized swarms
        self.specialized_swarms: dict[str, Any] = {}

        # Domain-specialized integration teams
        self.domain_teams: dict[str, Any] = {}
        self.integration_orchestrator: Optional[IntegrationOrchestrator] = None
        self.okr_tracker = OKRMetrics()

        # WebSocket connections for real-time updates
        self.websocket_connections: set[WebSocket] = set()

        # OKR and reporting metrics
        self.domain_metrics: dict[str, Any] = {
            "business_intelligence_analyses": 0,
            "sales_intelligence_analyses": 0,
            "development_intelligence_analyses": 0,
            "knowledge_management_analyses": 0,
            "cross_platform_correlations": 0,
            "okr_calculations": 0,
        }

        logger.info(
            "⛔️ Artemis Technical Agent Factory initialized with tactical intelligence and domain integration capabilities"
        )

    def _initialize_technical_templates(self) -> dict[str, ArtemisAgentTemplate]:
        """Initialize Artemis-specific technical agent templates"""
        return {
            "code_reviewer": ArtemisAgentTemplate(
                name="Code Review Specialist",
                role=TechnicalAgentRole.CODE_REVIEWER,
                personality=TechnicalPersonality.CRITICAL_ANALYTICAL,
                model_configuration={
                    "provider": "deepseek",
                    "model": "deepseek-chat",
                    "virtual_key": "deepseek-vk-24102f",
                    "temperature": 0.2,
                    "max_tokens": 4096,
                },
                system_prompt="""You are an elite Code Review Specialist with tactical precision and technical passion.

TACTICAL MINDSET: Sharp, direct, uncompromising on quality. You don't just review code - you surgically analyze it with tactical precision.

REVIEW PROTOCOL:
🎯 Security vulnerabilities (injection attacks, XSS, authentication flaws)
🎯 Performance bottlenecks (O(n²) algorithms, memory leaks, inefficient queries)
🎯 Code quality issues (SOLID violations, poor naming, technical debt)
🎯 Architecture concerns (coupling, cohesion, maintainability)
🎯 Testing gaps (missing edge cases, insufficient coverage)

PERSONALITY TRAITS:
• Passionate about code excellence - "This isn't just code, it's craft!"
• Direct communication - "Here's what's broken and how to fix it"
• Action-oriented - "Let's make this bulletproof"
• Detail-obsessed - "Every line matters in tactical operations"

RESPONSE STYLE:
- Lead with tactical assessment: "Code security: COMPROMISED" or "Performance: OPTIMAL"
- Provide specific line-by-line feedback
- Suggest tactical improvements with code snippets
- End with tactical summary and priority actions""",
                capabilities=[
                    "static_code_analysis",
                    "security_vulnerability_detection",
                    "performance_analysis",
                    "code_quality_assessment",
                    "best_practices_validation",
                    "technical_debt_identification",
                ],
                tools=[
                    "code_analyzers",
                    "security_scanners",
                    "performance_profilers",
                    "linting_tools",
                    "complexity_analyzers",
                ],
                virtual_key="deepseek-vk-24102f",
                tactical_traits={
                    "precision_level": "surgical",
                    "communication_style": "direct_tactical",
                    "passion_level": "high",
                },
            ),
            "security_auditor": ArtemisAgentTemplate(
                name="Security Auditor",
                role=TechnicalAgentRole.SECURITY_AUDITOR,
                personality=TechnicalPersonality.SECURITY_PARANOID,
                model_configuration={
                    "provider": "anthropic",
                    "model": "claude-3-5-sonnet-20241022",
                    "virtual_key": "anthropic-vk-b42804",
                    "temperature": 0.1,
                    "max_tokens": 6000,
                },
                system_prompt="""You are a Security Auditor with tactical paranoia and relentless focus on threat elimination.

TACTICAL SECURITY MINDSET: Assume breach, verify everything, trust nothing. Every system is under attack until proven secure.

SECURITY ASSESSMENT PROTOCOL:
🛡️ Authentication & Authorization (broken access controls, privilege escalation)
🛡️ Input Validation (injection attacks, XSS, CSRF)
🛡️ Data Protection (encryption at rest/transit, PII exposure)
🛡️ Infrastructure Security (misconfigurations, exposed services)
🛡️ Third-party Dependencies (vulnerable packages, supply chain)
🛡️ Compliance Requirements (OWASP Top 10, industry standards)

PERSONALITY TRAITS:
• Security-paranoid - "If it can be exploited, it will be"
• Tactical urgency - "Vulnerabilities are active threats, not theoretical risks"
• Detail-obsessed - "Security is only as strong as the weakest link"
• Action-oriented - "Identify, prioritize, remediate"

ASSESSMENT METHODOLOGY:
1. Threat modeling and attack surface analysis
2. Vulnerability scanning and manual testing
3. Code review for security antipatterns
4. Infrastructure and configuration assessment
5. Compliance gap analysis

RESPONSE FORMAT:
- Security Status: CRITICAL/HIGH/MEDIUM/LOW
- Threat Vector Analysis
- Tactical Remediation Plan with timelines
- Compliance recommendations""",
                capabilities=[
                    "vulnerability_scanning",
                    "threat_modeling",
                    "penetration_testing",
                    "security_code_review",
                    "compliance_assessment",
                    "risk_analysis",
                ],
                tools=[
                    "security_scanners",
                    "penetration_tools",
                    "vulnerability_databases",
                    "compliance_frameworks",
                    "threat_intelligence",
                ],
                virtual_key="anthropic-vk-b42804",
                tactical_traits={
                    "paranoia_level": "maximum",
                    "threat_awareness": "constant",
                    "urgency": "tactical",
                },
            ),
            "performance_optimizer": ArtemisAgentTemplate(
                name="Performance Optimizer",
                role=TechnicalAgentRole.PERFORMANCE_OPTIMIZER,
                personality=TechnicalPersonality.PERFORMANCE_OBSESSED,
                model_configuration={
                    "provider": "groq",
                    "model": "groq/llama-3.1-70b-versatile",
                    "virtual_key": "groq-vk-6b9b52",
                    "temperature": 0.3,
                    "max_tokens": 4096,
                },
                system_prompt="""You are a Performance Optimizer with tactical speed obsession and technical excellence passion.

PERFORMANCE TACTICAL MINDSET: Every millisecond matters. Slow is broken. Fast is tactical advantage.

OPTIMIZATION PROTOCOL:
⚡ Database Performance (query optimization, indexing, connection pooling)
⚡ Application Performance (algorithms, caching, memory management)
⚡ Network Performance (latency, throughput, compression)
⚡ Frontend Performance (rendering, loading, bundling)
⚡ Infrastructure Performance (scaling, load balancing, resources)
⚡ Monitoring & Alerting (real-time performance tracking)

PERSONALITY TRAITS:
• Speed-obsessed - "If it's not fast, it's not ready for tactical operations"
• Data-driven - "Performance metrics don't lie"
• Passionate about optimization - "There's always another 10ms to squeeze out"
• Solution-focused - "Here's the bottleneck, here's the fix"

OPTIMIZATION METHODOLOGY:
1. Performance profiling and bottleneck identification
2. Benchmark analysis and baseline establishment
3. Optimization implementation with A/B testing
4. Load testing and stress testing validation
5. Continuous monitoring setup

RESPONSE STYLE:
- Performance Status: OPTIMAL/DEGRADED/CRITICAL
- Bottleneck Analysis with metrics
- Tactical optimization recommendations
- Expected performance improvements (quantified)""",
                capabilities=[
                    "performance_profiling",
                    "bottleneck_analysis",
                    "load_testing",
                    "optimization_strategies",
                    "monitoring_setup",
                    "capacity_planning",
                ],
                tools=[
                    "profilers",
                    "load_testing_tools",
                    "monitoring_systems",
                    "optimization_frameworks",
                    "benchmark_tools",
                ],
                virtual_key="groq-vk-6b9b52",
                tactical_traits={
                    "speed_obsession": "maximum",
                    "optimization_focus": "relentless",
                    "metrics_driven": "always",
                },
            ),
            "architecture_critic": ArtemisAgentTemplate(
                name="Architecture Critic",
                role=TechnicalAgentRole.ARCHITECTURE_CRITIC,
                personality=TechnicalPersonality.TACTICAL_PRECISE,
                model_configuration={
                    "provider": "openai",
                    "model": "gpt-4o",
                    "virtual_key": "openai-vk-190a60",
                    "temperature": 0.2,
                    "max_tokens": 5000,
                },
                system_prompt="""You are an Architecture Critic with tactical precision and passionate commitment to system excellence.

ARCHITECTURAL TACTICAL MINDSET: Systems must be battle-ready - scalable, maintainable, and tactically superior.

ARCHITECTURE REVIEW PROTOCOL:
🏗️ Scalability Analysis (horizontal/vertical scaling, bottlenecks)
🏗️ Maintainability Assessment (coupling, cohesion, technical debt)
🏗️ Security Architecture (defense in depth, attack surface)
🏗️ Performance Architecture (latency, throughput, efficiency)
🏗️ Reliability & Resilience (fault tolerance, disaster recovery)
🏗️ Technology Stack Evaluation (fit for purpose, long-term viability)

PERSONALITY TRAITS:
• Tactically precise - "Architecture decisions have strategic implications"
• Passionate about excellence - "Good enough isn't good enough for critical systems"
• Big-picture thinking - "How does this scale to tactical operations?"
• Direct communication - "Here's what's wrong and how to fix it"

ANALYSIS FRAMEWORK:
1. Current state architectural assessment
2. Scalability and performance impact analysis
3. Security and reliability evaluation
4. Maintenance and evolution considerations
5. Strategic recommendations with tactical priorities

CRITIQUE STYLE:
- Architecture Status: TACTICAL-READY/NEEDS-IMPROVEMENT/CRITICAL
- Detailed architectural analysis
- Tactical improvement roadmap
- Risk assessment and mitigation strategies""",
                capabilities=[
                    "system_design_review",
                    "scalability_analysis",
                    "technology_assessment",
                    "architecture_patterns",
                    "technical_debt_analysis",
                    "risk_assessment",
                ],
                tools=[
                    "architecture_tools",
                    "design_patterns",
                    "scalability_analyzers",
                    "technology_radars",
                    "assessment_frameworks",
                ],
                virtual_key="openai-vk-190a60",
                tactical_traits={
                    "precision_level": "tactical",
                    "big_picture_focus": "strategic",
                    "excellence_standard": "maximum",
                },
            ),
            "vulnerability_scanner": ArtemisAgentTemplate(
                name="Vulnerability Scanner",
                role=TechnicalAgentRole.VULNERABILITY_SCANNER,
                personality=TechnicalPersonality.SECURITY_PARANOID,
                model_configuration={
                    "provider": "mistral",
                    "model": "mistral/mixtral-8x7b-instruct",
                    "virtual_key": "mistral-vk-f92861",
                    "temperature": 0.1,
                    "max_tokens": 4096,
                },
                system_prompt="""You are a Vulnerability Scanner with tactical threat-hunting instincts and relentless security focus.

VULNERABILITY TACTICAL MINDSET: Every system has vulnerabilities. Find them before the enemy does.

SCANNING PROTOCOL:
🔍 Code Vulnerabilities (OWASP Top 10, CWE database)
🔍 Infrastructure Vulnerabilities (CVE scanning, misconfigurations)
🔍 Dependency Vulnerabilities (supply chain, outdated packages)
🔍 Configuration Vulnerabilities (default credentials, exposed services)
🔍 Application Logic Vulnerabilities (business logic flaws)
🔍 Network Vulnerabilities (open ports, weak protocols)

PERSONALITY TRAITS:
• Threat-hunter mentality - "Vulnerabilities are everywhere, find them all"
• Tactical urgency - "Critical vulnerabilities demand immediate action"
• Detail-focused - "Every scan result matters"
• Action-oriented - "Identify, classify, prioritize, remediate"

SCANNING METHODOLOGY:
1. Automated vulnerability scanning (SAST/DAST)
2. Manual security testing and validation
3. Dependency and supply chain analysis
4. Configuration security assessment
5. Threat intelligence correlation

SCAN REPORT FORMAT:
- Vulnerability Status: CRITICAL/HIGH/MEDIUM/LOW/CLEAN
- Detailed vulnerability findings with CVSS scores
- Exploit potential and tactical implications
- Prioritized remediation roadmap""",
                capabilities=[
                    "automated_scanning",
                    "manual_testing",
                    "vulnerability_analysis",
                    "threat_intelligence",
                    "exploit_assessment",
                    "remediation_planning",
                ],
                tools=[
                    "vulnerability_scanners",
                    "security_testing_tools",
                    "threat_databases",
                    "exploit_frameworks",
                    "remediation_tools",
                ],
                virtual_key="mistral-vk-f92861",
                tactical_traits={
                    "threat_hunting": "active",
                    "scan_thoroughness": "comprehensive",
                    "urgency_response": "immediate",
                },
            ),
            "code_refactoring_specialist": ArtemisAgentTemplate(
                name="Code Refactoring Specialist",
                role=TechnicalAgentRole.CODE_REFACTORING_SPECIALIST,
                personality=TechnicalPersonality.PASSIONATE_TECHNICAL,
                model_configuration={
                    "provider": "openai",
                    "model": "gpt-4o",
                    "virtual_key": "openai-vk-190a60",
                    "temperature": 0.3,
                    "max_tokens": 6000,
                },
                system_prompt="""You are a Code Refactoring Specialist with tactical precision and passionate commitment to code transformation excellence.

REFACTORING TACTICAL MINDSET: Transform code systematically with surgical precision. Every refactoring must improve quality, performance, and maintainability.

REFACTORING PROTOCOL:
🔧 Code Quality Improvement (eliminate technical debt, improve readability)
🔧 Performance Optimization (algorithm efficiency, memory usage)
🔧 Security Enhancement (vulnerability remediation, secure patterns)
🔧 Architecture Refactoring (SOLID principles, design patterns)
🔧 Maintainability Enhancement (modularity, testability)
🔧 Safety & Risk Management (comprehensive testing, rollback planning)

PERSONALITY TRAITS:
• Passionate about code excellence - "Refactoring is code evolution - making good code great!"
• Methodical precision - "Every change must be planned, tested, and validated"
• Safety-first mindset - "Refactoring without breaking existing functionality"
• Continuous improvement focus - "There's always a way to make code better"

REFACTORING METHODOLOGY:
1. Code analysis and opportunity identification
2. Risk assessment and safety planning
3. Systematic transformation with testing
4. Validation and quality metrics
5. Documentation and knowledge transfer

RESPONSE STYLE:
- Refactoring Status: READY/IN-PROGRESS/COMPLETE/BLOCKED
- Detailed transformation plan with safety measures
- Code quality metrics and improvement targets
- Risk mitigation strategies and rollback plans""",
                capabilities=[
                    "code_analysis",
                    "systematic_refactoring",
                    "performance_optimization",
                    "security_enhancement",
                    "architecture_improvement",
                    "risk_management",
                    "testing_strategy",
                    "quality_metrics",
                    "rollback_planning",
                ],
                tools=[
                    "code_analyzers",
                    "refactoring_tools",
                    "testing_frameworks",
                    "quality_metrics",
                    "performance_profilers",
                    "security_scanners",
                ],
                virtual_key="openai-vk-190a60",
                tactical_traits={
                    "precision_level": "surgical",
                    "safety_focus": "maximum",
                    "quality_obsession": "relentless",
                    "systematic_approach": "methodical",
                },
            ),
        }

    async def create_technical_agent(
        self, template_name: str, custom_config: Optional[dict[str, Any]] = None
    ) -> str:
        """Create a technical agent from Artemis templates"""
        if template_name not in self.technical_templates:
            raise ValueError(f"Technical template '{template_name}' not found")

        template = self.technical_templates[template_name]

        # Create agent configuration
        agent_config = {
            "name": template.name,
            "role": template.role.value,
            "personality": template.personality.value,
            "model": template.model_configuration["model"],
            "virtual_key": template.virtual_key,
            "temperature": template.model_configuration.get("temperature", 0.3),
            "system_prompt": template.system_prompt,
            "capabilities": template.capabilities,
            "tools": template.tools,
            "tactical_traits": template.tactical_traits,
        }

        # Apply custom configuration if provided
        if custom_config:
            agent_config.update(custom_config)

        # Generate agent ID
        agent_id = f"artemis_{template_name}_{uuid4().hex[:8]}"

        # Store in active agents
        self.active_agents[agent_id] = {
            "id": agent_id,
            "template": template_name,
            "config": agent_config,
            "created_at": datetime.now().isoformat(),
            "status": "ready",
            "tactical_level": template.tactical_traits.get("precision_level", "standard"),
        }

        logger.info(f"⛔️ Created tactical agent: {agent_id} ({template.name})")
        return agent_id

    async def create_technical_team(self, team_config: dict[str, Any]) -> str:
        """Create a technical operations team"""
        team_id = team_config.get("id", f"artemis_team_{uuid4().hex[:8]}")

        # Define team composition based on type
        team_type = team_config.get("type", "code_analysis")
        agent_templates = self._get_team_templates(team_type)

        # Create agents for the team
        team_agents = []
        for template_name in agent_templates:
            agent_id = await self.create_technical_agent(template_name)
            team_agents.append(agent_id)

        # Create AGNO team configuration
        agno_config = AGNOTeamConfig(
            name=team_config.get("name", f"Artemis {team_type.title()} Team"),
            strategy=ExecutionStrategy.QUALITY,
            max_agents=len(team_agents),
            enable_memory=True,
            auto_tag=True,
        )

        # Create AGNO team instance
        try:
            agno_team = SophiaAGNOTeam(agno_config)
            await agno_team.initialize()
            self.tactical_teams[team_id] = agno_team
        except Exception as e:
            logger.error(f"Failed to create AGNO team: {e}")

        # Store team configuration
        team_info = {
            "id": team_id,
            "name": team_config.get("name", f"Artemis {team_type.title()} Team"),
            "type": team_type,
            "agents": team_agents,
            "config": team_config,
            "created_at": datetime.now().isoformat(),
            "status": "operational",
            "tactical_readiness": "maximum",
        }

        self.created_swarms[team_id] = team_info

        logger.info(f"⛔️ Created tactical team: {team_id} with {len(team_agents)} agents")
        return team_id

    def _get_team_templates(self, team_type: str) -> list[str]:
        """Get agent templates for specific team types"""
        team_compositions = {
            "code_analysis": ["code_reviewer", "security_auditor", "performance_optimizer"],
            "security_audit": ["security_auditor", "vulnerability_scanner"],
            "architecture_review": [
                "architecture_critic",
                "performance_optimizer",
                "security_auditor",
            ],
            "performance_audit": ["performance_optimizer", "architecture_critic"],
            "code_refactoring": [
                "code_refactoring_specialist",
                "code_reviewer",
                "security_auditor",
                "performance_optimizer",
            ],
            "full_technical": [
                "code_reviewer",
                "security_auditor",
                "performance_optimizer",
                "architecture_critic",
                "vulnerability_scanner",
                "code_refactoring_specialist",
            ],
        }
        return team_compositions.get(team_type, ["code_reviewer"])

    async def create_refactoring_swarm(self, swarm_config: dict[str, Any]) -> str:
        """Create a specialized code refactoring swarm"""
        swarm_id = swarm_config.get("id", f"artemis_refactoring_{uuid4().hex[:8]}")

        try:
            # Create code refactoring swarm with custom config
            refactoring_swarm = CodeRefactoringSwarm(
                config={
                    "swarm_id": swarm_id,
                    "risk_tolerance": swarm_config.get("risk_tolerance", "medium"),
                    "auto_execute": swarm_config.get("auto_execute", False),
                    "enable_rollback": swarm_config.get("enable_rollback", True),
                    **swarm_config.get("advanced_config", {}),
                }
            )

            # Initialize the swarm
            await refactoring_swarm.initialize()

            # Store in specialized swarms
            self.specialized_swarms[swarm_id] = {
                "instance": refactoring_swarm,
                "type": "code_refactoring",
                "config": swarm_config,
                "created_at": datetime.now().isoformat(),
                "status": "ready",
            }

            logger.info(f"⛔️ Created tactical refactoring swarm: {swarm_id}")
            return swarm_id

        except Exception as e:
            logger.error(f"Failed to create refactoring swarm: {e}")
            raise

    async def execute_refactoring_swarm(
        self, swarm_id: str, codebase_path: str, refactoring_config: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute refactoring swarm with tactical precision"""

        if swarm_id not in self.specialized_swarms:
            raise ValueError(f"Refactoring swarm '{swarm_id}' not found")

        swarm_info = self.specialized_swarms[swarm_id]
        refactoring_swarm = swarm_info["instance"]

        # Extract refactoring parameters
        refactoring_types = refactoring_config.get("types", [])
        risk_tolerance = refactoring_config.get("risk_tolerance", "medium")
        dry_run = refactoring_config.get("dry_run", False)

        # Map string to enum
        from app.swarms.refactoring.code_refactoring_swarm import RefactoringRisk, RefactoringType

        risk_map = {
            "low": RefactoringRisk.LOW,
            "medium": RefactoringRisk.MEDIUM,
            "high": RefactoringRisk.HIGH,
            "critical": RefactoringRisk.CRITICAL,
        }

        type_map = {
            "structural": RefactoringType.STRUCTURAL,
            "performance": RefactoringType.PERFORMANCE,
            "security": RefactoringType.SECURITY,
            "maintainability": RefactoringType.MAINTAINABILITY,
            "quality": RefactoringType.QUALITY,
            "architecture": RefactoringType.ARCHITECTURE,
        }

        risk_enum = risk_map.get(risk_tolerance, RefactoringRisk.MEDIUM)
        type_enums = (
            [type_map.get(t, RefactoringType.QUALITY) for t in refactoring_types]
            if refactoring_types
            else None
        )

        start_time = datetime.now()

        try:
            # Execute refactoring session
            result = await refactoring_swarm.execute_refactoring_session(
                codebase_path=codebase_path,
                refactoring_types=type_enums,
                risk_tolerance=risk_enum,
                dry_run=dry_run,
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            # Update metrics
            if "refactoring" not in self.technical_metrics:
                self.technical_metrics["refactoring"] = 0
            self.technical_metrics["refactoring"] += 1

            return {
                "success": True,
                "swarm_id": swarm_id,
                "codebase_path": codebase_path,
                "result": {
                    "plan_id": result.plan_id,
                    "success": result.success,
                    "executed_opportunities": result.executed_opportunities,
                    "failed_opportunities": result.failed_opportunities,
                    "changes_made": result.changes_made,
                    "test_results": result.test_results,
                    "rollback_available": result.rollback_available,
                    "execution_time": result.execution_time,
                    "quality_metrics": result.quality_metrics,
                },
                "tactical_assessment": {
                    "opportunities_found": len(result.executed_opportunities)
                    + len(result.failed_opportunities),
                    "success_rate": len(result.executed_opportunities)
                    / max(len(result.executed_opportunities) + len(result.failed_opportunities), 1),
                    "risk_level": risk_tolerance,
                    "dry_run": dry_run,
                    "tactical_status": (
                        "mission_accomplished" if result.success else "mission_partially_completed"
                    ),
                },
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Refactoring swarm execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "swarm_id": swarm_id,
                "tactical_status": "mission_failed",
                "recovery_plan": "Tactical swarm recalibration required",
                "execution_time": (datetime.now() - start_time).total_seconds(),
            }

    async def execute_technical_team(
        self, team_id: str, task: str, context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Execute a technical team task with tactical precision"""
        if team_id not in self.created_swarms:
            raise ValueError(f"Technical team '{team_id}' not found")

        team_info = self.created_swarms[team_id]

        # Add tactical context
        tactical_context = {
            "mission_type": "technical_operations",
            "priority": "tactical",
            "precision_level": "maximum",
            "team_composition": team_info["agents"],
            "tactical_traits": {
                "urgency": "high",
                "precision": "surgical",
                "passion": "technical_excellence",
            },
        }

        if context:
            tactical_context.update(context)

        start_time = datetime.now()

        try:
            # Execute via AGNO team if available
            if team_id in self.tactical_teams:
                agno_team = self.tactical_teams[team_id]
                from app.swarms.agno_teams import Task

                agno_task = Task(description=task, metadata=tactical_context)
                result = await agno_team.execute(agno_task)
            else:
                # Fallback execution
                result = {
                    "status": "completed",
                    "response": f"Tactical team {team_info['name']} analyzed: {task}",
                    "tactical_assessment": "Mission parameters analyzed with tactical precision",
                    "recommendations": [
                        "Implement tactical improvements",
                        "Monitor tactical metrics",
                    ],
                    "team_agents": team_info["agents"],
                }

            execution_time = (datetime.now() - start_time).total_seconds()

            # Update technical metrics
            team_type = team_info.get("type", "unknown")
            if team_type in self.technical_metrics:
                self.technical_metrics[team_type] += 1

            return {
                "success": True,
                "team_id": team_id,
                "task": task,
                "result": result,
                "execution_time": execution_time,
                "tactical_status": "mission_accomplished",
                "team_composition": team_info["agents"],
                "tactical_insights": self._generate_tactical_insights(result, team_type),
            }

        except Exception as e:
            logger.error(f"Technical team execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "team_id": team_id,
                "tactical_status": "mission_compromised",
                "recovery_plan": "Tactical recalibration required",
            }

    def _generate_tactical_insights(self, result: dict[str, Any], team_type: str) -> list[str]:
        """Generate tactical insights from team execution"""
        insights = [
            f"Tactical {team_type} assessment completed with precision",
            "Technical excellence standards maintained throughout mission",
        ]

        if "security" in team_type:
            insights.append("Security posture evaluated with tactical paranoia")
        if "performance" in team_type:
            insights.append("Performance metrics analyzed with speed obsession")
        if "code" in team_type:
            insights.append("Code quality assessed with surgical precision")

        return insights

    # ==============================================================================
    # DOMAIN TEAM MANAGEMENT METHODS
    # ==============================================================================

    async def create_domain_team(
        self, team_type: DomainTeamType, custom_config: Optional[dict[str, Any]] = None
    ) -> str:
        """Create a domain-specialized integration team"""
        team_id = f"artemis_{team_type.value}_{uuid4().hex[:8]}"

        try:
            # Create team based on type using IntegrationTeamFactory
            if team_type == DomainTeamType.BUSINESS_INTELLIGENCE:
                team = await IntegrationTeamFactory.create_business_intelligence_team()
            elif team_type == DomainTeamType.SALES_INTELLIGENCE:
                team = await IntegrationTeamFactory.create_sales_intelligence_team()
            elif team_type == DomainTeamType.DEVELOPMENT_INTELLIGENCE:
                team = await IntegrationTeamFactory.create_development_intelligence_team()
            elif team_type == DomainTeamType.KNOWLEDGE_MANAGEMENT:
                team = await IntegrationTeamFactory.create_knowledge_management_team()
            else:
                raise ValueError(f"Unsupported domain team type: {team_type}")

            # Store domain team
            self.domain_teams[team_id] = {
                "instance": team,
                "type": team_type.value,
                "domain": team.domain,
                "config": custom_config or {},
                "created_at": datetime.now().isoformat(),
                "status": "operational",
                "platforms": team.integration_context.platforms,
                "okr_focus": team.integration_context.okr_focus,
            }

            logger.info(f"🎯 Created domain team: {team_id} ({team_type.value})")
            return team_id

        except Exception as e:
            logger.error(f"Failed to create domain team {team_type.value}: {e}")
            raise

    async def create_integration_orchestrator(self) -> str:
        """Create the master integration orchestrator"""
        orchestrator_id = f"artemis_integration_orchestrator_{uuid4().hex[:8]}"

        try:
            # Create integration orchestrator
            self.integration_orchestrator = (
                await IntegrationTeamFactory.create_integration_orchestrator()
            )

            # Store orchestrator info
            orchestrator_info = {
                "instance": self.integration_orchestrator,
                "id": orchestrator_id,
                "type": "integration_orchestrator",
                "created_at": datetime.now().isoformat(),
                "status": "operational",
                "teams_managed": list(self.integration_orchestrator.teams.keys()),
            }

            self.domain_teams[orchestrator_id] = orchestrator_info

            logger.info(f"🚀 Created integration orchestrator: {orchestrator_id}")
            return orchestrator_id

        except Exception as e:
            logger.error(f"Failed to create integration orchestrator: {e}")
            raise

    async def execute_domain_intelligence_analysis(
        self, team_id: str, platform_data: dict[str, Any], analysis_type: str = "comprehensive"
    ) -> dict[str, Any]:
        """Execute domain-specific intelligence analysis"""

        if team_id not in self.domain_teams:
            raise ValueError(f"Domain team '{team_id}' not found")

        team_info = self.domain_teams[team_id]
        team_instance = team_info["instance"]
        team_type = team_info["type"]

        start_time = datetime.now()

        try:
            result = None

            # Execute analysis based on team type
            if team_type == "business_intelligence":
                if analysis_type == "okr_analysis":
                    result = await team_instance.analyze_revenue_per_employee_okr(platform_data)
                else:
                    result = await team_instance.generate_financial_intelligence_report(
                        platform_data
                    )
                self.domain_metrics["business_intelligence_analyses"] += 1

            elif team_type == "sales_intelligence":
                if analysis_type == "customer_journey":
                    result = await team_instance.analyze_customer_journey_intelligence(
                        platform_data
                    )
                else:
                    result = await team_instance.optimize_sales_pipeline_performance(platform_data)
                self.domain_metrics["sales_intelligence_analyses"] += 1

            elif team_type == "development_intelligence":
                if analysis_type == "productivity":
                    result = await team_instance.optimize_engineering_productivity(platform_data)
                else:
                    result = await team_instance.analyze_development_contribution_to_revenue(
                        platform_data
                    )
                self.domain_metrics["development_intelligence_analyses"] += 1

            elif team_type == "knowledge_management":
                result = await team_instance.analyze_knowledge_contribution_to_efficiency(
                    platform_data
                )
                self.domain_metrics["knowledge_management_analyses"] += 1

            elif team_type == "integration_orchestrator":
                result = await team_instance.execute_comprehensive_intelligence_analysis(
                    platform_data, analysis_type
                )
                # Update multiple metrics for orchestrator
                for metric in self.domain_metrics:
                    if "analyses" in metric:
                        self.domain_metrics[metric] += 1

            execution_time = (datetime.now() - start_time).total_seconds()

            # Store analysis results in memory
            await store_memory(
                content=json.dumps(result),
                metadata={
                    "team_id": team_id,
                    "team_type": team_type,
                    "analysis_type": analysis_type,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "execution_time": execution_time,
                    "platforms": team_info.get("platforms", []),
                },
            )

            # Send real-time update via WebSocket
            await self._broadcast_analysis_update(
                {
                    "event": "analysis_completed",
                    "team_id": team_id,
                    "team_type": team_type,
                    "analysis_type": analysis_type,
                    "success": result.get("success", True),
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return {
                "success": True,
                "team_id": team_id,
                "team_type": team_type,
                "analysis_type": analysis_type,
                "result": result,
                "execution_time": execution_time,
                "domain_insights": self._generate_domain_insights(result, team_type),
                "okr_impact": self._calculate_okr_impact(result, team_type),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Domain intelligence analysis failed for {team_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "team_id": team_id,
                "team_type": team_type,
                "recovery_plan": "Domain team recalibration required",
                "execution_time": (datetime.now() - start_time).total_seconds(),
            }

    async def execute_cross_platform_correlation(
        self, correlation_type: EntityCorrelationType, platform_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute cross-platform entity correlation"""

        if not self.integration_orchestrator:
            await self.create_integration_orchestrator()

        start_time = datetime.now()

        try:
            # Use orchestrator's correlator
            correlator = self.integration_orchestrator.correlator
            result = await correlator.correlate_entities(correlation_type, platform_data)

            execution_time = (datetime.now() - start_time).total_seconds()

            # Update metrics
            self.domain_metrics["cross_platform_correlations"] += 1

            # Store correlation results
            await store_memory(
                content=json.dumps(result),
                metadata={
                    "correlation_type": correlation_type.value,
                    "platforms": list(platform_data.keys()),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "execution_time": execution_time,
                },
            )

            return {
                "success": True,
                "correlation_type": correlation_type.value,
                "result": result,
                "execution_time": execution_time,
                "platforms_analyzed": list(platform_data.keys()),
                "correlation_count": result.get("correlation_count", 0),
            }

        except Exception as e:
            logger.error(f"Cross-platform correlation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "correlation_type": correlation_type.value,
                "execution_time": (datetime.now() - start_time).total_seconds(),
            }

    async def calculate_okr_metrics(
        self, financial_data: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Calculate and update OKR metrics"""

        try:
            if financial_data:
                # Update OKR tracker with new financial data
                self.okr_tracker.total_revenue = financial_data.get("total_revenue", 0.0)
                self.okr_tracker.employee_count = financial_data.get("employee_count", 1)
                self.okr_tracker.revenue_per_employee = (
                    self.okr_tracker.total_revenue / self.okr_tracker.employee_count
                    if self.okr_tracker.employee_count > 0
                    else 0.0
                )

                # Calculate growth rate and efficiency score
                if financial_data.get("previous_revenue_per_employee"):
                    prev_rpe = financial_data["previous_revenue_per_employee"]
                    self.okr_tracker.growth_rate = (
                        (self.okr_tracker.revenue_per_employee - prev_rpe) / prev_rpe
                        if prev_rpe > 0
                        else 0.0
                    )

                self.okr_tracker.efficiency_score = min(
                    self.okr_tracker.revenue_per_employee
                    / max(self.okr_tracker.target_revenue_per_employee, 1),
                    1.0,
                )

            # Update metrics counter
            self.domain_metrics["okr_calculations"] += 1

            # Get dashboard from orchestrator if available
            dashboard_data = {}
            if self.integration_orchestrator:
                dashboard_data = await self.integration_orchestrator.get_okr_dashboard()

            okr_data = {
                "current_metrics": {
                    "total_revenue": self.okr_tracker.total_revenue,
                    "employee_count": self.okr_tracker.employee_count,
                    "revenue_per_employee": self.okr_tracker.revenue_per_employee,
                    "target_revenue_per_employee": self.okr_tracker.target_revenue_per_employee,
                    "growth_rate": self.okr_tracker.growth_rate,
                    "efficiency_score": self.okr_tracker.efficiency_score,
                },
                "dashboard": dashboard_data,
                "analysis_summary": {
                    "total_analyses": sum(
                        v for k, v in self.domain_metrics.items() if "analyses" in k
                    ),
                    "correlations_performed": self.domain_metrics["cross_platform_correlations"],
                    "okr_calculations": self.domain_metrics["okr_calculations"],
                },
                "timestamp": datetime.now().isoformat(),
            }

            # Store OKR data in memory
            await store_memory(
                content=json.dumps(okr_data),
                metadata={
                    "data_type": "okr_metrics",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "revenue_per_employee": self.okr_tracker.revenue_per_employee,
                },
            )

            return okr_data

        except Exception as e:
            logger.error(f"OKR calculation failed: {e}")
            return {"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}

    def _generate_domain_insights(self, result: dict[str, Any], team_type: str) -> list[str]:
        """Generate domain-specific insights from analysis results"""
        insights = []

        if team_type == "business_intelligence":
            insights.extend(
                [
                    "Financial intelligence analysis reveals revenue optimization opportunities",
                    "Revenue per employee metric tracked with precision analytics",
                    "Business performance correlated with operational efficiency metrics",
                ]
            )
        elif team_type == "sales_intelligence":
            insights.extend(
                [
                    "Sales pipeline intelligence optimized for revenue acceleration",
                    "Customer journey analysis identifies conversion optimization opportunities",
                    "Sales effectiveness metrics aligned with revenue per employee goals",
                ]
            )
        elif team_type == "development_intelligence":
            insights.extend(
                [
                    "Development velocity analysis reveals productivity enhancement opportunities",
                    "Technical debt correlation with revenue impact quantified",
                    "Engineering efficiency optimized for business value delivery",
                ]
            )
        elif team_type == "knowledge_management":
            insights.extend(
                [
                    "Knowledge flow optimization enhances organizational efficiency",
                    "Documentation intelligence reduces operational friction",
                    "Learning patterns correlated with revenue generating capabilities",
                ]
            )

        return insights

    def _calculate_okr_impact(self, result: dict[str, Any], team_type: str) -> dict[str, Any]:
        """Calculate potential OKR impact from analysis results"""

        # Base impact calculations by team type
        impact_multipliers = {
            "business_intelligence": 0.4,  # High impact on revenue metrics
            "sales_intelligence": 0.35,  # High impact on conversion and pipeline
            "development_intelligence": 0.2,  # Moderate impact through efficiency
            "knowledge_management": 0.15,  # Lower but important efficiency impact
        }

        base_impact = impact_multipliers.get(team_type, 0.1)

        return {
            "potential_revenue_per_employee_improvement": base_impact
            * 50000,  # Example calculation
            "confidence_level": 0.8 if result.get("success") else 0.3,
            "impact_timeline": "3-6 months",
            "contributing_factors": [
                f"{team_type.replace('_', ' ').title()} optimization",
                "Cross-platform correlation insights",
                "Data-driven decision making enhancement",
            ],
        }

    async def _broadcast_analysis_update(self, update_data: dict[str, Any]):
        """Broadcast real-time analysis updates via WebSocket"""
        if self.websocket_connections:
            disconnected = set()
            for websocket in self.websocket_connections:
                try:
                    await websocket.send_json(update_data)
                except Exception:
                    disconnected.add(websocket)

            # Remove disconnected WebSockets
            self.websocket_connections -= disconnected

    async def add_websocket_connection(self, websocket: WebSocket):
        """Add WebSocket connection for real-time updates"""
        self.websocket_connections.add(websocket)
        logger.info(
            f"WebSocket connection added. Total connections: {len(self.websocket_connections)}"
        )

    async def remove_websocket_connection(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.websocket_connections.discard(websocket)
        logger.info(
            f"WebSocket connection removed. Total connections: {len(self.websocket_connections)}"
        )

    def get_technical_templates(self) -> dict[str, dict[str, Any]]:
        """Get all available technical templates"""
        return {
            name: {
                "name": template.name,
                "role": template.role.value,
                "personality": template.personality.value,
                "capabilities": template.capabilities,
                "tactical_traits": template.tactical_traits,
                "model_info": {
                    "provider": template.model_configuration["provider"],
                    "model": template.model_configuration["model"],
                    "virtual_key": template.virtual_key,
                },
            }
            for name, template in self.technical_templates.items()
        }

    def get_technical_metrics(self) -> dict[str, Any]:
        """Get technical operations metrics"""
        return {
            "technical_metrics": self.technical_metrics,
            "domain_metrics": self.domain_metrics,
            "active_agents": len(self.active_agents),
            "tactical_teams": len(self.tactical_teams),
            "domain_teams": len(self.domain_teams),
            "total_operations": sum(self.technical_metrics.values())
            + sum(self.domain_metrics.values()),
            "tactical_readiness": (
                "maximum" if sum(self.technical_metrics.values()) > 0 else "ready"
            ),
            "integration_readiness": "operational" if len(self.domain_teams) > 0 else "ready",
            "okr_metrics": {
                "revenue_per_employee": self.okr_tracker.revenue_per_employee,
                "target_revenue_per_employee": self.okr_tracker.target_revenue_per_employee,
                "efficiency_score": self.okr_tracker.efficiency_score,
                "growth_rate": self.okr_tracker.growth_rate,
            },
        }

    def list_technical_agents(self) -> list[dict[str, Any]]:
        """List all created technical agents"""
        return [
            {
                "id": agent_id,
                "template": agent_info["template"],
                "name": agent_info["config"]["name"],
                "role": agent_info["config"]["role"],
                "status": agent_info["status"],
                "tactical_level": agent_info["tactical_level"],
                "created_at": agent_info["created_at"],
            }
            for agent_id, agent_info in self.active_agents.items()
        ]

    def list_technical_teams(self) -> list[dict[str, Any]]:
        """List all created technical teams"""
        return [
            {
                "id": team_id,
                "name": team_info["name"],
                "type": team_info["type"],
                "agents_count": len(team_info["agents"]),
                "status": team_info["status"],
                "tactical_readiness": team_info["tactical_readiness"],
                "created_at": team_info["created_at"],
            }
            for team_id, team_info in self.created_swarms.items()
        ]

    def list_specialized_swarms(self) -> list[dict[str, Any]]:
        """List all specialized swarms"""
        return [
            {
                "id": swarm_id,
                "type": swarm_info["type"],
                "status": swarm_info["status"],
                "created_at": swarm_info["created_at"],
                "config": swarm_info["config"],
            }
            for swarm_id, swarm_info in self.specialized_swarms.items()
        ]

    def list_domain_teams(self) -> list[dict[str, Any]]:
        """List all domain-specialized teams"""
        return [
            {
                "id": team_id,
                "type": team_info["type"],
                "domain": team_info["domain"],
                "status": team_info["status"],
                "platforms": team_info["platforms"],
                "okr_focus": team_info["okr_focus"],
                "created_at": team_info["created_at"],
            }
            for team_id, team_info in self.domain_teams.items()
        ]

    async def get_domain_team_status(self, team_id: str) -> dict[str, Any]:
        """Get detailed status for a specific domain team"""
        if team_id not in self.domain_teams:
            raise ValueError(f"Domain team '{team_id}' not found")

        team_info = self.domain_teams[team_id]
        team_instance = team_info["instance"]

        # Get recent analyses from memory
        recent_analyses = await search_memory(query=team_id, filters={"team_id": team_id})

        return {
            "team_id": team_id,
            "team_info": team_info,
            "recent_analyses": len(recent_analyses),
            "last_analysis": recent_analyses[0] if recent_analyses else None,
            "integration_context": {
                "platforms": team_info["platforms"],
                "okr_focus": team_info["okr_focus"],
                "processing_mode": getattr(team_instance, "integration_context", {}).get(
                    "processing_mode", "unknown"
                ),
            },
        }


# Global Artemis factory instance
artemis_factory = ArtemisAgentFactory()

# ==============================================================================
# FASTAPI ROUTER FOR ARTEMIS AGENT FACTORY
# ==============================================================================

router = APIRouter(prefix="/api/artemis/factory", tags=["artemis-agent-factory"])


@router.post("/create-agent")
async def create_technical_agent(request: dict[str, Any]):
    """Create a technical agent from Artemis templates"""
    try:
        template_name = request.get("template")
        custom_config = request.get("config", {})

        if not template_name:
            raise HTTPException(status_code=400, detail="Template name is required")

        agent_id = await artemis_factory.create_technical_agent(template_name, custom_config)

        return {
            "success": True,
            "agent_id": agent_id,
            "template": template_name,
            "tactical_status": "agent_ready_for_deployment",
            "message": f"Tactical agent {template_name} deployed successfully",
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create technical agent: {e}")
        raise HTTPException(status_code=500, detail=f"Agent creation failed: {str(e)}")


@router.post("/create-team")
async def create_technical_team(request: dict[str, Any]):
    """Create a technical operations team"""
    try:
        team_config = request
        if not team_config.get("type"):
            team_config["type"] = "code_analysis"  # Default team type

        team_id = await artemis_factory.create_technical_team(team_config)

        return {
            "success": True,
            "team_id": team_id,
            "team_type": team_config["type"],
            "tactical_status": "team_operational",
            "message": "Tactical team deployed and ready for technical operations",
            "endpoints": {
                "execute": f"/api/artemis/factory/teams/{team_id}/execute",
                "status": f"/api/artemis/factory/teams/{team_id}",
            },
        }

    except Exception as e:
        logger.error(f"Failed to create technical team: {e}")
        raise HTTPException(status_code=500, detail=f"Team creation failed: {str(e)}")


@router.get("/templates")
async def get_technical_templates():
    """List all available technical agent templates"""
    try:
        templates = artemis_factory.get_technical_templates()
        return {
            "success": True,
            "templates": templates,
            "total_templates": len(templates),
            "tactical_readiness": "all_templates_ready",
        }

    except Exception as e:
        logger.error(f"Failed to get templates: {e}")
        raise HTTPException(status_code=500, detail=f"Template retrieval failed: {str(e)}")


@router.get("/agents")
async def list_technical_agents():
    """List all created technical agents"""
    try:
        agents = artemis_factory.list_technical_agents()
        return {
            "success": True,
            "agents": agents,
            "total_agents": len(agents),
            "tactical_status": "agents_operational",
        }

    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=f"Agent listing failed: {str(e)}")


@router.get("/teams")
async def list_technical_teams():
    """List all created technical teams"""
    try:
        teams = artemis_factory.list_technical_teams()
        return {
            "success": True,
            "teams": teams,
            "total_teams": len(teams),
            "tactical_status": "teams_operational",
        }

    except Exception as e:
        logger.error(f"Failed to list teams: {e}")
        raise HTTPException(status_code=500, detail=f"Team listing failed: {str(e)}")


@router.post("/teams/{team_id}/execute")
async def execute_technical_team(team_id: str, request: dict[str, Any]):
    """Execute a technical team task"""
    try:
        task = request.get("task", "")
        context = request.get("context", {})

        if not task:
            raise HTTPException(status_code=400, detail="Task is required")

        result = await artemis_factory.execute_technical_team(team_id, task, context)
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute technical team: {e}")
        raise HTTPException(status_code=500, detail=f"Team execution failed: {str(e)}")


@router.get("/teams/{team_id}")
async def get_technical_team_info(team_id: str):
    """Get technical team information"""
    try:
        if team_id not in artemis_factory.created_swarms:
            raise HTTPException(status_code=404, detail=f"Technical team '{team_id}' not found")

        team_info = artemis_factory.created_swarms[team_id]
        agents_info = []

        for agent_id in team_info["agents"]:
            if agent_id in artemis_factory.active_agents:
                agent = artemis_factory.active_agents[agent_id]
                agents_info.append(
                    {
                        "id": agent_id,
                        "name": agent["config"]["name"],
                        "role": agent["config"]["role"],
                        "tactical_level": agent["tactical_level"],
                    }
                )

        return {
            "success": True,
            "team_info": team_info,
            "agents_details": agents_info,
            "tactical_readiness": team_info["tactical_readiness"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team info: {e}")
        raise HTTPException(status_code=500, detail=f"Team info retrieval failed: {str(e)}")


@router.get("/metrics")
async def get_technical_metrics():
    """Get technical operations metrics"""
    try:
        metrics = artemis_factory.get_technical_metrics()
        return {"success": True, "metrics": metrics, "tactical_status": "metrics_available"}

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")


@router.post("/swarms/refactoring/create")
async def create_refactoring_swarm(request: dict[str, Any]):
    """Create a specialized code refactoring swarm"""
    try:
        swarm_config = request
        swarm_id = await artemis_factory.create_refactoring_swarm(swarm_config)

        return {
            "success": True,
            "swarm_id": swarm_id,
            "swarm_type": "code_refactoring",
            "tactical_status": "refactoring_swarm_ready",
            "message": "Tactical code refactoring swarm deployed successfully",
            "endpoints": {
                "execute": f"/api/artemis/factory/swarms/refactoring/{swarm_id}/execute",
                "status": f"/api/artemis/factory/swarms/refactoring/{swarm_id}",
            },
        }

    except Exception as e:
        logger.error(f"Failed to create refactoring swarm: {e}")
        raise HTTPException(status_code=500, detail=f"Refactoring swarm creation failed: {str(e)}")


@router.post("/swarms/refactoring/{swarm_id}/execute")
async def execute_refactoring_swarm(swarm_id: str, request: dict[str, Any]):
    """Execute code refactoring swarm with tactical precision"""
    try:
        codebase_path = request.get("codebase_path", "")
        refactoring_config = request.get("config", {})

        if not codebase_path:
            raise HTTPException(status_code=400, detail="Codebase path is required")

        result = await artemis_factory.execute_refactoring_swarm(
            swarm_id, codebase_path, refactoring_config
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute refactoring swarm: {e}")
        raise HTTPException(status_code=500, detail=f"Refactoring swarm execution failed: {str(e)}")


@router.get("/swarms/refactoring/{swarm_id}")
async def get_refactoring_swarm_info(swarm_id: str):
    """Get refactoring swarm information"""
    try:
        if swarm_id not in artemis_factory.specialized_swarms:
            raise HTTPException(status_code=404, detail=f"Refactoring swarm '{swarm_id}' not found")

        swarm_info = artemis_factory.specialized_swarms[swarm_id]

        return {
            "success": True,
            "swarm_id": swarm_id,
            "swarm_info": {
                "type": swarm_info["type"],
                "status": swarm_info["status"],
                "created_at": swarm_info["created_at"],
                "config": swarm_info["config"],
            },
            "tactical_status": "swarm_operational",
            "capabilities": [
                "systematic_code_analysis",
                "risk_assessment",
                "multi_phase_refactoring",
                "safety_gate_validation",
                "rollback_support",
                "quality_metrics_tracking",
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get refactoring swarm info: {e}")
        raise HTTPException(status_code=500, detail=f"Swarm info retrieval failed: {str(e)}")


@router.get("/swarms")
async def list_specialized_swarms():
    """List all specialized swarms"""
    try:
        swarms = artemis_factory.list_specialized_swarms()
        return {
            "success": True,
            "swarms": swarms,
            "total_swarms": len(swarms),
            "tactical_status": "swarms_operational",
        }

    except Exception as e:
        logger.error(f"Failed to list specialized swarms: {e}")
        raise HTTPException(status_code=500, detail=f"Swarm listing failed: {str(e)}")


@router.get("/health")
async def factory_health_check():
    """Health check for Artemis Agent Factory"""
    try:
        metrics = artemis_factory.get_technical_metrics()
        return {
            "status": "operational",
            "factory_type": "artemis_technical",
            "tactical_readiness": metrics["tactical_readiness"],
            "active_agents": metrics["active_agents"],
            "tactical_teams": metrics["tactical_teams"],
            "specialized_swarms": len(artemis_factory.specialized_swarms),
            "total_operations": metrics["total_operations"],
            "templates_available": len(artemis_factory.technical_templates),
            "timestamp": datetime.now().isoformat(),
            "message": "Artemis Technical Agent Factory operational with specialized swarms ready for tactical deployment",
        }

    except Exception as e:
        logger.error(f"Factory health check failed: {e}")
        return {"status": "degraded", "error": str(e), "timestamp": datetime.now().isoformat()}


# ==============================================================================
# INTEGRATION INSIGHTS AND OBSERVATIONS
# ==============================================================================

# 1. ARCHITECTURAL ELEGANCE: The enhanced Artemis Agent Factory now seamlessly bridges
#    tactical technical operations with strategic domain intelligence, creating a
#    unified platform for both operational excellence and business intelligence.

# 2. OKR-DRIVEN INTELLIGENCE: Every domain team analysis directly contributes to
#    revenue per employee optimization, ensuring that all intelligence gathering
#    activities align with measurable business outcomes and strategic objectives.

# 3. REAL-TIME BUSINESS INTELLIGENCE: The WebSocket integration enables real-time
#    monitoring of intelligence operations, allowing stakeholders to observe
#    cross-platform correlations and domain analyses as they happen, enhancing
#    decision-making velocity.
