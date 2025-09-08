"""
Sophia AI Chat Service - Real-time WebSocket Communication
Optimized for sophia-intel.ai deployment with neural architecture integration
"""

import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import asyncpg
import httpx
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenTelemetry tracing
OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "http://otel-collector:4318/v1/traces")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "chat-service")
resource = Resource.create({"service.name": SERVICE_NAME})
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_ENDPOINT))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

RedisInstrumentor().instrument()
AsyncPGInstrumentor().instrument()
HTTPXClientInstrumentor().instrument()

# Metrics
WEBSOCKET_CONNECTIONS = Gauge(
    "chat_websocket_connections_total", "Active WebSocket connections"
)
MESSAGE_COUNT = Counter(
    "chat_messages_total", "Total messages processed", ["message_type"]
)
MESSAGE_LATENCY = Histogram(
    "chat_message_latency_seconds", "Message processing latency"
)
NEURAL_REQUESTS = Counter(
    "chat_neural_requests_total", "Neural engine requests", ["status"]
)

# Global state
connection_manager: Optional["ChatConnectionManager"] = None
redis_client: redis.Redis | None = None
db_pool: asyncpg.Pool | None = None
http_client: httpx.AsyncClient | None = None


class ChatMessage(BaseModel):
    """Chat message model"""

    id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4()}")
    session_id: str
    role: str = Field(..., description="user or assistant")
    content: str
    attachments: list[str] | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict | None = None


class ChatSession(BaseModel):
    """Chat session model"""

    id: str = Field(default_factory=lambda: f"session_{uuid.uuid4()}")
    user_id: str
    agent_id: str | None = None
    model: str = "deepseek-r1-0528"
    context_window: int = 128000
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0
    context: list[str] = Field(default_factory=list)


class AgentStatus(BaseModel):
    """Agent status model"""

    status: str = Field(..., description="idle, thinking, responding, error")
    message: str | None = None
    progress: float | None = None


class ChatConnectionManager:
    """Manage WebSocket connections and chat sessions"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.user_sessions: dict[str, str] = {}  # user_id -> session_id
        self.session_connections: dict[str, str] = {}  # session_id -> user_id

    async def connect(self, websocket: WebSocket, user_id: str) -> ChatSession:
        """Accept new WebSocket connection"""
        await websocket.accept()

        # Check for existing session
        existing_session_id = self.user_sessions.get(user_id)
        if existing_session_id:
            session = await self.get_session(existing_session_id)
            if session:
                session.last_activity = datetime.utcnow()
                await self.save_session(session)
            else:
                session = await self.create_session(user_id)
        else:
            session = await self.create_session(user_id)

        # Store connection
        self.active_connections[user_id] = websocket
        self.user_sessions[user_id] = session.id
        self.session_connections[session.id] = user_id

        WEBSOCKET_CONNECTIONS.inc()

        # Send session info
        await self.send_to_user(
            user_id, {"type": "session_created", "data": session.dict()}
        )

        logger.info(f"User {user_id} connected to session {session.id}")
        return session

    async def disconnect(self, user_id: str):
        """Handle disconnection"""
        if user_id in self.active_connections:
            session_id = self.user_sessions.get(user_id)
            if session_id:
                # Update session last activity
                session = await self.get_session(session_id)
                if session:
                    session.last_activity = datetime.utcnow()
                    await self.save_session(session)

                # Clean up mappings
                del self.session_connections[session_id]

            del self.active_connections[user_id]
            del self.user_sessions[user_id]

            WEBSOCKET_CONNECTIONS.dec()
            logger.info(f"User {user_id} disconnected")

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user"""
        websocket = self.active_connections.get(user_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {user_id}: {e}")
                await self.disconnect(user_id)

    async def broadcast_to_session(self, session_id: str, message: dict):
        """Broadcast message to all users in session"""
        user_id = self.session_connections.get(session_id)
        if user_id:
            await self.send_to_user(user_id, message)

    async def create_session(self, user_id: str) -> ChatSession:
        """Create new chat session"""
        session = ChatSession(user_id=user_id)
        await self.save_session(session)
        return session

    async def get_session(self, session_id: str) -> ChatSession | None:
        """Get session from cache or database"""
        # Try Redis cache first
        cached = await redis_client.get(f"session:{session_id}")
        if cached:
            return ChatSession.parse_raw(cached)

        # Fallback to database
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM chat_sessions WHERE id = $1", session_id
            )
            if row:
                session = ChatSession(**dict(row))
                # Cache for future use
                await redis_client.setex(
                    f"session:{session_id}", 3600, session.json()  # 1 hour TTL
                )
                return session

        return None

    async def save_session(self, session: ChatSession):
        """Save session to cache and database"""
        # Update Redis cache
        await redis_client.setex(
            f"session:{session.id}", 3600, session.json()
        )  # 1 hour TTL

        # Update database
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO chat_sessions (
                    id, user_id, agent_id, model, context_window,
                    created_at, last_activity, message_count, context
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO UPDATE SET
                    last_activity = $7,
                    message_count = $8,
                    context = $9
            """,
                session.id,
                session.user_id,
                session.agent_id,
                session.model,
                session.context_window,
                session.created_at,
                session.last_activity,
                session.message_count,
                json.dumps(session.context),
            )

    async def save_message(self, message: ChatMessage):
        """Save message to database"""
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO chat_messages (
                    id, session_id, role, content, attachments,
                    timestamp, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                message.id,
                message.session_id,
                message.role,
                message.content,
                json.dumps(message.attachments) if message.attachments else None,
                message.timestamp,
                json.dumps(message.metadata) if message.metadata else None,
            )

    async def process_user_message(self, user_id: str, message_data: dict):
        """Process incoming user message"""
        session_id = self.user_sessions.get(user_id)
        if not session_id:
            await self.send_to_user(
                user_id, {"type": "error", "data": {"message": "No active session"}}
            )
            return

        session = await self.get_session(session_id)
        if not session:
            await self.send_to_user(
                user_id, {"type": "error", "data": {"message": "Session not found"}}
            )
            return

        # Create user message
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=message_data.get("content", ""),
            attachments=message_data.get("attachments"),
            metadata=message_data.get("metadata"),
        )

        # Save user message
        await self.save_message(user_message)
        MESSAGE_COUNT.labels(message_type="user").inc()

        # Update session
        session.message_count += 1
        session.last_activity = datetime.utcnow()
        session.context.append(f"User: {user_message.content}")

        # Trim context if too long
        if len(session.context) > 20:
            session.context = session.context[-20:]

        await self.save_session(session)

        # Send status update
        await self.send_to_user(
            user_id,
            {
                "type": "agent_status",
                "data": {"status": "thinking", "message": "Processing your request..."},
            },
        )

        # Process with neural engine
        await self.process_with_neural_engine(
            user_id, session, user_message, message_data
        )

    async def process_with_neural_engine(
        self,
        user_id: str,
        session: ChatSession,
        user_message: ChatMessage,
        message_data: dict,
    ):
        """Process message with neural engine"""
        try:
            # Prepare neural engine request
            neural_request = {
                "query": user_message.content,
                "context": session.context[-10:],  # Last 10 context items
                "max_tokens": message_data.get("max_tokens", 4096),
                "temperature": message_data.get("temperature", 0.6),
                "stream": message_data.get("stream", True),
                "reasoning_depth": message_data.get("reasoning_depth", 5),
            }

            # Send to neural gateway
            neural_url = "http://neural-gateway:8000/api/v1/inference"

            if neural_request["stream"]:
                await self.process_streaming_response(
                    user_id, session, neural_url, neural_request
                )
            else:
                await self.process_single_response(
                    user_id, session, neural_url, neural_request
                )

        except Exception as e:
            logger.error(f"Neural processing error: {e}")
            NEURAL_REQUESTS.labels(status="error").inc()

            await self.send_to_user(
                user_id,
                {
                    "type": "agent_status",
                    "data": {"status": "error", "message": f"Processing error: {e!s}"},
                },
            )

    async def process_streaming_response(
        self, user_id: str, session: ChatSession, url: str, request_data: dict
    ):
        """Process streaming response from neural engine"""
        try:
            async with http_client.stream("POST", url, json=request_data) as response:
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code, detail="Neural engine error"
                    )

                # Send status update
                await self.send_to_user(
                    user_id,
                    {
                        "type": "agent_status",
                        "data": {
                            "status": "responding",
                            "message": "Generating response...",
                        },
                    },
                )

                full_response = ""
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        # Send chunk to user
                        await self.send_to_user(
                            user_id, {"type": "stream_chunk", "data": {"chunk": chunk}}
                        )
                        full_response += chunk

                # Create assistant message
                assistant_message = ChatMessage(
                    session_id=session.id,
                    role="assistant",
                    content=full_response,
                    metadata={"model": session.model, "streaming": True},
                )

                # Save assistant message
                await self.save_message(assistant_message)
                MESSAGE_COUNT.labels(message_type="assistant").inc()

                # Update session
                session.message_count += 1
                session.context.append(f"Assistant: {full_response}")
                await self.save_session(session)

                # Send completion status
                await self.send_to_user(
                    user_id,
                    {
                        "type": "agent_status",
                        "data": {"status": "idle", "message": "Response complete"},
                    },
                )

                NEURAL_REQUESTS.labels(status="success").inc()

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            NEURAL_REQUESTS.labels(status="error").inc()

            await self.send_to_user(
                user_id,
                {
                    "type": "agent_status",
                    "data": {"status": "error", "message": f"Streaming error: {e!s}"},
                },
            )

    async def process_single_response(
        self, user_id: str, session: ChatSession, url: str, request_data: dict
    ):
        """Process single response from neural engine"""
        try:
            response = await http_client.post(url, json=request_data)
            response.raise_for_status()

            result = response.json()

            # Create assistant message
            assistant_message = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=result.get("response", ""),
                metadata={
                    "model": session.model,
                    "latency_ms": result.get("latency_ms"),
                    "tokens_used": result.get("tokens_used"),
                    "confidence": result.get("confidence"),
                },
            )

            # Save assistant message
            await self.save_message(assistant_message)
            MESSAGE_COUNT.labels(message_type="assistant").inc()

            # Update session
            session.message_count += 1
            session.context.append(f"Assistant: {assistant_message.content}")
            await self.save_session(session)

            # Send response to user
            await self.send_to_user(
                user_id, {"type": "message", "data": assistant_message.dict()}
            )

            # Send completion status
            await self.send_to_user(
                user_id,
                {
                    "type": "agent_status",
                    "data": {"status": "idle", "message": "Response complete"},
                },
            )

            NEURAL_REQUESTS.labels(status="success").inc()

        except Exception as e:
            logger.error(f"Single response error: {e}")
            NEURAL_REQUESTS.labels(status="error").inc()

            await self.send_to_user(
                user_id,
                {
                    "type": "agent_status",
                    "data": {"status": "error", "message": f"Response error: {e!s}"},
                },
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global connection_manager, redis_client, db_pool, http_client

    # Initialize Redis
    redis_client = redis.from_url("redis://redis-cluster:6379")

    # Initialize database pool
    db_pool = await asyncpg.create_pool(
        "postgresql://sophia:${POSTGRES_PASSWORD}@postgres-main:5432/sophia_ai",
        min_size=5,
        max_size=20,
    )

    # Initialize HTTP client
    http_client = httpx.AsyncClient(timeout=30.0)

    # Initialize connection manager
    connection_manager = ChatConnectionManager()

    logger.info("Chat service initialized")

    yield

    # Cleanup
    await redis_client.close()
    await db_pool.close()
    await http_client.aclose()

    logger.info("Chat service shutdown")


# FastAPI app
app = FastAPI(
    title="Sophia AI Chat Service",
    description="Real-time WebSocket chat service for sophia-intel.ai",
    version="1.0.0",
    lifespan=lifespan,
)

FastAPIInstrumentor.instrument_app(app)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.sophia-intel.ai",
        "https://chat.sophia-intel.ai",
        "https://dashboard.sophia-intel.ai",
        "${SOPHIA_FRONTEND_ENDPOINT}",  # Development
        "http://localhost:3001",  # Development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "chat-service",
        "timestamp": datetime.utcnow().isoformat(),
        "active_connections": (
            len(connection_manager.active_connections) if connection_manager else 0
        ),
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time chat"""
    session = await connection_manager.connect(websocket, user_id)

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            # Process based on message type
            message_type = data.get("type")

            if message_type == "send_message":
                await connection_manager.process_user_message(
                    user_id, data.get("data", {})
                )
            elif message_type == "ping":
                await connection_manager.send_to_user(
                    user_id, {"type": "pong", "data": {}}
                )
            else:
                logger.warning(f"Unknown message type: {message_type}")

    except WebSocketDisconnect:
        await connection_manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        await connection_manager.disconnect(user_id)


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    session = await connection_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, limit: int = 50, offset: int = 0):
    """Get session messages"""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM chat_messages 
            WHERE session_id = $1 
            ORDER BY timestamp DESC 
            LIMIT $2 OFFSET $3
        """,
            session_id,
            limit,
            offset,
        )

        messages = [ChatMessage(**dict(row)) for row in rows]
        return {"messages": messages, "total": len(messages)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="${BIND_IP}", port=8002)
