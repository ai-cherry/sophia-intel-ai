---
title: Swarm Communication Protocols
type: reference
status: active
version: 1.0.0
last_updated: 2025-09-01
ai_context: high
tags: [swarms, protocols, communication, handoffs]
---

# 🔄 Swarm Communication Protocols

This document defines the communication protocols for agent swarms in Sophia Intel AI, following the standards in `.ai-instructions/orchestration-standards.md`.

## 📋 Prerequisites

- Understanding of orchestration patterns (Sequential, Concurrent, Hierarchical)
- Familiarity with UnifiedOrchestratorFacade
- Knowledge of agent definitions in `agents.yaml`

## 🎯 Message Protocol

### Standard Message Format

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from enum import Enum

class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    HANDOFF = "handoff"
    ERROR = "error"
    STATUS = "status"
    HEARTBEAT = "heartbeat"

@dataclass
class AgentMessage:
    """Standard message format for inter-agent communication"""
    from_agent: str              # Agent ID sending the message
    to_agent: str               # Agent ID receiving the message
    message_type: MessageType   # Type of message
    content: Any               # Message payload
    timestamp: datetime        # Message timestamp
    correlation_id: str       # Request tracking ID
    priority: int            # 0-10, higher = more urgent
    context: Dict[str, Any]  # Shared context

    def to_json(self) -> str:
        """Serialize for transport"""
        return json.dumps({
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "priority": self.priority,
            "context": self.context
        })
```

## 🔄 Handoff Protocol

### Clean Handoff Between Agents

```python
class HandoffProtocol:
    """Manages agent handoffs following OpenAI Swarm patterns"""

    async def handoff(
        self,
        from_agent: Agent,
        to_agent: Agent,
        context: Dict[str, Any]
    ) -> HandoffResult:
        """
        Execute a clean handoff between agents

        Steps:
        1. Validate to_agent can handle task
        2. Package context for transfer
        3. Transfer context and state
        4. Confirm handoff received
        5. Clean up from_agent resources
        """
        # Step 1: Validate capability
        if not to_agent.can_handle(context['task']):
            raise HandoffError(f"{to_agent.id} cannot handle task")

        # Step 2: Package context
        handoff_package = {
            "task": context['task'],
            "state": from_agent.get_state(),
            "memory": await from_agent.export_memory(),
            "metadata": {
                "from_agent": from_agent.id,
                "handoff_time": datetime.now(),
                "reason": context.get('handoff_reason', 'task_completion')
            }
        }

        # Step 3: Transfer
        await to_agent.receive_context(handoff_package)

        # Step 4: Confirm
        confirmation = await to_agent.confirm_handoff()
        if not confirmation.success:
            raise HandoffError(f"Handoff failed: {confirmation.error}")

        # Step 5: Cleanup
        await from_agent.cleanup()

        return HandoffResult(
            success=True,
            from_agent=from_agent.id,
            to_agent=to_agent.id,
            timestamp=datetime.now()
        )
```

### Handoff Scenarios

```python
# 1. Task Completion Handoff
if task_complete and next_stage_required:
    await handoff_protocol.handoff(
        from_agent=code_generator,
        to_agent=code_reviewer,
        context={"task": task, "code": generated_code}
    )

# 2. Expertise Required Handoff
if requires_security_expertise:
    await handoff_protocol.handoff(
        from_agent=current_agent,
        to_agent=security_specialist,
        context={"task": task, "security_concern": concern}
    )

# 3. Error Recovery Handoff
if error_occurred and not recoverable:
    await handoff_protocol.handoff(
        from_agent=current_agent,
        to_agent=error_handler,
        context={"task": task, "error": error_details}
    )
```

## 📡 Broadcasting Protocol

### Multi-Agent Broadcast

```python
class BroadcastProtocol:
    """Manages broadcasting to multiple agents"""

    async def broadcast(
        self,
        sender: Agent,
        recipients: List[Agent],
        message: Any,
        pattern: str = "fanout"
    ) -> BroadcastResult:
        """
        Broadcast message to multiple agents

        Patterns:
        - fanout: All agents receive simultaneously
        - cascade: Sequential delivery with acknowledgment
        - selective: Only agents matching criteria
        """
        if pattern == "fanout":
            results = await asyncio.gather(*[
                agent.receive_message(message)
                for agent in recipients
            ])
        elif pattern == "cascade":
            results = []
            for agent in recipients:
                result = await agent.receive_message(message)
                results.append(result)
                if not result.success:
                    break
        elif pattern == "selective":
            eligible = [a for a in recipients if a.matches_criteria(message)]
            results = await asyncio.gather(*[
                agent.receive_message(message)
                for agent in eligible
            ])

        return BroadcastResult(
            sender=sender.id,
            recipients=[a.id for a in recipients],
            pattern=pattern,
            results=results
        )
```

## 🗳️ Consensus Protocol

### Multi-Agent Consensus

```python
class ConsensusProtocol:
    """Manages consensus building among agents"""

    async def build_consensus(
        self,
        agents: List[Agent],
        proposal: Any,
        threshold: float = 0.7
    ) -> ConsensusResult:
        """
        Build consensus among agents

        Voting mechanisms:
        - Simple majority (>50%)
        - Super majority (>66%)
        - Unanimous (100%)
        - Weighted (based on expertise)
        """
        # Collect votes
        votes = await asyncio.gather(*[
            agent.vote_on_proposal(proposal)
            for agent in agents
        ])

        # Calculate consensus
        agree_count = sum(1 for v in votes if v.agrees)
        consensus_ratio = agree_count / len(votes)

        # Apply weighted voting if configured
        if self.use_weighted_voting:
            weighted_score = sum(
                v.confidence * v.expertise_weight
                for v in votes if v.agrees
            )
            total_weight = sum(v.expertise_weight for v in votes)
            consensus_ratio = weighted_score / total_weight

        return ConsensusResult(
            achieved=consensus_ratio >= threshold,
            ratio=consensus_ratio,
            threshold=threshold,
            votes=votes,
            proposal=proposal
        )
```

## 🔄 State Synchronization

### Distributed State Management

```python
class StateSyncProtocol:
    """Manages state synchronization across agents"""

    async def sync_state(
        self,
        agents: List[Agent],
        state_type: str = "full"
    ) -> SyncResult:
        """
        Synchronize state across agents

        Types:
        - full: Complete state synchronization
        - incremental: Only changes since last sync
        - selective: Specific state components
        """
        if state_type == "full":
            # Get canonical state
            canonical_state = await self.get_canonical_state()

            # Distribute to all agents
            results = await asyncio.gather(*[
                agent.update_state(canonical_state)
                for agent in agents
            ])

        elif state_type == "incremental":
            # Get state changes
            changes = await self.get_state_changes()

            # Apply changes to agents
            results = await asyncio.gather(*[
                agent.apply_state_changes(changes)
                for agent in agents
            ])

        return SyncResult(
            success=all(r.success for r in results),
            synced_agents=[a.id for a in agents],
            sync_type=state_type,
            timestamp=datetime.now()
        )
```

## 📊 Performance Monitoring

### Protocol Metrics

```python
class ProtocolMetrics:
    """Track protocol performance"""

    def __init__(self):
        self.metrics = {
            "message_count": 0,
            "handoff_count": 0,
            "handoff_failures": 0,
            "broadcast_count": 0,
            "consensus_attempts": 0,
            "consensus_achieved": 0,
            "avg_handoff_time": 0,
            "avg_consensus_time": 0,
            "state_sync_count": 0
        }

    async def track_handoff(self, duration: float, success: bool):
        """Track handoff metrics"""
        self.metrics["handoff_count"] += 1
        if not success:
            self.metrics["handoff_failures"] += 1

        # Update rolling average
        current_avg = self.metrics["avg_handoff_time"]
        count = self.metrics["handoff_count"]
        self.metrics["avg_handoff_time"] = (
            (current_avg * (count - 1) + duration) / count
        )
```

## 🛡️ Error Handling

### Protocol Error Recovery

```python
class ProtocolErrorHandler:
    """Handle protocol-level errors"""

    async def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> ErrorRecoveryResult:
        """
        Handle protocol errors with appropriate recovery
        """
        if isinstance(error, HandoffError):
            # Try alternative agent
            alternative = await self.find_alternative_agent(
                context["to_agent"],
                context["task"]
            )
            if alternative:
                return await self.retry_handoff(alternative, context)

        elif isinstance(error, ConsensusTimeout):
            # Use fallback decision mechanism
            return await self.fallback_decision(context)

        elif isinstance(error, BroadcastFailure):
            # Retry with exponential backoff
            return await self.retry_broadcast_with_backoff(context)

        # Default: escalate to human
        return ErrorRecoveryResult(
            recovered=False,
            escalation_required=True,
            error=error
        )
```

## ✅ Validation

To validate protocol implementation:

```python
# Run protocol tests
pytest tests/test_protocols.py

# Check protocol compliance
python scripts/validate_protocols.py

# Monitor protocol metrics
python scripts/monitor_protocols.py
```

## 📚 Related

- [Orchestration Standards](../../.ai-instructions/orchestration-standards.md)
- [Agent Definitions](agents.yaml)
- [Safety Boundaries](safety.md)
- [Unified Facade](../../app/orchestration/unified_facade.py)
