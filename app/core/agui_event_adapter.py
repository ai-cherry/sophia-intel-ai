"""
AG-UI Event Adapter
Bridges existing WebSocket events to AG-UI format while maintaining backwards compatibility
Selective adoption for new features with fallback to existing infrastructure
"""

import logging
from collections.abc import AsyncGenerator
from dataclasses import replace
from datetime import datetime
from typing import Any, Optional

from .agui_event_types import (
    WEBSOCKET_TO_AGUI_MAPPING,
    AGUIEvent,
    AGUIEventMetadata,
    AGUIEventType,
    AGUIStateUpdate,
    AGUITextDelta,
    AGUIToolCall,
    DomainContext,
    WebSocketEventType,
    get_domain_from_message,
)

logger = logging.getLogger(__name__)


class AGUIEventAdapter:
    """
    Adapter that converts existing WebSocket events to AG-UI format
    Maintains backwards compatibility while enabling modern streaming features
    """

    def __init__(self, enable_streaming: bool = True, enable_deltas: bool = True):
        self.enable_streaming = enable_streaming
        self.enable_deltas = enable_deltas
        self.sequence_counter = 0
        self.active_streams: dict[str, dict[str, Any]] = {}
        self.text_buffers: dict[str, str] = {}

    async def convert_websocket_event(
        self,
        ws_event: dict[str, Any],
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[AGUIEvent]:
        """
        Convert existing WebSocket event to AG-UI format

        Args:
            ws_event: Original WebSocket event
            session_id: Session identifier
            user_id: User identifier
            tenant_id: Tenant identifier
            correlation_id: Request correlation ID

        Returns:
            Converted AG-UI event or None if not convertible
        """
        try:
            ws_type = ws_event.get("type")
            if not ws_type:
                logger.warning("WebSocket event missing type field")
                return None

            # Get domain context from message
            domain = get_domain_from_message(ws_event)

            # Create metadata
            metadata = AGUIEventMetadata(
                timestamp=ws_event.get("timestamp", datetime.utcnow().isoformat()),
                domain=domain,
                session_id=session_id,
                user_id=user_id,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
                sequence=self._get_next_sequence(),
            )

            # Convert based on WebSocket event type
            agui_event = None

            if ws_type == WebSocketEventType.CONNECTED:
                agui_event = self._convert_connected_event(ws_event, metadata)
            elif ws_type == WebSocketEventType.SWARM_EVENT:
                agui_event = self._convert_swarm_event(ws_event, metadata)
            elif ws_type == WebSocketEventType.MEMORY_UPDATE:
                agui_event = self._convert_memory_event(ws_event, metadata)
            elif ws_type == WebSocketEventType.PAY_READY_UPDATE:
                agui_event = self._convert_pay_ready_event(ws_event, metadata)
            elif ws_type == WebSocketEventType.STUCK_ACCOUNT_ALERT:
                agui_event = self._convert_stuck_account_event(ws_event, metadata)
            elif ws_type == WebSocketEventType.TEAM_PERFORMANCE_UPDATE:
                agui_event = self._convert_performance_event(ws_event, metadata)
            elif ws_type == WebSocketEventType.OPERATIONAL_INTELLIGENCE:
                agui_event = self._convert_intelligence_event(ws_event, metadata)
            elif ws_type == WebSocketEventType.SWARM_DEPLOYMENT_EVENT:
                agui_event = self._convert_deployment_event(ws_event, metadata)
            elif ws_type == WebSocketEventType.METRICS:
                agui_event = self._convert_metrics_event(ws_event, metadata)
            elif ws_type == WebSocketEventType.HEARTBEAT_ACK:
                agui_event = self._convert_heartbeat_event(ws_event, metadata)
            elif ws_type == WebSocketEventType.ERROR:
                agui_event = self._convert_error_event(ws_event, metadata)
            else:
                # Fallback for unmapped events
                agui_event = self._convert_generic_event(ws_event, metadata)

            if agui_event:
                # Store raw data for debugging/fallback
                agui_event.raw_data = ws_event
                logger.debug(f"Converted {ws_type} -> {agui_event.type}")

            return agui_event

        except Exception as e:
            logger.error(f"Error converting WebSocket event: {e}")
            logger.debug(f"Event data: {ws_event}")
            return None

    async def create_text_stream(
        self,
        stream_id: str,
        initial_text: str = "",
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> AsyncGenerator[AGUIEvent, None]:
        """
        Create a text streaming generator for delta updates

        Args:
            stream_id: Unique stream identifier
            initial_text: Initial text content
            session_id: Session identifier
            user_id: User identifier
            tenant_id: Tenant identifier

        Yields:
            AG-UI text delta events
        """
        if not self.enable_streaming:
            return

        self.text_buffers[stream_id] = initial_text
        self.active_streams[stream_id] = {
            "type": "text",
            "start_time": datetime.utcnow(),
            "session_id": session_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
        }

        logger.info(f"Started text stream: {stream_id}")

    async def add_text_delta(
        self, stream_id: str, delta_text: str, finish_reason: Optional[str] = None
    ) -> Optional[AGUIEvent]:
        """
        Add text delta to existing stream

        Args:
            stream_id: Stream identifier
            delta_text: New text to add
            finish_reason: Reason for completion (if any)

        Returns:
            AG-UI text delta event
        """
        if not self.enable_deltas or stream_id not in self.active_streams:
            return None

        try:
            stream_info = self.active_streams[stream_id]
            current_text = self.text_buffers.get(stream_id, "")
            new_text = current_text + delta_text
            self.text_buffers[stream_id] = new_text

            # Create metadata
            metadata = AGUIEventMetadata(
                domain=DomainContext.GENERAL,
                session_id=stream_info.get("session_id"),
                user_id=stream_info.get("user_id"),
                tenant_id=stream_info.get("tenant_id"),
                correlation_id=stream_id,
                sequence=self._get_next_sequence(),
            )

            # Create text delta
            text_delta = AGUITextDelta(
                delta=delta_text,
                index=len(current_text),
                cumulative_text=new_text,
                tokens_processed=len(new_text.split()),
                finish_reason=finish_reason,
            )

            # Determine event type
            event_type = (
                AGUIEventType.TEXT_COMPLETE
                if finish_reason
                else AGUIEventType.TEXT_DELTA
            )

            event = AGUIEvent(type=event_type, metadata=metadata, data=text_delta)

            # Clean up if complete
            if finish_reason:
                await self._cleanup_stream(stream_id)

            return event

        except Exception as e:
            logger.error(f"Error adding text delta: {e}")
            return None

    async def create_tool_call_event(
        self,
        tool_name: str,
        tool_id: str,
        arguments: dict[str, Any],
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> AGUIEvent:
        """
        Create AG-UI tool call event

        Args:
            tool_name: Name of the tool being called
            tool_id: Unique tool call identifier
            arguments: Tool call arguments
            session_id: Session identifier
            user_id: User identifier
            tenant_id: Tenant identifier

        Returns:
            AG-UI tool call event
        """
        metadata = AGUIEventMetadata(
            domain=get_domain_from_message({"tool": tool_name}),
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            correlation_id=tool_id,
            sequence=self._get_next_sequence(),
        )

        tool_call = AGUIToolCall(
            tool_name=tool_name,
            tool_id=tool_id,
            arguments=arguments,
            status="pending",
            start_time=datetime.utcnow().isoformat(),
        )

        return AGUIEvent(
            type=AGUIEventType.TOOL_CALL_START, metadata=metadata, data=tool_call
        )

    async def update_tool_call(
        self,
        tool_id: str,
        status: str,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> Optional[AGUIEvent]:
        """
        Update existing tool call with result or error

        Args:
            tool_id: Tool call identifier
            status: New status (running, complete, error)
            result: Tool execution result
            error: Error message if failed

        Returns:
            Updated AG-UI tool call event
        """
        # This would typically update an existing tool call
        # For now, create a completion event
        metadata = AGUIEventMetadata(
            correlation_id=tool_id, sequence=self._get_next_sequence()
        )

        tool_call = AGUIToolCall(
            tool_name="unknown",  # Would be retrieved from active calls
            tool_id=tool_id,
            arguments={},
            status=status,
            result=result,
            error=error,
            end_time=datetime.utcnow().isoformat(),
        )

        event_type = (
            AGUIEventType.TOOL_CALL_COMPLETE
            if status == "complete"
            else AGUIEventType.TOOL_RESULT
        )

        return AGUIEvent(type=event_type, metadata=metadata, data=tool_call)

    def _convert_connected_event(
        self, ws_event: dict[str, Any], metadata: AGUIEventMetadata
    ) -> AGUIEvent:
        """Convert connected event"""
        return AGUIEvent(
            type=AGUIEventType.CONNECTED,
            metadata=metadata,
            data={
                "client_id": ws_event.get("client_id"),
                "session_id": ws_event.get("session_id"),
                "authenticated": ws_event.get("authenticated", False),
                "security_enabled": ws_event.get("security_enabled", False),
            },
        )

    def _convert_swarm_event(
        self, ws_event: dict[str, Any], metadata: AGUIEventMetadata
    ) -> AGUIEvent:
        """Convert swarm event to appropriate AG-UI event type"""
        event_type_str = ws_event.get("event_type", "progress")
        ws_event.get("session_id")

        # Map swarm event types to AG-UI types
        event_mapping = WEBSOCKET_TO_AGUI_MAPPING.get(
            WebSocketEventType.SWARM_EVENT, {}
        )
        agui_type = event_mapping.get(event_type_str, AGUIEventType.SWARM_PROGRESS)

        # Update domain context for swarm events
        metadata = replace(metadata, domain=DomainContext.ARTEMIS)

        data = ws_event.get("data", {})

        # Enhance data based on event type
        if agui_type == AGUIEventType.TOOL_CALL_START:
            # Convert to tool call format
            tool_data = AGUIToolCall(
                tool_name=data.get("tool_name", "unknown"),
                tool_id=data.get("tool_id", str(self._get_next_sequence())),
                arguments=data.get("arguments", {}),
                status="running",
            )
            data = tool_data
        elif agui_type in [
            AGUIEventType.SWARM_START,
            AGUIEventType.SWARM_PROGRESS,
            AGUIEventType.SWARM_COMPLETE,
        ]:
            # Add progress information
            if agui_type == AGUIEventType.SWARM_PROGRESS:
                data["progress"] = data.get("progress", 0.5)
            elif agui_type == AGUIEventType.SWARM_START:
                data["progress"] = 0.0
            elif agui_type == AGUIEventType.SWARM_COMPLETE:
                data["progress"] = 1.0

        return AGUIEvent(type=agui_type, metadata=metadata, data=data)

    def _convert_memory_event(
        self, ws_event: dict[str, Any], metadata: AGUIEventMetadata
    ) -> AGUIEvent:
        """Convert memory update event"""
        metadata = replace(metadata, domain=DomainContext.SYSTEM)

        return AGUIEvent(
            type=AGUIEventType.MEMORY_UPDATE,
            metadata=metadata,
            data={
                "memory_id": ws_event.get("memory_id"),
                "operation": ws_event.get("operation", "update"),
                "content": ws_event.get("data", {}),
            },
        )

    def _convert_pay_ready_event(
        self, ws_event: dict[str, Any], metadata: AGUIEventMetadata
    ) -> AGUIEvent:
        """Convert Pay Ready update event"""
        metadata = replace(metadata, domain=DomainContext.PAY_READY)

        return AGUIEvent(
            type=AGUIEventType.ACCOUNT_STATUS_UPDATE,
            metadata=metadata,
            data={
                "account_id": ws_event.get("account_id"),
                "status": ws_event.get("status"),
                "previous_status": ws_event.get("data", {}).get("previous_status"),
                "metrics": ws_event.get("data", {}),
                "last_updated": ws_event.get("timestamp"),
            },
        )

    def _convert_stuck_account_event(
        self, ws_event: dict[str, Any], metadata: AGUIEventMetadata
    ) -> AGUIEvent:
        """Convert stuck account alert event"""
        metadata = replace(metadata, domain=DomainContext.PAY_READY)

        return AGUIEvent(
            type=AGUIEventType.STUCK_ACCOUNT_ALERT,
            metadata=metadata,
            data={
                "account_id": ws_event.get("account_id"),
                "alert_type": ws_event.get("alert_type"),
                "severity": ws_event.get("severity", "medium"),
                "details": ws_event.get("details", {}),
                "recommended_actions": ws_event.get("details", {}).get(
                    "recommended_actions", []
                ),
            },
        )

    def _convert_performance_event(
        self, ws_event: dict[str, Any], metadata: AGUIEventMetadata
    ) -> AGUIEvent:
        """Convert team performance update event"""
        metadata = replace(metadata, domain=DomainContext.OPERATIONS)

        return AGUIEvent(
            type=AGUIEventType.PERFORMANCE_METRIC,
            metadata=metadata,
            data={
                "team_id": ws_event.get("team_id"),
                "metrics": ws_event.get("metrics", {}),
                "period": ws_event.get("metrics", {}).get("period", "current"),
                "trends": ws_event.get("metrics", {}).get("trends", {}),
            },
        )

    def _convert_intelligence_event(
        self, ws_event: dict[str, Any], metadata: AGUIEventMetadata
    ) -> AGUIEvent:
        """Convert operational intelligence event"""
        metadata = replace(metadata, domain=DomainContext.SOPHIA_INTEL)

        return AGUIEvent(
            type=AGUIEventType.INTELLIGENCE_INSIGHT,
            metadata=metadata,
            data={
                "insight_type": ws_event.get("insight_type"),
                "content": ws_event.get("data", {}),
                "confidence": ws_event.get("confidence", 0.0),
                "impact": ws_event.get("data", {}).get("impact", "medium"),
                "recommendations": ws_event.get("data", {}).get("recommendations", []),
            },
        )

    def _convert_deployment_event(
        self, ws_event: dict[str, Any], metadata: AGUIEventMetadata
    ) -> AGUIEvent:
        """Convert swarm deployment event"""
        metadata = replace(metadata, domain=DomainContext.ARTEMIS)

        return AGUIEvent(
            type=AGUIEventType.DEPLOYMENT_STATUS,
            metadata=metadata,
            data={
                "deployment_id": ws_event.get("deployment_id"),
                "event_type": ws_event.get("event_type"),
                "status": ws_event.get("data", {}).get("status", "unknown"),
                "details": ws_event.get("data", {}),
            },
        )

    def _convert_metrics_event(
        self, ws_event: dict[str, Any], metadata: AGUIEventMetadata
    ) -> AGUIEvent:
        """Convert system metrics event"""
        metadata = replace(metadata, domain=DomainContext.SYSTEM)

        return AGUIEvent(
            type=AGUIEventType.SYSTEM_HEALTH,
            metadata=metadata,
            data={
                "metrics": ws_event.get("data", {}),
                "health_score": ws_event.get("data", {}).get("health_score", 1.0),
                "alerts": ws_event.get("data", {}).get("alerts", []),
            },
        )

    def _convert_heartbeat_event(
        self, ws_event: dict[str, Any], metadata: AGUIEventMetadata
    ) -> AGUIEvent:
        """Convert heartbeat event"""
        return AGUIEvent(
            type=AGUIEventType.HEARTBEAT,
            metadata=metadata,
            data={"timestamp": ws_event.get("timestamp"), "status": "alive"},
        )

    def _convert_error_event(
        self, ws_event: dict[str, Any], metadata: AGUIEventMetadata
    ) -> AGUIEvent:
        """Convert error event"""
        return AGUIEvent(
            type=AGUIEventType.ERROR,
            metadata=metadata,
            data={
                "message": ws_event.get("message", "Unknown error"),
                "code": ws_event.get("code"),
                "details": ws_event.get("details", {}),
            },
        )

    def _convert_generic_event(
        self, ws_event: dict[str, Any], metadata: AGUIEventMetadata
    ) -> AGUIEvent:
        """Fallback for unmapped events"""
        return AGUIEvent(
            type=AGUIEventType.STATE_UPDATE,
            metadata=metadata,
            data={"original_type": ws_event.get("type"), "content": ws_event},
        )

    async def _cleanup_stream(self, stream_id: str):
        """Clean up completed stream"""
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]
        if stream_id in self.text_buffers:
            del self.text_buffers[stream_id]
        logger.debug(f"Cleaned up stream: {stream_id}")

    def _get_next_sequence(self) -> int:
        """Get next sequence number"""
        self.sequence_counter += 1
        return self.sequence_counter

    def get_active_streams(self) -> dict[str, Any]:
        """Get information about active streams"""
        return {
            "count": len(self.active_streams),
            "streams": {
                stream_id: {
                    "type": info["type"],
                    "duration_seconds": (
                        datetime.utcnow() - info["start_time"]
                    ).total_seconds(),
                    "session_id": info.get("session_id"),
                }
                for stream_id, info in self.active_streams.items()
            },
        }

    def is_streaming_enabled(self) -> bool:
        """Check if streaming is enabled"""
        return self.enable_streaming

    def is_delta_enabled(self) -> bool:
        """Check if delta updates are enabled"""
        return self.enable_deltas

    async def create_state_update_event(
        self,
        state: str,
        previous_state: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        domain: DomainContext = DomainContext.GENERAL,
    ) -> AGUIEvent:
        """
        Create state update event

        Args:
            state: New state
            previous_state: Previous state
            context: Additional context
            progress: Progress (0.0 to 1.0)
            message: Status message
            session_id: Session identifier
            user_id: User identifier
            tenant_id: Tenant identifier
            domain: Domain context

        Returns:
            AG-UI state update event
        """
        metadata = AGUIEventMetadata(
            domain=domain,
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            sequence=self._get_next_sequence(),
        )

        state_update = AGUIStateUpdate(
            state=state,
            previous_state=previous_state,
            context=context or {},
            progress=progress,
            message=message,
        )

        return AGUIEvent(
            type=AGUIEventType.STATE_UPDATE, metadata=metadata, data=state_update
        )
