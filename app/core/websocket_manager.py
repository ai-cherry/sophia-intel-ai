"""
Secure WebSocket Manager for Real-time Updates
Handles WebSocket connections with comprehensive security, authentication, rate limiting,
and real-time monitoring for live swarm execution, memory updates, and metrics
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import HTTPException, WebSocket, WebSocketDisconnect

from .websocket_auth import (
    AuthenticatedUser,
    TenantType,
    UserRole,
    WebSocketAuthenticator,
)
from .websocket_rate_limiter import DomainType, WebSocketRateLimiter
from .websocket_security import WebSocketSecurityMiddleware

logger = logging.getLogger(__name__)


@dataclass
class WSConnection:
    """Secure WebSocket connection info"""

    websocket: WebSocket
    client_id: str
    session_id: str
    subscriptions: set[str]
    connected_at: datetime
    user: Optional[AuthenticatedUser] = None
    last_heartbeat: datetime = None
    message_count: int = 0
    security_violations: int = 0
    is_authenticated: bool = False


class WebSocketManager:
    """
    Secure WebSocket Manager with comprehensive security, authentication, and rate limiting
    """

    def __init__(
        self,
        secret_key: str,
        redis_url: str = "redis://localhost:6379",
        enable_security: bool = True,
        enable_rate_limiting: bool = True,
        enable_ddos_protection: bool = True,
    ):
        # Security components
        self.authenticator = (
            WebSocketAuthenticator(secret_key=secret_key, redis_url=redis_url)
            if enable_security
            else None
        )

        self.rate_limiter = (
            WebSocketRateLimiter(
                redis_url=redis_url, enable_ddos_protection=enable_ddos_protection
            )
            if enable_rate_limiting
            else None
        )

        self.security_middleware = (
            WebSocketSecurityMiddleware(redis_url=redis_url)
            if enable_security
            else None
        )

        # Connection management
        self.connections: dict[str, WSConnection] = {}
        self.channels: dict[str, set[str]] = {}
        self.message_queue: dict[str, list] = {}

        # Enhanced metrics
        self.metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "authenticated_connections": 0,
            "messages_sent": 0,
            "messages_failed": 0,
            "security_events": 0,
            "rate_limit_violations": 0,
            "blocked_connections": 0,
        }

        # Security settings
        self.enable_security = enable_security
        self.enable_rate_limiting = enable_rate_limiting
        self.require_authentication = True  # Require auth for all connections

    async def initialize(self):
        """Initialize secure WebSocket manager with all security components"""
        logger.info("Initializing Secure WebSocket Manager...")

        # Initialize security components
        if self.authenticator:
            await self.authenticator.initialize()
            await self.authenticator.start_cleanup_task()

        if self.rate_limiter:
            await self.rate_limiter.initialize()

        if self.security_middleware:
            await self.security_middleware.initialize()

        logger.info("Secure WebSocket Manager initialized with all security features")

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        session_id: str,
        token: Optional[str] = None,
    ) -> WSConnection:
        """
        Accept new secure WebSocket connection with authentication and security checks

        Args:
            websocket: FastAPI WebSocket instance
            client_id: Unique client identifier
            session_id: Session identifier
            token: Authentication token (JWT)

        Returns:
            WSConnection instance

        Raises:
            HTTPException: If authentication fails or security violation detected
        """
        try:
            # Security checks before accepting connection
            if self.security_middleware:
                # Check if client is blocked
                is_blocked, block_until = (
                    await self.security_middleware.is_client_blocked(client_id)
                )
                if is_blocked:
                    logger.warning(f"Blocked client attempted connection: {client_id}")
                    raise HTTPException(
                        status_code=403,
                        detail="Client blocked due to security violations",
                    )

            # Authenticate user if security is enabled
            user = None
            if self.authenticator and self.require_authentication:
                user = await self.authenticator.authenticate_websocket(
                    websocket, token, client_id
                )

            # Accept WebSocket connection after security checks pass
            await websocket.accept()

            # Create secure connection
            connection = WSConnection(
                websocket=websocket,
                client_id=client_id,
                session_id=session_id,
                subscriptions=set(),
                connected_at=datetime.utcnow(),
                user=user,
                last_heartbeat=datetime.utcnow(),
                message_count=0,
                security_violations=0,
                is_authenticated=user is not None,
            )

            # Create session if authenticated
            if user and self.authenticator:
                await self.authenticator.create_session(user, websocket)

            # Store connection
            self.connections[client_id] = connection
            self.metrics["total_connections"] += 1
            self.metrics["active_connections"] += 1
            if user:
                self.metrics["authenticated_connections"] += 1

            # Send secure welcome message
            welcome_message = {
                "type": "connected",
                "client_id": client_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "authenticated": user is not None,
                "security_enabled": self.enable_security,
                "rate_limiting_enabled": self.enable_rate_limiting,
            }

            if user:
                welcome_message.update(
                    {
                        "user_id": user.user_id,
                        "username": user.username,
                        "tenant_id": user.tenant_id,
                        "role": user.role.value,
                        "permissions": list(user.permissions)[
                            :10
                        ],  # Limit for security
                    }
                )

            await self.send_to_client(client_id, welcome_message)

            # Send any queued messages
            await self._send_queued_messages(client_id)

            logger.info(
                f"Secure WebSocket connected: {client_id} "
                f"(user: {user.username if user else 'anonymous'}, "
                f"tenant: {user.tenant_id if user else 'none'})"
            )

            return connection

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error establishing secure WebSocket connection: {e}")
            raise HTTPException(status_code=500, detail="Connection failed")

    async def disconnect(self, client_id: str):
        """
        Handle secure WebSocket disconnection with cleanup

        Args:
            client_id: Client to disconnect
        """
        if client_id in self.connections:
            connection = self.connections[client_id]

            # Close authentication session if exists
            if connection.user and self.authenticator:
                await self.authenticator.close_session(connection.session_id)

            # Remove from all channels
            for channel in connection.subscriptions:
                if channel in self.channels:
                    self.channels[channel].discard(client_id)

            # Close WebSocket
            try:
                await connection.websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")

            # Update metrics
            self.metrics["active_connections"] -= 1
            if connection.is_authenticated:
                self.metrics["authenticated_connections"] -= 1

            # Remove connection
            del self.connections[client_id]

            logger.info(
                f"Secure WebSocket disconnected: {client_id} "
                f"(user: {connection.user.username if connection.user else 'anonymous'})"
            )

    async def subscribe(self, client_id: str, channel: str):
        """
        Subscribe client to a channel

        Args:
            client_id: Client identifier
            channel: Channel name to subscribe to
        """
        if client_id not in self.connections:
            logger.warning(f"Client {client_id} not connected")
            return

        # Add to client's subscriptions
        self.connections[client_id].subscriptions.add(channel)

        # Add to channel's subscribers
        if channel not in self.channels:
            self.channels[channel] = set()
        self.channels[channel].add(client_id)

        # Confirm subscription
        await self.send_to_client(
            client_id,
            {
                "type": "subscribed",
                "channel": channel,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        logger.debug(f"Client {client_id} subscribed to {channel}")

    async def unsubscribe(self, client_id: str, channel: str):
        """
        Unsubscribe client from a channel

        Args:
            client_id: Client identifier
            channel: Channel to unsubscribe from
        """
        if client_id in self.connections:
            self.connections[client_id].subscriptions.discard(channel)

        if channel in self.channels:
            self.channels[channel].discard(client_id)

        logger.debug(f"Client {client_id} unsubscribed from {channel}")

    async def send_to_client(
        self, client_id: str, message: dict[str, Any], bypass_security: bool = False
    ):
        """
        Send secure message to specific client with authorization checks

        Args:
            client_id: Target client
            message: Message to send
            bypass_security: Skip security checks (for internal messages)
        """
        if client_id not in self.connections:
            # Queue message for when client reconnects
            if client_id not in self.message_queue:
                self.message_queue[client_id] = []
            self.message_queue[client_id].append(message)
            return

        connection = self.connections[client_id]

        # Security checks for outgoing messages (unless bypassed)
        if not bypass_security and self.enable_security:
            try:
                # Check if message contains sensitive data that requires tenant isolation
                if self.security_middleware and connection.user:
                    message_str = json.dumps(message)

                    # Check for Pay Ready data isolation
                    if (
                        "pay_ready" in message_str.lower()
                        or "stuck_account" in message_str.lower()
                    ):
                        has_access, security_event = (
                            await self.security_middleware.check_tenant_access(
                                connection.user, connection.user.tenant_id, "pay_ready"
                            )
                        )
                        if not has_access:
                            logger.warning(
                                f"Blocked Pay Ready data access for {client_id}"
                            )
                            return

                    # Check for Sophia intelligence data
                    if (
                        "sophia_intelligence" in message_str.lower()
                        or "operational_intelligence" in message_str.lower()
                    ):
                        has_access, security_event = (
                            await self.security_middleware.check_tenant_access(
                                connection.user,
                                connection.user.tenant_id,
                                "sophia_intelligence",
                            )
                        )
                        if not has_access:
                            logger.warning(
                                f"Blocked Sophia intelligence data access for {client_id}"
                            )
                            return

            except Exception as e:
                logger.error(f"Security check error for outgoing message: {e}")

        try:
            await connection.websocket.send_json(message)
            connection.message_count += 1
            self.metrics["messages_sent"] += 1

            # Update heartbeat
            connection.last_heartbeat = datetime.utcnow()

        except Exception as e:
            logger.error(f"Failed to send message to {client_id}: {e}")
            self.metrics["messages_failed"] += 1

            # Queue message for retry
            if client_id not in self.message_queue:
                self.message_queue[client_id] = []
            self.message_queue[client_id].append(message)

            # Disconnect failed client
            await self.disconnect(client_id)

    async def broadcast(self, channel: str, message: dict[str, Any]):
        """
        Broadcast message to all subscribers of a channel

        Args:
            channel: Channel to broadcast to
            message: Message to broadcast
        """
        if channel not in self.channels:
            logger.debug(f"No subscribers for channel {channel}")
            return

        # Add channel info to message
        message["channel"] = channel
        message["broadcast_time"] = datetime.utcnow().isoformat()

        # Send to all subscribers
        tasks = []
        for client_id in self.channels[channel].copy():
            tasks.append(self.send_to_client(client_id, message))

        await asyncio.gather(*tasks, return_exceptions=True)

        logger.debug(f"Broadcasted to {len(tasks)} clients on {channel}")

    async def broadcast_swarm_event(
        self, session_id: str, event_type: str, data: dict[str, Any]
    ):
        """
        Broadcast swarm execution event

        Args:
            session_id: Session executing the swarm
            event_type: Type of swarm event
            data: Event data
        """
        message = {
            "type": "swarm_event",
            "event_type": event_type,
            "session_id": session_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.broadcast(f"swarm_{session_id}", message)

    async def broadcast_memory_update(
        self, memory_id: str, operation: str, data: dict[str, Any]
    ):
        """
        Broadcast memory update event

        Args:
            memory_id: Memory item ID
            operation: Operation performed (create, update, delete)
            data: Memory data
        """
        message = {
            "type": "memory_update",
            "memory_id": memory_id,
            "operation": operation,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.broadcast("memory_updates", message)

    async def broadcast_metrics(self, metrics: dict[str, Any]):
        """
        Broadcast system metrics

        Args:
            metrics: Current system metrics
        """
        message = {
            "type": "metrics",
            "data": metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.broadcast("system_metrics", message)

    async def broadcast_sophia_pay_ready_update(
        self, account_id: str, status: str, data: dict[str, Any]
    ):
        """
        Broadcast Pay Ready account status update for Sophia dashboard

        Args:
            account_id: Account identifier
            status: Account status (ready, stuck, processing, etc.)
            data: Account data and metrics
        """
        message = {
            "type": "pay_ready_update",
            "account_id": account_id,
            "status": status,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.broadcast("sophia_pay_ready", message)

    async def broadcast_stuck_account_alert(
        self, account_id: str, alert_type: str, details: dict[str, Any]
    ):
        """
        Broadcast stuck account alert for immediate attention

        Args:
            account_id: Stuck account identifier
            alert_type: Type of stuck condition detected
            details: Alert details and recommended actions
        """
        message = {
            "type": "stuck_account_alert",
            "account_id": account_id,
            "alert_type": alert_type,
            "severity": details.get("severity", "medium"),
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.broadcast("stuck_accounts", message)

    async def broadcast_team_performance_update(
        self, team_id: str, metrics: dict[str, Any]
    ):
        """
        Broadcast team performance metrics update

        Args:
            team_id: Team identifier
            metrics: Performance metrics and analytics
        """
        message = {
            "type": "team_performance_update",
            "team_id": team_id,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.broadcast("team_performance", message)

    async def broadcast_operational_intelligence(
        self, insight_type: str, data: dict[str, Any]
    ):
        """
        Broadcast operational intelligence insights

        Args:
            insight_type: Type of operational insight
            data: Intelligence data and recommendations
        """
        message = {
            "type": "operational_intelligence",
            "insight_type": insight_type,
            "data": data,
            "confidence": data.get("confidence", 0.0),
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.broadcast("operational_intelligence", message)

    async def broadcast_swarm_deployment_event(
        self, deployment_id: str, event_type: str, data: dict[str, Any]
    ):
        """
        Broadcast swarm deployment events for monitoring

        Args:
            deployment_id: Unique deployment identifier
            event_type: Type of deployment event
            data: Event data and context
        """
        message = {
            "type": "swarm_deployment_event",
            "deployment_id": deployment_id,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.broadcast("swarm_deployments", message)

    async def _send_queued_messages(self, client_id: str):
        """Send any queued messages to reconnected client"""
        if client_id not in self.message_queue:
            return

        messages = self.message_queue[client_id]
        if not messages:
            return

        logger.info(f"Sending {len(messages)} queued messages to {client_id}")

        for message in messages:
            await self.send_to_client(client_id, message)

        # Clear queue
        del self.message_queue[client_id]

    async def handle_client_message(
        self, client_id: str, message: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handle incoming message from client with comprehensive security checks

        Args:
            client_id: Source client
            message: Received message

        Returns:
            Response to send back
        """
        try:
            if client_id not in self.connections:
                return {"type": "error", "message": "Connection not found"}

            connection = self.connections[client_id]
            msg_type = message.get("type", "unknown")

            # Update connection activity
            connection.last_heartbeat = datetime.utcnow()
            connection.message_count += 1

            # Security checks
            if self.enable_security:
                # Check if client is blocked
                if self.security_middleware:
                    is_blocked, block_until = (
                        await self.security_middleware.is_client_blocked(client_id)
                    )
                    if is_blocked:
                        return {
                            "type": "error",
                            "message": "Access denied - security violation",
                            "blocked_until": (
                                block_until.isoformat() if block_until else None
                            ),
                        }

                # Rate limiting check
                if self.rate_limiter:
                    domain = self._get_message_domain(msg_type)
                    rate_allowed, rate_info = await self.rate_limiter.check_rate_limit(
                        client_id, connection.user, domain, message
                    )
                    if not rate_allowed:
                        self.metrics["rate_limit_violations"] += 1
                        return {
                            "type": "error",
                            "message": "Rate limit exceeded",
                            "rate_limit_info": rate_info,
                        }

                # Input validation and threat detection
                if self.security_middleware:
                    is_valid, sanitized_message, security_event = (
                        await self.security_middleware.validate_input(
                            message, msg_type, connection.user
                        )
                    )
                    if not is_valid:
                        connection.security_violations += 1
                        self.metrics["security_events"] += 1
                        return {
                            "type": "error",
                            "message": "Security violation detected",
                            "event_id": (
                                security_event.event_id if security_event else None
                            ),
                        }
                    message = sanitized_message

                # Anomaly detection for authenticated users
                if self.security_middleware and connection.user:
                    anomaly_event = (
                        await self.security_middleware.detect_anomalous_behavior(
                            connection.user, msg_type, message
                        )
                    )
                    if anomaly_event and anomaly_event.blocked:
                        connection.security_violations += 1
                        self.metrics["security_events"] += 1
                        return {
                            "type": "error",
                            "message": "Anomalous behavior detected",
                            "event_id": anomaly_event.event_id,
                        }

            # Handle specific message types
            if msg_type == "ping":
                return {"type": "pong", "timestamp": datetime.utcnow().isoformat()}

            elif msg_type == "subscribe":
                return await self._handle_subscribe(client_id, message)

            elif msg_type == "unsubscribe":
                return await self._handle_unsubscribe(client_id, message)

            elif msg_type == "get_metrics":
                return await self._handle_get_metrics(client_id, message)

            elif msg_type == "pay_ready_query":
                return await self._handle_pay_ready_query(client_id, message)

            elif msg_type == "sophia_intelligence_query":
                return await self._handle_sophia_intelligence_query(client_id, message)

            elif msg_type == "artemis_operation":
                return await self._handle_artemis_operation(client_id, message)

            elif msg_type == "heartbeat":
                # Update session heartbeat if authenticated
                if connection.user and self.authenticator:
                    await self.authenticator.update_session_heartbeat(
                        connection.session_id
                    )
                return {
                    "type": "heartbeat_ack",
                    "timestamp": datetime.utcnow().isoformat(),
                }

            else:
                return {"type": "error", "message": f"Unknown message type: {msg_type}"}

        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            return {"type": "error", "message": "Internal server error"}

    def get_metrics(self) -> dict[str, Any]:
        """Get comprehensive WebSocket manager metrics including security stats"""
        base_metrics = {
            **self.metrics,
            "channels": {
                channel: len(subscribers)
                for channel, subscribers in self.channels.items()
            },
            "queued_messages": {
                client: len(messages) for client, messages in self.message_queue.items()
            },
        }

        # Add security metrics if available
        if self.authenticator:
            base_metrics["authentication_metrics"] = (
                self.authenticator.get_session_metrics()
            )

        if self.rate_limiter:
            base_metrics["rate_limiting_metrics"] = self.rate_limiter.get_metrics()

        if self.security_middleware:
            base_metrics["security_metrics"] = (
                self.security_middleware.get_security_metrics()
            )

        # Connection breakdown by tenant and role
        tenant_breakdown = {}
        role_breakdown = {}
        authenticated_count = 0

        for connection in self.connections.values():
            if connection.user:
                authenticated_count += 1
                tenant = connection.user.tenant_type.value
                role = connection.user.role.value
                tenant_breakdown[tenant] = tenant_breakdown.get(tenant, 0) + 1
                role_breakdown[role] = role_breakdown.get(role, 0) + 1

        base_metrics.update(
            {
                "connection_breakdown": {
                    "by_tenant": tenant_breakdown,
                    "by_role": role_breakdown,
                    "authenticated": authenticated_count,
                    "anonymous": len(self.connections) - authenticated_count,
                }
            }
        )

        return base_metrics

    def _get_message_domain(self, message_type: str) -> DomainType:
        """Get domain type for message to apply appropriate rate limits"""
        if "pay_ready" in message_type or "stuck_account" in message_type:
            return DomainType.PAY_READY
        elif "sophia" in message_type or "intelligence" in message_type:
            return DomainType.SOPHIA_INTEL
        elif "artemis" in message_type or "tactical" in message_type:
            return DomainType.ARTEMIS_TACTICAL
        elif "metrics" in message_type:
            return DomainType.SYSTEM_METRICS
        else:
            return DomainType.GENERAL

    async def _handle_subscribe(
        self, client_id: str, message: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle channel subscription with authorization"""
        channel = message.get("channel")
        if not channel:
            return {"type": "error", "message": "Channel name required"}

        connection = self.connections.get(client_id)
        if not connection:
            return {"type": "error", "message": "Connection not found"}

        # Check authorization for channel access
        if self.security_middleware and connection.user:
            has_access, security_event = (
                await self.security_middleware.check_tenant_isolation(
                    connection.user, channel
                )
            )
            if not has_access:
                return {"type": "error", "message": "Access denied to channel"}

        await self.subscribe(client_id, channel)
        return {"type": "subscribed", "channel": channel}

    async def _handle_unsubscribe(
        self, client_id: str, message: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle channel unsubscription"""
        channel = message.get("channel")
        if channel:
            await self.unsubscribe(client_id, channel)
            return {"type": "unsubscribed", "channel": channel}
        return {"type": "error", "message": "Channel name required"}

    async def _handle_get_metrics(
        self, client_id: str, message: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle metrics request with authorization"""
        connection = self.connections.get(client_id)
        if not connection:
            return {"type": "error", "message": "Connection not found"}

        # Check if user has permission to view metrics
        if connection.user and self.authenticator:
            has_permission = await self.authenticator.check_permission(
                connection.user, "view_system_metrics"
            )
            if not has_permission:
                return {"type": "error", "message": "Insufficient permissions"}

        return {"type": "metrics", "data": self.get_metrics()}

    async def _handle_pay_ready_query(
        self, client_id: str, message: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle Pay Ready specific queries with strict tenant isolation"""
        connection = self.connections.get(client_id)
        if not connection or not connection.user:
            return {
                "type": "error",
                "message": "Authentication required for Pay Ready data",
            }

        # Strict Pay Ready tenant isolation
        if (
            connection.user.tenant_type != TenantType.PAY_READY
            and connection.user.role != UserRole.ADMIN
        ):
            return {"type": "error", "message": "Pay Ready access denied"}

        # Check specific permission
        has_permission = await self.authenticator.check_permission(
            connection.user, "view_pay_ready_data"
        )
        if not has_permission:
            return {"type": "error", "message": "Insufficient Pay Ready permissions"}

        return {"type": "pay_ready_response", "message": "Query processed", "data": {}}

    async def _handle_sophia_intelligence_query(
        self, client_id: str, message: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle Sophia intelligence queries"""
        connection = self.connections.get(client_id)
        if not connection or not connection.user:
            return {
                "type": "error",
                "message": "Authentication required for Sophia intelligence",
            }

        # Check Sophia access
        has_permission = await self.authenticator.check_permission(
            connection.user, "view_sophia_intelligence"
        )
        if not has_permission:
            return {"type": "error", "message": "Insufficient Sophia permissions"}

        return {
            "type": "sophia_intelligence_response",
            "message": "Query processed",
            "data": {},
        }

    async def _handle_artemis_operation(
        self, client_id: str, message: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle Artemis tactical operations"""
        connection = self.connections.get(client_id)
        if not connection or not connection.user:
            return {
                "type": "error",
                "message": "Authentication required for Artemis operations",
            }

        # Check Artemis access
        has_permission = await self.authenticator.check_permission(
            connection.user, "view_artemis_operations"
        )
        if not has_permission:
            return {"type": "error", "message": "Insufficient Artemis permissions"}

        return {
            "type": "artemis_response",
            "message": "Operation processed",
            "data": {},
        }

    async def websocket_endpoint(
        self,
        websocket: WebSocket,
        client_id: str,
        session_id: str,
        token: Optional[str] = None,
    ):
        """
        Secure FastAPI WebSocket endpoint handler with comprehensive security

        Usage in FastAPI:
        @app.websocket("/ws/{client_id}/{session_id}")
        async def websocket_endpoint(
            websocket: WebSocket,
            client_id: str,
            session_id: str,
            token: str = Query(None)
        ):
            await ws_manager.websocket_endpoint(websocket, client_id, session_id, token)
        """
        try:
            # Establish secure connection
            await self.connect(websocket, client_id, session_id, token)

            # Main message loop
            while True:
                # Receive message from client
                data = await websocket.receive_json()

                # Handle message with security
                response = await self.handle_client_message(client_id, data)

                # Send response
                if response:
                    await self.send_to_client(client_id, response, bypass_security=True)

        except WebSocketDisconnect:
            logger.info(f"WebSocket client disconnected: {client_id}")
            await self.disconnect(client_id)
        except HTTPException as e:
            logger.warning(f"WebSocket HTTP error for {client_id}: {e.detail}")
            await websocket.close(code=e.status_code)
        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {e}")
            await self.disconnect(client_id)

    async def get_security_status(self) -> dict[str, Any]:
        """Get comprehensive security status"""
        status = {
            "security_enabled": self.enable_security,
            "rate_limiting_enabled": self.enable_rate_limiting,
            "authentication_required": self.require_authentication,
            "total_connections": len(self.connections),
            "authenticated_connections": self.metrics.get(
                "authenticated_connections", 0
            ),
            "security_violations": sum(
                conn.security_violations for conn in self.connections.values()
            ),
            "blocked_clients": 0,
        }

        # Add component-specific status
        if self.authenticator:
            status["authentication_status"] = "active"
            status["active_sessions"] = len(self.authenticator.active_sessions)

        if self.rate_limiter:
            status["rate_limiting_status"] = "active"
            ddos_alert = await self.rate_limiter.detect_ddos_patterns()
            status["ddos_alert_level"] = (
                ddos_alert.get("severity", "normal") if ddos_alert else "normal"
            )

        if self.security_middleware:
            status["security_middleware_status"] = "active"
            status["blocked_clients"] = len(self.security_middleware.blocked_clients)
            recent_events = await self.security_middleware.get_recent_security_events(
                limit=10
            )
            status["recent_security_events"] = len(recent_events)

        return status

    async def emergency_security_lockdown(self, duration_minutes: int = 15):
        """Emergency lockdown for critical security threats"""
        logger.critical("EMERGENCY SECURITY LOCKDOWN ACTIVATED")

        # Block all new connections temporarily
        self.require_authentication = True

        # Apply emergency rate limits
        if self.rate_limiter:
            await self.rate_limiter.apply_emergency_limits(duration_minutes * 60)

        # Disconnect all anonymous connections
        anonymous_clients = []
        for client_id, connection in self.connections.items():
            if not connection.is_authenticated:
                anonymous_clients.append(client_id)

        for client_id in anonymous_clients:
            await self.disconnect(client_id)

        logger.critical(
            f"Emergency lockdown: Disconnected {len(anonymous_clients)} anonymous clients"
        )

    async def audit_log_export(self, hours: int = 24) -> dict[str, Any]:
        """Export audit logs for compliance"""
        if not self.security_middleware:
            return {"error": "Security middleware not enabled"}

        events = await self.security_middleware.get_recent_security_events(
            limit=10000  # Large limit for audit export
        )

        # Filter events by time
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        filtered_events = [
            e for e in events if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]

        return {
            "audit_period_hours": hours,
            "total_events": len(filtered_events),
            "events": filtered_events,
            "exported_at": datetime.utcnow().isoformat(),
        }
