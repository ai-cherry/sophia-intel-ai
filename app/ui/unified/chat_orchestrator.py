"""
Backend Chat Orchestrator with WebSocket Support
Provides real-time streaming chat interface for AI Orchestra
Integrates with SmartCommandDispatcher and UnifiedOrchestratorFacade
"""

import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.agents.orchestra_manager import (
    ManagerIntegration,
    OrchestraManager,
)
from app.api.contracts import (
    APIContractFactory,
    BackwardCompatibilityAdapter,
    ChatRequestV1,
    ChatRequestV2,
    ChatResponseV1,
    ChatResponseV2,
    RequestValidationMiddleware,
    StreamTokenV1,
    WebSocketMessage,
    WebSocketMessageType,
)
from app.nl_interface.command_dispatcher import (
    ExecutionResult,
    SmartCommandDispatcher,
)
from app.orchestration.unified_facade import (
    OptimizationMode,
    SwarmType,
    UnifiedOrchestratorFacade,
)

logger = logging.getLogger(__name__)

@dataclass
class ConnectionState:
    """State for WebSocket connections"""
    client_id: str
    session_id: str
    websocket: WebSocket
    connected: bool = True
    last_activity: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

# ==================== Error Boundaries and Circuit Breakers ====================

class WebSocketErrorBoundary:
    """Error boundary for WebSocket handlers"""

    def __init__(self, connection_state: 'ConnectionState', fallback_message: str = "An error occurred"):
        self.connection = connection_state
        self.fallback_message = fallback_message
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(f"WebSocket error caught: {exc_val}", exc_info=True)
            try:
                await self.connection.websocket.send_json({
                    "type": "error",
                    "error": self.fallback_message,
                    "details": str(exc_val) if self.logger.level <= logging.DEBUG else None
                })
            except:
                pass  # Best effort - connection might be closed
            return True  # Suppress exception

class CircuitBreaker:
    """Circuit breaker for external service calls"""

    def __init__(self, name: str, failure_threshold: int = 5, timeout_seconds: int = 60, half_open_requests: int = 1):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.half_open_requests = half_open_requests

        self.failures = 0
        self.last_failure_time: datetime | None = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.half_open_attempts = 0
        self.success_count = 0
        self.total_calls = 0

        self.logger = logging.getLogger(f"CircuitBreaker.{name}")

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        self.total_calls += 1

        # Check if circuit should be reset
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                self.half_open_attempts = 0
                self.logger.info(f"Circuit {self.name} entering HALF_OPEN state")
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN")

        # Check half-open limit
        if self.state == "HALF_OPEN":
            if self.half_open_attempts >= self.half_open_requests:
                raise Exception(f"Circuit breaker {self.name} half-open limit reached")
            self.half_open_attempts += 1

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True
        return (datetime.utcnow() - self.last_failure_time).seconds >= self.timeout_seconds

    def _on_success(self):
        """Handle successful call"""
        self.success_count += 1
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failures = 0
            self.logger.info(f"Circuit {self.name} closed after successful half-open test")
        elif self.state == "CLOSED":
            self.failures = 0  # Reset failure count on success

    def _on_failure(self):
        """Handle failed call"""
        self.failures += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == "HALF_OPEN":
            self.state = "OPEN"
            self.logger.warning(f"Circuit {self.name} reopened after half-open failure")
        elif self.failures >= self.failure_threshold:
            self.state = "OPEN"
            self.logger.warning(f"Circuit {self.name} opened after {self.failures} failures")

    def get_state(self) -> dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state,
            "failures": self.failures,
            "success_count": self.success_count,
            "total_calls": self.total_calls,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }

class ConnectionTimeoutManager:
    """Manages connection timeouts and cleanup"""

    def __init__(self, idle_timeout_seconds: int = 300, check_interval_seconds: int = 30):
        self.idle_timeout = timedelta(seconds=idle_timeout_seconds)
        self.check_interval = check_interval_seconds
        self.connections: dict[str, ConnectionState] = {}
        self._cleanup_task: asyncio.Task | None = None
        self.logger = logging.getLogger(__name__)

    def add_connection(self, key: str, connection: ConnectionState):
        """Add connection to be monitored"""
        self.connections[key] = connection
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    def remove_connection(self, key: str):
        """Remove connection from monitoring"""
        self.connections.pop(key, None)
        if not self.connections and self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None

    async def _cleanup_loop(self):
        """Periodic cleanup of idle connections"""
        while self.connections:
            try:
                await asyncio.sleep(self.check_interval)
                await self._check_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")

    async def _check_connections(self):
        """Check and cleanup idle connections"""
        now = datetime.utcnow()
        to_remove = []

        for key, conn in list(self.connections.items()):
            idle_time = now - conn.last_activity

            if idle_time > self.idle_timeout:
                self.logger.info(f"Closing idle connection {key} (idle for {idle_time.seconds}s)")
                to_remove.append(key)

                try:
                    await conn.websocket.send_json({
                        "type": "timeout",
                        "message": "Connection closed due to inactivity"
                    })
                    await conn.websocket.close()
                except:
                    pass  # Best effort
            elif idle_time > self.idle_timeout / 2:
                # Send ping to keep connection alive
                try:
                    await conn.websocket.send_json({"type": "ping"})
                except:
                    to_remove.append(key)

        for key in to_remove:
            self.remove_connection(key)

# ==================== Chat Orchestrator ====================

class ChatOrchestrator:
    """
    Main chat orchestration engine with WebSocket support
    Coordinates between NL processing, swarm execution, and streaming
    """

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        redis_url: str = "redis://localhost:6379",
        mcp_server_url: str = "http://localhost:8004",
        n8n_url: str = "http://localhost:5678"
    ):
        """Initialize chat orchestrator"""
        # Core components
        self.command_dispatcher = SmartCommandDispatcher(
            ollama_url=ollama_url,
            redis_url=redis_url,
            mcp_server_url=mcp_server_url,
            n8n_url=n8n_url
        )

        self.unified_orchestrator = UnifiedOrchestratorFacade()

        # Initialize Orchestra Manager
        self.orchestra_manager = OrchestraManager(name="Maestro")
        self.manager_integration = ManagerIntegration(self.orchestra_manager)

        # Connection management (will be injected)
        self.connection_pool: WebSocketConnectionPool | None = None
        self.session_manager: SessionStateManager | None = None

        # Local connection tracking
        self.active_connections: dict[str, ConnectionState] = {}
        self.session_history: dict[str, list[dict]] = {}

        # Performance tracking
        self.metrics = {
            "total_messages": 0,
            "active_connections": 0,
            "avg_response_time": 0.0,
            "total_response_time": 0.0,
            "errors": 0
        }

        # Circuit breakers for each component
        self.circuit_breakers = {
            "dispatcher": CircuitBreaker("dispatcher", failure_threshold=3, timeout_seconds=30),
            "orchestrator": CircuitBreaker("orchestrator", failure_threshold=3, timeout_seconds=60),
            "manager": CircuitBreaker("manager", failure_threshold=5, timeout_seconds=20),
            "memory": CircuitBreaker("memory", failure_threshold=3, timeout_seconds=30)
        }

        # Connection timeout manager
        self.timeout_manager = ConnectionTimeoutManager(
            idle_timeout_seconds=300,  # 5 minutes
            check_interval_seconds=30
        )

        # API contract support
        self.contract_factory = APIContractFactory()
        self.compatibility_adapter = BackwardCompatibilityAdapter()
        self.validation_middleware = RequestValidationMiddleware()

        # Initialize flag
        self.initialized = False

        logger.info("ChatOrchestrator created with error boundaries and circuit breakers")

    async def initialize(self):
        """Initialize async components"""
        if self.initialized:
            return

        logger.info("Initializing ChatOrchestrator components")

        # Initialize unified orchestrator
        await self.unified_orchestrator.initialize()

        self.initialized = True
        logger.info("ChatOrchestrator initialized successfully")

    async def handle_chat(self, request: Union[ChatRequestV1, ChatRequestV2]) -> Union[ChatResponseV1, ChatResponseV2]:
        """
        Handle REST chat request
        
        Args:
            request: Chat request from client
            
        Returns:
            ChatResponse with execution results
        """
        start_time = time.time()
        self.metrics["total_messages"] += 1

        try:
            # Prepare manager context
            history = self.session_history.get(request.session_id, [])
            system_state = await self._get_system_state()
            manager_context = self.manager_integration.prepare_context(
                session_id=request.session_id,
                conversation_history=history,
                system_state=system_state
            )

            # Process through manager for intent and initial response with circuit breaker
            manager_result = await self.circuit_breakers["manager"].call(
                lambda: self.manager_integration.process_message(
                    request.message,
                    manager_context
                )
            )

            # Add manager's initial response to metadata
            request.user_context["manager_response"] = manager_result["response"]
            request.user_context["detected_intent"] = manager_result["intent"]
            request.user_context["confidence"] = manager_result["confidence"]

            # Process through command dispatcher with circuit breaker
            result = await self.circuit_breakers["dispatcher"].call(
                self.command_dispatcher.process_command,
                text=request.message,
                session_id=request.session_id,
                user_context=request.user_context
            )

            # Generate manager's result response
            final_response = self.manager_integration.process_result(
                intent=manager_result["intent"],
                parameters=manager_result["parameters"],
                result={
                    "success": result.success,
                    "quality_score": result.quality_score,
                    "execution_time": result.execution_time,
                    "response": result.response
                },
                context=manager_context
            )

            # Update session history
            self._update_session_history(
                request.session_id,
                request.message,
                result
            )

            # Update metrics
            execution_time = time.time() - start_time
            self._update_metrics(execution_time)

            # Create response data
            response_data = {
                "session_id": request.session_id,
                "response": result.response,
                "execution_mode": result.execution_mode.value,
                "execution_time": execution_time,
                "quality_score": result.quality_score,
                "success": result.success,
                "error": result.error,
                "metadata": {
                    **result.metadata,
                    "intent": manager_result["intent"],
                    "confidence": manager_result["confidence"]
                }
            }

            # Add V2-specific fields if applicable
            if isinstance(request, ChatRequestV2):
                response_data["manager_response"] = final_response
                response_data["intent"] = manager_result["intent"]
                response_data["confidence"] = manager_result["confidence"]

            # Create versioned response
            return await self.validation_middleware.validate_response(request, response_data)

        except Exception as e:
            logger.error(f"Chat handling failed: {e}")
            self.metrics["errors"] += 1

            # Create error response
            error_data = {
                "session_id": request.session_id,
                "response": None,
                "execution_mode": "lite",
                "execution_time": time.time() - start_time,
                "quality_score": 0.0,
                "success": False,
                "error": str(e)
            }

            return await self.validation_middleware.validate_response(request, error_data)

    async def websocket_endpoint(
        self,
        websocket: WebSocket,
        client_id: str,
        session_id: str
    ):
        """
        WebSocket endpoint for real-time streaming
        
        Args:
            websocket: WebSocket connection
            client_id: Client identifier
            session_id: Session identifier
        """
        await websocket.accept()

        # Create connection state
        connection = ConnectionState(
            client_id=client_id,
            session_id=session_id,
            websocket=websocket
        )

        # Register connection
        connection_key = f"{client_id}:{session_id}"

        # Check connection pool if available
        if self.connection_pool:
            if not await self.connection_pool.acquire_connection(connection_key, connection):
                await websocket.send_json({
                    "type": "error",
                    "error": "Connection limit reached. Please try again later."
                })
                await websocket.close()
                return

        self.active_connections[connection_key] = connection
        self.metrics["active_connections"] += 1

        # Add to timeout manager
        self.timeout_manager.add_connection(connection_key, connection)

        logger.info(f"WebSocket connected: {connection_key}")

        # Send initial status
        await self._send_status(connection, "connected")

        try:
            while connection.connected:
                # Receive message
                raw_message = await websocket.receive_text()
                connection.last_activity = datetime.utcnow()
                connection.message_count += 1

                # Parse and handle message with error boundary
                async with WebSocketErrorBoundary(connection, "Failed to process message"):
                    try:
                        # Parse as WebSocketMessage
                        message = WebSocketMessage(**json.loads(raw_message))
                    except:
                        # Fallback to raw dict for backward compatibility
                        message = WebSocketMessage(
                            type=WebSocketMessageType.CHAT,
                            data=json.loads(raw_message)
                        )
                    await self._handle_websocket_message(connection, message)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_key}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Clean up connection
            connection.connected = False

            if connection_key in self.active_connections:
                del self.active_connections[connection_key]
                self.metrics["active_connections"] -= 1

            # Release from connection pool if available
            if self.connection_pool:
                await self.connection_pool.release_connection(connection_key)

            # Remove from timeout manager
            self.timeout_manager.remove_connection(connection_key)

    async def _handle_websocket_message(
        self,
        connection: ConnectionState,
        message: WebSocketMessage
    ):
        """
        Handle incoming WebSocket message
        
        Args:
            connection: Connection state
            message: Parsed WebSocket message
        """
        msg_type = message.type if isinstance(message.type, str) else message.type.value

        if msg_type == WebSocketMessageType.CHAT.value:
            await self._handle_chat_message(connection, message.data)
        elif msg_type == WebSocketMessageType.COMMAND.value:
            await self._handle_command_message(connection, message.data)
        elif msg_type == WebSocketMessageType.CONTROL.value:
            await self._handle_control_message(connection, message.data)
        else:
            await self._send_error(connection, f"Unknown message type: {msg_type}")

    async def _handle_chat_message(
        self,
        connection: ConnectionState,
        data: dict[str, Any]
    ):
        """
        Handle chat message with streaming response
        
        Args:
            connection: Connection state
            data: Message data
        """
        start_time = time.time()

        # Extract message and context
        message_text = data.get("message", "")
        user_context = data.get("context", {})
        swarm_type = data.get("swarm_type")
        optimization_mode = data.get("optimization_mode", "balanced")

        # Prepare manager context
        history = self.session_history.get(connection.session_id, [])
        system_state = await self._get_system_state()
        manager_context = self.manager_integration.prepare_context(
            session_id=connection.session_id,
            conversation_history=history,
            system_state=system_state
        )

        # Get manager's interpretation with error boundary
        try:
            manager_result = await self.circuit_breakers["manager"].call(
                lambda: self.manager_integration.process_message(
                    message_text,
                    manager_context
                )
            )
        except Exception as e:
            logger.error(f"Manager interpretation failed: {e}")
            # Fallback response
            manager_result = {
                "intent": "unknown",
                "parameters": {},
                "confidence": 0.0,
                "response": "I'm having trouble understanding. Let me try to help anyway."
            }

        # Send manager's initial response
        await self._send_token(connection, StreamTokenV1(
            type="manager",
            content=manager_result["response"],
            metadata={
                "intent": manager_result["intent"],
                "confidence": manager_result["confidence"]
            }
        ))

        # Send processing status
        await self._send_status(connection, "processing")

        try:
            # Add manager context to user context
            user_context["manager_intent"] = manager_result["intent"]
            user_context["manager_confidence"] = manager_result["confidence"]

            # Stream tokens as they're generated
            async for token in self.stream_tokens(
                message=message_text,
                session_id=connection.session_id,
                user_context=user_context,
                swarm_type=swarm_type,
                optimization_mode=optimization_mode
            ):
                await self._send_token(connection, token)

            # Generate manager's final response
            final_response = self.manager_integration.process_result(
                intent=manager_result["intent"],
                parameters=manager_result["parameters"],
                result={
                    "success": True,
                    "execution_time": time.time() - start_time
                },
                context=manager_context
            )

            # Send manager's conclusion
            await self._send_token(connection, StreamTokenV1(
                type="manager_conclusion",
                content=final_response,
                metadata={"manager": self.orchestra_manager.name}
            ))

            # Send completion status
            execution_time = time.time() - start_time
            await self._send_status(connection, "completed", {
                "execution_time": execution_time
            })

            # Update metrics
            self._update_metrics(execution_time)

        except Exception as e:
            logger.error(f"Chat message processing failed: {e}")
            await self._send_error(connection, str(e))
            self.metrics["errors"] += 1

    async def _handle_command_message(
        self,
        connection: ConnectionState,
        data: dict[str, Any]
    ):
        """
        Handle command message (direct dispatcher commands)
        
        Args:
            connection: Connection state
            data: Command data
        """
        command = data.get("command", "")

        # Process command through dispatcher
        result = await self.command_dispatcher.process_command(
            text=command,
            session_id=connection.session_id,
            user_context=data.get("context", {})
        )

        # Send result
        await self._send_message(connection, {
            "type": "command_result",
            "result": asdict(result) if hasattr(result, "__dict__") else result
        })

    async def _handle_control_message(
        self,
        connection: ConnectionState,
        data: dict[str, Any]
    ):
        """
        Handle control messages (ping, status, etc.)
        
        Args:
            connection: Connection state
            data: Control data
        """
        control_type = data.get("type", "")

        if control_type == "ping":
            await self._send_message(connection, {"type": "pong"})
        elif control_type == "status":
            await self._send_status(connection, "active", {
                "message_count": connection.message_count,
                "session_id": connection.session_id,
                "uptime": (datetime.utcnow() - connection.last_activity).total_seconds()
            })
        elif control_type == "metrics":
            await self._send_message(connection, {
                "type": "metrics",
                "data": await self.get_metrics()
            })
        else:
            await self._send_error(connection, f"Unknown control type: {control_type}")

    async def stream_tokens(
        self,
        message: str,
        session_id: str,
        user_context: dict[str, Any] | None = None,
        swarm_type: str | None = None,
        optimization_mode: str = "balanced"
    ) -> AsyncGenerator[StreamTokenV1, None]:
        """
        Stream tokens for a message
        
        Args:
            message: Input message
            session_id: Session ID
            user_context: User context
            swarm_type: Optional swarm type to use
            optimization_mode: Optimization mode
            
        Yields:
            StreamToken objects
        """
        # Determine if we need swarm processing
        if swarm_type:
            # Use swarm orchestrator
            async for token in self._stream_swarm_tokens(
                message,
                session_id,
                swarm_type,
                optimization_mode,
                user_context
            ):
                yield token
        else:
            # Use command dispatcher
            async for token in self._stream_command_tokens(
                message,
                session_id,
                user_context
            ):
                yield token

    async def _stream_command_tokens(
        self,
        message: str,
        session_id: str,
        user_context: dict[str, Any] | None = None
    ) -> AsyncGenerator[StreamTokenV1, None]:
        """
        Stream tokens through command dispatcher
        
        Args:
            message: Input message
            session_id: Session ID
            user_context: User context
            
        Yields:
            StreamToken objects
        """
        # Process command
        result = await self.command_dispatcher.process_command(
            text=message,
            session_id=session_id,
            user_context=user_context or {}
        )

        # Convert result to tokens
        if result.success:
            response_text = json.dumps(result.response) if isinstance(result.response, dict) else str(result.response)

            # Simulate token streaming (in real implementation, this would come from LLM)
            words = response_text.split()
            for i, word in enumerate(words):
                yield StreamTokenV1(
                    type="token",
                    content=word + " ",
                    metadata={
                        "index": i,
                        "total": len(words)
                    }
                )
                # Small delay to simulate streaming
                await asyncio.sleep(0.01)

            # Send completion token
            yield StreamTokenV1(
                type="complete",
                metadata={
                    "execution_mode": result.execution_mode.value,
                    "quality_score": result.quality_score,
                    "execution_time": result.execution_time
                }
            )
        else:
            # Send error token
            yield StreamTokenV1(
                type="error",
                content=result.error,
                metadata={"execution_mode": result.execution_mode.value}
            )

    async def _stream_swarm_tokens(
        self,
        message: str,
        session_id: str,
        swarm_type: str,
        optimization_mode: str,
        user_context: dict[str, Any] | None = None
    ) -> AsyncGenerator[StreamTokenV1, None]:
        """
        Stream tokens through swarm orchestrator
        
        Args:
            message: Input message
            session_id: Session ID
            swarm_type: Type of swarm to use
            optimization_mode: Optimization mode
            user_context: User context
            
        Yields:
            StreamToken objects
        """
        # Create swarm request
        from app.orchestration.unified_facade import SwarmRequest as FacadeSwarmRequest
        request = FacadeSwarmRequest(
            swarm_type=SwarmType(swarm_type),
            task=message,
            mode=OptimizationMode(optimization_mode),
            session_id=session_id,
            stream=True,
            metadata=user_context
        )

        # Stream events from swarm
        async for event in self.unified_orchestrator.execute(request):
            if event.event_type == "started":
                yield StreamTokenV1(
                    type="status",
                    content="Swarm execution started",
                    metadata=event.data
                )
            elif event.event_type == "step":
                # Convert step data to tokens
                step_text = event.data.get("text", "")
                for word in step_text.split():
                    yield StreamTokenV1(
                        type="token",
                        content=word + " ",
                        metadata={"swarm": event.swarm}
                    )
                    await asyncio.sleep(0.01)
            elif event.event_type == "completed":
                yield StreamTokenV1(
                    type="complete",
                    metadata={
                        "swarm": event.swarm,
                        "duration": event.data.get("duration"),
                        "mode": event.data.get("mode")
                    }
                )
            elif event.event_type == "error":
                yield StreamTokenV1(
                    type="error",
                    content=event.data.get("error"),
                    metadata={"swarm": event.swarm}
                )

    async def process_command(
        self,
        command: str,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process a command directly
        
        Args:
            command: Command text
            context: Command context
            
        Returns:
            Command result
        """
        result = await self.command_dispatcher.process_command(
            text=command,
            session_id=context.get("session_id", "default"),
            user_context=context
        )

        return {
            "success": result.success,
            "response": result.response,
            "execution_mode": result.execution_mode.value,
            "quality_score": result.quality_score,
            "error": result.error
        }

    # ==================== Helper Methods ====================

    async def _send_message(
        self,
        connection: ConnectionState,
        message: dict[str, Any]
    ):
        """Send message to WebSocket connection"""
        if connection.connected:
            try:
                await connection.websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                connection.connected = False

    async def _send_token(
        self,
        connection: ConnectionState,
        token: StreamTokenV1
    ):
        """Send streaming token to connection"""
        await self._send_message(connection, {
            "type": "stream_token",
            "data": token.dict()
        })

    async def _send_status(
        self,
        connection: ConnectionState,
        status: str,
        metadata: dict[str, Any] | None = None
    ):
        """Send status update to connection"""
        await self._send_message(connection, {
            "type": "status",
            "status": status,
            "metadata": metadata or {}
        })

    async def _send_error(
        self,
        connection: ConnectionState,
        error: str
    ):
        """Send error message to connection"""
        await self._send_message(connection, {
            "type": "error",
            "error": error
        })

    def _update_session_history(
        self,
        session_id: str,
        message: str,
        result: ExecutionResult
    ):
        """Update session history"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "result": {
                "success": result.success,
                "execution_mode": result.execution_mode.value,
                "quality_score": result.quality_score,
                "execution_time": result.execution_time
            }
        }

        # Use session manager if available
        if self.session_manager:
            # Fire and forget - don't await to avoid blocking
            asyncio.create_task(
                self.session_manager.add_to_history(session_id, entry)
            )
        else:
            # Fallback to local storage
            if session_id not in self.session_history:
                self.session_history[session_id] = []

            self.session_history[session_id].append(entry)

            # Keep only last 100 messages per session
            if len(self.session_history[session_id]) > 100:
                self.session_history[session_id] = self.session_history[session_id][-100:]

    def _update_metrics(self, execution_time: float):
        """Update performance metrics"""
        self.metrics["total_response_time"] += execution_time
        self.metrics["avg_response_time"] = (
            self.metrics["total_response_time"] / self.metrics["total_messages"]
        )

    async def get_metrics(self) -> dict[str, Any]:
        """Get current metrics"""
        dispatcher_metrics = self.command_dispatcher._get_performance_metrics()
        orchestrator_metrics = await self.unified_orchestrator.get_metrics()

        return {
            "chat_orchestrator": self.metrics,
            "command_dispatcher": dispatcher_metrics,
            "unified_orchestrator": orchestrator_metrics,
            "orchestra_manager": self.orchestra_manager.get_status(),
            "circuit_breakers": {
                name: cb.get_state() for name, cb in self.circuit_breakers.items()
            },
            "connection_pool": self.connection_pool.get_metrics() if self.connection_pool else None,
            "active_sessions": len(self.session_history),
            "total_history_entries": sum(len(h) for h in self.session_history.values()),
            "active_connections": len(self.active_connections)
        }

    async def _get_system_state(self, include_metrics: bool = False) -> dict[str, Any]:
        """Get current system state for manager context"""
        base_state = {
            "health": self._calculate_health(),
            "active_connections": self.metrics["active_connections"],
            "avg_response_time": self.metrics["avg_response_time"],
            "components": self._get_component_status()
        }

        if include_metrics:
            base_state["detailed_metrics"] = await self.get_metrics()

        return base_state

    def _calculate_health(self) -> float:
        """Calculate system health score"""
        total = max(1, self.metrics.get("total_messages", 1))
        errors = self.metrics.get("errors", 0)
        return 1.0 - (errors / total)

    def _get_component_status(self) -> dict[str, str]:
        """Get status of each component"""
        return {
            "dispatcher": "available" if self.command_dispatcher else "unavailable",
            "orchestrator": "available" if self.unified_orchestrator else "unavailable",
            "manager": "available" if self.orchestra_manager else "unavailable"
        }

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down ChatOrchestrator")

        # Close all WebSocket connections
        for connection in self.active_connections.values():
            await self._send_status(connection, "shutdown")
            await connection.websocket.close()

        # Shutdown components
        await self.command_dispatcher.shutdown()

        # Cancel timeout manager
        if self.timeout_manager._cleanup_task:
            self.timeout_manager._cleanup_task.cancel()

        logger.info("ChatOrchestrator shutdown complete")

# ==================== FastAPI Router with Dependency Injection ====================

from app.infrastructure.dependency_injection import (
    ServiceConfig,
    SessionStateManager,
    WebSocketConnectionPool,
    initialize_container,
)

# Create router
router = APIRouter(prefix="/chat", tags=["chat"])

# DI Container reference
_di_container = None

@asynccontextmanager
async def lifespan(app):
    """Manage application lifecycle with DI"""
    global _di_container

    # Initialize DI container
    config = ServiceConfig.from_env()
    _di_container = await initialize_container(config)

    # Get and initialize orchestrator
    orchestrator = await _di_container.resolve(ChatOrchestrator)

    logger.info("Application started with dependency injection")

    yield

    # Cleanup
    if _di_container:
        await _di_container.dispose()

    logger.info("Application shutdown complete")

async def get_orchestrator() -> ChatOrchestrator:
    """Dependency to get orchestrator instance from DI container"""
    global _di_container
    if not _di_container:
        # Fallback initialization if not in lifespan context
        config = ServiceConfig.from_env()
        _di_container = await initialize_container(config)

    return await _di_container.resolve(ChatOrchestrator)

async def get_connection_pool() -> WebSocketConnectionPool:
    """Get connection pool from DI container"""
    global _di_container
    if not _di_container:
        config = ServiceConfig.from_env()
        _di_container = await initialize_container(config)

    return await _di_container.resolve(WebSocketConnectionPool)

async def get_session_manager() -> SessionStateManager:
    """Get session manager from DI container"""
    global _di_container
    if not _di_container:
        config = ServiceConfig.from_env()
        _di_container = await initialize_container(config)

    return await _di_container.resolve(SessionStateManager)

# ==================== REST Endpoints ====================

@router.post("/v1/chat", response_model=ChatResponseV1)
async def chat_v1(
    request: ChatRequestV1,
    orchestrator: ChatOrchestrator = Depends(get_orchestrator)
) -> ChatResponseV1:
    """
    Process chat message via REST API (V1)
    
    Args:
        request: Chat request V1
        orchestrator: Chat orchestrator instance
        
    Returns:
        Chat response V1 with execution results
    """
    return await orchestrator.handle_chat(request)

@router.post("/v2/chat", response_model=ChatResponseV2)
async def chat_v2(
    request: ChatRequestV2,
    orchestrator: ChatOrchestrator = Depends(get_orchestrator)
) -> ChatResponseV2:
    """
    Process chat message via REST API (V2)
    
    Args:
        request: Chat request V2
        orchestrator: Chat orchestrator instance
        
    Returns:
        Chat response V2 with execution results
    """
    return await orchestrator.handle_chat(request)

@router.post("/chat")
async def chat(
    request: dict[str, Any],
    orchestrator: ChatOrchestrator = Depends(get_orchestrator)
):
    """
    Process chat message via REST API (auto-version detection)
    
    Args:
        request: Raw chat request
        orchestrator: Chat orchestrator instance
        
    Returns:
        Chat response with execution results
    """
    # Use validation middleware to parse versioned request
    validation_middleware = RequestValidationMiddleware()
    validated_request = await validation_middleware.validate_request(request)

    # Process and return versioned response
    response = await orchestrator.handle_chat(validated_request)
    return response.dict()

@router.post("/stream")
async def chat_stream(
    request: dict[str, Any],
    orchestrator: ChatOrchestrator = Depends(get_orchestrator)
):
    """
    Stream chat response
    
    Args:
        request: Chat request
        orchestrator: Chat orchestrator instance
        
    Returns:
        Streaming response with tokens
    """
    # Parse request
    validation_middleware = RequestValidationMiddleware()
    validated_request = await validation_middleware.validate_request(request)

    async def generate():
        # Extract fields based on version
        swarm_type = None
        optimization_mode = "balanced"

        if isinstance(validated_request, ChatRequestV2):
            swarm_type = validated_request.swarm_type
            optimization_mode = validated_request.optimization_mode or "balanced"

        async for token in orchestrator.stream_tokens(
            message=validated_request.message,
            session_id=validated_request.session_id,
            user_context=validated_request.user_context,
            swarm_type=swarm_type,
            optimization_mode=optimization_mode
        ):
            yield json.dumps(token.dict()) + "\n"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson"
    )

@router.get("/metrics")
async def get_metrics(
    orchestrator: ChatOrchestrator = Depends(get_orchestrator)
) -> dict[str, Any]:
    """
    Get chat orchestrator metrics
    
    Args:
        orchestrator: Chat orchestrator instance
        
    Returns:
        Current metrics
    """
    return await orchestrator.get_metrics()

@router.get("/session/{session_id}")
async def get_session(
    session_id: str,
    orchestrator: ChatOrchestrator = Depends(get_orchestrator)
) -> dict[str, Any]:
    """
    Get session information
    
    Args:
        session_id: Session ID
        orchestrator: Chat orchestrator instance
        
    Returns:
        Session information and history
    """
    return {
        "session_id": session_id,
        "history": orchestrator.session_history.get(session_id, []),
        "status": await orchestrator.command_dispatcher.get_session_status(session_id)
    }

# ==================== WebSocket Endpoint ====================

@router.websocket("/ws/{client_id}/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    session_id: str,
    orchestrator: ChatOrchestrator = Depends(get_orchestrator),
    connection_pool: WebSocketConnectionPool = Depends(get_connection_pool)
):
    """
    WebSocket endpoint for real-time chat
    
    Args:
        websocket: WebSocket connection
        client_id: Client identifier
        session_id: Session identifier
        orchestrator: Chat orchestrator instance
        connection_pool: Connection pool for managing WebSocket limits
    """
    # Inject connection pool if not already set
    if not orchestrator.connection_pool:
        orchestrator.connection_pool = connection_pool

    await orchestrator.websocket_endpoint(websocket, client_id, session_id)

# ==================== Health Check Endpoints ====================

from enum import Enum as PythonEnum


class HealthStatus(str, PythonEnum):
    """Health status enum"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@router.get("/health")
async def health_check(
    orchestrator: ChatOrchestrator = Depends(get_orchestrator),
    connection_pool: WebSocketConnectionPool = Depends(get_connection_pool)
) -> dict[str, Any]:
    """
    Health check endpoint
    
    Returns:
        Health status of all components
    """
    checks = {}

    # Check orchestrator
    checks["orchestrator"] = {
        "status": HealthStatus.HEALTHY if orchestrator.initialized else HealthStatus.UNHEALTHY,
        "initialized": orchestrator.initialized,
        "active_connections": len(orchestrator.active_connections)
    }

    # Check connection pool
    pool_metrics = connection_pool.get_metrics()
    pool_utilization = pool_metrics.get("utilization", 0)
    checks["connection_pool"] = {
        "status": HealthStatus.HEALTHY if pool_utilization < 0.9 else HealthStatus.DEGRADED,
        "metrics": pool_metrics
    }

    # Check circuit breakers
    circuit_breaker_health = HealthStatus.HEALTHY
    for name, cb in orchestrator.circuit_breakers.items():
        state = cb.get_state()
        if state["state"] == "OPEN":
            circuit_breaker_health = HealthStatus.UNHEALTHY
            break
        elif state["state"] == "HALF_OPEN":
            circuit_breaker_health = HealthStatus.DEGRADED

    checks["circuit_breakers"] = {
        "status": circuit_breaker_health,
        "states": {name: cb.get_state() for name, cb in orchestrator.circuit_breakers.items()}
    }

    # Overall status
    overall_status = HealthStatus.HEALTHY
    for check in checks.values():
        if check["status"] == HealthStatus.UNHEALTHY:
            overall_status = HealthStatus.UNHEALTHY
            break
        elif check["status"] == HealthStatus.DEGRADED:
            overall_status = HealthStatus.DEGRADED

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }

@router.get("/ready")
async def readiness_probe(
    orchestrator: ChatOrchestrator = Depends(get_orchestrator)
) -> dict[str, bool]:
    """
    Readiness probe endpoint
    
    Returns:
        Ready status
    """
    if not orchestrator.initialized:
        raise HTTPException(status_code=503, detail="Service not ready")

    return {"ready": True}

@router.get("/live")
async def liveness_probe() -> dict[str, bool]:
    """
    Liveness probe endpoint
    
    Returns:
        Live status
    """
    return {"alive": True}

# ==================== Export ====================


__all__ = [
    "ChatOrchestrator",
    "WebSocketErrorBoundary",
    "CircuitBreaker",
    "ConnectionTimeoutManager",
    "router",
    "get_orchestrator",
    "get_connection_pool",
    "get_session_manager",
    "lifespan"
]
