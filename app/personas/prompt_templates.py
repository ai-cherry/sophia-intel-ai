"""
Dynamic Prompt Template System with A/B Testing

This module provides a sophisticated prompt template system that supports
dynamic prompt generation, A/B testing, versioning, and performance tracking.
"""

import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import jinja2

from .persona_manager import Persona, PersonaType, TaskDomain

logger = logging.getLogger(__name__)


class PromptType(Enum):
    """Types of prompts in the system."""

    SYSTEM_PROMPT = "system_prompt"
    TASK_SPECIFIC = "task_specific"
    CONTEXT_INJECTION = "context_injection"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    FEW_SHOT = "few_shot"
    INSTRUCTION = "instruction"


class PromptVersion(Enum):
    """Prompt versioning states."""

    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class PromptMetrics:
    """Metrics for prompt performance evaluation."""

    prompt_id: str
    version: str
    usage_count: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    user_satisfaction: float = 0.0
    error_rate: float = 0.0
    engagement_score: float = 0.0
    conversion_rate: float = 0.0
    last_used: datetime = field(default_factory=datetime.now)
    performance_history: list[float] = field(default_factory=list)


@dataclass
class PromptTemplate:
    """
    A dynamic prompt template with versioning and A/B testing capabilities.
    """

    id: str
    name: str
    prompt_type: PromptType
    template: str
    version: str = "1.0.0"
    status: PromptVersion = PromptVersion.DRAFT
    persona_types: list[PersonaType] = field(default_factory=list)
    task_domains: list[TaskDomain] = field(default_factory=list)

    # Template configuration
    parameters: dict[str, Any] = field(default_factory=dict)
    required_context: list[str] = field(default_factory=list)
    optional_context: list[str] = field(default_factory=list)

    # A/B testing configuration
    ab_test_group: Optional[str] = None
    ab_test_weight: float = 1.0

    # Performance tracking
    metrics: PromptMetrics = field(default_factory=lambda: PromptMetrics("", ""))

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    description: str = ""
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize metrics with proper IDs."""
        if not self.metrics.prompt_id:
            self.metrics.prompt_id = self.id
            self.metrics.version = self.version

    def render(self, context: dict[str, Any]) -> str:
        """
        Render the template with provided context.

        Args:
            context: Dictionary of variables to inject into template

        Returns:
            Rendered prompt string
        """
        try:
            jinja_template = jinja2.Template(self.template)
            rendered = jinja_template.render(**context)

            self.metrics.usage_count += 1
            self.metrics.last_used = datetime.now()

            return rendered.strip()

        except Exception as e:
            logger.error(f"Error rendering template {self.id}: {e}")
            self.metrics.error_rate += 0.01
            raise

    def validate_context(self, context: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate that required context is present.

        Args:
            context: Context dictionary to validate

        Returns:
            Tuple of (is_valid, missing_keys)
        """
        missing_keys = []
        for key in self.required_context:
            if key not in context:
                missing_keys.append(key)

        return len(missing_keys) == 0, missing_keys

    def update_performance(
        self, success: bool, response_time: float, user_satisfaction: Optional[float] = None
    ) -> None:
        """Update performance metrics for this template."""
        self.metrics.performance_history.append(1.0 if success else 0.0)

        # Keep only recent history
        if len(self.metrics.performance_history) > 100:
            self.metrics.performance_history = self.metrics.performance_history[-100:]

        # Update success rate
        self.metrics.success_rate = sum(self.metrics.performance_history) / len(
            self.metrics.performance_history
        )

        # Update response time (moving average)
        if self.metrics.avg_response_time == 0:
            self.metrics.avg_response_time = response_time
        else:
            self.metrics.avg_response_time = (self.metrics.avg_response_time * 0.9) + (
                response_time * 0.1
            )

        # Update user satisfaction
        if user_satisfaction is not None:
            if self.metrics.user_satisfaction == 0:
                self.metrics.user_satisfaction = user_satisfaction
            else:
                self.metrics.user_satisfaction = (self.metrics.user_satisfaction * 0.8) + (
                    user_satisfaction * 0.2
                )

        self.updated_at = datetime.now()


@dataclass
class ABTestConfiguration:
    """Configuration for A/B testing prompt templates."""

    test_id: str
    name: str
    variants: list[str]  # Template IDs
    weights: list[float]  # Relative weights for each variant
    start_date: datetime
    end_date: Optional[datetime] = None
    target_metric: str = "success_rate"
    minimum_sample_size: int = 100
    confidence_level: float = 0.95
    is_active: bool = True

    def __post_init__(self):
        """Validate configuration."""
        if len(self.variants) != len(self.weights):
            raise ValueError("Number of variants must match number of weights")

        if not abs(sum(self.weights) - 1.0) < 0.001:
            # Normalize weights
            total_weight = sum(self.weights)
            self.weights = [w / total_weight for w in self.weights]


class PromptTemplateManager:
    """
    Manages prompt templates, versioning, and A/B testing.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize the prompt template manager."""
        self.storage_path = storage_path or Path("data/prompt_templates")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.templates: dict[str, PromptTemplate] = {}
        self.ab_tests: dict[str, ABTestConfiguration] = {}

        # Performance tracking
        self.global_metrics: dict[str, Any] = {
            "total_renders": 0,
            "avg_success_rate": 0.0,
            "avg_response_time": 0.0,
            "active_ab_tests": 0,
        }

        logger.info(f"PromptTemplateManager initialized with storage path: {self.storage_path}")

    async def load_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Load a template from storage."""
        try:
            template_file = self.storage_path / f"{template_id}.json"

            if not template_file.exists():
                logger.warning(f"Template file not found: {template_file}")
                return None

            with open(template_file) as f:
                data = json.load(f)

            template = self._dict_to_template(data)
            self.templates[template_id] = template

            logger.info(f"Loaded template '{template_id}' from {template_file}")
            return template

        except Exception as e:
            logger.error(f"Failed to load template '{template_id}': {e}")
            return None

    async def save_template(self, template: PromptTemplate) -> bool:
        """Save a template to storage."""
        try:
            template_file = self.storage_path / f"{template.id}.json"

            with open(template_file, "w") as f:
                json.dump(self._template_to_dict(template), f, indent=2, default=str)

            logger.info(f"Saved template '{template.id}' to {template_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save template '{template.id}': {e}")
            return False

    async def create_template(
        self, template_id: str, name: str, prompt_type: PromptType, template_content: str, **kwargs
    ) -> PromptTemplate:
        """Create a new prompt template."""
        template = PromptTemplate(
            id=template_id, name=name, prompt_type=prompt_type, template=template_content, **kwargs
        )

        self.templates[template_id] = template
        await self.save_template(template)

        logger.info(f"Created new template '{template_id}'")
        return template

    async def get_best_template(
        self, persona: Persona, task_domain: TaskDomain, context: dict[str, Any]
    ) -> Optional[PromptTemplate]:
        """
        Get the best template for a given persona and task context.

        Uses A/B testing and performance metrics to select optimal template.
        """
        # Find eligible templates
        eligible_templates = []

        for template in self.templates.values():
            if template.status != PromptVersion.ACTIVE:
                continue

            # Check persona type compatibility
            if template.persona_types and persona.persona_type not in template.persona_types:
                continue

            # Check task domain compatibility
            if template.task_domains and task_domain not in template.task_domains:
                continue

            # Validate context requirements
            is_valid, _ = template.validate_context(context)
            if not is_valid:
                continue

            eligible_templates.append(template)

        if not eligible_templates:
            logger.warning(f"No eligible templates found for {persona.name} in {task_domain}")
            return None

        # Check for active A/B tests
        ab_template = await self._get_ab_test_template(eligible_templates, context)
        if ab_template:
            return ab_template

        # Select best performing template
        best_template = max(
            eligible_templates,
            key=lambda t: (t.metrics.success_rate * 0.6 + t.metrics.user_satisfaction * 0.4),
        )

        logger.debug(f"Selected template '{best_template.id}' for {persona.name}")
        return best_template

    async def _get_ab_test_template(
        self, eligible_templates: list[PromptTemplate], context: dict[str, Any]
    ) -> Optional[PromptTemplate]:
        """Select template based on active A/B tests."""
        # Find active A/B tests involving eligible templates
        active_tests = []
        for test in self.ab_tests.values():
            if not test.is_active:
                continue

            if test.end_date and datetime.now() > test.end_date:
                continue

            # Check if any eligible templates are in this test
            test_templates = [t for t in eligible_templates if t.id in test.variants]
            if test_templates:
                active_tests.append((test, test_templates))

        if not active_tests:
            return None

        # Select from the highest priority A/B test
        test, test_templates = active_tests[0]  # Assume first is highest priority

        # Weighted random selection
        template_weights = []
        for template in test_templates:
            variant_index = test.variants.index(template.id)
            template_weights.append(test.weights[variant_index])

        selected_template = random.choices(test_templates, weights=template_weights)[0]

        logger.debug(f"A/B test '{test.test_id}' selected template '{selected_template.id}'")
        return selected_template

    async def create_ab_test(
        self,
        test_id: str,
        name: str,
        template_ids: list[str],
        weights: Optional[list[float]] = None,
        duration_days: int = 30,
    ) -> ABTestConfiguration:
        """Create a new A/B test configuration."""
        if weights is None:
            weights = [1.0 / len(template_ids)] * len(template_ids)

        end_date = datetime.now() + timedelta(days=duration_days)

        ab_test = ABTestConfiguration(
            test_id=test_id,
            name=name,
            variants=template_ids,
            weights=weights,
            start_date=datetime.now(),
            end_date=end_date,
        )

        self.ab_tests[test_id] = ab_test
        self.global_metrics["active_ab_tests"] += 1

        logger.info(f"Created A/B test '{test_id}' with {len(template_ids)} variants")
        return ab_test

    async def get_ab_test_results(self, test_id: str) -> dict[str, Any]:
        """Get results and analysis for an A/B test."""
        if test_id not in self.ab_tests:
            return {"error": "Test not found"}

        test = self.ab_tests[test_id]
        results = {
            "test_id": test_id,
            "name": test.name,
            "status": "active" if test.is_active else "completed",
            "start_date": test.start_date.isoformat(),
            "end_date": test.end_date.isoformat() if test.end_date else None,
            "variants": [],
        }

        # Collect metrics for each variant
        for template_id in test.variants:
            template = self.templates.get(template_id)
            if not template:
                continue

            variant_data = {
                "template_id": template_id,
                "template_name": template.name,
                "usage_count": template.metrics.usage_count,
                "success_rate": template.metrics.success_rate,
                "avg_response_time": template.metrics.avg_response_time,
                "user_satisfaction": template.metrics.user_satisfaction,
                "error_rate": template.metrics.error_rate,
            }
            results["variants"].append(variant_data)

        # Determine winner if test is complete
        if not test.is_active and results["variants"]:
            winner = max(
                results["variants"],
                key=lambda v: v["success_rate"] * 0.6 + v["user_satisfaction"] * 0.4,
            )
            results["winner"] = winner["template_id"]
            results["confidence"] = self._calculate_statistical_significance(results["variants"])

        return results

    def _calculate_statistical_significance(self, variants: list[dict[str, Any]]) -> float:
        """Calculate statistical significance of A/B test results."""
        # Simplified significance calculation
        # In production, use proper statistical tests (chi-square, t-test, etc.)
        if len(variants) < 2:
            return 0.0

        # Get success rates and sample sizes
        rates = [v["success_rate"] for v in variants]
        sizes = [v["usage_count"] for v in variants]

        if min(sizes) < 30:  # Insufficient sample size
            return 0.0

        # Simple confidence based on difference and sample sizes
        max_rate = max(rates)
        min_rate = min(rates)
        rate_diff = max_rate - min_rate

        # Higher confidence with larger differences and sample sizes
        confidence = min(0.99, rate_diff * 2 + (min(sizes) / 1000))
        return confidence

    async def generate_dynamic_prompt(
        self, persona: Persona, task_domain: TaskDomain, context: dict[str, Any]
    ) -> str:
        """
        Generate a dynamic prompt based on persona, task, and context.

        This is the main entry point for prompt generation.
        """
        try:
            # Get the best template
            template = await self.get_best_template(persona, task_domain, context)

            if not template:
                # Fallback to basic prompt generation
                return persona.generate_system_prompt(context)

            # Validate and prepare context
            is_valid, missing_keys = template.validate_context(context)
            if not is_valid:
                logger.warning(f"Missing context keys for template {template.id}: {missing_keys}")
                # Use default values or skip missing context
                for key in missing_keys:
                    context[key] = f"[{key}_not_provided]"

            # Add persona-specific context
            enhanced_context = self._enhance_context_with_persona(context, persona)

            # Render the template
            rendered_prompt = template.render(enhanced_context)

            self.global_metrics["total_renders"] += 1

            return rendered_prompt

        except Exception as e:
            logger.error(f"Error generating dynamic prompt: {e}")
            # Fallback to persona's basic prompt generation
            return persona.generate_system_prompt(context)

    def _enhance_context_with_persona(
        self, context: dict[str, Any], persona: Persona
    ) -> dict[str, Any]:
        """Enhance context with persona-specific information."""
        enhanced = context.copy()

        enhanced.update(
            {
                "persona_name": persona.name,
                "persona_type": persona.persona_type.value,
                "persona_traits": {name: trait.value for name, trait in persona.traits.items()},
                "expertise_areas": {
                    domain: ka.expertise_level for domain, ka in persona.knowledge_areas.items()
                },
                "communication_style": persona.communication_style,
                "preferred_domains": [d.value for d in persona.preferred_domains],
            }
        )

        return enhanced

    def _template_to_dict(self, template: PromptTemplate) -> dict[str, Any]:
        """Convert template to dictionary for serialization."""
        return {
            "id": template.id,
            "name": template.name,
            "prompt_type": template.prompt_type.value,
            "template": template.template,
            "version": template.version,
            "status": template.status.value,
            "persona_types": [pt.value for pt in template.persona_types],
            "task_domains": [td.value for td in template.task_domains],
            "parameters": template.parameters,
            "required_context": template.required_context,
            "optional_context": template.optional_context,
            "ab_test_group": template.ab_test_group,
            "ab_test_weight": template.ab_test_weight,
            "metrics": {
                "prompt_id": template.metrics.prompt_id,
                "version": template.metrics.version,
                "usage_count": template.metrics.usage_count,
                "success_rate": template.metrics.success_rate,
                "avg_response_time": template.metrics.avg_response_time,
                "user_satisfaction": template.metrics.user_satisfaction,
                "error_rate": template.metrics.error_rate,
                "engagement_score": template.metrics.engagement_score,
                "conversion_rate": template.metrics.conversion_rate,
                "last_used": template.metrics.last_used.isoformat(),
                "performance_history": template.metrics.performance_history[
                    -20:
                ],  # Last 20 entries
            },
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
            "created_by": template.created_by,
            "description": template.description,
            "tags": template.tags,
        }

    def _dict_to_template(self, data: dict[str, Any]) -> PromptTemplate:
        """Convert dictionary to PromptTemplate object."""
        # Create metrics object
        metrics_data = data.get("metrics", {})
        metrics = PromptMetrics(
            prompt_id=metrics_data.get("prompt_id", ""),
            version=metrics_data.get("version", ""),
            usage_count=metrics_data.get("usage_count", 0),
            success_rate=metrics_data.get("success_rate", 0.0),
            avg_response_time=metrics_data.get("avg_response_time", 0.0),
            user_satisfaction=metrics_data.get("user_satisfaction", 0.0),
            error_rate=metrics_data.get("error_rate", 0.0),
            engagement_score=metrics_data.get("engagement_score", 0.0),
            conversion_rate=metrics_data.get("conversion_rate", 0.0),
            last_used=datetime.fromisoformat(
                metrics_data.get("last_used", datetime.now().isoformat())
            ),
            performance_history=metrics_data.get("performance_history", []),
        )

        # Create template
        template = PromptTemplate(
            id=data["id"],
            name=data["name"],
            prompt_type=PromptType(data["prompt_type"]),
            template=data["template"],
            version=data["version"],
            status=PromptVersion(data["status"]),
            persona_types=[PersonaType(pt) for pt in data.get("persona_types", [])],
            task_domains=[TaskDomain(td) for td in data.get("task_domains", [])],
            parameters=data.get("parameters", {}),
            required_context=data.get("required_context", []),
            optional_context=data.get("optional_context", []),
            ab_test_group=data.get("ab_test_group"),
            ab_test_weight=data.get("ab_test_weight", 1.0),
            metrics=metrics,
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            created_by=data.get("created_by", "system"),
            description=data.get("description", ""),
            tags=data.get("tags", []),
        )

        return template

    async def get_template_analytics(self) -> dict[str, Any]:
        """Get comprehensive analytics for all templates."""
        analytics = {
            "total_templates": len(self.templates),
            "active_templates": len(
                [t for t in self.templates.values() if t.status == PromptVersion.ACTIVE]
            ),
            "total_renders": self.global_metrics["total_renders"],
            "active_ab_tests": self.global_metrics["active_ab_tests"],
            "template_performance": [],
            "top_performers": [],
            "ab_test_summary": [],
        }

        # Template performance
        for template in self.templates.values():
            perf_data = {
                "id": template.id,
                "name": template.name,
                "type": template.prompt_type.value,
                "status": template.status.value,
                "usage_count": template.metrics.usage_count,
                "success_rate": template.metrics.success_rate,
                "user_satisfaction": template.metrics.user_satisfaction,
                "avg_response_time": template.metrics.avg_response_time,
            }
            analytics["template_performance"].append(perf_data)

        # Top performers
        active_templates = [t for t in self.templates.values() if t.status == PromptVersion.ACTIVE]
        if active_templates:
            top_performers = sorted(
                active_templates,
                key=lambda t: t.metrics.success_rate * 0.6 + t.metrics.user_satisfaction * 0.4,
                reverse=True,
            )[:5]
            analytics["top_performers"] = [
                {
                    "id": t.id,
                    "name": t.name,
                    "score": t.metrics.success_rate * 0.6 + t.metrics.user_satisfaction * 0.4,
                }
                for t in top_performers
            ]

        # A/B test summary
        for test_id, test in self.ab_tests.items():
            test_summary = {
                "test_id": test_id,
                "name": test.name,
                "status": "active" if test.is_active else "completed",
                "variant_count": len(test.variants),
                "start_date": test.start_date.isoformat(),
            }
            analytics["ab_test_summary"].append(test_summary)

        return analytics


# Pre-built template library
def get_default_templates() -> list[dict[str, Any]]:
    """Get default prompt templates for the system."""
    return [
        {
            "id": "sophia_business_analysis",
            "name": "Sophia Business Analysis Template",
            "prompt_type": PromptType.SYSTEM_PROMPT,
            "template": """
You are {{ persona_name }}, a business intelligence expert specializing in {{ task_domain }}.

Your expertise includes:
{% for domain, level in expertise_areas.items() %}
- {{ domain }}: {{ "%.1f"|format(level * 100) }}% expertise
{% endfor %}

Communication style: {{ communication_style.tone }} with {{ communication_style.formality }} formality.

Current task context:
{% if task_context %}
{{ task_context }}
{% endif %}

Your approach should be {{ communication_style.action_orientation }} and focus on {{ communication_style.detail_preference }}.

Provide insights that are actionable and backed by data analysis.
""",
            "persona_types": [PersonaType.SOPHIA],
            "task_domains": [TaskDomain.BUSINESS_ANALYSIS, TaskDomain.STRATEGIC_PLANNING],
            "required_context": ["task_context"],
            "optional_context": ["urgency", "audience"],
        },
        {
            "id": "artemis_code_review",
            "name": "Artemis Code Review Template",
            "prompt_type": PromptType.SYSTEM_PROMPT,
            "template": """
You are {{ persona_name }}, a code excellence specialist conducting a comprehensive code review.

Your technical expertise:
{% for domain, level in expertise_areas.items() %}
{% if domain.startswith('lang_') or domain.startswith('tech_') or domain.startswith('practice_') %}
- {{ domain.replace('_', ' ').title() }}: {{ "%.1f"|format(level * 100) }}% proficiency
{% endif %}
{% endfor %}

Focus areas for this review:
- Code quality and best practices adherence
- Security vulnerabilities and risks
- Performance optimization opportunities
- Maintainability and readability improvements
- Test coverage and testing strategies

{% if language %}
Language-specific considerations for {{ language }}:
- Follow {{ language }} coding standards and conventions
- Apply {{ language }}-specific best practices
- Consider {{ language }} performance characteristics
{% endif %}

Provide specific, actionable feedback with code examples where appropriate.
Structure your review with clear priorities and severity levels.
""",
            "persona_types": [PersonaType.ARTEMIS],
            "task_domains": [TaskDomain.CODE_REVIEW],
            "required_context": ["code_snippet"],
            "optional_context": ["language", "complexity", "team_experience"],
        },
        {
            "id": "chain_of_thought_analysis",
            "name": "Chain of Thought Analysis Template",
            "prompt_type": PromptType.CHAIN_OF_THOUGHT,
            "template": """
You are {{ persona_name }}. Let's approach this {{ task_domain }} task systematically.

Step 1: Understanding the Problem
First, let me analyze what we're dealing with:
{{ task_context }}

Step 2: Information Gathering
What information do I need to consider?
- Current situation and constraints
- Available data and resources
- Success criteria and objectives
- Potential risks and challenges

Step 3: Analysis and Reasoning
Let me work through this step by step:
[I will think through the problem systematically]

Step 4: Solution Development
Based on my analysis, here are the recommended approaches:
[I will provide specific, actionable recommendations]

Step 5: Implementation Guidance
Here's how to implement these solutions:
[I will provide clear next steps]

Let me begin with Step 1...
""",
            "persona_types": [PersonaType.SOPHIA, PersonaType.ARTEMIS],
            "task_domains": [TaskDomain.GENERAL],
            "required_context": ["task_context"],
            "optional_context": ["complexity", "constraints"],
        },
    ]


# Global template manager instance
_template_manager = None


def get_template_manager(storage_path: Optional[Path] = None) -> PromptTemplateManager:
    """Get or create global template manager instance."""
    global _template_manager
    if _template_manager is None:
        _template_manager = PromptTemplateManager(storage_path)
    return _template_manager
