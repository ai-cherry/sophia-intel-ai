"""
Pattern Store - Behavioral patterns and trends memory
Stores recurring patterns, behavioral insights, and predictive models
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from app.core.unified_memory import (
    MemoryContext,
    MemoryMetadata,
    MemoryPriority,
    unified_memory,
)

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns stored"""

    BEHAVIORAL = "behavioral"  # User/agent behavior patterns
    TEMPORAL = "temporal"  # Time-based patterns
    PERFORMANCE = "performance"  # Performance and efficiency patterns
    ERROR = "error"  # Error and failure patterns
    USAGE = "usage"  # System usage patterns
    INTERACTION = "interaction"  # User interaction patterns
    BUSINESS = "business"  # Business process patterns
    PREDICTIVE = "predictive"  # Predictive model patterns


class PatternStrength(Enum):
    """Pattern strength/confidence levels"""

    VERY_STRONG = 0.95
    STRONG = 0.80
    MODERATE = 0.65
    WEAK = 0.40
    VERY_WEAK = 0.20


@dataclass
class PatternMetrics:
    """Pattern statistical metrics"""

    occurrences: int = 0
    observation_period_days: int = 0
    frequency_per_day: float = 0.0
    last_occurrence: Optional[datetime] = None
    trend_direction: str = "stable"  # "increasing", "decreasing", "stable"
    seasonal_component: bool = False
    confidence_interval: tuple = (0.0, 1.0)
    statistical_significance: float = 0.0


@dataclass
class BehavioralPattern:
    """Comprehensive behavioral pattern"""

    pattern_id: str
    name: str
    description: str
    pattern_type: PatternType
    strength: PatternStrength

    # Pattern characteristics
    triggers: list[str] = field(default_factory=list)
    conditions: dict[str, Any] = field(default_factory=dict)
    outcomes: list[str] = field(default_factory=list)

    # Statistical data
    metrics: PatternMetrics = field(default_factory=PatternMetrics)

    # Context
    entities_involved: set[str] = field(default_factory=set)  # users, agents, systems
    domains: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)

    # Temporal aspects
    time_patterns: dict[str, Any] = field(
        default_factory=dict
    )  # hourly, daily, weekly patterns
    seasonal_factors: dict[str, float] = field(default_factory=dict)

    # Predictions
    next_likely_occurrence: Optional[datetime] = None
    probability_next_24h: float = 0.0
    predicted_outcome: Optional[str] = None


class PatternStore:
    """
    Specialized memory store for behavioral patterns and trends
    Optimized for pattern recognition, trend analysis, and prediction
    """

    def __init__(self):
        self.memory_interface = unified_memory
        self.namespace = "patterns"

    async def store_pattern(
        self, pattern: BehavioralPattern, domain: Optional[str] = None
    ) -> str:
        """Store a behavioral pattern"""

        # Create comprehensive content for storage
        content = self._format_pattern_content(pattern)

        # Create metadata with pattern-specific attributes
        metadata = MemoryMetadata(
            memory_id=pattern.pattern_id,
            context=MemoryContext.PATTERN,
            priority=self._determine_priority(pattern),
            tags=pattern.tags.union(
                {
                    pattern.pattern_type.value,
                    pattern.strength.name.lower(),
                    f"freq_{self._categorize_frequency(pattern.metrics.frequency_per_day)}",
                    f"trend_{pattern.metrics.trend_direction}",
                }
            ),
            domain=domain,
            source="pattern_store",
            confidence_score=pattern.strength.value,
        )

        # Store in unified memory
        memory_id = await self.memory_interface.store(content, metadata)

        # Store structured pattern data for analysis
        await self._store_structured_pattern(memory_id, pattern)

        logger.debug(f"Stored behavioral pattern: {pattern.name} ({memory_id})")
        return memory_id

    async def search_patterns(
        self,
        query: str,
        pattern_types: Optional[list[PatternType]] = None,
        min_strength: Optional[PatternStrength] = None,
        entities_filter: Optional[set[str]] = None,
        trend_filter: Optional[str] = None,
        max_results: int = 15,
        domain: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Search patterns with advanced filtering"""

        # Build search tags
        search_tags = set()
        if pattern_types:
            search_tags.update([t.value for t in pattern_types])
        if trend_filter:
            search_tags.add(f"trend_{trend_filter}")

        # Search unified memory
        from app.core.unified_memory import MemoryContext, MemorySearchRequest

        search_request = MemorySearchRequest(
            query=query,
            context_filter=[MemoryContext.PATTERN],
            tag_filter=search_tags if search_tags else None,
            domain_filter=domain,
            max_results=max_results,
            similarity_threshold=0.6,
        )

        results = await self.memory_interface.search(search_request)

        # Enhance results with structured data and apply filters
        enhanced_results = []
        for result in results:
            structured_data = await self._retrieve_structured_pattern(result.memory_id)

            if self._matches_pattern_filters(
                structured_data, min_strength, entities_filter
            ):
                enhanced_results.append(
                    {
                        "memory_id": result.memory_id,
                        "content": result.content,
                        "metadata": result.metadata,
                        "relevance_score": result.relevance_score,
                        "pattern_data": structured_data,
                    }
                )

        return enhanced_results

    async def get_trending_patterns(
        self, time_period_days: int = 7, domain: Optional[str] = None
    ) -> dict[str, Any]:
        """Get patterns that are currently trending"""

        # Search for patterns with increasing trends
        trending = await self.search_patterns(
            query="trending behavioral patterns",
            trend_filter="increasing",
            max_results=20,
            domain=domain,
        )

        # Analyze trending patterns
        analysis = {
            "time_period_days": time_period_days,
            "total_trending": len(trending),
            "by_type": {},
            "by_strength": {"strong": 0, "moderate": 0, "weak": 0},
            "top_patterns": [],
            "emerging_patterns": [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        for pattern in trending:
            data = pattern.get("pattern_data", {})

            # Count by type
            pattern_type = data.get("pattern_type")
            if pattern_type:
                analysis["by_type"][pattern_type] = (
                    analysis["by_type"].get(pattern_type, 0) + 1
                )

            # Count by strength
            strength = data.get("strength", "weak")
            if strength in analysis["by_strength"]:
                analysis["by_strength"][strength] += 1

            # Identify top patterns
            freq = data.get("metrics", {}).get("frequency_per_day", 0)
            if freq > 1.0:  # More than once per day
                analysis["top_patterns"].append(
                    {
                        "name": data.get("name"),
                        "frequency": freq,
                        "strength": strength,
                        "memory_id": pattern["memory_id"],
                    }
                )

            # Identify emerging patterns (recent, low occurrence count)
            metrics = data.get("metrics", {})
            if metrics.get("observation_period_days", 30) <= 7:
                analysis["emerging_patterns"].append(
                    {
                        "name": data.get("name"),
                        "age_days": metrics.get("observation_period_days", 0),
                        "memory_id": pattern["memory_id"],
                    }
                )

        # Sort lists
        analysis["top_patterns"] = sorted(
            analysis["top_patterns"], key=lambda x: x["frequency"], reverse=True
        )[:5]

        return analysis

    async def predict_pattern_occurrence(
        self, pattern_id: str, prediction_horizon_hours: int = 24
    ) -> dict[str, Any]:
        """Predict when a pattern might next occur"""

        structured_data = await self._retrieve_structured_pattern(pattern_id)
        if not structured_data:
            return {"error": "Pattern not found"}

        metrics = structured_data.get("metrics", {})
        frequency = metrics.get("frequency_per_day", 0)
        last_occurrence = metrics.get("last_occurrence")

        if frequency == 0 or not last_occurrence:
            return {
                "pattern_id": pattern_id,
                "prediction": "insufficient_data",
                "probability": 0.0,
            }

        # Simple prediction based on frequency
        hours_since_last = 0
        if last_occurrence:
            last_time = datetime.fromisoformat(last_occurrence)
            hours_since_last = (
                datetime.now(timezone.utc) - last_time
            ).total_seconds() / 3600

        expected_interval_hours = 24 / frequency if frequency > 0 else 24
        probability = max(0.0, min(1.0, hours_since_last / expected_interval_hours))

        next_expected = datetime.now(timezone.utc) + timedelta(
            hours=expected_interval_hours
        )

        return {
            "pattern_id": pattern_id,
            "pattern_name": structured_data.get("name"),
            "current_probability": round(probability, 3),
            "expected_next_occurrence": next_expected.isoformat(),
            "prediction_confidence": structured_data.get("strength", 0.5),
            "frequency_per_day": frequency,
            "hours_since_last": round(hours_since_last, 1),
            "prediction_horizon_hours": prediction_horizon_hours,
        }

    async def update_pattern_metrics(
        self,
        pattern_id: str,
        new_occurrence_time: datetime,
        outcome: Optional[str] = None,
    ) -> bool:
        """Update pattern metrics with a new occurrence"""

        structured_data = await self._retrieve_structured_pattern(pattern_id)
        if not structured_data:
            return False

        metrics = structured_data.get("metrics", {})

        # Update occurrence count
        metrics["occurrences"] = metrics.get("occurrences", 0) + 1
        metrics["last_occurrence"] = new_occurrence_time.isoformat()

        # Recalculate frequency
        if metrics.get("observation_period_days", 0) > 0:
            metrics["frequency_per_day"] = (
                metrics["occurrences"] / metrics["observation_period_days"]
            )

        # Store updated metrics
        structured_data["metrics"] = metrics
        await self._store_structured_pattern(pattern_id, None, structured_data)

        logger.debug(f"Updated pattern metrics for {pattern_id}")
        return True

    # Private helper methods

    def _format_pattern_content(self, pattern: BehavioralPattern) -> str:
        """Format pattern into comprehensive text content"""

        content_parts = [
            f"BEHAVIORAL PATTERN: {pattern.name}",
            f"ID: {pattern.pattern_id}",
            f"TYPE: {pattern.pattern_type.value}",
            f"STRENGTH: {pattern.strength.name} ({pattern.strength.value})",
            "",
            "DESCRIPTION:",
            pattern.description,
            "",
        ]

        if pattern.triggers:
            content_parts.extend(
                ["TRIGGERS:", *[f"• {trigger}" for trigger in pattern.triggers], ""]
            )

        if pattern.conditions:
            content_parts.extend(["CONDITIONS:", str(pattern.conditions), ""])

        if pattern.outcomes:
            content_parts.extend(
                [
                    "TYPICAL OUTCOMES:",
                    *[f"• {outcome}" for outcome in pattern.outcomes],
                    "",
                ]
            )

        # Metrics
        m = pattern.metrics
        content_parts.extend(
            [
                "PATTERN METRICS:",
                f"• Occurrences: {m.occurrences}",
                f"• Observation period: {m.observation_period_days} days",
                f"• Frequency: {m.frequency_per_day:.2f} per day",
                f"• Trend: {m.trend_direction}",
                f"• Last seen: {m.last_occurrence.isoformat() if m.last_occurrence else 'Never'}",
                "",
            ]
        )

        if pattern.entities_involved:
            content_parts.extend(
                [f"ENTITIES INVOLVED: {', '.join(pattern.entities_involved)}", ""]
            )

        if pattern.next_likely_occurrence:
            content_parts.extend(
                [
                    f"NEXT PREDICTED: {pattern.next_likely_occurrence.isoformat()}",
                    f"PROBABILITY (24h): {pattern.probability_next_24h:.1%}",
                    "",
                ]
            )

        return "\n".join(content_parts)

    def _determine_priority(self, pattern: BehavioralPattern) -> MemoryPriority:
        """Determine memory priority based on pattern characteristics"""

        if pattern.strength.value >= 0.9 or pattern.metrics.frequency_per_day >= 5:
            return MemoryPriority.HIGH
        elif pattern.strength.value >= 0.7 or pattern.metrics.frequency_per_day >= 1:
            return MemoryPriority.STANDARD
        else:
            return MemoryPriority.LOW

    def _categorize_frequency(self, frequency: float) -> str:
        """Categorize frequency for tagging"""
        if frequency >= 10:
            return "very_high"
        elif frequency >= 3:
            return "high"
        elif frequency >= 1:
            return "moderate"
        elif frequency >= 0.1:
            return "low"
        else:
            return "very_low"

    async def _store_structured_pattern(
        self,
        memory_id: str,
        pattern: Optional[BehavioralPattern],
        pattern_dict: Optional[dict[str, Any]] = None,
    ):
        """Store structured pattern data"""

        if not self.memory_interface.redis_manager:
            return

        if pattern:
            structured_data = {
                "pattern_id": pattern.pattern_id,
                "name": pattern.name,
                "description": pattern.description,
                "pattern_type": pattern.pattern_type.value,
                "strength": pattern.strength.name.lower(),
                "strength_value": pattern.strength.value,
                "triggers": pattern.triggers,
                "conditions": pattern.conditions,
                "outcomes": pattern.outcomes,
                "metrics": {
                    "occurrences": pattern.metrics.occurrences,
                    "observation_period_days": pattern.metrics.observation_period_days,
                    "frequency_per_day": pattern.metrics.frequency_per_day,
                    "last_occurrence": (
                        pattern.metrics.last_occurrence.isoformat()
                        if pattern.metrics.last_occurrence
                        else None
                    ),
                    "trend_direction": pattern.metrics.trend_direction,
                    "seasonal_component": pattern.metrics.seasonal_component,
                },
                "entities_involved": list(pattern.entities_involved),
                "domains": list(pattern.domains),
                "tags": list(pattern.tags),
                "time_patterns": pattern.time_patterns,
                "next_likely_occurrence": (
                    pattern.next_likely_occurrence.isoformat()
                    if pattern.next_likely_occurrence
                    else None
                ),
                "probability_next_24h": pattern.probability_next_24h,
            }
        else:
            structured_data = pattern_dict

        key = f"pattern_structured:{memory_id}"
        await self.memory_interface.redis_manager.set_with_ttl(
            key, structured_data, ttl=86400 * 14, namespace="patterns"  # 14 days
        )

    async def _retrieve_structured_pattern(
        self, pattern_id: str
    ) -> Optional[dict[str, Any]]:
        """Retrieve structured pattern data"""

        if not self.memory_interface.redis_manager:
            return None

        try:
            key = f"pattern_structured:{pattern_id}"
            data = await self.memory_interface.redis_manager.get(
                key, namespace="patterns"
            )

            if data:
                import json

                return json.loads(data.decode() if isinstance(data, bytes) else data)

        except Exception as e:
            logger.warning(f"Failed to retrieve structured pattern {pattern_id}: {e}")

        return None

    def _matches_pattern_filters(
        self,
        structured_data: Optional[dict[str, Any]],
        min_strength: Optional[PatternStrength],
        entities_filter: Optional[set[str]],
    ) -> bool:
        """Check if pattern matches filtering criteria"""

        if not structured_data:
            return True

        # Strength filter
        if min_strength:
            strength_value = structured_data.get("strength_value", 0)
            if strength_value < min_strength.value:
                return False

        # Entities filter
        if entities_filter:
            pattern_entities = set(structured_data.get("entities_involved", []))
            if not entities_filter.intersection(pattern_entities):
                return False

        return True


# Global pattern store instance
pattern_store = PatternStore()
