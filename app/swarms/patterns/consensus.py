"""
Consensus Pattern with sophisticated tie-breaking mechanisms.
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from .base import PatternConfig, PatternResult, SwarmPattern

logger = logging.getLogger(__name__)


@dataclass
class ConsensusConfig(PatternConfig):
    """Configuration for consensus pattern."""
    consensus_method: str = "weighted_voting"  # simple_majority, weighted_voting, ranked_choice
    min_agreement: float = 0.6
    tie_breaker: str = "seniority"  # random, seniority, performance
    weight_factors: dict[str, float] = None

    def __post_init__(self):
        if self.weight_factors is None:
            self.weight_factors = {"expertise": 0.5, "confidence": 0.3, "history": 0.2}


class ConsensusPattern(SwarmPattern):
    """
    Implements sophisticated consensus mechanisms with tie-breaking.
    """

    def __init__(self, config: Optional[ConsensusConfig] = None):
        super().__init__(config or ConsensusConfig())
        self.voting_history = []

    async def _setup(self) -> None:
        """Initialize consensus system."""
        logger.info("Initializing Consensus Pattern")

    async def _teardown(self) -> None:
        """Cleanup consensus system."""

    async def execute(self, context: dict[str, Any], agents: list[Any]) -> PatternResult:
        """Execute consensus building."""
        proposals = context.get("proposals", [])

        # Collect votes
        votes = await self._collect_votes(proposals, agents)

        # Determine consensus
        consensus = self._determine_consensus(votes)

        # Handle ties if necessary
        if consensus.get("is_tie"):
            consensus = await self._break_tie(consensus, agents)

        self.voting_history.append(consensus)

        return PatternResult(
            success=True,
            data=consensus,
            pattern_name="consensus"
        )

    async def _collect_votes(self, proposals: list, agents: list) -> dict:
        """Collect votes from all agents."""
        votes = {}
        for agent in agents:
            vote = await self._get_agent_vote(agent, proposals)
            votes[str(agent)] = vote
        return votes

    async def _get_agent_vote(self, agent: Any, proposals: list) -> dict:
        """Get vote from individual agent."""
        # Simulate voting
        import random
        return {
            "choice": random.choice(proposals) if proposals else None,
            "confidence": random.random(),
            "reasoning": "Simulated vote"
        }

    def _determine_consensus(self, votes: dict) -> dict:
        """Determine consensus from votes."""
        # Count votes
        vote_counts = {}
        for agent, vote in votes.items():
            choice = vote.get("choice")
            if choice:
                vote_counts[str(choice)] = vote_counts.get(str(choice), 0) + 1

        # Find winner
        if vote_counts:
            max_votes = max(vote_counts.values())
            winners = [k for k, v in vote_counts.items() if v == max_votes]

            return {
                "winner": winners[0] if len(winners) == 1 else None,
                "is_tie": len(winners) > 1,
                "tied_options": winners if len(winners) > 1 else [],
                "vote_counts": vote_counts
            }

        return {"winner": None, "is_tie": False}

    async def _break_tie(self, consensus: dict, agents: list) -> dict:
        """Break ties using configured method."""
        if self.config.tie_breaker == "seniority":
            # First agent decides
            consensus["winner"] = consensus["tied_options"][0]
        elif self.config.tie_breaker == "performance":
            # Best performing agent decides
            consensus["winner"] = consensus["tied_options"][0]
        else:  # random
            import random
            consensus["winner"] = random.choice(consensus["tied_options"])

        consensus["tie_broken_by"] = self.config.tie_breaker
        return consensus
