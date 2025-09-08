#!/usr/bin/env python3
"""
Sophia-Artemis Cross-Domain Intelligence Bridge
Translates between business (Sophia) and technical (Artemis) contexts
"""
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from portkey_ai import Portkey

logger = logging.getLogger(__name__)


class DomainType(Enum):
    """Domain types for translation"""

    BUSINESS = "business"
    TECHNICAL = "technical"


@dataclass
class TranslationMapping:
    """Mapping between business and technical terms"""

    business_term: str
    technical_term: str
    category: str
    confidence: float = 1.0


@dataclass
class CrossDomainInsight:
    """Insight that spans both domains"""

    source_domain: DomainType
    target_domain: DomainType
    original_content: str
    translated_content: str
    confidence: float
    metadata: dict[str, Any]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class SophiaArtemisBridge:
    """Bridges business and technical intelligence between orchestrators"""

    # Pre-defined mappings for common translations
    STATIC_MAPPINGS = [
        # Performance mappings
        TranslationMapping(
            "increase payment velocity", "reduce API latency below 200ms", "performance"
        ),
        TranslationMapping(
            "improve customer experience",
            "optimize frontend response time and error handling",
            "performance",
        ),
        TranslationMapping(
            "reduce operational costs",
            "optimize cloud resource utilization and API calls",
            "cost",
        ),
        # Reliability mappings
        TranslationMapping(
            "ensure business continuity",
            "implement 99.9% uptime with failover systems",
            "reliability",
        ),
        TranslationMapping(
            "minimize payment failures",
            "implement retry logic with exponential backoff",
            "reliability",
        ),
        TranslationMapping(
            "prevent revenue loss",
            "implement circuit breakers and graceful degradation",
            "reliability",
        ),
        # Efficiency mappings
        TranslationMapping(
            "reduce manual work",
            "implement automation pipelines and CI/CD",
            "efficiency",
        ),
        TranslationMapping(
            "accelerate team velocity",
            "optimize build times and deployment frequency",
            "efficiency",
        ),
        TranslationMapping(
            "improve team productivity",
            "implement code generation and testing automation",
            "efficiency",
        ),
        # Scale mappings
        TranslationMapping(
            "support business growth",
            "implement horizontal scaling and load balancing",
            "scale",
        ),
        TranslationMapping(
            "handle peak demand",
            "implement auto-scaling and caching strategies",
            "scale",
        ),
    ]

    # Metric translations
    METRIC_MAPPINGS = {
        # Technical to Business
        "api_latency_ms": "transaction_speed",
        "uptime_percent": "service_availability",
        "error_rate": "failure_rate",
        "throughput_rps": "processing_capacity",
        "cpu_utilization": "system_load",
        "memory_usage": "resource_consumption",
        "deployment_frequency": "release_velocity",
        "mttr_minutes": "recovery_time",
        "test_coverage": "quality_assurance",
        # Business to Technical
        "revenue_impact": "system_criticality",
        "customer_satisfaction": "user_experience_score",
        "operational_efficiency": "automation_level",
        "compliance_score": "security_posture",
        "time_to_market": "deployment_velocity",
    }

    def __init__(self):
        """Initialize the bridge"""
        self.sophia = None  # Will be initialized when needed
        self.artemis = None  # Will be initialized when needed
        self.translation_cache = {}
        self.learning_history = []
        self.portkey_client = self._init_portkey()

    def _init_portkey(self) -> Optional[Portkey]:
        """Initialize Portkey client for LLM translations"""
        try:
            import os

            api_key = os.environ.get("PORTKEY_API_KEY")
            if api_key:
                return Portkey(
                    api_key=api_key,
                    virtual_key="openai-vk-190a60",  # Use OpenAI for translations
                )
        except Exception as e:
            logger.warning(f"Portkey initialization failed: {e}")
        return None

    def translate_to_technical(self, business_request: str) -> CrossDomainInsight:
        """
        Translate business request to technical specification

        Examples:
            'Reduce stuck accounts by 50%' -> 'Implement timeout detection at 72h with automated escalation'
            'Improve team efficiency' -> 'Automate deployment pipeline and implement code generation'
            'Increase payment processing speed' -> 'Optimize database queries and implement caching layer'
        """
        # Check cache first
        cache_key = f"b2t:{business_request}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        # Try static mappings
        for mapping in self.STATIC_MAPPINGS:
            if mapping.business_term.lower() in business_request.lower():
                insight = CrossDomainInsight(
                    source_domain=DomainType.BUSINESS,
                    target_domain=DomainType.TECHNICAL,
                    original_content=business_request,
                    translated_content=mapping.technical_term,
                    confidence=mapping.confidence,
                    metadata={"mapping_type": "static", "category": mapping.category},
                )
                self.translation_cache[cache_key] = insight
                return insight

        # Use LLM for complex translations
        if self.portkey_client:
            technical_spec = self._llm_translate(
                business_request, "business_to_technical"
            )
            insight = CrossDomainInsight(
                source_domain=DomainType.BUSINESS,
                target_domain=DomainType.TECHNICAL,
                original_content=business_request,
                translated_content=technical_spec,
                confidence=0.85,
                metadata={"mapping_type": "llm"},
            )
        else:
            # Fallback to simple translation
            technical_spec = self._simple_translate_to_technical(business_request)
            insight = CrossDomainInsight(
                source_domain=DomainType.BUSINESS,
                target_domain=DomainType.TECHNICAL,
                original_content=business_request,
                translated_content=technical_spec,
                confidence=0.6,
                metadata={"mapping_type": "fallback"},
            )

        self.translation_cache[cache_key] = insight
        self.learning_history.append(insight)
        return insight

    def translate_to_business(
        self, technical_metric: dict[str, Any]
    ) -> CrossDomainInsight:
        """
        Translate technical metrics to business impact

        Examples:
            {'latency_reduction': '50%'} -> 'Customer transactions 2x faster, increasing satisfaction'
            {'uptime': '99.99%'} -> 'Near-zero downtime ensuring continuous revenue flow'
            {'test_coverage': '90%'} -> 'High quality assurance reducing customer issues by 60%'
        """
        # Convert metric to string for caching
        metric_str = json.dumps(technical_metric, sort_keys=True)
        cache_key = f"t2b:{metric_str}"

        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        # Build business narrative
        business_impact = self._build_business_narrative(technical_metric)

        insight = CrossDomainInsight(
            source_domain=DomainType.TECHNICAL,
            target_domain=DomainType.BUSINESS,
            original_content=metric_str,
            translated_content=business_impact,
            confidence=0.9,
            metadata={"metrics": technical_metric},
        )

        self.translation_cache[cache_key] = insight
        self.learning_history.append(insight)
        return insight

    def _llm_translate(self, content: str, direction: str) -> str:
        """Use LLM for complex translations"""
        try:
            prompt = self._build_translation_prompt(content, direction)

            response = self.portkey_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at translating between business requirements and technical specifications.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=200,
                temperature=0.3,
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM translation failed: {e}")
            return (
                self._simple_translate_to_technical(content)
                if direction == "business_to_technical"
                else content
            )

    def _build_translation_prompt(self, content: str, direction: str) -> str:
        """Build prompt for LLM translation"""
        if direction == "business_to_technical":
            return f"""
Translate this business requirement into technical specifications:

Business requirement: {content}

Provide a clear, actionable technical specification that includes:
1. Specific technical implementation needed
2. Performance targets or metrics
3. Technology components involved

Technical specification:"""
        else:
            return f"""
Translate these technical metrics into business impact:

Technical metrics: {content}

Provide a clear business narrative that includes:
1. Impact on revenue or costs
2. Effect on customer experience
3. Operational improvements

Business impact:"""

    def _simple_translate_to_technical(self, business_request: str) -> str:
        """Simple fallback translation to technical"""
        translations = {
            "fast": "low latency (<100ms)",
            "reliable": "high availability (>99.9%)",
            "scalable": "horizontal scaling capability",
            "secure": "encryption and authentication",
            "efficient": "optimized resource usage",
            "automated": "CI/CD pipeline implementation",
            "reduce": "optimize and minimize",
            "increase": "scale and enhance",
            "improve": "refactor and optimize",
        }

        result = business_request
        for business_term, tech_term in translations.items():
            if business_term in result.lower():
                result = result.replace(business_term, tech_term)

        return f"Technical implementation: {result}"

    def _build_business_narrative(self, technical_metric: dict[str, Any]) -> str:
        """Build business narrative from technical metrics"""
        narratives = []

        for key, value in technical_metric.items():
            # Map technical metric to business term
            business_term = self.METRIC_MAPPINGS.get(key, key)

            # Create narrative based on metric type and value
            if "latency" in key.lower():
                narratives.append(
                    f"Transaction speed improved by {value}, enhancing customer experience"
                )
            elif "uptime" in key.lower():
                narratives.append(
                    f"Service reliability at {value}, ensuring continuous business operations"
                )
            elif "error" in key.lower():
                narratives.append(
                    f"Failure rate reduced to {value}, improving customer trust"
                )
            elif "cost" in key.lower():
                narratives.append(
                    f"Operational costs reduced by {value}, improving margins"
                )
            elif "coverage" in key.lower():
                narratives.append(
                    f"Quality assurance at {value}, reducing customer issues"
                )
            else:
                narratives.append(f"{business_term}: {value}")

        return ". ".join(narratives)

    def create_unified_insight(
        self, business_context: dict[str, Any], technical_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Create unified insight combining both domains"""
        return {
            "timestamp": datetime.now().isoformat(),
            "business_view": {
                "summary": business_context.get("summary", ""),
                "metrics": business_context.get("metrics", {}),
                "impact": business_context.get("impact", ""),
            },
            "technical_view": {
                "implementation": technical_context.get("implementation", ""),
                "specifications": technical_context.get("specifications", {}),
                "requirements": technical_context.get("requirements", []),
            },
            "correlations": self._find_correlations(
                business_context, technical_context
            ),
            "recommendations": self._generate_recommendations(
                business_context, technical_context
            ),
        }

    def _find_correlations(
        self, business_context: dict[str, Any], technical_context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Find correlations between business and technical metrics"""
        correlations = []

        # Example correlation detection
        if business_context.get("revenue_impact") and technical_context.get("uptime"):
            correlations.append(
                {
                    "type": "reliability_revenue",
                    "strength": 0.85,
                    "description": "System uptime directly correlates with revenue generation",
                }
            )

        if business_context.get("customer_satisfaction") and technical_context.get(
            "latency"
        ):
            correlations.append(
                {
                    "type": "performance_satisfaction",
                    "strength": 0.78,
                    "description": "API latency inversely correlates with customer satisfaction",
                }
            )

        return correlations

    def _generate_recommendations(
        self, business_context: dict[str, Any], technical_context: dict[str, Any]
    ) -> list[str]:
        """Generate cross-domain recommendations"""
        recommendations = []

        # Business-driven technical recommendations
        if business_context.get("priority") == "growth":
            recommendations.append(
                "Prioritize scalability: Implement auto-scaling and load balancing"
            )

        if business_context.get("cost_pressure"):
            recommendations.append(
                "Optimize costs: Review cloud resources and implement cost monitoring"
            )

        # Technical-driven business recommendations
        if technical_context.get("tech_debt_high"):
            recommendations.append(
                "Allocate resources for refactoring to prevent future delays"
            )

        if technical_context.get("security_vulnerabilities"):
            recommendations.append(
                "Prioritize security updates to maintain compliance and trust"
            )

        return recommendations

    def sync_orchestrators(self):
        """Synchronize insights between Sophia and Artemis"""
        logger.info("Synchronizing insights between Sophia and Artemis")

        # This would integrate with actual orchestrators
        # For now, it's a placeholder for the synchronization logic
        pass

    def get_translation_performance(self) -> dict[str, Any]:
        """Get performance metrics for translations"""
        if not self.learning_history:
            return {"total_translations": 0}

        return {
            "total_translations": len(self.learning_history),
            "cache_size": len(self.translation_cache),
            "average_confidence": sum(i.confidence for i in self.learning_history)
            / len(self.learning_history),
            "domains": {
                "business_to_technical": sum(
                    1
                    for i in self.learning_history
                    if i.source_domain == DomainType.BUSINESS
                ),
                "technical_to_business": sum(
                    1
                    for i in self.learning_history
                    if i.source_domain == DomainType.TECHNICAL
                ),
            },
        }


# Singleton instance
_bridge_instance = None


def get_bridge() -> SophiaArtemisBridge:
    """Get singleton bridge instance"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = SophiaArtemisBridge()
    return _bridge_instance


if __name__ == "__main__":
    # Test the bridge
    bridge = get_bridge()

    # Test business to technical translation
    print("\n=== Business to Technical ===")
    business_requests = [
        "Increase payment processing speed by 50%",
        "Reduce operational costs",
        "Improve team productivity",
        "Ensure business continuity during peak times",
    ]

    for request in business_requests:
        insight = bridge.translate_to_technical(request)
        print(f"\nBusiness: {request}")
        print(f"Technical: {insight.translated_content}")
        print(f"Confidence: {insight.confidence:.2f}")

    # Test technical to business translation
    print("\n\n=== Technical to Business ===")
    technical_metrics = [
        {"api_latency_ms": "45ms", "improvement": "50%"},
        {"uptime_percent": "99.99%", "incidents": "0"},
        {"test_coverage": "92%", "bugs_prevented": "estimated 200/month"},
        {"deployment_frequency": "20/day", "mttr_minutes": "5"},
    ]

    for metric in technical_metrics:
        insight = bridge.translate_to_business(metric)
        print(f"\nTechnical: {metric}")
        print(f"Business: {insight.translated_content}")
        print(f"Confidence: {insight.confidence:.2f}")

    # Show performance
    print("\n\n=== Translation Performance ===")
    print(json.dumps(bridge.get_translation_performance(), indent=2))
