import asyncio
import logging
from dataclasses import dataclass
from typing import Any, List


logger = logging.getLogger(__name__)


@dataclass
class ConsensusSwarmConfig:
    """Configuration for :class:`ConsensusSwarm`."""

    consensus_threshold: int = 1


class ConsensusSwarm:
    """Orchestrates generators, critics and a judge to reach consensus.

    The swarm collects proposals from all generator agents in parallel.
    Each proposal is then reviewed by critic agents sequentially.  A
    proposal must receive a number of positive critic evaluations greater
    than or equal to ``consensus_threshold`` to be considered accepted.  The
    accepted proposal with the highest approval is sent to the judge agent
    for final decision.
    """

    def __init__(
        self,
        generators: List[Any],
        critics: List[Any],
        judge: Any,
        config: ConsensusSwarmConfig | None = None,
    ) -> None:
        self.generators = generators
        self.critics = critics
        self.judge = judge
        self.config = config or ConsensusSwarmConfig()
        self.logger = logging.getLogger(__name__)

    async def run(self, task: str) -> Any:
        """Execute the consensus swarm for a given task.

        Args:
            task: Problem statement provided to generator agents.

        Returns:
            Final decision from the judge agent.
        """
        self.logger.info("Collecting generator proposals")
        proposals = await asyncio.gather(
            *[gen.generate(task) for gen in self.generators]
        )

        best_proposal: Any | None = None
        best_score = -1

        # Evaluate proposals sequentially with critics
        for proposal in proposals:
            positive = 0
            for critic in self.critics:
                verdict = await critic.evaluate(proposal)
                if verdict:
                    positive += 1
            self.logger.debug(
                "Proposal evaluated with %d positive critic votes", positive
            )
            if positive >= self.config.consensus_threshold and positive > best_score:
                best_score = positive
                best_proposal = proposal

        # Fallback to first proposal if none reached threshold
        if best_proposal is None and proposals:
            best_proposal = proposals[0]

        self.logger.info("Sending best proposal to judge")
        final = await self.judge.judge(best_proposal)
        return final
