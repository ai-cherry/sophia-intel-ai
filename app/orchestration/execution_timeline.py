"""
Execution Timeline for Swarm Orchestration
Tracks agent actions, debate steps, quality gates, and patterns.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events in the execution timeline."""
    SWARM_START = "swarm_start"
    SWARM_END = "swarm_end"
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    AGENT_MESSAGE = "agent_message"
    DEBATE_START = "debate_start"
    DEBATE_TURN = "debate_turn"
    DEBATE_END = "debate_end"
    GATE_CHECK = "gate_check"
    GATE_RESULT = "gate_result"
    PATTERN_DETECTED = "pattern_detected"
    MEMORY_ACCESS = "memory_access"
    MEMORY_STORE = "memory_store"
    COST_UPDATE = "cost_update"
    ERROR = "error"
    MILESTONE = "milestone"


@dataclass
class TimelineEvent:
    """A single event in the execution timeline."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: EventType = EventType.AGENT_MESSAGE
    agent_id: Optional[str] = None
    agent_role: Optional[str] = None
    model: Optional[str] = None
    content: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    cost: Optional[float] = None
    tokens: Optional[int] = None
    duration_ms: Optional[float] = None
    parent_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "agent_role": self.agent_role,
            "model": self.model,
            "content": self.content,
            "metadata": self.metadata,
            "cost": self.cost,
            "tokens": self.tokens,
            "duration_ms": self.duration_ms,
            "parent_id": self.parent_id
        }


@dataclass
class ExecutionPattern:
    """Reusable pattern detected during execution."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    pattern_type: str = "sequence"  # sequence, debate, consensus, etc.
    steps: list[str] = field(default_factory=list)
    success_rate: float = 0.0
    avg_duration_ms: float = 0.0
    avg_cost: float = 0.0
    usage_count: int = 0
    last_used: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "pattern_type": self.pattern_type,
            "steps": self.steps,
            "success_rate": self.success_rate,
            "avg_duration_ms": self.avg_duration_ms,
            "avg_cost": self.avg_cost,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "metadata": self.metadata
        }


class ExecutionTimeline:
    """
    Manages the execution timeline for swarm orchestration.
    Records events, detects patterns, and provides analysis.
    """

    def __init__(self, session_id: Optional[str] = None):
        """Initialize execution timeline."""
        self.session_id = session_id or str(uuid.uuid4())
        self.events: list[TimelineEvent] = []
        self.patterns: dict[str, ExecutionPattern] = {}
        self.active_agents: set[str] = set()
        self.total_cost: float = 0.0
        self.total_tokens: int = 0
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._event_callbacks: list[callable] = []
        self._pattern_callbacks: list[callable] = []

    def add_event(self, event: TimelineEvent) -> None:
        """Add an event to the timeline."""
        self.events.append(event)

        # Update metrics
        if event.cost:
            self.total_cost += event.cost
        if event.tokens:
            self.total_tokens += event.tokens

        # Track active agents
        if event.event_type == EventType.AGENT_START and event.agent_id:
            self.active_agents.add(event.agent_id)
        elif event.event_type == EventType.AGENT_END and event.agent_id:
            self.active_agents.discard(event.agent_id)

        # Track swarm timing
        if event.event_type == EventType.SWARM_START:
            self.start_time = event.timestamp
        elif event.event_type == EventType.SWARM_END:
            self.end_time = event.timestamp

        # Notify callbacks
        for callback in self._event_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")

    async def add_event_async(self, event: TimelineEvent) -> None:
        """Add an event asynchronously."""
        self.add_event(event)

        # Detect patterns asynchronously
        await self._detect_patterns_async(event)

    def record_swarm_start(self, swarm_type: str, task: str, metadata: dict[str, Any] = None) -> str:
        """Record the start of a swarm execution."""
        event = TimelineEvent(
            event_type=EventType.SWARM_START,
            content=f"Starting {swarm_type} swarm for task: {task}",
            metadata=metadata or {}
        )
        self.add_event(event)
        return event.id

    def record_swarm_end(self, parent_id: str, result: str, success: bool) -> None:
        """Record the end of a swarm execution."""
        duration_ms = None
        if self.start_time and self.end_time:
            duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

        event = TimelineEvent(
            event_type=EventType.SWARM_END,
            parent_id=parent_id,
            content=result,
            metadata={"success": success},
            duration_ms=duration_ms,
            cost=self.total_cost,
            tokens=self.total_tokens
        )
        self.add_event(event)

    def record_agent_action(
        self,
        agent_id: str,
        agent_role: str,
        action: str,
        model: str,
        content: str,
        cost: float = 0,
        tokens: int = 0,
        metadata: dict[str, Any] = None
    ) -> None:
        """Record an agent action."""
        event = TimelineEvent(
            event_type=EventType.AGENT_MESSAGE,
            agent_id=agent_id,
            agent_role=agent_role,
            model=model,
            content=content,
            cost=cost,
            tokens=tokens,
            metadata=metadata or {}
        )
        self.add_event(event)

    def record_debate_turn(
        self,
        debate_id: str,
        agent_id: str,
        agent_role: str,
        position: str,
        argument: str,
        model: str,
        metadata: dict[str, Any] = None
    ) -> None:
        """Record a debate turn."""
        event = TimelineEvent(
            event_type=EventType.DEBATE_TURN,
            parent_id=debate_id,
            agent_id=agent_id,
            agent_role=agent_role,
            model=model,
            content=f"{position}: {argument}",
            metadata=metadata or {}
        )
        self.add_event(event)

    def record_gate_check(
        self,
        gate_name: str,
        gate_type: str,
        input_data: Any,
        metadata: dict[str, Any] = None
    ) -> str:
        """Record a quality gate check."""
        event = TimelineEvent(
            event_type=EventType.GATE_CHECK,
            content=f"Checking {gate_name} ({gate_type})",
            metadata={
                "gate_name": gate_name,
                "gate_type": gate_type,
                "input_preview": str(input_data)[:200],
                **(metadata or {})
            }
        )
        self.add_event(event)
        return event.id

    def record_gate_result(
        self,
        gate_check_id: str,
        passed: bool,
        score: float,
        feedback: str,
        metadata: dict[str, Any] = None
    ) -> None:
        """Record a quality gate result."""
        event = TimelineEvent(
            event_type=EventType.GATE_RESULT,
            parent_id=gate_check_id,
            content=f"Gate {'passed' if passed else 'failed'}: {feedback}",
            metadata={
                "passed": passed,
                "score": score,
                **(metadata or {})
            }
        )
        self.add_event(event)

    def record_pattern(self, pattern: ExecutionPattern) -> None:
        """Record a detected execution pattern."""
        self.patterns[pattern.id] = pattern

        event = TimelineEvent(
            event_type=EventType.PATTERN_DETECTED,
            content=f"Pattern detected: {pattern.name}",
            metadata=pattern.to_dict()
        )
        self.add_event(event)

        # Notify pattern callbacks
        for callback in self._pattern_callbacks:
            try:
                callback(pattern)
            except Exception as e:
                logger.error(f"Error in pattern callback: {e}")

    def record_memory_access(
        self,
        memory_type: str,
        query: str,
        results_count: int,
        metadata: dict[str, Any] = None
    ) -> None:
        """Record memory access."""
        event = TimelineEvent(
            event_type=EventType.MEMORY_ACCESS,
            content=f"Accessed {memory_type} memory: {query}",
            metadata={
                "memory_type": memory_type,
                "results_count": results_count,
                **(metadata or {})
            }
        )
        self.add_event(event)

    def record_memory_store(
        self,
        memory_type: str,
        content: str,
        tags: list[str],
        metadata: dict[str, Any] = None
    ) -> None:
        """Record memory storage."""
        event = TimelineEvent(
            event_type=EventType.MEMORY_STORE,
            content=f"Stored in {memory_type} memory",
            metadata={
                "memory_type": memory_type,
                "content_preview": content[:200],
                "tags": tags,
                **(metadata or {})
            }
        )
        self.add_event(event)

    def record_cost_update(self, cost: float, model: str, tokens: int) -> None:
        """Record a cost update."""
        event = TimelineEvent(
            event_type=EventType.COST_UPDATE,
            content=f"Cost update: ${cost:.4f} for {tokens} tokens",
            model=model,
            cost=cost,
            tokens=tokens
        )
        self.add_event(event)

    def record_error(self, error: str, agent_id: Optional[str] = None, metadata: dict[str, Any] = None) -> None:
        """Record an error."""
        event = TimelineEvent(
            event_type=EventType.ERROR,
            agent_id=agent_id,
            content=error,
            metadata=metadata or {}
        )
        self.add_event(event)

    def record_milestone(self, milestone: str, metadata: dict[str, Any] = None) -> None:
        """Record a significant milestone."""
        event = TimelineEvent(
            event_type=EventType.MILESTONE,
            content=milestone,
            metadata=metadata or {}
        )
        self.add_event(event)

    async def _detect_patterns_async(self, event: TimelineEvent) -> None:
        """Detect patterns from the event stream."""
        # Simple pattern detection - can be enhanced
        if len(self.events) < 3:
            return

        # Check for repeated sequences
        recent_events = self.events[-10:]
        event_sequence = [e.event_type.value for e in recent_events]

        # Look for debate patterns
        if event_sequence.count(EventType.DEBATE_TURN.value) >= 3:
            pattern = ExecutionPattern(
                name="Debate Pattern",
                description="Multiple debate turns detected",
                pattern_type="debate",
                steps=event_sequence,
                usage_count=1,
                last_used=datetime.now()
            )
            self.record_pattern(pattern)

        # Look for gate patterns
        gate_events = [e for e in recent_events if e.event_type == EventType.GATE_RESULT]
        if len(gate_events) >= 2:
            passed_count = sum(1 for e in gate_events if e.metadata.get("passed"))
            success_rate = passed_count / len(gate_events)

            pattern = ExecutionPattern(
                name="Quality Gate Pattern",
                description=f"Gates with {success_rate:.0%} success rate",
                pattern_type="quality_gates",
                success_rate=success_rate,
                usage_count=len(gate_events),
                last_used=datetime.now()
            )
            self.record_pattern(pattern)

    def on_event(self, callback: callable) -> None:
        """Register a callback for events."""
        self._event_callbacks.append(callback)

    def on_pattern(self, callback: callable) -> None:
        """Register a callback for patterns."""
        self._pattern_callbacks.append(callback)

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the execution."""
        duration_ms = None
        if self.start_time:
            end = self.end_time or datetime.now()
            duration_ms = (end - self.start_time).total_seconds() * 1000

        agent_stats = {}
        for event in self.events:
            if event.agent_id and event.agent_role:
                if event.agent_id not in agent_stats:
                    agent_stats[event.agent_id] = {
                        "role": event.agent_role,
                        "messages": 0,
                        "cost": 0,
                        "tokens": 0
                    }
                agent_stats[event.agent_id]["messages"] += 1
                if event.cost:
                    agent_stats[event.agent_id]["cost"] += event.cost
                if event.tokens:
                    agent_stats[event.agent_id]["tokens"] += event.tokens

        return {
            "session_id": self.session_id,
            "total_events": len(self.events),
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "duration_ms": duration_ms,
            "agent_stats": agent_stats,
            "patterns_detected": len(self.patterns),
            "active_agents": list(self.active_agents),
            "error_count": sum(1 for e in self.events if e.event_type == EventType.ERROR)
        }

    def export_timeline(self) -> dict[str, Any]:
        """Export the full timeline for persistence or analysis."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "events": [e.to_dict() for e in self.events],
            "patterns": {k: v.to_dict() for k, v in self.patterns.items()},
            "summary": self.get_summary()
        }

    def import_timeline(self, data: dict[str, Any]) -> None:
        """Import a timeline from exported data."""
        self.session_id = data.get("session_id", self.session_id)
        self.start_time = datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None
        self.end_time = datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None

        # Import events
        self.events = []
        for event_data in data.get("events", []):
            event = TimelineEvent(
                id=event_data["id"],
                timestamp=datetime.fromisoformat(event_data["timestamp"]),
                event_type=EventType(event_data["event_type"]),
                agent_id=event_data.get("agent_id"),
                agent_role=event_data.get("agent_role"),
                model=event_data.get("model"),
                content=event_data.get("content"),
                metadata=event_data.get("metadata", {}),
                cost=event_data.get("cost"),
                tokens=event_data.get("tokens"),
                duration_ms=event_data.get("duration_ms"),
                parent_id=event_data.get("parent_id")
            )
            self.events.append(event)

        # Import patterns
        self.patterns = {}
        for pattern_id, pattern_data in data.get("patterns", {}).items():
            pattern = ExecutionPattern(
                id=pattern_data["id"],
                name=pattern_data["name"],
                description=pattern_data["description"],
                pattern_type=pattern_data["pattern_type"],
                steps=pattern_data["steps"],
                success_rate=pattern_data["success_rate"],
                avg_duration_ms=pattern_data["avg_duration_ms"],
                avg_cost=pattern_data["avg_cost"],
                usage_count=pattern_data["usage_count"],
                last_used=datetime.fromisoformat(pattern_data["last_used"]) if pattern_data.get("last_used") else None,
                metadata=pattern_data.get("metadata", {})
            )
            self.patterns[pattern_id] = pattern
