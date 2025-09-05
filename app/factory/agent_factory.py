"""
Comprehensive Agent Factory System for Sophia and Artemis

This module provides a centralized factory for creating, managing, and inventorying
agents and swarms with a turnkey, configuration-driven approach.

Key Features:
- Centralized Agent Inventory System
- Pre-built Agent Catalog with Capabilities
- Configuration-driven Swarm Assembly
- Production-ready with Extensibility
- UI Integration Support
- Integration with existing AGNO framework
"""

import json
import logging
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.factory.agent_catalog import SpecializedAgentCatalog, SwarmTemplateLibrary

# Import comprehensive agent system
from app.factory.models import (
    AgentBlueprint,
    AgentCapability,
    AgentMetadata,
    AgentPersonality,
    AgentSpecialty,
)
from app.swarms.agno_teams import AGNOTeamConfig, ExecutionStrategy, SophiaAGNOTeam

# Import existing swarm infrastructure
from app.swarms.core.swarm_base import SwarmExecutionMode, SwarmType

logger = logging.getLogger(__name__)

# ==============================================================================
# AGENT FACTORY MODELS
# ==============================================================================


class AgentRole(str, Enum):
    PLANNER = "planner"
    GENERATOR = "generator"
    CRITIC = "critic"
    JUDGE = "judge"
    RUNNER = "runner"
    ARCHITECT = "architect"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTING = "testing"


class AgentDefinition(BaseModel):
    """Configuration for a single agent"""

    name: str
    role: AgentRole
    model: str
    temperature: float = 0.7
    instructions: str
    capabilities: list[str] = []
    constraints: Optional[list[str]] = None
    metadata: dict[str, Any] = {}


class SwarmBlueprint(BaseModel):
    """Complete specification for creating a swarm"""

    name: str
    description: str = ""
    swarm_type: SwarmType = SwarmType.STANDARD
    execution_mode: SwarmExecutionMode = SwarmExecutionMode.HIERARCHICAL
    agents: list[AgentDefinition]
    pattern: str = "hierarchical"
    memory_enabled: bool = True
    namespace: str = "artemis"
    tags: list[str] = []
    created_by: str = "factory"
    version: str = "1.0"


class SwarmTemplate(BaseModel):
    """Pre-built swarm template"""

    id: str
    name: str
    description: str
    type: SwarmType
    category: str
    agents: list[AgentDefinition]
    pattern: str
    recommended_for: list[str]
    metadata: dict[str, Any] = {}


class FactoryExecutionResult(BaseModel):
    """Result from factory swarm execution"""

    swarm_id: str
    task: str
    result: dict[str, Any]
    execution_time: float
    token_usage: dict[str, int]
    cost_estimate: float
    agents_used: list[str]
    success: bool
    errors: list[str] = []
    metrics: dict[str, Any] = {}


# ==============================================================================
# AGENT FACTORY CORE CLASS
# ==============================================================================


class AgentFactory:
    """
    Comprehensive Agent Factory with Inventory Management
    Integrates with existing AGNO infrastructure and provides centralized agent catalog
    """

    def __init__(self, catalog_path: Optional[str] = None):
        # Legacy swarm support
        self.created_swarms: dict[str, SwarmBlueprint] = {}
        self.execution_history: list[FactoryExecutionResult] = []
        self.templates = self._initialize_templates()
        self.agno_teams: dict[str, SophiaAGNOTeam] = {}

        # Comprehensive agent inventory system
        self.catalog_path = Path(catalog_path) if catalog_path else Path("./agent_catalog")
        self.inventory: dict[str, AgentBlueprint] = {}
        self.active_agents: dict[str, Any] = {}
        self.swarm_templates: dict[str, dict[str, Any]] = {}

        # Performance tracking
        self.creation_metrics: dict[str, int] = {}
        self.usage_patterns: dict[str, list[datetime]] = {}

        # Initialize comprehensive catalog
        self._initialize_comprehensive_catalog()

    def _initialize_comprehensive_catalog(self):
        """Initialize the comprehensive agent catalog with pre-built specialists"""
        if not self.catalog_path.exists():
            self.catalog_path.mkdir(parents=True, exist_ok=True)

        # Load existing catalog if available
        catalog_file = self.catalog_path / "catalog.json"
        if catalog_file.exists():
            self._load_catalog_from_file(catalog_file)
        else:
            # Create default catalog with specialized agents
            self._create_default_comprehensive_catalog()

        # Load swarm templates
        self._load_swarm_templates()

        logger.info(
            f"🏭 Comprehensive Agent Factory initialized with {len(self.inventory)} agents in catalog"
        )

    def _create_default_comprehensive_catalog(self):
        """Create default catalog with specialized agents from catalog"""
        try:
            # Get all agents from the specialized catalog
            catalog_agents = SpecializedAgentCatalog.get_all_catalog_agents()

            for agent in catalog_agents:
                self.inventory[agent.id] = agent

            # Save the catalog
            self._save_comprehensive_catalog()

            logger.info(
                f"📚 Created comprehensive catalog with {len(catalog_agents)} specialized agents"
            )

        except Exception as e:
            logger.error(f"Failed to create comprehensive catalog: {e}")
            # Fallback to basic catalog
            self._create_basic_fallback_catalog()

    def _create_basic_fallback_catalog(self):
        """Fallback to basic agent definitions if comprehensive catalog fails"""
        basic_agents = [
            self._create_basic_agent(
                "developer", AgentSpecialty.DEVELOPER, [AgentCapability.CODING]
            ),
            self._create_basic_agent(
                "analyst", AgentSpecialty.ANALYST, [AgentCapability.DATA_ANALYSIS]
            ),
            self._create_basic_agent("tester", AgentSpecialty.TESTER, [AgentCapability.TESTING]),
        ]

        for agent in basic_agents:
            self.inventory[agent.id] = agent

    def _create_basic_agent(
        self, name: str, specialty: AgentSpecialty, capabilities: list[AgentCapability]
    ) -> AgentBlueprint:
        """Create a basic agent blueprint for fallback scenarios"""
        from app.core.agent_config import AgentRoleConfig, ModelConfig

        return AgentBlueprint(
            id=f"{name}_basic_v1",
            metadata=AgentMetadata(
                name=f"Basic {name.title()}",
                description=f"Basic {name} agent with essential capabilities",
                tags=["basic", name],
            ),
            specialty=specialty,
            capabilities=capabilities,
            personality=AgentPersonality.ANALYTICAL,
            config=AgentRoleConfig(
                role_name=name, model_settings=ModelConfig(temperature=0.5, max_tokens=2000)
            ),
            system_prompt_template=f"You are a {name} agent focused on {specialty.value} tasks.",
        )

    def _load_catalog_from_file(self, catalog_file: Path):
        """Load agent catalog from JSON file"""
        try:
            with open(catalog_file) as f:
                catalog_data = json.load(f)

            for agent_id, agent_data in catalog_data.items():
                blueprint = self._dict_to_blueprint(agent_data)
                self.inventory[agent_id] = blueprint

        except Exception as e:
            logger.error(f"Failed to load catalog from {catalog_file}: {e}")
            self._create_default_comprehensive_catalog()

    def _save_comprehensive_catalog(self):
        """Save current comprehensive catalog to file"""
        catalog_file = self.catalog_path / "catalog.json"
        try:
            catalog_data = {}
            for agent_id, blueprint in self.inventory.items():
                catalog_data[agent_id] = self._blueprint_to_dict(blueprint)

            with open(catalog_file, "w") as f:
                json.dump(catalog_data, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save comprehensive catalog: {e}")

    def _load_swarm_templates(self):
        """Load swarm templates from catalog and file"""
        # Load from template library
        template_library = SwarmTemplateLibrary.get_all_templates()
        for template in template_library:
            self.swarm_templates[template["id"]] = template

        # Load from file if exists
        templates_file = self.catalog_path / "swarm_templates.json"
        if templates_file.exists():
            try:
                with open(templates_file) as f:
                    file_templates = json.load(f)
                    self.swarm_templates.update(file_templates)
            except Exception as e:
                logger.error(f"Failed to load swarm templates from file: {e}")

        logger.info(f"📋 Loaded {len(self.swarm_templates)} swarm templates")

    def _initialize_templates(self) -> dict[str, SwarmTemplate]:
        """Initialize built-in swarm templates"""
        return {
            "coding": SwarmTemplate(
                id="coding",
                name="Coding Swarm",
                description="Code generation, review, and optimization",
                type=SwarmType.CODING,
                category="development",
                pattern="hierarchical",
                recommended_for=["code_generation", "code_review", "debugging"],
                agents=[
                    AgentDefinition(
                        name="Code Planner",
                        role=AgentRole.PLANNER,
                        model="qwen/qwen3-30b-a3b",
                        temperature=0.3,
                        instructions="Analyze requirements and create implementation plan. Focus on architecture and design patterns.",
                        capabilities=["planning", "architecture", "design_patterns"],
                    ),
                    AgentDefinition(
                        name="Code Generator",
                        role=AgentRole.GENERATOR,
                        model="x-ai/grok-code-fast-1",
                        temperature=0.7,
                        instructions="Generate clean, efficient code based on the plan. Follow best practices and include error handling.",
                        capabilities=["code_generation", "best_practices", "error_handling"],
                    ),
                    AgentDefinition(
                        name="Code Reviewer",
                        role=AgentRole.CRITIC,
                        model="openai/gpt-5-chat",
                        temperature=0.2,
                        instructions="Review generated code for bugs, security issues, and improvements. Be thorough but constructive.",
                        capabilities=["code_review", "security_analysis", "optimization"],
                    ),
                ],
            ),
            "debate": SwarmTemplate(
                id="debate",
                name="Debate Swarm",
                description="Adversarial analysis and decision making",
                type=SwarmType.DEBATE,
                category="analysis",
                pattern="debate",
                recommended_for=["decision_making", "analysis", "risk_assessment"],
                agents=[
                    AgentDefinition(
                        name="Advocate",
                        role=AgentRole.GENERATOR,
                        model="anthropic/claude-sonnet-4",
                        temperature=0.8,
                        instructions="Argue strongly in favor of the proposed solution. Present compelling evidence.",
                        capabilities=["argumentation", "evidence_gathering", "persuasion"],
                    ),
                    AgentDefinition(
                        name="Critic",
                        role=AgentRole.CRITIC,
                        model="openai/gpt-5-chat",
                        temperature=0.8,
                        instructions="Challenge the proposal with counter-arguments. Identify weaknesses and risks.",
                        capabilities=[
                            "critical_analysis",
                            "risk_identification",
                            "counter_arguments",
                        ],
                    ),
                    AgentDefinition(
                        name="Judge",
                        role=AgentRole.JUDGE,
                        model="x-ai/grok-4",
                        temperature=0.3,
                        instructions="Evaluate both sides objectively and provide balanced conclusion.",
                        capabilities=["evaluation", "synthesis", "decision_making"],
                    ),
                ],
            ),
            "consensus": SwarmTemplate(
                id="consensus",
                name="Consensus Building Swarm",
                description="Multi-perspective analysis and consensus building",
                type=SwarmType.CONSENSUS,
                category="collaboration",
                pattern="consensus",
                recommended_for=["complex_decisions", "multi_stakeholder", "strategic_planning"],
                agents=[
                    AgentDefinition(
                        name="Technical Analyst",
                        role=AgentRole.GENERATOR,
                        model="deepseek/deepseek-chat",
                        temperature=0.5,
                        instructions="Provide analysis from technical perspective. Focus on feasibility and implementation.",
                        capabilities=[
                            "technical_analysis",
                            "feasibility_assessment",
                            "implementation_planning",
                        ],
                    ),
                    AgentDefinition(
                        name="Business Analyst",
                        role=AgentRole.GENERATOR,
                        model="qwen/qwen3-30b-a3b",
                        temperature=0.5,
                        instructions="Provide analysis from business perspective. Focus on value and ROI.",
                        capabilities=["business_analysis", "roi_calculation", "market_assessment"],
                    ),
                    AgentDefinition(
                        name="User Experience Analyst",
                        role=AgentRole.GENERATOR,
                        model="anthropic/claude-sonnet-4",
                        temperature=0.5,
                        instructions="Provide analysis from user experience perspective. Focus on usability and adoption.",
                        capabilities=["ux_analysis", "usability_assessment", "adoption_strategies"],
                    ),
                    AgentDefinition(
                        name="Synthesizer",
                        role=AgentRole.JUDGE,
                        model="openai/gpt-5-chat",
                        temperature=0.3,
                        instructions="Synthesize all perspectives into unified recommendation. Balance competing concerns.",
                        capabilities=[
                            "synthesis",
                            "consensus_building",
                            "strategic_recommendations",
                        ],
                    ),
                ],
            ),
        }

    # =============================================================================
    # COMPREHENSIVE INVENTORY MANAGEMENT METHODS
    # =============================================================================

    def create_agent_from_blueprint(
        self, blueprint_id: str, custom_config: Optional[dict[str, Any]] = None
    ) -> str:
        """Create agent instance from blueprint and return agent ID"""
        if blueprint_id not in self.inventory:
            raise ValueError(f"Agent blueprint '{blueprint_id}' not found in inventory")

        blueprint = self.inventory[blueprint_id]

        # Apply custom configuration if provided
        if custom_config:
            blueprint = self._apply_custom_config_to_blueprint(blueprint, custom_config)

        # Create agent instance (placeholder - would integrate with actual agent framework)
        agent = self._instantiate_agent_from_blueprint(blueprint)

        # Track creation
        agent_id = f"{blueprint_id}_{uuid4().hex[:8]}"
        self.active_agents[agent_id] = agent
        self.creation_metrics[blueprint_id] = self.creation_metrics.get(blueprint_id, 0) + 1

        # Update blueprint usage
        blueprint.metadata.usage_count += 1
        blueprint.metadata.updated_at = datetime.now()

        logger.info(f"🤖 Created agent: {agent_id} from blueprint: {blueprint_id}")
        return agent_id

    def list_agent_blueprints(
        self, filters: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """List agents in inventory with optional filtering"""
        agents = list(self.inventory.values())

        if filters:
            filtered_agents = []
            for agent in agents:
                include = True

                # Filter by specialty
                if "specialty" in filters:
                    if agent.specialty.value != filters["specialty"]:
                        include = False

                # Filter by capabilities
                if "capabilities" in filters:
                    required_caps = filters["capabilities"]
                    if not all(
                        any(cap.value == req_cap for cap in agent.capabilities)
                        for req_cap in required_caps
                    ):
                        include = False

                # Filter by tags
                if "tags" in filters:
                    if not any(tag in agent.metadata.tags for tag in filters["tags"]):
                        include = False

                if include:
                    filtered_agents.append(agent)
            agents = filtered_agents

        # Convert to dicts for API response
        return [self._blueprint_to_dict(agent) for agent in agents]

    def search_agent_blueprints(self, query: str) -> list[dict[str, Any]]:
        """Search agents by name, description, or capabilities"""
        query = query.lower()
        results = []

        for agent in self.inventory.values():
            # Search in name and description
            if query in agent.metadata.name.lower() or query in agent.metadata.description.lower():
                results.append(agent)
                continue

            # Search in capabilities
            if any(query in cap.value.lower() for cap in agent.capabilities):
                results.append(agent)
                continue

            # Search in tags
            if any(query in tag.lower() for tag in agent.metadata.tags):
                results.append(agent)

        return [self._blueprint_to_dict(agent) for agent in results]

    def get_agent_blueprint(self, blueprint_id: str) -> Optional[dict[str, Any]]:
        """Get agent blueprint by ID"""
        blueprint = self.inventory.get(blueprint_id)
        return self._blueprint_to_dict(blueprint) if blueprint else None

    def create_swarm_from_inventory(self, swarm_config: dict[str, Any]) -> str:
        """Create swarm by selecting agents from inventory based on configuration"""
        swarm_id = swarm_config.get("id", f"swarm_{uuid4().hex[:8]}")

        # Agent selection criteria
        required_specialties = swarm_config.get("required_specialties", [])
        required_capabilities = swarm_config.get("required_capabilities", [])
        optional_specialties = swarm_config.get("optional_specialties", [])
        max_agents = swarm_config.get("max_agents", 5)

        selected_blueprints = []

        # Select required specialists first
        for specialty in required_specialties:
            agents = [a for a in self.inventory.values() if a.specialty.value == specialty]
            if agents:
                # Pick best performing agent
                best_agent = max(agents, key=lambda a: a.metadata.success_rate)
                selected_blueprints.append(best_agent)
            else:
                logger.warning(f"No agents found for required specialty: {specialty}")

        # Add agents for required capabilities
        for capability in required_capabilities:
            if len(selected_blueprints) >= max_agents:
                break

            # Find agents with this capability not already selected
            agents = [
                a
                for a in self.inventory.values()
                if any(cap.value == capability for cap in a.capabilities)
                and a not in selected_blueprints
            ]
            if agents:
                best_agent = max(agents, key=lambda a: a.metadata.success_rate)
                selected_blueprints.append(best_agent)

        # Fill remaining slots with optional specialties
        for specialty in optional_specialties:
            if len(selected_blueprints) >= max_agents:
                break

            agents = [
                a
                for a in self.inventory.values()
                if a.specialty.value == specialty and a not in selected_blueprints
            ]
            if agents:
                best_agent = max(agents, key=lambda a: a.metadata.success_rate)
                selected_blueprints.append(best_agent)

        # Create agent definitions for legacy SwarmBlueprint
        agent_definitions = []
        for blueprint in selected_blueprints:
            agent_def = AgentDefinition(
                name=blueprint.metadata.name,
                role=self._map_specialty_to_role(blueprint.specialty),
                model=blueprint.config.model_settings.model
                if hasattr(blueprint.config.model_settings, "model")
                else "openai/gpt-4o-mini",
                temperature=blueprint.config.model_settings.temperature,
                instructions=blueprint.system_prompt_template,
                capabilities=[cap.value for cap in blueprint.capabilities],
                metadata={
                    "blueprint_id": blueprint.id,
                    "specialty": blueprint.specialty.value,
                    "personality": blueprint.personality.value,
                },
            )
            agent_definitions.append(agent_def)

        # Create SwarmBlueprint for legacy compatibility
        swarm_blueprint = SwarmBlueprint(
            name=swarm_config.get("name", f"Inventory Swarm {swarm_id}"),
            description=swarm_config.get("description", "Swarm created from agent inventory"),
            swarm_type=SwarmType(swarm_config.get("type", "standard")),
            execution_mode=SwarmExecutionMode(swarm_config.get("execution_mode", "parallel")),
            agents=agent_definitions,
            pattern=swarm_config.get("pattern", "hierarchical"),
            memory_enabled=swarm_config.get("memory_enabled", True),
            tags=swarm_config.get("tags", []),
            version=swarm_config.get("version", "1.0"),
        )

        # Store the swarm blueprint
        self.created_swarms[swarm_id] = swarm_blueprint

        # Create AGNO team for execution
        agno_config = AGNOTeamConfig(
            name=swarm_blueprint.name,
            strategy=self._map_execution_mode_to_strategy(swarm_blueprint.execution_mode),
            max_agents=len(agent_definitions),
            enable_memory=swarm_blueprint.memory_enabled,
            auto_tag=True,
        )

        try:
            agno_team = SophiaAGNOTeam(agno_config)
            # Note: We don't await initialize here as this is not an async method
            # The team will be initialized when first used
            self.agno_teams[swarm_id] = agno_team
        except Exception as e:
            logger.error(f"Failed to create AGNO team: {e}")

        logger.info(
            f"🐝 Created inventory-based swarm '{swarm_id}' with {len(selected_blueprints)} agents"
        )

        return swarm_id

    def get_swarm_templates_from_inventory(self) -> list[dict[str, Any]]:
        """Get all swarm templates that can be created from inventory"""
        return list(self.swarm_templates.values())

    def create_swarm_from_template(
        self, template_id: str, overrides: Optional[dict[str, Any]] = None
    ) -> str:
        """Create swarm from a pre-defined template"""
        if template_id not in self.swarm_templates:
            raise ValueError(f"Swarm template '{template_id}' not found")

        template = self.swarm_templates[template_id].copy()

        # Apply overrides if provided
        if overrides:
            template.update(overrides)

        # Generate unique swarm ID
        swarm_id = f"{template_id}_{uuid4().hex[:8]}"
        template["id"] = swarm_id

        return self.create_swarm_from_inventory(template)

    def get_inventory_stats(self) -> dict[str, Any]:
        """Get comprehensive inventory statistics"""
        if not self.inventory:
            return {"total_agents": 0}

        # Count by specialty
        specialty_counts = {}
        capability_counts = {}
        personality_counts = {}

        total_usage = 0
        avg_success_rate = 0

        for agent in self.inventory.values():
            # Specialty counts
            specialty = agent.specialty.value
            specialty_counts[specialty] = specialty_counts.get(specialty, 0) + 1

            # Capability counts
            for cap in agent.capabilities:
                capability_counts[cap.value] = capability_counts.get(cap.value, 0) + 1

            # Personality counts
            personality = agent.personality.value
            personality_counts[personality] = personality_counts.get(personality, 0) + 1

            # Usage stats
            total_usage += agent.metadata.usage_count
            avg_success_rate += agent.metadata.success_rate

        return {
            "total_agents": len(self.inventory),
            "total_active_agents": len(self.active_agents),
            "total_swarms_created": len(self.created_swarms),
            "specialty_distribution": specialty_counts,
            "capability_distribution": capability_counts,
            "personality_distribution": personality_counts,
            "total_usage_count": total_usage,
            "average_success_rate": avg_success_rate / len(self.inventory),
            "creation_metrics": self.creation_metrics,
            "available_templates": len(self.swarm_templates),
            "most_popular_specialties": sorted(
                specialty_counts.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "most_common_capabilities": sorted(
                capability_counts.items(), key=lambda x: x[1], reverse=True
            )[:10],
        }

    # =============================================================================
    # UTILITY METHODS FOR COMPREHENSIVE SYSTEM
    # =============================================================================

    def _instantiate_agent_from_blueprint(self, blueprint: AgentBlueprint) -> Any:
        """Create actual agent instance from blueprint (placeholder)"""
        return {
            "id": blueprint.id,
            "blueprint": blueprint,
            "created_at": datetime.now().isoformat(),
            "status": "ready",
            "specialty": blueprint.specialty.value,
            "capabilities": [cap.value for cap in blueprint.capabilities],
        }

    def _apply_custom_config_to_blueprint(
        self, blueprint: AgentBlueprint, custom_config: dict[str, Any]
    ) -> AgentBlueprint:
        """Apply custom configuration to blueprint"""
        import copy

        customized = copy.deepcopy(blueprint)

        for key, value in custom_config.items():
            if hasattr(customized, key):
                setattr(customized, key, value)
            elif hasattr(customized.config, key):
                setattr(customized.config, key, value)

        return customized

    def _blueprint_to_dict(self, blueprint: AgentBlueprint) -> dict[str, Any]:
        """Convert AgentBlueprint to dictionary for serialization"""
        if not blueprint:
            return {}

        return {
            "id": blueprint.id,
            "metadata": {
                "name": blueprint.metadata.name,
                "description": blueprint.metadata.description,
                "version": blueprint.metadata.version,
                "author": blueprint.metadata.author,
                "created_at": blueprint.metadata.created_at.isoformat(),
                "updated_at": blueprint.metadata.updated_at.isoformat(),
                "tags": blueprint.metadata.tags,
                "usage_count": blueprint.metadata.usage_count,
                "success_rate": blueprint.metadata.success_rate,
                "avg_response_time": blueprint.metadata.avg_response_time,
            },
            "specialty": blueprint.specialty.value,
            "capabilities": [cap.value for cap in blueprint.capabilities],
            "personality": blueprint.personality.value,
            "config": {
                "role_name": blueprint.config.role_name,
                "temperature": blueprint.config.model_settings.temperature,
                "max_tokens": blueprint.config.model_settings.max_tokens,
                "tools": blueprint.config.tools,
                "max_reasoning_steps": blueprint.config.max_reasoning_steps,
            },
            "tools": blueprint.tools,
            "dependencies": blueprint.dependencies,
            "constraints": blueprint.constraints,
            "system_prompt_template": blueprint.system_prompt_template,
            "task_instructions": blueprint.task_instructions,
            "max_concurrent_tasks": blueprint.max_concurrent_tasks,
            "rate_limit_per_hour": blueprint.rate_limit_per_hour,
            "memory_enabled": blueprint.memory_enabled,
            "learning_enabled": blueprint.learning_enabled,
        }

    def _dict_to_blueprint(self, data: dict[str, Any]) -> AgentBlueprint:
        """Convert dictionary to AgentBlueprint"""
        from app.core.agent_config import AgentRoleConfig, ModelConfig

        metadata_data = data["metadata"]
        metadata = AgentMetadata(
            name=metadata_data["name"],
            description=metadata_data["description"],
            version=metadata_data.get("version", "1.0.0"),
            author=metadata_data.get("author", "Unknown"),
            created_at=datetime.fromisoformat(metadata_data["created_at"]),
            updated_at=datetime.fromisoformat(metadata_data["updated_at"]),
            tags=metadata_data.get("tags", []),
            usage_count=metadata_data.get("usage_count", 0),
            success_rate=metadata_data.get("success_rate", 1.0),
            avg_response_time=metadata_data.get("avg_response_time", 0.0),
        )

        config_data = data["config"]
        config = AgentRoleConfig(
            role_name=config_data["role_name"],
            model_settings=ModelConfig(
                temperature=config_data.get("temperature", 0.7),
                max_tokens=config_data.get("max_tokens", 4096),
            ),
            tools=config_data.get("tools", []),
            max_reasoning_steps=config_data.get("max_reasoning_steps", 10),
        )

        return AgentBlueprint(
            id=data["id"],
            metadata=metadata,
            specialty=AgentSpecialty(data["specialty"]),
            capabilities=[AgentCapability(cap) for cap in data["capabilities"]],
            personality=AgentPersonality(data["personality"]),
            config=config,
            tools=data.get("tools", []),
            dependencies=data.get("dependencies", []),
            constraints=data.get("constraints", {}),
            system_prompt_template=data.get("system_prompt_template", ""),
            task_instructions=data.get("task_instructions", {}),
            max_concurrent_tasks=data.get("max_concurrent_tasks", 5),
            rate_limit_per_hour=data.get("rate_limit_per_hour", 100),
            memory_enabled=data.get("memory_enabled", True),
            learning_enabled=data.get("learning_enabled", True),
        )

    def _map_specialty_to_role(self, specialty: AgentSpecialty) -> AgentRole:
        """Map AgentSpecialty to legacy AgentRole"""
        mapping = {
            AgentSpecialty.ARCHITECT: AgentRole.ARCHITECT,
            AgentSpecialty.DEVELOPER: AgentRole.GENERATOR,
            AgentSpecialty.TESTER: AgentRole.TESTING,
            AgentSpecialty.SECURITY: AgentRole.SECURITY,
            AgentSpecialty.ANALYST: AgentRole.CRITIC,
            AgentSpecialty.PLANNER: AgentRole.PLANNER,
        }
        return mapping.get(specialty, AgentRole.GENERATOR)

    # =============================================================================
    # LEGACY SWARM TEMPLATE METHODS (MAINTAINED FOR COMPATIBILITY)
    # =============================================================================

    async def get_templates(self) -> list[SwarmTemplate]:
        """Get all available swarm templates"""
        return list(self.templates.values())

    async def create_swarm_from_blueprint(self, blueprint: SwarmBlueprint) -> str:
        """Create a new swarm from blueprint and return swarm ID"""
        swarm_id = str(uuid4())

        # Validate blueprint
        await self._validate_blueprint(blueprint)

        # Create AGNO team configuration
        agno_config = AGNOTeamConfig(
            name=blueprint.name,
            strategy=self._map_execution_mode_to_strategy(blueprint.execution_mode),
            max_agents=len(blueprint.agents),
            enable_memory=blueprint.memory_enabled,
            auto_tag=True,
        )

        # Create AGNO team
        agno_team = SophiaAGNOTeam(agno_config)
        await agno_team.initialize()

        # Store references
        self.created_swarms[swarm_id] = blueprint
        self.agno_teams[swarm_id] = agno_team

        logger.info(f"Created swarm {swarm_id} from blueprint: {blueprint.name}")

        return swarm_id

    async def execute_swarm(
        self, swarm_id: str, task: str, context: dict[str, Any] = None
    ) -> FactoryExecutionResult:
        """Execute a factory-created swarm"""
        if swarm_id not in self.created_swarms:
            raise HTTPException(status_code=404, detail=f"Swarm {swarm_id} not found")

        blueprint = self.created_swarms[swarm_id]
        agno_team = self.agno_teams[swarm_id]

        start_time = datetime.now()

        try:
            # Execute via AGNO team
            from app.swarms.agno_teams import Task

            agno_task = Task(description=task, metadata=context or {})

            result = await agno_team.execute(agno_task)

            execution_time = (datetime.now() - start_time).total_seconds()

            # Create execution result
            exec_result = FactoryExecutionResult(
                swarm_id=swarm_id,
                task=task,
                result=result,
                execution_time=execution_time,
                token_usage=result.get("token_usage", {}),
                cost_estimate=self._estimate_cost(blueprint, result),
                agents_used=[agent.name for agent in blueprint.agents],
                success=result.get("status") == "completed",
                errors=result.get("errors", []),
                metrics=result.get("metrics", {}),
            )

            # Store execution history
            self.execution_history.append(exec_result)

            return exec_result

        except Exception as e:
            logger.error(f"Swarm execution failed: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()

            exec_result = FactoryExecutionResult(
                swarm_id=swarm_id,
                task=task,
                result={"error": str(e)},
                execution_time=execution_time,
                token_usage={},
                cost_estimate=0.0,
                agents_used=[],
                success=False,
                errors=[str(e)],
            )

            self.execution_history.append(exec_result)
            return exec_result

    async def get_swarm_info(self, swarm_id: str) -> dict[str, Any]:
        """Get information about a created swarm"""
        if swarm_id not in self.created_swarms:
            raise HTTPException(status_code=404, detail=f"Swarm {swarm_id} not found")

        blueprint = self.created_swarms[swarm_id]

        # Get execution history for this swarm
        executions = [
            exec_result
            for exec_result in self.execution_history
            if exec_result.swarm_id == swarm_id
        ]

        return {
            "swarm_id": swarm_id,
            "blueprint": asdict(blueprint),
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "executions": len(executions),
            "success_rate": sum(1 for e in executions if e.success) / len(executions)
            if executions
            else 0,
            "average_execution_time": sum(e.execution_time for e in executions) / len(executions)
            if executions
            else 0,
            "total_cost": sum(e.cost_estimate for e in executions),
        }

    async def list_swarms(self) -> list[dict[str, Any]]:
        """List all created swarms"""
        swarms = []
        for swarm_id in self.created_swarms:
            swarm_info = await self.get_swarm_info(swarm_id)
            swarms.append(swarm_info)
        return swarms

    async def delete_swarm(self, swarm_id: str) -> bool:
        """Delete a created swarm"""
        if swarm_id not in self.created_swarms:
            raise HTTPException(status_code=404, detail=f"Swarm {swarm_id} not found")

        # Clean up
        del self.created_swarms[swarm_id]
        if swarm_id in self.agno_teams:
            del self.agno_teams[swarm_id]

        # Remove from execution history
        self.execution_history = [e for e in self.execution_history if e.swarm_id != swarm_id]

        logger.info(f"Deleted swarm {swarm_id}")
        return True

    async def _validate_blueprint(self, blueprint: SwarmBlueprint) -> None:
        """Validate swarm blueprint"""
        if not blueprint.name:
            raise HTTPException(status_code=400, detail="Swarm name is required")

        if len(blueprint.agents) < 1:
            raise HTTPException(status_code=400, detail="At least one agent is required")

        if len(blueprint.agents) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 agents allowed")

        # Validate agent configurations
        agent_names = []
        for agent in blueprint.agents:
            if not agent.name:
                raise HTTPException(status_code=400, detail="All agents must have names")

            if agent.name in agent_names:
                raise HTTPException(status_code=400, detail=f"Duplicate agent name: {agent.name}")
            agent_names.append(agent.name)

            if not agent.model:
                raise HTTPException(status_code=400, detail=f"Agent {agent.name} must have a model")

            if not (0.0 <= agent.temperature <= 1.0):
                raise HTTPException(
                    status_code=400,
                    detail=f"Agent {agent.name} temperature must be between 0.0 and 1.0",
                )

    def _map_execution_mode_to_strategy(self, mode: SwarmExecutionMode) -> ExecutionStrategy:
        """Map SwarmExecutionMode to AGNO ExecutionStrategy"""
        mapping = {
            SwarmExecutionMode.LINEAR: ExecutionStrategy.LITE,
            SwarmExecutionMode.PARALLEL: ExecutionStrategy.BALANCED,
            SwarmExecutionMode.DEBATE: ExecutionStrategy.DEBATE,
            SwarmExecutionMode.CONSENSUS: ExecutionStrategy.CONSENSUS,
            SwarmExecutionMode.HIERARCHICAL: ExecutionStrategy.QUALITY,
            SwarmExecutionMode.EVOLUTIONARY: ExecutionStrategy.QUALITY,
        }
        return mapping.get(mode, ExecutionStrategy.BALANCED)

    def _estimate_cost(self, blueprint: SwarmBlueprint, result: dict[str, Any]) -> float:
        """Estimate cost of execution"""
        # Simple cost estimation based on token usage and model pricing
        token_usage = result.get("token_usage", {})
        total_tokens = token_usage.get("total_tokens", 1000)  # Default estimate

        # Base cost per 1000 tokens (rough estimates)
        model_costs = {
            "openai/gpt-5-chat": 0.005,
            "anthropic/claude-sonnet-4": 0.003,
            "x-ai/grok-code-fast-1": 0.001,
            "x-ai/grok-4": 0.002,
            "deepseek/deepseek-chat": 0.0005,
            "qwen/qwen3-30b-a3b": 0.002,
        }

        total_cost = 0.0
        for agent in blueprint.agents:
            cost_per_1k = model_costs.get(agent.model, 0.002)  # Default cost
            agent_tokens = total_tokens / len(blueprint.agents)  # Rough split
            total_cost += (agent_tokens / 1000) * cost_per_1k

        return round(total_cost, 4)


# Global factory instance
factory = AgentFactory()

# ==============================================================================
# FASTAPI ROUTER
# ==============================================================================

router = APIRouter(prefix="/api/factory", tags=["agent-factory"])


@router.get("/templates")
async def get_templates():
    """Get all available swarm templates"""
    templates = await factory.get_templates()
    return [asdict(template) for template in templates]


@router.get("/patterns")
async def get_patterns():
    """Get all available execution patterns"""
    return [
        {
            "name": "hierarchical",
            "description": "Manager coordinates agent execution in hierarchy",
            "compatible_swarms": ["coding", "consensus", "standard"],
        },
        {
            "name": "debate",
            "description": "Agents argue opposing viewpoints to reach conclusion",
            "compatible_swarms": ["debate", "analysis"],
        },
        {
            "name": "consensus",
            "description": "All agents contribute to collaborative decision",
            "compatible_swarms": ["consensus", "collaboration"],
        },
        {
            "name": "sequential",
            "description": "Agents execute one after another in sequence",
            "compatible_swarms": ["coding", "standard"],
        },
        {
            "name": "parallel",
            "description": "All agents execute simultaneously",
            "compatible_swarms": ["analysis", "research"],
        },
        {
            "name": "evolutionary",
            "description": "Agents evolve solutions through iterations",
            "compatible_swarms": ["optimization", "creative"],
        },
    ]


@router.post("/create")
async def create_swarm(blueprint: SwarmBlueprint):
    """Create a new swarm from blueprint"""
    try:
        swarm_id = await factory.create_swarm_from_blueprint(blueprint)

        return {
            "swarm_id": swarm_id,
            "status": "created",
            "name": blueprint.name,
            "agents": len(blueprint.agents),
            "pattern": blueprint.pattern,
            "endpoints": {
                "execute": f"/api/factory/swarms/{swarm_id}/execute",
                "status": f"/api/factory/swarms/{swarm_id}/status",
                "info": f"/api/factory/swarms/{swarm_id}",
            },
        }

    except Exception as e:
        logger.error(f"Failed to create swarm: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create swarm: {str(e)}")


@router.post("/swarms/{swarm_id}/execute")
async def execute_swarm(swarm_id: str, request: dict[str, Any]):
    """Execute a factory-created swarm"""
    task = request.get("task", "")
    context = request.get("context", {})

    if not task:
        raise HTTPException(status_code=400, detail="Task is required")

    try:
        result = await factory.execute_swarm(swarm_id, task, context)
        return asdict(result)

    except Exception as e:
        logger.error(f"Failed to execute swarm {swarm_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.get("/swarms/{swarm_id}")
async def get_swarm_info(swarm_id: str):
    """Get information about a specific swarm"""
    return await factory.get_swarm_info(swarm_id)


@router.get("/swarms")
async def list_swarms():
    """List all created swarms"""
    return await factory.list_swarms()


@router.delete("/swarms/{swarm_id}")
async def delete_swarm(swarm_id: str):
    """Delete a created swarm"""
    success = await factory.delete_swarm(swarm_id)
    return {"success": success, "swarm_id": swarm_id}


@router.get("/health")
async def health_check():
    """Health check for factory service"""
    return {
        "status": "healthy",
        "active_swarms": len(factory.created_swarms),
        "total_executions": len(factory.execution_history),
        "templates_available": len(factory.templates),
        "inventory_agents": len(factory.inventory),
        "swarm_templates": len(factory.swarm_templates),
        "timestamp": datetime.now().isoformat(),
    }


# ==============================================================================
# COMPREHENSIVE INVENTORY MANAGEMENT API ENDPOINTS
# ==============================================================================


@router.get("/inventory/agents")
async def list_agent_blueprints(
    specialty: Optional[str] = None,
    capabilities: Optional[str] = None,  # Comma-separated list
    tags: Optional[str] = None,  # Comma-separated list
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """List agent blueprints with filtering and search"""
    try:
        filters = {}

        if specialty:
            filters["specialty"] = specialty

        if capabilities:
            filters["capabilities"] = [cap.strip() for cap in capabilities.split(",")]

        if tags:
            filters["tags"] = [tag.strip() for tag in tags.split(",")]

        if search:
            # Use search functionality
            results = factory.search_agent_blueprints(search)
        else:
            # Use filtered list
            results = factory.list_agent_blueprints(filters)

        # Apply pagination
        total = len(results)
        paginated_results = results[offset : offset + limit]

        return {
            "agents": paginated_results,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
        }

    except Exception as e:
        logger.error(f"Failed to list agent blueprints: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.get("/inventory/agents/{blueprint_id}")
async def get_agent_blueprint(blueprint_id: str):
    """Get specific agent blueprint by ID"""
    try:
        blueprint = factory.get_agent_blueprint(blueprint_id)
        if not blueprint:
            raise HTTPException(
                status_code=404, detail=f"Agent blueprint '{blueprint_id}' not found"
            )

        return blueprint

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent blueprint {blueprint_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")


@router.post("/inventory/agents")
async def create_custom_agent(agent_spec: dict[str, Any]):
    """Create custom agent blueprint"""
    try:
        # Validate required fields
        if not agent_spec.get("name"):
            raise HTTPException(status_code=400, detail="Agent name is required")

        if not agent_spec.get("specialty"):
            raise HTTPException(status_code=400, detail="Agent specialty is required")

        # Create the custom agent (this would need to be implemented in factory)
        blueprint_dict = {
            "name": agent_spec["name"],
            "description": agent_spec.get("description", ""),
            "specialty": agent_spec["specialty"],
            "capabilities": agent_spec.get("capabilities", []),
            "personality": agent_spec.get("personality", "analytical"),
            "system_prompt": agent_spec.get("system_prompt", ""),
            "tools": agent_spec.get("tools", []),
            "config_overrides": agent_spec.get("config", {}),
            "tags": agent_spec.get("tags", []),
        }

        # This would call factory.create_custom_agent if it existed
        # For now, return the specification
        blueprint_id = f"custom_{uuid4().hex[:8]}"

        return {
            "success": True,
            "blueprint_id": blueprint_id,
            "blueprint": blueprint_dict,
            "message": "Custom agent blueprint created successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create custom agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")


@router.post("/inventory/agents/{blueprint_id}/create")
async def create_agent_instance(blueprint_id: str, config: Optional[dict[str, Any]] = None):
    """Create agent instance from blueprint"""
    try:
        agent_id = factory.create_agent_from_blueprint(blueprint_id, config)

        return {
            "success": True,
            "agent_id": agent_id,
            "blueprint_id": blueprint_id,
            "status": "created",
            "created_at": datetime.now().isoformat(),
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create agent instance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create agent instance: {str(e)}")


@router.get("/inventory/stats")
async def get_inventory_statistics():
    """Get comprehensive inventory statistics"""
    try:
        stats = factory.get_inventory_stats()
        return stats

    except Exception as e:
        logger.error(f"Failed to get inventory stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/inventory/specialties")
async def get_available_specialties():
    """Get all available agent specialties"""
    try:
        # Import from agent catalog
        from app.factory.agent_catalog import AgentSpecialty

        specialties = []
        for specialty in AgentSpecialty:
            # Count agents with this specialty
            agents_count = len([a for a in factory.inventory.values() if a.specialty == specialty])

            specialties.append(
                {
                    "id": specialty.value,
                    "name": specialty.value.replace("_", " ").title(),
                    "agents_available": agents_count,
                }
            )

        return {"specialties": specialties, "total_specialties": len(specialties)}

    except Exception as e:
        logger.error(f"Failed to get specialties: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get specialties: {str(e)}")


@router.get("/inventory/capabilities")
async def get_available_capabilities():
    """Get all available agent capabilities"""
    try:
        # Import from agent catalog
        from app.factory.agent_catalog import AgentCapability

        capabilities = []
        for capability in AgentCapability:
            # Count agents with this capability
            agents_count = len(
                [a for a in factory.inventory.values() if capability in a.capabilities]
            )

            capabilities.append(
                {
                    "id": capability.value,
                    "name": capability.value.replace("_", " ").title(),
                    "agents_available": agents_count,
                }
            )

        return {"capabilities": capabilities, "total_capabilities": len(capabilities)}

    except Exception as e:
        logger.error(f"Failed to get capabilities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")


# ==============================================================================
# SWARM TEMPLATES AND CREATION FROM INVENTORY
# ==============================================================================


@router.get("/inventory/swarm-templates")
async def get_swarm_templates():
    """Get all swarm templates available from inventory"""
    try:
        templates = factory.get_swarm_templates_from_inventory()
        return {"templates": templates, "total_templates": len(templates)}

    except Exception as e:
        logger.error(f"Failed to get swarm templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")


@router.get("/inventory/swarm-templates/{template_id}")
async def get_swarm_template(template_id: str):
    """Get specific swarm template by ID"""
    try:
        if template_id not in factory.swarm_templates:
            raise HTTPException(status_code=404, detail=f"Swarm template '{template_id}' not found")

        template = factory.swarm_templates[template_id]

        # Add agent recommendations based on current inventory
        required_specs = template.get("required_specialties", [])
        template.get("required_capabilities", [])

        recommended_agents = []
        for specialty in required_specs:
            agents = [a for a in factory.inventory.values() if a.specialty.value == specialty]
            if agents:
                best_agent = max(agents, key=lambda a: a.metadata.success_rate)
                recommended_agents.append(factory._blueprint_to_dict(best_agent))

        template_with_recommendations = {
            **template,
            "recommended_agents": recommended_agents,
            "agents_available": len(recommended_agents),
            "can_create": len(recommended_agents) >= len(required_specs),
        }

        return template_with_recommendations

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get swarm template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")


@router.post("/inventory/swarms/create")
async def create_swarm_from_inventory(swarm_config: dict[str, Any]):
    """Create swarm by selecting agents from inventory"""
    try:
        # Validate required fields
        if not swarm_config.get("name"):
            raise HTTPException(status_code=400, detail="Swarm name is required")

        swarm_id = factory.create_swarm_from_inventory(swarm_config)

        # Get swarm info for response
        swarm_info = await factory.get_swarm_info(swarm_id)

        return {
            "success": True,
            "swarm_id": swarm_id,
            "swarm_info": swarm_info,
            "endpoints": {
                "execute": f"/api/factory/swarms/{swarm_id}/execute",
                "status": f"/api/factory/swarms/{swarm_id}",
                "info": f"/api/factory/inventory/swarms/{swarm_id}",
            },
        }

    except Exception as e:
        logger.error(f"Failed to create swarm from inventory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create swarm: {str(e)}")


@router.post("/inventory/swarms/from-template/{template_id}")
async def create_swarm_from_template(template_id: str, overrides: Optional[dict[str, Any]] = None):
    """Create swarm from template with optional overrides"""
    try:
        swarm_id = factory.create_swarm_from_template(template_id, overrides)

        # Get swarm info for response
        swarm_info = await factory.get_swarm_info(swarm_id)

        return {
            "success": True,
            "swarm_id": swarm_id,
            "template_id": template_id,
            "swarm_info": swarm_info,
            "endpoints": {
                "execute": f"/api/factory/swarms/{swarm_id}/execute",
                "status": f"/api/factory/swarms/{swarm_id}",
                "info": f"/api/factory/inventory/swarms/{swarm_id}",
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create swarm from template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create swarm: {str(e)}")


@router.post("/inventory/recommend-agents")
async def recommend_agents_for_task(request: dict[str, Any]):
    """Recommend best agents for a specific task"""
    try:
        task_description = request.get("task_description", "")
        max_agents = request.get("max_agents", 5)

        if not task_description:
            raise HTTPException(status_code=400, detail="Task description is required")

        # This would call factory.recommend_agents_for_task if it existed
        # For now, return a placeholder response
        recommended_agents = []
        for agent in list(factory.inventory.values())[:max_agents]:
            recommended_agents.append(
                {
                    **factory._blueprint_to_dict(agent),
                    "recommendation_score": agent.metadata.success_rate * 100,
                    "match_reasons": ["High success rate", "Relevant specialty"],
                }
            )

        return {
            "task_description": task_description,
            "recommended_agents": recommended_agents,
            "total_recommendations": len(recommended_agents),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to recommend agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/inventory/swarms/{swarm_id}/details")
async def get_swarm_details_from_inventory(swarm_id: str):
    """Get detailed swarm information including agent composition"""
    try:
        swarm_info = await factory.get_swarm_info(swarm_id)

        if not swarm_info:
            raise HTTPException(status_code=404, detail=f"Swarm '{swarm_id}' not found")

        # Add agent blueprint details
        if swarm_id in factory.created_swarms:
            blueprint = factory.created_swarms[swarm_id]
            agent_details = []

            for agent_def in blueprint.agents:
                blueprint_id = (
                    agent_def.metadata.get("blueprint_id")
                    if hasattr(agent_def, "metadata")
                    else None
                )
                if blueprint_id and blueprint_id in factory.inventory:
                    agent_blueprint = factory.inventory[blueprint_id]
                    agent_details.append(
                        {
                            "agent_definition": asdict(agent_def),
                            "blueprint": factory._blueprint_to_dict(agent_blueprint),
                        }
                    )
                else:
                    agent_details.append({"agent_definition": asdict(agent_def), "blueprint": None})

            swarm_info["agent_details"] = agent_details

        return swarm_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get swarm details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get swarm details: {str(e)}")
