"""
Sophia Semantic Business Intelligence Orchestrator
==================================================

Enhanced Sophia orchestrator with semantic understanding, multi-source
data gathering, insight synthesis, and advanced analytics capabilities.

AI Context:
- Semantic business layer for intelligent data interpretation
- Multi-source data aggregation and correlation
- Advanced insight synthesis with confidence scoring
- Dynamic persona adaptation for different business contexts
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from app.integrations.connectors.base_connector import BaseConnector
from app.memory.unified_memory_router import MemoryDomain, UnifiedMemoryRouter
from app.orchestrators.base_orchestrator import (
    BaseOrchestrator,
    OrchestratorConfig,
)
from app.scaffolding.embedding_system import (
    EmbeddingConfig,
    EmbeddingType,
    MultiModalEmbeddingSystem,
)
from app.scaffolding.persona_manager import (
    PersonaContext,
    get_persona_manager,
)
from app.sophia.sophia_orchestrator import BusinessContext, InsightReport

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Types of data sources Sophia can access"""

    CRM = "crm"  # Salesforce, HubSpot, etc.
    ERP = "erp"  # SAP, Oracle, etc.
    ANALYTICS = "analytics"  # Google Analytics, Mixpanel, etc.
    FINANCIAL = "financial"  # QuickBooks, Xero, etc.
    COMMUNICATION = "communication"  # Gong, Chorus, etc.
    MARKET = "market"  # Market research APIs
    SOCIAL = "social"  # Social media analytics
    CUSTOM = "custom"  # Custom data sources


class InsightType(Enum):
    """Types of insights Sophia can generate"""

    TREND = "trend"
    ANOMALY = "anomaly"
    CORRELATION = "correlation"
    PREDICTION = "prediction"
    OPPORTUNITY = "opportunity"
    RISK = "risk"
    RECOMMENDATION = "recommendation"
    BENCHMARK = "benchmark"


@dataclass
class SemanticQuery:
    """Semantic query for business intelligence"""

    intent: str  # What the user wants to know
    entities: list[str]  # Key entities mentioned
    metrics: list[str]  # Metrics to analyze
    time_range: Optional[tuple[datetime, datetime]] = None
    filters: dict[str, Any] = field(default_factory=dict)
    comparison: Optional[str] = None  # e.g., "vs last quarter"
    granularity: str = "daily"  # daily, weekly, monthly, quarterly
    confidence_threshold: float = 0.7


@dataclass
class DataGatheringPlan:
    """Plan for gathering data from multiple sources"""

    sources: list[DataSourceType]
    queries: dict[DataSourceType, list[str]]
    priority: dict[DataSourceType, int]
    dependencies: dict[str, list[str]]
    timeout_s: int = 60
    parallel: bool = True


@dataclass
class SemanticInsight:
    """Enhanced insight with semantic understanding"""

    type: InsightType
    title: str
    description: str
    impact: str  # Business impact description
    confidence: float
    supporting_data: list[dict[str, Any]]
    visualizations: list[dict[str, Any]]
    actions: list[str]  # Recommended actions
    related_insights: list[str]  # IDs of related insights
    semantic_tags: set[str]
    timestamp: datetime = field(default_factory=datetime.now)


class SemanticBusinessLayer:
    """Semantic layer for business intelligence understanding"""

    def __init__(self, orchestrator: "SophiaSemanticOrchestrator"):
        self.orchestrator = orchestrator
        self.business_ontology = self._load_business_ontology()
        self.metric_definitions = self._load_metric_definitions()
        self.industry_benchmarks = {}

    def _load_business_ontology(self) -> dict[str, Any]:
        """Load business domain ontology"""
        return {
            "sales": {
                "entities": ["opportunity", "lead", "account", "contact", "deal"],
                "metrics": ["revenue", "pipeline", "conversion_rate", "acv", "arr"],
                "relationships": {
                    "opportunity": ["account", "contact"],
                    "deal": ["opportunity", "account"],
                },
            },
            "marketing": {
                "entities": ["campaign", "channel", "segment", "persona"],
                "metrics": ["cac", "ltv", "roi", "attribution", "engagement"],
            },
            "finance": {
                "entities": ["invoice", "expense", "budget", "forecast"],
                "metrics": ["revenue", "profit", "margin", "cash_flow", "burn_rate"],
            },
            "customer": {
                "entities": ["customer", "segment", "cohort", "journey"],
                "metrics": [
                    "satisfaction",
                    "nps",
                    "churn",
                    "retention",
                    "health_score",
                ],
            },
        }

    def _load_metric_definitions(self) -> dict[str, Any]:
        """Load standard metric definitions"""
        return {
            "arr": {
                "name": "Annual Recurring Revenue",
                "formula": "monthly_recurring_revenue * 12",
                "category": "revenue",
                "aggregation": "sum",
            },
            "cac": {
                "name": "Customer Acquisition Cost",
                "formula": "total_sales_marketing_cost / new_customers",
                "category": "efficiency",
                "aggregation": "average",
            },
            "ltv": {
                "name": "Customer Lifetime Value",
                "formula": "average_revenue_per_user * average_customer_lifetime",
                "category": "customer",
                "aggregation": "average",
            },
            "nps": {
                "name": "Net Promoter Score",
                "formula": "promoters_pct - detractors_pct",
                "category": "satisfaction",
                "aggregation": "average",
            },
        }

    def parse_natural_query(self, query: str) -> SemanticQuery:
        """Parse natural language query into semantic query"""
        # Extract entities and metrics
        entities = []
        metrics = []

        query_lower = query.lower()

        # Check against ontology
        for _domain, info in self.business_ontology.items():
            for entity in info["entities"]:
                if entity in query_lower:
                    entities.append(entity)
            for metric in info["metrics"]:
                if metric in query_lower:
                    metrics.append(metric)

        # Extract time range
        time_range = self._extract_time_range(query)

        # Detect comparison
        comparison = None
        if "vs" in query_lower or "compared to" in query_lower:
            comparison = self._extract_comparison(query)

        return SemanticQuery(
            intent=query,
            entities=entities,
            metrics=metrics,
            time_range=time_range,
            comparison=comparison,
        )

    def _extract_time_range(self, query: str) -> Optional[tuple[datetime, datetime]]:
        """Extract time range from query"""
        now = datetime.now()
        query_lower = query.lower()

        if "last quarter" in query_lower:
            end = now
            start = now - timedelta(days=90)
            return (start, end)
        elif "last month" in query_lower:
            end = now
            start = now - timedelta(days=30)
            return (start, end)
        elif "last year" in query_lower:
            end = now
            start = now - timedelta(days=365)
            return (start, end)
        elif "ytd" in query_lower or "year to date" in query_lower:
            start = datetime(now.year, 1, 1)
            return (start, now)

        return None

    def _extract_comparison(self, query: str) -> str:
        """Extract comparison period from query"""
        query_lower = query.lower()

        if "last quarter" in query_lower:
            return "previous_quarter"
        elif "last year" in query_lower:
            return "previous_year"
        elif "last month" in query_lower:
            return "previous_month"

        return "previous_period"

    def enrich_with_context(
        self, query: SemanticQuery, business_context: BusinessContext
    ) -> SemanticQuery:
        """Enrich query with business context"""
        # Add industry-specific metrics
        if business_context.industry == "saas":
            if "revenue" in query.metrics and "arr" not in query.metrics:
                query.metrics.append("arr")
            if "customer" in query.entities and "churn" not in query.metrics:
                query.metrics.append("churn")

        # Add compliance-related filters
        if "gdpr" in business_context.compliance_requirements:
            query.filters["data_privacy"] = "gdpr_compliant"

        return query


class InsightSynthesizer:
    """Synthesizes insights from multiple data sources"""

    def __init__(self, orchestrator: "SophiaSemanticOrchestrator"):
        self.orchestrator = orchestrator
        self.insight_patterns = self._load_insight_patterns()

    def _load_insight_patterns(self) -> dict[InsightType, Any]:
        """Load patterns for different insight types"""
        return {
            InsightType.TREND: {
                "min_data_points": 7,
                "statistical_tests": ["mann_kendall", "linear_regression"],
                "visualization": "line_chart",
            },
            InsightType.ANOMALY: {
                "methods": ["isolation_forest", "z_score", "iqr"],
                "visualization": "scatter_plot",
            },
            InsightType.CORRELATION: {
                "methods": ["pearson", "spearman"],
                "min_correlation": 0.5,
                "visualization": "heatmap",
            },
            InsightType.PREDICTION: {
                "models": ["arima", "prophet", "lstm"],
                "validation": "time_series_cv",
                "visualization": "forecast_chart",
            },
        }

    async def synthesize(
        self,
        data_sources: dict[DataSourceType, Any],
        semantic_query: SemanticQuery,
    ) -> list[SemanticInsight]:
        """Synthesize insights from multiple data sources"""
        insights = []

        # Detect trends
        trend_insights = await self._detect_trends(data_sources, semantic_query)
        insights.extend(trend_insights)

        # Detect anomalies
        anomaly_insights = await self._detect_anomalies(data_sources, semantic_query)
        insights.extend(anomaly_insights)

        # Find correlations
        correlation_insights = await self._find_correlations(
            data_sources, semantic_query
        )
        insights.extend(correlation_insights)

        # Generate predictions if enough data
        if self._has_sufficient_data(data_sources):
            prediction_insights = await self._generate_predictions(
                data_sources, semantic_query
            )
            insights.extend(prediction_insights)

        # Identify opportunities and risks
        opportunity_insights = await self._identify_opportunities(
            data_sources, semantic_query, insights
        )
        insights.extend(opportunity_insights)

        # Cross-reference and validate insights
        validated_insights = self._validate_insights(insights)

        # Rank by impact and confidence
        ranked_insights = self._rank_insights(validated_insights)

        return ranked_insights

    async def _detect_trends(
        self, data_sources: dict[DataSourceType, Any], query: SemanticQuery
    ) -> list[SemanticInsight]:
        """Detect trends in data"""
        insights = []

        for metric in query.metrics:
            # Analyze metric trends across sources
            trend_data = self._extract_metric_data(data_sources, metric)

            if len(trend_data) >= 7:  # Minimum data points
                trend_direction = self._calculate_trend(trend_data)

                if abs(trend_direction) > 0.1:  # Significant trend
                    insight = SemanticInsight(
                        type=InsightType.TREND,
                        title=f"{metric.upper()} Trending {'Up' if trend_direction > 0 else 'Down'}",
                        description=f"{metric} has shown a {abs(trend_direction)*100:.1f}% "
                        f"{'increase' if trend_direction > 0 else 'decrease'} over the period",
                        impact=self._assess_trend_impact(metric, trend_direction),
                        confidence=0.85,
                        supporting_data=[{"metric": metric, "trend": trend_direction}],
                        visualizations=[
                            {
                                "type": "line_chart",
                                "data": trend_data,
                            }
                        ],
                        actions=self._generate_trend_actions(metric, trend_direction),
                        semantic_tags={
                            metric,
                            "trend",
                            query.entities[0] if query.entities else "general",
                        },
                    )
                    insights.append(insight)

        return insights

    async def _detect_anomalies(
        self, data_sources: dict[DataSourceType, Any], query: SemanticQuery
    ) -> list[SemanticInsight]:
        """Detect anomalies in data"""
        insights = []

        # Implementation would use statistical methods or ML models
        # This is a simplified version

        return insights

    async def _find_correlations(
        self, data_sources: dict[DataSourceType, Any], query: SemanticQuery
    ) -> list[SemanticInsight]:
        """Find correlations between metrics"""
        insights = []

        # Implementation would calculate correlations
        # This is a simplified version

        return insights

    async def _generate_predictions(
        self, data_sources: dict[DataSourceType, Any], query: SemanticQuery
    ) -> list[SemanticInsight]:
        """Generate predictive insights"""
        insights = []

        # Implementation would use time series models
        # This is a simplified version

        return insights

    async def _identify_opportunities(
        self,
        data_sources: dict[DataSourceType, Any],
        query: SemanticQuery,
        existing_insights: list[SemanticInsight],
    ) -> list[SemanticInsight]:
        """Identify business opportunities"""
        insights = []

        # Analyze existing insights for opportunity patterns
        for insight in existing_insights:
            if insight.type == InsightType.TREND and "increase" in insight.description:
                opportunity = SemanticInsight(
                    type=InsightType.OPPORTUNITY,
                    title=f"Growth Opportunity in {insight.semantic_tags}",
                    description="Based on positive trends, there's an opportunity to capitalize on growth",
                    impact="High potential for revenue increase",
                    confidence=insight.confidence * 0.8,
                    supporting_data=insight.supporting_data,
                    visualizations=[],
                    actions=["Increase investment", "Scale operations", "Expand team"],
                    related_insights=[insight.title],
                    semantic_tags=insight.semantic_tags | {"opportunity"},
                )
                insights.append(opportunity)

        return insights

    def _extract_metric_data(
        self, data_sources: dict[DataSourceType, Any], metric: str
    ) -> list[float]:
        """Extract metric data from sources"""
        # Simplified implementation
        return [float(i) for i in range(10)]  # Mock data

    def _calculate_trend(self, data: list[float]) -> float:
        """Calculate trend direction and strength"""
        # Simplified linear trend
        if not data:
            return 0.0
        return (data[-1] - data[0]) / (data[0] if data[0] != 0 else 1)

    def _assess_trend_impact(self, metric: str, trend: float) -> str:
        """Assess business impact of trend"""
        if abs(trend) > 0.3:
            return "Critical business impact requiring immediate attention"
        elif abs(trend) > 0.15:
            return "Significant impact on business operations"
        else:
            return "Moderate impact worth monitoring"

    def _generate_trend_actions(self, metric: str, trend: float) -> list[str]:
        """Generate recommended actions based on trend"""
        actions = []

        if trend > 0.2:
            actions.extend(
                [
                    f"Investigate drivers of {metric} growth",
                    "Consider scaling related operations",
                    "Update forecasts to reflect positive trend",
                ]
            )
        elif trend < -0.2:
            actions.extend(
                [
                    f"Identify root causes of {metric} decline",
                    "Implement corrective measures",
                    "Review and adjust strategy",
                ]
            )

        return actions

    def _has_sufficient_data(self, data_sources: dict[DataSourceType, Any]) -> bool:
        """Check if we have sufficient data for predictions"""
        # Simplified check
        return len(data_sources) >= 2

    def _validate_insights(
        self, insights: list[SemanticInsight]
    ) -> list[SemanticInsight]:
        """Validate and cross-reference insights"""
        validated = []

        for insight in insights:
            # Check for contradictions
            for other in insights:
                if other != insight and self._contradicts(insight, other):
                    insight.confidence *= 0.7  # Reduce confidence

            if insight.confidence >= 0.5:  # Minimum confidence threshold
                validated.append(insight)

        return validated

    def _contradicts(
        self, insight1: SemanticInsight, insight2: SemanticInsight
    ) -> bool:
        """Check if two insights contradict each other"""
        # Simplified contradiction check
        return False

    def _rank_insights(self, insights: list[SemanticInsight]) -> list[SemanticInsight]:
        """Rank insights by importance"""
        return sorted(
            insights,
            key=lambda i: (i.confidence, len(i.actions), len(i.supporting_data)),
            reverse=True,
        )


class SophiaSemanticOrchestrator(BaseOrchestrator):
    """
    Enhanced Sophia Orchestrator with Semantic Intelligence

    Features:
    - Semantic query understanding
    - Multi-source data aggregation
    - Advanced insight synthesis
    - Dynamic persona adaptation
    - Confidence-scored recommendations
    """

    def __init__(
        self,
        business_context: Optional[BusinessContext] = None,
        embedding_config: Optional[EmbeddingConfig] = None,
    ):
        """Initialize enhanced Sophia orchestrator"""

        config = OrchestratorConfig(
            domain=MemoryDomain.SOPHIA,
            name="Sophia Semantic Intelligence",
            description="Advanced semantic BI orchestrator with multi-source synthesis",
            max_concurrent_tasks=10,
            default_timeout_s=300,
            enable_caching=True,
            enable_monitoring=True,
            enable_memory=True,
            budget_limits={
                "hourly_cost_usd": 100.0,
                "daily_cost_usd": 1000.0,
                "monthly_cost_usd": 20000.0,
            },
        )

        super().__init__(config)

        self.business_context = business_context or self._get_default_business_context()

        # Semantic components
        self.semantic_layer = SemanticBusinessLayer(self)
        self.insight_synthesizer = InsightSynthesizer(self)

        # Embedding system for semantic search
        embedding_config = embedding_config or EmbeddingConfig(
            model="text-embedding-3-large",
            dimensions=3072,
            chunk_size=1024,
        )
        self.embedding_system = MultiModalEmbeddingSystem(embedding_config)

        # Persona management
        self.persona_manager = get_persona_manager()
        self.active_persona = self.persona_manager.activate_persona("sophia")

        # Data source connectors
        self.data_sources: dict[DataSourceType, BaseConnector] = {}
        self._initialize_data_sources()

        # Cache for insights
        self.insight_cache: dict[str, SemanticInsight] = {}

        logger.info("Initialized Sophia Semantic Orchestrator")

    def _get_default_business_context(self) -> BusinessContext:
        """Get default business context"""
        return BusinessContext(
            industry="technology",
            company_size="enterprise",
            key_metrics=["revenue", "customers", "churn", "nps"],
            fiscal_year_start="01-01",
            currency="USD",
            time_zone="America/Los_Angeles",
            compliance_requirements=["sox", "gdpr"],
        )

    def _initialize_data_sources(self) -> None:
        """Initialize data source connectors"""
        # Would initialize actual connectors here
        # This is a placeholder
        pass

    async def process_query(
        self,
        query: str,
        context: Optional[dict[str, Any]] = None,
    ) -> InsightReport:
        """
        Process a business intelligence query

        Args:
            query: Natural language query
            context: Additional context for the query

        Returns:
            InsightReport with findings and recommendations
        """
        # Parse query semantically
        semantic_query = self.semantic_layer.parse_natural_query(query)

        # Enrich with business context
        semantic_query = self.semantic_layer.enrich_with_context(
            semantic_query, self.business_context
        )

        # Adapt persona based on query
        persona_context = PersonaContext(
            domain=self._determine_domain(semantic_query),
            task_type="business_analysis",
            user_expertise=(
                context.get("user_expertise", "intermediate")
                if context
                else "intermediate"
            ),
            constraints=["accuracy", "timeliness", "actionability"],
        )
        self.active_persona.adapt_to_context(persona_context)

        # Create data gathering plan
        gathering_plan = self._create_gathering_plan(semantic_query)

        # Gather data from multiple sources
        data_results = await self._gather_multi_source_data(gathering_plan)

        # Synthesize insights
        insights = await self.insight_synthesizer.synthesize(
            data_results, semantic_query
        )

        # Generate report
        report = self._generate_insight_report(semantic_query, insights, data_results)

        # Store in memory for future reference
        await self._store_in_memory(query, report, insights)

        # Update persona performance
        self.persona_manager.evaluate_persona_performance(
            "sophia",
            "business_analysis",
            {"accuracy": 0.85, "relevance": 0.9, "actionability": 0.8},
        )

        return report

    def _determine_domain(self, query: SemanticQuery) -> str:
        """Determine business domain from query"""
        if any(m in ["revenue", "profit", "cost"] for m in query.metrics):
            return "finance"
        elif any(m in ["cac", "ltv", "conversion"] for m in query.metrics):
            return "marketing"
        elif any(m in ["pipeline", "deals", "quota"] for m in query.metrics):
            return "sales"
        else:
            return "operations"

    def _create_gathering_plan(self, query: SemanticQuery) -> DataGatheringPlan:
        """Create plan for gathering data"""
        sources = []
        queries = {}

        # Determine relevant sources based on query
        if any(e in ["customer", "account", "contact"] for e in query.entities):
            sources.append(DataSourceType.CRM)
            queries[DataSourceType.CRM] = [
                f"SELECT * FROM {e} WHERE date >= '{query.time_range[0]}'"
                for e in query.entities
                if query.time_range
            ]

        if any(m in ["revenue", "profit", "expense"] for m in query.metrics):
            sources.append(DataSourceType.FINANCIAL)
            queries[DataSourceType.FINANCIAL] = [
                f"GET /metrics/{m}" for m in query.metrics
            ]

        if "campaign" in query.entities or "marketing" in str(query.intent):
            sources.append(DataSourceType.ANALYTICS)
            queries[DataSourceType.ANALYTICS] = ["GET /campaigns", "GET /attribution"]

        return DataGatheringPlan(
            sources=sources,
            queries=queries,
            priority={s: i for i, s in enumerate(sources)},
            dependencies={},
            parallel=True,
        )

    async def _gather_multi_source_data(
        self, plan: DataGatheringPlan
    ) -> dict[DataSourceType, Any]:
        """Gather data from multiple sources according to plan"""
        results = {}

        if plan.parallel:
            # Gather in parallel
            tasks = []
            for source in plan.sources:
                if source in self.data_sources:
                    task = self._fetch_from_source(source, plan.queries.get(source, []))
                    tasks.append(task)

            if tasks:
                gathered = await asyncio.gather(*tasks, return_exceptions=True)
                for i, source in enumerate(plan.sources):
                    if i < len(gathered) and not isinstance(gathered[i], Exception):
                        results[source] = gathered[i]
        else:
            # Gather sequentially
            for source in sorted(plan.sources, key=lambda s: plan.priority.get(s, 999)):
                if source in self.data_sources:
                    try:
                        data = await self._fetch_from_source(
                            source, plan.queries.get(source, [])
                        )
                        results[source] = data
                    except Exception as e:
                        logger.error(f"Failed to fetch from {source}: {e}")

        return results

    async def _fetch_from_source(
        self, source: DataSourceType, queries: list[str]
    ) -> Any:
        """Fetch data from a specific source"""
        # This would use actual connectors
        # Returning mock data for now
        return {
            "source": source.value,
            "data": [{"metric": "revenue", "value": 1000000}],
            "timestamp": datetime.now().isoformat(),
        }

    def _generate_insight_report(
        self,
        query: SemanticQuery,
        insights: list[SemanticInsight],
        data_sources: dict[DataSourceType, Any],
    ) -> InsightReport:
        """Generate comprehensive insight report"""

        # Create executive summary
        exec_summary = self._create_executive_summary(query, insights)

        # Extract key findings
        key_findings = [
            {
                "title": insight.title,
                "description": insight.description,
                "confidence": insight.confidence,
                "type": insight.type.value,
            }
            for insight in insights[:5]  # Top 5 insights
        ]

        # Generate recommendations
        recommendations = []
        for insight in insights:
            if insight.actions:
                recommendations.append(
                    {
                        "action": insight.actions[0],
                        "rationale": insight.description,
                        "priority": "high" if insight.confidence > 0.8 else "medium",
                        "effort": "medium",  # Would be calculated
                    }
                )

        # Identify risks
        risks = [
            {
                "risk": insight.title,
                "impact": insight.impact,
                "likelihood": insight.confidence,
            }
            for insight in insights
            if insight.type == InsightType.RISK
        ]

        # Identify opportunities
        opportunities = [
            {
                "opportunity": insight.title,
                "potential": insight.impact,
                "confidence": insight.confidence,
            }
            for insight in insights
            if insight.type == InsightType.OPPORTUNITY
        ]

        # Compile supporting data
        supporting_data = []
        for source, data in data_sources.items():
            supporting_data.append(
                {
                    "source": source.value,
                    "records": (
                        len(data.get("data", [])) if isinstance(data, dict) else 0
                    ),
                    "timestamp": (
                        data.get("timestamp") if isinstance(data, dict) else None
                    ),
                }
            )

        # Calculate overall confidence
        avg_confidence = (
            sum(i.confidence for i in insights) / len(insights) if insights else 0.5
        )

        return InsightReport(
            executive_summary=exec_summary,
            key_findings=key_findings,
            recommendations=recommendations,
            risks=risks,
            opportunities=opportunities,
            supporting_data=supporting_data,
            confidence_level=avg_confidence,
            data_sources=[s.value for s in data_sources],
        )

    def _create_executive_summary(
        self, query: SemanticQuery, insights: list[SemanticInsight]
    ) -> str:
        """Create executive summary from insights"""
        if not insights:
            return "No significant insights were found for the given query."

        summary = f"Analysis of {', '.join(query.metrics)} "

        if query.time_range:
            summary += (
                f"from {query.time_range[0].date()} to {query.time_range[1].date()} "
            )

        summary += f"reveals {len(insights)} key insights. "

        # Highlight top insight
        top_insight = insights[0]
        summary += f"Most notably, {top_insight.description.lower()}. "

        # Add overall sentiment
        positive_insights = sum(
            1 for i in insights if i.type == InsightType.OPPORTUNITY
        )
        negative_insights = sum(1 for i in insights if i.type == InsightType.RISK)

        if positive_insights > negative_insights:
            summary += (
                "Overall outlook is positive with significant growth opportunities."
            )
        elif negative_insights > positive_insights:
            summary += "Several risks require immediate attention and mitigation."
        else:
            summary += (
                "Mixed signals suggest careful monitoring and strategic adjustment."
            )

        return summary

    async def _store_in_memory(
        self,
        query: str,
        report: InsightReport,
        insights: list[SemanticInsight],
    ) -> None:
        """Store insights in memory for future reference"""
        memory_router = UnifiedMemoryRouter()

        # Store report
        await memory_router.store(
            key=f"report_{datetime.now().isoformat()}",
            data={
                "query": query,
                "report": report.__dict__,
                "timestamp": datetime.now().isoformat(),
            },
            domain=MemoryDomain.SOPHIA,
            ttl_seconds=86400 * 30,  # 30 days
        )

        # Store individual insights for semantic search
        for insight in insights:
            self.insight_cache[insight.title] = insight

            # Create embedding for semantic search
            await self.embedding_system.generator.generate_embedding(
                chunk={
                    "content": f"{insight.title} {insight.description}",
                    "metadata": {"type": "insight", "confidence": insight.confidence},
                },
                embedding_type=EmbeddingType.SEMANTIC,
            )
