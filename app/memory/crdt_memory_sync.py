"""
CRDT-Backed Distributed Memory Synchronization
Enables conflict-free memory synchronization across distributed swarm agents
Part of 2025 Memory Stack Modernization
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.core.ai_logger import logger

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """CRDT operation types"""
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    MERGE = "merge"


@dataclass
class VectorClock:
    """Vector clock for causality tracking"""
    clock: dict[str, int] = field(default_factory=dict)

    def increment(self, agent_id: str):
        """Increment clock for agent"""
        self.clock[agent_id] = self.clock.get(agent_id, 0) + 1

    def update(self, other_clock: dict[str, int]):
        """Update with another vector clock"""
        for agent_id, timestamp in other_clock.items():
            self.clock[agent_id] = max(
                self.clock.get(agent_id, 0),
                timestamp
            )

    def happens_before(self, other: 'VectorClock') -> bool:
        """Check if this clock happens before another"""
        for agent_id, timestamp in self.clock.items():
            if timestamp > other.clock.get(agent_id, 0):
                return False
        return any(
            timestamp < other.clock.get(agent_id, 0)
            for agent_id, timestamp in self.clock.items()
        )

    def concurrent_with(self, other: 'VectorClock') -> bool:
        """Check if clocks are concurrent"""
        return not self.happens_before(other) and not other.happens_before(self)

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary"""
        return self.clock.copy()


@dataclass
class MemoryOperation:
    """Represents a CRDT memory operation"""
    operation_id: str
    operation_type: OperationType
    memory_id: str
    content: dict[str, Any]
    agent_id: str
    timestamp: float
    vector_clock: dict[str, int]
    checksum: str | None = None

    def __post_init__(self):
        """Generate checksum if not provided"""
        if not self.checksum:
            self.checksum = self._generate_checksum()

    def _generate_checksum(self) -> str:
        """Generate operation checksum for integrity"""
        data = f"{self.operation_id}{self.operation_type.value}{self.memory_id}{json.dumps(self.content, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def verify_integrity(self) -> bool:
        """Verify operation integrity"""
        return self.checksum == self._generate_checksum()


@dataclass
class CRDTMemoryState:
    """State-based CRDT for memory"""
    memory_id: str
    content: dict[str, Any]
    vector_clock: VectorClock
    tombstone: bool = False  # For deletion tracking
    last_modified: float = field(default_factory=time.time)

    def merge(self, other: 'CRDTMemoryState') -> 'CRDTMemoryState':
        """Merge with another state using CRDT rules"""
        # If one is deleted (tombstone), deleted state wins
        if self.tombstone or other.tombstone:
            if self.vector_clock.happens_before(other.vector_clock):
                return other
            elif other.vector_clock.happens_before(self.vector_clock):
                return self
            else:
                # Concurrent deletes - tombstone wins
                return self if self.tombstone else other

        # Merge based on vector clocks
        if self.vector_clock.happens_before(other.vector_clock):
            return other
        elif other.vector_clock.happens_before(self.vector_clock):
            return self
        else:
            # Concurrent updates - merge content
            merged_content = self._merge_content(self.content, other.content)
            merged_clock = VectorClock()
            merged_clock.update(self.vector_clock.to_dict())
            merged_clock.update(other.vector_clock.to_dict())

            return CRDTMemoryState(
                memory_id=self.memory_id,
                content=merged_content,
                vector_clock=merged_clock,
                tombstone=False,
                last_modified=max(self.last_modified, other.last_modified)
            )

    def _merge_content(self, content1: dict, content2: dict) -> dict:
        """Merge concurrent content updates"""
        merged = {}
        all_keys = set(content1.keys()) | set(content2.keys())

        for key in all_keys:
            if key in content1 and key in content2:
                # Both have the key - use latest timestamp or merge
                if isinstance(content1[key], dict) and isinstance(content2[key], dict):
                    merged[key] = self._merge_content(content1[key], content2[key])
                elif isinstance(content1[key], list) and isinstance(content2[key], list):
                    # Union of lists for concurrent updates
                    merged[key] = list(set(content1[key] + content2[key]))
                else:
                    # Use value with higher timestamp
                    merged[key] = content1[key] if self.last_modified >= other.last_modified else content2[key]
            elif key in content1:
                merged[key] = content1[key]
            else:
                merged[key] = content2[key]

        return merged


class CRDTMemoryStore:
    """
    Distributed memory store with CRDT synchronization
    Features:
    - State-based CRDTs for memory snapshots
    - Operation-based CRDTs for real-time updates
    - Lamport timestamps for causality
    - Deterministic conflict resolution
    """

    def __init__(self, agent_id: str, sync_interval: float = 1.0):
        """
        Initialize CRDT memory store
        
        Args:
            agent_id: Unique agent identifier
            sync_interval: Synchronization interval in seconds
        """
        self.agent_id = agent_id
        self.sync_interval = sync_interval

        # Memory state
        self.memory_states: dict[str, CRDTMemoryState] = {}
        self.vector_clock = VectorClock()

        # Operation log for synchronization
        self.operation_log: list[MemoryOperation] = []
        self.pending_operations: set[str] = set()
        self.processed_operations: set[str] = set()

        # Peers for synchronization
        self.peers: dict[str, CRDTMemoryStore] = {}

        # Sync control
        self._sync_task: asyncio.Task | None = None
        self._running = False

        # Metrics
        self.metrics = {
            'operations_sent': 0,
            'operations_received': 0,
            'conflicts_resolved': 0,
            'sync_cycles': 0,
            'avg_sync_time_ms': 0.0
        }

    async def start(self):
        """Start synchronization loop"""
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        logger.info(f"Started CRDT memory store for agent {self.agent_id}")

    async def stop(self):
        """Stop synchronization loop"""
        self._running = False
        if self._sync_task:
            await self._sync_task
        logger.info(f"Stopped CRDT memory store for agent {self.agent_id}")

    async def add_memory(
        self,
        memory_id: str,
        content: dict[str, Any],
        broadcast: bool = True
    ) -> bool:
        """
        Add new memory with CRDT tracking
        
        Args:
            memory_id: Unique memory identifier
            content: Memory content
            broadcast: Whether to broadcast to peers
            
        Returns:
            Success status
        """
        # Increment vector clock
        self.vector_clock.increment(self.agent_id)

        # Create operation
        operation = MemoryOperation(
            operation_id=f"{self.agent_id}_{time.time_ns()}",
            operation_type=OperationType.ADD,
            memory_id=memory_id,
            content=content,
            agent_id=self.agent_id,
            timestamp=time.time(),
            vector_clock=self.vector_clock.to_dict()
        )

        # Apply locally
        await self._apply_operation(operation)

        # Add to log
        self.operation_log.append(operation)

        # Broadcast to peers
        if broadcast:
            await self._broadcast_operation(operation)

        return True

    async def update_memory(
        self,
        memory_id: str,
        updates: dict[str, Any],
        broadcast: bool = True
    ) -> bool:
        """
        Update existing memory
        
        Args:
            memory_id: Memory identifier
            updates: Updates to apply
            broadcast: Whether to broadcast to peers
            
        Returns:
            Success status
        """
        if memory_id not in self.memory_states:
            logger.warning(f"Memory {memory_id} not found")
            return False

        # Increment vector clock
        self.vector_clock.increment(self.agent_id)

        # Create operation
        operation = MemoryOperation(
            operation_id=f"{self.agent_id}_{time.time_ns()}",
            operation_type=OperationType.UPDATE,
            memory_id=memory_id,
            content=updates,
            agent_id=self.agent_id,
            timestamp=time.time(),
            vector_clock=self.vector_clock.to_dict()
        )

        # Apply locally
        await self._apply_operation(operation)

        # Add to log
        self.operation_log.append(operation)

        # Broadcast to peers
        if broadcast:
            await self._broadcast_operation(operation)

        return True

    async def delete_memory(
        self,
        memory_id: str,
        broadcast: bool = True
    ) -> bool:
        """
        Delete memory (mark as tombstone)
        
        Args:
            memory_id: Memory identifier
            broadcast: Whether to broadcast to peers
            
        Returns:
            Success status
        """
        if memory_id not in self.memory_states:
            return False

        # Increment vector clock
        self.vector_clock.increment(self.agent_id)

        # Create operation
        operation = MemoryOperation(
            operation_id=f"{self.agent_id}_{time.time_ns()}",
            operation_type=OperationType.DELETE,
            memory_id=memory_id,
            content={},
            agent_id=self.agent_id,
            timestamp=time.time(),
            vector_clock=self.vector_clock.to_dict()
        )

        # Apply locally
        await self._apply_operation(operation)

        # Add to log
        self.operation_log.append(operation)

        # Broadcast to peers
        if broadcast:
            await self._broadcast_operation(operation)

        return True

    async def get_memory(self, memory_id: str) -> dict[str, Any] | None:
        """
        Get memory content
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory content or None
        """
        state = self.memory_states.get(memory_id)
        if state and not state.tombstone:
            return state.content
        return None

    async def merge_remote_operations(
        self,
        operations: list[MemoryOperation]
    ) -> int:
        """
        Merge operations from remote agent
        
        Args:
            operations: List of remote operations
            
        Returns:
            Number of operations applied
        """
        applied = 0

        for op in operations:
            # Skip if already processed
            if op.operation_id in self.processed_operations:
                continue

            # Verify integrity
            if not op.verify_integrity():
                logger.warning(f"Operation {op.operation_id} failed integrity check")
                continue

            # Apply operation with conflict resolution
            if await self._apply_operation_with_conflict_resolution(op):
                applied += 1
                self.processed_operations.add(op.operation_id)

                # Update vector clock
                self.vector_clock.update(op.vector_clock)

        self.metrics['operations_received'] += len(operations)

        return applied

    async def _apply_operation(self, operation: MemoryOperation) -> bool:
        """Apply operation to local state"""
        memory_id = operation.memory_id

        if operation.operation_type == OperationType.ADD:
            # Create new memory state
            self.memory_states[memory_id] = CRDTMemoryState(
                memory_id=memory_id,
                content=operation.content,
                vector_clock=VectorClock(operation.vector_clock),
                tombstone=False
            )

        elif operation.operation_type == OperationType.UPDATE:
            if memory_id in self.memory_states:
                state = self.memory_states[memory_id]
                state.content.update(operation.content)
                state.vector_clock.update(operation.vector_clock)
                state.last_modified = operation.timestamp

        elif operation.operation_type == OperationType.DELETE:
            if memory_id in self.memory_states:
                self.memory_states[memory_id].tombstone = True
                self.memory_states[memory_id].vector_clock.update(operation.vector_clock)

        return True

    async def _apply_operation_with_conflict_resolution(
        self,
        operation: MemoryOperation
    ) -> bool:
        """Apply operation with CRDT conflict resolution"""
        memory_id = operation.memory_id

        # Create state from operation
        new_state = CRDTMemoryState(
            memory_id=memory_id,
            content=operation.content,
            vector_clock=VectorClock(operation.vector_clock),
            tombstone=(operation.operation_type == OperationType.DELETE)
        )

        if memory_id in self.memory_states:
            # Merge with existing state
            existing_state = self.memory_states[memory_id]
            merged_state = existing_state.merge(new_state)

            if merged_state != existing_state:
                self.memory_states[memory_id] = merged_state
                self.metrics['conflicts_resolved'] += 1
        else:
            # New memory
            self.memory_states[memory_id] = new_state

        return True

    async def _broadcast_operation(self, operation: MemoryOperation):
        """Broadcast operation to all peers"""
        if not self.peers:
            return

        tasks = []
        for peer_id, peer in self.peers.items():
            tasks.append(peer.merge_remote_operations([operation]))

        await asyncio.gather(*tasks, return_exceptions=True)
        self.metrics['operations_sent'] += len(self.peers)

    async def _sync_loop(self):
        """Periodic synchronization loop"""
        while self._running:
            try:
                await asyncio.sleep(self.sync_interval)
                await self._sync_with_peers()
            except Exception as e:
                logger.error(f"Sync loop error: {e}")

    async def _sync_with_peers(self):
        """Synchronize with all peers"""
        if not self.peers:
            return

        start_time = time.perf_counter()

        # Get operations to sync
        ops_to_sync = [
            op for op in self.operation_log
            if op.operation_id not in self.pending_operations
        ]

        # Send to all peers
        tasks = []
        for peer_id, peer in self.peers.items():
            tasks.append(peer.merge_remote_operations(ops_to_sync))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update metrics
        sync_time_ms = (time.perf_counter() - start_time) * 1000
        self.metrics['sync_cycles'] += 1
        n = self.metrics['sync_cycles']
        prev_avg = self.metrics['avg_sync_time_ms']
        self.metrics['avg_sync_time_ms'] = (prev_avg * (n - 1) + sync_time_ms) / n

        logger.debug(f"Synced with {len(self.peers)} peers in {sync_time_ms:.2f}ms")

    def add_peer(self, peer_id: str, peer: 'CRDTMemoryStore'):
        """Add peer for synchronization"""
        self.peers[peer_id] = peer
        logger.info(f"Added peer {peer_id} to agent {self.agent_id}")

    def remove_peer(self, peer_id: str):
        """Remove peer"""
        if peer_id in self.peers:
            del self.peers[peer_id]
            logger.info(f"Removed peer {peer_id} from agent {self.agent_id}")

    def get_state_snapshot(self) -> dict[str, Any]:
        """Get snapshot of current state"""
        return {
            'agent_id': self.agent_id,
            'vector_clock': self.vector_clock.to_dict(),
            'memory_count': len(self.memory_states),
            'active_memories': sum(1 for s in self.memory_states.values() if not s.tombstone),
            'tombstones': sum(1 for s in self.memory_states.values() if s.tombstone),
            'operation_log_size': len(self.operation_log),
            'metrics': self.metrics
        }


# Example usage
if __name__ == "__main__":
    async def test_crdt_sync():
        # Create two agents
        agent1 = CRDTMemoryStore("agent-1")
        agent2 = CRDTMemoryStore("agent-2")

        # Connect as peers
        agent1.add_peer("agent-2", agent2)
        agent2.add_peer("agent-1", agent1)

        # Start sync
        await agent1.start()
        await agent2.start()

        # Concurrent updates
        await agent1.add_memory("mem-1", {"content": "version 1", "author": "agent1"})
        await agent2.add_memory("mem-1", {"content": "version 2", "author": "agent2"})

        # Wait for sync
        await asyncio.sleep(2)

        # Check convergence
        mem1 = await agent1.get_memory("mem-1")
        mem2 = await agent2.get_memory("mem-1")

        logger.info(f"Agent 1 memory: {mem1}")
        logger.info(f"Agent 2 memory: {mem2}")
        logger.info(f"Converged: {mem1 == mem2}")

        # Show metrics
        logger.info(f"\nAgent 1 snapshot: {agent1.get_state_snapshot()}")
        logger.info(f"Agent 2 snapshot: {agent2.get_state_snapshot()}")

        # Cleanup
        await agent1.stop()
        await agent2.stop()

    asyncio.run(test_crdt_sync())
