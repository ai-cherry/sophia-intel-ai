"""
AG-UI Stream API Routes
FastAPI endpoints for Server-Sent Events (SSE) with AG-UI event streaming
Provides domain routing, event filtering, and performance monitoring
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from sse_starlette import EventSourceResponse

from ...core.agui_event_adapter import AGUIEventAdapter
from ...core.agui_event_types import (
    AGUIEvent,
    AGUIEventType,
    DomainContext,
    get_events_for_domain,
    requires_authentication,
)
from ...core.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agui", tags=["AG-UI Events"])

# Global instances (would be injected in real app)
event_adapter = AGUIEventAdapter(enable_streaming=True, enable_deltas=True)
active_connections: dict[str, dict[str, Any]] = {}
performance_metrics = {
    "total_connections": 0,
    "active_connections": 0,
    "events_sent": 0,
    "events_filtered": 0,
    "errors": 0,
    "avg_latency_ms": 0.0,
}


class AGUIStreamManager:
    """Manages AG-UI SSE streams with domain-based routing and filtering"""

    def __init__(self, websocket_manager: Optional[WebSocketManager] = None):
        self.websocket_manager = websocket_manager
        self.connections: dict[str, dict[str, Any]] = {}
        self.domain_subscriptions: dict[DomainContext, set[str]] = {}
        self.event_queues: dict[str, asyncio.Queue] = {}
        self.metrics = {
            "connections_created": 0,
            "connections_closed": 0,
            "events_streamed": 0,
            "events_filtered": 0,
            "domain_subscriptions": {},
            "average_connection_duration": 0.0,
        }

    async def create_connection(
        self,
        request: Request,
        connection_id: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        event_types: list[str] = None,
        domains: list[str] = None,
        auth_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create new AG-UI SSE connection"""

        connection_info = {
            "id": connection_id,
            "created_at": datetime.utcnow(),
            "session_id": session_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "event_types": set(event_types or []),
            "domains": set(domains or []),
            "auth_token": auth_token,
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "events_sent": 0,
            "last_activity": datetime.utcnow(),
        }

        # Create event queue for this connection
        self.event_queues[connection_id] = asyncio.Queue(maxsize=1000)

        # Store connection
        self.connections[connection_id] = connection_info

        # Update domain subscriptions
        for domain_str in domains or []:
            try:
                domain = DomainContext(domain_str)
                if domain not in self.domain_subscriptions:
                    self.domain_subscriptions[domain] = set()
                self.domain_subscriptions[domain].add(connection_id)
            except ValueError:
                logger.warning(f"Invalid domain: {domain_str}")

        # Update metrics
        self.metrics["connections_created"] += 1
        self.metrics["domain_subscriptions"] = {
            domain.value: len(connections)
            for domain, connections in self.domain_subscriptions.items()
        }

        logger.info(f"Created AG-UI connection: {connection_id} for user: {user_id}")
        return connection_info

    async def close_connection(self, connection_id: str):
        """Close AG-UI SSE connection"""
        if connection_id not in self.connections:
            return

        connection_info = self.connections[connection_id]

        # Calculate connection duration
        duration = (datetime.utcnow() - connection_info["created_at"]).total_seconds()

        # Remove from domain subscriptions
        for domain_set in self.domain_subscriptions.values():
            domain_set.discard(connection_id)

        # Clean up event queue
        if connection_id in self.event_queues:
            del self.event_queues[connection_id]

        # Remove connection
        del self.connections[connection_id]

        # Update metrics
        self.metrics["connections_closed"] += 1
        self.metrics["average_connection_duration"] = (
            self.metrics["average_connection_duration"]
            * (self.metrics["connections_closed"] - 1)
            + duration
        ) / self.metrics["connections_closed"]

        logger.info(
            f"Closed AG-UI connection: {connection_id} (duration: {duration:.1f}s)"
        )

    async def broadcast_event(
        self,
        event: AGUIEvent,
        target_domains: list[DomainContext] = None,
        target_connections: list[str] = None,
    ):
        """Broadcast AG-UI event to relevant connections"""

        # Determine target connections
        targets = set()

        if target_connections:
            targets.update(target_connections)
        elif target_domains:
            for domain in target_domains:
                targets.update(self.domain_subscriptions.get(domain, set()))
        else:
            # Broadcast to connections matching event domain
            targets.update(self.domain_subscriptions.get(event.metadata.domain, set()))

        # Filter connections by event type and domain preferences
        filtered_targets = []
        for connection_id in targets:
            if connection_id not in self.connections:
                continue

            connection = self.connections[connection_id]

            # Check event type filter
            if (
                connection["event_types"]
                and event.type not in connection["event_types"]
            ):
                continue

            # Check domain filter
            if (
                connection["domains"]
                and event.metadata.domain.value not in connection["domains"]
            ):
                continue

            # Check authentication requirements
            if requires_authentication(AGUIEventType(event.type)):
                if not connection["user_id"] or not connection["auth_token"]:
                    self.metrics["events_filtered"] += 1
                    continue

            filtered_targets.append(connection_id)

        # Queue event for each target connection
        event_dict = event.to_dict()
        queued_count = 0

        for connection_id in filtered_targets:
            try:
                queue = self.event_queues.get(connection_id)
                if queue and not queue.full():
                    await queue.put(event_dict)
                    queued_count += 1

                    # Update connection activity
                    if connection_id in self.connections:
                        self.connections[connection_id]["events_sent"] += 1
                        self.connections[connection_id][
                            "last_activity"
                        ] = datetime.utcnow()

            except Exception as e:
                logger.error(f"Error queuing event for connection {connection_id}: {e}")

        # Update metrics
        self.metrics["events_streamed"] += queued_count

        logger.debug(f"Broadcast event {event.type} to {queued_count} connections")

    async def get_event_stream(self, connection_id: str):
        """Get event stream generator for SSE"""
        if connection_id not in self.event_queues:
            raise ValueError(f"Connection {connection_id} not found")

        queue = self.event_queues[connection_id]

        try:
            while connection_id in self.connections:
                try:
                    # Wait for event with timeout
                    event_dict = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": event_dict["type"],
                        "data": json.dumps(event_dict),
                        "id": event_dict["metadata"]["event_id"],
                    }

                except asyncio.TimeoutError:
                    # Send keepalive heartbeat
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps(
                            {
                                "type": "heartbeat",
                                "timestamp": datetime.utcnow().isoformat(),
                                "connection_id": connection_id,
                            }
                        ),
                    }

        except Exception as e:
            logger.error(f"Error in event stream for {connection_id}: {e}")
        finally:
            await self.close_connection(connection_id)

    def get_metrics(self) -> dict[str, Any]:
        """Get stream manager metrics"""
        return {
            **self.metrics,
            "active_connections": len(self.connections),
            "active_queues": len(self.event_queues),
            "domain_subscriptions": self.metrics["domain_subscriptions"],
            "queue_sizes": {
                conn_id: queue.qsize() for conn_id, queue in self.event_queues.items()
            },
        }


# Global stream manager
stream_manager = AGUIStreamManager()


# Dependency for authentication (placeholder)
async def get_current_user(auth_token: Optional[str] = None):
    """Get current user from auth token (placeholder implementation)"""
    # In real implementation, validate JWT token and return user info
    return {
        "user_id": "user123" if auth_token else None,
        "tenant_id": "tenant456" if auth_token else None,
        "permissions": ["view_events"] if auth_token else [],
    }


@router.get("/stream")
async def agui_event_stream(
    request: Request,
    types: Optional[str] = Query(
        None, description="Comma-separated event types to filter"
    ),
    domains: Optional[str] = Query(
        None, description="Comma-separated domains to filter"
    ),
    session_id: Optional[str] = Query(None, description="Session identifier"),
    user_id: Optional[str] = Query(None, description="User identifier"),
    tenant_id: Optional[str] = Query(None, description="Tenant identifier"),
    auth_token: Optional[str] = Query(None, description="Authentication token"),
):
    """
    Server-Sent Events endpoint for AG-UI events

    Provides real-time streaming of AG-UI formatted events with:
    - Event type filtering
    - Domain-based routing
    - Authentication support
    - Performance monitoring
    """

    # Generate connection ID
    connection_id = str(uuid.uuid4())

    # Parse filters
    event_types = [t.strip() for t in types.split(",")] if types else []
    domain_list = [d.strip() for d in domains.split(",")] if domains else []

    # Validate event types
    valid_types = []
    for event_type in event_types:
        try:
            AGUIEventType(event_type)
            valid_types.append(event_type)
        except ValueError:
            logger.warning(f"Invalid event type: {event_type}")

    # Validate domains
    valid_domains = []
    for domain in domain_list:
        try:
            DomainContext(domain)
            valid_domains.append(domain)
        except ValueError:
            logger.warning(f"Invalid domain: {domain}")

    try:
        # Create connection
        await stream_manager.create_connection(
            request=request,
            connection_id=connection_id,
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            event_types=valid_types,
            domains=valid_domains,
            auth_token=auth_token,
        )

        # Return SSE response
        return EventSourceResponse(
            stream_manager.get_event_stream(connection_id),
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    except Exception as e:
        logger.error(f"Error creating AG-UI stream: {e}")
        performance_metrics["errors"] += 1
        raise HTTPException(status_code=500, detail="Failed to create event stream")


@router.get("/domains")
async def get_available_domains():
    """Get list of available domain contexts"""
    return {
        "domains": [domain.value for domain in DomainContext],
        "descriptions": {
            DomainContext.PAY_READY.value: "Pay Ready business operations",
            DomainContext.ARTEMIS.value: "Artemis tactical operations",
            DomainContext.SOPHIA_INTEL.value: "Sophia intelligence insights",
            DomainContext.SYSTEM.value: "System health and metrics",
            DomainContext.GENERAL.value: "General purpose events",
        },
    }


@router.get("/event-types")
async def get_available_event_types():
    """Get list of available event types"""
    return {
        "event_types": [event_type.value for event_type in AGUIEventType],
        "streaming_types": [
            AGUIEventType.TEXT_DELTA.value,
            AGUIEventType.TOOL_CALL_DELTA.value,
        ],
        "authenticated_types": [
            event_type.value
            for event_type in AGUIEventType
            if requires_authentication(event_type)
        ],
    }


@router.get("/domain/{domain}/events")
async def get_domain_events(domain: str):
    """Get available event types for a specific domain"""
    try:
        domain_context = DomainContext(domain)
        event_types = get_events_for_domain(domain_context)

        return {
            "domain": domain,
            "event_types": [event_type.value for event_type in event_types],
            "description": f"Events available for {domain} domain",
        }

    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")


@router.post("/test-event")
async def send_test_event(
    event_type: str = Query(..., description="Event type to send"),
    domain: str = Query(DomainContext.GENERAL.value, description="Domain context"),
    message: str = Query("Test event", description="Test message"),
    session_id: Optional[str] = Query(None, description="Session ID"),
):
    """Send test event for development and testing"""

    try:
        # Validate event type and domain
        agui_event_type = AGUIEventType(event_type)
        domain_context = DomainContext(domain)

        # Create test event using adapter
        test_ws_event = {
            "type": "test",
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "test": True,
        }

        # Convert to AG-UI event
        agui_event = await event_adapter.convert_websocket_event(
            test_ws_event, session_id=session_id
        )

        if agui_event:
            # Override type and domain for test
            agui_event.type = agui_event_type
            agui_event.metadata.domain = domain_context

            # Broadcast to relevant connections
            await stream_manager.broadcast_event(agui_event)

            return {
                "success": True,
                "event_sent": agui_event.to_dict(),
                "connections_notified": len(
                    stream_manager.domain_subscriptions.get(domain_context, set())
                ),
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create test event")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/metrics")
async def get_stream_metrics():
    """Get streaming performance metrics"""
    return {
        "stream_manager": stream_manager.get_metrics(),
        "adapter": {
            "active_streams": event_adapter.get_active_streams(),
            "streaming_enabled": event_adapter.is_streaming_enabled(),
            "delta_enabled": event_adapter.is_delta_enabled(),
        },
        "performance": performance_metrics,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/connections")
async def get_active_connections():
    """Get information about active connections"""
    connections = []

    for conn_id, conn_info in stream_manager.connections.items():
        connections.append(
            {
                "id": conn_id,
                "created_at": conn_info["created_at"].isoformat(),
                "session_id": conn_info.get("session_id"),
                "user_id": conn_info.get("user_id"),
                "tenant_id": conn_info.get("tenant_id"),
                "event_types": list(conn_info["event_types"]),
                "domains": list(conn_info["domains"]),
                "events_sent": conn_info["events_sent"],
                "last_activity": conn_info["last_activity"].isoformat(),
                "queue_size": stream_manager.event_queues[conn_id].qsize(),
                "client_ip": conn_info.get("client_ip"),
            }
        )

    return {
        "active_connections": len(connections),
        "connections": connections,
        "total_queue_items": sum(
            queue.qsize() for queue in stream_manager.event_queues.values()
        ),
    }


@router.post("/broadcast")
async def broadcast_custom_event(
    event_data: dict[str, Any],
    target_domains: Optional[list[str]] = Query(None, description="Target domains"),
    target_connections: Optional[list[str]] = Query(
        None, description="Target connection IDs"
    ),
):
    """Broadcast custom event to specified targets (admin only)"""

    # Note: In production, this would require admin authentication

    try:
        # Create AG-UI event from custom data
        agui_event = await event_adapter.convert_websocket_event(event_data)

        if not agui_event:
            raise HTTPException(status_code=400, detail="Invalid event data")

        # Parse target domains
        domains = []
        if target_domains:
            for domain_str in target_domains:
                try:
                    domains.append(DomainContext(domain_str))
                except ValueError:
                    raise HTTPException(
                        status_code=400, detail=f"Invalid domain: {domain_str}"
                    )

        # Broadcast event
        await stream_manager.broadcast_event(
            agui_event, target_domains=domains, target_connections=target_connections
        )

        return {
            "success": True,
            "event_broadcast": agui_event.to_dict(),
            "targets": {
                "domains": [d.value for d in domains] if domains else None,
                "connections": target_connections,
            },
        }

    except Exception as e:
        logger.error(f"Error broadcasting custom event: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast event")


# WebSocket integration bridge
async def bridge_websocket_event(ws_event: dict[str, Any], session_id: str = None):
    """Bridge WebSocket event to AG-UI stream (called from WebSocket manager)"""

    try:
        # Convert to AG-UI event
        agui_event = await event_adapter.convert_websocket_event(
            ws_event, session_id=session_id
        )

        if agui_event:
            # Broadcast to relevant AG-UI connections
            await stream_manager.broadcast_event(agui_event)
            logger.debug(f"Bridged WebSocket event {ws_event.get('type')} to AG-UI")

    except Exception as e:
        logger.error(f"Error bridging WebSocket event: {e}")


# Performance monitoring
@router.get("/health")
async def health_check():
    """Health check endpoint for AG-UI streaming"""

    active_connections = len(stream_manager.connections)
    total_events = stream_manager.metrics["events_streamed"]

    # Determine health status
    status = "healthy"
    if active_connections > 1000:  # High load threshold
        status = "degraded"
    if performance_metrics["errors"] > 10:  # Error threshold
        status = "unhealthy"

    return {
        "status": status,
        "active_connections": active_connections,
        "total_events_streamed": total_events,
        "uptime_seconds": (
            datetime.utcnow() - datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).total_seconds(),
        "performance": {
            "avg_latency_ms": performance_metrics["avg_latency_ms"],
            "error_rate": performance_metrics["errors"] / max(total_events, 1) * 100,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
