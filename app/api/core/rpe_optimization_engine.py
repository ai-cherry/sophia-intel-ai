"""
Unified Revenue Per Employee Engine - The single source of truth
Blends original OKR alignment with refined RPE focus
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List

import asyncpg
import networkx as nx
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RPEImpactType(Enum):
    DIRECT_REVENUE = "direct_revenue"
    COST_REDUCTION = "cost_reduction"
    RETENTION = "retention"
    ENABLEMENT = "enablement"
    MARKET_CAPTURE = "market_capture"
    FOUNDATION = "foundation"


@dataclass
class RPEImpact:
    current_rpe: float
    projected_rpe_impact: float
    confidence_score: float
    time_to_impact: int
    impact_type: RPEImpactType
    supporting_metrics: Dict[str, float]


class RPEOptimizationEngine:
    """
    Core engine that evaluates EVERYTHING through revenue per employee impact
    Integrates with Sophia's existing infrastructure
    """

    def __init__(
        self, db_pool: asyncpg.Pool, redis_client: redis.Redis, sophia_context: Dict
    ):
        self.db_pool = db_pool  # Neon PostgreSQL
        self.redis = redis_client  # Redis for caching
        self.graph = nx.DiGraph()  # For blockage detection
        self.sophia_context = sophia_context  # Integration with main Sophia
        self.cache_ttl = 300  # 5-minute Redis cache for performance

        # Initialize baseline metrics cache
        self._baseline_cache = None
        self._baseline_cache_time = None

    async def evaluate_any_activity(
        self,
        activity_type: str,  # 'project', 'task', 'meeting', 'hire', etc.
        activity_data: Dict,
        source_system: str,  # 'linear', 'asana', 'notion', 'gong', etc.
    ) -> RPEImpact:
        """
        Universal evaluation function - EVERYTHING gets RPE scored
        """

        try:
            # Check cache first
            cache_key = f"rpe_eval:{activity_type}:{activity_data.get('id', 'unknown')}:{source_system}"
            cached_result = await self.redis.get(cache_key)

            if cached_result:
                logger.info(f"Cache hit for RPE evaluation: {cache_key}")
                cached_data = json.loads(cached_result)
                return RPEImpact(**cached_data)

            # Get current baseline
            baseline = await self._get_current_baseline()

            # Calculate direct revenue impact
            revenue_impact = await self._calculate_revenue_impact(
                activity_type, activity_data, source_system
            )

            # Calculate efficiency gains (cost reduction/automation)
            efficiency_impact = await self._calculate_efficiency_impact(
                activity_type, activity_data
            )

            # Calculate ARPU contribution (expediting implementation, cross-sell)
            arpu_impact = await self._calculate_arpu_impact(activity_data)

            # Calculate market signal adjustments from Gong/HubSpot
            market_multiplier = await self._apply_market_signals(activity_data)

            # Core RPE calculation
            total_impact = (revenue_impact + efficiency_impact) * market_multiplier
            rpe_delta = (
                total_impact / baseline["employee_count"]
                if baseline["employee_count"] > 0
                else 0
            )

            # Create RPE impact object
            rpe_impact = RPEImpact(
                current_rpe=(
                    baseline["current_revenue"] / baseline["employee_count"]
                    if baseline["employee_count"] > 0
                    else 0
                ),
                projected_rpe_impact=rpe_delta,
                confidence_score=await self._calculate_confidence(
                    activity_data, source_system
                ),
                time_to_impact=await self._estimate_time_to_impact(activity_data),
                impact_type=await self._determine_impact_type(activity_data),
                supporting_metrics=await self._calc_supporting_metrics(activity_data),
            )

            # Cache the result
            cache_data = {
                "current_rpe": rpe_impact.current_rpe,
                "projected_rpe_impact": rpe_impact.projected_rpe_impact,
                "confidence_score": rpe_impact.confidence_score,
                "time_to_impact": rpe_impact.time_to_impact,
                "impact_type": rpe_impact.impact_type,
                "supporting_metrics": rpe_impact.supporting_metrics,
            }

            await self.redis.setex(
                cache_key, self.cache_ttl, json.dumps(cache_data, default=str)
            )

            logger.info(
                f"RPE evaluation completed for {activity_type}: ${rpe_delta:,.2f}"
            )
            return rpe_impact

        except Exception as e:
            logger.error(f"Error in RPE evaluation: {str(e)}")
            # Return safe default
            return RPEImpact(
                current_rpe=0,
                projected_rpe_impact=0,
                confidence_score=0,
                time_to_impact=0,
                impact_type=RPEImpactType.FOUNDATION,
                supporting_metrics={},
            )

    async def detect_collaboration_gaps(self) -> List[Dict]:
        """
        Find missing inter-departmental collaboration affecting RPE
        Uses NetworkX graph analysis for importance scoring
        """

        try:
            async with self.db_pool.acquire() as conn:
                # Build collaboration graph from Linear/Asana/Notion
                await self._rebuild_collaboration_graph(conn)

                gaps = []

                # Find disconnected components that should be connected
                components = list(nx.weakly_connected_components(self.graph))

                for i, comp1 in enumerate(components):
                    for comp2 in components[i + 1 :]:
                        # Check if components share semantic similarity
                        similarity = await self._calculate_component_similarity(
                            comp1, comp2
                        )

                        if similarity > 0.7:  # Should be connected but aren't
                            gap_impact = await self._calculate_gap_impact(comp1, comp2)
                            gaps.append(
                                {
                                    "type": "missing_collaboration",
                                    "departments": self._get_departments(comp1, comp2),
                                    "projects": self._get_projects(comp1, comp2),
                                    "rpe_loss": gap_impact["daily_rpe_loss"],
                                    "resolution": gap_impact["recommended_action"],
                                    "urgency": (
                                        "critical"
                                        if gap_impact["daily_rpe_loss"] > 1000
                                        else "high"
                                    ),
                                }
                            )

                # Find customer needs from Gong not reflected in projects
                unaddressed_needs = await self._find_unaddressed_customer_needs(conn)
                baseline = await self._get_current_baseline()

                for need in unaddressed_needs:
                    gaps.append(
                        {
                            "type": "unaddressed_market_signal",
                            "source": "gong",
                            "description": need["description"],
                            "rpe_opportunity": (
                                need["potential_revenue"] / baseline["employee_count"]
                                if baseline["employee_count"] > 0
                                else 0
                            ),
                            "resolution": f"Create project: {need['suggested_project']}",
                            "urgency": need["urgency"],
                        }
                    )

                return sorted(
                    gaps,
                    key=lambda x: x.get("rpe_loss", x.get("rpe_opportunity", 0)),
                    reverse=True,
                )

        except Exception as e:
            logger.error(f"Error detecting collaboration gaps: {str(e)}")
            return []

    async def auto_escalate_from_signals(
        self, signal_source: str = "all"
    ) -> List[Dict]:
        """
        Automatically adjust priorities based on market signals
        Integrates Gong transcripts, HubSpot deals, industry data
        """

        try:
            escalations = []

            # Get signals from various sources
            if signal_source in ["gong", "all"]:
                gong_signals = await self._process_gong_signals()
                escalations.extend(await self._evaluate_gong_escalations(gong_signals))

            if signal_source in ["hubspot", "all"]:
                hubspot_signals = await self._process_hubspot_pipeline()
                escalations.extend(
                    await self._evaluate_deal_escalations(hubspot_signals)
                )

            if signal_source in ["industry", "all"]:
                # Use web search for industry intel
                industry_signals = await self._gather_industry_intelligence()
                escalations.extend(
                    await self._evaluate_competitive_escalations(industry_signals)
                )

            # Apply escalations automatically
            for escalation in escalations:
                if (
                    escalation.get("auto_apply", False)
                    and escalation.get("confidence", 0) > 0.8
                ):
                    await self._apply_escalation(escalation)

                    # Log the auto-escalation
                    await self._log_auto_escalation(escalation)

            return escalations

        except Exception as e:
            logger.error(f"Error in auto-escalation: {str(e)}")
            return []

    async def _apply_market_signals(self, activity_data: Dict) -> float:
        """
        Adjust impact based on real-time market conditions
        """
        try:
            multiplier = 1.0

            # Check Gong for customer urgency on this topic
            gong_urgency = await self._check_gong_urgency(activity_data)
            if gong_urgency > 0.7:
                multiplier *= 1.3  # 30% boost for high customer demand

            # Check HubSpot for deal dependencies
            deal_dependencies = await self._check_deal_dependencies(activity_data)
            if deal_dependencies.get("total_value", 0) > 100000:
                multiplier *= 1.5  # 50% boost for large deal impact

            # Check competitive intelligence
            competitive_threat = await self._check_competitive_landscape(activity_data)
            if competitive_threat.get("severity") == "high":
                multiplier *= 1.4  # 40% boost for competitive threats

            return min(multiplier, 2.0)  # Cap at 2x to avoid over-weighting

        except Exception as e:
            logger.error(f"Error applying market signals: {str(e)}")
            return 1.0

    async def _get_current_baseline(self) -> Dict:
        """Get current company baseline metrics with caching"""

        # Check cache first
        if (
            self._baseline_cache
            and self._baseline_cache_time
            and datetime.utcnow() - self._baseline_cache_time < timedelta(hours=1)
        ):
            return self._baseline_cache

        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    SELECT 
                        COALESCE(current_revenue, 0) as current_revenue,
                        COALESCE(employee_count, 1) as employee_count,
                        COALESCE(current_arpu, 0) as current_arpu,
                        COALESCE(current_ebitda_margin, 0) as current_ebitda_margin
                    FROM company_baseline_metrics 
                    WHERE is_current = true
                    LIMIT 1
                """
                )

                if result:
                    baseline = dict(result)
                else:
                    # Default values if no baseline exists
                    baseline = {
                        "current_revenue": 1000000,  # $1M default
                        "employee_count": 50,  # 50 employees default
                        "current_arpu": 500,  # $500 ARPU default
                        "current_ebitda_margin": 0.2,  # 20% EBITDA default
                    }

                # Cache the result
                self._baseline_cache = baseline
                self._baseline_cache_time = datetime.utcnow()

                return baseline

        except Exception as e:
            logger.error(f"Error getting baseline metrics: {str(e)}")
            # Return safe defaults
            return {
                "current_revenue": 1000000,
                "employee_count": 50,
                "current_arpu": 500,
                "current_ebitda_margin": 0.2,
            }

    async def _calculate_revenue_impact(
        self, activity_type: str, activity_data: Dict, source: str
    ) -> float:
        """Calculate direct revenue impact"""
        try:
            if activity_type == "project":
                # Direct revenue from project completion
                return activity_data.get("estimated_revenue_impact", 0)
            elif activity_type == "task":
                # Revenue from task completion (part of larger project)
                project_revenue = await self._get_project_revenue(
                    activity_data.get("project_id")
                )
                task_weight = activity_data.get("weight", 0.1)
                return project_revenue * task_weight
            elif activity_type == "okr":
                # OKR revenue impact based on strategic value
                return activity_data.get("revenue_target", 0) * 0.8  # 80% confidence
            return 0
        except Exception as e:
            logger.error(f"Error calculating revenue impact: {str(e)}")
            return 0

    async def _calculate_efficiency_impact(
        self, activity_type: str, activity_data: Dict
    ) -> float:
        """Calculate cost reduction/efficiency gains"""
        try:
            description = activity_data.get("description", "").lower()

            if "automation" in description:
                # Automation projects typically save 40-60% of manual effort
                manual_cost = activity_data.get("manual_cost_estimate", 0)
                return manual_cost * 0.5
            elif "process improvement" in description:
                # Process improvements typically save 20-30%
                current_cost = activity_data.get("current_process_cost", 0)
                return current_cost * 0.25
            elif "ai" in description or "machine learning" in description:
                # AI projects typically provide 30-50% efficiency gains
                baseline_cost = activity_data.get("baseline_cost", 0)
                return baseline_cost * 0.4
            return 0
        except Exception as e:
            logger.error(f"Error calculating efficiency impact: {str(e)}")
            return 0

    async def _calculate_arpu_impact(self, activity_data: Dict) -> float:
        """Calculate ARPU contribution"""
        try:
            description = activity_data.get("description", "").lower()
            baseline = await self._get_current_baseline()

            if any(
                keyword in description
                for keyword in ["onboarding", "implementation", "setup"]
            ):
                # Faster implementation = higher ARPU
                speed_improvement = (
                    activity_data.get("speed_improvement_percent", 0) / 100
                )
                return baseline["current_arpu"] * speed_improvement * 0.3
            elif any(
                keyword in description
                for keyword in ["cross-sell", "upsell", "expansion"]
            ):
                # Direct ARPU expansion
                return activity_data.get("expansion_revenue_estimate", 0)
            elif "retention" in description:
                # Retention improvements
                retention_improvement = (
                    activity_data.get("retention_improvement_percent", 0) / 100
                )
                return baseline["current_arpu"] * retention_improvement * 0.5
            return 0
        except Exception as e:
            logger.error(f"Error calculating ARPU impact: {str(e)}")
            return 0

    # Placeholder methods for complex integrations
    async def _calculate_confidence(
        self, activity_data: Dict, source_system: str
    ) -> float:
        """Calculate confidence score based on data quality and source reliability"""
        base_confidence = 0.7

        # Adjust based on source system reliability
        source_multipliers = {
            "notion": 0.9,  # CEO-owned, high trust
            "linear": 0.85,  # Engineering estimates, good reliability
            "asana": 0.8,  # Operations estimates, decent reliability
            "gong": 0.75,  # Customer signals, variable quality
            "hubspot": 0.8,  # Sales data, good reliability
        }

        return base_confidence * source_multipliers.get(source_system, 0.7)

    async def _estimate_time_to_impact(self, activity_data: Dict) -> int:
        """Estimate time to impact in days"""
        # Simple heuristic based on activity type and complexity
        complexity = activity_data.get("complexity", "medium")

        complexity_days = {"low": 30, "medium": 60, "high": 120, "very_high": 180}

        return complexity_days.get(complexity, 60)

    async def _determine_impact_type(self, activity_data: Dict) -> RPEImpactType:
        """Determine the type of RPE impact"""
        description = activity_data.get("description", "").lower()

        if any(
            keyword in description
            for keyword in ["revenue", "sales", "customer acquisition"]
        ):
            return RPEImpactType.DIRECT_REVENUE
        elif any(
            keyword in description
            for keyword in ["automation", "efficiency", "cost reduction"]
        ):
            return RPEImpactType.COST_REDUCTION
        elif any(
            keyword in description for keyword in ["retention", "churn", "satisfaction"]
        ):
            return RPEImpactType.RETENTION
        elif any(
            keyword in description for keyword in ["training", "enablement", "tools"]
        ):
            return RPEImpactType.ENABLEMENT
        elif any(
            keyword in description for keyword in ["market", "competitive", "expansion"]
        ):
            return RPEImpactType.MARKET_CAPTURE
        else:
            return RPEImpactType.FOUNDATION

    async def _calc_supporting_metrics(self, activity_data: Dict) -> Dict[str, float]:
        """Calculate supporting metrics for the RPE impact"""
        return {
            "estimated_hours": activity_data.get("estimated_hours", 0),
            "resource_cost": activity_data.get("resource_cost", 0),
            "risk_factor": activity_data.get("risk_factor", 0.1),
            "strategic_alignment": activity_data.get("strategic_alignment", 0.5),
        }

    # Placeholder methods for complex graph analysis
    async def _rebuild_collaboration_graph(self, conn):
        """Rebuild the collaboration graph from database"""
        # This would build a NetworkX graph from project/task relationships

    async def _calculate_component_similarity(self, comp1, comp2) -> float:
        """Calculate semantic similarity between graph components"""
        # This would use NLP to compare project descriptions/goals
        return 0.5  # Placeholder

    async def _calculate_gap_impact(self, comp1, comp2) -> Dict:
        """Calculate the impact of a collaboration gap"""
        return {
            "daily_rpe_loss": 500,  # Placeholder
            "recommended_action": "Create cross-functional team",
        }

    async def _get_departments(self, comp1, comp2) -> List[str]:
        """Get departments involved in components"""
        return ["Engineering", "Operations"]  # Placeholder

    async def _get_projects(self, comp1, comp2) -> List[str]:
        """Get projects involved in components"""
        return ["Project A", "Project B"]  # Placeholder

    async def _find_unaddressed_customer_needs(self, conn) -> List[Dict]:
        """Find customer needs from Gong not reflected in projects"""
        return []  # Placeholder

    async def _process_gong_signals(self) -> List[Dict]:
        """Process signals from Gong transcripts"""
        return []  # Placeholder

    async def _evaluate_gong_escalations(self, signals) -> List[Dict]:
        """Evaluate escalations from Gong signals"""
        return []  # Placeholder

    async def _process_hubspot_pipeline(self) -> List[Dict]:
        """Process HubSpot pipeline data"""
        return []  # Placeholder

    async def _evaluate_deal_escalations(self, signals) -> List[Dict]:
        """Evaluate escalations from deal data"""
        return []  # Placeholder

    async def _gather_industry_intelligence(self) -> List[Dict]:
        """Gather industry intelligence"""
        return []  # Placeholder

    async def _evaluate_competitive_escalations(self, signals) -> List[Dict]:
        """Evaluate competitive escalations"""
        return []  # Placeholder

    async def _apply_escalation(self, escalation: Dict):
        """Apply an escalation"""
        pass  # Placeholder

    async def _log_auto_escalation(self, escalation: Dict):
        """Log an auto-escalation"""
        logger.info(f"Auto-escalation applied: {escalation}")

    async def _check_gong_urgency(self, activity_data: Dict) -> float:
        """Check Gong for customer urgency"""
        return 0.5  # Placeholder

    async def _check_deal_dependencies(self, activity_data: Dict) -> Dict:
        """Check HubSpot for deal dependencies"""
        return {"total_value": 0}  # Placeholder

    async def _check_competitive_landscape(self, activity_data: Dict) -> Dict:
        """Check competitive landscape"""
        return {"severity": "low"}  # Placeholder

    async def _get_project_revenue(self, project_id: str) -> float:
        """Get revenue estimate for a project"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval(
                    """
                    SELECT COALESCE(estimated_revenue_impact, 0)
                    FROM projects 
                    WHERE id = $1
                """,
                    project_id,
                )
                return result or 0
        except Exception as e:
            logger.error(f"Error getting project revenue: {str(e)}")
            return 0
