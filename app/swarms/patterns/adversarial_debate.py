"""
Adversarial Debate Pattern for solution quality improvement through structured argumentation.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from .base import PatternConfig, PatternResult, SwarmPattern

logger = logging.getLogger(__name__)


@dataclass
class DebateConfig(PatternConfig):
    """Configuration for adversarial debate pattern."""
    min_participants: int = 3
    max_debate_rounds: int = 3
    argument_timeout: float = 30.0
    require_consensus: bool = False
    judge_selection: str = "random"  # random, rotating, designated
    scoring_method: str = "weighted"  # weighted, simple, ranked


@dataclass
class DebateResult:
    """Result of a debate session."""
    solution: dict[str, Any]
    pro_arguments: list[dict[str, Any]]
    con_arguments: list[dict[str, Any]]
    verdict: dict[str, Any]
    score: float
    rounds: int
    participants: list[str]


class AdversarialDebatePattern(SwarmPattern):
    """
    Implements structured debate between agents to improve solution quality.
    
    This pattern assigns agents to advocate for or against proposed solutions,
    with a judge evaluating arguments to select the best approach.
    """

    def __init__(self, config: Optional[DebateConfig] = None):
        """Initialize adversarial debate pattern."""
        super().__init__(config or DebateConfig())
        self.debate_history: list[DebateResult] = []
        self.judge_rotation_index = 0

    async def _setup(self) -> None:
        """Setup debate resources."""
        logger.info("Initializing Adversarial Debate Pattern")

    async def _teardown(self) -> None:
        """Cleanup debate resources."""
        logger.info("Cleaning up Adversarial Debate Pattern")

    async def execute(self, context: dict[str, Any], agents: list[Any]) -> PatternResult[DebateResult]:
        """
        Execute adversarial debate on proposed solutions.
        
        Args:
            context: Must contain 'problem' and 'solutions' keys
            agents: List of available agents (minimum 3 required)
            
        Returns:
            PatternResult containing the winning solution and debate details
        """
        start_time = time.time()

        try:
            # Validate inputs
            if len(agents) < self.config.min_participants:
                return PatternResult(
                    success=False,
                    error=f"Insufficient agents: {len(agents)} < {self.config.min_participants}",
                    pattern_name="adversarial_debate"
                )

            problem = context.get("problem", "")
            solutions = context.get("solutions", [])

            if not solutions:
                return PatternResult(
                    success=False,
                    error="No solutions provided for debate",
                    pattern_name="adversarial_debate"
                )

            # Conduct debate for each solution
            debate_results = []
            for solution in solutions:
                result = await self._debate_solution(problem, solution, agents)
                debate_results.append(result)

            # Select best solution
            best_debate = max(debate_results, key=lambda x: x.score)

            # Record in history
            self.debate_history.append(best_debate)

            execution_time = time.time() - start_time

            return PatternResult(
                success=True,
                data=best_debate,
                metrics={
                    "total_solutions": len(solutions),
                    "debate_rounds": best_debate.rounds,
                    "winning_score": best_debate.score,
                    "participants": len(best_debate.participants)
                },
                pattern_name="adversarial_debate",
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"Debate execution failed: {e}")
            return PatternResult(
                success=False,
                error=str(e),
                pattern_name="adversarial_debate",
                execution_time=time.time() - start_time
            )

    async def _debate_solution(self, problem: str, solution: dict[str, Any], agents: list[Any]) -> DebateResult:
        """Conduct debate for a single solution."""

        # Select participants
        advocate = random.choice(agents)
        remaining = [a for a in agents if a != advocate]
        critic = random.choice(remaining) if remaining else advocate
        judge = self._select_judge(agents, [advocate, critic])

        pro_arguments = []
        con_arguments = []

        # Conduct debate rounds
        for round_num in range(self.config.max_debate_rounds):
            # Generate arguments
            pro_arg = await self._generate_argument(advocate, solution, "support", round_num)
            con_arg = await self._generate_argument(critic, solution, "oppose", round_num)

            pro_arguments.append(pro_arg)
            con_arguments.append(con_arg)

            # Early termination if consensus reached
            if self.config.require_consensus:
                consensus = await self._check_consensus(pro_arg, con_arg)
                if consensus:
                    break

        # Judge evaluates
        verdict = await self._evaluate_debate(judge, pro_arguments, con_arguments, solution)

        return DebateResult(
            solution=solution,
            pro_arguments=pro_arguments,
            con_arguments=con_arguments,
            verdict=verdict,
            score=verdict.get("score", 0.5),
            rounds=len(pro_arguments),
            participants=[str(advocate), str(critic), str(judge)]
        )

    def _select_judge(self, agents: list[Any], exclude: list[Any]) -> Any:
        """Select judge based on configuration."""
        available = [a for a in agents if a not in exclude]

        if not available:
            return random.choice(agents)

        if self.config.judge_selection == "rotating":
            judge = available[self.judge_rotation_index % len(available)]
            self.judge_rotation_index += 1
            return judge
        elif self.config.judge_selection == "designated":
            # Could implement logic to select most experienced agent
            return available[0]
        else:  # random
            return random.choice(available)

    async def _generate_argument(self, agent: Any, solution: dict[str, Any], stance: str, round_num: int) -> dict[str, Any]:
        """Generate argument for or against solution."""
        # In real implementation, this would call the agent's LLM
        # For now, return simulated argument

        await asyncio.sleep(0.1)  # Simulate processing time

        if stance == "support":
            points = [
                f"Efficient implementation (Round {round_num + 1})",
                "Scalable architecture",
                "Well-tested approach"
            ]
            confidence = 0.85 - (round_num * 0.05)  # Decrease confidence over rounds
        else:
            points = [
                f"Potential edge cases not covered (Round {round_num + 1})",
                "Performance concerns at scale",
                "Maintenance complexity"
            ]
            confidence = 0.75 - (round_num * 0.05)

        return {
            "agent": str(agent),
            "stance": stance,
            "round": round_num + 1,
            "points": points,
            "confidence": max(confidence, 0.3),
            "timestamp": datetime.now().isoformat()
        }

    async def _evaluate_debate(self, judge: Any, pro_args: list[dict], con_args: list[dict], solution: dict) -> dict[str, Any]:
        """Judge evaluates the debate."""

        if self.config.scoring_method == "weighted":
            # Weight later arguments more heavily
            pro_score = sum(arg["confidence"] * (1 + i * 0.1) for i, arg in enumerate(pro_args))
            con_score = sum(arg["confidence"] * (1 + i * 0.1) for i, arg in enumerate(con_args))
        elif self.config.scoring_method == "ranked":
            # Rank arguments and use rankings
            pro_score = sum(arg["confidence"] * (len(pro_args) - i) for i, arg in enumerate(pro_args))
            con_score = sum(arg["confidence"] * (len(con_args) - i) for i, arg in enumerate(con_args))
        else:  # simple
            pro_score = sum(arg["confidence"] for arg in pro_args)
            con_score = sum(arg["confidence"] for arg in con_args)

        # Normalize scores
        total_score = pro_score + con_score
        if total_score > 0:
            pro_normalized = pro_score / total_score
            con_normalized = con_score / total_score
        else:
            pro_normalized = con_normalized = 0.5

        decision = "accept" if pro_normalized > con_normalized else "reject"
        final_score = pro_normalized if decision == "accept" else (1 - con_normalized)

        return {
            "judge": str(judge),
            "decision": decision,
            "score": final_score,
            "pro_strength": pro_normalized,
            "con_strength": con_normalized,
            "scoring_method": self.config.scoring_method,
            "reasoning": f"Pro arguments: {pro_normalized:.2f}, Con arguments: {con_normalized:.2f}"
        }

    async def _check_consensus(self, pro_arg: dict, con_arg: dict) -> bool:
        """Check if consensus has been reached."""
        # Simple consensus check based on confidence levels
        return abs(pro_arg["confidence"] - con_arg["confidence"]) > 0.3
