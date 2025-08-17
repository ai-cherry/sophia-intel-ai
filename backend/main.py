"""
Main Backend Application for SOPHIA Intel Dashboard
Combines chat proxy, web access, and research capabilities
"""

import asyncio
import json
import uuid
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from backend.notion_service import NotionCreatePageRequest, NotionSearchRequest, NotionService
from backend.web_access_service import WebAccessService, WebScrapeRequest, WebSearchRequest
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
    use_swarm: bool = False  # New flag for explicit Swarm routing
    # Additional metadata
    user_id: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7


class ResearchRequest(BaseModel):
    query: str
    strategy: str = "serp"  # serp, web_scrape, comprehensive


class SummarizeRequest(BaseModel):
    content: str
    max_length: int = 500


class SophiaBackend:
    """
    Main backend application for SOPHIA Intel Dashboard
    """

    def __init__(self):
        self.app = FastAPI(
            title="SOPHIA Intel Backend",
            description="Unified backend for SOPHIA Intel Dashboard with chat, web access, and research",
            version="1.0.0",
        )

        # Initialize services
        self.memory_client = MCPMemoryClient()
        self.web_access = WebAccessService()
        self.notion_service = NotionService()

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
        """Setup all API routes"""

        # Chat endpoints
        @self.app.post("/api/chat")
        async def chat(request: ChatRequest):
            """Handle chat requests with streaming support and memory integration"""
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

        # Research endpoints
        @self.app.post("/api/research")
        async def research(request: ResearchRequest):
            """Perform web research using various strategies"""
            try:
                logger.info(f"Processing research request: {request.query}")

                if request.strategy == "serp":
                    # Use web search
                    results = await self.web_access.search(query=request.query, max_results=10, strategy="auto")

                    return {
                        "query": request.query,
                        "strategy": request.strategy,
                        "results": results,
                        "total_found": len(results),
                    }

                elif request.strategy == "comprehensive":
                    # Combine search and scraping
                    search_results = await self.web_access.search(query=request.query, max_results=5, strategy="auto")

                    # Scrape top results for more content
                    detailed_results = []
                    for result in search_results[:3]:  # Limit to top 3 to avoid rate limits
                        try:
                            scraped = await self.web_access.scrape(
                                url=result["url"], strategy="auto", extract_text=True
                            )

                            result["scraped_content"] = scraped.get("content", "")[:1000]  # Limit content
                            result["scraped_title"] = scraped.get("title", "")

                        except Exception as e:
                            logger.warning(f"Failed to scrape {result['url']}: {e}")
                            result["scraped_content"] = ""
                            result["scraped_title"] = ""

                        detailed_results.append(result)

                    return {
                        "query": request.query,
                        "strategy": request.strategy,
                        "results": detailed_results,
                        "total_found": len(detailed_results),
                    }

                else:
                    raise ValueError(f"Unknown research strategy: {request.strategy}")

            except Exception as e:
                logger.error(f"Research request failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Web access endpoints
        @self.app.post("/api/web/search")
        async def web_search(request: WebSearchRequest):
            """Perform web search"""
            try:
                results = await self.web_access.search(
                    query=request.query, max_results=request.max_results, strategy=request.strategy
                )

                return {"query": request.query, "results": results, "total_found": len(results)}

            except Exception as e:
                logger.error(f"Web search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/web/scrape")
        async def web_scrape(request: WebScrapeRequest):
            """Scrape content from a URL"""
            try:
                result = await self.web_access.scrape(
                    url=request.url,
                    strategy=request.strategy,
                    extract_text=request.extract_text,
                    extract_links=request.extract_links,
                    extract_images=request.extract_images,
                )

                return result

            except Exception as e:
                logger.error(f"Web scraping failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/web/summarize")
        async def web_summarize(request: SummarizeRequest):
            """Summarize content using AI"""
            try:
                # Use the MCP server to summarize content
                summary_prompt = f"Please provide a concise summary of the following content in {request.max_length} characters or less:\\n\\n{request.content}"

                mcp_request = {
                    "prompt": summary_prompt,
                    "session_id": str(uuid.uuid4()),
                    "use_context": False,
                    "stream": False,
                    "metadata": {"source": "web_summarize", "content_length": len(request.content)},
                }

                response = await self._get_chat_response(mcp_request)

                return {
                    "original_length": len(request.content),
                    "summary": response.get("content", ""),
                    "summary_length": len(response.get("content", "")),
                    "compression_ratio": (
                        len(response.get("content", "")) / len(request.content) if request.content else 0
                    ),
                }

            except Exception as e:
                logger.error(f"Summarization failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Notion Integration Endpoints
        @self.app.post("/api/notion/search")
        async def notion_search(request: NotionSearchRequest):
            """Search Notion databases for knowledge"""
            try:
                results = await self.notion_service.search_databases(
                    query=request.query, database_id=request.database_id, max_results=request.max_results
                )

                return {
                    "query": request.query,
                    "results": results,
                    "total_found": len(results),
                    "timestamp": asyncio.get_event_loop().time(),
                }

            except Exception as e:
                logger.error(f"Notion search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/notion/create")
        async def notion_create_page(request: NotionCreatePageRequest):
            """Create a new page in Notion database"""
            try:
                result = await self.notion_service.create_page(
                    database_id=request.database_id,
                    title=request.title,
                    content=request.content,
                    properties=request.properties,
                )

                return {
                    "success": True,
                    "page_id": result.get("id", ""),
                    "url": result.get("url", ""),
                    "created_time": result.get("created_time", ""),
                }

            except Exception as e:
                logger.error(f"Notion page creation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/notion/principles/pending")
        async def get_pending_principles():
            """Get pending canonical principles from Notion"""
            try:
                principles = await self.notion_service.get_pending_principles()

                return {
                    "principles": principles,
                    "total_pending": len(principles),
                    "timestamp": asyncio.get_event_loop().time(),
                }

            except Exception as e:
                logger.error(f"Failed to get pending principles: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/notion/principles/{principle_id}/approve")
        async def approve_principle(principle_id: str):
            """Approve a canonical principle"""
            try:
                result = await self.notion_service.approve_principle(principle_id)

                return {
                    "success": True,
                    "principle_id": principle_id,
                    "updated_time": result.get("last_edited_time", ""),
                }

            except Exception as e:
                logger.error(f"Failed to approve principle: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/chat/save-to-notion")
        async def save_chat_to_notion(request: dict):
            """Save chat conversation or insights to Notion"""
            try:
                title = request.get("title", "Chat Insight")
                content = request.get("content", "")
                session_id = request.get("session_id", "")
                database_id = request.get("database_id") or self.notion_service.knowledge_db_id

                if not content:
                    raise HTTPException(status_code=400, detail="Content is required")

                if not database_id:
                    raise HTTPException(status_code=400, detail="Notion database not configured")

                # Add metadata to content
                enhanced_content = f"{content}\\n\\n---\\n**Source:** SOPHIA Chat\\n**Session ID:** {session_id}\\n**Created:** {asyncio.get_event_loop().time()}"

                result = await self.notion_service.create_page(
                    database_id=database_id,
                    title=title,
                    content=enhanced_content,
                    properties={
                        "Source": {"select": {"name": "SOPHIA Chat"}},
                        "Session ID": {"rich_text": [{"text": {"content": session_id}}]},
                    },
                )

                return {"success": True, "page_id": result.get("id", ""), "url": result.get("url", ""), "title": title}

            except Exception as e:
                logger.error(f"Failed to save chat to Notion: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Chat session management
        @self.app.get("/api/chat/sessions/{session_id}/history")
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

        @self.app.delete("/api/chat/sessions/{session_id}")
        async def clear_chat_session(session_id: str):
            """Clear a chat session"""
            try:
                result = await self.memory_client.clear_session(session_id)
                return {"session_id": session_id, "cleared": True, "deleted_count": result.get("deleted_count", 0)}
            except Exception as e:
                logger.error(f"Failed to clear chat session: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Health check
        @self.app.get("/health")
        async def health():
            """Comprehensive health check"""
            try:
                # Test MCP server connectivity
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{settings.ORCHESTRATOR_URL}/health")
                    mcp_healthy = response.status_code == 200

                # Test memory client
                memory_health = await self.memory_client.health_check()

                # Check web access service configuration
                web_access_status = {
                    "brightdata_configured": bool(self.web_access.brightdata_key),
                    "apify_configured": bool(self.web_access.apify_key),
                    "zenrows_configured": bool(self.web_access.zenrows_key),
                }

                return {
                    "status": "healthy" if mcp_healthy and memory_health.get("status") == "healthy" else "unhealthy",
                    "mcp_server": "healthy" if mcp_healthy else "unhealthy",
                    "memory_client": memory_health.get("status", "unknown"),
                    "web_access": web_access_status,
                    "version": "1.0.0",
                    "endpoints": [
                        "/api/chat",
                        "/api/research",
                        "/api/web/search",
                        "/api/web/scrape",
                        "/api/web/summarize",
                    ],
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
backend = SophiaBackend()
app = backend.app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
