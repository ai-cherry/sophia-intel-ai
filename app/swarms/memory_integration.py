"""
Swarm Memory Integration System
Implements ADR-005: Memory System Integration Architecture
Connects swarm orchestrators with Supermemory MCP and Weaviate systems.
"""

import json
import hashlib
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import aiohttp

from app.config.env_loader import get_env_config
from app.memory.supermemory_mcp import MemoryEntry, MemoryType
from app.core.circuit_breaker import with_circuit_breaker, get_llm_circuit_breaker, get_weaviate_circuit_breaker, get_redis_circuit_breaker, get_webhook_circuit_breaker

logger = logging.getLogger(__name__)


class SwarmMemoryEventType(Enum):
    """Types of swarm memory events."""
    SWARM_INITIALIZED = "swarm_initialized"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    PATTERN_EXECUTED = "pattern_executed"
    CONSENSUS_REACHED = "consensus_reached"
    QUALITY_GATE_FAILED = "quality_gate_failed"
    STRATEGY_ARCHIVED = "strategy_archived"
    KNOWLEDGE_TRANSFERRED = "knowledge_transferred"
    INTER_SWARM_COMMUNICATION = "inter_swarm_communication"
    EVOLUTION_EVENT = "evolution_event"
    CONSCIOUSNESS_MEASURED = "consciousness_measured"


@dataclass
class SwarmMemoryEvent:
    """Structured swarm memory event."""
    event_type: SwarmMemoryEventType
    swarm_type: str
    swarm_id: str
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_memory_entry(self) -> MemoryEntry:
        """Convert to memory entry for storage."""
        content = {
            "event_type": self.event_type.value,
            "swarm_type": self.swarm_type,
            "swarm_id": self.swarm_id,
            "data": self.data,
            "metadata": self.metadata
        }
        
        topic = f"SwarmEvent:{self.event_type.value}:{self.swarm_type}"
        
        return MemoryEntry(
            topic=topic,
            content=json.dumps(content, default=str),
            source=f"swarm_{self.swarm_type}",
            tags=["swarm_event", self.event_type.value, self.swarm_type],
            memory_type=MemoryType.EPISODIC,
            timestamp=self.timestamp
        )


class SwarmMemoryClient:
    """
    Memory client for swarm orchestrators following ADR-005.
    Provides unified interface to Supermemory MCP + Weaviate + Redis system.
    """
    
    def __init__(self, swarm_type: str, swarm_id: str):
        """
        Initialize swarm memory client.
        
        Args:
            swarm_type: Type of swarm (coding_team, coding_swarm, etc.)
            swarm_id: Unique identifier for this swarm instance
        """
        self.swarm_type = swarm_type
        self.swarm_id = swarm_id
        self.config = get_env_config()
        self.mcp_server_url = self.config.mcp_server_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.memory_cache = {}
        self.event_buffer = []
        
        logger.info(f"SwarmMemoryClient initialized for {swarm_type}:{swarm_id}")
    
    async def initialize(self):
        """Initialize memory client with connection to MCP server."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        
        # Test connection to MCP server
        try:
            await self._test_connection()
            logger.info(f"Memory client connected to MCP server: {self.mcp_server_url}")
        except Exception as e:
            logger.warning(f"MCP server connection failed, using local fallback: {e}")
        
        # Ensure this returns None explicitly for proper async/await behavior
        return None
    
    async def close(self):
        """Close memory client connections."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _test_connection(self):
        """Test connection to MCP server."""
        async with self.session.get(f"{self.mcp_server_url}/health") as response:
            if response.status != 200:
                raise Exception(f"MCP server unhealthy: {response.status}")
    
    # ============================================
    # Core Memory Operations
    # ============================================
    
    async def store_memory(
        self,
        topic: str,
        content: str,
        memory_type: MemoryType = MemoryType.SEMANTIC,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store memory entry in unified memory system.
        
        Args:
            topic: Memory topic/title
            content: Memory content
            memory_type: Type of memory (semantic, episodic, procedural)
            tags: Optional tags for categorization
            metadata: Optional metadata
            
        Returns:
            Storage result with hash_id and status
        """
        if not self.session:
            await self.initialize()
        
        # Prepare memory entry
        tags_list = (tags or []) + [self.swarm_type, "swarm_memory"]
        
        # Add metadata tags
        if metadata:
            for key in ['task_id', 'agent_role', 'repo_path', 'file_path']:
                if key in metadata:
                    tags_list.append(metadata[key])
        
        entry_data = {
            "topic": topic,
            "content": content,
            "source": f"swarm_{self.swarm_type}_{self.swarm_id}",
            "tags": tags_list,
            "memory_type": memory_type.value
        }
        
        # Add metadata
        if metadata:
            entry_data["metadata"] = metadata
        
        try:
            async with self.session.post(
                f"{self.mcp_server_url}/mcp/memory/add",
                json=entry_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.debug(f"Stored memory: {topic[:50]}... -> {result.get('id')}")
                    return result
                else:
                    error_text = await response.text()
                    raise Exception(f"Memory storage failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            # Cache for retry
            self._cache_for_retry("store", entry_data)
            raise
    
    @with_circuit_breaker("database")
    async def search_memory(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        include_other_swarms: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search memory with swarm-aware filtering.
        
        Args:
            query: Search query
            limit: Maximum results
            memory_type: Filter by memory type
            tags: Filter by tags
            include_other_swarms: Include memories from other swarms
            
        Returns:
            List of matching memory entries
        """
        if not self.session:
            await self.initialize()
        
        # Build search request
        search_data = {
            "query": query,
            "limit": limit
        }
        
        if memory_type:
            search_data["memory_type"] = memory_type.value
        
        # Add swarm filtering
        search_tags = tags or []
        if not include_other_swarms:
            search_tags.append(self.swarm_type)
        
        if search_tags:
            search_data["tags"] = search_tags
        
        try:
            async with self.session.post(
                f"{self.mcp_server_url}/mcp/memory/search",
                json=search_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    memories = result.get("results", [])
                    logger.debug(f"Memory search: '{query}' -> {len(memories)} results")
                    return memories
                else:
                    error_text = await response.text()
                    raise Exception(f"Memory search failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            return []
    
    # ============================================
    # Swarm Event Tracking
    # ============================================
    
    async def log_swarm_event(
        self,
        event_type: SwarmMemoryEventType,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log swarm event to memory system.
        
        Args:
            event_type: Type of swarm event
            data: Event data
            metadata: Optional metadata
        """
        event = SwarmMemoryEvent(
            event_type=event_type,
            swarm_type=self.swarm_type,
            swarm_id=self.swarm_id,
            timestamp=datetime.now(),
            data=data,
            metadata=metadata or {}
        )
        
        # Convert to memory entry and store
        memory_entry = event.to_memory_entry()
        
        try:
            await self.store_memory(
                topic=memory_entry.topic,
                content=memory_entry.content,
                memory_type=memory_entry.memory_type,
                tags=memory_entry.tags
            )
        except Exception as e:
            logger.error(f"Failed to log swarm event: {e}")
            # Buffer for retry
            self.event_buffer.append(event)
    
    @with_circuit_breaker("database")
    async def get_swarm_history(
        self,
        event_types: Optional[List[SwarmMemoryEventType]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get swarm execution history from memory.
        
        Args:
            event_types: Filter by specific event types
            limit: Maximum results
            
        Returns:
            List of swarm events
        """
        # Build search query
        if event_types:
            event_names = [et.value for et in event_types]
            query = f"SwarmEvent:({' OR '.join(event_names)})"
        else:
            query = f"SwarmEvent:{self.swarm_type}"
        
        memories = await self.search_memory(
            query=query,
            limit=limit,
            memory_type=MemoryType.EPISODIC,
            tags=["swarm_event"],
            include_other_swarms=False
        )
        
        # Parse event data from memory entries
        events = []
        for memory in memories:
            try:
                content = json.loads(memory.get("content", "{}"))
                events.append(content)
            except json.JSONDecodeError:
                continue
        
        return events
    
    # ============================================
    # Knowledge Management
    # ============================================
    
    async def store_pattern(
        self,
        pattern_name: str,
        pattern_data: Dict[str, Any],
        success_score: float,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Store successful pattern in memory system.
        
        Args:
            pattern_name: Name of the pattern
            pattern_data: Pattern configuration and results
            success_score: Quality/success score
            context: Optional context information
        """
        pattern_content = {
            "pattern_name": pattern_name,
            "pattern_data": pattern_data,
            "success_score": success_score,
            "context": context or {},
            "swarm_type": self.swarm_type,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.store_memory(
            topic=f"Pattern:{pattern_name}:{self.swarm_type}",
            content=json.dumps(pattern_content, default=str),
            memory_type=MemoryType.PROCEDURAL,
            tags=["pattern", "strategy", self.swarm_type, pattern_name],
            metadata={"success_score": success_score}
        )
    
    @with_circuit_breaker("database")
    async def retrieve_patterns(
        self,
        pattern_name: Optional[str] = None,
        min_success_score: float = 0.7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve successful patterns from memory.
        
        Args:
            pattern_name: Specific pattern name to search for
            min_success_score: Minimum success score threshold
            limit: Maximum results
            
        Returns:
            List of matching patterns
        """
        # Build search query
        if pattern_name:
            query = f"Pattern:{pattern_name}"
        else:
            query = f"Pattern swarm_type:{self.swarm_type}"
        
        memories = await self.search_memory(
            query=query,
            limit=limit,
            memory_type=MemoryType.PROCEDURAL,
            tags=["pattern"]
        )
        
        # Filter by success score and parse
        patterns = []
        for memory in memories:
            try:
                content = json.loads(memory.get("content", "{}"))
                if content.get("success_score", 0) >= min_success_score:
                    patterns.append(content)
            except json.JSONDecodeError:
                continue
        
        # Sort by success score
        patterns.sort(key=lambda p: p.get("success_score", 0), reverse=True)
        return patterns
    
    # ============================================
    # Inter-Swarm Communication
    # ============================================
    
    async def send_message_to_swarm(
        self,
        target_swarm_type: str,
        message: Dict[str, Any],
        priority: str = "normal"
    ):
        """
        Send message to another swarm through memory system.
        
        Args:
            target_swarm_type: Target swarm type
            message: Message content
            priority: Message priority (low, normal, high, critical)
        """
        comm_data = {
            "from_swarm": f"{self.swarm_type}:{self.swarm_id}",
            "to_swarm": target_swarm_type,
            "message": message,
            "priority": priority,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.store_memory(
            topic=f"InterSwarm:{self.swarm_type}->{target_swarm_type}",
            content=json.dumps(comm_data, default=str),
            memory_type=MemoryType.EPISODIC,
            tags=["inter_swarm", "communication", self.swarm_type, target_swarm_type, priority]
        )
        
        # Log communication event
        await self.log_swarm_event(
            SwarmMemoryEventType.INTER_SWARM_COMMUNICATION,
            {
                "target_swarm": target_swarm_type,
                "message_summary": str(message)[:100],
                "priority": priority
            }
        )
    
    @with_circuit_breaker("database")
    async def get_messages_for_swarm(
        self,
        priority_filter: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get messages sent to this swarm.
        
        Args:
            priority_filter: Filter by priority level
            limit: Maximum messages to retrieve
            
        Returns:
            List of messages for this swarm
        """
        # Search for messages to this swarm
        query = f"InterSwarm to_swarm:{self.swarm_type}"
        
        tags = ["inter_swarm", "communication", self.swarm_type]
        if priority_filter:
            tags.append(priority_filter)
        
        memories = await self.search_memory(
            query=query,
            limit=limit,
            memory_type=MemoryType.EPISODIC,
            tags=tags
        )
        
        # Parse and return messages
        messages = []
        for memory in memories:
            try:
                content = json.loads(memory.get("content", "{}"))
                if content.get("to_swarm") == self.swarm_type:
                    messages.append(content)
            except json.JSONDecodeError:
                continue
        
        # Sort by priority and timestamp
        priority_order = {"critical": 4, "high": 3, "normal": 2, "low": 1}
        messages.sort(
            key=lambda m: (
                priority_order.get(m.get("priority", "normal"), 2),
                m.get("timestamp", "")
            ),
            reverse=True
        )
        
        return messages
    
    # ============================================
    # Learning and Adaptation
    # ============================================
    
    async def store_learning(
        self,
        learning_type: str,
        content: str,
        confidence: float,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Store learning or insight gained by swarm.
        
        Args:
            learning_type: Type of learning (pattern, optimization, error_correction, etc.)
            content: Learning content
            confidence: Confidence in the learning (0.0-1.0)
            context: Optional context information
        """
        learning_data = {
            "learning_type": learning_type,
            "content": content,
            "confidence": confidence,
            "context": context or {},
            "swarm_type": self.swarm_type,
            "swarm_id": self.swarm_id
        }
        
        await self.store_memory(
            topic=f"Learning:{learning_type}:{self.swarm_type}",
            content=json.dumps(learning_data, default=str),
            memory_type=MemoryType.SEMANTIC,
            tags=["learning", learning_type, self.swarm_type],
            metadata={"confidence": confidence}
        )
        
        logger.info(f"Stored learning: {learning_type} (confidence: {confidence:.2f})")
    
    @with_circuit_breaker("database")
    async def retrieve_learnings(
        self,
        learning_type: Optional[str] = None,
        min_confidence: float = 0.7,
        include_other_swarms: bool = True,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant learnings from memory.
        
        Args:
            learning_type: Specific type of learning to search for
            min_confidence: Minimum confidence threshold
            include_other_swarms: Include learnings from other swarms
            limit: Maximum results
            
        Returns:
            List of relevant learnings
        """
        # Build search query
        if learning_type:
            query = f"Learning:{learning_type}"
        else:
            query = "Learning"
        
        tags = ["learning"]
        if not include_other_swarms:
            tags.append(self.swarm_type)
        
        memories = await self.search_memory(
            query=query,
            limit=limit,
            memory_type=MemoryType.SEMANTIC,
            tags=tags,
            include_other_swarms=include_other_swarms
        )
        
        # Filter by confidence and parse
        learnings = []
        for memory in memories:
            try:
                content = json.loads(memory.get("content", "{}"))
                if content.get("confidence", 0) >= min_confidence:
                    learnings.append(content)
            except json.JSONDecodeError:
                continue
        
        # Sort by confidence
        learnings.sort(key=lambda l: l.get("confidence", 0), reverse=True)
        return learnings
    
    # ============================================
    # Context Loading
    # ============================================
    
    async def load_swarm_context(self) -> Dict[str, Any]:
        """
        Load contextual information for swarm initialization.
        
        Returns:
            Context data including patterns, learnings, and history
        """
        context = {
            "swarm_type": self.swarm_type,
            "swarm_id": self.swarm_id,
            "loaded_at": datetime.now().isoformat()
        }
        
        # Load recent patterns
        context["patterns"] = await self.retrieve_patterns(limit=5)
        
        # Load recent learnings
        context["learnings"] = await self.retrieve_learnings(limit=10)
        
        # Load recent events
        context["recent_events"] = await self.get_swarm_history(limit=20)
        
        # Load inter-swarm messages
        context["messages"] = await self.get_messages_for_swarm(limit=10)
        
        logger.info(f"Loaded swarm context: {len(context['patterns'])} patterns, "
                   f"{len(context['learnings'])} learnings, {len(context['recent_events'])} events")
        
        return context
    
    # ============================================
    # Performance and Metrics
    # ============================================
    
    async def store_performance_metrics(
        self,
        metrics: Dict[str, Any],
        execution_context: Optional[Dict[str, Any]] = None
    ):
        """
        Store swarm performance metrics.
        
        Args:
            metrics: Performance metrics data
            execution_context: Optional execution context
        """
        metrics_data = {
            "metrics": metrics,
            "execution_context": execution_context or {},
            "swarm_type": self.swarm_type,
            "swarm_id": self.swarm_id,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.store_memory(
            topic=f"Metrics:{self.swarm_type}:{datetime.now().strftime('%Y%m%d_%H')}",
            content=json.dumps(metrics_data, default=str),
            memory_type=MemoryType.EPISODIC,
            tags=["metrics", "performance", self.swarm_type],
            metadata={"execution_time": metrics.get("execution_time", 0)}
        )
    
    @with_circuit_breaker("database")
    async def get_performance_trends(
        self,
        metric_name: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get performance trends over time.
        
        Args:
            metric_name: Specific metric to analyze
            days: Number of days to look back
            
        Returns:
            List of performance data points
        """
        query = f"Metrics:{self.swarm_type}"
        
        memories = await self.search_memory(
            query=query,
            limit=100,
            memory_type=MemoryType.EPISODIC,
            tags=["metrics", "performance"],
            include_other_swarms=False
        )
        
        # Parse and filter by date
        cutoff = datetime.now().timestamp() - (days * 24 * 3600)
        trends = []
        
        for memory in memories:
            try:
                content = json.loads(memory.get("content", "{}"))
                timestamp = datetime.fromisoformat(content.get("timestamp", "")).timestamp()
                
                if timestamp >= cutoff:
                    if metric_name and metric_name in content.get("metrics", {}):
                        trends.append({
                            "timestamp": content["timestamp"],
                            "value": content["metrics"][metric_name],
                            "context": content.get("execution_context", {})
                        })
                    elif not metric_name:
                        trends.append(content)
            except (json.JSONDecodeError, ValueError):
                continue
        
        # Sort by timestamp
        trends.sort(key=lambda t: t.get("timestamp", ""))
        return trends
    
    # ============================================
    # Utility Methods
    # ============================================
    
    def _cache_for_retry(self, operation: str, data: Dict[str, Any]):
        """Cache failed operation for retry."""
        if len(self.memory_cache) < 100:  # Limit cache size
            cache_key = f"{operation}_{hashlib.md5(json.dumps(data, default=str).encode()).hexdigest()[:8]}"
            self.memory_cache[cache_key] = {
                "operation": operation,
                "data": data,
                "timestamp": datetime.now(),
                "retry_count": 0
            }
    
    async def retry_failed_operations(self):
        """Retry failed memory operations."""
        if not self.memory_cache:
            return
        
        successful_operations = []
        
        for cache_key, cached_op in self.memory_cache.items():
            if cached_op["retry_count"] >= 3:  # Max retries
                continue
            
            try:
                if cached_op["operation"] == "store":
                    await self.store_memory(**cached_op["data"])
                    successful_operations.append(cache_key)
                    logger.info(f"Retry successful for: {cache_key}")
            except Exception as e:
                cached_op["retry_count"] += 1
                logger.warning(f"Retry failed for {cache_key}: {e}")
        
        # Remove successful operations from cache
        for key in successful_operations:
            del self.memory_cache[key]
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        try:
            async with self.session.get(f"{self.mcp_server_url}/mcp/stats") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"Failed to get stats: {response.status}"}
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}


# ============================================
# Memory Pattern Mixins
# ============================================

class SwarmMemoryMixin:
    """
    Mixin class to add memory capabilities to existing swarm classes.
    Provides memory integration without requiring major refactoring.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory_client: Optional[SwarmMemoryClient] = None
        self._memory_initialized = False
    
    async def initialize_memory(self, swarm_type: str, swarm_id: Optional[str] = None):
        """Initialize memory client for swarm."""
        if not swarm_id:
            swarm_id = f"{swarm_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.memory_client = SwarmMemoryClient(swarm_type, swarm_id)
        await self.memory_client.initialize()
        self._memory_initialized = True
        
        # Log initialization
        await self.memory_client.log_swarm_event(
            SwarmMemoryEventType.SWARM_INITIALIZED,
            {
                "agent_count": len(getattr(self, 'agents', [])),
                "config": getattr(self, 'config', {})
            }
        )
        
        logger.info(f"Memory initialized for {swarm_type}:{swarm_id}")
    
    async def close_memory(self):
        """Close memory client."""
        if self.memory_client:
            await self.memory_client.close()
            self.memory_client = None
            self._memory_initialized = False
    
    async def _store_task_execution(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Store task execution in memory."""
        if not self._memory_initialized:
            return
        
        # Log task completion
        await self.memory_client.log_swarm_event(
            SwarmMemoryEventType.TASK_COMPLETED,
            {
                "task_summary": str(task).get("description", str(task))[:200],
                "success": result.get("success", False),
                "quality_score": result.get("quality_score", 0),
                "execution_time": result.get("execution_time", 0),
                "agent_roles": result.get("agent_roles", [])
            }
        )
        
        # Store successful patterns
        if result.get("quality_score", 0) > 0.8:
            await self.memory_client.store_pattern(
                pattern_name=f"successful_{task.get('type', 'general')}",
                pattern_data={
                    "task": task,
                    "result_summary": {k: v for k, v in result.items() if k != "result"},
                    "agent_roles": result.get("agent_roles", [])
                },
                success_score=result.get("quality_score", 0),
                context={"execution_time": result.get("execution_time", 0)}
            )
    
    @with_circuit_breaker("database")
    async def _load_relevant_context(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Load relevant context from memory for task execution."""
        if not self._memory_initialized:
            return {}
        
        # Search for relevant patterns
        task_type = task.get("type", "general")
        patterns = await self.memory_client.retrieve_patterns(
            pattern_name=f"successful_{task_type}",
            limit=3
        )
        
        # Search for relevant learnings
        learnings = await self.memory_client.retrieve_learnings(
            learning_type="optimization",
            limit=5
        )
        
        # Get recent similar tasks
        similar_tasks = await self.memory_client.search_memory(
            query=str(task.get("description", ""))[:100],
            limit=5,
            memory_type=MemoryType.EPISODIC,
            tags=["swarm_event", "task_completed"]
        )
        
        return {
            "relevant_patterns": patterns,
            "relevant_learnings": learnings,
            "similar_tasks": similar_tasks
        }