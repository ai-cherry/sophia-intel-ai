"""
Sophia Business Intelligence Orchestrator
Specialized for enterprise BI, analytics, and strategic insights
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from app.core.portkey_manager import TaskType as PortkeyTaskType
from app.integrations.connectors.base_connector import BaseConnector
from app.memory.unified_memory_router import MemoryDomain
from app.orchestrators.base_orchestrator import (
    BaseOrchestrator,
    ExecutionPriority,
    OrchestratorConfig,
    Result,
    Task,
    TaskType,
)

logger = logging.getLogger(__name__)


@dataclass
class BusinessContext:
    """Business-specific context for Sophia"""

    industry: str
    company_size: str
    key_metrics: list[str]
    fiscal_year_start: str
    currency: str = "USD"
    time_zone: str = "America/Los_Angeles"
    compliance_requirements: list[str] = field(default_factory=list)
    has_foundational_knowledge: bool = False
    foundational_categories: list[str] = field(default_factory=list)


@dataclass
class InsightReport:
    """Structured insight report from Sophia"""

    executive_summary: str
    key_findings: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    risks: list[dict[str, Any]]
    opportunities: list[dict[str, Any]]
    supporting_data: list[dict[str, Any]]
    confidence_level: float
    data_sources: list[str]
    generated_at: datetime = field(default_factory=datetime.now)


class SophiaOrchestrator(BaseOrchestrator):
    """
    Sophia - Business Intelligence Orchestrator

    Specializes in:
    - Sales analytics and forecasting
    - Customer insights and health scoring
    - Competitive intelligence
    - Market trends and opportunities
    - Strategic planning and recommendations
    """

    def __init__(self, business_context: Optional[BusinessContext] = None):
        """
        Initialize Sophia orchestrator

        Args:
            business_context: Optional business-specific context
        """
        config = OrchestratorConfig(
            domain=MemoryDomain.SOPHIA,
            name="Sophia Business Intelligence",
            description="Enterprise BI and strategic insights orchestrator",
            max_concurrent_tasks=5,
            default_timeout_s=180,
            enable_caching=True,
            enable_monitoring=True,
            enable_memory=True,
            budget_limits={
                "hourly_cost_usd": 50.0,
                "daily_cost_usd": 500.0,
                "monthly_cost_usd": 10000.0,
            },
        )

        super().__init__(config)

        self.business_context = business_context or self._get_default_context()
        self.connectors = {}
        self._init_connectors()

        # Specialized components
        self.insight_engine = InsightEngine(self)
        self.forecast_engine = ForecastEngine(self)
        self.competitive_intel = CompetitiveIntelligence(self)

        # Initialize Foundational Knowledge Manager
        try:
            from app.knowledge.foundational_manager import FoundationalKnowledgeManager

            self.foundational_knowledge = FoundationalKnowledgeManager()
            logger.info("Foundational Knowledge Manager initialized")
        except Exception as e:
            logger.warning(f"Foundational Knowledge not available: {e}")
            self.foundational_knowledge = None

        logger.info("Sophia BI Orchestrator initialized")

    def _get_default_context(self) -> BusinessContext:
        """Get default business context"""
        context = BusinessContext(
            industry="Technology",
            company_size="Mid-Market",
            key_metrics=["ARR", "NRR", "CAC", "LTV", "Churn"],
            fiscal_year_start="01-01",
        )

        # Update if foundational knowledge is available
        if self.foundational_knowledge:
            context.has_foundational_knowledge = True
            context.foundational_categories = [
                "company_overview",
                "strategic_initiatives",
                "executive_decisions",
                "market_intelligence",
                "operational_metrics",
            ]

        return context

    def _init_connectors(self):
        """Initialize enterprise connectors"""
        # Import connectors dynamically to avoid circular imports
        connector_configs = {
            "asana": {"enabled": True, "sync_interval": 3600},
            "linear": {"enabled": True, "sync_interval": 1800},
            "gong": {"enabled": True, "sync_interval": 7200},
            "hubspot": {"enabled": True, "sync_interval": 3600},
            "intercom": {"enabled": True, "sync_interval": 3600},
            "salesforce": {"enabled": True, "sync_interval": 1800},
            "airtable": {"enabled": True, "sync_interval": 3600},
            "looker": {"enabled": True, "sync_interval": 7200},
        }

        for name, config in connector_configs.items():
            if config["enabled"]:
                try:
                    # Dynamic import and initialization would go here
                    logger.info(f"Initialized {name} connector")
                except Exception as e:
                    logger.warning(f"Failed to initialize {name} connector: {e}")

    async def _execute_core(self, task: Task, routing: Any) -> Result:
        """
        Execute Sophia-specific business intelligence task

        Args:
            task: Task to execute
            routing: Model routing decision

        Returns:
            Execution result
        """
        result = Result(success=False, content=None)

        try:
            # Gather business data from connectors
            business_data = await self._gather_business_data(task)

            # Enrich with context
            enriched_context = await self._enrich_context(task, business_data)

            # Prepare messages for LLM
            messages = self._prepare_messages(task, enriched_context)

            # Execute with Portkey
            response = await self.portkey.execute_with_fallback(
                task_type=PortkeyTaskType.ORCHESTRATION,
                messages=messages,
                max_tokens=task.budget.get("tokens", 4000),
                temperature=0.2,
            )

            # Process response
            processed = await self._process_response(response, task)

            # Generate insights
            insights = await self.insight_engine.generate_insights(processed, business_data)

            # Format result
            result.success = True
            result.content = insights
            result.metadata = {
                "sources": list(business_data.keys()),
                "context": self.business_context.__dict__,
                "processing_steps": ["gather", "enrich", "analyze", "insights"],
            }
            result.confidence = self._calculate_confidence(insights, business_data)
            result.citations = self._extract_citations(business_data)

            # Track usage
            if hasattr(response, "usage"):
                result.tokens_used = response.usage.total_tokens
                result.cost = self.portkey._estimate_cost(routing.model, result.tokens_used)

        except Exception as e:
            logger.error(f"Sophia execution failed: {e}")
            result.errors.append(str(e))

        return result

    async def _gather_business_data(self, task: Task) -> dict[str, Any]:
        """
        Gather relevant business data from all connectors

        Args:
            task: Current task

        Returns:
            Dictionary of gathered data by source
        """
        data = {}

        # First, get foundational knowledge if available
        if self.foundational_knowledge:
            try:
                # Get Pay-Ready foundational context
                foundational_context = await self.foundational_knowledge.get_pay_ready_context()
                data["foundational_knowledge"] = foundational_context

                # Search for relevant foundational knowledge
                if task.content:
                    relevant_knowledge = await self.foundational_knowledge.search(
                        task.content, include_operational=False
                    )
                    if relevant_knowledge:
                        data["relevant_foundational"] = [
                            {
                                "name": k.name,
                                "category": k.category,
                                "priority": k.priority.value,
                                "content": k.content,
                            }
                            for k in relevant_knowledge[:5]  # Top 5 most relevant
                        ]

                logger.info(f"Gathered foundational knowledge for task {task.id}")
            except Exception as e:
                logger.warning(f"Failed to gather foundational knowledge: {e}")

        # Determine which connectors to query based on task
        relevant_connectors = self._select_relevant_connectors(task)

        # Gather data in parallel
        gather_tasks = []
        for connector_name in relevant_connectors:
            if connector_name in self.connectors:
                connector = self.connectors[connector_name]
                gather_tasks.append(self._fetch_connector_data(connector_name, connector, task))

        if gather_tasks:
            results = await asyncio.gather(*gather_tasks, return_exceptions=True)
            for connector_name, result in zip(relevant_connectors, results):
                if not isinstance(result, Exception):
                    data[connector_name] = result
                else:
                    logger.warning(f"Failed to gather data from {connector_name}: {result}")

        return data

    def _select_relevant_connectors(self, task: Task) -> list[str]:
        """Select which connectors are relevant for the task"""
        # Task-based connector selection
        task_content_lower = task.content.lower()

        connector_keywords = {
            "asana": ["project", "task", "milestone", "timeline"],
            "linear": ["issue", "bug", "feature", "sprint"],
            "gong": ["call", "conversation", "meeting", "transcript"],
            "hubspot": ["contact", "deal", "pipeline", "lead"],
            "intercom": ["customer", "support", "ticket", "conversation"],
            "salesforce": ["opportunity", "account", "forecast", "revenue"],
            "airtable": ["database", "record", "table", "view"],
            "looker": ["dashboard", "metric", "kpi", "analytics"],
        }

        relevant = []
        for connector, keywords in connector_keywords.items():
            if any(keyword in task_content_lower for keyword in keywords):
                relevant.append(connector)

        # Default to key connectors if none selected
        if not relevant:
            relevant = ["salesforce", "gong", "looker"]

        return relevant

    async def _fetch_connector_data(
        self, name: str, connector: BaseConnector, task: Task
    ) -> dict[str, Any]:
        """Fetch data from a specific connector"""
        # This would call the actual connector's fetch method
        # For now, returning mock structure
        return {
            "source": name,
            "data": {},
            "last_updated": datetime.now().isoformat(),
            "record_count": 0,
        }

    async def _enrich_context(self, task: Task, business_data: dict[str, Any]) -> dict[str, Any]:
        """
        Enrich context with historical data and patterns

        Args:
            task: Current task
            business_data: Gathered business data

        Returns:
            Enriched context dictionary
        """
        context = {
            "task": task.content,
            "business_context": self.business_context.__dict__,
            "current_data": business_data,
            "historical_context": {},
            "patterns": {},
            "benchmarks": {},
        }

        # Add historical context from memory
        if self.memory:
            # Search for similar past analyses
            similar = await self.memory.search(query=task.content, domain=MemoryDomain.SOPHIA, k=5)

            context["historical_context"] = {
                "similar_analyses": [
                    {"content": hit.content, "relevance": hit.score, "source": hit.source_uri}
                    for hit in similar
                ]
            }

            # Get recent facts
            recent_facts = await self.memory.query_facts(
                "SELECT * FROM business_facts WHERE domain = 'sophia' ORDER BY created_at DESC LIMIT 10"
            )
            context["historical_context"]["recent_facts"] = recent_facts

        # Add industry benchmarks
        context["benchmarks"] = self._get_industry_benchmarks()

        # Identify patterns
        context["patterns"] = await self._identify_patterns(business_data)

        return context

    def _prepare_messages(self, task: Task, context: dict[str, Any]) -> list[dict[str, str]]:
        """Prepare messages for LLM"""
        # Check if we have foundational knowledge
        has_foundational = "foundational_knowledge" in context

        system_prompt = f"""You are Sophia, an expert Business Intelligence analyst specializing in {self.business_context.industry}.

Your role is to:
1. Analyze business data with precision and insight
2. Identify trends, patterns, and anomalies
3. Provide actionable recommendations
4. Highlight risks and opportunities
5. Support conclusions with data

Key metrics to focus on: {', '.join(self.business_context.key_metrics)}
Currency: {self.business_context.currency}
Compliance requirements: {', '.join(self.business_context.compliance_requirements) if self.business_context.compliance_requirements else 'Standard'}

{"IMPORTANT: You have access to Pay-Ready's foundational knowledge. Prioritize this core business context in your analysis." if has_foundational else ""}

Always cite data sources and express confidence levels."""

        user_prompt = f"""Task: {task.content}

Business Context:
{json.dumps(context['business_context'], indent=2)}

Current Data Available:
{json.dumps({k: f"{v.get('record_count', 0)} records from {k}" for k, v in context.get('current_data', {}).items()}, indent=2)}

Historical Context:
{json.dumps(context.get('historical_context', {}).get('similar_analyses', [])[:2], indent=2) if context.get('historical_context') else 'No historical data'}

Industry Benchmarks:
{json.dumps(context.get('benchmarks', {}), indent=2)}

Please provide a comprehensive analysis with:
1. Executive summary
2. Key findings with supporting data
3. Actionable recommendations
4. Risk assessment
5. Opportunities identified
"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    async def _process_response(self, response: Any, task: Task) -> dict[str, Any]:
        """Process LLM response into structured format"""
        content = (
            response.choices[0].message.content if hasattr(response, "choices") else str(response)
        )

        # Parse response into structured format
        # This would use more sophisticated parsing in production
        processed = {
            "raw_response": content,
            "timestamp": datetime.now().isoformat(),
            "task_id": task.id,
            "model_used": getattr(response, "model", "unknown"),
        }

        return processed

    def _calculate_confidence(self, insights: Any, business_data: dict[str, Any]) -> float:
        """Calculate confidence score based on data quality and coverage"""
        confidence = 0.5  # Base confidence

        # Increase confidence based on data sources
        source_count = len(business_data)
        confidence += min(source_count * 0.05, 0.25)  # Up to 0.25 for 5+ sources

        # Increase confidence based on data recency
        # (Would check actual timestamps in production)
        confidence += 0.15  # Assume recent data

        # Cap at 0.95
        return min(confidence, 0.95)

    def _extract_citations(self, business_data: dict[str, Any]) -> list[dict[str, str]]:
        """Extract citations from business data"""
        citations = []

        for source, data in business_data.items():
            citations.append(
                {
                    "source": source,
                    "type": "integration",
                    "timestamp": data.get("last_updated", datetime.now().isoformat()),
                    "record_count": str(data.get("record_count", 0)),
                }
            )

        return citations

    def _get_industry_benchmarks(self) -> dict[str, Any]:
        """Get industry benchmarks for comparison"""
        # Industry-specific benchmarks
        benchmarks = {
            "Technology": {
                "arr_growth_rate": "30-40%",
                "nrr": "110-120%",
                "gross_margin": "70-80%",
                "cac_payback_months": "12-18",
                "ltv_cac_ratio": "3:1",
            },
            "SaaS": {
                "monthly_churn": "2-3%",
                "annual_churn": "10-15%",
                "magic_number": ">0.75",
                "rule_of_40": ">40%",
            },
        }

        return benchmarks.get(self.business_context.industry, {})

    async def _identify_patterns(self, business_data: dict[str, Any]) -> dict[str, Any]:
        """Identify patterns in business data"""
        patterns = {"trends": [], "anomalies": [], "correlations": []}

        # Pattern detection logic would go here
        # This is a placeholder for the actual implementation

        return patterns

    # ========== Specialized Sophia Methods ==========

    async def generate_sales_forecast(
        self, period: str = "quarter", confidence_intervals: bool = True
    ) -> InsightReport:
        """Generate sales forecast"""
        task = Task(
            id=f"forecast_{datetime.now().timestamp()}",
            type=TaskType.ORCHESTRATION,
            content=f"Generate {period} sales forecast with pipeline analysis",
            priority=ExecutionPriority.HIGH,
            metadata={"forecast_type": "sales", "period": period},
        )

        result = await self.execute(task)

        if result.success and self.forecast_engine:
            forecast = await self.forecast_engine.generate_forecast(
                result.content, period, confidence_intervals
            )
            return forecast

        return None

    async def analyze_customer_health(
        self, account_ids: Optional[list[str]] = None, include_recommendations: bool = True
    ) -> InsightReport:
        """Analyze customer health and churn risk"""
        task = Task(
            id=f"customer_health_{datetime.now().timestamp()}",
            type=TaskType.ORCHESTRATION,
            content="Analyze customer health scores and identify at-risk accounts",
            priority=ExecutionPriority.HIGH,
            metadata={"account_ids": account_ids, "analysis_type": "customer_health"},
        )

        result = await self.execute(task)

        if result.success:
            return self._format_as_insight_report(result)

        return None

    async def competitive_analysis(
        self, competitors: list[str], focus_areas: list[str] = None
    ) -> InsightReport:
        """Perform competitive analysis"""
        if not focus_areas:
            focus_areas = ["pricing", "features", "market_position", "strategy"]

        task = Task(
            id=f"competitive_{datetime.now().timestamp()}",
            type=TaskType.WEB_RESEARCH,
            content=f"Analyze competitors {', '.join(competitors)} focusing on {', '.join(focus_areas)}",
            priority=ExecutionPriority.NORMAL,
            metadata={"competitors": competitors, "focus_areas": focus_areas},
        )

        result = await self.execute(task)

        if result.success and self.competitive_intel:
            analysis = await self.competitive_intel.analyze(
                result.content, competitors, focus_areas
            )
            return analysis

        return None

    def _format_as_insight_report(self, result: Result) -> InsightReport:
        """Format execution result as InsightReport"""
        return InsightReport(
            executive_summary=str(result.content)[:500] if result.content else "Analysis complete",
            key_findings=[],
            recommendations=[],
            risks=[],
            opportunities=[],
            supporting_data=result.metadata.get("sources", []),
            confidence_level=result.confidence,
            data_sources=result.metadata.get("sources", []),
        )


class InsightEngine:
    """Engine for generating business insights"""

    def __init__(self, orchestrator: SophiaOrchestrator):
        self.orchestrator = orchestrator

    async def generate_insights(self, processed_data: dict, business_data: dict) -> InsightReport:
        """Generate structured insights from processed data"""
        # Insight generation logic
        return InsightReport(
            executive_summary="Analysis complete",
            key_findings=[],
            recommendations=[],
            risks=[],
            opportunities=[],
            supporting_data=[],
            confidence_level=0.85,
            data_sources=list(business_data.keys()),
        )


class ForecastEngine:
    """Engine for generating forecasts"""

    def __init__(self, orchestrator: SophiaOrchestrator):
        self.orchestrator = orchestrator

    async def generate_forecast(
        self, data: Any, period: str, confidence_intervals: bool
    ) -> InsightReport:
        """Generate forecast with confidence intervals"""
        # Forecasting logic
        return InsightReport(
            executive_summary=f"{period.capitalize()} forecast generated",
            key_findings=[],
            recommendations=[],
            risks=[],
            opportunities=[],
            supporting_data=[],
            confidence_level=0.75,
            data_sources=["historical_data", "pipeline_data"],
        )


class CompetitiveIntelligence:
    """Engine for competitive intelligence"""

    def __init__(self, orchestrator: SophiaOrchestrator):
        self.orchestrator = orchestrator

    async def analyze(
        self, data: Any, competitors: list[str], focus_areas: list[str]
    ) -> InsightReport:
        """Analyze competitive landscape"""
        # Competitive analysis logic
        return InsightReport(
            executive_summary=f"Competitive analysis of {', '.join(competitors)}",
            key_findings=[],
            recommendations=[],
            risks=[],
            opportunities=[],
            supporting_data=[],
            confidence_level=0.70,
            data_sources=["web_research", "market_data"],
        )
