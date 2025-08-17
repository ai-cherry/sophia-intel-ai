"""
Chat Proxy Service for SOPHIA Intel Dashboard
Provides streaming chat interface with MCP server integration
"""

import asyncio
import json
import uuid
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from config.config import settings
from libs.mcp_client.memory_client import MCPMemoryClient


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    use_context: bool = True
    stream: bool = True
    # Feature toggle flags
    web_access: bool = False
    deep_research: bool = False
    training: bool = False


class ChatProxy:
    """
    Chat proxy service that forwards requests to the Enhanced Unified MCP Server
    with streaming support and memory integration.
    """

    def __init__(self):
        self.app = FastAPI(
            title="SOPHIA Chat Proxy", description="Streaming chat interface for SOPHIA Intel", version="1.0.0"
        )

        # Initialize MCP Memory Client
        self.memory_client = MCPMemoryClient()

        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        @self.app.post("/chat")
        async def chat(request: ChatRequest):
            """
            Handle chat requests with streaming support and memory integration
            """
            try:
                # Generate session ID if not provided
                session_id = request.session_id or str(uuid.uuid4())

                logger.info(f"Processing chat request for session {session_id}")

                # Store user message in memory
                await self._store_user_message(session_id, request.message)

                # Prepare request for MCP server
                mcp_request = {
                    "prompt": request.message,
                    "session_id": session_id,
                    "use_context": request.use_context,
                    "stream": request.stream,
                    "web_access": request.web_access,
                    "deep_research": request.deep_research,
                    "training": request.training,
                    "metadata": {"source": "dashboard_chat", "timestamp": asyncio.get_event_loop().time()},
                }

                if request.stream:
                    # Return streaming response
                    return StreamingResponse(
                        self._stream_chat_response(mcp_request, session_id),
                        media_type="text/event-stream",
                        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Session-ID": session_id},
                    )
                else:
                    # Return regular response
                    response = await self._get_chat_response(mcp_request)

                    # Store AI response in memory
                    if response.get("content"):
                        await self._store_ai_message(session_id, response["content"])

                    return {
                        "session_id": session_id,
                        "response": response.get("content", ""),
                        "metadata": response.get("metadata", {}),
                    }

            except Exception as e:
                logger.error(f"Chat request failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/chat/sessions/{session_id}/history")
        async def get_chat_history(session_id: str, limit: int = 50):
            """Get chat history for a session"""
            try:
                results = await self.memory_client.query(
                    session_id=session_id,
                    query="",  # Empty query to get all messages
                    top_k=limit,
                    threshold=0.0,  # Get all messages regardless of similarity
                )

                # Sort by timestamp and format as chat history
                history = []
                for result in sorted(results, key=lambda x: x.get("metadata", {}).get("timestamp", 0)):
                    metadata = result.get("metadata", {})
                    role = metadata.get("role", "unknown")
                    content = result.get("content", "")

                    if role in ["user", "assistant"]:
                        history.append({"role": role, "content": content, "timestamp": metadata.get("timestamp")})

                return {"session_id": session_id, "history": history, "total_messages": len(history)}

            except Exception as e:
                logger.error(f"Failed to get chat history: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/chat/sessions/{session_id}")
        async def clear_chat_session(session_id: str):
            """Clear a chat session"""
            try:
                result = await self.memory_client.clear_session(session_id)
                return {"session_id": session_id, "cleared": True, "deleted_count": result.get("deleted_count", 0)}
            except Exception as e:
                logger.error(f"Failed to clear chat session: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health")
        async def health():
            """Health check endpoint"""
            try:
                # Test MCP server connectivity
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{settings.ORCHESTRATOR_URL}/health")
                    mcp_healthy = response.status_code == 200

                # Test memory client
                memory_health = await self.memory_client.health_check()

                return {
                    "status": "healthy" if mcp_healthy and memory_health.get("status") == "healthy" else "unhealthy",
                    "mcp_server": "healthy" if mcp_healthy else "unhealthy",
                    "memory_client": memory_health.get("status", "unknown"),
                    "version": "1.0.0",
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return {"status": "unhealthy", "error": str(e)}

    async def _stream_chat_response(self, mcp_request: Dict[str, Any], session_id: str):
        """Stream chat response from MCP server"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{settings.ORCHESTRATOR_URL}/ai/chat",
                    json=mcp_request,
                    headers={"Accept": "text/event-stream"},
                ) as response:
                    response.raise_for_status()

                    full_response = ""
                    async for chunk in response.aiter_text():
                        if chunk.strip():
                            # Send chunk to client
                            yield f"data: {json.dumps({'content': chunk, 'session_id': session_id})}\\n\\n"
                            full_response += chunk

                    # Store complete AI response in memory
                    if full_response:
                        await self._store_ai_message(session_id, full_response)

                    # Send completion signal
                    yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\\n\\n"

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"data: {json.dumps({'error': str(e), 'session_id': session_id})}\\n\\n"

    async def _get_chat_response(self, mcp_request: Dict[str, Any]) -> Dict[str, Any]:
        """Get non-streaming chat response from MCP server"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(f"{settings.ORCHESTRATOR_URL}/ai/chat", json=mcp_request)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Chat request failed: {e}")
            raise

    async def _store_user_message(self, session_id: str, message: str):
        """Store user message in memory"""
        try:
            await self.memory_client.store(
                session_id=session_id,
                content=message,
                metadata={"role": "user", "timestamp": asyncio.get_event_loop().time()},
                context_type="chat_message",
            )
        except Exception as e:
            logger.warning(f"Failed to store user message: {e}")

    async def _store_ai_message(self, session_id: str, message: str):
        """Store AI response in memory"""
        try:
            await self.memory_client.store(
                session_id=session_id,
                content=message,
                metadata={"role": "assistant", "timestamp": asyncio.get_event_loop().time()},
                context_type="chat_message",
            )
        except Exception as e:
            logger.warning(f"Failed to store AI message: {e}")


# Create FastAPI app instance
chat_proxy = ChatProxy()
app = chat_proxy.app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
