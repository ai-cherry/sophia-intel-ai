"""
Quality Gates Pattern with automatic retry strategies.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging
import time

from .base import SwarmPattern, PatternConfig, PatternResult

logger = logging.getLogger(__name__)


@dataclass
class QualityGateConfig(PatternConfig):
    """Configuration for quality gates pattern."""
    min_quality_threshold: float = 0.7
    max_retry_rounds: int = 3
    quality_metrics: List[str] = field(default_factory=lambda: ["accuracy", "completeness", "coherence"])
    retry_strategies: Dict[str, str] = field(default_factory=lambda: {
        "low_quality": "expand_team",
        "medium_quality": "increase_creativity",
        "timeout": "simplify_problem"
    })
    progressive_threshold: bool = True  # Lower threshold with each retry
    threshold_decay: float = 0.05  # How much to lower threshold per retry


@dataclass
class QualityAssessment:
    """Result of quality assessment."""
    overall_score: float
    metric_scores: Dict[str, float]
    passed: bool
    feedback: List[str]
    assessor: str


class QualityGatesPattern(SwarmPattern):
    """
    Implements quality thresholds with automatic retry strategies.
    
    This pattern ensures outputs meet quality standards and automatically
    applies different strategies when quality is insufficient.
    """
    
    def __init__(self, config: Optional[QualityGateConfig] = None):
        """Initialize quality gates pattern."""
        super().__init__(config or QualityGateConfig())
        self.quality_history: List[QualityAssessment] = []
        self.retry_count = 0
        
    async def _setup(self) -> None:
        """Setup quality gate resources."""
        logger.info("Initializing Quality Gates Pattern")
        self.retry_count = 0
        
    async def _teardown(self) -> None:
        """Cleanup quality gate resources."""
        logger.info("Cleaning up Quality Gates Pattern")
        
    async def execute(self, context: Dict[str, Any], agents: List[Any]) -> PatternResult[Dict[str, Any]]:
        """
        Execute workflow with quality gates and retries.
        
        Args:
            context: Execution context with problem and constraints
            agents: List of available agents
            
        Returns:
            PatternResult containing the quality-assured result
        """
        start_time = time.time()
        self.retry_count = 0
        
        try:
            problem = context.get("problem", {})
            original_agents = agents.copy()
            current_threshold = self.config.min_quality_threshold
            
            for round_num in range(self.config.max_retry_rounds):
                self.retry_count = round_num
                
                # Adjust threshold if progressive
                if self.config.progressive_threshold and round_num > 0:
                    current_threshold = max(
                        current_threshold - self.config.threshold_decay,
                        0.5  # Never go below 0.5
                    )
                    logger.info(f"Adjusted quality threshold to {current_threshold}")
                
                # Execute workflow
                result = await self._execute_workflow(problem, agents)
                
                # Assess quality
                assessment = await self._assess_quality(result, agents)
                self.quality_history.append(assessment)
                
                logger.info(f"Round {round_num + 1}: Quality score = {assessment.overall_score}")
                
                # Check if quality meets threshold
                if assessment.overall_score >= current_threshold:
                    execution_time = time.time() - start_time
                    
                    return PatternResult(
                        success=True,
                        data={
                            "result": result,
                            "quality_assessment": assessment,
                            "rounds_required": round_num + 1,
                            "final_threshold": current_threshold
                        },
                        metrics={
                            "quality_score": assessment.overall_score,
                            "rounds": round_num + 1,
                            "threshold_used": current_threshold,
                            "metric_scores": assessment.metric_scores
                        },
                        pattern_name="quality_gates",
                        execution_time=execution_time
                    )
                
                # Apply retry strategy
                agents = await self._apply_retry_strategy(
                    agents, 
                    original_agents, 
                    assessment, 
                    round_num
                )
            
            # Max retries exceeded
            execution_time = time.time() - start_time
            
            return PatternResult(
                success=False,
                data={
                    "result": result,
                    "quality_assessment": assessment,
                    "rounds_required": self.config.max_retry_rounds
                },
                error=f"Quality threshold not met after {self.config.max_retry_rounds} retries",
                metrics={
                    "final_quality_score": assessment.overall_score,
                    "rounds": self.config.max_retry_rounds,
                    "threshold_required": current_threshold
                },
                pattern_name="quality_gates",
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Quality gates execution failed: {e}")
            return PatternResult(
                success=False,
                error=str(e),
                pattern_name="quality_gates",
                execution_time=time.time() - start_time
            )
    
    async def _execute_workflow(self, problem: Dict[str, Any], agents: List[Any]) -> Dict[str, Any]:
        """Execute the main workflow with given agents."""
        # In real implementation, this would coordinate agents to solve the problem
        # For now, simulate workflow execution
        
        await asyncio.sleep(0.5)  # Simulate processing
        
        # Simulate result generation with some randomness
        import random
        base_quality = 0.5 + (self.retry_count * 0.15)  # Improve with retries
        quality_variance = random.uniform(-0.2, 0.3)
        
        return {
            "solution": f"Solution for {problem.get('description', 'problem')}",
            "implementation": "Mock implementation details",
            "agents_used": [str(agent) for agent in agents[:3]],
            "simulated_quality": min(base_quality + quality_variance, 1.0),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _assess_quality(self, result: Dict[str, Any], agents: List[Any]) -> QualityAssessment:
        """Assess the quality of the result."""
        
        # Select assessor agent
        assessor = agents[0] if agents else "system"
        
        # Calculate metric scores (simulated)
        metric_scores = {}
        feedback = []
        
        # Use simulated quality if available (for testing)
        base_score = result.get("simulated_quality", 0.6)
        
        for metric in self.config.quality_metrics:
            if metric == "accuracy":
                score = min(base_score + 0.1, 1.0)
                if score < 0.7:
                    feedback.append("Accuracy needs improvement")
            elif metric == "completeness":
                score = min(base_score, 1.0)
                if score < 0.8:
                    feedback.append("Solution incomplete")
            elif metric == "coherence":
                score = min(base_score + 0.05, 1.0)
                if score < 0.6:
                    feedback.append("Logic flow unclear")
            else:
                score = base_score
                
            metric_scores[metric] = score
        
        # Calculate overall score
        overall_score = sum(metric_scores.values()) / len(metric_scores) if metric_scores else 0.0
        
        # Add general feedback
        if overall_score >= 0.9:
            feedback.append("Excellent quality")
        elif overall_score >= 0.7:
            feedback.append("Good quality, minor improvements possible")
        else:
            feedback.append("Significant quality issues detected")
        
        return QualityAssessment(
            overall_score=overall_score,
            metric_scores=metric_scores,
            passed=overall_score >= self.config.min_quality_threshold,
            feedback=feedback,
            assessor=str(assessor)
        )
    
    async def _apply_retry_strategy(self, 
                                   agents: List[Any], 
                                   original_agents: List[Any],
                                   assessment: QualityAssessment, 
                                   round_num: int) -> List[Any]:
        """Apply retry strategy based on quality assessment."""
        
        quality_level = assessment.overall_score
        
        if quality_level < 0.4:
            strategy = self.config.retry_strategies.get("low_quality", "expand_team")
        elif quality_level < 0.6:
            strategy = self.config.retry_strategies.get("medium_quality", "increase_creativity")
        else:
            strategy = "refine"
        
        logger.info(f"Applying retry strategy: {strategy}")
        
        if strategy == "expand_team":
            # Add more agents if available
            return await self._expand_agent_team(agents, original_agents)
        elif strategy == "increase_creativity":
            # Adjust agent parameters
            return await self._increase_creativity(agents)
        elif strategy == "simplify_problem":
            # This would modify the problem context
            return agents
        else:
            # Default: keep same agents
            return agents
    
    async def _expand_agent_team(self, current: List[Any], available: List[Any]) -> List[Any]:
        """Expand the agent team with additional members."""
        # Add agents not currently in the team
        additional = [a for a in available if a not in current]
        
        if additional:
            # Add up to 2 more agents
            to_add = additional[:min(2, len(additional))]
            logger.info(f"Adding {len(to_add)} agents to team")
            return current + to_add
        
        return current
    
    async def _increase_creativity(self, agents: List[Any]) -> List[Any]:
        """Adjust agent parameters to increase creativity."""
        # In real implementation, this would adjust temperature, top_p, etc.
        logger.info("Increasing agent creativity parameters")
        
        # For now, just shuffle the order to change dynamics
        import random
        shuffled = agents.copy()
        random.shuffle(shuffled)
        return shuffled
    
    def get_quality_trends(self) -> Dict[str, Any]:
        """Analyze quality trends across executions."""
        if not self.quality_history:
            return {}
        
        scores = [a.overall_score for a in self.quality_history]
        
        return {
            "average_quality": sum(scores) / len(scores),
            "min_quality": min(scores),
            "max_quality": max(scores),
            "improvement_rate": (scores[-1] - scores[0]) / len(scores) if len(scores) > 1 else 0,
            "pass_rate": sum(1 for a in self.quality_history if a.passed) / len(self.quality_history)
        }