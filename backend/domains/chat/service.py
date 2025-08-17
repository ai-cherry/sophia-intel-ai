"""
Unified Chat Service - Consolidates all chat functionality
Combines chat_proxy, chat_router, and unified_chat_service into single domain service
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import HTTPException
from loguru import logger

from .models import (
    ChatRequest, ChatResponse, ChatMessage, StreamingChatChunk, 
    ChatSession, BackendAnalysis
)
from .router import ChatRouter
from .streaming import StreamingChatHandler
from ..research.service import ResearchService
from ..persona.service import PersonaService
from ..monitoring.service import MonitoringService
from libs.mcp_client.enhanced_memory_client import EnhancedMemoryClient


class ChatService:
    """
    Unified chat service that handles all chat functionality:
    - Intelligent backend routing (Orchestrator vs Swarm)
    - Streaming responses
    - Web research integration
    - Persona enhancement
    - Voice generation
    - Memory management
    - Session analytics
    """
    
    def __init__(
        self,
        memory_client: EnhancedMemoryClient,
        research_service: ResearchService,
        persona_service: PersonaService,
        monitoring_service: MonitoringService
    ):
        self.memory_client = memory_client
        self.research_service = research_service
        self.persona_service = persona_service
        self.monitoring_service = monitoring_service
        
        # Initialize components
        self.router = ChatRouter()
        self.streaming_handler = StreamingChatHandler()
        
        # Session management
        self.active_sessions: Dict[str, ChatSession] = {}
        
        # Performance tracking
        self.backend_performance: Dict[str, List[float]] = {
            "orchestrator": [],
            "swarm": []
        }
        
        logger.info("ChatService initialized with unified architecture")
    
    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """
        Process chat request with intelligent routing and feature integration
        """
        start_time = time.time()
        
        try:
            # Ensure session exists
            session = await self._get_or_create_session(request.session_id, request.user_id)
            
            # Analyze message for backend selection
            backend_analysis = await self.router.analyze_message(
                request.message,
                request.conversation_history,
                request.use_swarm,
                request.backend_preference
            )
            
            # Pre-process with research if enabled
            enhanced_message = request.message
            research_results = None
            
            if request.web_access or request.deep_research:
                research_results = await self.research_service.enhance_message(
                    request.message,
                    depth=request.research_depth,
                    strategy=request.research_strategy
                )
                enhanced_message = research_results.get("enhanced_message", request.message)
            
            # Process with selected backend
            backend_response = await self._process_with_backend(
                backend_analysis.recommended_backend,
                enhanced_message,
                request,
                session
            )
            
            # Apply persona enhancement if enabled
            final_response = backend_response
            persona_applied = False
            
            if request.persona_enabled:
                persona_response = await self.persona_service.enhance_response(
                    backend_response,
                    session.persona_settings
                )
                final_response = persona_response.get("enhanced_response", backend_response)
                persona_applied = True
            
            # Generate voice if enabled
            voice_url = None
            if request.voice_enabled and request.voice_id:
                voice_url = await self.persona_service.generate_voice(
                    final_response,
                    request.voice_id,
                    session.voice_settings
                )
            
            # Update memory
            await self._update_memory(session, request, final_response, backend_analysis.recommended_backend)
            
            # Update session analytics
            await self._update_session_analytics(session, backend_analysis.recommended_backend, request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Track backend performance
            self.backend_performance[backend_analysis.recommended_backend].append(response_time)
            
            # Create response
            response = ChatResponse(
                message=final_response,
                session_id=session.session_id,
                backend_used=backend_analysis.recommended_backend,
                response_time=response_time,
                model_used=request.model,
                research_results=research_results,
                persona_applied=persona_applied,
                voice_url=voice_url,
                memory_updated=True,
                confidence_score=backend_analysis.confidence,
                routing_reason=backend_analysis.reasoning
            )
            
            # Log analytics
            await self.monitoring_service.track_chat_request(request, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            
            # Track error
            await self.monitoring_service.track_error("chat_processing", str(e))
            
            raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")
    
    async def process_streaming_chat(self, request: ChatRequest) -> AsyncGenerator[StreamingChatChunk, None]:
        """
        Process chat request with streaming response
        """
        start_time = time.time()
        stream_id = f"stream_{int(time.time() * 1000)}"
        
        try:
            # Ensure session exists
            session = await self._get_or_create_session(request.session_id, request.user_id)
            
            # Analyze message for backend selection
            backend_analysis = await self.router.analyze_message(
                request.message,
                request.conversation_history,
                request.use_swarm,
                request.backend_preference
            )
            
            # Pre-process with research if enabled
            enhanced_message = request.message
            if request.web_access or request.deep_research:
                research_results = await self.research_service.enhance_message(
                    request.message,
                    depth=request.research_depth,
                    strategy=request.research_strategy
                )
                enhanced_message = research_results.get("enhanced_message", request.message)
            
            # Stream response from backend
            full_response = ""
            chunk_count = 0
            
            async for chunk in self._stream_from_backend(
                backend_analysis.recommended_backend,
                enhanced_message,
                request,
                session
            ):
                chunk_count += 1
                full_response += chunk
                
                # Create streaming chunk
                streaming_chunk = StreamingChatChunk(
                    chunk_id=f"{stream_id}_{chunk_count}",
                    stream_id=stream_id,
                    content=chunk,
                    is_final=False,
                    metadata={
                        "backend_used": backend_analysis.recommended_backend,
                        "chunk_number": chunk_count
                    }
                )
                
                yield streaming_chunk
            
            # Apply persona enhancement to full response if enabled
            if request.persona_enabled:
                persona_response = await self.persona_service.enhance_response(
                    full_response,
                    session.persona_settings
                )
                full_response = persona_response.get("enhanced_response", full_response)
            
            # Send final chunk
            final_chunk = StreamingChatChunk(
                chunk_id=f"{stream_id}_final",
                stream_id=stream_id,
                content="",
                is_final=True,
                metadata={
                    "backend_used": backend_analysis.recommended_backend,
                    "total_chunks": chunk_count,
                    "response_time": time.time() - start_time,
                    "persona_applied": request.persona_enabled
                }
            )
            
            yield final_chunk
            
            # Update memory with full response
            await self._update_memory(session, request, full_response, backend_analysis.recommended_backend)
            
            # Update session analytics
            await self._update_session_analytics(session, backend_analysis.recommended_backend, request)
            
        except Exception as e:
            logger.error(f"Streaming chat failed: {e}")
            
            # Send error chunk
            error_chunk = StreamingChatChunk(
                chunk_id=f"{stream_id}_error",
                stream_id=stream_id,
                content=f"Error: {str(e)}",
                is_final=True,
                metadata={"error": True}
            )
            
            yield error_chunk
    
    async def get_session_info(self, session_id: str) -> Optional[ChatSession]:
        """Get session information"""
        return self.active_sessions.get(session_id)
    
    async def update_session_settings(
        self, 
        session_id: str, 
        persona_settings: Optional[Dict[str, Any]] = None,
        voice_settings: Optional[Dict[str, Any]] = None
    ) -> ChatSession:
        """Update session settings"""
        session = self.active_sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if persona_settings:
            session.persona_settings.update(persona_settings)
        
        if voice_settings:
            session.voice_settings.update(voice_settings)
        
        session.updated_at = datetime.now()
        
        return session
    
    async def get_backend_performance(self) -> Dict[str, Any]:
        """Get backend performance statistics"""
        stats = {}
        
        for backend, times in self.backend_performance.items():
            if times:
                stats[backend] = {
                    "avg_response_time": sum(times) / len(times),
                    "min_response_time": min(times),
                    "max_response_time": max(times),
                    "total_requests": len(times),
                    "p95_response_time": sorted(times)[int(len(times) * 0.95)] if len(times) > 20 else max(times) if times else 0
                }
            else:
                stats[backend] = {
                    "avg_response_time": 0,
                    "min_response_time": 0,
                    "max_response_time": 0,
                    "total_requests": 0,
                    "p95_response_time": 0
                }
        
        return stats
    
    # Private methods
    
    async def _get_or_create_session(self, session_id: Optional[str], user_id: Optional[str]) -> ChatSession:
        """Get existing session or create new one"""
        if not session_id:
            session_id = f"session_{int(time.time() * 1000)}"
        
        if session_id not in self.active_sessions:
            session = ChatSession(
                session_id=session_id,
                user_id=user_id,
                persona_settings={},
                voice_settings={}
            )
            self.active_sessions[session_id] = session
        
        return self.active_sessions[session_id]
    
    async def _process_with_backend(
        self, 
        backend: str, 
        message: str, 
        request: ChatRequest, 
        session: ChatSession
    ) -> str:
        """Process message with selected backend"""
        if backend == "swarm":
            return await self._process_with_swarm(message, request, session)
        else:
            return await self._process_with_orchestrator(message, request, session)
    
    async def _stream_from_backend(
        self, 
        backend: str, 
        message: str, 
        request: ChatRequest, 
        session: ChatSession
    ) -> AsyncGenerator[str, None]:
        """Stream response from selected backend"""
        if backend == "swarm":
            async for chunk in self._stream_from_swarm(message, request, session):
                yield chunk
        else:
            async for chunk in self._stream_from_orchestrator(message, request, session):
                yield chunk
    
    async def _process_with_orchestrator(self, message: str, request: ChatRequest, session: ChatSession) -> str:
        """Process with orchestrator backend"""
        # This would integrate with the actual orchestrator
        # For now, return a simulated response
        await asyncio.sleep(0.1)  # Simulate processing time
        return f"Orchestrator response to: {message}"
    
    async def _process_with_swarm(self, message: str, request: ChatRequest, session: ChatSession) -> str:
        """Process with swarm backend"""
        # This would integrate with the actual swarm system
        # For now, return a simulated response
        await asyncio.sleep(0.2)  # Simulate processing time
        return f"Swarm response to: {message}"
    
    async def _stream_from_orchestrator(self, message: str, request: ChatRequest, session: ChatSession) -> AsyncGenerator[str, None]:
        """Stream from orchestrator backend"""
        response = f"Orchestrator streaming response to: {message}"
        words = response.split()
        
        for word in words:
            yield word + " "
            await asyncio.sleep(0.05)  # Simulate streaming delay
    
    async def _stream_from_swarm(self, message: str, request: ChatRequest, session: ChatSession) -> AsyncGenerator[str, None]:
        """Stream from swarm backend"""
        response = f"Swarm streaming response to: {message}"
        words = response.split()
        
        for word in words:
            yield word + " "
            await asyncio.sleep(0.05)  # Simulate streaming delay
    
    async def _update_memory(self, session: ChatSession, request: ChatRequest, response: str, backend: str):
        """Update session memory"""
        try:
            # Add user message to memory
            await self.memory_client.add_message(
                session.session_id,
                ChatMessage(role="user", content=request.message)
            )
            
            # Add assistant response to memory
            await self.memory_client.add_message(
                session.session_id,
                ChatMessage(
                    role="assistant", 
                    content=response,
                    metadata={"backend": backend}
                )
            )
            
        except Exception as e:
            logger.warning(f"Memory update failed: {e}")
    
    async def _update_session_analytics(self, session: ChatSession, backend: str, request: ChatRequest):
        """Update session analytics"""
        session.message_count += 1
        session.updated_at = datetime.now()
        
        # Track backend usage
        if backend not in session.backend_usage:
            session.backend_usage[backend] = 0
        session.backend_usage[backend] += 1
        
        # Track feature usage
        features = []
        if request.web_access:
            features.append("web_access")
        if request.deep_research:
            features.append("deep_research")
        if request.persona_enabled:
            features.append("persona")
        if request.voice_enabled:
            features.append("voice")
        
        for feature in features:
            if feature not in session.feature_usage:
                session.feature_usage[feature] = 0
            session.feature_usage[feature] += 1
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for chat service"""
        return {
            "status": "healthy",
            "active_sessions": len(self.active_sessions),
            "backend_performance": await self.get_backend_performance(),
            "components": {
                "router": await self.router.health_check(),
                "streaming_handler": await self.streaming_handler.health_check(),
                "memory_client": await self.memory_client.health_check(),
                "research_service": await self.research_service.health_check(),
                "persona_service": await self.persona_service.health_check()
            }
        }

