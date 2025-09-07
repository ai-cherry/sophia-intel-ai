"""
Persona Management Framework
=============================

Dynamic persona system for AI agents with evolution capabilities,
trait management, and context-aware behavior adaptation.

AI Context:
- Sophia: Business intelligence and analysis persona
- Artemis: Code generation and technical implementation persona
- Supports persona evolution based on interaction history
- Enables cross-persona knowledge sharing
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PersonaTrait(Enum):
    """Core personality traits for AI personas"""

    # Communication style
    FORMAL = "formal"
    CONVERSATIONAL = "conversational"
    TECHNICAL = "technical"
    EDUCATIONAL = "educational"
    CONCISE = "concise"
    DETAILED = "detailed"

    # Approach style
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    SYSTEMATIC = "systematic"
    EXPLORATORY = "exploratory"
    PRAGMATIC = "pragmatic"
    THEORETICAL = "theoretical"

    # Interaction style
    PROACTIVE = "proactive"
    REACTIVE = "reactive"
    COLLABORATIVE = "collaborative"
    AUTONOMOUS = "autonomous"
    CAUTIOUS = "cautious"
    CONFIDENT = "confident"

    # Specialization
    DATA_FOCUSED = "data_focused"
    CODE_FOCUSED = "code_focused"
    BUSINESS_FOCUSED = "business_focused"
    USER_FOCUSED = "user_focused"
    SYSTEM_FOCUSED = "system_focused"


class PersonaCapability(Enum):
    """Capabilities that personas can have"""

    # Analysis capabilities
    DATA_ANALYSIS = "data_analysis"
    CODE_ANALYSIS = "code_analysis"
    BUSINESS_ANALYSIS = "business_analysis"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"

    # Generation capabilities
    CODE_GENERATION = "code_generation"
    REPORT_GENERATION = "report_generation"
    DOCUMENTATION_GENERATION = "documentation_generation"
    TEST_GENERATION = "test_generation"

    # Integration capabilities
    API_INTEGRATION = "api_integration"
    DATABASE_INTEGRATION = "database_integration"
    CLOUD_INTEGRATION = "cloud_integration"
    ML_MODEL_INTEGRATION = "ml_model_integration"

    # Specialized capabilities
    PROMPT_ENGINEERING = "prompt_engineering"
    SEMANTIC_SEARCH = "semantic_search"
    PATTERN_RECOGNITION = "pattern_recognition"
    ANOMALY_DETECTION = "anomaly_detection"


@dataclass
class PersonaContext:
    """Context for persona behavior"""

    domain: str  # Current domain (e.g., "finance", "engineering", "analytics")
    task_type: str  # Type of task being performed
    user_expertise: str  # User's expertise level
    interaction_history: list[dict[str, Any]] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)


@dataclass
class PersonaEvolution:
    """Tracks persona evolution over time"""

    timestamp: str
    trigger: str  # What triggered the evolution
    changes: dict[str, Any]  # What changed
    performance_before: float
    performance_after: float
    reason: str


@dataclass
class Persona:
    """AI Persona definition"""

    name: str
    description: str
    role: str
    traits: set[PersonaTrait] = field(default_factory=set)
    capabilities: set[PersonaCapability] = field(default_factory=set)
    knowledge_domains: list[str] = field(default_factory=list)
    prompt_template: str = ""
    system_message: str = ""
    temperature: float = 0.7
    max_tokens: int = 4000
    evolution_history: list[PersonaEvolution] = field(default_factory=list)
    performance_metrics: dict[str, float] = field(default_factory=dict)
    context_adaptations: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "role": self.role,
            "traits": [t.value for t in self.traits],
            "capabilities": [c.value for c in self.capabilities],
            "knowledge_domains": self.knowledge_domains,
            "prompt_template": self.prompt_template,
            "system_message": self.system_message,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "performance_metrics": self.performance_metrics,
        }

    def adapt_to_context(self, context: PersonaContext) -> "Persona":
        """Create context-adapted version of persona"""
        adapted = Persona(
            name=self.name,
            description=self.description,
            role=self.role,
            traits=self.traits.copy(),
            capabilities=self.capabilities.copy(),
            knowledge_domains=self.knowledge_domains.copy(),
            prompt_template=self.prompt_template,
            system_message=self.system_message,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        # Adapt based on domain
        if context.domain in self.context_adaptations:
            adaptations = self.context_adaptations[context.domain]

            # Adjust traits
            if "add_traits" in adaptations:
                for trait in adaptations["add_traits"]:
                    adapted.traits.add(PersonaTrait(trait))

            if "remove_traits" in adaptations:
                for trait in adaptations["remove_traits"]:
                    adapted.traits.discard(PersonaTrait(trait))

            # Adjust temperature
            if "temperature" in adaptations:
                adapted.temperature = adaptations["temperature"]

        # Adapt based on user expertise
        if context.user_expertise == "beginner":
            adapted.traits.add(PersonaTrait.EDUCATIONAL)
            adapted.traits.add(PersonaTrait.DETAILED)
            adapted.traits.discard(PersonaTrait.TECHNICAL)
        elif context.user_expertise == "expert":
            adapted.traits.add(PersonaTrait.TECHNICAL)
            adapted.traits.add(PersonaTrait.CONCISE)
            adapted.traits.discard(PersonaTrait.EDUCATIONAL)

        return adapted

    def evolve(self, trigger: str, changes: dict[str, Any], performance_delta: float) -> None:
        """Evolve the persona based on performance"""
        evolution = PersonaEvolution(
            timestamp=datetime.now().isoformat(),
            trigger=trigger,
            changes=changes,
            performance_before=self.performance_metrics.get("overall", 0.5),
            performance_after=self.performance_metrics.get("overall", 0.5) + performance_delta,
            reason=f"Performance improvement of {performance_delta:.2%}",
        )

        # Apply changes
        for key, value in changes.items():
            if key == "add_traits":
                for trait in value:
                    self.traits.add(PersonaTrait(trait))
            elif key == "remove_traits":
                for trait in value:
                    self.traits.discard(PersonaTrait(trait))
            elif key == "add_capabilities":
                for cap in value:
                    self.capabilities.add(PersonaCapability(cap))
            elif hasattr(self, key):
                setattr(self, key, value)

        # Update performance
        self.performance_metrics["overall"] = evolution.performance_after

        # Record evolution
        self.evolution_history.append(evolution)

        logger.info(f"Persona {self.name} evolved: {changes}")


class PersonaManager:
    """Manages AI personas and their interactions"""

    def __init__(self):
        self.personas: dict[str, Persona] = {}
        self.active_persona: Optional[Persona] = None
        self.shared_knowledge: dict[str, Any] = {}
        self._initialize_default_personas()

    def _initialize_default_personas(self) -> None:
        """Initialize Sophia and Artemis personas"""

        # Sophia - Business Intelligence Persona
        sophia = Persona(
            name="Sophia",
            description="Business intelligence and analytics expert",
            role="business_analyst",
            traits={
                PersonaTrait.ANALYTICAL,
                PersonaTrait.BUSINESS_FOCUSED,
                PersonaTrait.FORMAL,
                PersonaTrait.SYSTEMATIC,
                PersonaTrait.DATA_FOCUSED,
                PersonaTrait.PROACTIVE,
            },
            capabilities={
                PersonaCapability.DATA_ANALYSIS,
                PersonaCapability.BUSINESS_ANALYSIS,
                PersonaCapability.REPORT_GENERATION,
                PersonaCapability.PATTERN_RECOGNITION,
                PersonaCapability.ANOMALY_DETECTION,
            },
            knowledge_domains=[
                "business_intelligence",
                "data_analytics",
                "market_research",
                "competitive_analysis",
                "financial_analysis",
                "customer_insights",
            ],
            prompt_template="""You are Sophia, an expert business intelligence analyst.

Your role is to:
- Analyze complex business data and extract actionable insights
- Identify patterns, trends, and anomalies in data
- Generate comprehensive reports and visualizations
- Provide strategic recommendations based on data
- Synthesize information from multiple sources

Key traits:
{traits}

Current context:
{context}

Task: {task}""",
            system_message="""You are Sophia, a sophisticated business intelligence system designed to provide deep analytical insights and strategic recommendations. You excel at data analysis, pattern recognition, and translating complex information into actionable business intelligence.""",
            temperature=0.7,
            max_tokens=4000,
        )

        # Context adaptations for Sophia
        sophia.context_adaptations = {
            "finance": {
                "add_traits": ["detailed", "cautious"],
                "temperature": 0.5,
            },
            "marketing": {
                "add_traits": ["creative", "user_focused"],
                "temperature": 0.8,
            },
            "operations": {
                "add_traits": ["pragmatic", "system_focused"],
                "temperature": 0.6,
            },
        }

        # Artemis - Code Generation Persona
        artemis = Persona(
            name="Artemis",
            description="Advanced code generation and technical implementation expert",
            role="code_architect",
            traits={
                PersonaTrait.TECHNICAL,
                PersonaTrait.CODE_FOCUSED,
                PersonaTrait.SYSTEMATIC,
                PersonaTrait.DETAILED,
                PersonaTrait.PRAGMATIC,
                PersonaTrait.AUTONOMOUS,
            },
            capabilities={
                PersonaCapability.CODE_GENERATION,
                PersonaCapability.CODE_ANALYSIS,
                PersonaCapability.TEST_GENERATION,
                PersonaCapability.DOCUMENTATION_GENERATION,
                PersonaCapability.API_INTEGRATION,
                PersonaCapability.PERFORMANCE_ANALYSIS,
                PersonaCapability.SECURITY_ANALYSIS,
            },
            knowledge_domains=[
                "software_architecture",
                "design_patterns",
                "algorithms",
                "data_structures",
                "testing_strategies",
                "performance_optimization",
                "security_best_practices",
            ],
            prompt_template="""You are Artemis, an expert software architect and code generation specialist.

Your role is to:
- Design and implement robust software solutions
- Generate high-quality, maintainable code
- Ensure code follows best practices and patterns
- Create comprehensive tests and documentation
- Optimize for performance and security

Key traits:
{traits}

Technical context:
{context}

Task: {task}

Code quality requirements:
- Follow PEP 8 and language-specific style guides
- Include type hints and docstrings
- Ensure 80%+ test coverage
- Consider edge cases and error handling""",
            system_message="""You are Artemis, an advanced code generation and software architecture system. You excel at creating robust, scalable, and maintainable code solutions. You follow best practices, design patterns, and ensure high code quality with comprehensive testing and documentation.""",
            temperature=0.5,
            max_tokens=8000,
        )

        # Context adaptations for Artemis
        artemis.context_adaptations = {
            "api_development": {
                "add_traits": ["detailed", "cautious"],
                "temperature": 0.4,
            },
            "data_processing": {
                "add_traits": ["systematic", "performance_focused"],
                "temperature": 0.5,
            },
            "ui_development": {
                "add_traits": ["creative", "user_focused"],
                "temperature": 0.6,
            },
            "infrastructure": {
                "add_traits": ["cautious", "system_focused"],
                "temperature": 0.3,
            },
        }

        self.personas["sophia"] = sophia
        self.personas["artemis"] = artemis

        logger.info("Initialized default personas: Sophia and Artemis")

    def get_persona(self, name: str) -> Optional[Persona]:
        """Get a persona by name"""
        return self.personas.get(name.lower())

    def create_persona(
        self,
        name: str,
        description: str,
        role: str,
        traits: list[str],
        capabilities: list[str],
        **kwargs,
    ) -> Persona:
        """Create a new persona"""
        persona = Persona(
            name=name,
            description=description,
            role=role,
            traits={PersonaTrait(t) for t in traits},
            capabilities={PersonaCapability(c) for c in capabilities},
            **kwargs,
        )

        self.personas[name.lower()] = persona
        logger.info(f"Created new persona: {name}")

        return persona

    def activate_persona(self, name: str, context: Optional[PersonaContext] = None) -> Persona:
        """Activate a persona with optional context"""
        persona = self.get_persona(name)
        if not persona:
            raise ValueError(f"Persona {name} not found")

        # Apply context if provided
        if context:
            persona = persona.adapt_to_context(context)

        self.active_persona = persona
        logger.info(f"Activated persona: {name}")

        return persona

    def share_knowledge(
        self, source_persona: str, target_persona: str, knowledge: dict[str, Any]
    ) -> None:
        """Share knowledge between personas"""
        source = self.get_persona(source_persona)
        target = self.get_persona(target_persona)

        if not source or not target:
            raise ValueError("Invalid persona names")

        # Store in shared knowledge
        key = f"{source_persona}_to_{target_persona}_{datetime.now().isoformat()}"
        self.shared_knowledge[key] = {
            "source": source_persona,
            "target": target_persona,
            "knowledge": knowledge,
            "timestamp": datetime.now().isoformat(),
        }

        # Update target persona's knowledge
        if "insights" in knowledge:
            target.knowledge_domains.extend(knowledge.get("new_domains", []))

        logger.info(f"Shared knowledge from {source_persona} to {target_persona}")

    def get_collaboration_prompt(
        self,
        personas: list[str],
        task: str,
        context: PersonaContext,
    ) -> str:
        """Generate a collaboration prompt for multiple personas"""
        persona_objs = [self.get_persona(p) for p in personas if self.get_persona(p)]

        if not persona_objs:
            raise ValueError("No valid personas found")

        prompt = f"""Multi-Persona Collaboration:

Task: {task}

Participating Personas:
"""

        for persona in persona_objs:
            adapted = persona.adapt_to_context(context)
            prompt += f"""
- {persona.name} ({persona.role}):
  Traits: {', '.join(t.value for t in adapted.traits)}
  Capabilities: {', '.join(c.value for c in adapted.capabilities[:3])}
"""

        prompt += f"""

Collaboration Guidelines:
1. Each persona should contribute from their area of expertise
2. Build upon each other's insights
3. Identify synergies and complementary perspectives
4. Synthesize a comprehensive solution

Context:
- Domain: {context.domain}
- Task Type: {context.task_type}
- Constraints: {', '.join(context.constraints)}

Begin collaborative analysis:"""

        return prompt

    def evaluate_persona_performance(
        self,
        persona_name: str,
        task_type: str,
        success_metrics: dict[str, float],
    ) -> float:
        """Evaluate persona performance and trigger evolution if needed"""
        persona = self.get_persona(persona_name)
        if not persona:
            return 0.0

        # Calculate performance score
        performance = sum(success_metrics.values()) / len(success_metrics)

        # Update metrics
        persona.performance_metrics[task_type] = performance
        persona.performance_metrics["overall"] = sum(persona.performance_metrics.values()) / len(
            persona.performance_metrics
        )

        # Check for evolution trigger
        if performance > 0.8 and len(persona.evolution_history) < 10:
            # High performance - evolve to be more confident/autonomous
            changes = {
                "add_traits": ["confident", "autonomous"],
                "temperature": persona.temperature + 0.05,
            }
            persona.evolve(f"high_performance_{task_type}", changes, 0.05)

        elif performance < 0.4:
            # Low performance - evolve to be more cautious/detailed
            changes = {
                "add_traits": ["cautious", "detailed"],
                "temperature": max(0.3, persona.temperature - 0.05),
            }
            persona.evolve(f"low_performance_{task_type}", changes, -0.05)

        return performance

    def export_personas(self, path: Path) -> None:
        """Export all personas to file"""
        data = {
            "personas": {name: persona.to_dict() for name, persona in self.personas.items()},
            "shared_knowledge": self.shared_knowledge,
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(self.personas)} personas to {path}")

    def import_personas(self, path: Path) -> None:
        """Import personas from file"""
        with open(path) as f:
            data = json.load(f)

        for name, persona_dict in data.get("personas", {}).items():
            # Reconstruct persona
            persona = Persona(
                name=persona_dict["name"],
                description=persona_dict["description"],
                role=persona_dict["role"],
                traits={PersonaTrait(t) for t in persona_dict.get("traits", [])},
                capabilities={PersonaCapability(c) for c in persona_dict.get("capabilities", [])},
                knowledge_domains=persona_dict.get("knowledge_domains", []),
                prompt_template=persona_dict.get("prompt_template", ""),
                system_message=persona_dict.get("system_message", ""),
                temperature=persona_dict.get("temperature", 0.7),
                max_tokens=persona_dict.get("max_tokens", 4000),
            )
            self.personas[name] = persona

        self.shared_knowledge = data.get("shared_knowledge", {})

        logger.info(f"Imported {len(self.personas)} personas from {path}")


# Global persona manager instance
_persona_manager = None


def get_persona_manager() -> PersonaManager:
    """Get or create the global persona manager"""
    global _persona_manager
    if _persona_manager is None:
        _persona_manager = PersonaManager()
    return _persona_manager
