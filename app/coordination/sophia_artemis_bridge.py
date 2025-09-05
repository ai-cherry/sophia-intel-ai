"""
Sophia-Artemis Coordination Bridge
==================================

Enhanced coordination framework that enables seamless collaboration between
Sophia (Business Intelligence) and Artemis (Technical Excellence) orchestrators.

This builds on the existing dual orchestrator architecture to provide:
- Hierarchical task delegation (Sophia -> Artemis for technical work)
- Bi-directional communication and feedback
- Resource allocation and load balancing
- Context preservation across orchestrator boundaries
- Unified result synthesis
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of cross-orchestrator tasks"""

    BUSINESS_ANALYSIS = "business_analysis"
    TECHNICAL_IMPLEMENTATION = "technical_implementation"
    HYBRID_ANALYSIS = "hybrid_analysis"
    CODE_REVIEW_WITH_BUSINESS_CONTEXT = "code_review_with_business_context"
    BUSINESS_IMPACT_ASSESSMENT = "business_impact_assessment"


class CoordinationPattern(Enum):
    """Coordination patterns between orchestrators"""

    SOPHIA_LEADS = "sophia_leads"  # Sophia delegates to Artemis
    ARTEMIS_LEADS = "artemis_leads"  # Artemis requests business context from Sophia
    COLLABORATIVE = "collaborative"  # Both work together as peers
    SEQUENTIAL = "sequential"  # One after the other
    PARALLEL_WITH_SYNC = "parallel_with_sync"  # Parallel work with synchronization points


@dataclass
class CoordinationContext:
    """Context shared between orchestrators"""

    session_id: str = field(default_factory=lambda: str(uuid4()))
    original_query: str = ""
    business_context: Dict[str, Any] = field(default_factory=dict)
    technical_context: Dict[str, Any] = field(default_factory=dict)
    shared_memory: Dict[str, Any] = field(default_factory=dict)
    coordination_pattern: CoordinationPattern = CoordinationPattern.SOPHIA_LEADS
    priority_level: int = 1  # 1 = highest
    created_at: datetime = field(default_factory=datetime.now)

    def add_business_insight(self, key: str, value: Any) -> None:
        """Add business insight to shared context"""
        self.business_context[key] = value
        self.shared_memory[f"business_{key}"] = value

    def add_technical_insight(self, key: str, value: Any) -> None:
        """Add technical insight to shared context"""
        self.technical_context[key] = value
        self.shared_memory[f"technical_{key}"] = value

    def get_combined_context(self) -> Dict[str, Any]:
        """Get combined context for comprehensive analysis"""
        return {
            "business": self.business_context,
            "technical": self.technical_context,
            "shared": self.shared_memory,
            "session": self.session_id,
            "query": self.original_query,
        }


@dataclass
class DelegationRequest:
    """Request for delegation between orchestrators"""

    id: str = field(default_factory=lambda: str(uuid4()))
    from_orchestrator: str = ""
    to_orchestrator: str = ""
    task_type: TaskType = TaskType.TECHNICAL_IMPLEMENTATION
    request_details: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    context: CoordinationContext = field(default_factory=CoordinationContext)
    priority: int = 1
    timeout_seconds: int = 300
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DelegationResponse:
    """Response from delegated task execution"""

    request_id: str = ""
    success: bool = False
    result: Any = None
    error: Optional[str] = None
    execution_time_seconds: float = 0.0
    additional_context: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class SophiaArtemisCoordinationBridge:
    """
    Bridge that coordinates between Sophia and Artemis orchestrators
    """

    def __init__(self):
        self.active_sessions: Dict[str, CoordinationContext] = {}
        self.delegation_history: List[Dict[str, Any]] = []

        # Performance metrics
        self.metrics = {
            "total_coordinations": 0,
            "successful_delegations": 0,
            "failed_delegations": 0,
            "average_coordination_time": 0.0,
            "sophia_to_artemis_count": 0,
            "artemis_to_sophia_count": 0,
        }

        logger.info("Sophia-Artemis Coordination Bridge initialized")

    async def coordinate_business_analysis(
        self, query: str, user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Coordinate a business analysis that may require technical insights

        Flow: Sophia leads, may delegate technical portions to Artemis
        """
        context = CoordinationContext(
            original_query=query, coordination_pattern=CoordinationPattern.SOPHIA_LEADS
        )

        if user_context:
            context.business_context.update(user_context)

        self.active_sessions[context.session_id] = context
        start_time = datetime.now()

        try:
            logger.info(f"Starting business analysis coordination: {context.session_id}")

            # Phase 1: Sophia initial analysis
            sophia_result = await self._invoke_sophia(
                query=query, context=context, analysis_type="initial_business_analysis"
            )

            context.add_business_insight("initial_analysis", sophia_result)

            # Phase 2: Check if technical delegation is needed
            needs_technical = self._analyze_technical_needs(sophia_result, query)

            if needs_technical:
                logger.info("Business analysis requires technical insights - delegating to Artemis")

                # Delegate technical analysis to Artemis
                technical_request = DelegationRequest(
                    from_orchestrator="sophia",
                    to_orchestrator="artemis",
                    task_type=TaskType.TECHNICAL_IMPLEMENTATION,
                    request_details=self._extract_technical_requirements(sophia_result),
                    parameters={"business_context": context.business_context},
                    context=context,
                )

                artemis_result = await self._delegate_to_artemis(technical_request)
                context.add_technical_insight("technical_analysis", artemis_result.result)

                # Phase 3: Sophia synthesis with technical insights
                final_result = await self._invoke_sophia(
                    query=f"Synthesize business analysis with technical insights: {query}",
                    context=context,
                    analysis_type="synthesis_with_technical",
                )
            else:
                final_result = sophia_result

            # Record successful coordination
            execution_time = (datetime.now() - start_time).total_seconds()
            self.metrics["total_coordinations"] += 1
            self.metrics["successful_delegations"] += 1
            self.metrics["sophia_to_artemis_count"] += 1

            # Update average execution time
            total_time = self.metrics["average_coordination_time"] * (
                self.metrics["total_coordinations"] - 1
            )
            self.metrics["average_coordination_time"] = (
                total_time + execution_time
            ) / self.metrics["total_coordinations"]

            # Log decision tree for hybrid tasks
            if context.coordination_pattern in [CoordinationPattern.COLLABORATIVE, CoordinationPattern.PARALLEL_WITH_SYNC]:
                decision_tree = {
                    "session_id": context.session_id,
                    "sophia_decisions": context.business_context.get("decisions", []),
                    "artemis_decisions": context.technical_context.get("decisions", []),
                    "combined_reasoning": final_result.get("reasoning", ""),
                    "pattern": context.coordination_pattern.value,
                    "timestamp": datetime.now().isoformat()
                }
                logger.info(f"HYBRID_DECISION_TREE: {json.dumps(decision_tree)}")

            return {
                "session_id": context.session_id,
                "success": True,
                "result": final_result,
                "business_insights": context.business_context,
                "technical_insights": context.technical_context,
                "execution_time_seconds": execution_time,
                "coordination_pattern": context.coordination_pattern.value,
            }

        except Exception as e:
            logger.error(f"Business analysis coordination failed: {e}")
            self.metrics["failed_delegations"] += 1

            return {
                "session_id": context.session_id,
                "success": False,
                "error": str(e),
                "execution_time_seconds": (datetime.now() - start_time).total_seconds(),
            }

        finally:
            # Clean up session
            if context.session_id in self.active_sessions:
                del self.active_sessions[context.session_id]

    async def coordinate_technical_implementation(
        self, requirements: str, business_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Coordinate technical implementation with business validation

        Flow: Artemis leads, requests business context from Sophia as needed
        """
        context = CoordinationContext(
            original_query=requirements, coordination_pattern=CoordinationPattern.ARTEMIS_LEADS
        )

        if business_context:
            context.business_context.update(business_context)

        self.active_sessions[context.session_id] = context
        start_time = datetime.now()

        try:
            logger.info(f"Starting technical implementation coordination: {context.session_id}")

            # Phase 1: Artemis technical analysis and planning
            artemis_plan = await self._invoke_artemis(
                query=requirements, context=context, task_type="technical_planning"
            )

            context.add_technical_insight("implementation_plan", artemis_plan)

            # Phase 2: Request business validation from Sophia
            business_request = DelegationRequest(
                from_orchestrator="artemis",
                to_orchestrator="sophia",
                task_type=TaskType.BUSINESS_IMPACT_ASSESSMENT,
                request_details=f"Validate business impact of technical implementation: {requirements}",
                parameters={"technical_plan": artemis_plan},
                context=context,
            )

            sophia_validation = await self._delegate_to_sophia(business_request)
            context.add_business_insight("business_validation", sophia_validation.result)

            # Phase 3: Artemis implementation with business constraints
            final_implementation = await self._invoke_artemis(
                query=f"Implement with business constraints: {requirements}",
                context=context,
                task_type="implementation_with_constraints",
            )

            execution_time = (datetime.now() - start_time).total_seconds()
            self.metrics["total_coordinations"] += 1
            self.metrics["successful_delegations"] += 1
            self.metrics["artemis_to_sophia_count"] += 1

            return {
                "session_id": context.session_id,
                "success": True,
                "implementation": final_implementation,
                "business_validation": context.business_context,
                "technical_details": context.technical_context,
                "execution_time_seconds": execution_time,
                "coordination_pattern": context.coordination_pattern.value,
            }

        except Exception as e:
            logger.error(f"Technical implementation coordination failed: {e}")
            self.metrics["failed_delegations"] += 1

            return {
                "session_id": context.session_id,
                "success": False,
                "error": str(e),
                "execution_time_seconds": (datetime.now() - start_time).total_seconds(),
            }

        finally:
            if context.session_id in self.active_sessions:
                del self.active_sessions[context.session_id]

    async def coordinate_hybrid_analysis(
        self, query: str, require_both: bool = True
    ) -> Dict[str, Any]:
        """
        Coordinate analysis that requires both business and technical perspectives

        Flow: Parallel execution with synchronization
        """
        context = CoordinationContext(
            original_query=query, coordination_pattern=CoordinationPattern.PARALLEL_WITH_SYNC
        )

        self.active_sessions[context.session_id] = context
        start_time = datetime.now()

        try:
            logger.info(f"Starting hybrid analysis coordination: {context.session_id}")

            # Execute both analyses in parallel
            sophia_task = self._invoke_sophia(
                query=query, context=context, analysis_type="business_perspective"
            )

            artemis_task = self._invoke_artemis(
                query=query, context=context, task_type="technical_perspective"
            )

            # Wait for both to complete
            sophia_result, artemis_result = await asyncio.gather(
                sophia_task, artemis_task, return_exceptions=True
            )

            # Handle exceptions
            if isinstance(sophia_result, Exception):
                if require_both:
                    raise sophia_result
                else:
                    sophia_result = {"error": str(sophia_result)}

            if isinstance(artemis_result, Exception):
                if require_both:
                    raise artemis_result
                else:
                    artemis_result = {"error": str(artemis_result)}

            context.add_business_insight("parallel_analysis", sophia_result)
            context.add_technical_insight("parallel_analysis", artemis_result)

            # Synthesis phase - use Sophia to combine insights
            synthesis_query = f"Synthesize business and technical perspectives: {query}"
            synthesis = await self._invoke_sophia(
                query=synthesis_query, context=context, analysis_type="hybrid_synthesis"
            )

            execution_time = (datetime.now() - start_time).total_seconds()
            self.metrics["total_coordinations"] += 1
            self.metrics["successful_delegations"] += 1

            return {
                "session_id": context.session_id,
                "success": True,
                "business_perspective": sophia_result,
                "technical_perspective": artemis_result,
                "synthesis": synthesis,
                "combined_context": context.get_combined_context(),
                "execution_time_seconds": execution_time,
                "coordination_pattern": context.coordination_pattern.value,
            }

        except Exception as e:
            logger.error(f"Hybrid analysis coordination failed: {e}")
            self.metrics["failed_delegations"] += 1

            return {
                "session_id": context.session_id,
                "success": False,
                "error": str(e),
                "execution_time_seconds": (datetime.now() - start_time).total_seconds(),
            }

        finally:
            if context.session_id in self.active_sessions:
                del self.active_sessions[context.session_id]

    async def _delegate_to_artemis(self, request: DelegationRequest) -> DelegationResponse:
        """Delegate task to Artemis orchestrator"""
        logger.info(f"Delegating to Artemis: {request.task_type.value}")

        start_time = datetime.now()

        try:
            # This would call the actual Artemis orchestrator
            # For now, simulate the call
            result = await self._invoke_artemis(
                query=request.request_details,
                context=request.context,
                task_type=request.task_type.value,
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            return DelegationResponse(
                request_id=request.id,
                success=True,
                result=result,
                execution_time_seconds=execution_time,
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            return DelegationResponse(
                request_id=request.id,
                success=False,
                error=str(e),
                execution_time_seconds=execution_time,
            )

    async def _delegate_to_sophia(self, request: DelegationRequest) -> DelegationResponse:
        """Delegate task to Sophia orchestrator"""
        logger.info(f"Delegating to Sophia: {request.task_type.value}")

        start_time = datetime.now()

        try:
            result = await self._invoke_sophia(
                query=request.request_details,
                context=request.context,
                analysis_type=request.task_type.value,
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            return DelegationResponse(
                request_id=request.id,
                success=True,
                result=result,
                execution_time_seconds=execution_time,
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            return DelegationResponse(
                request_id=request.id,
                success=False,
                error=str(e),
                execution_time_seconds=execution_time,
            )

    async def _invoke_sophia(
        self, query: str, context: CoordinationContext, analysis_type: str
    ) -> Dict[str, Any]:
        """Invoke Sophia orchestrator (will integrate with actual Sophia)"""

        # This will call the actual Sophia orchestrator
        # For now, simulate business intelligence response
        await asyncio.sleep(1)  # Simulate processing time

        business_response = {
            "analysis_type": analysis_type,
            "business_insights": [
                "Strong market opportunity identified",
                "Competitive advantage potential",
                "Revenue impact projected at $2M annually",
            ],
            "strategic_recommendations": [
                "Prioritize user experience improvements",
                "Focus on enterprise customer segment",
                "Implement phased rollout approach",
            ],
            "risk_assessment": {
                "market_risk": "Low",
                "execution_risk": "Medium",
                "competitive_risk": "Low",
            },
            "business_metrics": {
                "projected_roi": "340%",
                "payback_period_months": 8,
                "customer_satisfaction_impact": "+15%",
            },
            "context_used": {
                "business_context": len(context.business_context),
                "technical_context": len(context.technical_context),
                "shared_memory": len(context.shared_memory),
            },
        }

        logger.info(f"Sophia analysis ({analysis_type}) completed")
        return business_response

    async def _invoke_artemis(
        self, query: str, context: CoordinationContext, task_type: str
    ) -> Dict[str, Any]:
        """Invoke Artemis orchestrator (will integrate with actual Artemis)"""

        # This will call the actual Artemis orchestrator
        # For now, simulate technical response
        await asyncio.sleep(1.5)  # Simulate processing time

        technical_response = {
            "task_type": task_type,
            "technical_assessment": {
                "complexity": "Medium",
                "estimated_effort_hours": 120,
                "risk_factors": ["Database migration required", "API changes needed"],
                "technology_stack": ["Python", "FastAPI", "PostgreSQL", "React"],
            },
            "implementation_plan": {
                "phases": [
                    {"phase": 1, "name": "Database Schema Updates", "duration_days": 3},
                    {"phase": 2, "name": "API Development", "duration_days": 7},
                    {"phase": 3, "name": "Frontend Integration", "duration_days": 5},
                    {"phase": 4, "name": "Testing & Deployment", "duration_days": 3},
                ],
                "total_duration_days": 18,
            },
            "quality_metrics": {
                "test_coverage_target": "90%",
                "performance_requirements": "< 200ms response time",
                "security_considerations": ["Input validation", "Authentication", "Rate limiting"],
            },
            "resource_requirements": {"developers": 2, "devops": 1, "qa_engineers": 1},
            "context_integration": {
                "business_constraints_considered": len(context.business_context) > 0,
                "cross_functional_requirements": True,
            },
        }

        logger.info(f"Artemis analysis ({task_type}) completed")
        return technical_response

    def _analyze_technical_needs(self, sophia_result: Dict[str, Any], original_query: str) -> bool:
        """Analyze if business result needs technical implementation insights"""

        # Check for technical keywords or requirements in the analysis
        technical_indicators = [
            "implement",
            "develop",
            "code",
            "system",
            "architecture",
            "database",
            "api",
            "integration",
            "performance",
            "scalability",
        ]

        query_lower = original_query.lower()
        result_str = json.dumps(sophia_result).lower()

        technical_mentions = sum(
            1
            for indicator in technical_indicators
            if indicator in query_lower or indicator in result_str
        )

        # If multiple technical concepts are mentioned, delegate to Artemis
        return technical_mentions >= 2

    def _extract_technical_requirements(self, sophia_result: Dict[str, Any]) -> str:
        """Extract technical requirements from Sophia's business analysis"""

        requirements = []

        # Extract from recommendations
        recommendations = sophia_result.get("strategic_recommendations", [])
        for rec in recommendations:
            if any(word in rec.lower() for word in ["implement", "system", "develop"]):
                requirements.append(rec)

        # Extract from business insights
        insights = sophia_result.get("business_insights", [])
        for insight in insights:
            if any(word in insight.lower() for word in ["technical", "system", "platform"]):
                requirements.append(insight)

        if not requirements:
            requirements.append("Implement technical solution based on business requirements")

        return "; ".join(requirements)

    def get_coordination_metrics(self) -> Dict[str, Any]:
        """Get coordination performance metrics"""
        return {
            "metrics": self.metrics.copy(),
            "active_sessions": len(self.active_sessions),
            "delegation_success_rate": (
                (
                    self.metrics["successful_delegations"]
                    / max(self.metrics["total_coordinations"], 1)
                )
                * 100
            ),
            "coordination_patterns": {
                "sophia_leads": self.metrics["sophia_to_artemis_count"],
                "artemis_leads": self.metrics["artemis_to_sophia_count"],
            },
        }

    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get information about currently active coordination sessions"""
        return {
            session_id: {
                "original_query": context.original_query,
                "coordination_pattern": context.coordination_pattern.value,
                "created_at": context.created_at.isoformat(),
                "business_context_keys": list(context.business_context.keys()),
                "technical_context_keys": list(context.technical_context.keys()),
            }
            for session_id, context in self.active_sessions.items()
        }


# Global coordination bridge instance
_coordination_bridge = None


def get_coordination_bridge() -> SophiaArtemisCoordinationBridge:
    """Get singleton coordination bridge instance"""
    global _coordination_bridge
    if _coordination_bridge is None:
        _coordination_bridge = SophiaArtemisCoordinationBridge()
    return _coordination_bridge


# Convenience functions for common coordination patterns


async def analyze_with_business_lead(query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Sophia-led analysis with potential technical delegation"""
    bridge = get_coordination_bridge()
    return await bridge.coordinate_business_analysis(query, context)


async def implement_with_business_validation(
    requirements: str, business_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Artemis-led implementation with business validation"""
    bridge = get_coordination_bridge()
    return await bridge.coordinate_technical_implementation(requirements, business_context)


async def hybrid_perspective_analysis(query: str, require_both: bool = True) -> Dict[str, Any]:
    """Combined business and technical analysis"""
    bridge = get_coordination_bridge()
    return await bridge.coordinate_hybrid_analysis(query, require_both)


# Example usage
async def example_coordination():
    """Example of coordinated analysis"""

    # Business-led analysis that may need technical insights
    business_result = await analyze_with_business_lead(
        "Should we implement real-time notifications for our customer dashboard?",
        {"company_size": "mid-market", "technical_team_size": 8},
    )

    print("Business Analysis Result:")
    print(json.dumps(business_result, indent=2, default=str))

    # Technical implementation with business validation
    tech_result = await implement_with_business_validation(
        "Implement WebSocket-based real-time notifications with fallback to polling",
        {"budget_constraint": 50000, "timeline_weeks": 8},
    )

    print("\nTechnical Implementation Result:")
    print(json.dumps(tech_result, indent=2, default=str))

    # Hybrid analysis
    hybrid_result = await hybrid_perspective_analysis(
        "Evaluate the feasibility and business impact of migrating to microservices architecture"
    )

    print("\nHybrid Analysis Result:")
    print(json.dumps(hybrid_result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(example_coordination())
