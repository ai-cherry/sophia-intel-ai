"""
Core persona management framework for Sophia and .
This module provides the foundational classes and utilities for managing
AI personas, including trait evolution, task instantiation, and performance tracking.
"""
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4
# Configure logging
logger = logging.getLogger(__name__)
class PersonaType(Enum):
    """Enumeration of available persona types."""
    SOPHIA = "sophia"  # Business Intelligence
    CODE = "code"  # Code Excellence
    HYBRID = "hybrid"  # Combination of both
class TaskDomain(Enum):
    """Task domains for persona specialization."""
    BUSINESS_ANALYSIS = "business_analysis"
    DATA_VISUALIZATION = "data_visualization"
    STRATEGIC_PLANNING = "strategic_planning"
    CODE_REVIEW = "code_review"
    ARCHITECTURE_DESIGN = "architecture_design"
    DEBUGGING = "debugging"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    GENERAL = "general"
class EvolutionTrigger(Enum):
    """Triggers that can cause persona evolution."""
    PERFORMANCE_THRESHOLD = "performance_threshold"
    TASK_COMPLETION = "task_completion"
    ERROR_PATTERN = "error_pattern"
    FEEDBACK_SCORE = "feedback_score"
    TIME_BASED = "time_based"
@dataclass
class PersonaTrait:
    """Represents a single trait of a persona."""
    name: str
    value: float  # 0.0 to 1.0
    weight: float = 1.0  # Importance weight
    description: str = ""
    last_updated: datetime = field(default_factory=datetime.now)
    evolution_rate: float = 0.05  # How quickly this trait can change
    def evolve(self, delta: float) -> None:
        """Evolve the trait value based on performance feedback."""
        old_value = self.value
        # Apply bounded evolution
        self.value = max(0.0, min(1.0, self.value + (delta * self.evolution_rate)))
        self.last_updated = datetime.now()
        if abs(old_value - self.value) > 0.01:
            logger.debug(
                f"Trait '{self.name}' evolved from {old_value:.3f} to {self.value:.3f}"
            )
@dataclass
class KnowledgeArea:
    """Represents a knowledge domain for a persona."""
    domain: str
    expertise_level: float  # 0.0 to 1.0
    recent_performance: list[float] = field(default_factory=list)
    learning_rate: float = 0.1
    decay_rate: float = 0.02  # Knowledge decay over time
    last_accessed: datetime = field(default_factory=datetime.now)
    def update_performance(self, score: float) -> None:
        """Update performance history and adjust expertise level."""
        self.recent_performance.append(score)
        # Keep only recent performances (last 10)
        if len(self.recent_performance) > 10:
            self.recent_performance = self.recent_performance[-10:]
        # Adjust expertise based on recent performance
        avg_performance = sum(self.recent_performance) / len(self.recent_performance)
        if avg_performance > 0.8:  # Good performance
            self.expertise_level = min(1.0, self.expertise_level + self.learning_rate)
        elif avg_performance < 0.6:  # Poor performance
            self.expertise_level = max(0.0, self.expertise_level - self.learning_rate)
        self.last_accessed = datetime.now()
        logger.debug(
            f"Knowledge area '{self.domain}' updated: expertise={self.expertise_level:.3f}"
        )
@dataclass
class PerformanceMetrics:
    """Performance tracking for persona evaluation."""
    task_id: str
    domain: TaskDomain
    success_rate: float
    response_time: float
    quality_score: float
    user_satisfaction: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    feedback: str = ""
@dataclass
class Persona:
    """
    Core persona class representing an AI assistant personality.
    This class encapsulates all aspects of a persona including traits,
    knowledge areas, communication style, and evolution capabilities.
    """
    name: str
    persona_type: PersonaType
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    # Core characteristics
    traits: dict[str, PersonaTrait] = field(default_factory=dict)
    knowledge_areas: dict[str, KnowledgeArea] = field(default_factory=dict)
    communication_style: dict[str, Any] = field(default_factory=dict)
    # Evolution and performance
    performance_history: list[PerformanceMetrics] = field(default_factory=list)
    evolution_triggers: list[EvolutionTrigger] = field(default_factory=list)
    adaptation_rate: float = 0.1
    # Context and specialization
    preferred_domains: list[TaskDomain] = field(default_factory=list)
    system_prompt_template: str = ""
    context_window_size: int = 4000
    def add_trait(
        self,
        name: str,
        value: float,
        weight: float = 1.0,
        description: str = "",
        evolution_rate: float = 0.05,
    ) -> None:
        """Add or update a personality trait."""
        self.traits[name] = PersonaTrait(
            name=name,
            value=value,
            weight=weight,
            description=description,
            evolution_rate=evolution_rate,
        )
        self.last_updated = datetime.now()
        logger.debug(f"Added trait '{name}' with value {value}")
    def add_knowledge_area(
        self, domain: str, expertise_level: float = 0.5, learning_rate: float = 0.1
    ) -> None:
        """Add or update a knowledge area."""
        self.knowledge_areas[domain] = KnowledgeArea(
            domain=domain, expertise_level=expertise_level, learning_rate=learning_rate
        )
        self.last_updated = datetime.now()
        logger.debug(
            f"Added knowledge area '{domain}' with expertise {expertise_level}"
        )
    def update_performance(self, metrics: PerformanceMetrics) -> None:
        """Update persona performance and trigger evolution if needed."""
        self.performance_history.append(metrics)
        # Keep only recent history (last 100 entries)
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        # Update knowledge area performance
        domain_str = metrics.domain.value
        if domain_str in self.knowledge_areas:
            self.knowledge_areas[domain_str].update_performance(metrics.quality_score)
        # Check for evolution triggers
        self._check_evolution_triggers(metrics)
        self.last_updated = datetime.now()
    def _check_evolution_triggers(self, metrics: PerformanceMetrics) -> None:
        """Check if evolution should be triggered based on performance."""
        if EvolutionTrigger.PERFORMANCE_THRESHOLD in self.evolution_triggers:
            if metrics.quality_score < 0.6:  # Poor performance
                self._evolve_traits(-0.1)
            elif metrics.quality_score > 0.9:  # Excellent performance
                self._evolve_traits(0.05)
        if EvolutionTrigger.FEEDBACK_SCORE in self.evolution_triggers:
            if metrics.user_satisfaction is not None:
                if metrics.user_satisfaction < 0.6:
                    self._evolve_traits(-0.05)
                elif metrics.user_satisfaction > 0.8:
                    self._evolve_traits(0.03)
    def _evolve_traits(self, base_delta: float) -> None:
        """Evolve persona traits based on performance feedback."""
        for trait in self.traits.values():
            # Add some randomness to evolution
            import random
            delta = base_delta * (0.5 + random.random())
            trait.evolve(delta)
        logger.info(
            f"Persona '{self.name}' evolved traits with base delta {base_delta}"
        )
    def get_expertise_score(self, domain: TaskDomain) -> float:
        """Get expertise score for a specific domain."""
        domain_str = domain.value
        if domain_str in self.knowledge_areas:
            return self.knowledge_areas[domain_str].expertise_level
        return 0.0
    def generate_system_prompt(
        self, task_context: Optional[dict[str, Any]] = None
    ) -> str:
        """Generate a system prompt based on current persona state."""
        # This is a basic implementation - will be enhanced by prompt_templates.py
        prompt_parts = [
            f"You are {self.name}, an AI assistant with the following characteristics:",
            "",
            "## Personality Traits:",
        ]
        for trait_name, trait in self.traits.items():
            prompt_parts.append(
                f"- {trait_name}: {trait.value:.2f} ({trait.description})"
            )
        prompt_parts.extend(["", "## Knowledge Areas:"])
        for domain, knowledge in self.knowledge_areas.items():
            prompt_parts.append(
                f"- {domain}: {knowledge.expertise_level:.2f} expertise"
            )
        if task_context:
            prompt_parts.extend(
                ["", "## Current Task Context:", json.dumps(task_context, indent=2)]
            )
        return "\n".join(prompt_parts)
    def to_dict(self) -> dict[str, Any]:
        """Convert persona to dictionary for serialization."""
        return {
            "name": self.name,
            "persona_type": self.persona_type.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "traits": {name: asdict(trait) for name, trait in self.traits.items()},
            "knowledge_areas": {
                name: asdict(ka) for name, ka in self.knowledge_areas.items()
            },
            "communication_style": self.communication_style,
            "preferred_domains": [d.value for d in self.preferred_domains],
            "system_prompt_template": self.system_prompt_template,
            "context_window_size": self.context_window_size,
            "adaptation_rate": self.adaptation_rate,
            "evolution_triggers": [t.value for t in self.evolution_triggers],
        }
class PersonaManager:
    """
    Manages persona lifecycle, instantiation, and coordination.
    This class handles loading, saving, updating, and coordinating
    between different personas in the system.
    """
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize the persona manager."""
        self.storage_path = storage_path or Path("data/personas")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.personas: dict[str, Persona] = {}
        self.active_instances: dict[str, Persona] = {}  # Task-specific instances
        logger.info(
            f"PersonaManager initialized with storage path: {self.storage_path}"
        )
    async def load_persona(self, persona_name: str) -> Optional[Persona]:
        """Load a persona from storage."""
        try:
            persona_file = self.storage_path / f"{persona_name.lower()}.json"
            if not persona_file.exists():
                logger.warning(f"Persona file not found: {persona_file}")
                return None
            with open(persona_file) as f:
                data = json.load(f)
            persona = self._dict_to_persona(data)
            self.personas[persona_name] = persona
            logger.info(f"Loaded persona '{persona_name}' from {persona_file}")
            return persona
        except Exception as e:
            logger.error(f"Failed to load persona '{persona_name}': {e}")
            return None
    async def save_persona(self, persona: Persona) -> bool:
        """Save a persona to storage."""
        try:
            persona_file = self.storage_path / f"{persona.name.lower()}.json"
            with open(persona_file, "w") as f:
                json.dump(persona.to_dict(), f, indent=2, default=str)
            logger.info(f"Saved persona '{persona.name}' to {persona_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save persona '{persona.name}': {e}")
            return False
    async def create_persona_instance(
        self, persona_name: str, task_context: dict[str, Any]
    ) -> Optional[Persona]:
        """Create a task-specific instance of a persona."""
        try:
            base_persona = self.personas.get(persona_name)
            if not base_persona:
                base_persona = await self.load_persona(persona_name)
                if not base_persona:
                    logger.error(
                        f"Cannot create instance: persona '{persona_name}' not found"
                    )
                    return None
            # Create a copy for the specific task
            instance_id = str(uuid4())
            instance = self._deep_copy_persona(base_persona)
            # Customize instance for task context
            task_domain = task_context.get("domain")
            if task_domain and isinstance(task_domain, str):
                try:
                    domain_enum = TaskDomain(task_domain)
                    # Boost expertise in relevant domain
                    if domain_enum.value in instance.knowledge_areas:
                        instance.knowledge_areas[
                            domain_enum.value
                        ].expertise_level *= 1.1
                        instance.knowledge_areas[domain_enum.value].expertise_level = (
                            min(
                                1.0,
                                instance.knowledge_areas[
                                    domain_enum.value
                                ].expertise_level,
                            )
                        )
                except ValueError:
                    logger.warning(f"Unknown task domain: {task_domain}")
            self.active_instances[instance_id] = instance
            logger.info(
                f"Created persona instance '{instance_id}' for '{persona_name}'"
            )
            return instance
        except Exception as e:
            logger.error(f"Failed to create persona instance: {e}")
            return None
    async def update_instance_performance(
        self, instance_id: str, metrics: PerformanceMetrics
    ) -> bool:
        """Update performance metrics for a persona instance."""
        try:
            if instance_id not in self.active_instances:
                logger.warning(f"Instance '{instance_id}' not found")
                return False
            instance = self.active_instances[instance_id]
            instance.update_performance(metrics)
            # Propagate learning to base persona
            base_persona_name = instance.name
            if base_persona_name in self.personas:
                base_persona = self.personas[base_persona_name]
                base_persona.update_performance(metrics)
                await self.save_persona(base_persona)
            logger.debug(f"Updated performance for instance '{instance_id}'")
            return True
        except Exception as e:
            logger.error(f"Failed to update instance performance: {e}")
            return False
    async def cleanup_instance(self, instance_id: str) -> None:
        """Clean up a completed task instance."""
        if instance_id in self.active_instances:
            del self.active_instances[instance_id]
            logger.debug(f"Cleaned up instance '{instance_id}'")
    async def get_best_persona_for_task(
        self,
        task_domain: TaskDomain,
        additional_criteria: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        """Determine the best persona for a given task."""
        best_persona = None
        best_score = 0.0
        for persona_name, persona in self.personas.items():
            score = persona.get_expertise_score(task_domain)
            # Apply additional criteria
            if additional_criteria:
                complexity = additional_criteria.get("complexity", 0.5)
                if complexity > 0.8 and "technical_depth" in persona.traits:
                    score *= persona.traits["technical_depth"].value
                urgency = additional_criteria.get("urgency", 0.5)
                if urgency > 0.7 and "efficiency" in persona.traits:
                    score *= persona.traits["efficiency"].value
            if score > best_score:
                best_score = score
                best_persona = persona_name
        logger.info(
            f"Best persona for {task_domain.value}: '{best_persona}' (score: {best_score:.3f})"
        )
        return best_persona
    def _dict_to_persona(self, data: dict[str, Any]) -> Persona:
        """Convert dictionary to Persona object."""
        persona = Persona(
            name=data["name"],
            persona_type=PersonaType(data["persona_type"]),
            version=data["version"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            communication_style=data["communication_style"],
            system_prompt_template=data["system_prompt_template"],
            context_window_size=data["context_window_size"],
            adaptation_rate=data["adaptation_rate"],
        )
        # Reconstruct traits
        for name, trait_data in data["traits"].items():
            trait_data["last_updated"] = datetime.fromisoformat(
                trait_data["last_updated"]
            )
            persona.traits[name] = PersonaTrait(**trait_data)
        # Reconstruct knowledge areas
        for domain, ka_data in data["knowledge_areas"].items():
            ka_data["last_accessed"] = datetime.fromisoformat(ka_data["last_accessed"])
            persona.knowledge_areas[domain] = KnowledgeArea(**ka_data)
        # Reconstruct enums
        persona.preferred_domains = [TaskDomain(d) for d in data["preferred_domains"]]
        persona.evolution_triggers = [
            EvolutionTrigger(t) for t in data["evolution_triggers"]
        ]
        return persona
    def _deep_copy_persona(self, persona: Persona) -> Persona:
        """Create a deep copy of a persona for task instances."""
        import copy
        return copy.deepcopy(persona)
    async def get_persona_analytics(self, persona_name: str) -> dict[str, Any]:
        """Get analytics and insights for a persona."""
        persona = self.personas.get(persona_name)
        if not persona:
            return {}
        # Calculate performance metrics
        recent_performance = persona.performance_history[-20:]  # Last 20 tasks
        avg_quality = 0.0
        avg_response_time = 0.0
        domain_performance = {}
        if recent_performance:
            avg_quality = sum(p.quality_score for p in recent_performance) / len(
                recent_performance
            )
            avg_response_time = sum(p.response_time for p in recent_performance) / len(
                recent_performance
            )
            # Domain-specific performance
            for perf in recent_performance:
                domain = perf.domain.value
                if domain not in domain_performance:
                    domain_performance[domain] = []
                domain_performance[domain].append(perf.quality_score)
        # Calculate domain averages
        domain_averages = {
            domain: sum(scores) / len(scores)
            for domain, scores in domain_performance.items()
        }
        return {
            "persona_name": persona_name,
            "version": persona.version,
            "total_tasks": len(persona.performance_history),
            "recent_avg_quality": avg_quality,
            "recent_avg_response_time": avg_response_time,
            "domain_performance": domain_averages,
            "knowledge_areas": {
                domain: ka.expertise_level
                for domain, ka in persona.knowledge_areas.items()
            },
            "trait_values": {
                name: trait.value for name, trait in persona.traits.items()
            },
            "last_updated": persona.last_updated.isoformat(),
        }
# Global persona manager instance
_persona_manager = None
def get_persona_manager(storage_path: Optional[Path] = None) -> PersonaManager:
    """Get or create global persona manager instance"""
    global _persona_manager
    if _persona_manager is None:
        _persona_manager = PersonaManager(storage_path)
    return _persona_manager
