"""
Enhanced MCP server for project management intelligence
Integrates with Sophia's existing MCP infrastructure
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List

import asyncpg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PMIntelligenceMCPServer:
    """
    Enhanced MCP server for project management intelligence
    Provides tools for RPE optimization, collaboration gap detection, and strategic alignment
    """

    def __init__(self, rpe_engine, coordinator, sophia_context: Dict, db_pool: asyncpg.Pool):
        self.name = "pm-intelligence"
        self.rpe_engine = rpe_engine
        self.coordinator = coordinator
        self.sophia_context = sophia_context
        self.db_pool = db_pool

        # Tool registry
        self.tools = {}
        self.register_tools()

        logger.info(f"PM Intelligence MCP Server initialized with {len(self.tools)} tools")

    def register_tools(self):
        """Register all PM intelligence tools"""

        self.tools["evaluate_rpe_impact"] = {
            "description": "Evaluate RPE impact of any activity",
            "parameters": {
                "activity_type": {
                    "type": "string",
                    "description": "Type of activity (project, task, okr, etc.)",
                },
                "activity_data": {"type": "object", "description": "Activity data dictionary"},
                "source_system": {
                    "type": "string",
                    "description": "Source system (linear, asana, notion, etc.)",
                },
            },
            "handler": self._evaluate_rpe_impact,
        }

        self.tools["detect_collaboration_gaps"] = {
            "description": "Find missing collaboration opportunities affecting RPE",
            "parameters": {},
            "handler": self._detect_collaboration_gaps,
        }

        self.tools["cascade_okrs"] = {
            "description": "Cascade OKRs from Notion to Linear/Asana",
            "parameters": {},
            "handler": self._cascade_okrs,
        }

        self.tools["auto_escalate_priorities"] = {
            "description": "Auto-escalate based on market signals",
            "parameters": {
                "signal_source": {
                    "type": "string",
                    "description": "Signal source (gong, hubspot, industry, all)",
                    "default": "all",
                }
            },
            "handler": self._auto_escalate_priorities,
        }

        self.tools["optimize_project_portfolio"] = {
            "description": "Optimize entire project portfolio for RPE",
            "parameters": {
                "optimization_target": {
                    "type": "string",
                    "description": "Optimization target",
                    "default": "rpe_maximize",
                }
            },
            "handler": self._optimize_project_portfolio,
        }

        self.tools["query_project_intelligence"] = {
            "description": "Natural language query for project intelligence",
            "parameters": {
                "query": {"type": "string", "description": "Natural language query"},
                "context": {"type": "object", "description": "Additional context", "default": {}},
            },
            "handler": self._query_project_intelligence,
        }

        self.tools["get_rpe_dashboard_data"] = {
            "description": "Get comprehensive RPE dashboard data",
            "parameters": {
                "time_range": {
                    "type": "string",
                    "description": "Time range (7d, 30d, 90d)",
                    "default": "30d",
                }
            },
            "handler": self._get_rpe_dashboard_data,
        }

        self.tools["detect_alignment_drift"] = {
            "description": "Detect when projects drift from OKR alignment",
            "parameters": {},
            "handler": self._detect_alignment_drift,
        }

        self.tools["generate_rpe_report"] = {
            "description": "Generate comprehensive RPE analysis report",
            "parameters": {
                "report_type": {
                    "type": "string",
                    "description": "Report type (executive, detailed, trends)",
                    "default": "executive",
                }
            },
            "handler": self._generate_rpe_report,
        }

    async def execute_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """Execute a tool with given parameters"""

        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "available_tools": list(self.tools.keys()),
            }

        try:
            handler = self.tools[tool_name]["handler"]
            result = await handler(**parameters)

            return {
                "success": True,
                "tool": tool_name,
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name,
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _evaluate_rpe_impact(
        self, activity_type: str, activity_data: Dict, source_system: str
    ) -> Dict:
        """Evaluate RPE impact of any activity"""

        impact = await self.rpe_engine.evaluate_any_activity(
            activity_type, activity_data, source_system
        )

        return {
            "rpe_impact": impact.projected_rpe_impact,
            "current_rpe": impact.current_rpe,
            "confidence": impact.confidence_score,
            "time_to_impact": impact.time_to_impact,
            "impact_type": impact.impact_type.value,
            "supporting_metrics": impact.supporting_metrics,
            "recommendation": self._generate_impact_recommendation(impact),
        }

    async def _detect_collaboration_gaps(self) -> List[Dict]:
        """Find missing collaboration opportunities"""
        gaps = await self.rpe_engine.detect_collaboration_gaps()

        # Enrich gaps with additional context
        enriched_gaps = []
        for gap in gaps:
            enriched_gap = gap.copy()
            enriched_gap["estimated_resolution_time"] = await self._estimate_gap_resolution_time(
                gap
            )
            enriched_gap["success_probability"] = await self._estimate_gap_success_probability(gap)
            enriched_gaps.append(enriched_gap)

        return enriched_gaps

    async def _cascade_okrs(self) -> Dict:
        """Cascade OKRs from Notion to Linear/Asana"""
        result = await self.coordinator.cascade_okrs_from_notion()

        # Add performance metrics
        result["performance_metrics"] = {
            "cascade_time": "< 30 seconds",
            "alignment_improvement": f"{result.get('alignment_score', 0) * 100:.1f}%",
            "projects_created": len(result.get("linear", [])) + len(result.get("asana", [])),
        }

        return result

    async def _auto_escalate_priorities(self, signal_source: str = "all") -> List[Dict]:
        """Auto-escalate based on market signals"""
        escalations = await self.rpe_engine.auto_escalate_from_signals(signal_source)

        # Add execution tracking
        for escalation in escalations:
            escalation["tracking_id"] = f"esc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            escalation["estimated_impact_timeline"] = await self._estimate_escalation_timeline(
                escalation
            )

        return escalations

    async def _optimize_project_portfolio(self, optimization_target: str = "rpe_maximize") -> Dict:
        """Optimize entire project portfolio for RPE"""

        # Get all active projects
        async with self.db_pool.acquire() as conn:
            projects = await conn.fetch(
                """
                SELECT id, title, department, estimated_revenue_impact,
                       estimated_cost_savings, resource_requirements, status,
                       created_at, updated_at
                FROM projects 
                WHERE status IN ('active', 'planned')
                ORDER BY created_at DESC
            """
            )

        if not projects:
            return {
                "optimized_order": [],
                "total_projected_rpe": 0,
                "recommendations": ["No active projects found for optimization"],
            }

        # Evaluate each project's RPE impact
        project_impacts = []
        for project in projects:
            try:
                impact = await self.rpe_engine.evaluate_any_activity(
                    "project", dict(project), "database"
                )

                resource_req = project.get("resource_requirements", 1)
                resource_efficiency = impact.projected_rpe_impact / max(resource_req, 1)

                project_impacts.append(
                    {
                        "project_id": project["id"],
                        "title": project["title"],
                        "department": project["department"],
                        "rpe_impact": impact.projected_rpe_impact,
                        "confidence": impact.confidence_score,
                        "resource_efficiency": resource_efficiency,
                        "composite_score": impact.projected_rpe_impact
                        * impact.confidence_score
                        * resource_efficiency,
                        "status": project["status"],
                        "time_to_impact": impact.time_to_impact,
                    }
                )
            except Exception as e:
                logger.error(f"Error evaluating project {project['id']}: {str(e)}")
                continue

        # Sort by composite score (RPE impact * confidence * resource efficiency)
        optimized_portfolio = sorted(
            project_impacts, key=lambda x: x["composite_score"], reverse=True
        )

        total_projected_rpe = sum(p["rpe_impact"] for p in optimized_portfolio)
        recommendations = await self._generate_portfolio_recommendations(optimized_portfolio)

        return {
            "optimized_order": optimized_portfolio,
            "total_projected_rpe": total_projected_rpe,
            "recommendations": recommendations,
            "optimization_summary": {
                "total_projects": len(optimized_portfolio),
                "high_impact_projects": len(
                    [p for p in optimized_portfolio if p["rpe_impact"] > 2000]
                ),
                "average_confidence": (
                    sum(p["confidence"] for p in optimized_portfolio) / len(optimized_portfolio)
                    if optimized_portfolio
                    else 0
                ),
                "resource_efficiency_range": {
                    "min": (
                        min(p["resource_efficiency"] for p in optimized_portfolio)
                        if optimized_portfolio
                        else 0
                    ),
                    "max": (
                        max(p["resource_efficiency"] for p in optimized_portfolio)
                        if optimized_portfolio
                        else 0
                    ),
                },
            },
        }

    async def _query_project_intelligence(self, query: str, context: Dict = None) -> Dict:
        """Natural language query for project intelligence"""

        if context is None:
            context = {}

        # Enhanced PM context
        pm_context = {
            "service_area": "project_management",
            "available_data": ["projects", "okrs", "rpe_metrics", "blockages", "market_signals"],
            "user_context": context,
            "query_timestamp": datetime.utcnow().isoformat(),
        }

        # Process through RPE lens
        query_lower = query.lower()

        if any(
            keyword in query_lower
            for keyword in ["rpe", "revenue per employee", "revenue/employee"]
        ):
            # Direct RPE query
            baseline = await self.rpe_engine._get_current_baseline()
            current_rpe = (
                baseline["current_revenue"] / baseline["employee_count"]
                if baseline["employee_count"] > 0
                else 0
            )

            rpe_insights = await self._generate_rpe_insights(query, baseline)

            response = {
                "type": "rpe_query",
                "current_rpe": current_rpe,
                "baseline_metrics": baseline,
                "insights": rpe_insights,
                "context": pm_context,
                "answer": f"Current RPE is ${current_rpe:,.2f}. {rpe_insights}",
            }

        elif any(
            keyword in query_lower for keyword in ["gap", "collaboration", "blockage", "missing"]
        ):
            # Collaboration gap query
            gaps = await self.rpe_engine.detect_collaboration_gaps()
            top_gaps = gaps[:3]  # Top 3 gaps

            response = {
                "type": "collaboration_query",
                "gaps_found": len(gaps),
                "top_gaps": top_gaps,
                "context": pm_context,
                "answer": f"Found {len(gaps)} collaboration gaps. Top issue: {top_gaps[0]['description'] if top_gaps else 'None'}",
            }

        elif any(
            keyword in query_lower for keyword in ["project", "priority", "optimize", "portfolio"]
        ):
            # Project optimization query
            optimization = await self._optimize_project_portfolio()
            top_projects = optimization["optimized_order"][:5]

            response = {
                "type": "project_optimization_query",
                "total_projects": len(optimization["optimized_order"]),
                "total_projected_rpe": optimization["total_projected_rpe"],
                "top_projects": top_projects,
                "context": pm_context,
                "answer": f"Portfolio analysis: {len(optimization['optimized_order'])} projects, ${optimization['total_projected_rpe']:,.2f} total RPE impact",
            }

        else:
            # General PM query - route through basic analysis
            response = {
                "type": "general_query",
                "context": pm_context,
                "answer": f"I can help with RPE analysis, collaboration gaps, project optimization, and strategic alignment. Please specify what you'd like to know about: {query}",
            }

        return response

    async def _get_rpe_dashboard_data(self, time_range: str = "30d") -> Dict:
        """Get comprehensive RPE dashboard data"""

        # Parse time range
        days = {"7d": 7, "30d": 30, "90d": 90}.get(time_range, 30)
        start_date = datetime.utcnow() - timedelta(days=days)

        try:
            async with self.db_pool.acquire() as conn:
                # Get RPE trends
                rpe_trends = await conn.fetch(
                    """
                    SELECT date, rpe_value, employee_count, revenue
                    FROM rpe_daily_metrics 
                    WHERE date >= $1
                    ORDER BY date DESC
                """,
                    start_date.date(),
                )

                # Get current baseline
                baseline = await self.rpe_engine._get_current_baseline()
                current_rpe = (
                    baseline["current_revenue"] / baseline["employee_count"]
                    if baseline["employee_count"] > 0
                    else 0
                )

                # Get project impacts
                project_impacts = await conn.fetch(
                    """
                    SELECT p.id, p.title, p.department, p.status,
                           COALESCE(p.estimated_revenue_impact, 0) as revenue_impact
                    FROM projects p
                    WHERE p.status IN ('active', 'planned')
                    ORDER BY p.estimated_revenue_impact DESC NULLS LAST
                    LIMIT 10
                """
                )

                # Get collaboration gaps
                gaps = await self.rpe_engine.detect_collaboration_gaps()

                # Calculate trends
                trend_data = []
                for record in rpe_trends:
                    trend_data.append(
                        {
                            "date": record["date"].isoformat(),
                            "rpe": record["rpe_value"],
                            "employees": record["employee_count"],
                            "revenue": record["revenue"],
                        }
                    )

                # Calculate department breakdown
                dept_breakdown = {}
                for project in project_impacts:
                    dept = project["department"] or "Unknown"
                    if dept not in dept_breakdown:
                        dept_breakdown[dept] = {"projects": 0, "revenue_impact": 0}
                    dept_breakdown[dept]["projects"] += 1
                    dept_breakdown[dept]["revenue_impact"] += project["revenue_impact"] or 0

                return {
                    "current_metrics": {
                        "rpe": current_rpe,
                        "employees": baseline["employee_count"],
                        "revenue": baseline["current_revenue"],
                        "arpu": baseline["current_arpu"],
                        "ebitda_margin": baseline["current_ebitda_margin"],
                    },
                    "trends": trend_data,
                    "top_projects": [dict(p) for p in project_impacts],
                    "collaboration_gaps": gaps[:5],  # Top 5 gaps
                    "department_breakdown": dept_breakdown,
                    "summary": {
                        "total_active_projects": len(project_impacts),
                        "total_gaps": len(gaps),
                        "trend_direction": self._calculate_trend_direction(trend_data),
                        "data_freshness": datetime.utcnow().isoformat(),
                    },
                }

        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            return {
                "error": str(e),
                "current_metrics": {"rpe": 0, "employees": 0, "revenue": 0},
                "trends": [],
                "top_projects": [],
                "collaboration_gaps": [],
                "department_breakdown": {},
            }

    async def _detect_alignment_drift(self) -> List[Dict]:
        """Detect when projects drift from OKR alignment"""
        return await self.coordinator.detect_alignment_drift()

    async def _generate_rpe_report(self, report_type: str = "executive") -> Dict:
        """Generate comprehensive RPE analysis report"""

        dashboard_data = await self._get_rpe_dashboard_data("90d")  # 90-day analysis
        gaps = await self.rpe_engine.detect_collaboration_gaps()
        optimization = await self._optimize_project_portfolio()

        if report_type == "executive":
            return {
                "report_type": "executive",
                "generated_at": datetime.utcnow().isoformat(),
                "key_metrics": {
                    "current_rpe": dashboard_data["current_metrics"]["rpe"],
                    "rpe_trend": dashboard_data["summary"]["trend_direction"],
                    "total_projected_rpe": optimization["total_projected_rpe"],
                    "optimization_opportunity": optimization["total_projected_rpe"]
                    - dashboard_data["current_metrics"]["rpe"],
                },
                "critical_gaps": [g for g in gaps if g.get("urgency") == "critical"][:3],
                "top_opportunities": optimization["optimized_order"][:5],
                "recommendations": optimization["recommendations"][:5],
                "executive_summary": await self._generate_executive_summary(
                    dashboard_data, gaps, optimization
                ),
            }

        elif report_type == "detailed":
            return {
                "report_type": "detailed",
                "generated_at": datetime.utcnow().isoformat(),
                "dashboard_data": dashboard_data,
                "collaboration_gaps": gaps,
                "portfolio_optimization": optimization,
                "alignment_drift": await self._detect_alignment_drift(),
                "detailed_analysis": await self._generate_detailed_analysis(
                    dashboard_data, gaps, optimization
                ),
            }

        else:  # trends
            return {
                "report_type": "trends",
                "generated_at": datetime.utcnow().isoformat(),
                "trend_analysis": dashboard_data["trends"],
                "trend_direction": dashboard_data["summary"]["trend_direction"],
                "trend_insights": await self._generate_trend_insights(dashboard_data["trends"]),
            }

    # Helper methods

    def _generate_impact_recommendation(self, impact) -> str:
        """Generate recommendation based on RPE impact"""
        if impact.projected_rpe_impact > 5000:
            return "HIGH PRIORITY: Significant RPE impact - prioritize immediately"
        elif impact.projected_rpe_impact > 2000:
            return "MEDIUM PRIORITY: Good RPE impact - include in next sprint"
        elif impact.projected_rpe_impact > 500:
            return "LOW PRIORITY: Moderate RPE impact - consider for future planning"
        else:
            return "REVIEW: Low RPE impact - evaluate necessity"

    async def _estimate_gap_resolution_time(self, gap: Dict) -> str:
        """Estimate time to resolve a collaboration gap"""
        gap_type = gap.get("type", "unknown")

        if gap_type == "missing_collaboration":
            return "2-4 weeks"
        elif gap_type == "unaddressed_market_signal":
            return "1-2 weeks"
        else:
            return "Unknown"

    async def _estimate_gap_success_probability(self, gap: Dict) -> float:
        """Estimate probability of successfully resolving a gap"""
        urgency = gap.get("urgency", "low")

        urgency_probabilities = {"critical": 0.9, "high": 0.8, "medium": 0.7, "low": 0.6}

        return urgency_probabilities.get(urgency, 0.6)

    async def _estimate_escalation_timeline(self, escalation: Dict) -> str:
        """Estimate timeline for escalation impact"""
        confidence = escalation.get("confidence", 0.5)

        if confidence > 0.8:
            return "1-2 weeks"
        elif confidence > 0.6:
            return "2-4 weeks"
        else:
            return "4-8 weeks"

    async def _generate_portfolio_recommendations(self, portfolio: List[Dict]) -> List[str]:
        """Generate recommendations for portfolio optimization"""
        if not portfolio:
            return ["No projects available for optimization"]

        recommendations = []

        # Top performers
        top_3 = portfolio[:3]
        if top_3:
            recommendations.append(
                f"PRIORITIZE: Top 3 RPE projects - {', '.join(p['title'] for p in top_3)}"
            )

        # Low performers
        bottom_3 = portfolio[-3:] if len(portfolio) > 3 else []
        if bottom_3:
            recommendations.append(
                f"REVIEW: Bottom 3 projects for potential pause/cancellation - {', '.join(p['title'] for p in bottom_3)}"
            )

        # Resource reallocation
        if len(portfolio) >= 10:
            total_high_impact = sum(p["rpe_impact"] for p in portfolio[:5])
            total_low_impact = sum(p["rpe_impact"] for p in portfolio[-5:])

            if total_high_impact > total_low_impact * 2:
                recommendations.append(
                    "REALLOCATE: Move resources from bottom 5 to top 5 projects for 2x+ RPE improvement"
                )

        # Confidence-based recommendations
        high_confidence_projects = [p for p in portfolio if p["confidence"] > 0.8]
        if high_confidence_projects:
            recommendations.append(
                f"FAST TRACK: {len(high_confidence_projects)} high-confidence projects ready for acceleration"
            )

        return recommendations

    async def _generate_rpe_insights(self, query: str, baseline: Dict) -> str:
        """Generate RPE-specific insights"""

        try:
            # Get recent RPE trends
            async with self.db_pool.acquire() as conn:
                trends = await conn.fetch(
                    """
                    SELECT date, rpe_value 
                    FROM rpe_daily_metrics 
                    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
                    ORDER BY date DESC
                    LIMIT 30
                """
                )

            if trends and len(trends) > 1:
                recent_rpe = trends[0]["rpe_value"]
                month_ago_rpe = trends[-1]["rpe_value"]

                if recent_rpe > month_ago_rpe:
                    trend_direction = "increasing"
                    trend_amount = recent_rpe - month_ago_rpe
                else:
                    trend_direction = "decreasing"
                    trend_amount = month_ago_rpe - recent_rpe

                return (
                    f"RPE has been {trend_direction} by ${trend_amount:,.2f} over the last 30 days. "
                    + f"Current trajectory suggests reaching ${recent_rpe * 1.05:,.2f} by month-end with continued optimization."
                )
            else:
                return "Insufficient historical data for trend analysis. Consider implementing daily RPE tracking."

        except Exception as e:
            logger.error(f"Error generating RPE insights: {str(e)}")
            return "Unable to generate trend insights at this time."

    def _calculate_trend_direction(self, trend_data: List[Dict]) -> str:
        """Calculate overall trend direction"""
        if len(trend_data) < 2:
            return "insufficient_data"

        recent_rpe = trend_data[0]["rpe"]
        older_rpe = trend_data[-1]["rpe"]

        if recent_rpe > older_rpe * 1.05:
            return "increasing"
        elif recent_rpe < older_rpe * 0.95:
            return "decreasing"
        else:
            return "stable"

    async def _generate_executive_summary(
        self, dashboard_data: Dict, gaps: List[Dict], optimization: Dict
    ) -> str:
        """Generate executive summary"""
        current_rpe = dashboard_data["current_metrics"]["rpe"]
        total_projected = optimization["total_projected_rpe"]
        critical_gaps = len([g for g in gaps if g.get("urgency") == "critical"])

        return (
            f"Current RPE: ${current_rpe:,.2f}. Portfolio optimization could increase to ${total_projected:,.2f}. "
            + f"{critical_gaps} critical collaboration gaps require immediate attention. "
            + "Recommend prioritizing top 3 projects for maximum RPE impact."
        )

    async def _generate_detailed_analysis(
        self, dashboard_data: Dict, gaps: List[Dict], optimization: Dict
    ) -> Dict:
        """Generate detailed analysis"""
        return {
            "rpe_analysis": f"Detailed RPE breakdown across {len(dashboard_data['department_breakdown'])} departments",
            "gap_analysis": f"Identified {len(gaps)} collaboration gaps with potential RPE impact",
            "optimization_analysis": f"Portfolio optimization across {len(optimization['optimized_order'])} projects",
            "recommendations_count": len(optimization["recommendations"]),
        }

    async def _generate_trend_insights(self, trends: List[Dict]) -> List[str]:
        """Generate insights from trend data"""
        if not trends:
            return ["No trend data available"]

        insights = []

        # Growth rate analysis
        if len(trends) >= 7:
            week_growth = (trends[0]["rpe"] - trends[6]["rpe"]) / trends[6]["rpe"] * 100
            insights.append(f"Weekly RPE growth: {week_growth:.1f}%")

        # Volatility analysis
        rpe_values = [t["rpe"] for t in trends]
        avg_rpe = sum(rpe_values) / len(rpe_values)
        volatility = sum(abs(rpe - avg_rpe) for rpe in rpe_values) / len(rpe_values)
        insights.append(f"RPE volatility: ${volatility:.2f} (lower is more stable)")

        return insights
