"""
Chat Service V2 - Proper dependency injection architecture
Unified chat functionality with intelligent routing
"""

from typing import Dict, Any, Optional, AsyncGenerator
import asyncio
from datetime import datetime

from backend.core.base_service import BaseService
from backend.config.settings import Settings
from .models import ChatRequest, ChatResponse, ChatMessage
from .router import ChatRouter
from .streaming import StreamingChatHandler


class ChatService(BaseService):
    """Unified chat service with dependency injection"""
    
    def __init__(self, name: str, dependencies: Optional[Dict[str, Any]] = None):
        super().__init__(name, dependencies)
        self.settings: Optional[Settings] = None
        self.router: Optional[ChatRouter] = None
        self.streaming_handler: Optional[StreamingChatHandler] = None
        self.session_memory: Dict[str, Dict[str, Any]] = {}
    
    async def _initialize(self) -> None:
        """Initialize chat service"""
        # Get settings from dependencies or create default
        self.settings = self.dependencies.get('settings') or Settings()
        
        # Initialize components
        self.router = ChatRouter(self.settings)
        self.streaming_handler = StreamingChatHandler(self.settings)
        
        self.logger.info("Chat service initialized with intelligent routing")
    
    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request with intelligent routing"""
        try:
            start_time = datetime.utcnow()
            
            # Get or create session context
            session_context = self._get_session_context(request.session_id)
            
            # Determine backend if not explicitly specified
            if not request.use_swarm:
                backend = await self.router.select_backend(
                    request.message, 
                    explicit_backend=None,
                    context=session_context
                )
            else:
                backend = 'swarm'
            
            # Update session context
            session_context['recent_backend'] = backend
            session_context['message_count'] = session_context.get('message_count', 0) + 1
            
            # Process with selected backend
            if backend == 'swarm':
                response_content = await self._process_with_swarm(request)
            else:
                response_content = await self._process_with_orchestrator(request)
            
            # Calculate performance metrics
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            
            # Create response
            response = ChatResponse(
                message=response_content,
                session_id=request.session_id,
                backend_used=backend,
                response_time=response_time,
                model_used=request.model or "claude-3-5-sonnet-20241022",
                performance_metrics={
                    'response_time': response_time,
                    'backend': backend,
                    'timestamp': end_time.isoformat()
                },
                sophia_context={
                    'session_message_count': session_context['message_count'],
                    'backend_confidence': session_context.get('backend_confidence', 0.5)
                }
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing chat request: {e}")
            return ChatResponse(
                message=f"I apologize, but I encountered an error: {str(e)}",
                session_id=request.session_id,
                backend_used='error',
                response_time=0.0,
                model_used="error",
                error=str(e)
            )
    
    async def stream_chat_response(self, request: ChatRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response in real-time"""
        try:
            # Determine backend
            session_context = self._get_session_context(request.session_id)
            backend = await self.router.select_backend(request.message, context=session_context)
            
            # Create mock streaming response (in real implementation, this would call actual backends)
            async def mock_response_generator():
                response_parts = [
                    "I understand your question about ",
                    request.message[:50] + "..." if len(request.message) > 50 else request.message,
                    ". Let me provide you with a comprehensive response. ",
                    "This is being processed by the ",
                    backend,
                    " backend for optimal results."
                ]
                
                for part in response_parts:
                    yield part
                    await asyncio.sleep(0.1)  # Simulate processing time
            
            # Stream response
            async for chunk in self.streaming_handler.stream_response(
                mock_response_generator(),
                request.session_id,
                metadata={'backend': backend}
            ):
                yield chunk
                
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "session_id": request.session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _process_with_swarm(self, request: ChatRequest) -> str:
        """Process request with Swarm backend"""
        # Mock implementation - in real system, this would call the Swarm orchestrator
        await asyncio.sleep(0.2)  # Simulate processing time
        return f"[Swarm Response] I've analyzed your request comprehensively. {request.message[:100]}..."
    
    async def _process_with_orchestrator(self, request: ChatRequest) -> str:
        """Process request with Orchestrator backend"""
        # Mock implementation - in real system, this would call the Orchestrator
        await asyncio.sleep(0.1)  # Simulate processing time
        return f"[Orchestrator Response] Here's a direct answer to your question: {request.message[:100]}..."
    
    def _get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get or create session context"""
        if session_id not in self.session_memory:
            self.session_memory[session_id] = {
                'created_at': datetime.utcnow(),
                'message_count': 0,
                'recent_backend': None
            }
        return self.session_memory[session_id]
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get session statistics"""
        context = self.session_memory.get(session_id, {})
        return {
            'session_id': session_id,
            'message_count': context.get('message_count', 0),
            'recent_backend': context.get('recent_backend'),
            'created_at': context.get('created_at', datetime.utcnow()).isoformat() if context.get('created_at') else None
        }
    
    async def _health_check(self) -> Dict[str, Any]:
        """Chat service health check"""
        try:
            # Test router
            router_health = await self.router.health_check()
            
            # Test streaming handler
            streaming_health = await self.streaming_handler.health_check()
            
            return {
                'router': router_health,
                'streaming': streaming_health,
                'active_sessions': len(self.session_memory),
                'status': 'healthy'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

