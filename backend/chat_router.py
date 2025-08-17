"""
Intelligent Chat Router for SOPHIA Intel
Routes chat requests to appropriate backend (Orchestrator vs Swarm) based on message analysis
"""

import asyncio
import json
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from config.config import settings
from libs.mcp_client.memory_client import MCPMemoryClient
from swarm.chat_interface import SwarmChatInterface


class EnhancedChatRequest(BaseModel):
    """Enhanced chat request with all feature toggles and routing options"""
    message: str
    session_id: Optional[str] = None
    use_context: bool = True
    stream: bool = True
    # Feature toggle flags
    web_access: bool = False
    deep_research: bool = False
    training: bool = False
    use_swarm: bool = False  # New flag for explicit Swarm routing
    # Additional metadata
    user_id: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7


class ChatRouter:
    """
    Intelligent chat router that determines whether to use:
    - Orchestrator (LangGraph) via MCP for simple Q&A, coding, document editing
    - Swarm system for complex multi-phase tasks (plan → code → test)
    """

    def __init__(self):
        self.app = FastAPI(
            title="SOPHIA Chat Router",
            description="Intelligent routing for unified chat experience",
            version="2.0.0"
        )

        # Initialize components
        self.memory_client = MCPMemoryClient()
        self.swarm_interface = SwarmChatInterface()

        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Routing keywords for intelligent backend selection
        self.swarm_keywords = {
            # Multi-phase project keywords
            "project", "build", "create", "develop", "implement", "deploy",
            "architecture", "design", "plan", "strategy", "roadmap",
            # Testing and validation keywords
            "test", "validate", "verify", "check", "debug", "troubleshoot",
            # Complex analysis keywords
            "analyze", "research", "investigate", "compare", "evaluate",
            "comprehensive", "detailed", "thorough", "complete",
            # Workflow keywords
            "workflow", "process", "pipeline", "automation", "orchestrate",
            "coordinate", "manage", "organize", "structure"
        }

        self.orchestrator_keywords = {
            # Simple Q&A keywords
            "what", "how", "why", "when", "where", "who", "explain", "define",
            # Coding assistance keywords
            "code", "function", "class", "method", "variable", "syntax",
            "error", "fix", "help", "assist", "guide", "show",
            # Document editing keywords
            "edit", "write", "draft", "review", "format", "correct",
            "improve", "optimize", "refactor", "clean"
        }

        self._setup_routes()

    def _setup_routes(self):
        """Setup unified chat routing endpoints"""

        @self.app.post("/chat")
        async def unified_chat(request: EnhancedChatRequest):
            """
            Unified chat endpoint with intelligent routing
            """
            try:
                # Generate session ID if not provided
                session_id = request.session_id or str(uuid.uuid4())
                
                logger.info(f"Processing chat request for session {session_id}")
                logger.info(f"Feature flags: web_access={request.web_access}, "
                           f"deep_research={request.deep_research}, training={request.training}, "
                           f"use_swarm={request.use_swarm}")

                # Store user message in memory
                await self._store_user_message(session_id, request.message, request.user_id)

                # Determine backend routing
                backend_choice = self._determine_backend(request)
                
                logger.info(f"Routing to backend: {backend_choice}")

                if backend_choice == "swarm":
                    return await self._handle_swarm_request(request, session_id)
                else:
                    return await self._handle_orchestrator_request(request, session_id)

            except Exception as e:
                logger.error(f"Chat routing failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/chat/sessions/{session_id}/history")
        async def get_chat_history(session_id: str, limit: int = 50):
            """Get unified chat history for a session"""
            try:
                results = await self.memory_client.query(
                    session_id=session_id,
                    query="",
                    top_k=limit,
                    threshold=0.0,
                )

                # Sort by timestamp and format as chat history
                history = []
                for result in sorted(results, key=lambda x: x.get("metadata", {}).get("timestamp", 0)):
                    metadata = result.get("metadata", {})
                    role = metadata.get("role", "unknown")
                    content = result.get("content", "")
                    backend_used = metadata.get("backend_used", "unknown")

                    if role in ["user", "assistant"]:
                        history.append({
                            "role": role,
                            "content": content,
                            "timestamp": metadata.get("timestamp"),
                            "backend_used": backend_used
                        })

                return {
                    "session_id": session_id,
                    "history": history,
                    "total_messages": len(history)
                }

            except Exception as e:
                logger.error(f"Failed to get chat history: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/chat/sessions/{session_id}")
        async def clear_chat_session(session_id: str):
            """Clear a chat session"""
            try:
                result = await self.memory_client.clear_session(session_id)
                # Also reset swarm conversation for this session
                self.swarm_interface.reset_conversation()
                
                return {
                    "session_id": session_id,
                    "cleared": True,
                    "deleted_count": result.get("deleted_count", 0)
                }
            except Exception as e:
                logger.error(f"Failed to clear chat session: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/chat/backend/analyze")
        async def analyze_message_routing(message: str):
            """Analyze how a message would be routed (for debugging)"""
            try:
                request = EnhancedChatRequest(message=message)
                backend_choice = self._determine_backend(request)
                analysis = self._analyze_message_content(message)
                
                return {
                    "message": message,
                    "backend_choice": backend_choice,
                    "analysis": analysis,
                    "routing_logic": {
                        "swarm_score": analysis["swarm_score"],
                        "orchestrator_score": analysis["orchestrator_score"],
                        "explicit_swarm_flag": request.use_swarm
                    }
                }
            except Exception as e:
                logger.error(f"Failed to analyze message routing: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health")
        async def health():
            """Health check for chat router"""
            try:
                # Test orchestrator connectivity
                orchestrator_healthy = await self._test_orchestrator_health()
                
                # Test memory client
                memory_health = await self.memory_client.health_check()
                
                # Test swarm interface
                swarm_healthy = True  # Swarm is local, assume healthy
                
                return {
                    "status": "healthy" if all([orchestrator_healthy, memory_health.get("status") == "healthy", swarm_healthy]) else "unhealthy",
                    "components": {
                        "orchestrator": "healthy" if orchestrator_healthy else "unhealthy",
                        "memory_client": memory_health.get("status", "unknown"),
                        "swarm_interface": "healthy" if swarm_healthy else "unhealthy"
                    },
                    "version": "2.0.0"
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return {"status": "unhealthy", "error": str(e)}

    def _determine_backend(self, request: EnhancedChatRequest) -> str:
        """
        Intelligent backend selection based on message analysis and flags
        """
        # Explicit Swarm flag takes precedence
        if request.use_swarm:
            return "swarm"
        
        # Analyze message content for routing hints
        analysis = self._analyze_message_content(request.message)
        
        # Complex multi-phase tasks → Swarm
        if analysis["swarm_score"] > analysis["orchestrator_score"]:
            return "swarm"
        
        # Deep research flag suggests complex analysis → Swarm
        if request.deep_research:
            return "swarm"
        
        # Default to orchestrator for simple tasks
        return "orchestrator"

    def _analyze_message_content(self, message: str) -> Dict[str, Any]:
        """
        Analyze message content to determine routing preference
        """
        message_lower = message.lower()
        
        # Count keyword matches
        swarm_matches = sum(1 for keyword in self.swarm_keywords if keyword in message_lower)
        orchestrator_matches = sum(1 for keyword in self.orchestrator_keywords if keyword in message_lower)
        
        # Look for complexity indicators
        complexity_indicators = [
            len(message.split()) > 50,  # Long messages
            message.count('?') > 2,     # Multiple questions
            'step by step' in message_lower,
            'comprehensive' in message_lower,
            'detailed analysis' in message_lower,
            'multi-phase' in message_lower,
            'end-to-end' in message_lower
        ]
        
        complexity_score = sum(complexity_indicators)
        
        # Calculate final scores
        swarm_score = swarm_matches + complexity_score
        orchestrator_score = orchestrator_matches
        
        return {
            "swarm_score": swarm_score,
            "orchestrator_score": orchestrator_score,
            "swarm_keywords_found": swarm_matches,
            "orchestrator_keywords_found": orchestrator_matches,
            "complexity_indicators": complexity_score,
            "message_length": len(message.split()),
            "routing_recommendation": "swarm" if swarm_score > orchestrator_score else "orchestrator"
        }

    async def _handle_swarm_request(self, request: EnhancedChatRequest, session_id: str) -> Dict[str, Any]:
        """Handle request using Swarm system"""
        try:
            # Prepare context for Swarm
            context = {
                "session_id": session_id,
                "user_id": request.user_id,
                "feature_flags": {
                    "web_access": request.web_access,
                    "deep_research": request.deep_research,
                    "training": request.training
                }
            }
            
            # Process with Swarm
            swarm_response = self.swarm_interface.handle_message(
                message=request.message,
                user_id=request.user_id,
                context=context
            )
            
            # Store AI response in memory
            response_content = swarm_response.get("text", "")
            await self._store_ai_message(session_id, response_content, request.user_id, "swarm")
            
            return {
                "session_id": session_id,
                "response": response_content,
                "backend_used": "swarm",
                "swarm_metadata": swarm_response.get("swarm_summary", {}),
                "success": swarm_response.get("success", True)
            }
            
        except Exception as e:
            logger.error(f"Swarm request failed: {e}")
            raise

    async def _handle_orchestrator_request(self, request: EnhancedChatRequest, session_id: str) -> Dict[str, Any]:
        """Handle request using Orchestrator (MCP)"""
        try:
            # Prepare request for MCP server
            mcp_request = {
                "prompt": request.message,
                "session_id": session_id,
                "use_context": request.use_context,
                "stream": request.stream,
                "web_access": request.web_access,
                "deep_research": request.deep_research,
                "training": request.training,
                "metadata": {
                    "source": "chat_router",
                    "timestamp": asyncio.get_event_loop().time(),
                    "user_id": request.user_id
                }
            }

            if request.stream:
                # Return streaming response
                return StreamingResponse(
                    self._stream_orchestrator_response(mcp_request, session_id, request.user_id),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Session-ID": session_id,
                        "X-Backend-Used": "orchestrator"
                    }
                )
            else:
                # Get non-streaming response
                response = await self._get_orchestrator_response(mcp_request)
                
                # Store AI response in memory
                if response.get("content"):
                    await self._store_ai_message(session_id, response["content"], request.user_id, "orchestrator")
                
                return {
                    "session_id": session_id,
                    "response": response.get("content", ""),
                    "backend_used": "orchestrator",
                    "metadata": response.get("metadata", {}),
                    "success": True
                }
                
        except Exception as e:
            logger.error(f"Orchestrator request failed: {e}")
            raise

    async def _stream_orchestrator_response(self, mcp_request: Dict[str, Any], session_id: str, user_id: Optional[str]):
        """Stream response from orchestrator"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{settings.ORCHESTRATOR_URL}/ai/chat",
                    json=mcp_request,
                    headers={"Accept": "text/event-stream"}
                ) as response:
                    response.raise_for_status()
                    
                    full_response = ""
                    async for chunk in response.aiter_text():
                        if chunk.strip():
                            yield f"data: {json.dumps({'content': chunk, 'session_id': session_id, 'backend_used': 'orchestrator'})}\\n\\n"
                            full_response += chunk
                    
                    # Store complete response
                    if full_response:
                        await self._store_ai_message(session_id, full_response, user_id, "orchestrator")
                    
                    yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'backend_used': 'orchestrator'})}\\n\\n"
                    
        except Exception as e:
            logger.error(f"Orchestrator streaming failed: {e}")
            yield f"data: {json.dumps({'error': str(e), 'session_id': session_id, 'backend_used': 'orchestrator'})}\\n\\n"

    async def _get_orchestrator_response(self, mcp_request: Dict[str, Any]) -> Dict[str, Any]:
        """Get non-streaming response from orchestrator"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(f"{settings.ORCHESTRATOR_URL}/ai/chat", json=mcp_request)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Orchestrator request failed: {e}")
            raise

    async def _test_orchestrator_health(self) -> bool:
        """Test orchestrator connectivity"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{settings.ORCHESTRATOR_URL}/health")
                return response.status_code == 200
        except Exception:
            return False

    async def _store_user_message(self, session_id: str, message: str, user_id: Optional[str]):
        """Store user message in memory"""
        try:
            await self.memory_client.store(
                session_id=session_id,
                content=message,
                metadata={
                    "role": "user",
                    "timestamp": asyncio.get_event_loop().time(),
                    "user_id": user_id
                },
                context_type="chat_message"
            )
        except Exception as e:
            logger.warning(f"Failed to store user message: {e}")

    async def _store_ai_message(self, session_id: str, message: str, user_id: Optional[str], backend_used: str):
        """Store AI response in memory"""
        try:
            await self.memory_client.store(
                session_id=session_id,
                content=message,
                metadata={
                    "role": "assistant",
                    "timestamp": asyncio.get_event_loop().time(),
                    "user_id": user_id,
                    "backend_used": backend_used
                },
                context_type="chat_message"
            )
        except Exception as e:
            logger.warning(f"Failed to store AI message: {e}")


# Create FastAPI app instance
chat_router = ChatRouter()
app = chat_router.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

