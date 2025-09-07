"""
Intelligence Store - High-level reasoning and insights memory
Stores strategic insights, analytical findings, and high-level cognitive outputs
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from app.core.unified_memory import (
    MemoryContext,
    MemoryEntry,
    MemoryMetadata,
    MemoryPriority,
    unified_memory,
)

logger = logging.getLogger(__name__)


class IntelligenceType(Enum):
    """Types of intelligence stored"""

    STRATEGIC_INSIGHT = "strategic_insight"
    ANALYTICAL_FINDING = "analytical_finding"
    MARKET_INTELLIGENCE = "market_intelligence"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    BUSINESS_RECOMMENDATION = "business_recommendation"
    TECHNICAL_ASSESSMENT = "technical_assessment"
    RISK_ANALYSIS = "risk_analysis"
    OPPORTUNITY_IDENTIFICATION = "opportunity_identification"


class IntelligenceConfidence(Enum):
    """Confidence levels for intelligence entries"""

    VERY_HIGH = 0.95
    HIGH = 0.85
    MEDIUM = 0.70
    LOW = 0.50
    VERY_LOW = 0.30


@dataclass
class IntelligenceInsight:
    """Structured intelligence insight"""

    title: str
    summary: str
    detailed_analysis: str
    intelligence_type: IntelligenceType
    confidence: IntelligenceConfidence
    supporting_evidence: List[str]
    implications: List[str]
    recommendations: List[str]
    stakeholders: Set[str]
    time_relevance: str  # "immediate", "short_term", "long_term"
    business_impact: str  # "critical", "high", "medium", "low"
    sources: List[str]
    tags: Set[str]


class IntelligenceStore:
    """
    Specialized memory store for high-level intelligence and insights
    Optimized for strategic decision-making and analytical insights
    """

    def __init__(self):
        self.memory_interface = unified_memory
        self.namespace = "intelligence"

    async def store_insight(
        self,
        insight: IntelligenceInsight,
        user_id: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> str:
        """Store a strategic insight or intelligence finding"""

        # Create comprehensive content for storage
        content = self._format_insight_content(insight)

        # Create metadata with intelligence-specific attributes
        metadata = MemoryMetadata(
            context=MemoryContext.INTELLIGENCE,
            priority=self._determine_priority(insight),
            tags=insight.tags.union(
                {
                    insight.intelligence_type.value,
                    insight.business_impact,
                    insight.time_relevance,
                    f"confidence_{insight.confidence.name.lower()}",
                }
            ),
            user_id=user_id,
            domain=domain,
            source="intelligence_store",
            confidence_score=insight.confidence.value,
        )

        # Store in unified memory
        memory_id = await self.memory_interface.store(content, metadata)

        # Store structured insight data separately for complex queries
        await self._store_structured_insight(memory_id, insight)

        logger.info(f"Stored intelligence insight: {insight.title} ({memory_id})")
        return memory_id

    async def retrieve_insight(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific intelligence insight"""
        entry = await self.memory_interface.retrieve(memory_id)
        if not entry:
            return None

        # Get structured data
        structured_data = await self._retrieve_structured_insight(memory_id)

        return {
            "memory_id": memory_id,
            "content": entry.content,
            "metadata": entry.metadata,
            "structured_insight": structured_data,
        }

    async def search_insights(
        self,
        query: str,
        intelligence_types: Optional[List[IntelligenceType]] = None,
        business_impact: Optional[List[str]] = None,
        time_relevance: Optional[List[str]] = None,
        min_confidence: Optional[IntelligenceConfidence] = None,
        stakeholders: Optional[Set[str]] = None,
        max_results: int = 10,
        domain: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search intelligence insights with advanced filtering"""

        # Build search tags
        search_tags = set()
        if intelligence_types:
            search_tags.update([t.value for t in intelligence_types])
        if business_impact:
            search_tags.update(business_impact)
        if time_relevance:
            search_tags.update(time_relevance)

        # Search unified memory
        from app.core.unified_memory import MemoryContext, MemorySearchRequest

        search_request = MemorySearchRequest(
            query=query,
            context_filter=[MemoryContext.INTELLIGENCE],
            tag_filter=search_tags if search_tags else None,
            domain_filter=domain,
            max_results=max_results,
            similarity_threshold=0.7 if min_confidence is None else min_confidence.value,
        )

        results = await self.memory_interface.search(search_request)

        # Enhance results with structured data
        enhanced_results = []
        for result in results:
            structured_data = await self._retrieve_structured_insight(result.memory_id)

            # Apply additional filters
            if self._matches_advanced_filters(
                structured_data,
                intelligence_types,
                business_impact,
                time_relevance,
                min_confidence,
                stakeholders,
            ):
                enhanced_results.append(
                    {
                        "memory_id": result.memory_id,
                        "content": result.content,
                        "metadata": result.metadata,
                        "relevance_score": result.relevance_score,
                        "structured_insight": structured_data,
                    }
                )

        return enhanced_results

    async def get_strategic_summary(
        self, domain: Optional[str] = None, time_period_days: int = 30
    ) -> Dict[str, Any]:
        """Get strategic intelligence summary for executive dashboards"""

        # Search for high-impact insights from recent period
        recent_insights = await self.search_insights(
            query="strategic business intelligence",
            business_impact=["critical", "high"],
            time_relevance=["immediate", "short_term"],
            max_results=20,
            domain=domain,
        )

        # Categorize insights
        summary = {
            "total_insights": len(recent_insights),
            "by_type": {},
            "by_impact": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "by_confidence": {"very_high": 0, "high": 0, "medium": 0, "low": 0},
            "top_insights": [],
            "key_recommendations": [],
            "risk_alerts": [],
            "opportunities": [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        for insight in recent_insights:
            structured = insight.get("structured_insight", {})

            # Count by type
            intel_type = structured.get("intelligence_type")
            if intel_type:
                summary["by_type"][intel_type] = summary["by_type"].get(intel_type, 0) + 1

            # Count by impact
            impact = structured.get("business_impact", "low")
            summary["by_impact"][impact] += 1

            # Count by confidence
            confidence = structured.get("confidence", "medium")
            summary["by_confidence"][confidence] += 1

            # Collect top insights (high relevance and confidence)
            if insight["relevance_score"] > 0.8:
                summary["top_insights"].append(
                    {
                        "title": structured.get("title", ""),
                        "summary": structured.get("summary", ""),
                        "impact": impact,
                        "confidence": confidence,
                        "memory_id": insight["memory_id"],
                    }
                )

            # Collect recommendations
            recommendations = structured.get("recommendations", [])
            summary["key_recommendations"].extend(recommendations[:2])  # Top 2 per insight

            # Identify risk alerts
            if intel_type == "risk_analysis" and impact in ["critical", "high"]:
                summary["risk_alerts"].append(
                    {
                        "title": structured.get("title", ""),
                        "summary": structured.get("summary", ""),
                        "memory_id": insight["memory_id"],
                    }
                )

            # Identify opportunities
            if intel_type == "opportunity_identification":
                summary["opportunities"].append(
                    {
                        "title": structured.get("title", ""),
                        "summary": structured.get("summary", ""),
                        "memory_id": insight["memory_id"],
                    }
                )

        # Limit collections
        summary["top_insights"] = summary["top_insights"][:5]
        summary["key_recommendations"] = list(set(summary["key_recommendations"]))[:10]
        summary["risk_alerts"] = summary["risk_alerts"][:3]
        summary["opportunities"] = summary["opportunities"][:5]

        return summary

    async def update_insight(self, memory_id: str, updated_insight: IntelligenceInsight) -> bool:
        """Update an existing intelligence insight"""

        # Update the main content
        content = self._format_insight_content(updated_insight)
        success = await self.memory_interface.update(memory_id, content=content)

        if success:
            # Update structured data
            await self._store_structured_insight(memory_id, updated_insight)
            logger.info(f"Updated intelligence insight: {memory_id}")

        return success

    async def delete_insight(self, memory_id: str) -> bool:
        """Delete an intelligence insight"""

        # Delete from unified memory
        success = await self.memory_interface.delete(memory_id)

        if success:
            # Clean up structured data
            await self._delete_structured_insight(memory_id)
            logger.info(f"Deleted intelligence insight: {memory_id}")

        return success

    async def get_intelligence_analytics(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """Get analytics on intelligence store usage and patterns"""

        # This would integrate with the analytics system
        return {
            "total_insights": 0,
            "insights_by_type": {},
            "confidence_distribution": {},
            "impact_distribution": {},
            "recent_activity": [],
            "top_stakeholders": [],
            "domain": domain,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Private helper methods

    def _format_insight_content(self, insight: IntelligenceInsight) -> str:
        """Format insight into comprehensive text content"""

        content_parts = [
            f"INTELLIGENCE INSIGHT: {insight.title}",
            "",
            f"TYPE: {insight.intelligence_type.value}",
            f"CONFIDENCE: {insight.confidence.name} ({insight.confidence.value})",
            f"BUSINESS IMPACT: {insight.business_impact}",
            f"TIME RELEVANCE: {insight.time_relevance}",
            "",
            "SUMMARY:",
            insight.summary,
            "",
            "DETAILED ANALYSIS:",
            insight.detailed_analysis,
            "",
        ]

        if insight.supporting_evidence:
            content_parts.extend(
                [
                    "SUPPORTING EVIDENCE:",
                    *[f"• {evidence}" for evidence in insight.supporting_evidence],
                    "",
                ]
            )

        if insight.implications:
            content_parts.extend(
                ["IMPLICATIONS:", *[f"• {implication}" for implication in insight.implications], ""]
            )

        if insight.recommendations:
            content_parts.extend(
                [
                    "RECOMMENDATIONS:",
                    *[f"• {recommendation}" for recommendation in insight.recommendations],
                    "",
                ]
            )

        if insight.stakeholders:
            content_parts.extend([f"STAKEHOLDERS: {', '.join(insight.stakeholders)}", ""])

        if insight.sources:
            content_parts.extend(["SOURCES:", *[f"• {source}" for source in insight.sources], ""])

        return "\n".join(content_parts)

    def _determine_priority(self, insight: IntelligenceInsight) -> MemoryPriority:
        """Determine memory priority based on insight characteristics"""

        if insight.business_impact == "critical":
            return MemoryPriority.CRITICAL
        elif (
            insight.business_impact == "high"
            and insight.time_relevance == "immediate"
            or insight.confidence.value >= 0.85
        ):
            return MemoryPriority.HIGH
        else:
            return MemoryPriority.STANDARD

    async def _store_structured_insight(self, memory_id: str, insight: IntelligenceInsight):
        """Store structured insight data for complex queries"""

        if not self.memory_interface.redis_manager:
            return

        structured_data = {
            "title": insight.title,
            "summary": insight.summary,
            "intelligence_type": insight.intelligence_type.value,
            "confidence": insight.confidence.name.lower(),
            "confidence_value": insight.confidence.value,
            "business_impact": insight.business_impact,
            "time_relevance": insight.time_relevance,
            "stakeholders": list(insight.stakeholders),
            "recommendations": insight.recommendations,
            "implications": insight.implications,
            "supporting_evidence": insight.supporting_evidence,
            "sources": insight.sources,
            "tags": list(insight.tags),
        }

        key = f"intelligence_structured:{memory_id}"
        await self.memory_interface.redis_manager.set_with_ttl(
            key, structured_data, ttl=86400 * 30, namespace="intelligence"  # 30 days
        )

    async def _retrieve_structured_insight(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve structured insight data"""

        if not self.memory_interface.redis_manager:
            return None

        try:
            key = f"intelligence_structured:{memory_id}"
            data = await self.memory_interface.redis_manager.get(key, namespace="intelligence")

            if data:
                import json

                return json.loads(data.decode() if isinstance(data, bytes) else data)

        except Exception as e:
            logger.warning(f"Failed to retrieve structured insight {memory_id}: {e}")

        return None

    async def _delete_structured_insight(self, memory_id: str):
        """Delete structured insight data"""

        if not self.memory_interface.redis_manager:
            return

        key = f"intelligence_structured:{memory_id}"
        await self.memory_interface.redis_manager.delete(key, namespace="intelligence")

    def _matches_advanced_filters(
        self,
        structured_data: Optional[Dict[str, Any]],
        intelligence_types: Optional[List[IntelligenceType]],
        business_impact: Optional[List[str]],
        time_relevance: Optional[List[str]],
        min_confidence: Optional[IntelligenceConfidence],
        stakeholders: Optional[Set[str]],
    ) -> bool:
        """Check if insight matches advanced filtering criteria"""

        if not structured_data:
            return True

        # Intelligence type filter
        if intelligence_types:
            insight_type = structured_data.get("intelligence_type")
            if insight_type not in [t.value for t in intelligence_types]:
                return False

        # Business impact filter
        if business_impact:
            impact = structured_data.get("business_impact")
            if impact not in business_impact:
                return False

        # Time relevance filter
        if time_relevance:
            relevance = structured_data.get("time_relevance")
            if relevance not in time_relevance:
                return False

        # Minimum confidence filter
        if min_confidence:
            confidence_value = structured_data.get("confidence_value", 0)
            if confidence_value < min_confidence.value:
                return False

        # Stakeholders filter
        if stakeholders:
            insight_stakeholders = set(structured_data.get("stakeholders", []))
            if not stakeholders.intersection(insight_stakeholders):
                return False

        return True


# Global intelligence store instance
intelligence_store = IntelligenceStore()
