"""
Unified Chat Orchestrator
Central controller for the integrated chat UI with swarms, NL, and memory
"""

import asyncio
import json
from typing import Dict, Any, Optional, AsyncGenerator, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from app.orchestration.unified_facade import UnifiedOrchestratorFacade, SwarmRequest, SwarmType, OptimizationMode
from app.orchestration.mode_normalizer import get_mode_normalizer
from app.api.nl_processor import QuickNLPProcessor
from app.mcp.unified_memory import UnifiedMemoryStore
from app.core.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types of messages in the chat"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    SWARM_STATUS = "swarm_status"
    MEMORY_CONTEXT = "memory_context"
    DEBUG = "debug"

@dataclass
class ChatMessage:
    """Unified chat message structure"""
    id: str
    type: MessageType
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    memory_refs: List[str] = None
    swarm_execution_id: Optional[str] = None
    confidence: Optional[float] = None

@dataclass
class SwarmVisualizationData:
    """Data for real-time swarm visualization"""
    execution_id: str
    swarm_type: str
    current_step: str
    progress: float
    agent_states: Dict[str, str]
    debate_flow: List[Dict]
    metrics: Dict[str, float]
    patterns_active: List[str]

@dataclass
class MemoryContextData:
    """Memory context for current conversation"""
    relevant_memories: List[Dict]
    suggested_memories: List[Dict]
    memory_graph: Dict  # For visualization
    coherence_score: float

class UnifiedChatOrchestrator:
    """
    Orchestrates all chat UI components:
    - NL processing
    - Swarm execution & visualization
    - Memory integration
    - Real-time updates
    """
    
    def __init__(self):
        # Core components
        self.nl_processor = QuickNLPProcessor()
        self.swarm_orchestrator = UnifiedOrchestratorFacade()
        self.memory_store = UnifiedMemoryStore()
        self.mode_normalizer = get_mode_normalizer()
        
        # WebSocket for real-time updates
        self.ws_manager = WebSocketManager()
        
        # Session management
        self.active_sessions: Dict[str, Dict] = {}
        self.conversation_history: Dict[str, List[ChatMessage]] = {}
        
        # Metrics
        self.metrics = {
            "messages_processed": 0,
            "swarms_executed": 0,
            "memories_accessed": 0,
            "avg_response_time": 0.0
        }
        
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing Unified Chat Orchestrator")
        
        # Initialize components
        await self.swarm_orchestrator.initialize()
        await self.memory_store.initialize()
        await self.nl_processor.initialize()
        await self.ws_manager.initialize()
        
        logger.info("Unified Chat Orchestrator initialized")
    
    async def process_message(
        self,
        session_id: str,
        message: str,
        user_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a user message with full integration
        
        Yields:
            Stream of events (messages, swarm updates, memory context)
        """
        start_time = datetime.utcnow()
        self.metrics["messages_processed"] += 1
        
        # Create message
        user_message = ChatMessage(
            id=f"msg_{datetime.utcnow().timestamp()}",
            type=MessageType.USER,
            content=message,
            timestamp=datetime.utcnow(),
            metadata={"user_id": user_id}
        )
        
        # Store in history
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        self.conversation_history[session_id].append(user_message)
        
        # Yield user message
        yield {
            "type": "message",
            "data": asdict(user_message)
        }
        
        try:
            # 1. Get memory context
            memory_context = await self._get_memory_context(message, session_id)
            if memory_context.relevant_memories:
                yield {
                    "type": "memory_context",
                    "data": asdict(memory_context)
                }
            
            # 2. Process with NL
            nl_result = await self.nl_processor.process(
                message,
                context={"memories": memory_context.relevant_memories}
            )
            
            # 3. Determine execution path
            if nl_result.intent == "swarm_execution":
                # Execute with swarm
                async for event in self._execute_swarm(
                    session_id,
                    nl_result,
                    memory_context
                ):
                    yield event
                    
            elif nl_result.intent == "memory_operation":
                # Handle memory operation
                result = await self._handle_memory_operation(nl_result)
                yield {
                    "type": "message",
                    "data": asdict(ChatMessage(
                        id=f"msg_{datetime.utcnow().timestamp()}",
                        type=MessageType.ASSISTANT,
                        content=result["message"],
                        timestamp=datetime.utcnow(),
                        metadata=result
                    ))
                }
                
            else:
                # Simple response
                yield {
                    "type": "message",
                    "data": asdict(ChatMessage(
                        id=f"msg_{datetime.utcnow().timestamp()}",
                        type=MessageType.ASSISTANT,
                        content=nl_result.response,
                        timestamp=datetime.utcnow(),
                        confidence=nl_result.confidence
                    ))
                }
            
            # 4. Store conversation in memory
            await self._store_conversation_memory(
                session_id,
                user_message,
                nl_result
            )
            
            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics["avg_response_time"] = (
                self.metrics["avg_response_time"] * 0.9 + duration * 0.1
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            yield {
                "type": "error",
                "data": {
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
    
    async def _get_memory_context(
        self,
        message: str,
        session_id: str
    ) -> MemoryContextData:
        """Get relevant memory context for the message"""
        self.metrics["memories_accessed"] += 1
        
        try:
            # Search for relevant memories
            relevant = await self.memory_store.search_memory(
                query=message,
                limit=5,
                metadata_filter={"session_id": session_id}
            )
            
            # Get suggested memories based on patterns
            suggested = await self.memory_store.get_suggestions(
                context=message,
                limit=3
            )
            
            # Build memory graph for visualization
            memory_graph = await self._build_memory_graph(relevant)
            
            # Calculate coherence score
            coherence = self._calculate_coherence(relevant, message)
            
            return MemoryContextData(
                relevant_memories=relevant,
                suggested_memories=suggested,
                memory_graph=memory_graph,
                coherence_score=coherence
            )
            
        except Exception as e:
            logger.warning(f"Failed to get memory context: {e}")
            return MemoryContextData(
                relevant_memories=[],
                suggested_memories=[],
                memory_graph={},
                coherence_score=0.0
            )
    
    async def _execute_swarm(
        self,
        session_id: str,
        nl_result: Any,
        memory_context: MemoryContextData
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute swarm with real-time visualization"""
        self.metrics["swarms_executed"] += 1
        
        # Determine swarm type and mode
        task = nl_result.extracted_task or nl_result.query
        complexity = self.swarm_orchestrator.optimizer.calculate_task_complexity(task)
        
        # Select swarm type
        if "code" in task.lower():
            swarm_type = SwarmType.CODING_DEBATE
        elif complexity > 0.7:
            swarm_type = SwarmType.IMPROVED_SOLVE
        elif nl_result.suggested_assistants:
            swarm_type = SwarmType.MCP_COORDINATED
        else:
            swarm_type = SwarmType.SIMPLE_AGENTS
        
        # Select optimization mode
        mode = self.mode_normalizer.select_mode_for_task(
            task_complexity=complexity,
            urgency=nl_result.urgency or "normal"
        )
        
        # Create swarm request
        request = SwarmRequest(
            swarm_type=swarm_type,
            task=task,
            mode=OptimizationMode(mode.value),
            urgency=nl_result.urgency or "normal",
            use_memory=True,
            stream=True,
            session_id=session_id,
            metadata={
                "nl_confidence": nl_result.confidence,
                "memory_coherence": memory_context.coherence_score
            },
            mcp_assistants=nl_result.suggested_assistants
        )
        
        # Create execution ID
        execution_id = f"exec_{session_id}_{datetime.utcnow().timestamp()}"
        
        # Initial visualization data
        viz_data = SwarmVisualizationData(
            execution_id=execution_id,
            swarm_type=swarm_type.value,
            current_step="initializing",
            progress=0.0,
            agent_states={},
            debate_flow=[],
            metrics={},
            patterns_active=[]
        )
        
        # Yield initial swarm status
        yield {
            "type": "swarm_visualization",
            "data": asdict(viz_data)
        }
        
        # Execute swarm with streaming
        step_count = 0
        total_steps = 10  # Estimate
        
        async for event in self.swarm_orchestrator.execute(request):
            step_count += 1
            
            # Update visualization
            viz_data.current_step = event.event_type
            viz_data.progress = min(step_count / total_steps, 0.95)
            
            if event.event_type == "step":
                # Update agent states
                if "agent" in event.data:
                    viz_data.agent_states[event.data["agent"]] = event.data.get("status", "active")
                
                # Add to debate flow
                viz_data.debate_flow.append({
                    "step": step_count,
                    "type": event.event_type,
                    "data": event.data,
                    "timestamp": event.timestamp
                })
                
            elif event.event_type == "critic":
                # Add critic decision to flow
                viz_data.debate_flow.append({
                    "step": step_count,
                    "type": "critic",
                    "verdict": event.data.get("verdict"),
                    "confidence": event.data.get("confidence"),
                    "timestamp": event.timestamp
                })
                
            elif event.event_type == "completed":
                viz_data.progress = 1.0
                viz_data.current_step = "completed"
                viz_data.metrics = event.data.get("metrics", {})
                
                # Create assistant message with result
                yield {
                    "type": "message",
                    "data": asdict(ChatMessage(
                        id=f"msg_{datetime.utcnow().timestamp()}",
                        type=MessageType.ASSISTANT,
                        content=self._format_swarm_result(event.data["result"]),
                        timestamp=datetime.utcnow(),
                        swarm_execution_id=execution_id,
                        metadata=event.data
                    ))
                }
                
            # Yield visualization update
            yield {
                "type": "swarm_visualization",
                "data": asdict(viz_data)
            }
            
            # Broadcast to WebSocket subscribers
            await self.ws_manager.broadcast(
                f"swarm_{session_id}",
                {
                    "type": "swarm_update",
                    "execution_id": execution_id,
                    "event": event.event_type,
                    "data": event.data
                }
            )
    
    async def _handle_memory_operation(self, nl_result: Any) -> Dict[str, Any]:
        """Handle memory-specific operations"""
        operation = nl_result.memory_operation
        
        if operation == "store":
            result = await self.memory_store.store_memory(
                content=nl_result.content,
                metadata=nl_result.metadata
            )
            return {
                "message": f"Stored memory: {result['id']}",
                "memory_id": result["id"]
            }
            
        elif operation == "search":
            results = await self.memory_store.search_memory(
                query=nl_result.query,
                limit=nl_result.limit or 10
            )
            return {
                "message": f"Found {len(results)} memories",
                "memories": results
            }
            
        elif operation == "update":
            result = await self.memory_store.update_memory(
                memory_id=nl_result.memory_id,
                content=nl_result.content,
                metadata=nl_result.metadata
            )
            return {
                "message": f"Updated memory: {nl_result.memory_id}",
                "memory": result
            }
            
        else:
            return {
                "message": f"Unknown memory operation: {operation}"
            }
    
    async def _store_conversation_memory(
        self,
        session_id: str,
        user_message: ChatMessage,
        nl_result: Any
    ):
        """Store conversation in memory for future reference"""
        try:
            await self.memory_store.store_memory(
                content=json.dumps({
                    "user": user_message.content,
                    "assistant": nl_result.response,
                    "intent": nl_result.intent,
                    "confidence": nl_result.confidence
                }),
                metadata={
                    "type": "conversation",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_id": user_message.metadata.get("user_id")
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store conversation memory: {e}")
    
    async def _build_memory_graph(self, memories: List[Dict]) -> Dict:
        """Build memory graph for visualization"""
        nodes = []
        edges = []
        
        for i, memory in enumerate(memories):
            nodes.append({
                "id": memory.get("id", f"mem_{i}"),
                "label": memory.get("content", "")[:50],
                "type": memory.get("metadata", {}).get("type", "general")
            })
            
            # Create edges based on similarity or references
            if i > 0:
                edges.append({
                    "from": nodes[i-1]["id"],
                    "to": nodes[i]["id"],
                    "weight": 0.5  # Similarity score
                })
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    def _calculate_coherence(self, memories: List[Dict], message: str) -> float:
        """Calculate coherence score between memories and message"""
        if not memories:
            return 0.0
        
        # Simple coherence based on keyword overlap
        message_words = set(message.lower().split())
        memory_words = set()
        
        for memory in memories:
            content = memory.get("content", "")
            memory_words.update(content.lower().split())
        
        if not memory_words:
            return 0.0
        
        overlap = len(message_words & memory_words)
        return min(overlap / len(message_words), 1.0)
    
    def _format_swarm_result(self, result: Dict) -> str:
        """Format swarm result for display"""
        if isinstance(result, dict):
            if "solution" in result:
                return result["solution"]
            elif "answer" in result:
                return result["answer"]
            elif "results" in result:
                return json.dumps(result["results"], indent=2)
            else:
                return json.dumps(result, indent=2)
        else:
            return str(result)
    
    async def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get current session state"""
        return {
            "session_id": session_id,
            "conversation": [
                asdict(msg) for msg in self.conversation_history.get(session_id, [])
            ],
            "active": session_id in self.active_sessions,
            "metrics": self.metrics
        }
    
    async def export_conversation(
        self,
        session_id: str,
        format: str = "json"
    ) -> str:
        """Export conversation in specified format"""
        conversation = self.conversation_history.get(session_id, [])
        
        if format == "json":
            return json.dumps([asdict(msg) for msg in conversation], indent=2)
        elif format == "txt":
            lines = []
            for msg in conversation:
                lines.append(f"[{msg.timestamp}] {msg.type.value}: {msg.content}")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")