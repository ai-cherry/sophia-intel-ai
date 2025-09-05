"""
Enhanced Memory System with Pattern Storage
Stores and retrieves execution patterns, shared context, and swarm knowledge.
"""

import hashlib
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class SharedContext:
    """Shared context across swarm agents."""

    session_id: str
    task: str
    objective: str
    constraints: list[str] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
    memory_refs: list[str] = field(default_factory=list)
    discovered_facts: dict[str, Any] = field(default_factory=dict)
    cost_budget: float = 100.0
    cost_spent: float = 0.0
    token_budget: int = 100000
    tokens_used: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_fact(self, key: str, value: Any) -> None:
        """Add a discovered fact to shared context."""
        self.discovered_facts[key] = value
        self.updated_at = datetime.now()

    def update_cost(self, cost: float, tokens: int) -> bool:
        """Update cost and check budget."""
        self.cost_spent += cost
        self.tokens_used += tokens
        self.updated_at = datetime.now()

        # Check if within budget
        return self.cost_spent <= self.cost_budget and self.tokens_used <= self.token_budget

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "session_id": self.session_id,
            "task": self.task,
            "objective": self.objective,
            "constraints": self.constraints,
            "preferences": self.preferences,
            "memory_refs": self.memory_refs,
            "discovered_facts": self.discovered_facts,
            "cost_budget": self.cost_budget,
            "cost_spent": self.cost_spent,
            "token_budget": self.token_budget,
            "tokens_used": self.tokens_used,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class PatternInstance:
    """An instance of a pattern execution."""

    pattern_id: str
    session_id: str
    success: bool
    duration_ms: float
    cost: float
    tokens: int
    input_hash: str
    output_summary: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class EnhancedMemorySystem:
    """
    Enhanced memory system for swarm orchestration.
    Manages patterns, shared context, and persistent knowledge.
    """

    def __init__(self, cache_ttl: int = 3600):
        """Initialize enhanced memory system."""
        # Pattern storage
        self.patterns: dict[str, dict[str, Any]] = {}
        self.pattern_instances: list[PatternInstance] = []
        self.pattern_index: dict[str, list[str]] = defaultdict(list)  # task_type -> pattern_ids

        # Shared context storage
        self.active_contexts: dict[str, SharedContext] = {}
        self.context_history: list[SharedContext] = []

        # Knowledge base
        self.knowledge_base: dict[str, Any] = {}
        self.fact_cache: dict[str, tuple[Any, datetime]] = {}
        self.cache_ttl = cache_ttl

        # Metrics
        self.access_count: dict[str, int] = defaultdict(int)
        self.success_rates: dict[str, float] = defaultdict(float)

    async def store_pattern(
        self,
        pattern_id: str,
        name: str,
        pattern_type: str,
        steps: list[dict[str, Any]],
        metadata: dict[str, Any] = None,
    ) -> None:
        """Store a reusable execution pattern."""
        pattern = {
            "id": pattern_id,
            "name": name,
            "type": pattern_type,
            "steps": steps,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "usage_count": 0,
            "success_count": 0,
            "total_cost": 0.0,
            "avg_duration_ms": 0.0,
        }

        self.patterns[pattern_id] = pattern

        # Index by type
        if pattern_type:
            self.pattern_index[pattern_type].append(pattern_id)

        logger.info(f"Stored pattern: {name} ({pattern_type})")

    async def record_pattern_usage(
        self,
        pattern_id: str,
        session_id: str,
        success: bool,
        duration_ms: float,
        cost: float,
        tokens: int,
        input_data: Any,
        output_data: Any,
    ) -> None:
        """Record usage of a pattern."""
        if pattern_id not in self.patterns:
            logger.warning(f"Pattern {pattern_id} not found")
            return

        # Create instance record
        instance = PatternInstance(
            pattern_id=pattern_id,
            session_id=session_id,
            success=success,
            duration_ms=duration_ms,
            cost=cost,
            tokens=tokens,
            input_hash=self._hash_data(input_data),
            output_summary=str(output_data)[:200],
        )
        self.pattern_instances.append(instance)

        # Update pattern metrics
        pattern = self.patterns[pattern_id]
        pattern["usage_count"] += 1
        if success:
            pattern["success_count"] += 1
        pattern["total_cost"] += cost

        # Update average duration
        prev_avg = pattern["avg_duration_ms"]
        pattern["avg_duration_ms"] = (
            prev_avg * (pattern["usage_count"] - 1) + duration_ms
        ) / pattern["usage_count"]

        # Update success rate
        self.success_rates[pattern_id] = pattern["success_count"] / pattern["usage_count"]

        logger.info(f"Recorded pattern usage: {pattern_id} (success={success})")

    async def get_best_pattern(
        self, task_type: str, constraints: dict[str, Any] = None
    ) -> Optional[dict[str, Any]]:
        """Get the best pattern for a task type."""
        pattern_ids = self.pattern_index.get(task_type, [])
        if not pattern_ids:
            return None

        # Score patterns based on success rate and usage
        best_pattern = None
        best_score = -1

        for pattern_id in pattern_ids:
            pattern = self.patterns.get(pattern_id)
            if not pattern:
                continue

            # Check constraints
            if constraints:
                if (
                    constraints.get("max_cost")
                    and pattern["avg_duration_ms"] > constraints["max_cost"]
                ):
                    continue
                if (
                    constraints.get("min_success_rate")
                    and self.success_rates[pattern_id] < constraints["min_success_rate"]
                ):
                    continue

            # Calculate score (weighted by success rate and usage)
            success_rate = self.success_rates.get(pattern_id, 0)
            usage_normalized = min(pattern["usage_count"] / 100, 1.0)  # Normalize to 0-1
            score = (success_rate * 0.7) + (usage_normalized * 0.3)

            if score > best_score:
                best_score = score
                best_pattern = pattern

        return best_pattern

    async def create_shared_context(
        self,
        session_id: str,
        task: str,
        objective: str,
        constraints: list[str] = None,
        preferences: dict[str, Any] = None,
        cost_budget: float = 100.0,
        token_budget: int = 100000,
    ) -> SharedContext:
        """Create a new shared context for a swarm session."""
        context = SharedContext(
            session_id=session_id,
            task=task,
            objective=objective,
            constraints=constraints or [],
            preferences=preferences or {},
            cost_budget=cost_budget,
            token_budget=token_budget,
        )

        self.active_contexts[session_id] = context
        logger.info(f"Created shared context for session: {session_id}")

        return context

    async def get_shared_context(self, session_id: str) -> Optional[SharedContext]:
        """Get shared context for a session."""
        return self.active_contexts.get(session_id)

    async def update_shared_context(self, session_id: str, updates: dict[str, Any]) -> bool:
        """Update shared context with new information."""
        context = self.active_contexts.get(session_id)
        if not context:
            logger.warning(f"Context not found for session: {session_id}")
            return False

        # Update fields
        for key, value in updates.items():
            if key == "discovered_facts":
                context.discovered_facts.update(value)
            elif key == "memory_refs":
                context.memory_refs.extend(value)
            elif key == "cost":
                context.cost_spent += value.get("amount", 0)
                context.tokens_used += value.get("tokens", 0)
            elif hasattr(context, key):
                setattr(context, key, value)

        context.updated_at = datetime.now()
        return True

    async def finalize_context(self, session_id: str) -> None:
        """Move context from active to history."""
        context = self.active_contexts.pop(session_id, None)
        if context:
            self.context_history.append(context)
            logger.info(f"Finalized context for session: {session_id}")

    async def store_knowledge(
        self, key: str, value: Any, category: str = "general", tags: list[str] = None
    ) -> None:
        """Store knowledge in the persistent knowledge base."""
        knowledge_entry = {
            "value": value,
            "category": category,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "access_count": 0,
        }

        self.knowledge_base[key] = knowledge_entry

        # Update cache
        self.fact_cache[key] = (value, datetime.now())

        logger.info(f"Stored knowledge: {key} ({category})")

    async def get_knowledge(self, key: str, use_cache: bool = True) -> Optional[Any]:
        """Retrieve knowledge from the knowledge base."""
        # Check cache first
        if use_cache and key in self.fact_cache:
            value, timestamp = self.fact_cache[key]
            if (datetime.now() - timestamp).total_seconds() < self.cache_ttl:
                self.access_count[key] += 1
                return value

        # Get from knowledge base
        entry = self.knowledge_base.get(key)
        if entry:
            value = entry["value"]
            entry["access_count"] += 1
            self.access_count[key] += 1

            # Update cache
            self.fact_cache[key] = (value, datetime.now())

            return value

        return None

    async def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        limit: int = 10,
    ) -> list[tuple[str, Any]]:
        """Search the knowledge base."""
        results = []

        for key, entry in self.knowledge_base.items():
            # Filter by category
            if category and entry["category"] != category:
                continue

            # Filter by tags
            if tags and not any(tag in entry["tags"] for tag in tags):
                continue

            # Simple text matching
            if query.lower() in key.lower() or query.lower() in str(entry["value"]).lower():
                results.append((key, entry["value"]))

        # Sort by access count and limit
        results.sort(key=lambda x: self.access_count.get(x[0], 0), reverse=True)

        return results[:limit]

    async def get_related_patterns(self, pattern_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Get patterns related to a given pattern."""
        pattern = self.patterns.get(pattern_id)
        if not pattern:
            return []

        pattern_type = pattern.get("type")
        related = []

        # Find patterns of the same type
        for pid in self.pattern_index.get(pattern_type, []):
            if pid != pattern_id:
                related_pattern = self.patterns.get(pid)
                if related_pattern:
                    related.append(related_pattern)

        # Sort by success rate and limit
        related.sort(key=lambda p: self.success_rates.get(p["id"], 0), reverse=True)

        return related[:limit]

    def _hash_data(self, data: Any) -> str:
        """Create a hash of input data."""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(data_str.encode()).hexdigest()

    async def get_statistics(self) -> dict[str, Any]:
        """Get memory system statistics."""
        return {
            "patterns": {
                "total": len(self.patterns),
                "by_type": {ptype: len(pids) for ptype, pids in self.pattern_index.items()},
                "total_usage": sum(p["usage_count"] for p in self.patterns.values()),
                "avg_success_rate": sum(self.success_rates.values()) / len(self.success_rates)
                if self.success_rates
                else 0,
            },
            "contexts": {
                "active": len(self.active_contexts),
                "historical": len(self.context_history),
                "total_cost": sum(c.cost_spent for c in self.active_contexts.values()),
                "total_tokens": sum(c.tokens_used for c in self.active_contexts.values()),
            },
            "knowledge": {
                "entries": len(self.knowledge_base),
                "cached": len(self.fact_cache),
                "most_accessed": sorted(
                    self.access_count.items(), key=lambda x: x[1], reverse=True
                )[:5],
            },
        }

    async def export_memory(self) -> dict[str, Any]:
        """Export entire memory state for persistence."""
        return {
            "patterns": self.patterns,
            "pattern_instances": [
                {
                    "pattern_id": pi.pattern_id,
                    "session_id": pi.session_id,
                    "success": pi.success,
                    "duration_ms": pi.duration_ms,
                    "cost": pi.cost,
                    "tokens": pi.tokens,
                    "timestamp": pi.timestamp.isoformat(),
                }
                for pi in self.pattern_instances
            ],
            "pattern_index": dict(self.pattern_index),
            "contexts": {
                "active": {sid: ctx.to_dict() for sid, ctx in self.active_contexts.items()},
                "history": [ctx.to_dict() for ctx in self.context_history],
            },
            "knowledge_base": self.knowledge_base,
            "statistics": await self.get_statistics(),
        }

    async def import_memory(self, data: dict[str, Any]) -> None:
        """Import memory state from exported data."""
        # Import patterns
        self.patterns = data.get("patterns", {})
        self.pattern_index = defaultdict(list, data.get("pattern_index", {}))

        # Import pattern instances
        self.pattern_instances = []
        for pi_data in data.get("pattern_instances", []):
            instance = PatternInstance(
                pattern_id=pi_data["pattern_id"],
                session_id=pi_data["session_id"],
                success=pi_data["success"],
                duration_ms=pi_data["duration_ms"],
                cost=pi_data["cost"],
                tokens=pi_data["tokens"],
                input_hash="",
                output_summary="",
                timestamp=datetime.fromisoformat(pi_data["timestamp"]),
            )
            self.pattern_instances.append(instance)

        # Import knowledge base
        self.knowledge_base = data.get("knowledge_base", {})

        # Recalculate success rates
        for pattern_id, pattern in self.patterns.items():
            if pattern["usage_count"] > 0:
                self.success_rates[pattern_id] = pattern["success_count"] / pattern["usage_count"]

        logger.info(
            f"Imported memory with {len(self.patterns)} patterns and {len(self.knowledge_base)} knowledge entries"
        )
