# Auto-added by pre-commit hook
import sys, os
try:
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    from core.environment_enforcer import enforce_environment
    enforce_environment()
except ImportError:

"""
Evolver Agent - Self-Improvement with Mem0 v2 Memory Graphs

Provides continuous learning and improvement capabilities:
- Memory graph construction with Mem0 v2
- Performance pattern analysis
- Self-optimization recommendations
- Privacy-filtered learning
- Swarm intelligence evolution
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict

try:
    from crewai import Agent
    from mem0 import MemoryClient
except ImportError as e:
    logging.warning(f"Missing dependencies for Evolver Agent: {e}")
    Agent = MemoryClient = None

@dataclass
class LearningInsight:
    """Individual learning insight"""
    category: str
    insight: str
    confidence: float
    evidence: List[str]
    recommendation: str

@dataclass
class EvolutionResult:
    """Evolution analysis result"""
    insights: List[LearningInsight]
    performance_trends: Dict[str, Any]
    optimization_suggestions: List[str]
    memory_updates: List[str]
    privacy_filtered: bool

class EvolverAgent:
    """
    Evolver Agent with Mem0 v2 Memory Graphs

    Responsible for:
    - Analyzing swarm performance patterns
    - Learning from successes and failures
    - Storing insights in memory graphs
    - Generating optimization recommendations
    - Evolving swarm intelligence over time
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        self.agent_id = "artemis_evolver"
        self.version = "2.0.0"
        self.status = "initialized"

        # Initialize Mem0 memory client
        self.memory_client = None
        if MemoryClient:
            try:
                self.memory_client = MemoryClient()
                self.logger.info("Mem0 memory client initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Mem0 client: {e}")

        # Learning categories
        self.learning_categories = [
            "planning_effectiveness",
            "code_quality",
            "testing_coverage",
            "deployment_success",
            "error_patterns",
            "performance_optimization"
        ]

        # Performance history (in-memory fallback)
        self.performance_history = defaultdict(list)

    async def learn_and_improve(self, swarm_state: Any) -> Dict[str, Any]:
        """
        Learn from swarm execution and generate improvements

        Args:
            swarm_state: Complete state from swarm execution

        Returns:
            Dictionary containing learning insights and recommendations
        """
        self.logger.info("Starting evolution analysis")

        try:
            # Extract performance data
            performance_data = self._extract_performance_data(swarm_state)

            # Analyze patterns
            insights = await self._analyze_patterns(performance_data)

            # Generate optimization suggestions
            optimizations = await self._generate_optimizations(insights, performance_data)

            # Update memory with privacy filtering
            memory_updates = await self._update_memory(insights, performance_data)

            # Track performance trends
            trends = self._analyze_trends(performance_data)

            result = EvolutionResult(
                insights=insights,
                performance_trends=trends,
                optimization_suggestions=optimizations,
                memory_updates=memory_updates,
                privacy_filtered=True
            )

            return {
                "evolution_result": asdict(result),
                "learning_summary": self._generate_learning_summary(result),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Evolution analysis failed: {e}")
            return {
                "error": str(e),
                "fallback_insights": await self._fallback_analysis(swarm_state),
                "timestamp": datetime.now().isoformat()
            }

    def _extract_performance_data(self, swarm_state: Any) -> Dict[str, Any]:
        """Extract performance metrics from swarm state"""

        if hasattr(swarm_state, '__dict__'):
            state_dict = swarm_state.__dict__
        else:
            state_dict = swarm_state if isinstance(swarm_state, dict) else {}

        performance_data = {
            "intent": state_dict.get("intent", ""),
            "completed": state_dict.get("completed", False),
            "errors": state_dict.get("errors", []),
            "iteration": state_dict.get("iteration", 0),
            "plan_quality": self._assess_plan_quality(state_dict.get("plan", {})),
            "code_quality": self._assess_code_quality(state_dict.get("code", {})),
            "sophia_results": self._assess_test_results(state_dict.get("tests", {})),
            "deployment_success": self._assess_deployment(state_dict.get("deployment", {})),
            "execution_time": datetime.now().isoformat()
        }

        return performance_data

    def _assess_plan_quality(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Assess planning phase quality"""
        if not plan:
            return {"score": 0, "issues": ["No plan generated"]}

        tasks = plan.get("tasks", [])
        score = 0
        issues = []

        if tasks:
            score += 30  # Has tasks
            if len(tasks) > 1:
                score += 20  # Multiple tasks
            if any(task.get("dependencies") for task in tasks if isinstance(task, dict)):
                score += 20  # Has dependencies
            if plan.get("architecture"):
                score += 15  # Has architecture
            if plan.get("risks"):
                score += 15  # Identified risks
        else:
            issues.append("No tasks in plan")

        return {"score": score, "issues": issues, "task_count": len(tasks)}

    def _assess_code_quality(self, code: Dict[str, Any]) -> Dict[str, Any]:
        """Assess code generation quality"""
        if not code:
            return {"score": 0, "issues": ["No code generated"]}

        files = code.get("files", {})
        score = 0
        issues = []

        if files:
            score += 40  # Has files

            # Check for documentation
            documented_files = sum(1 for f in files.values() 
                                 if isinstance(f, dict) and f.get("documentation"))
            if documented_files > 0:
                score += 20

            # Check for tests
            tested_files = sum(1 for f in files.values() 
                             if isinstance(f, dict) and f.get("tests"))
            if tested_files > 0:
                score += 20

            # Check for proofs
            verified_files = sum(1 for f in files.values() 
                               if isinstance(f, dict) and f.get("proof_hash"))
            if verified_files > 0:
                score += 20
        else:
            issues.append("No code files generated")

        return {"score": score, "issues": issues, "file_count": len(files)}

    def _assess_test_results(self, tests: Dict[str, Any]) -> Dict[str, Any]:
        """Assess testing phase quality"""
        if not tests:
            return {"score": 0, "issues": ["No tests run"]}

        summary = tests.get("summary", {})
        score = 0
        issues = []

        if summary.get("pytest_passed"):
            score += 40
        else:
            issues.append("Pytest failed")

        if summary.get("mypy_clean"):
            score += 30
        else:
            issues.append("Type checking issues")

        overall_score = summary.get("overall_score", 0)
        if overall_score >= 80:
            score += 30
        elif overall_score >= 60:
            score += 20
        elif overall_score >= 40:
            score += 10

        return {"score": score, "issues": issues, "overall_score": overall_score}

    def _assess_deployment(self, deployment: Dict[str, Any]) -> Dict[str, Any]:
        """Assess deployment phase quality"""
        if not deployment:
            return {"score": 0, "issues": ["No deployment attempted"]}

        score = 0
        issues = []

        if deployment.get("status") == "success":
            score += 60
        elif deployment.get("status") == "failed":
            issues.append("Deployment failed")

        if deployment.get("url"):
            score += 20  # Has accessible URL

        if deployment.get("cluster_info"):
            score += 20  # Has cluster information

        return {"score": score, "issues": issues, "status": deployment.get("status")}

    async def _analyze_patterns(self, performance_data: Dict[str, Any]) -> List[LearningInsight]:
        """Analyze performance patterns and generate insights"""
        insights = []

        # Analyze planning patterns
        plan_insight = self._analyze_planning_patterns(performance_data)
        if plan_insight:
            insights.append(plan_insight)

        # Analyze code quality patterns
        code_insight = self._analyze_code_patterns(performance_data)
        if code_insight:
            insights.append(code_insight)

        # Analyze error patterns
        error_insight = self._analyze_error_patterns(performance_data)
        if error_insight:
            insights.append(error_insight)

        # Analyze success patterns
        success_insight = self._analyze_success_patterns(performance_data)
        if success_insight:
            insights.append(success_insight)

        return insights

    def _analyze_planning_patterns(self, data: Dict[str, Any]) -> Optional[LearningInsight]:
        """Analyze planning effectiveness patterns"""
        plan_quality = data.get("plan_quality", {})
        score = plan_quality.get("score", 0)

        if score < 50:
            return LearningInsight(
                category="planning_effectiveness",
                insight="Planning phase needs improvement",
                confidence=0.8,
                evidence=[f"Plan quality score: {score}", "Missing key planning elements"],
                recommendation="Enhance planning prompts and add more detailed task breakdown"
            )
        elif score > 80:
            return LearningInsight(
                category="planning_effectiveness",
                insight="Planning phase performing well",
                confidence=0.9,
                evidence=[f"Plan quality score: {score}", "Good task structure and dependencies"],
                recommendation="Maintain current planning approach"
            )

        return None

    def _analyze_code_patterns(self, data: Dict[str, Any]) -> Optional[LearningInsight]:
        """Analyze code generation patterns"""
        code_quality = data.get("code_quality", {})
        score = code_quality.get("score", 0)

        if score < 60:
            return LearningInsight(
                category="code_quality",
                insight="Code generation needs improvement",
                confidence=0.7,
                evidence=[f"Code quality score: {score}", "Missing documentation or tests"],
                recommendation="Improve code templates and add better documentation generation"
            )

        return None

    def _analyze_error_patterns(self, data: Dict[str, Any]) -> Optional[LearningInsight]:
        """Analyze error patterns"""
        errors = data.get("errors", [])

        if errors:
            error_types = defaultdict(int)
            for error in errors:
                if "Planning" in error:
                    error_types["planning"] += 1
                elif "Coding" in error:
                    error_types["coding"] += 1
                elif "Testing" in error:
                    error_types["testing"] += 1
                elif "Deployment" in error:
                    error_types["deployment"] += 1

            most_common = max(error_types.items(), key=lambda x: x[1]) if error_types else None

            if most_common:
                return LearningInsight(
                    category="error_patterns",
                    insight=f"Frequent {most_common[0]} errors detected",
                    confidence=0.8,
                    evidence=[f"{most_common[1]} {most_common[0]} errors", "Pattern analysis"],
                    recommendation=f"Focus on improving {most_common[0]} agent reliability"
                )

        return None

    def _analyze_success_patterns(self, data: Dict[str, Any]) -> Optional[LearningInsight]:
        """Analyze success patterns"""
        completed = data.get("completed", False)

        if completed and not data.get("errors"):
            return LearningInsight(
                category="performance_optimization",
                insight="Successful execution with no errors",
                confidence=0.9,
                evidence=["Task completed successfully", "No errors encountered"],
                recommendation="Analyze this execution pattern for replication"
            )

        return None

    async def _generate_optimizations(self, insights: List[LearningInsight], performance_data: Dict[str, Any]) -> List[str]:
        """Generate optimization suggestions based on insights"""
        optimizations = []

        for insight in insights:
            optimizations.append(insight.recommendation)

        # Add general optimizations based on performance data
        if performance_data.get("iteration", 0) > 1:
            optimizations.append("Consider caching intermediate results to reduce iterations")

        if len(performance_data.get("errors", [])) > 2:
            optimizations.append("Implement better error recovery mechanisms")

        return optimizations

    async def _update_memory(self, insights: List[LearningInsight], performance_data: Dict[str, Any]) -> List[str]:
        """Update memory with privacy-filtered insights"""
        memory_updates = []

        if self.memory_client:
            try:
                # Store insights in memory with privacy filtering
                for insight in insights:
                    filtered_insight = self._apply_privacy_filter(insight)

                    # Store in Mem0
                    memory_id = await self._store_in_memory(filtered_insight)
                    memory_updates.append(f"Stored insight {insight.category}: {memory_id}")

                # Store performance trends
                trends_id = await self._store_performance_trends(performance_data)
                memory_updates.append(f"Stored performance trends: {trends_id}")

            except Exception as e:
                self.logger.error(f"Failed to update memory: {e}")
                memory_updates.append(f"Memory update failed: {e}")
        else:
            # Fallback to in-memory storage
            for insight in insights:
                self.performance_history[insight.category].append({
                    "insight": insight.insight,
                    "timestamp": datetime.now().isoformat()
                })
            memory_updates.append("Stored insights in local memory (fallback)")

        return memory_updates

    def _apply_privacy_filter(self, insight: LearningInsight) -> LearningInsight:
        """Apply privacy filtering to insights"""
        # Remove any potentially sensitive information
        filtered_evidence = []
        for evidence in insight.evidence:
            # Remove specific file paths, URLs, or personal information
            filtered = evidence.replace("/home/", "/path/").replace("@", "[at]")
            filtered_evidence.append(filtered)

        return LearningInsight(
            category=insight.category,
            insight=insight.insight,
            confidence=insight.confidence,
            evidence=filtered_evidence,
            recommendation=insight.recommendation
        )

    async def _store_in_memory(self, insight: LearningInsight) -> str:
        """Store insight in Mem0 memory"""
        if not self.memory_client:
            return "memory_unavailable"

        try:
            # Create memory entry
            memory_data = {
                "category": insight.category,
                "insight": insight.insight,
                "confidence": insight.confidence,
                "recommendation": insight.recommendation,
                "timestamp": datetime.now().isoformat()
            }

            # Store in memory (simplified - actual Mem0 API may differ)
            result = self.memory_client.add(
                messages=[{"role": "system", "content": json.dumps(memory_data)}],
                user_id="artemis_swarm"
            )

            return str(result.get("id", "unknown"))

        except Exception as e:
            self.logger.error(f"Failed to store in memory: {e}")
            return f"error: {e}"

    async def _store_performance_trends(self, performance_data: Dict[str, Any]) -> str:
        """Store performance trends in memory"""
        if not self.memory_client:
            return "memory_unavailable"

        try:
            trends_data = {
                "type": "performance_trends",
                "data": performance_data,
                "timestamp": datetime.now().isoformat()
            }

            result = self.memory_client.add(
                messages=[{"role": "system", "content": json.dumps(trends_data)}],
                user_id="artemis_swarm_trends"
            )

            return str(result.get("id", "unknown"))

        except Exception as e:
            return f"error: {e}"

    def _analyze_trends(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        # Add current data to history
        timestamp = datetime.now().isoformat()
        self.performance_history["overall"].append({
            "timestamp": timestamp,
            "completed": performance_data.get("completed", False),
            "error_count": len(performance_data.get("errors", [])),
            "plan_score": performance_data.get("plan_quality", {}).get("score", 0),
            "code_score": performance_data.get("code_quality", {}).get("score", 0)
        })

        # Analyze trends (simplified)
        recent_data = self.performance_history["overall"][-10:]  # Last 10 executions

        if len(recent_data) > 1:
            success_rate = sum(1 for d in recent_data if d["completed"]) / len(recent_data)
            avg_errors = sum(d["error_count"] for d in recent_data) / len(recent_data)

            return {
                "success_rate": success_rate,
                "average_errors": avg_errors,
                "trend_direction": "improving" if success_rate > 0.7 else "needs_attention",
                "data_points": len(recent_data)
            }

        return {"insufficient_data": True}

    def _generate_learning_summary(self, result: EvolutionResult) -> Dict[str, Any]:
        """Generate a summary of learning outcomes"""
        return {
            "insights_generated": len(result.insights),
            "categories_analyzed": list(set(i.category for i in result.insights)),
            "high_confidence_insights": len([i for i in result.insights if i.confidence > 0.8]),
            "optimization_count": len(result.optimization_suggestions),
            "memory_updates": len(result.memory_updates),
            "privacy_filtered": result.privacy_filtered
        }

    async def _fallback_analysis(self, swarm_state: Any) -> Dict[str, Any]:
        """Fallback analysis when main evolution fails"""
        return {
            "basic_analysis": "Execution completed",
            "recommendation": "Review error logs for improvement opportunities",
            "method": "fallback"
        }

    def get_crewai_agent(self) -> Optional[Agent]:
        """Get CrewAI agent representation"""
        if not Agent:
            return None

        return Agent(
            role="AI Evolution Specialist",
            goal="Continuously improve swarm performance through learning and optimization",
            backstory="""You are an expert in artificial intelligence evolution and 
            machine learning optimization. You excel at analyzing performance patterns, 
            identifying improvement opportunities, and implementing self-learning systems 
            that enhance AI capabilities over time.""",
            verbose=True,
            allow_delegation=False
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "version": self.version,
            "status": self.status,
            "memory_available": self.memory_client is not None,
            "capabilities": [
                "pattern_analysis",
                "performance_optimization",
                "memory_management",
                "privacy_filtering",
                "trend_analysis"
            ],
            "learning_categories": self.learning_categories,
            "timestamp": datetime.now().isoformat()
        }

# Example usage
if __name__ == "__main__":
    async def main():
        evolver = EvolverAgent()

        # Mock swarm state
        class MockState:
            def __init__(self):
                self.intent = "Create API"
                self.completed = True
                self.errors = []
                self.plan = {"tasks": [{"id": "1", "title": "API"}]}
                self.code = {"files": {"main.py": {"content": "code"}}}
                self.tests = {"summary": {"pytest_passed": True}}
                self.deployment = {"status": "success"}

        result = await evolver.learn_and_improve(MockState())
        print(json.dumps(result, indent=2))

    asyncio.run(main())
