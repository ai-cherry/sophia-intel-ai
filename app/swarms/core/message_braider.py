"""
Message Braiding System for Micro-Swarms
Advanced inter-agent communication with context threading, semantic linking, and collaborative reasoning
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from app.memory.unified_memory_router import get_memory_router
from app.swarms.core.micro_swarm_base import AgentRole, MessageType, SwarmMessage

logger = logging.getLogger(__name__)


class BraidType(Enum):
    """Types of message braiding patterns"""

    SEQUENTIAL = "sequential"  # Linear conversation flow
    PARALLEL = "parallel"  # Concurrent message streams
    DEBATE = "debate"  # Back-and-forth argumentation
    CONSENSUS = "consensus"  # Convergence seeking
    HIERARCHICAL = "hierarchical"  # Parent-child relationships
    SEMANTIC = "semantic"  # Content-based linking
    TEMPORAL = "temporal"  # Time-based sequencing


class BraidStrength(Enum):
    """Strength of braiding connections"""

    WEAK = 0.3  # Loose association
    MEDIUM = 0.6  # Moderate connection
    STRONG = 0.8  # Strong relationship
    CRITICAL = 0.95  # Essential dependency


@dataclass
class BraidConnection:
    """Connection between messages in a braid"""

    source_message_id: str
    target_message_id: str
    connection_type: BraidType
    strength: float
    semantic_similarity: float
    temporal_proximity: float
    logical_dependency: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class BraidThread:
    """A thread of connected messages"""

    thread_id: str
    thread_type: BraidType
    messages: List[SwarmMessage] = field(default_factory=list)
    connections: List[BraidConnection] = field(default_factory=list)
    participants: Set[AgentRole] = field(default_factory=set)
    topic_embedding: Optional[List[float]] = None
    coherence_score: float = 0.0
    completion_status: str = "active"  # active, completed, abandoned
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class BraidingContext:
    """Context for message braiding decisions"""

    swarm_id: str
    current_coordination_pattern: str
    active_threads: List[BraidThread]
    message_history: List[SwarmMessage]
    semantic_coherence_threshold: float = 0.7
    temporal_window_ms: int = 30000  # 30 seconds
    max_thread_length: int = 20
    enable_semantic_linking: bool = True
    enable_debate_detection: bool = True


@dataclass
class BraidingResult:
    """Result of braiding analysis"""

    message_id: str
    assigned_threads: List[str]
    new_connections: List[BraidConnection]
    thread_updates: List[BraidThread]
    braiding_confidence: float
    reasoning: str
    suggested_responses: List[Dict[str, Any]] = field(default_factory=list)


class MessageBraider:
    """
    Advanced message braiding system for micro-swarms
    Manages sophisticated inter-agent communication patterns
    """

    def __init__(self, context: BraidingContext):
        self.context = context
        self.memory = get_memory_router()

        # Active braids
        self.active_threads: Dict[str, BraidThread] = {}
        self.message_index: Dict[str, SwarmMessage] = {}
        self.connection_graph: Dict[str, List[BraidConnection]] = defaultdict(list)

        # Semantic analysis
        self.topic_embeddings: Dict[str, List[float]] = {}
        self.semantic_cache: Dict[Tuple[str, str], float] = {}

        # Pattern detection
        self.debate_patterns: List[Dict[str, Any]] = []
        self.consensus_indicators: List[Dict[str, Any]] = []

        logger.info(f"Message braider initialized for swarm {context.swarm_id}")

    async def process_message(self, message: SwarmMessage) -> BraidingResult:
        """
        Process incoming message and determine braiding

        Args:
            message: Message to process and braid

        Returns:
            Braiding result with thread assignments and connections
        """
        start_time = datetime.now()

        # Index the message
        self.message_index[message.id] = message

        try:
            # Analyze message content and context
            message_analysis = await self._analyze_message(message)

            # Find relevant threads
            relevant_threads = await self._find_relevant_threads(message, message_analysis)

            # Determine braiding pattern
            braiding_pattern = await self._determine_braiding_pattern(message, relevant_threads)

            # Create connections
            new_connections = await self._create_connections(
                message, relevant_threads, braiding_pattern
            )

            # Update or create threads
            thread_updates = await self._update_threads(message, relevant_threads, new_connections)

            # Calculate braiding confidence
            confidence = self._calculate_braiding_confidence(
                message, new_connections, thread_updates
            )

            # Generate suggested responses
            suggested_responses = await self._generate_response_suggestions(message, thread_updates)

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            result = BraidingResult(
                message_id=message.id,
                assigned_threads=[thread.thread_id for thread in thread_updates],
                new_connections=new_connections,
                thread_updates=thread_updates,
                braiding_confidence=confidence,
                reasoning=f"Processed message in {processing_time:.2f}ms, found {len(relevant_threads)} relevant threads, created {len(new_connections)} connections",
                suggested_responses=suggested_responses,
            )

            # Update active threads
            for thread in thread_updates:
                self.active_threads[thread.thread_id] = thread

            return result

        except Exception as e:
            logger.error(f"Message braiding failed: {e}")
            return BraidingResult(
                message_id=message.id,
                assigned_threads=[],
                new_connections=[],
                thread_updates=[],
                braiding_confidence=0.0,
                reasoning=f"Braiding failed: {str(e)}",
            )

    async def _analyze_message(self, message: SwarmMessage) -> Dict[str, Any]:
        """Analyze message content and context"""

        analysis = {
            "content_length": len(message.content),
            "message_type": message.message_type,
            "sender_role": message.sender_role,
            "recipient_role": message.recipient_role,
            "confidence": message.confidence,
            "timestamp": message.timestamp,
            "reasoning_present": bool(message.reasoning),
            "citations_present": len(message.citations) > 0,
        }

        # Content analysis
        content_lower = message.content.lower()
        analysis.update(
            {
                "is_question": "?" in message.content,
                "is_challenge": any(
                    word in content_lower
                    for word in ["however", "but", "disagree", "wrong", "incorrect"]
                ),
                "is_agreement": any(
                    word in content_lower
                    for word in ["agree", "correct", "exactly", "yes", "indeed"]
                ),
                "is_synthesis": any(
                    word in content_lower
                    for word in ["combining", "together", "overall", "in summary"]
                ),
                "is_conclusion": any(
                    word in content_lower for word in ["therefore", "conclude", "final", "decision"]
                ),
                "has_data": any(
                    word in content_lower for word in ["data", "metrics", "statistics", "numbers"]
                ),
                "has_recommendations": any(
                    word in content_lower for word in ["recommend", "suggest", "propose", "should"]
                ),
            }
        )

        # Semantic embedding (simplified - in production would use actual embedding model)
        if self.context.enable_semantic_linking:
            analysis["content_embedding"] = await self._get_content_embedding(message.content)

        return analysis

    async def _find_relevant_threads(
        self, message: SwarmMessage, analysis: Dict[str, Any]
    ) -> List[BraidThread]:
        """Find threads relevant to the current message"""

        relevant_threads = []

        for thread_id, thread in self.active_threads.items():
            relevance_score = await self._calculate_thread_relevance(message, thread, analysis)

            if relevance_score > 0.3:  # Minimum relevance threshold
                relevant_threads.append((thread, relevance_score))

        # Sort by relevance score (descending)
        relevant_threads.sort(key=lambda x: x[1], reverse=True)

        # Return top relevant threads
        return [thread for thread, score in relevant_threads[:5]]

    async def _calculate_thread_relevance(
        self, message: SwarmMessage, thread: BraidThread, analysis: Dict[str, Any]
    ) -> float:
        """Calculate relevance between message and thread"""

        relevance_factors = []

        # Participant relevance
        if (
            message.sender_role in thread.participants
            or message.recipient_role in thread.participants
        ):
            relevance_factors.append(0.4)

        # Temporal relevance
        time_since_last_update = (message.timestamp - thread.updated_at).total_seconds()
        if time_since_last_update < self.context.temporal_window_ms / 1000:
            temporal_relevance = 1.0 - (
                time_since_last_update / (self.context.temporal_window_ms / 1000)
            )
            relevance_factors.append(0.3 * temporal_relevance)

        # Semantic relevance
        if (
            self.context.enable_semantic_linking
            and thread.topic_embedding
            and analysis.get("content_embedding")
        ):
            semantic_similarity = await self._calculate_semantic_similarity(
                analysis["content_embedding"], thread.topic_embedding
            )
            if semantic_similarity > self.context.semantic_coherence_threshold:
                relevance_factors.append(0.4 * semantic_similarity)

        # Message type relevance
        if thread.messages:
            last_message = thread.messages[-1]
            if self._message_types_related(message.message_type, last_message.message_type):
                relevance_factors.append(0.2)

        # Thread ID matching
        if message.thread_id and message.thread_id == thread.thread_id:
            relevance_factors.append(0.8)  # Strong indicator

        return sum(relevance_factors)

    async def _determine_braiding_pattern(
        self, message: SwarmMessage, relevant_threads: List[BraidThread]
    ) -> BraidType:
        """Determine the braiding pattern for this message"""

        # Pattern indicators
        is_response = message.message_type in [
            MessageType.CHALLENGE,
            MessageType.VALIDATION,
            MessageType.SYNTHESIS,
        ]
        is_new_topic = len(relevant_threads) == 0
        is_debate_message = message.message_type == MessageType.CHALLENGE
        is_consensus_seeking = (
            "consensus" in message.content.lower() or "agree" in message.content.lower()
        )

        # Determine pattern
        if is_new_topic:
            return BraidType.SEQUENTIAL
        elif is_debate_message:
            return BraidType.DEBATE
        elif is_consensus_seeking:
            return BraidType.CONSENSUS
        elif message.recipient_role and len(relevant_threads) == 1:
            return BraidType.SEQUENTIAL
        elif len(relevant_threads) > 1:
            return BraidType.SEMANTIC
        else:
            return BraidType.SEQUENTIAL

    async def _create_connections(
        self, message: SwarmMessage, relevant_threads: List[BraidThread], pattern: BraidType
    ) -> List[BraidConnection]:
        """Create connections between messages based on braiding pattern"""

        connections = []

        for thread in relevant_threads:
            if not thread.messages:
                continue

            # Connect to most recent relevant message in thread
            target_message = thread.messages[-1]

            # Calculate connection strength
            strength = await self._calculate_connection_strength(message, target_message, pattern)

            if strength > 0.2:  # Minimum strength threshold
                connection = BraidConnection(
                    source_message_id=target_message.id,
                    target_message_id=message.id,
                    connection_type=pattern,
                    strength=strength,
                    semantic_similarity=await self._get_semantic_similarity(
                        message, target_message
                    ),
                    temporal_proximity=self._calculate_temporal_proximity(message, target_message),
                    logical_dependency=self._calculate_logical_dependency(message, target_message),
                    metadata={
                        "thread_id": thread.thread_id,
                        "pattern": pattern.value,
                        "auto_generated": True,
                    },
                )

                connections.append(connection)

                # Add to connection graph
                self.connection_graph[target_message.id].append(connection)

        return connections

    async def _update_threads(
        self,
        message: SwarmMessage,
        relevant_threads: List[BraidThread],
        connections: List[BraidConnection],
    ) -> List[BraidThread]:
        """Update threads with new message and connections"""

        updated_threads = []

        if not relevant_threads:
            # Create new thread
            new_thread = BraidThread(
                thread_id=message.thread_id or str(uuid.uuid4()),
                thread_type=BraidType.SEQUENTIAL,
                messages=[message],
                connections=[],
                participants={message.sender_role} if message.sender_role else set(),
                created_at=message.timestamp,
                updated_at=message.timestamp,
            )

            if self.context.enable_semantic_linking:
                new_thread.topic_embedding = await self._get_content_embedding(message.content)

            updated_threads.append(new_thread)
        else:
            # Update existing threads
            for thread in relevant_threads:
                # Add message to thread
                thread.messages.append(message)
                thread.connections.extend(
                    [
                        conn
                        for conn in connections
                        if conn.metadata.get("thread_id") == thread.thread_id
                    ]
                )

                # Update participants
                if message.sender_role:
                    thread.participants.add(message.sender_role)
                if message.recipient_role:
                    thread.participants.add(message.recipient_role)

                # Update timestamp
                thread.updated_at = message.timestamp

                # Update topic embedding (weighted average)
                if self.context.enable_semantic_linking and thread.topic_embedding:
                    message_embedding = await self._get_content_embedding(message.content)
                    thread.topic_embedding = self._blend_embeddings(
                        thread.topic_embedding, message_embedding, 0.3
                    )

                # Update coherence score
                thread.coherence_score = await self._calculate_thread_coherence(thread)

                # Check if thread should be completed
                if len(thread.messages) >= self.context.max_thread_length:
                    thread.completion_status = "completed"

                updated_threads.append(thread)

        return updated_threads

    async def _calculate_connection_strength(
        self, message1: SwarmMessage, message2: SwarmMessage, pattern: BraidType
    ) -> float:
        """Calculate strength of connection between two messages"""

        factors = []

        # Temporal proximity
        time_diff = abs((message1.timestamp - message2.timestamp).total_seconds())
        temporal_strength = max(0, 1.0 - (time_diff / 3600))  # Decay over 1 hour
        factors.append(0.3 * temporal_strength)

        # Semantic similarity
        if self.context.enable_semantic_linking:
            semantic_sim = await self._get_semantic_similarity(message1, message2)
            factors.append(0.4 * semantic_sim)

        # Role relationship
        if message1.sender_role and message2.sender_role:
            if (
                message1.sender_role == message2.recipient_role
                or message2.sender_role == message1.recipient_role
            ):
                factors.append(0.3)  # Direct response relationship

        # Pattern-specific bonuses
        if pattern == BraidType.DEBATE:
            if (
                message1.message_type == MessageType.CHALLENGE
                or message2.message_type == MessageType.CHALLENGE
            ):
                factors.append(0.2)
        elif pattern == BraidType.CONSENSUS:
            if "agree" in message1.content.lower() or "agree" in message2.content.lower():
                factors.append(0.2)

        return min(1.0, sum(factors))

    def _calculate_braiding_confidence(
        self, message: SwarmMessage, connections: List[BraidConnection], threads: List[BraidThread]
    ) -> float:
        """Calculate confidence in the braiding decisions"""

        confidence_factors = []

        # Connection quality
        if connections:
            avg_connection_strength = sum(conn.strength for conn in connections) / len(connections)
            confidence_factors.append(0.4 * avg_connection_strength)
        else:
            confidence_factors.append(0.2)  # Lower confidence for isolated messages

        # Thread coherence
        if threads:
            avg_coherence = sum(thread.coherence_score for thread in threads) / len(threads)
            confidence_factors.append(0.3 * avg_coherence)

        # Message quality indicators
        if message.confidence > 0.8:
            confidence_factors.append(0.2)
        if message.reasoning:
            confidence_factors.append(0.1)

        return min(1.0, sum(confidence_factors))

    async def _generate_response_suggestions(
        self, message: SwarmMessage, threads: List[BraidThread]
    ) -> List[Dict[str, Any]]:
        """Generate suggested responses based on braiding context"""

        suggestions = []

        for thread in threads:
            if thread.thread_type == BraidType.DEBATE:
                suggestions.append(
                    {
                        "type": "challenge_response",
                        "description": "Respond to the debate with supporting evidence or counter-arguments",
                        "priority": 0.8,
                        "suggested_agents": [
                            role for role in AgentRole if role != message.sender_role
                        ],
                    }
                )

            elif thread.thread_type == BraidType.CONSENSUS:
                suggestions.append(
                    {
                        "type": "consensus_contribution",
                        "description": "Contribute to consensus building with agreements or refinements",
                        "priority": 0.7,
                        "suggested_agents": [AgentRole.VALIDATOR, AgentRole.STRATEGIST],
                    }
                )

            elif message.message_type == MessageType.ANALYSIS_RESULT:
                suggestions.append(
                    {
                        "type": "strategic_synthesis",
                        "description": "Synthesize analysis into strategic recommendations",
                        "priority": 0.9,
                        "suggested_agents": [AgentRole.STRATEGIST],
                    }
                )

        return suggestions

    async def _get_content_embedding(self, content: str) -> List[float]:
        """Get embedding for content (simplified implementation)"""
        # In production, this would use an actual embedding model
        # For now, return a simple hash-based embedding
        import hashlib

        content_hash = hashlib.md5(content.encode()).hexdigest()
        return [float(int(content_hash[i : i + 2], 16)) / 255.0 for i in range(0, 32, 2)]

    async def _calculate_semantic_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """Calculate semantic similarity between embeddings"""
        if len(embedding1) != len(embedding2):
            return 0.0

        # Simple cosine similarity
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def _get_semantic_similarity(
        self, message1: SwarmMessage, message2: SwarmMessage
    ) -> float:
        """Get cached or calculate semantic similarity between messages"""
        cache_key = (message1.id, message2.id)
        if cache_key in self.semantic_cache:
            return self.semantic_cache[cache_key]

        # Calculate similarity
        emb1 = await self._get_content_embedding(message1.content)
        emb2 = await self._get_content_embedding(message2.content)
        similarity = await self._calculate_semantic_similarity(emb1, emb2)

        # Cache result
        self.semantic_cache[cache_key] = similarity
        return similarity

    def _calculate_temporal_proximity(
        self, message1: SwarmMessage, message2: SwarmMessage
    ) -> float:
        """Calculate temporal proximity between messages (0-1, higher is closer)"""
        time_diff = abs((message1.timestamp - message2.timestamp).total_seconds())
        max_time = 3600  # 1 hour maximum
        return max(0, 1.0 - (time_diff / max_time))

    def _calculate_logical_dependency(
        self, message1: SwarmMessage, message2: SwarmMessage
    ) -> float:
        """Calculate logical dependency between messages"""
        # Simple heuristics for logical dependency
        dependency = 0.0

        # Response patterns
        if (
            message1.message_type == MessageType.CHALLENGE
            and message2.message_type == MessageType.VALIDATION
        ):
            dependency += 0.5
        elif (
            message1.message_type == MessageType.ANALYSIS_RESULT
            and message2.message_type == MessageType.SYNTHESIS
        ):
            dependency += 0.4

        # Content references
        if message1.id in message2.content or any(
            word in message2.content.lower() for word in ["previous", "above", "earlier"]
        ):
            dependency += 0.3

        return min(1.0, dependency)

    def _message_types_related(self, type1: MessageType, type2: MessageType) -> bool:
        """Check if two message types are related"""
        related_pairs = [
            (MessageType.TASK_ASSIGNMENT, MessageType.ANALYSIS_RESULT),
            (MessageType.ANALYSIS_RESULT, MessageType.CHALLENGE),
            (MessageType.CHALLENGE, MessageType.VALIDATION),
            (MessageType.VALIDATION, MessageType.SYNTHESIS),
            (MessageType.SYNTHESIS, MessageType.FINAL_OUTPUT),
        ]

        return (type1, type2) in related_pairs or (type2, type1) in related_pairs

    def _blend_embeddings(
        self, embedding1: List[float], embedding2: List[float], alpha: float
    ) -> List[float]:
        """Blend two embeddings with given weight"""
        return [alpha * e1 + (1 - alpha) * e2 for e1, e2 in zip(embedding1, embedding2)]

    async def _calculate_thread_coherence(self, thread: BraidThread) -> float:
        """Calculate coherence score for a thread"""
        if len(thread.messages) < 2:
            return 1.0

        coherence_factors = []

        # Semantic coherence
        if thread.messages and self.context.enable_semantic_linking:
            similarities = []
            for i in range(len(thread.messages) - 1):
                sim = await self._get_semantic_similarity(
                    thread.messages[i], thread.messages[i + 1]
                )
                similarities.append(sim)

            if similarities:
                coherence_factors.append(sum(similarities) / len(similarities))

        # Temporal coherence (messages should be reasonably spaced)
        if len(thread.messages) > 1:
            time_gaps = []
            for i in range(len(thread.messages) - 1):
                gap = (
                    thread.messages[i + 1].timestamp - thread.messages[i].timestamp
                ).total_seconds()
                time_gaps.append(min(1.0, 300 / max(gap, 1)))  # 5 minute ideal gap

            coherence_factors.append(sum(time_gaps) / len(time_gaps))

        # Logical flow coherence
        logical_flow = 0.0
        for i in range(len(thread.messages) - 1):
            if self._message_types_related(
                thread.messages[i].message_type, thread.messages[i + 1].message_type
            ):
                logical_flow += 1.0

        if len(thread.messages) > 1:
            coherence_factors.append(logical_flow / (len(thread.messages) - 1))

        return sum(coherence_factors) / len(coherence_factors) if coherence_factors else 0.5

    def get_thread_summary(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of a specific thread"""
        if thread_id not in self.active_threads:
            return None

        thread = self.active_threads[thread_id]

        return {
            "thread_id": thread.thread_id,
            "thread_type": thread.thread_type.value,
            "message_count": len(thread.messages),
            "participants": [role.value for role in thread.participants],
            "coherence_score": thread.coherence_score,
            "completion_status": thread.completion_status,
            "duration_minutes": (thread.updated_at - thread.created_at).total_seconds() / 60,
            "connections_count": len(thread.connections),
            "created_at": thread.created_at.isoformat(),
            "updated_at": thread.updated_at.isoformat(),
        }

    def get_braiding_statistics(self) -> Dict[str, Any]:
        """Get comprehensive braiding statistics"""

        stats = {
            "active_threads": len(self.active_threads),
            "total_messages": len(self.message_index),
            "total_connections": sum(
                len(connections) for connections in self.connection_graph.values()
            ),
            "thread_types": defaultdict(int),
            "message_types": defaultdict(int),
            "agent_participation": defaultdict(int),
            "average_thread_coherence": 0.0,
            "connection_strength_distribution": {
                "weak": 0,
                "medium": 0,
                "strong": 0,
                "critical": 0,
            },
        }

        # Thread type distribution
        for thread in self.active_threads.values():
            stats["thread_types"][thread.thread_type.value] += 1

        # Message type distribution
        for message in self.message_index.values():
            if message.message_type:
                stats["message_types"][message.message_type.value] += 1
            if message.sender_role:
                stats["agent_participation"][message.sender_role.value] += 1

        # Average coherence
        if self.active_threads:
            total_coherence = sum(thread.coherence_score for thread in self.active_threads.values())
            stats["average_thread_coherence"] = total_coherence / len(self.active_threads)

        # Connection strength distribution
        for connections in self.connection_graph.values():
            for conn in connections:
                if conn.strength < 0.4:
                    stats["connection_strength_distribution"]["weak"] += 1
                elif conn.strength < 0.7:
                    stats["connection_strength_distribution"]["medium"] += 1
                elif conn.strength < 0.9:
                    stats["connection_strength_distribution"]["strong"] += 1
                else:
                    stats["connection_strength_distribution"]["critical"] += 1

        return dict(stats)


# Factory function for creating message braider
def create_message_braider(swarm_id: str, coordination_pattern: str) -> MessageBraider:
    """Create message braider with appropriate configuration"""

    context = BraidingContext(
        swarm_id=swarm_id,
        current_coordination_pattern=coordination_pattern,
        active_threads=[],
        message_history=[],
        semantic_coherence_threshold=0.7,
        temporal_window_ms=30000,
        max_thread_length=20,
        enable_semantic_linking=True,
        enable_debate_detection=True,
    )

    return MessageBraider(context)
