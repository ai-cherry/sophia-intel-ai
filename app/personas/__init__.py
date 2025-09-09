"""
Personas Package

Comprehensive persona management framework for Sophia (Business Intelligence)
and Artemis (Code Excellence) with dynamic prompt generation, A/B testing,
and evolution capabilities.

This package provides:
- Core persona management with trait evolution
- Specialized Sophia and Artemis personas
- Dynamic prompt templates with A/B testing
- Performance analysis and evolution engine
- Integration with existing Portkey manager

Usage:
    from app.personas import get_persona_manager, SophiaPersonaFactory, ArtemisPersonaFactory

    # Initialize persona manager
    persona_manager = get_persona_manager()

    # Create personas
    sophia = SophiaPersonaFactory.create_base_sophia()
    artemis = ArtemisPersonaFactory.create_base_artemis()

    # Save personas
    await persona_manager.save_persona(sophia)
    await persona_manager.save_persona(artemis)
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# Removed - no longer supported

# Evolution engine
from .evolution_engine import (
    EvolutionEngine,
    EvolutionEvent,
    EvolutionStrategy,
    LearningPhase,
    PerformanceAnalysis,
    get_evolution_engine,
)

# Core persona management
from .persona_manager import (
    EvolutionTrigger,
    KnowledgeArea,
    PerformanceMetrics,
    Persona,
    PersonaManager,
    PersonaTrait,
    PersonaType,
    TaskDomain,
    get_persona_manager,
)

# Prompt template system
from .prompt_templates import (
    ABTestConfiguration,
    PromptMetrics,
    PromptTemplate,
    PromptTemplateManager,
    PromptType,
    PromptVersion,
    get_default_templates,
    get_template_manager,
)

# Specialized personas
from .sophia_persona import (
    SOPHIA_CONFIG,
    SophiaPersonaFactory,
    create_sophia_persona,
    customize_sophia_for_context,
    get_sophia_evolution_patterns,
    get_sophia_specialized_prompts,
)

logger = logging.getLogger(__name__)

# Package version
__version__ = "1.0.0"

# Export main classes and functions
__all__ = [
    # Core classes
    "PersonaManager",
    "Persona",
    "PersonaType",
    "TaskDomain",
    "EvolutionTrigger",
    "PersonaTrait",
    "KnowledgeArea",
    "PerformanceMetrics",
    # Sophia persona
    "create_sophia_persona",
    "SophiaPersonaFactory",
    "customize_sophia_for_context",
    # Removed from system
    # Prompt templates
    "PromptTemplateManager",
    "PromptTemplate",
    "PromptType",
    "PromptVersion",
    "ABTestConfiguration",
    # Evolution engine
    "EvolutionEngine",
    "EvolutionStrategy",
    "PerformanceAnalysis",
    # Factory functions
    "get_persona_manager",
    "get_template_manager",
    "get_evolution_engine",
    # Configuration
    "SOPHIA_CONFIG",
    # Main initialization function
    "initialize_persona_system",
]


async def initialize_persona_system(
    storage_path: Optional[Path] = None,
) -> dict[str, Any]:
    """
    Initialize the complete persona management system.

    Args:
        storage_path: Optional custom storage path for persona data

    Returns:
        Dictionary with initialized components and their status
    """
    try:
        logger.info("Initializing persona management system...")

        # Initialize managers
        persona_manager = get_persona_manager(storage_path)
        template_manager = get_template_manager(storage_path)
        get_evolution_engine(storage_path)

        # Create base personas
        sophia = create_sophia_persona()
        # Removed completely

        # Save personas
        sophia_saved = await persona_manager.save_persona(sophia)
        # Not applicable

        # Load default prompt templates
        default_templates = get_default_templates()
        templates_loaded = 0

        for template_data in default_templates:
            try:
                template = await template_manager.create_template(
                    template_id=template_data["id"],
                    name=template_data["name"],
                    prompt_type=template_data["prompt_type"],
                    template_content=template_data["template"],
                    persona_types=template_data.get("persona_types", []),
                    task_domains=template_data.get("task_domains", []),
                    required_context=template_data.get("required_context", []),
                    optional_context=template_data.get("optional_context", []),
                    status=PromptVersion.ACTIVE,
                )
                templates_loaded += 1
                logger.debug(f"Loaded template: {template.id}")
            except Exception as e:
                logger.warning(f"Failed to load template {template_data['id']}: {e}")

        # Initialize performance tracking
        initialization_status = {
            "success": True,
            "persona_manager": "initialized",
            "template_manager": "initialized",
            "evolution_engine": "initialized",
            "sophia_persona": "created" if sophia_saved else "creation_failed",
            "artemis_persona": "created" if artemis_saved else "creation_failed",
            "templates_loaded": templates_loaded,
            "total_templates": len(default_templates),
            "storage_path": str(storage_path or Path("data")),
            "version": __version__,
        }

        logger.info(
            f"Persona system initialized successfully. Status: {initialization_status}"
        )
        return initialization_status

    except Exception as e:
        logger.error(f"Failed to initialize persona system: {e}")
        return {"success": False, "error": str(e), "version": __version__}


def get_persona_system_info() -> dict[str, Any]:
    """
    Get information about the persona system capabilities.

    Returns:
        Dictionary with system capabilities and features
    """
    return {
        "version": __version__,
        "personas": {
            "sophia": {
                "type": "business_intelligence",
                "capabilities": [
                    "Business analysis and strategy",
                    "Data visualization and interpretation",
                    "Executive communication",
                    "Market research and competitive analysis",
                    "Financial analysis and forecasting",
                ],
                "variants": list(SophiaPersonaFactory.get_all_sophia_variants().keys()),
            },
            # No longer part of system
        },
        "features": {
            "dynamic_prompts": "Dynamic prompt generation with context injection",
            "ab_testing": "A/B testing for prompt optimization",
            "performance_tracking": "Comprehensive performance metrics and analytics",
            "evolution_engine": "Automated persona improvement based on feedback",
            "cross_persona_learning": "Knowledge sharing between personas",
            "specialization": "Task-specific persona customization",
        },
        "supported_domains": [domain.value for domain in TaskDomain],
        "evolution_strategies": [strategy.value for strategy in EvolutionStrategy],
        "prompt_types": [ptype.value for ptype in PromptType],
    }


async def create_custom_persona(
    name: str,
    persona_type: PersonaType,
    traits: dict[str, float],
    knowledge_areas: dict[str, float],
    **kwargs,
) -> Persona:
    """
    Create a custom persona with specified traits and knowledge areas.

    Args:
        name: Persona name
        persona_type: Type of persona (SOPHIA or HYBRID)
        traits: Dictionary of trait names and values (0.0 to 1.0)
        knowledge_areas: Dictionary of knowledge domain names and expertise levels
        **kwargs: Additional persona parameters

    Returns:
        Configured custom persona
    """
    persona = Persona(name=name, persona_type=persona_type, **kwargs)

    # Add traits
    for trait_name, value in traits.items():
        persona.add_trait(trait_name, value)

    # Add knowledge areas
    for domain, expertise in knowledge_areas.items():
        persona.add_knowledge_area(domain, expertise)

    logger.info(
        f"Created custom persona '{name}' with {len(traits)} traits and {len(knowledge_areas)} knowledge areas"
    )
    return persona


async def run_persona_benchmark(
    personas: list[Persona], benchmark_tasks: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Run benchmark tests on personas to compare their performance.

    Args:
        personas: List of personas to benchmark
        benchmark_tasks: List of benchmark task definitions

    Returns:
        Benchmark results and comparison
    """
    results = {
        "benchmark_id": f"benchmark_{int(datetime.now().timestamp())}",
        "personas_tested": len(personas),
        "tasks_completed": 0,
        "persona_results": {},
        "comparative_analysis": {},
    }

    template_manager = get_template_manager()

    for persona in personas:
        persona_results = {
            "persona_name": persona.name,
            "persona_type": persona.persona_type.value,
            "task_scores": [],
            "avg_score": 0.0,
            "strengths": [],
            "weaknesses": [],
        }

        for task in benchmark_tasks:
            try:
                # Generate prompt for task
                task_domain = TaskDomain(task.get("domain", "general"))
                context = task.get("context", {})

                await template_manager.generate_dynamic_prompt(
                    persona, task_domain, context
                )

                # Simulate task performance (in real implementation, this would call the LLM)
                # For now, we'll estimate based on persona's expertise in the domain
                expertise_score = persona.get_expertise_score(task_domain)
                task_complexity = task.get("complexity", 0.5)

                # Simple performance estimation
                performance_score = min(1.0, expertise_score * (2.0 - task_complexity))

                persona_results["task_scores"].append(
                    {
                        "task_id": task.get("id", "unknown"),
                        "domain": task_domain.value,
                        "score": performance_score,
                        "complexity": task_complexity,
                    }
                )

                results["tasks_completed"] += 1

            except Exception as e:
                logger.warning(f"Benchmark task failed for {persona.name}: {e}")

        # Calculate averages and identify patterns
        if persona_results["task_scores"]:
            persona_results["avg_score"] = sum(
                task["score"] for task in persona_results["task_scores"]
            ) / len(persona_results["task_scores"])

            # Identify strengths (scores > 0.8) and weaknesses (scores < 0.6)
            for task_result in persona_results["task_scores"]:
                if task_result["score"] > 0.8:
                    persona_results["strengths"].append(task_result["domain"])
                elif task_result["score"] < 0.6:
                    persona_results["weaknesses"].append(task_result["domain"])

        results["persona_results"][persona.name] = persona_results

    # Comparative analysis
    if results["persona_results"]:
        all_scores = [
            result["avg_score"] for result in results["persona_results"].values()
        ]

        if all_scores:
            results["comparative_analysis"] = {
                "highest_avg_score": max(all_scores),
                "lowest_avg_score": min(all_scores),
                "score_range": max(all_scores) - min(all_scores),
                "overall_avg": sum(all_scores) / len(all_scores),
            }

    logger.info(
        f"Completed benchmark with {results['tasks_completed']} tasks across {len(personas)} personas"
    )
    return results


# Portkey integration helper
async def integrate_with_portkey(portkey_manager) -> bool:
    """
    Integrate persona system with existing Portkey manager.

    Args:
        portkey_manager: Existing Portkey manager instance

    Returns:
        True if integration successful
    """
    try:
        from app.core.portkey_manager import PortkeyManager

        if not isinstance(portkey_manager, PortkeyManager):
            logger.error("Invalid Portkey manager instance")
            return False

        # Add persona-aware model selection to Portkey manager
        def persona_model_selector(
            persona_type: PersonaType, task_domain: TaskDomain
        ) -> str:
            """Select optimal model based on persona type and task domain."""
            if persona_type == PersonaType.SOPHIA:
                # Business intelligence tasks benefit from analytical models
                if task_domain in [
                    TaskDomain.BUSINESS_ANALYSIS,
                    TaskDomain.STRATEGIC_PLANNING,
                ]:
                    return "claude-3-opus-20240229"  # High reasoning capability
                else:
                    return "claude-3-sonnet-20240229"  # Balanced performance
            # Removed
            else:
                return "claude-3-haiku-20240307"  # Fast for general tasks

        # Add method to Portkey manager
        portkey_manager.persona_model_selector = persona_model_selector

        logger.info("Successfully integrated persona system with Portkey manager")
        return True

    except Exception as e:
        logger.error(f"Failed to integrate with Portkey manager: {e}")
        return False
