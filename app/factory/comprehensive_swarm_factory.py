"""
Comprehensive Agent Factory Configuration System
Integrates mythology agents, military swarms, Portkey routing, and Slack delivery
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from app.core.portkey_manager import TaskType, get_portkey_manager
from app.factory.agent_factory import AgentFactory
from app.memory.unified_memory_router import MemoryDomain
from app.swarms.artemis.military_swarm_config import (
    ARTEMIS_MILITARY_UNITS,
    ARTEMIS_MISSION_TEMPLATES,
    MilitaryAgentFactory,
)
from app.swarms.core.micro_swarm_base import (
    AgentRole,
    CoordinationPattern,
    MicroSwarmCoordinator,
    SwarmConfig,
)
from app.swarms.core.slack_delivery import (
    DeliveryConfig,
    DeliveryFormat,
    DeliveryPriority,
    SlackDeliveryEngine,
    create_executive_delivery_config,
    create_technical_delivery_config,
)
from app.swarms.sophia.mythology_agents import (
    MYTHOLOGY_AGENTS,
    SOPHIA_SWARMS,
    SophiaMythologySwarmFactory,
)

logger = logging.getLogger(__name__)


class SwarmType(Enum):
    """Types of swarms available in the factory"""

    MYTHOLOGY_BUSINESS = "mythology_business"
    MYTHOLOGY_STRATEGIC = "mythology_strategic"
    MYTHOLOGY_HEALTH = "mythology_health"
    MYTHOLOGY_COMPREHENSIVE = "mythology_comprehensive"
    MILITARY_RECON = "military_recon"
    MILITARY_QC = "military_qc"
    MILITARY_PLANNING = "military_planning"
    MILITARY_STRIKE = "military_strike"
    MILITARY_REVIEW = "military_review"
    HYBRID_TACTICAL = "hybrid_tactical"
    CUSTOM = "custom"


class DeploymentSchedule(Enum):
    """Deployment schedule options"""

    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    ON_DEMAND = "on_demand"
    TRIGGERED = "triggered"


@dataclass
class SwarmFactoryConfig:
    """Configuration for swarm factory operations"""

    name: str
    swarm_type: SwarmType
    coordination_pattern: CoordinationPattern
    deployment_schedule: DeploymentSchedule = DeploymentSchedule.ON_DEMAND

    # Cost and performance limits
    max_cost_per_execution: float = 2.0
    max_execution_time_minutes: int = 15
    max_concurrent_swarms: int = 5

    # Memory and context
    memory_domain: MemoryDomain = MemoryDomain.GENERAL
    enable_memory_integration: bool = True
    context_window_size: int = 8000

    # Delivery configuration
    slack_delivery_config: Optional[DeliveryConfig] = None
    auto_deliver_results: bool = False

    # Monitoring and alerts
    enable_monitoring: bool = True
    alert_on_failure: bool = True
    alert_on_cost_threshold: bool = True
    cost_alert_threshold: float = 5.0

    # Additional metadata
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "factory"
    version: str = "1.0"


@dataclass
class ExecutionContext:
    """Context for swarm execution"""

    task: str
    priority: int = 1  # 1=highest, 5=lowest
    requester: str = "system"
    deadline: Optional[datetime] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    delivery_overrides: Optional[DeliveryConfig] = None
    cost_limit_override: Optional[float] = None


@dataclass
class SwarmExecutionResult:
    """Result from swarm execution with factory metadata"""

    execution_id: str
    swarm_type: SwarmType
    swarm_name: str
    task: str

    # Execution results
    success: bool
    final_output: str
    confidence: float
    consensus_achieved: bool

    # Performance metrics
    execution_time_ms: float
    total_cost: float
    tokens_used: int
    models_used: List[str]

    # Agent details
    agents_participated: List[str]
    agent_contributions: Dict[str, Any]
    coordination_pattern: CoordinationPattern

    # Factory metadata
    executed_at: datetime = field(default_factory=datetime.now)
    factory_config: Optional[SwarmFactoryConfig] = None
    execution_context: Optional[ExecutionContext] = None

    # Delivery results
    delivery_results: List[Dict[str, Any]] = field(default_factory=list)

    # Errors and warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ComprehensiveSwarmFactory:
    """
    Comprehensive factory that integrates all swarm types with advanced features:
    - Mythology agents (Hermes, Athena, etc.)
    - Military swarms (Pathfinders, Sentinels, etc.)
    - Portkey model routing
    - Slack delivery
    - Scheduling and monitoring
    """

    def __init__(self):
        # Core components
        self.base_factory = AgentFactory()
        self.portkey = get_portkey_manager()
        self.slack_delivery = SlackDeliveryEngine()
        self.military_factory = MilitaryAgentFactory()
        self.mythology_factory = SophiaMythologySwarmFactory()

        # Factory configurations
        self.swarm_configs: Dict[str, SwarmFactoryConfig] = {}
        self.active_swarms: Dict[str, MicroSwarmCoordinator] = {}
        self.execution_history: List[SwarmExecutionResult] = []

        # Monitoring and metrics
        self.execution_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "total_cost": 0.0,
            "avg_execution_time": 0.0,
            "swarm_type_counts": {},
            "daily_executions": 0,
            "last_reset": datetime.now().date(),
        }

        # Load pre-configured swarms
        self._initialize_preconfigured_swarms()

        logger.info("Comprehensive Swarm Factory initialized")

    def _initialize_preconfigured_swarms(self):
        """Initialize pre-configured swarm types"""

        # Mythology Business Intelligence
        self.swarm_configs["sophia_business_intel"] = SwarmFactoryConfig(
            name="Sophia Business Intelligence Swarm",
            swarm_type=SwarmType.MYTHOLOGY_BUSINESS,
            coordination_pattern=CoordinationPattern.SEQUENTIAL,
            max_cost_per_execution=2.0,
            memory_domain=MemoryDomain.SOPHIA,
            slack_delivery_config=create_executive_delivery_config("#sophia-reports"),
            auto_deliver_results=True,
            tags=["sophia", "business", "intelligence", "hermes", "athena", "minerva"],
        )

        # Mythology Strategic Planning
        self.swarm_configs["sophia_strategic"] = SwarmFactoryConfig(
            name="Sophia Strategic Planning Swarm",
            swarm_type=SwarmType.MYTHOLOGY_STRATEGIC,
            coordination_pattern=CoordinationPattern.DEBATE,
            max_cost_per_execution=3.0,
            memory_domain=MemoryDomain.SOPHIA,
            slack_delivery_config=create_executive_delivery_config("#strategy"),
            auto_deliver_results=True,
            tags=["sophia", "strategy", "planning", "athena", "odin", "minerva"],
        )

        # Military Reconnaissance
        self.swarm_configs["artemis_recon"] = SwarmFactoryConfig(
            name="Artemis Reconnaissance Battalion",
            swarm_type=SwarmType.MILITARY_RECON,
            coordination_pattern=CoordinationPattern.PARALLEL,
            max_cost_per_execution=1.5,
            memory_domain=MemoryDomain.ARTEMIS,
            slack_delivery_config=create_technical_delivery_config("#artemis-ops"),
            auto_deliver_results=True,
            tags=["artemis", "recon", "pathfinders", "scanning", "intelligence"],
        )

        # Military Strike Force
        self.swarm_configs["artemis_strike"] = SwarmFactoryConfig(
            name="Artemis Coding Strike Force",
            swarm_type=SwarmType.MILITARY_STRIKE,
            coordination_pattern=CoordinationPattern.HIERARCHICAL,
            max_cost_per_execution=4.0,
            max_execution_time_minutes=30,
            memory_domain=MemoryDomain.ARTEMIS,
            slack_delivery_config=create_technical_delivery_config("#artemis-ops"),
            auto_deliver_results=True,
            tags=["artemis", "strike", "operators", "coding", "implementation"],
        )

        # Hybrid Tactical (combines mythology wisdom with military precision)
        self.swarm_configs["hybrid_tactical"] = SwarmFactoryConfig(
            name="Hybrid Tactical Analysis Swarm",
            swarm_type=SwarmType.HYBRID_TACTICAL,
            coordination_pattern=CoordinationPattern.CONSENSUS,
            max_cost_per_execution=3.5,
            memory_domain=MemoryDomain.GENERAL,
            slack_delivery_config=DeliveryConfig(
                channel="#tactical-analysis",
                format=DeliveryFormat.DETAILED,
                priority=DeliveryPriority.HIGH,
                include_reasoning=True,
                include_confidence=True,
            ),
            auto_deliver_results=True,
            tags=["hybrid", "tactical", "analysis", "sophia", "artemis"],
        )

        logger.info(f"Initialized {len(self.swarm_configs)} pre-configured swarms")

    async def create_swarm(
        self, config: SwarmFactoryConfig, custom_agents: Optional[List[str]] = None
    ) -> str:
        """
        Create a swarm based on factory configuration

        Args:
            config: Swarm factory configuration
            custom_agents: Optional list of custom agents to use

        Returns:
            Swarm ID for execution
        """
        swarm_id = f"{config.swarm_type.value}_{uuid4().hex[:8]}"

        try:
            # Create the appropriate swarm coordinator
            if config.swarm_type in [
                SwarmType.MYTHOLOGY_BUSINESS,
                SwarmType.MYTHOLOGY_STRATEGIC,
                SwarmType.MYTHOLOGY_HEALTH,
                SwarmType.MYTHOLOGY_COMPREHENSIVE,
            ]:
                coordinator = await self._create_mythology_swarm(config, custom_agents)

            elif config.swarm_type in [
                SwarmType.MILITARY_RECON,
                SwarmType.MILITARY_QC,
                SwarmType.MILITARY_PLANNING,
                SwarmType.MILITARY_STRIKE,
                SwarmType.MILITARY_REVIEW,
            ]:
                coordinator = await self._create_military_swarm(config, custom_agents)

            elif config.swarm_type == SwarmType.HYBRID_TACTICAL:
                coordinator = await self._create_hybrid_swarm(config, custom_agents)

            else:
                coordinator = await self._create_custom_swarm(config, custom_agents)

            # Store the coordinator and config
            self.active_swarms[swarm_id] = coordinator
            self.swarm_configs[swarm_id] = config

            logger.info(f"Created swarm {swarm_id} of type {config.swarm_type.value}")
            return swarm_id

        except Exception as e:
            logger.error(f"Failed to create swarm: {e}")
            raise

    async def _create_mythology_swarm(
        self, config: SwarmFactoryConfig, custom_agents: Optional[List[str]]
    ) -> MicroSwarmCoordinator:
        """Create mythology-based swarm"""

        if config.swarm_type == SwarmType.MYTHOLOGY_BUSINESS:
            return self.mythology_factory.create_business_intelligence_swarm()
        elif config.swarm_type == SwarmType.MYTHOLOGY_STRATEGIC:
            return self.mythology_factory.create_strategic_planning_swarm()
        elif config.swarm_type == SwarmType.MYTHOLOGY_HEALTH:
            return self.mythology_factory.create_business_health_swarm()
        elif config.swarm_type == SwarmType.MYTHOLOGY_COMPREHENSIVE:
            return self.mythology_factory.create_comprehensive_analysis_swarm()
        else:
            # Custom mythology swarm
            agents = custom_agents or ["hermes", "athena", "minerva"]
            return self.mythology_factory.create_custom_swarm(agents, config.coordination_pattern)

    async def _create_military_swarm(
        self, config: SwarmFactoryConfig, custom_agents: Optional[List[str]]
    ) -> MicroSwarmCoordinator:
        """Create military-themed swarm"""

        # Map swarm type to military unit
        unit_mapping = {
            SwarmType.MILITARY_RECON: "recon_battalion",
            SwarmType.MILITARY_QC: "qc_division",
            SwarmType.MILITARY_PLANNING: "planning_command",
            SwarmType.MILITARY_STRIKE: "strike_force",
            SwarmType.MILITARY_REVIEW: "review_battalion",
        }

        unit_name = unit_mapping.get(config.swarm_type)
        if not unit_name:
            raise ValueError(f"Unknown military swarm type: {config.swarm_type}")

        # Get unit configuration
        unit_config = ARTEMIS_MILITARY_UNITS.get(unit_name, {})
        if not unit_config:
            raise ValueError(f"Military unit configuration not found: {unit_name}")

        # Convert military agents to micro-swarm profiles
        agents = []
        squad = unit_config.get("squad_composition", {})

        for role_name, profile in squad.items():
            # Map military roles to micro-swarm roles
            role_mapping = {
                "Reconnaissance Lead": AgentRole.ANALYST,
                "Architecture Analyst": AgentRole.ANALYST,
                "QC Commander": AgentRole.VALIDATOR,
                "Senior Validator": AgentRole.VALIDATOR,
                "Strategic Commander": AgentRole.STRATEGIST,
                "Tactical Advisor": AgentRole.STRATEGIST,
                "Strike Team Leader": AgentRole.STRATEGIST,
                "Senior Developer": AgentRole.ANALYST,
                "Review Commander": AgentRole.VALIDATOR,
            }

            micro_role = role_mapping.get(profile.rank, AgentRole.ANALYST)

            # Create agent profile
            from app.swarms.core.micro_swarm_base import AgentProfile

            agent_profile = AgentProfile(
                role=micro_role,
                name=f"{profile.callsign} - {profile.rank}",
                description=profile.specialty,
                model_preferences=[profile.model],
                specializations=[profile.specialty],
                reasoning_style=f"Military precision with {profile.specialty} expertise",
                confidence_threshold=0.8 + (profile.clearance_level * 0.02),
                max_tokens=6000,
                temperature=0.2,
            )

            agents.append(agent_profile)

        # Create swarm configuration
        swarm_config = SwarmConfig(
            name=config.name,
            domain=config.memory_domain,
            coordination_pattern=config.coordination_pattern,
            agents=agents,
            max_iterations=3,
            consensus_threshold=0.85,
            timeout_seconds=config.max_execution_time_minutes * 60,
            enable_memory_integration=config.enable_memory_integration,
            enable_debate=True,
            cost_limit_usd=config.max_cost_per_execution,
        )

        return MicroSwarmCoordinator(swarm_config)

    async def _create_hybrid_swarm(
        self, config: SwarmFactoryConfig, custom_agents: Optional[List[str]]
    ) -> MicroSwarmCoordinator:
        """Create hybrid swarm combining mythology and military elements"""

        # Combine mythology wisdom with military precision
        from app.swarms.core.micro_swarm_base import AgentProfile
        from app.swarms.sophia.mythology_agents import AthenaAgent, MinervaAgent

        # Get Athena for strategic wisdom
        athena = AthenaAgent.get_profile()
        athena.name = "ATHENA-TACTICAL - Divine Strategic Advisor"
        athena.specializations.extend(["tactical_analysis", "military_strategy"])

        # Get Minerva for validation
        minerva = MinervaAgent.get_profile()
        minerva.name = "MINERVA-OPS - Strategic Validator"
        minerva.specializations.extend(["tactical_validation", "operational_readiness"])

        # Create tactical analyst (military-style)
        tactical_analyst = AgentProfile(
            role=AgentRole.ANALYST,
            name="TACTICAL-1 - Intelligence Analyst",
            description="Rapid tactical analysis with military precision and divine insight",
            model_preferences=["gpt-4", "deepseek-chat"],
            specializations=["tactical_intelligence", "rapid_assessment", "threat_analysis"],
            reasoning_style="Rapid military-style analysis enhanced with mythological wisdom",
            confidence_threshold=0.85,
            max_tokens=6000,
            temperature=0.15,
        )

        agents = [tactical_analyst, athena, minerva]

        swarm_config = SwarmConfig(
            name=config.name,
            domain=config.memory_domain,
            coordination_pattern=config.coordination_pattern,
            agents=agents,
            max_iterations=4,
            consensus_threshold=0.88,
            timeout_seconds=config.max_execution_time_minutes * 60,
            enable_memory_integration=config.enable_memory_integration,
            enable_debate=True,
            cost_limit_usd=config.max_cost_per_execution,
        )

        return MicroSwarmCoordinator(swarm_config)

    async def _create_custom_swarm(
        self, config: SwarmFactoryConfig, custom_agents: Optional[List[str]]
    ) -> MicroSwarmCoordinator:
        """Create custom swarm from agent specifications"""

        if not custom_agents:
            raise ValueError("Custom agents must be specified for custom swarm type")

        # Use base factory to create agents from blueprints
        agents = []
        for agent_id in custom_agents:
            try:
                agent_instance_id = self.base_factory.create_agent_from_blueprint(agent_id)
                agents.append(agent_instance_id)
            except Exception as e:
                logger.warning(f"Failed to create agent {agent_id}: {e}")

        if not agents:
            raise ValueError("No valid agents could be created")

        # For now, create a simple configuration
        # This would need enhancement to properly convert base factory agents
        # to micro-swarm format

        from app.swarms.core.micro_swarm_base import AgentProfile

        # Create placeholder profiles (would need proper conversion)
        agent_profiles = []
        for i, agent_id in enumerate(agents[:3]):  # Limit to 3 for micro-swarm
            profile = AgentProfile(
                role=list(AgentRole)[i % 3],  # Cycle through roles
                name=f"Custom Agent {i+1}",
                description="Custom agent from factory blueprint",
                model_preferences=["gpt-4"],
                specializations=["custom_task"],
                reasoning_style="Custom reasoning based on blueprint configuration",
                confidence_threshold=0.8,
                max_tokens=6000,
                temperature=0.3,
            )
            agent_profiles.append(profile)

        swarm_config = SwarmConfig(
            name=config.name,
            domain=config.memory_domain,
            coordination_pattern=config.coordination_pattern,
            agents=agent_profiles,
            max_iterations=3,
            consensus_threshold=0.85,
            timeout_seconds=config.max_execution_time_minutes * 60,
            enable_memory_integration=config.enable_memory_integration,
            enable_debate=True,
            cost_limit_usd=config.max_cost_per_execution,
        )

        return MicroSwarmCoordinator(swarm_config)

    async def execute_swarm(self, swarm_id: str, context: ExecutionContext) -> SwarmExecutionResult:
        """
        Execute a swarm with comprehensive monitoring and delivery

        Args:
            swarm_id: ID of the swarm to execute
            context: Execution context with task and parameters

        Returns:
            Comprehensive execution result
        """
        execution_id = f"exec_{uuid4().hex[:8]}"
        start_time = datetime.now()

        # Get swarm coordinator and config
        if swarm_id not in self.active_swarms:
            raise ValueError(f"Swarm {swarm_id} not found")

        coordinator = self.active_swarms[swarm_id]
        config = self.swarm_configs.get(swarm_id)

        try:
            # Check cost limits
            cost_limit = context.cost_limit_override or config.max_cost_per_execution
            if cost_limit and cost_limit > 10.0:  # Safety check
                raise ValueError(f"Cost limit too high: ${cost_limit}")

            # Add factory context
            execution_context = {
                "task_description": context.task,
                "swarm_name": config.name if config else swarm_id,
                "coordination_pattern": coordinator.config.coordination_pattern.value,
                "requester": context.requester,
                "priority": context.priority,
                "cost_limit": cost_limit,
                **context.context_data,
            }

            # Execute the swarm
            swarm_result = await coordinator.execute(context.task, execution_context)

            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Create comprehensive result
            result = SwarmExecutionResult(
                execution_id=execution_id,
                swarm_type=config.swarm_type if config else SwarmType.CUSTOM,
                swarm_name=config.name if config else swarm_id,
                task=context.task,
                success=swarm_result.success,
                final_output=swarm_result.final_output,
                confidence=swarm_result.confidence,
                consensus_achieved=swarm_result.consensus_achieved,
                execution_time_ms=execution_time_ms,
                total_cost=swarm_result.total_cost,
                tokens_used=sum(
                    msg.metadata.get("tokens_used", 0) for msg in swarm_result.reasoning_chain
                ),
                models_used=list(
                    set(
                        msg.metadata.get("model_used", "unknown")
                        for msg in swarm_result.reasoning_chain
                    )
                ),
                agents_participated=[
                    role.value for role in swarm_result.agent_contributions.keys()
                ],
                agent_contributions=swarm_result.agent_contributions,
                coordination_pattern=coordinator.config.coordination_pattern,
                factory_config=config,
                execution_context=context,
                errors=swarm_result.errors,
            )

            # Auto-deliver results if configured
            if config and config.auto_deliver_results and config.slack_delivery_config:
                delivery_config = context.delivery_overrides or config.slack_delivery_config
                delivery_result = await self.slack_delivery.deliver_result(
                    swarm_result=swarm_result, config=delivery_config, context=execution_context
                )
                result.delivery_results.append(
                    {
                        "delivery_id": delivery_result.delivery_id,
                        "success": delivery_result.success,
                        "channel": delivery_result.channel,
                        "error": delivery_result.error_message,
                    }
                )

            # Update metrics
            self._update_execution_metrics(result)

            # Store result
            self.execution_history.append(result)

            logger.info(f"Swarm execution completed: {execution_id} in {execution_time_ms:.2f}ms")

            return result

        except Exception as e:
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.error(f"Swarm execution failed: {e}")

            # Create error result
            error_result = SwarmExecutionResult(
                execution_id=execution_id,
                swarm_type=config.swarm_type if config else SwarmType.CUSTOM,
                swarm_name=config.name if config else swarm_id,
                task=context.task,
                success=False,
                final_output=f"Execution failed: {str(e)}",
                confidence=0.0,
                consensus_achieved=False,
                execution_time_ms=execution_time_ms,
                total_cost=0.0,
                tokens_used=0,
                models_used=[],
                agents_participated=[],
                agent_contributions={},
                coordination_pattern=coordinator.config.coordination_pattern,
                factory_config=config,
                execution_context=context,
                errors=[str(e)],
            )

            self.execution_history.append(error_result)
            return error_result

    def _update_execution_metrics(self, result: SwarmExecutionResult):
        """Update factory execution metrics"""

        # Reset daily counter if needed
        today = datetime.now().date()
        if self.execution_metrics["last_reset"] != today:
            self.execution_metrics["daily_executions"] = 0
            self.execution_metrics["last_reset"] = today

        # Update counters
        self.execution_metrics["total_executions"] += 1
        self.execution_metrics["daily_executions"] += 1

        if result.success:
            self.execution_metrics["successful_executions"] += 1

        self.execution_metrics["total_cost"] += result.total_cost

        # Update averages
        total = self.execution_metrics["total_executions"]
        self.execution_metrics["avg_execution_time"] = (
            self.execution_metrics["avg_execution_time"] * (total - 1) + result.execution_time_ms
        ) / total

        # Update swarm type counts
        swarm_type = result.swarm_type.value
        self.execution_metrics["swarm_type_counts"][swarm_type] = (
            self.execution_metrics["swarm_type_counts"].get(swarm_type, 0) + 1
        )

    def get_available_swarms(self) -> Dict[str, Dict[str, Any]]:
        """Get all available swarm configurations"""

        available = {}

        for swarm_id, config in self.swarm_configs.items():
            available[swarm_id] = {
                "name": config.name,
                "type": config.swarm_type.value,
                "coordination_pattern": config.coordination_pattern.value,
                "max_cost": config.max_cost_per_execution,
                "max_time_minutes": config.max_execution_time_minutes,
                "memory_domain": config.memory_domain.value,
                "auto_deliver": config.auto_deliver_results,
                "tags": config.tags,
                "created_at": config.created_at.isoformat(),
            }

        return available

    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get comprehensive execution metrics"""

        # Calculate success rate
        success_rate = 0.0
        if self.execution_metrics["total_executions"] > 0:
            success_rate = (
                self.execution_metrics["successful_executions"]
                / self.execution_metrics["total_executions"]
            )

        # Recent performance (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_executions = [r for r in self.execution_history if r.executed_at >= recent_cutoff]

        return {
            "overview": {
                "total_executions": self.execution_metrics["total_executions"],
                "successful_executions": self.execution_metrics["successful_executions"],
                "success_rate": success_rate,
                "total_cost_usd": self.execution_metrics["total_cost"],
                "avg_execution_time_ms": self.execution_metrics["avg_execution_time"],
                "daily_executions": self.execution_metrics["daily_executions"],
            },
            "swarm_types": self.execution_metrics["swarm_type_counts"],
            "active_swarms": len(self.active_swarms),
            "configured_swarms": len(self.swarm_configs),
            "recent_performance": {
                "executions_24h": len(recent_executions),
                "success_rate_24h": (
                    len([r for r in recent_executions if r.success]) / len(recent_executions)
                    if recent_executions
                    else 0
                ),
                "avg_cost_24h": (
                    sum(r.total_cost for r in recent_executions) / len(recent_executions)
                    if recent_executions
                    else 0
                ),
            },
            "top_performers": self._get_top_performing_swarms(),
            "cost_analysis": self._get_cost_analysis(),
        }

    def _get_top_performing_swarms(self) -> List[Dict[str, Any]]:
        """Get top performing swarms by success rate and efficiency"""

        swarm_performance = {}

        for result in self.execution_history:
            swarm_name = result.swarm_name
            if swarm_name not in swarm_performance:
                swarm_performance[swarm_name] = {
                    "executions": 0,
                    "successes": 0,
                    "total_time": 0.0,
                    "total_cost": 0.0,
                    "avg_confidence": 0.0,
                }

            perf = swarm_performance[swarm_name]
            perf["executions"] += 1
            if result.success:
                perf["successes"] += 1
            perf["total_time"] += result.execution_time_ms
            perf["total_cost"] += result.total_cost
            perf["avg_confidence"] += result.confidence

        # Calculate final metrics
        performers = []
        for swarm_name, perf in swarm_performance.items():
            if perf["executions"] > 0:
                performers.append(
                    {
                        "swarm_name": swarm_name,
                        "success_rate": perf["successes"] / perf["executions"],
                        "avg_time_ms": perf["total_time"] / perf["executions"],
                        "avg_cost": perf["total_cost"] / perf["executions"],
                        "avg_confidence": perf["avg_confidence"] / perf["executions"],
                        "total_executions": perf["executions"],
                    }
                )

        # Sort by success rate and confidence
        performers.sort(key=lambda x: (x["success_rate"], x["avg_confidence"]), reverse=True)
        return performers[:5]

    def _get_cost_analysis(self) -> Dict[str, Any]:
        """Get cost analysis across swarms and time periods"""

        if not self.execution_history:
            return {"total_cost": 0.0, "daily_costs": {}, "cost_by_swarm": {}}

        daily_costs = {}
        cost_by_swarm = {}

        for result in self.execution_history:
            # Daily costs
            day_key = result.executed_at.date().isoformat()
            daily_costs[day_key] = daily_costs.get(day_key, 0.0) + result.total_cost

            # Cost by swarm
            swarm_type = result.swarm_type.value
            cost_by_swarm[swarm_type] = cost_by_swarm.get(swarm_type, 0.0) + result.total_cost

        return {
            "total_cost": sum(r.total_cost for r in self.execution_history),
            "daily_costs": daily_costs,
            "cost_by_swarm": cost_by_swarm,
            "avg_cost_per_execution": sum(r.total_cost for r in self.execution_history)
            / len(self.execution_history),
            "highest_cost_execution": max(r.total_cost for r in self.execution_history),
            "cost_trend": (
                "increasing"
                if len(self.execution_history) > 1
                and self.execution_history[-1].total_cost > self.execution_history[-2].total_cost
                else "stable"
            ),
        }

    async def cleanup_inactive_swarms(self, inactive_threshold_hours: int = 24):
        """Clean up swarms that haven't been used recently"""

        cutoff_time = datetime.now() - timedelta(hours=inactive_threshold_hours)
        inactive_swarms = []

        for swarm_id in list(self.active_swarms.keys()):
            # Check if swarm has been used recently
            recent_executions = [
                r
                for r in self.execution_history
                if r.swarm_name == self.swarm_configs.get(swarm_id, {}).get("name", "")
                and r.executed_at >= cutoff_time
            ]

            if not recent_executions:
                inactive_swarms.append(swarm_id)

        # Remove inactive swarms (keep configurations)
        for swarm_id in inactive_swarms:
            if swarm_id in self.active_swarms:
                del self.active_swarms[swarm_id]
                logger.info(f"Cleaned up inactive swarm: {swarm_id}")

        return inactive_swarms


# Factory instance for global access
_comprehensive_factory = None


def get_comprehensive_factory() -> ComprehensiveSwarmFactory:
    """Get global comprehensive factory instance"""
    global _comprehensive_factory
    if _comprehensive_factory is None:
        _comprehensive_factory = ComprehensiveSwarmFactory()
    return _comprehensive_factory


# Convenience functions for quick swarm creation
async def create_business_intelligence_swarm() -> str:
    """Quick create Sophia business intelligence swarm"""
    factory = get_comprehensive_factory()
    return await factory.create_swarm(factory.swarm_configs["sophia_business_intel"])


async def create_tactical_recon_swarm() -> str:
    """Quick create Artemis tactical reconnaissance swarm"""
    factory = get_comprehensive_factory()
    return await factory.create_swarm(factory.swarm_configs["artemis_recon"])


async def create_strategic_planning_swarm() -> str:
    """Quick create Sophia strategic planning swarm"""
    factory = get_comprehensive_factory()
    return await factory.create_swarm(factory.swarm_configs["sophia_strategic"])


async def create_coding_strike_swarm() -> str:
    """Quick create Artemis coding strike force swarm"""
    factory = get_comprehensive_factory()
    return await factory.create_swarm(factory.swarm_configs["artemis_strike"])


async def execute_quick_analysis(
    task: str,
    swarm_type: str = "sophia_business_intel",
    priority: int = 1,
    requester: str = "system",
) -> SwarmExecutionResult:
    """Execute quick analysis with specified swarm type"""
    factory = get_comprehensive_factory()

    # Get or create swarm
    if swarm_type in factory.swarm_configs:
        swarm_id = await factory.create_swarm(factory.swarm_configs[swarm_type])
    else:
        raise ValueError(f"Unknown swarm type: {swarm_type}")

    # Execute
    context = ExecutionContext(task=task, priority=priority, requester=requester)

    return await factory.execute_swarm(swarm_id, context)
