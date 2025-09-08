"""Evaluation Swarm: Post-project analysis and learning system.

This module implements the evaluation swarm that analyzes completed projects,
extracts patterns, grades performance, and generates improvement recommendations.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

import numpy as np

from app.memory.unified_memory_router import UnifiedMemoryRouter

logger = logging.getLogger(__name__)


class GradeLevel(Enum):
    """Grade levels for swarm executions."""

    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


@dataclass
class SwarmGrade:
    """Multi-dimensional grading for swarm execution."""

    # Quality Metrics (0-100)
    accuracy_score: float = 0.0
    completeness_score: float = 0.0
    clarity_score: float = 0.0

    # Efficiency Metrics (0-100)
    speed_score: float = 0.0
    cost_efficiency: float = 0.0
    token_efficiency: float = 0.0

    # Process Metrics
    consensus_level: float = 0.0
    iteration_count: int = 0
    escalation_count: int = 0

    # Business Impact
    user_satisfaction: float = 0.0
    rework_required: bool = False
    production_ready: bool = False

    # Metadata
    execution_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def overall_score(self) -> float:
        """Calculate overall score."""
        return (
            self.accuracy_score * 0.3
            + self.completeness_score * 0.2
            + self.cost_efficiency * 0.2
            + self.speed_score * 0.15
            + self.clarity_score * 0.15
        )

    @property
    def grade(self) -> GradeLevel:
        """Get letter grade."""
        score = self.overall_score
        if score >= 95:
            return GradeLevel.A_PLUS
        elif score >= 90:
            return GradeLevel.A
        elif score >= 80:
            return GradeLevel.B
        elif score >= 70:
            return GradeLevel.C
        elif score >= 60:
            return GradeLevel.D
        else:
            return GradeLevel.F

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "accuracy_score": self.accuracy_score,
            "completeness_score": self.completeness_score,
            "clarity_score": self.clarity_score,
            "speed_score": self.speed_score,
            "cost_efficiency": self.cost_efficiency,
            "token_efficiency": self.token_efficiency,
            "consensus_level": self.consensus_level,
            "iteration_count": self.iteration_count,
            "escalation_count": self.escalation_count,
            "user_satisfaction": self.user_satisfaction,
            "rework_required": self.rework_required,
            "production_ready": self.production_ready,
            "overall_score": self.overall_score,
            "grade": self.grade.value,
            "execution_id": self.execution_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Pattern:
    """Represents a discovered pattern."""

    id: str
    name: str
    description: str
    category: str
    frequency: int
    success_rate: float
    applicable_scenarios: list[str]
    recommendations: list[str]
    discovered_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Insight:
    """Represents an insight from analysis."""

    id: str
    title: str
    description: str
    severity: str  # 'info', 'warning', 'critical'
    category: str
    affected_agents: list[str]
    recommendations: list[str]
    confidence: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EvaluationReport:
    """Complete evaluation report for a project."""

    project_id: str
    grade: SwarmGrade
    insights: list[Insight]
    patterns_discovered: list[Pattern]
    recommendations: list[str]
    config_updates: dict[str, Any]
    learning_applied: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "project_id": self.project_id,
            "grade": self.grade.to_dict(),
            "insights": [
                {
                    "id": i.id,
                    "title": i.title,
                    "description": i.description,
                    "severity": i.severity,
                    "category": i.category,
                    "recommendations": i.recommendations,
                }
                for i in self.insights
            ],
            "patterns_discovered": [
                {
                    "name": p.name,
                    "description": p.description,
                    "success_rate": p.success_rate,
                }
                for p in self.patterns_discovered
            ],
            "recommendations": self.recommendations,
            "config_updates": self.config_updates,
            "learning_applied": self.learning_applied,
            "timestamp": self.timestamp.isoformat(),
        }


class PerformanceAnalyst:
    """Analyzes execution performance metrics."""

    async def analyze(self, executions: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze performance metrics from executions."""
        if not executions:
            return {"status": "no_data"}

        # Calculate performance metrics
        total_time = sum(e.get("execution_time", 0) for e in executions)
        avg_time = total_time / len(executions)

        total_tokens = sum(e.get("total_tokens", 0) for e in executions)
        avg_tokens = total_tokens / len(executions)

        # Identify bottlenecks
        bottlenecks = []
        for execution in executions:
            if execution.get("execution_time", 0) > avg_time * 1.5:
                bottlenecks.append(
                    {
                        "execution_id": execution.get("execution_id"),
                        "time": execution.get("execution_time"),
                        "reason": "Slow execution",
                    }
                )

        # Calculate efficiency scores
        speed_score = max(0, 100 - (avg_time / 30) * 100)  # 30s baseline
        token_efficiency = max(
            0, 100 - (avg_tokens / 1000) * 100
        )  # 1000 tokens baseline

        return {
            "total_executions": len(executions),
            "avg_execution_time": avg_time,
            "avg_tokens_used": avg_tokens,
            "bottlenecks": bottlenecks,
            "speed_score": speed_score,
            "token_efficiency": token_efficiency,
            "recommendations": self._generate_performance_recommendations(
                bottlenecks, avg_time
            ),
        }

    def _generate_performance_recommendations(
        self, bottlenecks: list[dict], avg_time: float
    ) -> list[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        if bottlenecks:
            recommendations.append(
                f"Optimize {len(bottlenecks)} slow executions identified"
            )

        if avg_time > 20:
            recommendations.append("Consider using faster models for simple tasks")
            recommendations.append("Implement caching for repeated queries")

        if avg_time < 5:
            recommendations.append(
                "Performance is excellent - maintain current configuration"
            )

        return recommendations


class QualityAuditor:
    """Audits output quality and completeness."""

    async def audit(self, executions: list[dict[str, Any]]) -> dict[str, Any]:
        """Audit quality of execution outputs."""
        if not executions:
            return {"status": "no_data"}

        quality_scores = []
        completeness_scores = []
        issues_found = []

        for execution in executions:
            # Analyze individual results
            result = execution.get("result", {})

            # Check for completeness
            if result.get("synthesized_response"):
                completeness_scores.append(90)
            else:
                completeness_scores.append(50)
                issues_found.append(
                    {
                        "execution_id": execution.get("execution_id"),
                        "issue": "Missing synthesized response",
                    }
                )

            # Check for quality indicators
            individual_results = result.get("individual_results", {})
            if individual_results:
                avg_confidence = np.mean(
                    [r.get("confidence", 0.5) for r in individual_results.values()]
                )
                quality_scores.append(avg_confidence * 100)
            else:
                quality_scores.append(60)

        # Calculate averages
        avg_quality = np.mean(quality_scores) if quality_scores else 0
        avg_completeness = np.mean(completeness_scores) if completeness_scores else 0

        return {
            "avg_quality_score": avg_quality,
            "avg_completeness_score": avg_completeness,
            "issues_found": issues_found,
            "total_issues": len(issues_found),
            "recommendations": self._generate_quality_recommendations(
                avg_quality, issues_found
            ),
        }

    def _generate_quality_recommendations(
        self, avg_quality: float, issues: list[dict]
    ) -> list[str]:
        """Generate quality improvement recommendations."""
        recommendations = []

        if avg_quality < 70:
            recommendations.append(
                "Implement quality gates to ensure minimum standards"
            )
            recommendations.append("Add validation checks before final output")

        if issues:
            unique_issues = {issue["issue"] for issue in issues}
            for issue_type in unique_issues:
                recommendations.append(f"Address issue: {issue_type}")

        if avg_quality > 85:
            recommendations.append(
                "Quality standards are high - maintain current practices"
            )

        return recommendations


class ProcessOptimizer:
    """Identifies process improvement opportunities."""

    async def optimize(self, executions: list[dict[str, Any]]) -> dict[str, Any]:
        """Identify process optimizations."""
        if not executions:
            return {"status": "no_data"}

        # Analyze agent utilization
        agent_usage = {}
        for execution in executions:
            agents = execution.get("agents", [])
            for agent in agents:
                template = agent.get("template", "unknown")
                agent_usage[template] = agent_usage.get(template, 0) + 1

        # Identify patterns
        patterns = []

        # Check for redundant agent usage
        total_uses = sum(agent_usage.values())
        for agent, count in agent_usage.items():
            if count / total_uses > 0.5:
                patterns.append(
                    {
                        "type": "over_reliance",
                        "agent": agent,
                        "usage_rate": count / total_uses,
                    }
                )

        # Check for inefficient routing
        routing_issues = []
        for execution in executions:
            if len(execution.get("agents", [])) > 3:
                routing_issues.append(
                    {
                        "execution_id": execution.get("execution_id"),
                        "agent_count": len(execution.get("agents", [])),
                        "issue": "Too many agents for single task",
                    }
                )

        return {
            "agent_usage": agent_usage,
            "patterns": patterns,
            "routing_issues": routing_issues,
            "optimization_potential": len(patterns) + len(routing_issues),
            "recommendations": self._generate_process_recommendations(
                patterns, routing_issues
            ),
        }

    def _generate_process_recommendations(
        self, patterns: list[dict], routing_issues: list[dict]
    ) -> list[str]:
        """Generate process improvement recommendations."""
        recommendations = []

        for pattern in patterns:
            if pattern["type"] == "over_reliance":
                recommendations.append(
                    f"Diversify agent usage - {pattern['agent']} is used {pattern['usage_rate']:.1%} of the time"
                )

        if routing_issues:
            recommendations.append(
                f"Optimize agent routing - {len(routing_issues)} tasks used excessive agents"
            )

        if not patterns and not routing_issues:
            recommendations.append(
                "Process efficiency is good - no major issues detected"
            )

        return recommendations


class LearningExtractor:
    """Extracts reusable patterns and lessons."""

    def __init__(self):
        self.pattern_library: list[Pattern] = []

    async def extract(self, executions: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract learning patterns from executions."""
        if not executions:
            return {"status": "no_data"}

        patterns = []
        successful_strategies = []
        failure_modes = []

        for execution in executions:
            result = execution.get("result", {})

            # Identify successful patterns
            if result.get("execution_time", float("inf")) < 10:
                successful_strategies.append(
                    {
                        "strategy": "fast_execution",
                        "agents": execution.get("agents", []),
                        "time": result.get("execution_time"),
                    }
                )

            # Identify failure patterns
            if execution.get("status") == "failed":
                failure_modes.append(
                    {
                        "error": execution.get("error"),
                        "agents": execution.get("agents", []),
                        "context": execution.get("request", {}).get("type"),
                    }
                )

        # Create patterns from strategies
        if successful_strategies:
            patterns.append(
                Pattern(
                    id=str(uuid4()),
                    name="Fast Execution Pattern",
                    description="Configuration for sub-10 second executions",
                    category="performance",
                    frequency=len(successful_strategies),
                    success_rate=len(successful_strategies) / len(executions),
                    applicable_scenarios=["simple_queries", "cached_responses"],
                    recommendations=["Use this pattern for similar simple tasks"],
                )
            )

        # Store patterns
        self.pattern_library.extend(patterns)

        return {
            "patterns_discovered": len(patterns),
            "successful_strategies": successful_strategies,
            "failure_modes": failure_modes,
            "patterns": [p.__dict__ for p in patterns],
            "recommendations": self._generate_learning_recommendations(
                patterns, failure_modes
            ),
        }

    def _generate_learning_recommendations(
        self, patterns: list[Pattern], failures: list[dict]
    ) -> list[str]:
        """Generate learning-based recommendations."""
        recommendations = []

        for pattern in patterns:
            recommendations.append(
                f"Apply '{pattern.name}' pattern to similar {', '.join(pattern.applicable_scenarios)} scenarios"
            )

        if failures:
            unique_errors = {f.get("error", "unknown") for f in failures}
            for error in unique_errors:
                recommendations.append(f"Implement error handling for: {error}")

        if not patterns:
            recommendations.append("Continue collecting data to identify patterns")

        return recommendations


class RetrospectiveSwarm:
    """Main evaluation swarm that coordinates all analysis agents."""

    def __init__(self):
        self.performance_analyst = PerformanceAnalyst()
        self.quality_auditor = QualityAuditor()
        self.process_optimizer = ProcessOptimizer()
        self.learning_extractor = LearningExtractor()
        self.memory_router = UnifiedMemoryRouter()

        logger.info("RetrospectiveSwarm initialized")

    async def evaluate_project(self, project_id: str) -> EvaluationReport:
        """Evaluate a completed project."""
        try:
            # Gather all execution data
            executions = await self._gather_executions(project_id)

            if not executions:
                logger.warning(f"No executions found for project {project_id}")
                return self._create_empty_report(project_id)

            # Run all analysis agents in parallel
            results = await asyncio.gather(
                self.performance_analyst.analyze(executions),
                self.quality_auditor.audit(executions),
                self.process_optimizer.optimize(executions),
                self.learning_extractor.extract(executions),
            )

            performance_analysis = results[0]
            quality_audit = results[1]
            process_optimization = results[2]
            learning_extraction = results[3]

            # Synthesize insights
            insights = self._synthesize_insights(
                performance_analysis,
                quality_audit,
                process_optimization,
                learning_extraction,
            )

            # Generate grade
            grade = self._calculate_grade(
                performance_analysis, quality_audit, process_optimization
            )

            # Generate recommendations
            recommendations = self._consolidate_recommendations(
                performance_analysis.get("recommendations", []),
                quality_audit.get("recommendations", []),
                process_optimization.get("recommendations", []),
                learning_extraction.get("recommendations", []),
            )

            # Generate config updates
            config_updates = self._generate_config_updates(insights)

            # Create report
            report = EvaluationReport(
                project_id=project_id,
                grade=grade,
                insights=insights,
                patterns_discovered=[
                    Pattern(**p) for p in learning_extraction.get("patterns", [])
                ],
                recommendations=recommendations,
                config_updates=config_updates,
                learning_applied=False,  # Will be set to True after applying
            )

            # Apply learnings
            await self._apply_learnings(report)
            report.learning_applied = True

            # Store report
            await self._store_report(report)

            logger.info(
                f"Completed evaluation for project {project_id} with grade {grade.grade.value}"
            )

            return report

        except Exception as e:
            logger.error(f"Error evaluating project {project_id}: {e}")
            return self._create_empty_report(project_id)

    async def _gather_executions(self, project_id: str) -> list[dict[str, Any]]:
        """Gather all executions for a project."""
        # In production, this would query the memory system
        # For now, return mock data
        return [
            {
                "execution_id": str(uuid4()),
                "request": {"type": "business_analysis"},
                "agents": [{"template": "sales_analyst", "id": "agent1"}],
                "result": {
                    "execution_time": 8.5,
                    "total_tokens": 450,
                    "synthesized_response": "Analysis complete",
                    "individual_results": {
                        "agent1": {"confidence": 0.85, "tokens_used": 450}
                    },
                },
                "status": "complete",
            }
        ]

    def _synthesize_insights(
        self, performance: dict, quality: dict, process: dict, learning: dict
    ) -> list[Insight]:
        """Synthesize insights from all analyses."""
        insights = []

        # Performance insights
        if performance.get("bottlenecks"):
            insights.append(
                Insight(
                    id=str(uuid4()),
                    title="Performance Bottlenecks Detected",
                    description=f"Found {len(performance['bottlenecks'])} slow executions",
                    severity="warning",
                    category="performance",
                    affected_agents=[],
                    recommendations=performance.get("recommendations", []),
                    confidence=0.85,
                )
            )

        # Quality insights
        if quality.get("avg_quality_score", 0) < 70:
            insights.append(
                Insight(
                    id=str(uuid4()),
                    title="Quality Below Threshold",
                    description=f"Average quality score is {quality.get('avg_quality_score', 0):.1f}%",
                    severity="critical",
                    category="quality",
                    affected_agents=[],
                    recommendations=quality.get("recommendations", []),
                    confidence=0.90,
                )
            )

        # Process insights
        if process.get("routing_issues"):
            insights.append(
                Insight(
                    id=str(uuid4()),
                    title="Inefficient Agent Routing",
                    description=f"{len(process['routing_issues'])} tasks used excessive agents",
                    severity="warning",
                    category="process",
                    affected_agents=[],
                    recommendations=process.get("recommendations", []),
                    confidence=0.75,
                )
            )

        # Learning insights
        if learning.get("patterns_discovered", 0) > 0:
            insights.append(
                Insight(
                    id=str(uuid4()),
                    title="New Patterns Discovered",
                    description=f"Identified {learning['patterns_discovered']} reusable patterns",
                    severity="info",
                    category="learning",
                    affected_agents=[],
                    recommendations=learning.get("recommendations", []),
                    confidence=0.80,
                )
            )

        return insights

    def _calculate_grade(
        self, performance: dict, quality: dict, process: dict
    ) -> SwarmGrade:
        """Calculate overall grade for the project."""
        grade = SwarmGrade()

        # Set scores from analyses
        grade.accuracy_score = quality.get("avg_quality_score", 70)
        grade.completeness_score = quality.get("avg_completeness_score", 70)
        grade.speed_score = performance.get("speed_score", 70)
        grade.token_efficiency = performance.get("token_efficiency", 70)

        # Calculate other scores
        grade.cost_efficiency = (grade.token_efficiency + grade.speed_score) / 2
        grade.clarity_score = 80  # Default for now
        grade.consensus_level = 85  # Default for now

        # Set other metrics
        grade.iteration_count = len(performance.get("bottlenecks", []))
        grade.escalation_count = len(process.get("routing_issues", []))
        grade.user_satisfaction = 75  # Would come from user feedback

        return grade

    def _consolidate_recommendations(self, *recommendation_lists) -> list[str]:
        """Consolidate and deduplicate recommendations."""
        all_recommendations = []
        for rec_list in recommendation_lists:
            all_recommendations.extend(rec_list)

        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in all_recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)

        return unique_recommendations[:10]  # Limit to top 10

    def _generate_config_updates(self, insights: list[Insight]) -> dict[str, Any]:
        """Generate configuration updates based on insights."""
        config_updates = {}

        for insight in insights:
            if insight.severity == "critical":
                if insight.category == "quality":
                    config_updates["min_quality_threshold"] = 0.75
                elif insight.category == "performance":
                    config_updates["max_execution_time"] = 15
            elif insight.severity == "warning" and insight.category == "process":
                config_updates["max_agents_per_task"] = 2

        return config_updates

    async def _apply_learnings(self, report: EvaluationReport):
        """Apply learnings from the evaluation."""
        # Store patterns in memory
        for pattern in report.patterns_discovered:
            await self.memory_router.store(
                key=f"pattern:{pattern.id}",
                value=pattern.__dict__,
                domain="SHARED",
                tier="L3",  # Vector storage for semantic search
            )

        # Apply config updates (in production, this would update actual configs)
        if report.config_updates:
            logger.info(f"Applying config updates: {report.config_updates}")

    async def _store_report(self, report: EvaluationReport):
        """Store the evaluation report."""
        await self.memory_router.store(
            key=f"evaluation:{report.project_id}",
            value=report.to_dict(),
            domain="SHARED",
            tier="L2",  # Warm storage
        )

    def _create_empty_report(self, project_id: str) -> EvaluationReport:
        """Create an empty report when no data is available."""
        return EvaluationReport(
            project_id=project_id,
            grade=SwarmGrade(),
            insights=[],
            patterns_discovered=[],
            recommendations=["No data available for evaluation"],
            config_updates={},
            learning_applied=False,
        )


# Global evaluation swarm instance
_evaluation_swarm = None


def get_evaluation_swarm() -> RetrospectiveSwarm:
    """Get or create the global evaluation swarm instance."""
    global _evaluation_swarm
    if _evaluation_swarm is None:
        _evaluation_swarm = RetrospectiveSwarm()
    return _evaluation_swarm
