"""
Artemis Unified Factory - Consolidated Agent and Swarm Creation System
Merges ArtemisAgentFactory and MilitaryAgentFactory into a unified system
Enforces 8 concurrent task execution limit and maintains domain separation
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from fastapi import APIRouter, HTTPException, WebSocket

# Import Portkey configuration manager
from app.core.portkey_config import AgentRole, ModelProvider, portkey_manager

# Import memory system for persistence
from app.memory.unified_memory import search_memory, store_memory
from app.models.schemas import ModelFieldsModel

# Import existing orchestrator components
from app.orchestrators.base_orchestrator import OrchestratorConfig

logger = logging.getLogger(__name__)

# ==============================================================================
# UNIFIED CONFIGURATION
# ==============================================================================


class UnifiedArtemisConfig:
    """Unified configuration for Artemis factory"""

    def __init__(self):
        self.max_concurrent_tasks = 8  # Standardized limit as per architecture
        self.domain = "ARTEMIS"
        self.capabilities = [
            "code_generation",
            "code_review",
            "refactoring",
            "security_scanning",
            "architecture_design",
            "tactical_operations",
            "military_coordination",
        ]
        self.tactical_mode_enabled = True
        self.enable_memory_integration = True
        self.enable_websocket_updates = True


# ==============================================================================
# ENUMS AND TYPES
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


class MilitaryUnitType(str, Enum):
    """Military unit classifications"""

    RECON = "reconnaissance"
    TACTICAL = "tactical_operations"
    STRIKE = "strike_force"
    SUPPORT = "support_operations"
    COMMAND = "command_control"


class MissionStatus(str, Enum):
    """Mission execution status codes"""

    PENDING = "AWAITING_DEPLOYMENT"
    ACTIVE = "MISSION_ACTIVE"
    COMPLETE = "MISSION_COMPLETE"
    CRITICAL = "PRIORITY_OVERRIDE"
    ABORT = "MISSION_ABORT"


class TechnicalPersonality(str, Enum):
    """Technical personality traits for Artemis agents"""

    TACTICAL_PRECISE = "tactical_precise"
    PASSIONATE_TECHNICAL = "passionate_technical"
    CRITICAL_ANALYTICAL = "critical_analytical"
    SECURITY_PARANOID = "security_paranoid"
    PERFORMANCE_OBSESSED = "performance_obsessed"


class SwarmType(str, Enum):
    """Types of swarms that can be created"""

    TECHNICAL_TEAM = "technical_team"
    MILITARY_SQUAD = "military_squad"
    REFACTORING_SWARM = "refactoring_swarm"
    DOMAIN_TEAM = "domain_team"
    TACTICAL_MISSION = "tactical_mission"


# ==============================================================================
# DATA MODELS
# ==============================================================================


@dataclass
class AgentProfile:
    """Unified agent profile for both technical and military agents"""

    id: str
    name: str
    role: str
    model: str
    specialty: str
    personality: Optional[str] = None
    clearance_level: int = 3
    deployment_ready: bool = True
    mission_count: int = 0
    success_rate: float = 1.0
    capabilities: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    virtual_key: str = "openai-vk-190a60"
    tactical_traits: Dict[str, Any] = field(default_factory=dict)
    callsign: Optional[str] = None
    rank: Optional[str] = None


@dataclass
class SquadFormation:
    """Squad tactical formation configuration"""

    designation: str
    unit_type: MilitaryUnitType
    motto: str
    minimum_agents: int
    maximum_agents: int
    required_specialists: List[str]
    communication_protocol: str
    chain_of_command: List[str]


@dataclass
class MissionTemplate:
    """Mission execution template"""

    name: str
    objective: str
    units_deployed: List[str]
    phases: List[Dict[str, Any]]
    total_duration: str
    success_criteria: Dict[str, Any]
    priority: str = "NORMAL"


# ==============================================================================
# ARTEMIS UNIFIED FACTORY CLASS
# ==============================================================================


class ArtemisUnifiedFactory:
    """
    Consolidated factory combining agent creation and military swarm configuration
    Enforces 8 concurrent task limit and maintains tactical excellence
    """

    def __init__(self, catalog_path: Optional[str] = None):
        # Unified configuration
        self.config = UnifiedArtemisConfig()

        # Agent and swarm management
        self.agent_templates: Dict[str, AgentProfile] = {}
        self.military_units: Dict[str, Dict[str, Any]] = {}
        self.specialized_swarms: Dict[str, Any] = {}
        self.domain_teams: Dict[str, Any] = {}
        self.active_agents: Dict[str, AgentProfile] = {}
        self.active_swarms: Dict[str, Any] = {}

        # Concurrent task management
        self._concurrent_tasks = 0
        self._task_queue: List[Any] = []
        self._task_lock = asyncio.Lock()

        # Mission management
        self.mission_templates: Dict[str, MissionTemplate] = {}
        self.active_missions: Dict[str, Any] = {}

        # Metrics tracking
        self.technical_metrics = {
            "security_scans": 0,
            "code_reviews": 0,
            "performance_audits": 0,
            "architecture_reviews": 0,
            "vulnerability_assessments": 0,
            "missions_completed": 0,
            "squads_deployed": 0,
        }

        # WebSocket connections for real-time updates
        self.websocket_connections: Set[WebSocket] = set()

        # Initialize templates and configurations
        self._initialize_technical_templates()
        self._initialize_military_units()
        self._initialize_mission_templates()

        logger.info(
            f"⚔️ Artemis Unified Factory initialized with {self.config.max_concurrent_tasks} "
            f"concurrent task limit and tactical intelligence capabilities"
        )

    # ==============================================================================
    # INITIALIZATION METHODS
    # ==============================================================================

    def _initialize_technical_templates(self):
        """Initialize technical agent templates with tactical traits"""
        # Code Reviewer
        self.agent_templates["code_reviewer"] = AgentProfile(
            id="code_reviewer_template",
            name="Code Review Specialist",
            role=TechnicalAgentRole.CODE_REVIEWER,
            model="deepseek/deepseek-chat",
            specialty="Code review with tactical precision",
            personality=TechnicalPersonality.CRITICAL_ANALYTICAL,
            clearance_level=4,
            capabilities=[
                "static_code_analysis",
                "security_vulnerability_detection",
                "performance_analysis",
                "code_quality_assessment",
                "best_practices_validation",
            ],
            tools=["code_analyzers", "security_scanners", "performance_profilers", "linting_tools"],
            virtual_key=(
                portkey_manager.providers[ModelProvider.DEEPSEEK].virtual_key
                if portkey_manager
                else "deepseek-vk-24102f"
            ),
            tactical_traits={
                "precision_level": "surgical",
                "communication_style": "direct_tactical",
                "passion_level": "high",
            },
        )

        # Security Auditor
        self.agent_templates["security_auditor"] = AgentProfile(
            id="security_auditor_template",
            name="Security Auditor",
            role=TechnicalAgentRole.SECURITY_AUDITOR,
            model="anthropic/claude-opus-4.1",
            specialty="Security assessment with tactical paranoia",
            personality=TechnicalPersonality.SECURITY_PARANOID,
            clearance_level=5,
            capabilities=[
                "vulnerability_scanning",
                "threat_modeling",
                "penetration_testing",
                "security_code_review",
                "compliance_assessment",
            ],
            tools=[
                "security_scanners",
                "penetration_tools",
                "vulnerability_databases",
                "compliance_frameworks",
            ],
            virtual_key=(
                portkey_manager.providers[ModelProvider.ANTHROPIC].virtual_key
                if portkey_manager
                else "anthropic-vk-b42804"
            ),
            tactical_traits={
                "paranoia_level": "maximum",
                "threat_awareness": "constant",
                "urgency": "tactical",
            },
        )

        # Performance Optimizer
        self.agent_templates["performance_optimizer"] = AgentProfile(
            id="performance_optimizer_template",
            name="Performance Optimizer",
            role=TechnicalAgentRole.PERFORMANCE_OPTIMIZER,
            model="groq/llama-3.1-70b-versatile",
            specialty="Performance optimization with speed obsession",
            personality=TechnicalPersonality.PERFORMANCE_OBSESSED,
            clearance_level=4,
            capabilities=[
                "performance_profiling",
                "bottleneck_analysis",
                "load_testing",
                "optimization_strategies",
                "capacity_planning",
            ],
            tools=["profilers", "load_testing_tools", "monitoring_systems", "benchmark_tools"],
            virtual_key=(
                portkey_manager.providers[ModelProvider.GROQ].virtual_key
                if portkey_manager
                else "groq-vk-6b9b52"
            ),
            tactical_traits={
                "speed_obsession": "maximum",
                "optimization_focus": "relentless",
                "metrics_driven": "always",
            },
        )

    def _initialize_military_units(self):
        """Initialize military unit configurations"""
        # Reconnaissance Battalion
        self.military_units["recon_battalion"] = {
            "designation": "1st Reconnaissance Battalion 'Pathfinders'",
            "unit_type": MilitaryUnitType.RECON,
            "motto": "First to Know, First to Strike",
            "mission_brief": "Repository scanning and intelligence gathering operations",
            "squad_composition": [
                AgentProfile(
                    id="scout_alpha",
                    name="SCOUT-1",
                    role="Reconnaissance Lead",
                    model="google/gemini-2.5-flash",
                    specialty="Rapid codebase scanning and conflict detection",
                    clearance_level=4,
                    callsign="SCOUT-1",
                    rank="Reconnaissance Lead",
                ),
                AgentProfile(
                    id="scout_bravo",
                    name="SCOUT-2",
                    role="Architecture Analyst",
                    model="google/gemini-2.5-pro",
                    specialty="Structural pattern recognition and dependency mapping",
                    clearance_level=3,
                    callsign="SCOUT-2",
                    rank="Architecture Analyst",
                ),
            ],
            "operational_parameters": {
                "scan_speed": "maximum",
                "coverage_requirement": 0.95,
                "reporting_interval": 30,
                "parallel_operations": True,
            },
            "communication_protocol": "RECON-NET-SECURE",
        }

        # Strike Force
        self.military_units["strike_force"] = {
            "designation": "1st Coding Strike Force 'Operators'",
            "unit_type": MilitaryUnitType.STRIKE,
            "motto": "Swift, Silent, Effective",
            "mission_brief": "Direct action code remediation and implementation",
            "squad_composition": [
                AgentProfile(
                    id="strike_leader",
                    name="OPERATOR-LEAD",
                    role="Strike Team Leader",
                    model="x-ai/grok-code-fast-1",
                    specialty="Advanced code generation and refactoring",
                    clearance_level=5,
                    callsign="OPERATOR-LEAD",
                    rank="Strike Team Leader",
                ),
                AgentProfile(
                    id="operator_alpha",
                    name="OPERATOR-1",
                    role="Senior Developer",
                    model="deepseek/deepseek-reasoner-v3.1",
                    specialty="Complex algorithm implementation",
                    clearance_level=4,
                    callsign="OPERATOR-1",
                    rank="Senior Developer",
                ),
            ],
            "operational_parameters": {
                "execution_mode": "parallel_strike",
                "code_quality_threshold": 0.9,
                "test_coverage_minimum": 0.85,
                "rollback_capability": True,
            },
            "communication_protocol": "STRIKE-SECURE-OPS",
        }

        # Quality Control Division
        self.military_units["qc_division"] = {
            "designation": "Quality Control Division 'Sentinels'",
            "unit_type": MilitaryUnitType.SUPPORT,
            "motto": "Excellence Through Vigilance",
            "mission_brief": "Detailed review and validation of reconnaissance findings",
            "squad_composition": [
                AgentProfile(
                    id="qc_commander",
                    name="SENTINEL-LEAD",
                    role="QC Commander",
                    model="anthropic/claude-3.5-sonnet-20241022",
                    specialty="Strategic quality assessment and validation",
                    clearance_level=5,
                    callsign="SENTINEL-LEAD",
                    rank="QC Commander",
                )
            ],
            "operational_parameters": {
                "review_depth": "comprehensive",
                "validation_rounds": 2,
                "consensus_requirement": 0.8,
            },
            "communication_protocol": "QC-SECURE-CHANNEL",
        }

    def _initialize_mission_templates(self):
        """Initialize mission templates"""
        self.mission_templates["operation_clean_sweep"] = MissionTemplate(
            name="Operation Clean Sweep",
            objective="Full repository scan and comprehensive remediation",
            units_deployed=["recon_battalion", "qc_division", "strike_force"],
            phases=[
                {
                    "phase": 1,
                    "name": "Reconnaissance",
                    "units": ["recon_battalion"],
                    "duration": "5-10 minutes",
                    "deliverables": ["Initial scan report", "Issue inventory"],
                },
                {
                    "phase": 2,
                    "name": "Analysis",
                    "units": ["qc_division"],
                    "duration": "10-15 minutes",
                    "deliverables": ["Detailed findings", "Priority matrix"],
                },
                {
                    "phase": 3,
                    "name": "Execution",
                    "units": ["strike_force"],
                    "duration": "15-30 minutes",
                    "deliverables": ["Code fixes", "Improvements"],
                },
            ],
            total_duration="30-55 minutes",
            success_criteria={
                "issues_resolved": ">90%",
                "test_coverage": ">85%",
                "quality_score": ">95%",
            },
        )

        self.mission_templates["rapid_response"] = MissionTemplate(
            name="Rapid Response Protocol",
            objective="Quick critical issue resolution",
            units_deployed=["recon_battalion", "strike_force"],
            phases=[
                {
                    "phase": 1,
                    "name": "Quick Scan",
                    "units": ["recon_battalion"],
                    "duration": "2-5 minutes",
                    "deliverables": ["Critical issues list"],
                },
                {
                    "phase": 2,
                    "name": "Strike",
                    "units": ["strike_force"],
                    "duration": "5-10 minutes",
                    "deliverables": ["Critical fixes"],
                },
            ],
            total_duration="7-15 minutes",
            success_criteria={"critical_issues_fixed": "100%", "deployment_ready": True},
            priority="HIGH",
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

    async def queue_task(self, task: Dict[str, Any]) -> str:
        """Queue a task for execution when a slot becomes available"""
        task_id = f"queued_{uuid4().hex[:8]}"
        task["id"] = task_id
        task["queued_at"] = datetime.now(timezone.utc).isoformat()

        async with self._task_lock:
            self._task_queue.append(task)
            logger.info(f"Task {task_id} queued. Queue length: {len(self._task_queue)}")

        return task_id

    def get_task_status(self) -> Dict[str, Any]:
        """Get current task execution status"""
        return {
            "active_tasks": self._concurrent_tasks,
            "max_concurrent": self.config.max_concurrent_tasks,
            "queued_tasks": len(self._task_queue),
            "capacity_available": self._concurrent_tasks < self.config.max_concurrent_tasks,
            "utilization": self._concurrent_tasks / self.config.max_concurrent_tasks,
        }

    # ==============================================================================
    # AGENT CREATION METHODS
    # ==============================================================================

    async def create_technical_agent(
        self, template_name: str, custom_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a technical agent from templates"""
        if not await self._acquire_task_slot():
            return await self.queue_task(
                {"type": "create_agent", "template": template_name, "config": custom_config}
            )

        try:
            if template_name not in self.agent_templates:
                raise ValueError(f"Technical template '{template_name}' not found")

            template = self.agent_templates[template_name]
            agent_id = f"artemis_{template_name}_{uuid4().hex[:8]}"

            # Create agent instance from template
            agent = AgentProfile(
                id=agent_id,
                name=template.name,
                role=template.role,
                model=template.model,
                specialty=template.specialty,
                personality=template.personality,
                clearance_level=template.clearance_level,
                capabilities=template.capabilities.copy(),
                tools=template.tools.copy(),
                virtual_key=template.virtual_key,
                tactical_traits=template.tactical_traits.copy(),
            )

            # Apply custom configuration if provided
            if custom_config:
                for key, value in custom_config.items():
                    if hasattr(agent, key):
                        setattr(agent, key, value)

            # Store in active agents
            self.active_agents[agent_id] = agent

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
                        "domain": self.config.domain,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )

            logger.info(f"⚔️ Created tactical agent: {agent_id} ({template.name})")
            return agent_id

        finally:
            await self._release_task_slot()

    async def create_military_squad(
        self, unit_designation: str, mission_parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a military squad from unit configuration"""
        if not await self._acquire_task_slot():
            return await self.queue_task(
                {"type": "create_squad", "unit": unit_designation, "parameters": mission_parameters}
            )

        try:
            if unit_designation not in self.military_units:
                raise ValueError(f"Military unit '{unit_designation}' not found")

            unit = self.military_units[unit_designation]
            squad_id = f"squad_{unit_designation}_{uuid4().hex[:8]}"

            # Create squad with agents
            squad_agents = []
            for agent_template in unit["squad_composition"]:
                agent_id = f"{squad_id}_{agent_template.id}"
                agent = AgentProfile(
                    id=agent_id,
                    name=agent_template.name,
                    role=agent_template.role,
                    model=agent_template.model,
                    specialty=agent_template.specialty,
                    clearance_level=agent_template.clearance_level,
                    callsign=agent_template.callsign,
                    rank=agent_template.rank,
                )
                squad_agents.append(agent)
                self.active_agents[agent_id] = agent

            # Create squad configuration
            squad_config = {
                "id": squad_id,
                "designation": unit["designation"],
                "unit_type": unit["unit_type"],
                "motto": unit["motto"],
                "agents": squad_agents,
                "mission_parameters": mission_parameters or {},
                "operational_parameters": unit["operational_parameters"],
                "communication_protocol": unit["communication_protocol"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": MissionStatus.PENDING,
            }

            self.active_swarms[squad_id] = squad_config
            self.technical_metrics["squads_deployed"] += 1

            logger.info(
                f"🎖️ Created military squad: {squad_id} ({unit['designation']}) "
                f"with {len(squad_agents)} agents"
            )
            return squad_id

        finally:
            await self._release_task_slot()

    async def create_specialized_swarm(
        self, swarm_type: SwarmType, swarm_config: Dict[str, Any]
    ) -> str:
        """Create a specialized swarm (refactoring, domain team, etc.)"""
        if not await self._acquire_task_slot():
            return await self.queue_task(
                {"type": "create_swarm", "swarm_type": swarm_type, "config": swarm_config}
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
            }

            # Create agents based on swarm type
            if swarm_type == SwarmType.REFACTORING_SWARM:
                # Create refactoring specialists
                for role in ["code_reviewer", "performance_optimizer"]:
                    agent_id = await self.create_technical_agent(role)
                    swarm_instance["agents"].append(agent_id)

            elif swarm_type == SwarmType.DOMAIN_TEAM:
                # Create domain-specific team
                domain = swarm_config.get("domain", "technical")
                for role in ["security_auditor", "code_reviewer"]:
                    agent_id = await self.create_technical_agent(role)
                    swarm_instance["agents"].append(agent_id)

            self.specialized_swarms[swarm_id] = swarm_instance

            logger.info(f"🔧 Created specialized swarm: {swarm_id} ({swarm_type.value})")
            return swarm_id

        finally:
            await self._release_task_slot()

    # ==============================================================================
    # MISSION EXECUTION METHODS
    # ==============================================================================

    async def execute_mission(
        self,
        mission_type: str,
        target: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a tactical mission with military units"""
        if not await self._acquire_task_slot():
            return {
                "success": False,
                "reason": "Task limit reached",
                "queued": True,
                "queue_id": await self.queue_task(
                    {
                        "type": "mission",
                        "mission_type": mission_type,
                        "target": target,
                        "parameters": parameters,
                    }
                ),
            }

        try:
            if mission_type not in self.mission_templates:
                raise ValueError(f"Mission template '{mission_type}' not found")

            mission = self.mission_templates[mission_type]
            mission_id = f"mission_{mission_type}_{uuid4().hex[:8]}"

            # Initialize mission
            active_mission = {
                "id": mission_id,
                "template": mission_type,
                "target": target,
                "parameters": parameters or {},
                "status": MissionStatus.ACTIVE,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "phases_completed": [],
                "current_phase": 1,
                "units_deployed": {},
                "results": {},
            }

            # Deploy units for mission
            for unit_name in mission.units_deployed:
                squad_id = await self.create_military_squad(unit_name, parameters)
                active_mission["units_deployed"][unit_name] = squad_id

            # Execute mission phases
            for phase in mission.phases:
                phase_result = await self._execute_mission_phase(
                    mission_id, phase, active_mission["units_deployed"]
                )
                active_mission["phases_completed"].append(phase["name"])
                active_mission["results"][phase["name"]] = phase_result
                active_mission["current_phase"] += 1

                # Broadcast progress if WebSocket connected
                await self._broadcast_mission_update(mission_id, active_mission)

            # Complete mission
            active_mission["status"] = MissionStatus.COMPLETE
            active_mission["completed_at"] = datetime.now(timezone.utc).isoformat()

            self.active_missions[mission_id] = active_mission
            self.technical_metrics["missions_completed"] += 1

            logger.info(f"✅ Mission completed: {mission_id} ({mission.name})")

            return {
                "success": True,
                "mission_id": mission_id,
                "mission_name": mission.name,
                "status": active_mission["status"],
                "phases_completed": active_mission["phases_completed"],
                "results": active_mission["results"],
                "duration": active_mission.get("completed_at", ""),
            }

        except Exception as e:
            logger.error(f"Mission execution failed: {e}")
            return {"success": False, "error": str(e), "mission_type": mission_type}

        finally:
            await self._release_task_slot()

    async def _execute_mission_phase(
        self, mission_id: str, phase: Dict[str, Any], deployed_units: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute a single mission phase"""
        phase_result = {
            "phase": phase["phase"],
            "name": phase["name"],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "units_involved": phase.get("units", []),
            "deliverables": [],
        }

        # Simulate phase execution (would integrate with actual agent execution)
        await asyncio.sleep(2)  # Simulated processing time

        phase_result["completed_at"] = datetime.now(timezone.utc).isoformat()
        phase_result["deliverables"] = phase.get("deliverables", [])
        phase_result["success"] = True

        return phase_result

    # ==============================================================================
    # TEAM MANAGEMENT METHODS
    # ==============================================================================

    async def create_technical_team(self, team_config: Dict[str, Any]) -> str:
        """Create a technical operations team"""
        team_id = f"team_{uuid4().hex[:8]}"
        team_type = team_config.get("type", "code_analysis")

        # Define team composition based on type
        team_compositions = {
            "code_analysis": ["code_reviewer", "security_auditor", "performance_optimizer"],
            "security_audit": ["security_auditor"],
            "architecture_review": ["code_reviewer", "performance_optimizer"],
            "full_technical": list(self.agent_templates.keys()),
        }

        agent_templates = team_compositions.get(team_type, ["code_reviewer"])

        # Create agents for the team
        team_agents = []
        for template_name in agent_templates:
            agent_id = await self.create_technical_agent(template_name)
            team_agents.append(agent_id)

        # Create team configuration
        team_info = {
            "id": team_id,
            "name": team_config.get("name", f"Technical {team_type.title()} Team"),
            "type": team_type,
            "agents": team_agents,
            "config": team_config,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "operational",
            "tactical_readiness": "maximum",
        }

        self.active_swarms[team_id] = team_info

        logger.info(f"⚔️ Created technical team: {team_id} with {len(team_agents)} agents")
        return team_id

    # ==============================================================================
    # WEBSOCKET AND REAL-TIME UPDATES
    # ==============================================================================

    async def _broadcast_mission_update(self, mission_id: str, mission_data: Dict[str, Any]):
        """Broadcast mission updates via WebSocket"""
        if self.websocket_connections:
            update = {
                "type": "mission_update",
                "mission_id": mission_id,
                "status": mission_data["status"],
                "current_phase": mission_data["current_phase"],
                "phases_completed": mission_data["phases_completed"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
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
        logger.info(f"WebSocket connection added. Total: {len(self.websocket_connections)}")

    async def remove_websocket_connection(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.websocket_connections.discard(websocket)
        logger.info(f"WebSocket connection removed. Total: {len(self.websocket_connections)}")

    # ==============================================================================
    # QUERY AND STATUS METHODS
    # ==============================================================================

    def get_technical_templates(self) -> Dict[str, Any]:
        """Get all available technical templates"""
        return {
            name: {
                "name": template.name,
                "role": template.role,
                "personality": template.personality,
                "capabilities": template.capabilities,
                "tactical_traits": template.tactical_traits,
                "model": template.model,
                "virtual_key": template.virtual_key,
            }
            for name, template in self.agent_templates.items()
        }

    def get_military_units(self) -> Dict[str, Any]:
        """Get all military unit configurations"""
        return {
            name: {
                "designation": unit["designation"],
                "unit_type": (
                    unit["unit_type"].value
                    if isinstance(unit["unit_type"], Enum)
                    else unit["unit_type"]
                ),
                "motto": unit["motto"],
                "mission_brief": unit["mission_brief"],
                "squad_size": len(unit["squad_composition"]),
            }
            for name, unit in self.military_units.items()
        }

    def get_mission_templates(self) -> Dict[str, Any]:
        """Get all mission templates"""
        return {
            name: {
                "name": mission.name,
                "objective": mission.objective,
                "units_required": mission.units_deployed,
                "phases": len(mission.phases),
                "duration": mission.total_duration,
                "priority": mission.priority,
            }
            for name, mission in self.mission_templates.items()
        }

    def get_factory_metrics(self) -> Dict[str, Any]:
        """Get factory performance metrics"""
        return {
            "technical_metrics": self.technical_metrics,
            "active_agents": len(self.active_agents),
            "active_swarms": len(self.active_swarms),
            "active_missions": len(self.active_missions),
            "task_status": self.get_task_status(),
            "total_operations": sum(self.technical_metrics.values()),
            "tactical_readiness": (
                "maximum"
                if self._concurrent_tasks < self.config.max_concurrent_tasks
                else "engaged"
            ),
            "domain": self.config.domain,
            "capabilities": self.config.capabilities,
        }

    def list_active_agents(self) -> List[Dict[str, Any]]:
        """List all active agents"""
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "specialty": agent.specialty,
                "clearance_level": agent.clearance_level,
                "callsign": agent.callsign,
                "rank": agent.rank,
            }
            for agent in self.active_agents.values()
        ]

    def list_active_swarms(self) -> List[Dict[str, Any]]:
        """List all active swarms and squads"""
        return [
            {
                "id": swarm["id"],
                "type": swarm.get("type", "military_squad"),
                "agents_count": len(swarm.get("agents", [])),
                "status": swarm.get("status", "unknown"),
                "created_at": swarm.get("created_at", ""),
            }
            for swarm in self.active_swarms.values()
        ]

    def list_active_missions(self) -> List[Dict[str, Any]]:
        """List all active and recent missions"""
        return [
            {
                "id": mission["id"],
                "template": mission["template"],
                "status": mission["status"],
                "current_phase": mission["current_phase"],
                "phases_completed": mission["phases_completed"],
                "started_at": mission["started_at"],
            }
            for mission in self.active_missions.values()
        ]


# ==============================================================================
# FACTORY INSTANCE
# ==============================================================================

# Global factory instance
artemis_unified_factory = ArtemisUnifiedFactory()

# ==============================================================================
# FASTAPI ROUTER
# ==============================================================================

router = APIRouter(prefix="/api/artemis/unified", tags=["artemis-unified-factory"])


@router.post("/agents/create")
async def create_agent(request: Dict[str, Any]):
    """Create a technical agent"""
    try:
        template = request.get("template")
        config = request.get("config", {})

        if not template:
            raise HTTPException(status_code=400, detail="Template name required")

        agent_id = await artemis_unified_factory.create_technical_agent(template, config)

        return {
            "success": True,
            "agent_id": agent_id,
            "template": template,
            "tactical_status": "deployed",
        }
    except Exception as e:
        logger.error(f"Agent creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/squads/create")
async def create_squad(request: Dict[str, Any]):
    """Create a military squad"""
    try:
        unit = request.get("unit")
        parameters = request.get("parameters", {})

        if not unit:
            raise HTTPException(status_code=400, detail="Unit designation required")

        squad_id = await artemis_unified_factory.create_military_squad(unit, parameters)

        return {"success": True, "squad_id": squad_id, "unit": unit, "status": "deployed"}
    except Exception as e:
        logger.error(f"Squad creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/missions/execute")
async def execute_mission(request: Dict[str, Any]):
    """Execute a tactical mission"""
    try:
        mission_type = request.get("mission_type")
        target = request.get("target")
        parameters = request.get("parameters", {})

        if not mission_type:
            raise HTTPException(status_code=400, detail="Mission type required")

        result = await artemis_unified_factory.execute_mission(mission_type, target, parameters)

        return result
    except Exception as e:
        logger.error(f"Mission execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_factory_status():
    """Get factory status and metrics"""
    return artemis_unified_factory.get_factory_metrics()


@router.get("/templates")
async def get_templates():
    """Get all available templates"""
    return {
        "technical_agents": artemis_unified_factory.get_technical_templates(),
        "military_units": artemis_unified_factory.get_military_units(),
        "mission_templates": artemis_unified_factory.get_mission_templates(),
    }


@router.get("/agents")
async def list_agents():
    """List all active agents"""
    return {
        "agents": artemis_unified_factory.list_active_agents(),
        "total": len(artemis_unified_factory.active_agents),
    }


@router.get("/swarms")
async def list_swarms():
    """List all active swarms"""
    return {
        "swarms": artemis_unified_factory.list_active_swarms(),
        "total": len(artemis_unified_factory.active_swarms),
    }


@router.get("/missions")
async def list_missions():
    """List all missions"""
    return {
        "missions": artemis_unified_factory.list_active_missions(),
        "total": len(artemis_unified_factory.active_missions),
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    await artemis_unified_factory.add_websocket_connection(websocket)

    try:
        while True:
            # Keep connection alive and handle messages
            data = await websocket.receive_text()
            # Process commands if needed
    except Exception:
        pass
    finally:
        await artemis_unified_factory.remove_websocket_connection(websocket)
