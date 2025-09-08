"""
Resilient WebSocket Handler for MCP Integration
Implements automatic reconnection, circuit breakers, and error recovery
"""

import asyncio
import builtins
import contextlib
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import websockets
from websockets.exceptions import (
    ConnectionClosed,
    ConnectionClosedError,
    WebSocketException,
)

from app.core.circuit_breaker import with_circuit_breaker
from app.core.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"
    CLOSED = "closed"


@dataclass
class ReconnectionConfig:
    """Configuration for reconnection behavior"""

    max_attempts: int = 10
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: float = 0.1
    circuit_breaker_timeout: float = 300.0  # 5 minutes


@dataclass
class ConnectionMetrics:
    """Connection health metrics"""

    total_connections: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    reconnection_attempts: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    connection_duration: float = 0.0
    last_error: Optional[str] = None
    error_count: int = 0
    circuit_breaker_trips: int = 0


@dataclass
class MCPMessage:
    """MCP protocol message"""

    id: str
    method: str
    params: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3


class ResilientWebSocketClient:
    """
    Resilient WebSocket client with automatic reconnection and circuit breaking
    Designed for MCP server communication
    """

    def __init__(
        self,
        url: str,
        reconnect_config: Optional[ReconnectionConfig] = None,
        message_handlers: Optional[dict[str, Callable]] = None,
    ):
        self.url = url
        self.reconnect_config = reconnect_config or ReconnectionConfig()
        self.message_handlers = message_handlers or {}

        # Connection state
        self.state = ConnectionState.DISCONNECTED
        self.websocket: websockets.Optional[WebSocketClientProtocol] = None
        self.connection_task: asyncio.Optional[Task] = None

        # Reconnection state
        self.reconnect_attempts = 0
        self.last_connection_time: Optional[datetime] = None
        self.connection_start_time: Optional[datetime] = None

        # Message handling
        self.pending_messages: dict[str, MCPMessage] = {}
        self.message_queue: list[MCPMessage] = []
        self.response_futures: dict[str, asyncio.Future] = {}

        # Metrics
        self.metrics = ConnectionMetrics()

        # Event callbacks
        self.on_connected: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None
        self.on_message: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

        # Circuit breaker state
        self.circuit_breaker_open = False
        self.circuit_breaker_open_time: Optional[datetime] = None

    async def connect(self, timeout: float = 10.0) -> bool:
        """
        Establish WebSocket connection with timeout and retries

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if connected successfully
        """
        if self.state == ConnectionState.CONNECTED:
            return True

        if self.circuit_breaker_open:
            if (
                datetime.now() - self.circuit_breaker_open_time
            ).seconds < self.reconnect_config.circuit_breaker_timeout:
                logger.warning(f"Circuit breaker open for {self.url}")
                return False
            else:
                logger.info(f"Circuit breaker reset for {self.url}")
                self.circuit_breaker_open = False

        self.state = ConnectionState.CONNECTING
        self.connection_start_time = datetime.now()

        try:
            logger.info(f"Connecting to MCP WebSocket: {self.url}")

            # Configure WebSocket with timeouts and headers
            extra_headers = {
                "User-Agent": "Sophia-Intel-AI/1.0",
                "X-Client-Type": "MCP-Client",
            }

            self.websocket = await websockets.connect(
                self.url,
                timeout=timeout,
                extra_headers=extra_headers,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10,
            )

            self.state = ConnectionState.CONNECTED
            self.last_connection_time = datetime.now()
            self.reconnect_attempts = 0

            # Update metrics
            self.metrics.total_connections += 1
            self.metrics.successful_connections += 1

            # Start message handling task
            self.connection_task = asyncio.create_task(self._handle_connection())

            # Send queued messages
            await self._send_queued_messages()

            # Trigger connected callback
            if self.on_connected:
                await self.on_connected()

            logger.info(f"Successfully connected to MCP WebSocket: {self.url}")
            return True

        except Exception as e:
            self.state = ConnectionState.FAILED
            self.metrics.failed_connections += 1
            self.metrics.last_error = str(e)
            self.metrics.error_count += 1

            logger.error(f"Failed to connect to MCP WebSocket: {e}")

            # Trigger error callback
            if self.on_error:
                await self.on_error(e)

            return False

    async def disconnect(self, code: int = 1000, reason: str = "Normal closure"):
        """
        Gracefully disconnect WebSocket

        Args:
            code: WebSocket close code
            reason: Close reason
        """
        if self.state == ConnectionState.DISCONNECTED:
            return

        logger.info(f"Disconnecting from MCP WebSocket: {reason}")

        self.state = ConnectionState.CLOSED

        # Cancel connection task
        if self.connection_task and not self.connection_task.done():
            self.connection_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.connection_task

        # Close WebSocket
        if self.websocket and not self.websocket.closed:
            try:
                await self.websocket.close(code, reason)
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")

        # Update metrics
        if self.connection_start_time:
            self.metrics.connection_duration += (
                datetime.now() - self.connection_start_time
            ).total_seconds()

        # Clear state
        self.websocket = None
        self.connection_task = None

        # Trigger disconnected callback
        if self.on_disconnected:
            await self.on_disconnected()

    @with_circuit_breaker("mcp_websocket")
    async def send_mcp_message(
        self,
        method: str,
        params: dict[str, Any] = None,
        message_id: Optional[str] = None,
        expect_response: bool = True,
        timeout: float = 30.0,
    ) -> Optional[dict[str, Any]]:
        """
        Send MCP message with automatic retry and response handling

        Args:
            method: MCP method name
            params: Message parameters
            message_id: Optional message ID
            expect_response: Whether to wait for response
            timeout: Response timeout

        Returns:
            Response message if expect_response is True
        """
        if not message_id:
            message_id = f"msg_{int(datetime.now().timestamp() * 1000000)}"

        message = MCPMessage(id=message_id, method=method, params=params or {})

        # Queue message if not connected
        if self.state != ConnectionState.CONNECTED:
            self.message_queue.append(message)

            # Try to connect if not already trying
            if self.state == ConnectionState.DISCONNECTED:
                await self.connect()

            if self.state != ConnectionState.CONNECTED:
                logger.warning(f"Cannot send MCP message - not connected: {method}")
                return None

        try:
            # Prepare message payload
            payload = {
                "jsonrpc": "2.0",
                "id": message.id,
                "method": method,
                "params": params or {},
            }

            # Send message
            await self.websocket.send(json.dumps(payload))
            self.metrics.messages_sent += 1

            # Store pending message for response tracking
            if expect_response:
                self.pending_messages[message.id] = message
                future = asyncio.Future()
                self.response_futures[message.id] = future

                try:
                    # Wait for response with timeout
                    response = await asyncio.wait_for(future, timeout=timeout)
                    return response

                except asyncio.TimeoutError:
                    logger.warning(f"MCP message timeout: {method} ({message.id})")
                    self._handle_message_timeout(message.id)
                    return None

                finally:
                    # Clean up
                    self.pending_messages.pop(message.id, None)
                    self.response_futures.pop(message.id, None)

            return {"status": "sent"}

        except Exception as e:
            logger.error(f"Failed to send MCP message {method}: {e}")
            self.metrics.error_count += 1

            # Queue for retry if connection error
            if isinstance(e, (ConnectionClosed, WebSocketException)):
                message.retry_count += 1
                if message.retry_count <= message.max_retries:
                    self.message_queue.append(message)
                    # Trigger reconnection
                    asyncio.create_task(self._handle_connection_error(e))

            return None

    async def _handle_connection(self):
        """Handle incoming messages and connection lifecycle"""
        try:
            while self.state == ConnectionState.CONNECTED and self.websocket:
                try:
                    # Receive message with timeout
                    raw_message = await asyncio.wait_for(
                        self.websocket.recv(), timeout=60.0  # 1 minute timeout
                    )

                    self.metrics.messages_received += 1

                    # Parse JSON message
                    try:
                        message = json.loads(raw_message)
                        await self._handle_incoming_message(message)
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in MCP message: {e}")
                        continue

                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    if self.websocket and not self.websocket.closed:
                        try:
                            await self.websocket.ping()
                        except Exception as e:
                            logger.warning(f"Ping failed: {e}")
                            break
                    continue

                except (ConnectionClosed, ConnectionClosedError) as e:
                    logger.info(f"MCP WebSocket connection closed: {e}")
                    break

                except Exception as e:
                    logger.error(f"Error in MCP WebSocket handler: {e}")
                    self.metrics.error_count += 1
                    break

        except asyncio.CancelledError:
            logger.info("MCP WebSocket handler cancelled")
        except Exception as e:
            logger.error(f"Fatal error in MCP WebSocket handler: {e}")
        finally:
            # Connection ended - attempt reconnection if appropriate
            if self.state == ConnectionState.CONNECTED:
                await self._handle_connection_error(
                    Exception("Connection ended unexpectedly")
                )

    async def _handle_incoming_message(self, message: dict[str, Any]):
        """Handle incoming MCP message"""
        message_id = message.get("id")
        method = message.get("method")

        # Response to our request
        if message_id and message_id in self.response_futures:
            future = self.response_futures[message_id]
            if not future.done():
                if "error" in message:
                    future.set_exception(Exception(f"MCP error: {message['error']}"))
                else:
                    future.set_result(message.get("result", message))

        # Request from server
        elif method:
            handler = self.message_handlers.get(method)
            if handler:
                try:
                    response = await handler(message.get("params", {}))

                    # Send response if message has ID
                    if message_id:
                        response_payload = {
                            "jsonrpc": "2.0",
                            "id": message_id,
                            "result": response,
                        }
                        await self.websocket.send(json.dumps(response_payload))

                except Exception as e:
                    logger.error(f"Error handling MCP method {method}: {e}")

                    # Send error response
                    if message_id:
                        error_payload = {
                            "jsonrpc": "2.0",
                            "id": message_id,
                            "error": {"code": -32603, "message": str(e)},
                        }
                        await self.websocket.send(json.dumps(error_payload))
            else:
                logger.warning(f"No handler for MCP method: {method}")

        # Trigger message callback
        if self.on_message:
            await self.on_message(message)

    async def _handle_connection_error(self, error: Exception):
        """Handle connection error and attempt reconnection"""
        if self.state == ConnectionState.CLOSED:
            return

        logger.warning(f"MCP WebSocket connection error: {error}")

        self.state = ConnectionState.RECONNECTING
        self.metrics.reconnection_attempts += 1

        # Close current connection
        if self.websocket and not self.websocket.closed:
            with contextlib.suppress(builtins.BaseException):
                await self.websocket.close()

        # Attempt reconnection with exponential backoff
        delay = self.reconnect_config.initial_delay

        while (
            self.reconnect_attempts < self.reconnect_config.max_attempts
            and self.state == ConnectionState.RECONNECTING
        ):
            self.reconnect_attempts += 1

            logger.info(
                f"Reconnection attempt {self.reconnect_attempts}/{self.reconnect_config.max_attempts} in {delay:.1f}s"
            )

            await asyncio.sleep(delay)

            if await self.connect():
                logger.info("Successfully reconnected to MCP WebSocket")
                return

            # Exponential backoff with jitter
            delay = min(
                delay * self.reconnect_config.backoff_factor,
                self.reconnect_config.max_delay,
            )
            delay += (
                delay
                * self.reconnect_config.jitter
                * (0.5 - asyncio.get_event_loop().time() % 1)
            )

        # Exhausted reconnection attempts
        logger.error(
            f"Failed to reconnect to MCP WebSocket after {self.reconnect_attempts} attempts"
        )
        self.state = ConnectionState.FAILED

        # Open circuit breaker
        self.circuit_breaker_open = True
        self.circuit_breaker_open_time = datetime.now()
        self.metrics.circuit_breaker_trips += 1

    async def _send_queued_messages(self):
        """Send messages that were queued while disconnected"""
        if not self.message_queue or self.state != ConnectionState.CONNECTED:
            return

        logger.info(f"Sending {len(self.message_queue)} queued MCP messages")

        for message in self.message_queue.copy():
            try:
                await self.send_mcp_message(
                    method=message.method,
                    params=message.params,
                    message_id=message.id,
                    expect_response=False,
                )
                self.message_queue.remove(message)

            except Exception as e:
                logger.warning(f"Failed to send queued message {message.id}: {e}")

    def _handle_message_timeout(self, message_id: str):
        """Handle message response timeout"""
        message = self.pending_messages.get(message_id)
        if message:
            message.retry_count += 1
            if message.retry_count <= message.max_retries:
                logger.info(f"Retrying timed out MCP message: {message.method}")
                self.message_queue.append(message)

    def get_metrics(self) -> dict[str, Any]:
        """Get connection metrics"""
        return {
            "state": self.state.value,
            "url": self.url,
            "connected": self.state == ConnectionState.CONNECTED,
            "reconnect_attempts": self.reconnect_attempts,
            "circuit_breaker_open": self.circuit_breaker_open,
            "pending_messages": len(self.pending_messages),
            "queued_messages": len(self.message_queue),
            "last_connection": (
                self.last_connection_time.isoformat()
                if self.last_connection_time
                else None
            ),
            "metrics": {
                "total_connections": self.metrics.total_connections,
                "successful_connections": self.metrics.successful_connections,
                "failed_connections": self.metrics.failed_connections,
                "messages_sent": self.metrics.messages_sent,
                "messages_received": self.metrics.messages_received,
                "error_count": self.metrics.error_count,
                "circuit_breaker_trips": self.metrics.circuit_breaker_trips,
            },
        }

    async def health_check(self) -> dict[str, Any]:
        """Perform health check by pinging MCP server"""
        try:
            response = await self.send_mcp_message(
                method="ping", expect_response=True, timeout=5.0
            )

            return {
                "healthy": response is not None,
                "response": response,
                "state": self.state.value,
                "metrics": self.get_metrics(),
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "state": self.state.value,
                "metrics": self.get_metrics(),
            }


class MCPWebSocketManager(WebSocketManager):
    """
    Enhanced WebSocket manager with MCP-specific functionality
    Extends the base WebSocketManager with resilient MCP client support
    """

    def __init__(self):
        # Get secret key from environment or use default
        import os

        secret_key = os.getenv(
            "JWT_SECRET_KEY", "default-secret-key-change-in-production"
        )
        super().__init__(secret_key)
        self.mcp_clients: dict[str, ResilientWebSocketClient] = {}
        self.mcp_servers = {
            "main": "ws://localhost:8003/mcp/ws",
            "memory": "ws://localhost:8003/memory/ws",
            "tools": "ws://localhost:8003/tools/ws",
        }

    async def initialize(self):
        """Initialize MCP WebSocket manager with clients"""
        await super().initialize()

        # Initialize MCP clients
        for server_name, url in self.mcp_servers.items():
            client = ResilientWebSocketClient(
                url=url,
                message_handlers={
                    "memory_update": self._handle_memory_update,
                    "tool_result": self._handle_tool_result,
                    "status_update": self._handle_status_update,
                },
            )

            # Set up callbacks
            client.on_connected = lambda: self._on_mcp_connected(server_name)
            client.on_disconnected = lambda: self._on_mcp_disconnected(server_name)
            client.on_error = lambda e: self._on_mcp_error(server_name, e)

            self.mcp_clients[server_name] = client

            # Attempt initial connection
            await client.connect()

    async def send_to_mcp_server(
        self,
        server: str,
        method: str,
        params: dict[str, Any] = None,
        expect_response: bool = True,
    ) -> Optional[dict[str, Any]]:
        """Send message to specific MCP server"""
        client = self.mcp_clients.get(server)
        if not client:
            logger.error(f"MCP server not found: {server}")
            return None

        return await client.send_mcp_message(
            method=method, params=params, expect_response=expect_response
        )

    async def _handle_memory_update(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle memory update from MCP server"""
        # Broadcast to WebSocket clients
        await self.broadcast(
            "memory_updates", {"type": "mcp_memory_update", "data": params}
        )
        return {"status": "received"}

    async def _handle_tool_result(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tool execution result from MCP server"""
        # Broadcast to WebSocket clients
        await self.broadcast(
            "tool_results", {"type": "mcp_tool_result", "data": params}
        )
        return {"status": "received"}

    async def _handle_status_update(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle status update from MCP server"""
        # Broadcast to WebSocket clients
        await self.broadcast(
            "status_updates", {"type": "mcp_status_update", "data": params}
        )
        return {"status": "received"}

    async def _on_mcp_connected(self, server_name: str):
        """Handle MCP client connection"""
        logger.info(f"MCP client connected: {server_name}")
        await self.broadcast(
            "mcp_status", {"type": "mcp_connected", "server": server_name}
        )

    async def _on_mcp_disconnected(self, server_name: str):
        """Handle MCP client disconnection"""
        logger.warning(f"MCP client disconnected: {server_name}")
        await self.broadcast(
            "mcp_status", {"type": "mcp_disconnected", "server": server_name}
        )

    async def _on_mcp_error(self, server_name: str, error: Exception):
        """Handle MCP client error"""
        logger.error(f"MCP client error on {server_name}: {error}")
        await self.broadcast(
            "mcp_status",
            {"type": "mcp_error", "server": server_name, "error": str(error)},
        )

    async def get_mcp_health(self) -> dict[str, Any]:
        """Get health status of all MCP connections"""
        health_status = {}

        for server_name, client in self.mcp_clients.items():
            health_status[server_name] = await client.health_check()

        return {
            "servers": health_status,
            "overall_healthy": all(
                status["healthy"] for status in health_status.values()
            ),
            "timestamp": datetime.now().isoformat(),
        }


# Global instance
mcp_ws_manager = MCPWebSocketManager()
