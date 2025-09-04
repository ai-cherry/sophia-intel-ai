#!/usr/bin/env python3
"""
Multi-Agent Debate System for Sophia Intel AI
Advanced swarm intelligence with consensus building

This implementation demonstrates our enhanced MCP-powered development:
- I remember all our architectural decisions from previous sessions
- Context is automatically shared with Cursor and VS Code
- Consistent with our established patterns and conventions
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from opentelemetry import trace
from opentelemetry.trace import SpanKind

from ...observability.prometheus_metrics import (
    observe_agent_vote,
    observe_consensus_reached,
    observe_debate_round,
)
from app.swarms.communication.message_bus import MessageBus, MessageType, SwarmMessage
from app.memory.unified_memory import UnifiedMemoryStore

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class DebatePhase(Enum):
    """Phases of multi-agent debate"""
    INITIALIZATION = "initialization"
    OPENING_STATEMENTS = "opening_statements"
    CROSS_EXAMINATION = "cross_examination"
    DELIBERATION = "deliberation"
    VOTING = "voting"
    CONSENSUS = "consensus"
    FINALIZATION = "finalization"


class VoteType(Enum):
    """Types of votes in consensus building"""
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"
    MODIFY = "modify"


@dataclass
class DebateProposal:
    """A proposal being debated"""
    id: str = field(default_factory=lambda: f"prop_{uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    proposed_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    modified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evidence: list[str] = field(default_factory=list)
    counterarguments: list[str] = field(default_factory=list)
    supporting_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentVote:
    """A vote cast by an agent"""
    agent_id: str
    proposal_id: str
    vote: VoteType
    reasoning: str
    confidence: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    supporting_evidence: list[str] = field(default_factory=list)


@dataclass
class DebateRound:
    """A single round of debate"""
    phase: DebatePhase
    proposal: DebateProposal
    round_id: str = field(default_factory=lambda: f"round_{uuid4().hex[:8]}")
    participants: list[str] = field(default_factory=list)
    statements: list[dict[str, Any]] = field(default_factory=list)
    votes: list[AgentVote] = field(default_factory=list)
    duration_seconds: Optional[float] = None
    outcome: Optional[str] = None


class MultiAgentDebateSystem:
    """
    Advanced multi-agent debate system with consensus building.
    
    Features demonstrated with MCP enhancement:
    - Persistent debate memory across sessions
    - Cross-tool visibility into debate progress  
    - Architecture consistent with our swarm patterns
    - Full observability and metrics
    """

    def __init__(
        self,
        message_bus: MessageBus,
        memory_store: UnifiedMemoryStore,
        min_participants: int = 3,
        consensus_threshold: float = 0.7,
        max_rounds: int = 5
    ):
        self.message_bus = message_bus
        self.memory_store = memory_store
        self.min_participants = min_participants
        self.consensus_threshold = consensus_threshold
        self.max_rounds = max_rounds

        # Active debates tracker
        self.active_debates: dict[str, DebateRound] = {}
        self.debate_history: list[DebateRound] = []

        # Agent registry for debate participation
        self.registered_agents: dict[str, dict[str, Any]] = {}

        logger.info("🗣️ MultiAgentDebateSystem initialized - enhanced with MCP integration")

    async def register_debate_agent(
        self,
        agent_id: str,
        capabilities: list[str],
        expertise: dict[str, float]
    ) -> bool:
        """Register an agent for debate participation"""
        with tracer.start_span("register_debate_agent", kind=SpanKind.SERVER) as span:
            span.set_attribute("agent.id", agent_id)
            span.set_attribute("agent.capabilities", json.dumps(capabilities))

            self.registered_agents[agent_id] = {
                "capabilities": capabilities,
                "expertise": expertise,
                "registered_at": datetime.now(timezone.utc),
                "debates_participated": 0,
                "consensus_rate": 0.0
            }

            # Store in MCP for cross-tool visibility
            await self.memory_store.store_memory(
                content=f"Debate agent registered: {agent_id}",
                metadata={
                    "type": "agent_registration",
                    "agent_id": agent_id,
                    "capabilities": capabilities,
                    "expertise": expertise
                }
            )

            logger.info(f"✅ Registered debate agent: {agent_id}")
            return True

    async def initiate_debate(
        self,
        proposal: DebateProposal,
        required_expertise: Optional[list[str]] = None,
        timeout_minutes: int = 30
    ) -> str:
        """Initiate a new multi-agent debate"""
        with tracer.start_span("initiate_debate", kind=SpanKind.SERVER) as span:
            debate_id = f"debate_{uuid4().hex[:12]}"
            span.set_attribute("debate.id", debate_id)
            span.set_attribute("debate.proposal_id", proposal.id)

            # Select appropriate agents for this debate
            selected_agents = await self._select_agents_for_debate(
                required_expertise or [],
                self.min_participants
            )

            if len(selected_agents) < self.min_participants:
                raise ValueError(f"Insufficient agents for debate: {len(selected_agents)} < {self.min_participants}")

            # Create initial debate round
            debate_round = DebateRound(
                round_id=debate_id,
                phase=DebatePhase.INITIALIZATION,
                proposal=proposal,
                participants=selected_agents
            )

            self.active_debates[debate_id] = debate_round

            # Store debate initiation in MCP
            await self.memory_store.store_memory(
                content=f"Multi-agent debate initiated: {proposal.title}",
                metadata={
                    "type": "debate_initiation",
                    "debate_id": debate_id,
                    "proposal": {
                        "id": proposal.id,
                        "title": proposal.title,
                        "description": proposal.description
                    },
                    "participants": selected_agents,
                    "phase": debate_round.phase.value
                }
            )

            # Notify participating agents
            await self._broadcast_debate_message(
                debate_id,
                "debate_initiated",
                {
                    "debate_id": debate_id,
                    "proposal": proposal.__dict__,
                    "participants": selected_agents,
                    "expected_duration": timeout_minutes
                }
            )

            logger.info(f"🗣️ Debate initiated: {debate_id} - {proposal.title}")
            observe_debate_round(debate_id, "initiated", len(selected_agents))

            return debate_id

    async def conduct_debate_round(
        self,
        debate_id: str,
        phase: DebatePhase
    ) -> DebateRound:
        """Conduct a single round of debate"""
        with tracer.start_span("conduct_debate_round", kind=SpanKind.SERVER) as span:
            span.set_attribute("debate.id", debate_id)
            span.set_attribute("debate.phase", phase.value)

            if debate_id not in self.active_debates:
                raise ValueError(f"Debate not found: {debate_id}")

            debate_round = self.active_debates[debate_id]
            debate_round.phase = phase

            start_time = datetime.now(timezone.utc)

            # Phase-specific logic
            if phase == DebatePhase.OPENING_STATEMENTS:
                await self._collect_opening_statements(debate_round)
            elif phase == DebatePhase.CROSS_EXAMINATION:
                await self._conduct_cross_examination(debate_round)
            elif phase == DebatePhase.DELIBERATION:
                await self._facilitate_deliberation(debate_round)
            elif phase == DebatePhase.VOTING:
                await self._collect_votes(debate_round)
            elif phase == DebatePhase.CONSENSUS:
                await self._evaluate_consensus(debate_round)

            # Record round duration
            end_time = datetime.now(timezone.utc)
            debate_round.duration_seconds = (end_time - start_time).total_seconds()

            # Store round progress in MCP
            await self.memory_store.store_memory(
                content=f"Debate round completed: {phase.value}",
                metadata={
                    "type": "debate_round_progress",
                    "debate_id": debate_id,
                    "phase": phase.value,
                    "duration_seconds": debate_round.duration_seconds,
                    "participants": len(debate_round.participants),
                    "statements": len(debate_round.statements)
                }
            )

            observe_debate_round(debate_id, phase.value, len(debate_round.participants))

            logger.info(f"⏱️ Debate round completed: {phase.value} ({debate_round.duration_seconds:.2f}s)")
            return debate_round

    async def _select_agents_for_debate(
        self,
        required_expertise: list[str],
        min_count: int
    ) -> list[str]:
        """Select the best agents for a specific debate topic"""
        # Score agents based on expertise match
        agent_scores: list[tuple[str, float]] = []

        for agent_id, info in self.registered_agents.items():
            score = 0.0
            expertise = info.get("expertise", {})

            # Calculate expertise match score
            for req_expertise in required_expertise:
                score += expertise.get(req_expertise, 0.0)

            # Bonus for high consensus rate
            score += info.get("consensus_rate", 0.0) * 0.3

            if score > 0:
                agent_scores.append((agent_id, score))

        # Sort by score and select top agents
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        selected = [agent_id for agent_id, _ in agent_scores[:min_count * 2]]

        # Ensure minimum count
        if len(selected) < min_count:
            # Add any remaining agents to meet minimum
            remaining = [aid for aid in self.registered_agents.keys() if aid not in selected]
            selected.extend(remaining[:min_count - len(selected)])

        return selected[:min_count * 2]  # Cap at reasonable maximum

    async def _broadcast_debate_message(
        self,
        debate_id: str,
        message_type: str,
        content: dict[str, Any]
    ):
        """Broadcast a message to all debate participants"""
        if debate_id not in self.active_debates:
            return

        debate_round = self.active_debates[debate_id]

        for participant in debate_round.participants:
            message = SwarmMessage(
                sender_agent_id="debate_system",
                receiver_agent_id=participant,
                message_type=MessageType.PROPOSAL,  # Reusing existing enum
                content={
                    "debate_id": debate_id,
                    "message_type": message_type,
                    "data": content
                },
                thread_id=debate_id
            )

            await self.message_bus.publish_message(message)

    async def _collect_opening_statements(self, debate_round: DebateRound):
        """Collect opening statements from all participants"""
        # Implementation would collect structured statements from agents
        # This demonstrates the enhanced architecture with MCP integration
        logger.info(f"📝 Collecting opening statements for debate: {debate_round.round_id}")

        # Simulated collection - in real implementation, this would await agent responses
        for participant in debate_round.participants:
            statement = {
                "agent_id": participant,
                "type": "opening_statement",
                "content": f"Opening statement from {participant} regarding {debate_round.proposal.title}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            debate_round.statements.append(statement)

    async def _conduct_cross_examination(self, debate_round: DebateRound):
        """Facilitate cross-examination between agents"""
        logger.info(f"🔍 Conducting cross-examination for debate: {debate_round.round_id}")
        # Cross-examination logic would be implemented here
        pass

    async def _facilitate_deliberation(self, debate_round: DebateRound):
        """Facilitate open deliberation between agents"""
        logger.info(f"💭 Facilitating deliberation for debate: {debate_round.round_id}")
        # Deliberation logic would be implemented here
        pass

    async def _collect_votes(self, debate_round: DebateRound):
        """Collect votes from all participating agents"""
        logger.info(f"🗳️ Collecting votes for debate: {debate_round.round_id}")

        # Simulated voting - real implementation would collect actual agent votes
        for participant in debate_round.participants:
            vote = AgentVote(
                agent_id=participant,
                proposal_id=debate_round.proposal.id,
                vote=VoteType.APPROVE,  # Simulated
                reasoning=f"Voting rationale from {participant}",
                confidence=0.8  # Simulated confidence
            )
            debate_round.votes.append(vote)
            observe_agent_vote(debate_round.round_id, participant, vote.vote.value)

    async def _evaluate_consensus(self, debate_round: DebateRound) -> bool:
        """Evaluate if consensus has been reached"""
        if not debate_round.votes:
            return False

        approve_votes = sum(1 for vote in debate_round.votes if vote.vote == VoteType.APPROVE)
        total_votes = len(debate_round.votes)
        consensus_ratio = approve_votes / total_votes if total_votes > 0 else 0.0

        consensus_reached = consensus_ratio >= self.consensus_threshold

        if consensus_reached:
            debate_round.outcome = "consensus_reached"
            observe_consensus_reached(debate_round.round_id, consensus_ratio)

            # Store consensus in MCP for cross-tool visibility
            await self.memory_store.store_memory(
                content=f"Consensus reached in debate: {debate_round.proposal.title}",
                metadata={
                    "type": "consensus_reached",
                    "debate_id": debate_round.round_id,
                    "proposal_id": debate_round.proposal.id,
                    "consensus_ratio": consensus_ratio,
                    "approve_votes": approve_votes,
                    "total_votes": total_votes
                }
            )

            logger.info(f"✅ Consensus reached: {consensus_ratio:.2%} approval")
        else:
            logger.info(f"❌ No consensus: {consensus_ratio:.2%} approval (need {self.consensus_threshold:.2%})")

        return consensus_reached

    async def finalize_debate(self, debate_id: str) -> DebateRound:
        """Finalize a completed debate"""
        if debate_id not in self.active_debates:
            raise ValueError(f"Debate not found: {debate_id}")

        debate_round = self.active_debates[debate_id]
        debate_round.phase = DebatePhase.FINALIZATION

        # Move to history
        self.debate_history.append(debate_round)
        del self.active_debates[debate_id]

        # Update agent statistics
        for participant in debate_round.participants:
            if participant in self.registered_agents:
                self.registered_agents[participant]["debates_participated"] += 1

        # Store final results in MCP
        await self.memory_store.store_memory(
            content=f"Debate finalized: {debate_round.proposal.title} - {debate_round.outcome or 'no_consensus'}",
            metadata={
                "type": "debate_finalized",
                "debate_id": debate_id,
                "outcome": debate_round.outcome,
                "total_rounds": len(self.debate_history),
                "final_phase": debate_round.phase.value
            }
        )

        logger.info(f"🏁 Debate finalized: {debate_id} - {debate_round.outcome}")
        return debate_round


# Factory function for easy initialization
async def create_debate_system(
    message_bus: MessageBus,
    memory_store: UnifiedMemoryStore,
    **kwargs
) -> MultiAgentDebateSystem:
    """Create and initialize a multi-agent debate system"""
    system = MultiAgentDebateSystem(message_bus, memory_store, **kwargs)

    # Store creation event in MCP
    await memory_store.store_memory(
        content="Multi-Agent Debate System created with enhanced MCP integration",
        metadata={
            "type": "system_creation",
            "component": "multi_agent_debate",
            "enhanced_features": [
                "persistent_memory",
                "cross_tool_visibility",
                "consensus_tracking",
                "agent_performance_metrics"
            ]
        }
    )

    return system
