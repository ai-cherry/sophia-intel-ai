"""
Evolution Engine for Persona Performance Analysis and Improvement

This module provides sophisticated algorithms for analyzing persona performance,
triggering evolution, managing learning rates, and facilitating knowledge sharing
between personas.
"""

import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from .persona_manager import (
    EvolutionTrigger,
    PerformanceMetrics,
    Persona,
)

logger = logging.getLogger(__name__)


class EvolutionStrategy(Enum):
    """Strategies for persona evolution."""

    CONSERVATIVE = "conservative"  # Small, gradual changes
    AGGRESSIVE = "aggressive"  # Larger, faster changes
    ADAPTIVE = "adaptive"  # Strategy changes based on performance
    TARGETED = "targeted"  # Focus on specific weak areas
    BALANCED = "balanced"  # Balanced improvement across all areas


class LearningPhase(Enum):
    """Learning phases for persona development."""

    INITIALIZATION = "initialization"  # Initial learning phase
    EXPLORATION = "exploration"  # Exploring different strategies
    EXPLOITATION = "exploitation"  # Optimizing known good strategies
    SPECIALIZATION = "specialization"  # Focusing on specific domains
    MASTERY = "mastery"  # Fine-tuning expert performance


@dataclass
class EvolutionEvent:
    """Records a persona evolution event."""

    persona_id: str
    timestamp: datetime
    trigger: EvolutionTrigger
    strategy: EvolutionStrategy
    changes: dict[str, Any]
    performance_before: dict[str, float]
    performance_after: dict[str, float]
    success_impact: float
    confidence: float


@dataclass
class PerformanceAnalysis:
    """Comprehensive performance analysis for a persona."""

    persona_id: str
    analysis_date: datetime

    # Performance metrics
    overall_performance: float
    domain_performance: dict[str, float]
    trait_effectiveness: dict[str, float]
    knowledge_utilization: dict[str, float]

    # Trends and patterns
    performance_trend: str  # "improving", "declining", "stable"
    strength_areas: list[str]
    weakness_areas: list[str]

    # Evolution recommendations
    recommended_strategy: EvolutionStrategy
    recommended_changes: dict[str, float]
    confidence_level: float

    # Learning insights
    learning_rate_assessment: float
    adaptation_effectiveness: float
    specialization_level: float


class EvolutionEngine:
    """
    Advanced evolution engine for persona performance analysis and improvement.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize the evolution engine."""
        self.storage_path = storage_path or Path("data/evolution")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.evolution_history: dict[str, list[EvolutionEvent]] = {}
        self.performance_analyses: dict[str, list[PerformanceAnalysis]] = {}

        # Configuration
        self.config = {
            "min_data_points": 10,
            "confidence_threshold": 0.7,
            "max_evolution_rate": 0.2,
            "learning_rate_decay": 0.95,
            "cross_persona_sharing_threshold": 0.8,
            "performance_window_days": 30,
        }

        logger.info("EvolutionEngine initialized")

    async def analyze_persona_performance(
        self, persona: Persona
    ) -> PerformanceAnalysis:
        """
        Conduct comprehensive performance analysis for a persona.

        Args:
            persona: The persona to analyze

        Returns:
            Detailed performance analysis
        """
        analysis_date = datetime.now()

        # Calculate overall performance
        recent_performance = self._get_recent_performance(persona)
        overall_performance = self._calculate_overall_performance(recent_performance)

        # Analyze domain-specific performance
        domain_performance = self._analyze_domain_performance(persona)

        # Evaluate trait effectiveness
        trait_effectiveness = self._analyze_trait_effectiveness(persona)

        # Assess knowledge utilization
        knowledge_utilization = self._analyze_knowledge_utilization(persona)

        # Determine performance trends
        performance_trend = self._analyze_performance_trend(persona)

        # Identify strengths and weaknesses
        strength_areas, weakness_areas = self._identify_strength_weakness_areas(
            persona, domain_performance, trait_effectiveness
        )

        # Generate evolution recommendations
        recommended_strategy, recommended_changes, confidence = (
            self._generate_evolution_recommendations(
                persona, overall_performance, domain_performance, trait_effectiveness
            )
        )

        # Assess learning characteristics
        learning_rate_assessment = self._assess_learning_rate(persona)
        adaptation_effectiveness = self._assess_adaptation_effectiveness(persona)
        specialization_level = self._calculate_specialization_level(persona)

        analysis = PerformanceAnalysis(
            persona_id=persona.name,
            analysis_date=analysis_date,
            overall_performance=overall_performance,
            domain_performance=domain_performance,
            trait_effectiveness=trait_effectiveness,
            knowledge_utilization=knowledge_utilization,
            performance_trend=performance_trend,
            strength_areas=strength_areas,
            weakness_areas=weakness_areas,
            recommended_strategy=recommended_strategy,
            recommended_changes=recommended_changes,
            confidence_level=confidence,
            learning_rate_assessment=learning_rate_assessment,
            adaptation_effectiveness=adaptation_effectiveness,
            specialization_level=specialization_level,
        )

        # Store analysis
        if persona.name not in self.performance_analyses:
            self.performance_analyses[persona.name] = []
        self.performance_analyses[persona.name].append(analysis)

        # Keep only recent analyses (last 50)
        if len(self.performance_analyses[persona.name]) > 50:
            self.performance_analyses[persona.name] = self.performance_analyses[
                persona.name
            ][-50:]

        logger.info(
            f"Completed performance analysis for {persona.name}: {overall_performance:.3f} overall"
        )
        return analysis

    async def evolve_persona(
        self,
        persona: Persona,
        trigger: EvolutionTrigger,
        strategy: Optional[EvolutionStrategy] = None,
    ) -> bool:
        """
        Evolve a persona based on performance analysis and trigger.

        Args:
            persona: The persona to evolve
            trigger: What triggered the evolution
            strategy: Evolution strategy to use (optional, will be determined automatically)

        Returns:
            True if evolution was successful
        """
        try:
            # Analyze current performance
            analysis = await self.analyze_persona_performance(persona)

            # Determine evolution strategy if not provided
            if strategy is None:
                strategy = analysis.recommended_strategy

            # Record pre-evolution state
            performance_before = {
                "overall": analysis.overall_performance,
                **analysis.domain_performance,
            }

            # Apply evolution based on strategy
            changes = await self._apply_evolution_strategy(persona, analysis, strategy)

            if not changes:
                logger.warning(f"No changes applied during evolution of {persona.name}")
                return False

            # Record post-evolution performance (estimated)
            performance_after = self._estimate_post_evolution_performance(
                performance_before, changes
            )

            # Create evolution event
            evolution_event = EvolutionEvent(
                persona_id=persona.name,
                timestamp=datetime.now(),
                trigger=trigger,
                strategy=strategy,
                changes=changes,
                performance_before=performance_before,
                performance_after=performance_after,
                success_impact=sum(performance_after.values())
                - sum(performance_before.values()),
                confidence=analysis.confidence_level,
            )

            # Store evolution event
            if persona.name not in self.evolution_history:
                self.evolution_history[persona.name] = []
            self.evolution_history[persona.name].append(evolution_event)

            # Keep only recent evolution history (last 100 events)
            if len(self.evolution_history[persona.name]) > 100:
                self.evolution_history[persona.name] = self.evolution_history[
                    persona.name
                ][-100:]

            logger.info(
                f"Successfully evolved {persona.name} using {strategy.value} strategy"
            )
            return True

        except Exception as e:
            logger.error(f"Error evolving persona {persona.name}: {e}")
            return False

    async def _apply_evolution_strategy(
        self,
        persona: Persona,
        analysis: PerformanceAnalysis,
        strategy: EvolutionStrategy,
    ) -> dict[str, Any]:
        """Apply the specified evolution strategy to the persona."""
        changes = {}

        if strategy == EvolutionStrategy.CONSERVATIVE:
            changes = self._apply_conservative_evolution(persona, analysis)
        elif strategy == EvolutionStrategy.AGGRESSIVE:
            changes = self._apply_aggressive_evolution(persona, analysis)
        elif strategy == EvolutionStrategy.ADAPTIVE:
            changes = self._apply_adaptive_evolution(persona, analysis)
        elif strategy == EvolutionStrategy.TARGETED:
            changes = self._apply_targeted_evolution(persona, analysis)
        elif strategy == EvolutionStrategy.BALANCED:
            changes = self._apply_balanced_evolution(persona, analysis)

        return changes

    def _apply_conservative_evolution(
        self, persona: Persona, analysis: PerformanceAnalysis
    ) -> dict[str, Any]:
        """Apply conservative evolution strategy (small, gradual changes)."""
        changes = {}
        max_change = 0.05

        # Focus on weakest areas with small improvements
        for area in analysis.weakness_areas[:2]:  # Top 2 weaknesses
            if area in persona.traits:
                trait = persona.traits[area]
                change = min(max_change, (1.0 - trait.value) * 0.1)
                trait.evolve(change)
                changes[f"trait_{area}"] = change
            elif area in persona.knowledge_areas:
                knowledge = persona.knowledge_areas[area]
                change = min(max_change, (1.0 - knowledge.expertise_level) * 0.1)
                knowledge.expertise_level = min(1.0, knowledge.expertise_level + change)
                changes[f"knowledge_{area}"] = change

        return changes

    def _apply_aggressive_evolution(
        self, persona: Persona, analysis: PerformanceAnalysis
    ) -> dict[str, Any]:
        """Apply aggressive evolution strategy (larger, faster changes)."""
        changes = {}
        max_change = 0.15

        # Make significant changes to address weaknesses
        for area in analysis.weakness_areas:
            if area in persona.traits:
                trait = persona.traits[area]
                change = min(max_change, (1.0 - trait.value) * 0.3)
                trait.evolve(change)
                changes[f"trait_{area}"] = change
            elif area in persona.knowledge_areas:
                knowledge = persona.knowledge_areas[area]
                change = min(max_change, (1.0 - knowledge.expertise_level) * 0.3)
                knowledge.expertise_level = min(1.0, knowledge.expertise_level + change)
                changes[f"knowledge_{area}"] = change

        # Also boost strongest areas
        for area in analysis.strength_areas[:2]:
            if area in persona.traits:
                trait = persona.traits[area]
                change = min(0.05, (1.0 - trait.value) * 0.2)
                trait.evolve(change)
                changes[f"trait_{area}"] = changes.get(f"trait_{area}", 0) + change

        return changes

    def _apply_adaptive_evolution(
        self, persona: Persona, analysis: PerformanceAnalysis
    ) -> dict[str, Any]:
        """Apply adaptive evolution strategy (changes based on performance)."""

        # Adjust evolution intensity based on performance
        if analysis.overall_performance < 0.6:
            # Poor performance - aggressive changes
            return self._apply_aggressive_evolution(persona, analysis)
        elif analysis.overall_performance > 0.8:
            # Good performance - conservative changes
            return self._apply_conservative_evolution(persona, analysis)
        else:
            # Moderate performance - balanced changes
            return self._apply_balanced_evolution(persona, analysis)

    def _apply_targeted_evolution(
        self, persona: Persona, analysis: PerformanceAnalysis
    ) -> dict[str, Any]:
        """Apply targeted evolution strategy (focus on specific weak areas)."""
        changes = {}

        # Identify the single weakest area and focus on it
        if analysis.weakness_areas:
            target_area = analysis.weakness_areas[0]  # Weakest area
            max_change = 0.2

            if target_area in persona.traits:
                trait = persona.traits[target_area]
                change = min(max_change, (1.0 - trait.value) * 0.5)
                trait.evolve(change)
                changes[f"trait_{target_area}"] = change
            elif target_area in persona.knowledge_areas:
                knowledge = persona.knowledge_areas[target_area]
                change = min(max_change, (1.0 - knowledge.expertise_level) * 0.5)
                knowledge.expertise_level = min(1.0, knowledge.expertise_level + change)
                changes[f"knowledge_{target_area}"] = change

        return changes

    def _apply_balanced_evolution(
        self, persona: Persona, analysis: PerformanceAnalysis
    ) -> dict[str, Any]:
        """Apply balanced evolution strategy (improvement across all areas)."""
        changes = {}
        base_change = 0.03

        # Apply small improvements to all traits and knowledge areas
        for trait_name, trait in persona.traits.items():
            if trait.value < 0.95:  # Don't over-optimize already high traits
                change = base_change * (1.0 - trait.value)
                trait.evolve(change)
                changes[f"trait_{trait_name}"] = change

        for ka_name, knowledge in persona.knowledge_areas.items():
            if knowledge.expertise_level < 0.95:
                change = base_change * (1.0 - knowledge.expertise_level)
                knowledge.expertise_level = min(1.0, knowledge.expertise_level + change)
                changes[f"knowledge_{ka_name}"] = change

        return changes

    def _get_recent_performance(
        self, persona: Persona, days: int = 30
    ) -> list[PerformanceMetrics]:
        """Get recent performance metrics for a persona."""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [
            perf
            for perf in persona.performance_history
            if perf.timestamp >= cutoff_date
        ]

    def _calculate_overall_performance(
        self, performance_metrics: list[PerformanceMetrics]
    ) -> float:
        """Calculate overall performance score from metrics."""
        if not performance_metrics:
            return 0.0

        # Weighted average of different performance aspects
        weights = {
            "success_rate": 0.4,
            "quality_score": 0.3,
            "user_satisfaction": 0.2,
            "response_time": 0.1,  # Lower is better, so we'll invert this
        }

        total_score = 0.0
        total_weight = 0.0

        for metric in performance_metrics:
            score = (
                weights["success_rate"] * metric.success_rate
                + weights["quality_score"] * metric.quality_score
                + weights["user_satisfaction"] * (metric.user_satisfaction or 0.0)
                + weights["response_time"]
                * max(
                    0.0, 1.0 - min(1.0, metric.response_time / 10.0)
                )  # Invert and normalize
            )
            total_score += score
            total_weight += 1.0

        return total_score / total_weight if total_weight > 0 else 0.0

    def _analyze_domain_performance(self, persona: Persona) -> dict[str, float]:
        """Analyze performance by domain."""
        domain_performance = {}
        recent_performance = self._get_recent_performance(persona)

        # Group by domain
        domain_metrics = {}
        for metric in recent_performance:
            domain = metric.domain.value
            if domain not in domain_metrics:
                domain_metrics[domain] = []
            domain_metrics[domain].append(metric)

        # Calculate average performance per domain
        for domain, metrics in domain_metrics.items():
            if metrics:
                avg_quality = statistics.mean([m.quality_score for m in metrics])
                avg_success = statistics.mean([m.success_rate for m in metrics])
                domain_performance[domain] = (avg_quality + avg_success) / 2.0

        return domain_performance

    def _analyze_trait_effectiveness(self, persona: Persona) -> dict[str, float]:
        """Analyze how effective each trait is based on recent performance."""
        trait_effectiveness = {}
        recent_performance = self._get_recent_performance(persona)

        if not recent_performance:
            return dict.fromkeys(persona.traits.keys(), 0.5)  # Default neutral

        # Simple correlation analysis between trait values and performance
        overall_performance = self._calculate_overall_performance(recent_performance)

        for trait_name, trait in persona.traits.items():
            # Estimate effectiveness based on trait value and recent performance
            # Higher trait values should correlate with better performance in relevant areas
            effectiveness = min(1.0, trait.value * trait.weight * overall_performance)
            trait_effectiveness[trait_name] = effectiveness

        return trait_effectiveness

    def _analyze_knowledge_utilization(self, persona: Persona) -> dict[str, float]:
        """Analyze how well knowledge areas are being utilized."""
        utilization = {}
        recent_performance = self._get_recent_performance(persona)

        if not recent_performance:
            return dict.fromkeys(persona.knowledge_areas.keys(), 0.5)

        # Calculate utilization based on domain access and performance
        domain_access_count = {}
        for metric in recent_performance:
            domain = metric.domain.value
            domain_access_count[domain] = domain_access_count.get(domain, 0) + 1

        total_tasks = len(recent_performance)

        for ka_name, knowledge in persona.knowledge_areas.items():
            # Calculate utilization based on how often the knowledge area was accessed
            # and how well it performed
            access_frequency = domain_access_count.get(ka_name, 0) / max(1, total_tasks)
            performance_quality = knowledge.expertise_level

            utilization[ka_name] = (access_frequency * 0.4) + (
                performance_quality * 0.6
            )

        return utilization

    def _analyze_performance_trend(self, persona: Persona) -> str:
        """Analyze performance trend over time."""
        recent_performance = self._get_recent_performance(persona)

        if len(recent_performance) < 5:
            return "insufficient_data"

        # Sort by timestamp
        sorted_performance = sorted(recent_performance, key=lambda x: x.timestamp)

        # Calculate trend using simple linear regression
        x_values = list(range(len(sorted_performance)))
        y_values = [p.quality_score for p in sorted_performance]

        if len(set(y_values)) == 1:  # All values are the same
            return "stable"

        # Simple trend calculation
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

        if slope > 0.05:
            return "improving"
        elif slope < -0.05:
            return "declining"
        else:
            return "stable"

    def _identify_strength_weakness_areas(
        self,
        persona: Persona,
        domain_performance: dict[str, float],
        trait_effectiveness: dict[str, float],
    ) -> tuple[list[str], list[str]]:
        """Identify strength and weakness areas."""
        all_performance = {**domain_performance, **trait_effectiveness}

        if not all_performance:
            return [], []

        # Sort by performance
        sorted_areas = sorted(all_performance.items(), key=lambda x: x[1], reverse=True)

        # Top 30% are strengths, bottom 30% are weaknesses
        total_areas = len(sorted_areas)
        strength_count = max(1, int(total_areas * 0.3))
        weakness_count = max(1, int(total_areas * 0.3))

        strengths = [area for area, _ in sorted_areas[:strength_count]]
        weaknesses = [area for area, _ in sorted_areas[-weakness_count:]]

        return strengths, weaknesses

    def _generate_evolution_recommendations(
        self,
        persona: Persona,
        overall_performance: float,
        domain_performance: dict[str, float],
        trait_effectiveness: dict[str, float],
    ) -> tuple[EvolutionStrategy, dict[str, float], float]:
        """Generate evolution strategy and change recommendations."""
        confidence = 0.0

        # Determine strategy based on performance patterns
        if overall_performance < 0.5:
            strategy = EvolutionStrategy.AGGRESSIVE
            confidence = 0.9
        elif overall_performance > 0.9:
            strategy = EvolutionStrategy.CONSERVATIVE
            confidence = 0.8
        elif len(domain_performance) > 0 and min(domain_performance.values()) < 0.4:
            strategy = EvolutionStrategy.TARGETED
            confidence = 0.85
        else:
            strategy = EvolutionStrategy.BALANCED
            confidence = 0.75

        # Generate specific change recommendations
        recommended_changes = {}

        # Focus on the lowest performing areas
        all_performance = {**domain_performance, **trait_effectiveness}
        if all_performance:
            sorted_performance = sorted(all_performance.items(), key=lambda x: x[1])

            # Recommend improvements for bottom performers
            for area, performance in sorted_performance[:3]:  # Bottom 3
                improvement_needed = 0.8 - performance  # Target 0.8 performance
                recommended_changes[area] = max(0.02, min(0.2, improvement_needed))

        return strategy, recommended_changes, confidence

    def _assess_learning_rate(self, persona: Persona) -> float:
        """Assess how quickly the persona learns and adapts."""
        evolution_events = self.evolution_history.get(persona.name, [])

        if len(evolution_events) < 3:
            return 0.5  # Default moderate learning rate

        # Calculate average improvement per evolution
        total_improvement = 0.0
        for event in evolution_events[-10:]:  # Last 10 events
            total_improvement += event.success_impact

        avg_improvement = total_improvement / min(10, len(evolution_events))

        # Normalize to 0-1 range
        learning_rate = max(0.0, min(1.0, 0.5 + (avg_improvement * 2)))

        return learning_rate

    def _assess_adaptation_effectiveness(self, persona: Persona) -> float:
        """Assess how effectively the persona adapts to new situations."""
        recent_performance = self._get_recent_performance(persona, days=14)

        if len(recent_performance) < 5:
            return 0.5

        # Look at performance consistency across different domains
        domain_scores = {}
        for metric in recent_performance:
            domain = metric.domain.value
            if domain not in domain_scores:
                domain_scores[domain] = []
            domain_scores[domain].append(metric.quality_score)

        if len(domain_scores) < 2:
            return 0.5  # Need multiple domains to assess adaptation

        # Calculate coefficient of variation across domains
        domain_averages = [statistics.mean(scores) for scores in domain_scores.values()]

        if not domain_averages:
            return 0.5

        mean_performance = statistics.mean(domain_averages)

        if mean_performance == 0:
            return 0.0

        std_performance = (
            statistics.stdev(domain_averages) if len(domain_averages) > 1 else 0
        )
        coefficient_of_variation = std_performance / mean_performance

        # Lower variation indicates better adaptation (more consistent performance)
        adaptation_effectiveness = max(0.0, min(1.0, 1.0 - coefficient_of_variation))

        return adaptation_effectiveness

    def _calculate_specialization_level(self, persona: Persona) -> float:
        """Calculate how specialized the persona is."""
        # Look at the distribution of knowledge areas
        if not persona.knowledge_areas:
            return 0.0

        expertise_levels = [
            ka.expertise_level for ka in persona.knowledge_areas.values()
        ]

        # High specialization = high variance in expertise levels
        # Low specialization = similar expertise levels across areas

        if len(expertise_levels) == 1:
            return expertise_levels[0]  # Single area = specialization level

        statistics.mean(expertise_levels)
        std_expertise = statistics.stdev(expertise_levels)

        # Higher standard deviation indicates more specialization
        specialization = min(1.0, std_expertise * 2)  # Scale to 0-1

        return specialization

    def _estimate_post_evolution_performance(
        self, performance_before: dict[str, float], changes: dict[str, Any]
    ) -> dict[str, float]:
        """Estimate performance after evolution changes."""
        performance_after = performance_before.copy()

        # Simple estimation: assume changes correlate with performance improvements
        for change_key, change_value in changes.items():
            # Extract area name from change key (e.g., "trait_analytical_thinking" -> "analytical_thinking")
            area_key = change_key.split("_", 1)[1] if "_" in change_key else change_key

            # Find corresponding performance metric
            for perf_key in performance_after:
                if area_key in perf_key or perf_key in area_key:
                    # Estimate improvement based on change magnitude
                    improvement = change_value * 0.5  # Conservative estimate
                    performance_after[perf_key] = min(
                        1.0, performance_after[perf_key] + improvement
                    )
                    break

        return performance_after

    async def cross_persona_knowledge_sharing(
        self, source_persona: Persona, target_persona: Persona, knowledge_area: str
    ) -> bool:
        """
        Share knowledge between personas in complementary domains.

        Args:
            source_persona: Persona with expertise to share
            target_persona: Persona to receive knowledge
            knowledge_area: Specific knowledge area to share

        Returns:
            True if knowledge sharing was successful
        """
        try:
            if knowledge_area not in source_persona.knowledge_areas:
                logger.warning(
                    f"Knowledge area '{knowledge_area}' not found in source persona"
                )
                return False

            source_expertise = source_persona.knowledge_areas[
                knowledge_area
            ].expertise_level

            # Only share if source has high expertise
            if source_expertise < self.config["cross_persona_sharing_threshold"]:
                return False

            # Create or update knowledge area in target persona
            if knowledge_area not in target_persona.knowledge_areas:
                target_persona.add_knowledge_area(knowledge_area, 0.0)

            target_knowledge = target_persona.knowledge_areas[knowledge_area]

            # Transfer knowledge (limited by learning capacity)
            transfer_amount = min(
                0.1, (source_expertise - target_knowledge.expertise_level) * 0.2
            )

            if transfer_amount > 0:
                target_knowledge.expertise_level = min(
                    1.0, target_knowledge.expertise_level + transfer_amount
                )
                target_knowledge.last_accessed = datetime.now()

                logger.info(
                    f"Shared {transfer_amount:.3f} knowledge in '{knowledge_area}' "
                    f"from {source_persona.name} to {target_persona.name}"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error in cross-persona knowledge sharing: {e}")
            return False

    async def get_evolution_insights(self, persona_name: str) -> dict[str, Any]:
        """Get comprehensive evolution insights for a persona."""
        insights = {
            "persona_name": persona_name,
            "evolution_summary": {},
            "performance_trends": {},
            "learning_patterns": {},
            "recommendations": {},
        }

        # Evolution history analysis
        evolution_events = self.evolution_history.get(persona_name, [])
        if evolution_events:
            insights["evolution_summary"] = {
                "total_evolutions": len(evolution_events),
                "successful_evolutions": len(
                    [e for e in evolution_events if e.success_impact > 0]
                ),
                "avg_success_impact": statistics.mean(
                    [e.success_impact for e in evolution_events]
                ),
                "most_used_strategy": statistics.mode(
                    [e.strategy.value for e in evolution_events]
                ),
                "recent_evolution_frequency": len(
                    [
                        e
                        for e in evolution_events
                        if e.timestamp > datetime.now() - timedelta(days=30)
                    ]
                ),
            }

        # Performance analysis
        analyses = self.performance_analyses.get(persona_name, [])
        if analyses:
            recent_analysis = analyses[-1]
            insights["performance_trends"] = {
                "current_overall_performance": recent_analysis.overall_performance,
                "performance_trend": recent_analysis.performance_trend,
                "top_strengths": recent_analysis.strength_areas[:3],
                "key_weaknesses": recent_analysis.weakness_areas[:3],
                "specialization_level": recent_analysis.specialization_level,
                "adaptation_effectiveness": recent_analysis.adaptation_effectiveness,
            }

        # Learning pattern analysis
        if evolution_events and analyses:
            insights["learning_patterns"] = {
                "learning_rate": analyses[-1].learning_rate_assessment,
                "preferred_evolution_triggers": self._analyze_evolution_triggers(
                    evolution_events
                ),
                "effectiveness_by_strategy": self._analyze_strategy_effectiveness(
                    evolution_events
                ),
                "knowledge_growth_rate": self._calculate_knowledge_growth_rate(
                    evolution_events
                ),
            }

        # Generate actionable recommendations
        if analyses:
            insights["recommendations"] = self._generate_actionable_recommendations(
                analyses[-1]
            )

        return insights

    def _analyze_evolution_triggers(
        self, evolution_events: list[EvolutionEvent]
    ) -> dict[str, int]:
        """Analyze which triggers are most common for this persona."""
        trigger_counts = {}
        for event in evolution_events:
            trigger = event.trigger.value
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1

        return dict(sorted(trigger_counts.items(), key=lambda x: x[1], reverse=True))

    def _analyze_strategy_effectiveness(
        self, evolution_events: list[EvolutionEvent]
    ) -> dict[str, float]:
        """Analyze effectiveness of different evolution strategies."""
        strategy_impacts = {}

        for event in evolution_events:
            strategy = event.strategy.value
            if strategy not in strategy_impacts:
                strategy_impacts[strategy] = []
            strategy_impacts[strategy].append(event.success_impact)

        return {
            strategy: statistics.mean(impacts)
            for strategy, impacts in strategy_impacts.items()
        }

    def _calculate_knowledge_growth_rate(
        self, evolution_events: list[EvolutionEvent]
    ) -> float:
        """Calculate rate of knowledge acquisition over time."""
        if len(evolution_events) < 2:
            return 0.0

        knowledge_changes = []
        for event in evolution_events:
            knowledge_change = sum(
                change
                for key, change in event.changes.items()
                if key.startswith("knowledge_")
            )
            knowledge_changes.append(knowledge_change)

        if not knowledge_changes:
            return 0.0

        return statistics.mean(knowledge_changes)

    def _generate_actionable_recommendations(
        self, analysis: PerformanceAnalysis
    ) -> dict[str, Any]:
        """Generate specific, actionable recommendations."""
        recommendations = {
            "immediate_actions": [],
            "medium_term_goals": [],
            "long_term_strategy": "",
            "focus_areas": analysis.weakness_areas[:2],
            "evolution_strategy": analysis.recommended_strategy.value,
        }

        # Immediate actions based on weaknesses
        for weakness in analysis.weakness_areas[:2]:
            recommendations["immediate_actions"].append(
                f"Improve {weakness} through targeted practice and feedback"
            )

        # Medium-term goals based on performance trend
        if analysis.performance_trend == "declining":
            recommendations["medium_term_goals"].append(
                "Stabilize performance across all domains"
            )
        elif analysis.performance_trend == "stable":
            recommendations["medium_term_goals"].append(
                "Identify breakthrough opportunities"
            )
        else:
            recommendations["medium_term_goals"].append("Maintain improvement momentum")

        # Long-term strategy based on specialization level
        if analysis.specialization_level < 0.3:
            recommendations["long_term_strategy"] = (
                "Develop deeper specialization in core domains"
            )
        elif analysis.specialization_level > 0.7:
            recommendations["long_term_strategy"] = (
                "Expand capabilities to adjacent domains"
            )
        else:
            recommendations["long_term_strategy"] = (
                "Balance specialization with versatility"
            )

        return recommendations


# Global evolution engine instance
_evolution_engine = None


def get_evolution_engine(storage_path: Optional[Path] = None) -> EvolutionEngine:
    """Get or create global evolution engine instance."""
    global _evolution_engine
    if _evolution_engine is None:
        _evolution_engine = EvolutionEngine(storage_path)
    return _evolution_engine
