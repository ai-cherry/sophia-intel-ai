"""
AG-UI Event Type Definitions
Standard event types for AG-UI compatibility with mapping to existing WebSocket events
Maintains backwards compatibility while enabling modern streaming features
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union


class AGUIEventType(str, Enum):
    """Standard AG-UI event types"""

    # Text streaming events
    TEXT_DELTA = "text_delta"
    TEXT_COMPLETE = "text_complete"

    # Tool execution events
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_DELTA = "tool_call_delta"
    TOOL_CALL_COMPLETE = "tool_call_complete"
    TOOL_RESULT = "tool_result"

    # Agent state events
    STATE_UPDATE = "state_update"
    STATUS_CHANGE = "status_change"

    # Business domain events (Pay Ready)
    ACCOUNT_STATUS_UPDATE = "account_status_update"
    PAYMENT_FLOW_UPDATE = "payment_flow_update"
    STUCK_ACCOUNT_ALERT = "stuck_account_alert"

    # Technical domain events (Artemis)
    TACTICAL_OPERATION = "tactical_operation"
    DEPLOYMENT_STATUS = "deployment_status"
    SYSTEM_HEALTH = "system_health"

    # Intelligence events (Sophia)
    INTELLIGENCE_INSIGHT = "intelligence_insight"
    PERFORMANCE_METRIC = "performance_metric"
    OPERATIONAL_UPDATE = "operational_update"

    # Swarm events
    SWARM_START = "swarm_start"
    SWARM_PROGRESS = "swarm_progress"
    SWARM_COMPLETE = "swarm_complete"
    SWARM_ERROR = "swarm_error"

    # Memory events
    MEMORY_UPDATE = "memory_update"
    MEMORY_RETRIEVAL = "memory_retrieval"

    # Connection events
    CONNECTED = "connected"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class WebSocketEventType(str, Enum):
    """Existing WebSocket event types for mapping"""

    CONNECTED = "connected"
    SWARM_EVENT = "swarm_event"
    MEMORY_UPDATE = "memory_update"
    METRICS = "metrics"
    PAY_READY_UPDATE = "pay_ready_update"
    STUCK_ACCOUNT_ALERT = "stuck_account_alert"
    TEAM_PERFORMANCE_UPDATE = "team_performance_update"
    OPERATIONAL_INTELLIGENCE = "operational_intelligence"
    SWARM_DEPLOYMENT_EVENT = "swarm_deployment_event"
    HEARTBEAT_ACK = "heartbeat_ack"
    ERROR = "error"


class DomainContext(str, Enum):
    """Business and technical domain contexts"""

    # Business domains
    PAY_READY = "pay_ready"
    CUSTOMER_SUCCESS = "customer_success"
    OPERATIONS = "operations"

    # Technical domains
    ARTEMIS = "artemis"
    SOPHIA_INTEL = "sophia_intel"
    SYSTEM = "system"

    # General
    GENERAL = "general"


@dataclass
class AGUIEventMetadata:
    """Metadata for AG-UI events"""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source: str = "sophia-intel-ai"
    domain: DomainContext = DomainContext.GENERAL
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    correlation_id: Optional[str] = None
    sequence: int = 0
    version: str = "1.0"


@dataclass
class AGUITextDelta:
    """Text delta for streaming responses"""

    delta: str
    index: int = 0
    cumulative_text: str = ""
    tokens_processed: int = 0
    tokens_remaining: Optional[int] = None
    finish_reason: Optional[str] = None


@dataclass
class AGUIToolCall:
    """Tool call information"""

    tool_name: str
    tool_id: str
    arguments: dict[str, Any]
    status: str = "pending"  # pending, running, complete, error
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_ms: Optional[int] = None


@dataclass
class AGUIStateUpdate:
    """Agent state update"""

    state: str
    previous_state: Optional[str] = None
    context: dict[str, Any] = field(default_factory=dict)
    progress: Optional[float] = None  # 0.0 to 1.0
    message: Optional[str] = None


@dataclass
class AGUIEvent:
    """Complete AG-UI event structure"""

    type: AGUIEventType
    metadata: AGUIEventMetadata
    data: Union[AGUITextDelta, AGUIToolCall, AGUIStateUpdate, dict[str, Any]]
    raw_data: Optional[dict[str, Any]] = None  # Original WebSocket event data

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "type": self.type.value,
            "metadata": {
                "event_id": self.metadata.event_id,
                "timestamp": self.metadata.timestamp,
                "source": self.metadata.source,
                "domain": self.metadata.domain.value,
                "sequence": self.metadata.sequence,
                "version": self.metadata.version,
            },
            "data": {},
        }

        # Add optional metadata
        if self.metadata.session_id:
            result["metadata"]["session_id"] = self.metadata.session_id
        if self.metadata.user_id:
            result["metadata"]["user_id"] = self.metadata.user_id
        if self.metadata.tenant_id:
            result["metadata"]["tenant_id"] = self.metadata.tenant_id
        if self.metadata.correlation_id:
            result["metadata"]["correlation_id"] = self.metadata.correlation_id

        # Handle data based on type
        if isinstance(self.data, dict):
            result["data"] = self.data
        else:
            # Convert dataclass to dict
            if hasattr(self.data, "__dict__"):
                result["data"] = {k: v for k, v in self.data.__dict__.items() if v is not None}
            else:
                result["data"] = self.data

        return result


# Event mapping configuration
WEBSOCKET_TO_AGUI_MAPPING = {
    # Direct mappings
    WebSocketEventType.CONNECTED: AGUIEventType.CONNECTED,
    WebSocketEventType.HEARTBEAT_ACK: AGUIEventType.HEARTBEAT,
    WebSocketEventType.ERROR: AGUIEventType.ERROR,
    # Business domain mappings
    WebSocketEventType.PAY_READY_UPDATE: AGUIEventType.ACCOUNT_STATUS_UPDATE,
    WebSocketEventType.STUCK_ACCOUNT_ALERT: AGUIEventType.STUCK_ACCOUNT_ALERT,
    WebSocketEventType.TEAM_PERFORMANCE_UPDATE: AGUIEventType.PERFORMANCE_METRIC,
    # Technical domain mappings
    WebSocketEventType.SWARM_DEPLOYMENT_EVENT: AGUIEventType.DEPLOYMENT_STATUS,
    WebSocketEventType.OPERATIONAL_INTELLIGENCE: AGUIEventType.INTELLIGENCE_INSIGHT,
    # Swarm mappings (contextual based on event_type)
    WebSocketEventType.SWARM_EVENT: {
        "start": AGUIEventType.SWARM_START,
        "progress": AGUIEventType.SWARM_PROGRESS,
        "complete": AGUIEventType.SWARM_COMPLETE,
        "error": AGUIEventType.SWARM_ERROR,
        "tool_call": AGUIEventType.TOOL_CALL_START,
        "tool_result": AGUIEventType.TOOL_RESULT,
        "state_update": AGUIEventType.STATE_UPDATE,
    },
    # Memory mappings
    WebSocketEventType.MEMORY_UPDATE: AGUIEventType.MEMORY_UPDATE,
    # System mappings
    WebSocketEventType.METRICS: AGUIEventType.SYSTEM_HEALTH,
}

# Domain context mapping
DOMAIN_MAPPING = {
    # Business domains
    "pay_ready": DomainContext.PAY_READY,
    "stuck_account": DomainContext.PAY_READY,
    "team_performance": DomainContext.OPERATIONS,
    # Technical domains
    "swarm_deployment": DomainContext.ARTEMIS,
    "artemis": DomainContext.ARTEMIS,
    "operational_intelligence": DomainContext.SOPHIA_INTEL,
    "sophia": DomainContext.SOPHIA_INTEL,
    # System
    "metrics": DomainContext.SYSTEM,
    "memory": DomainContext.SYSTEM,
    # Default
    "default": DomainContext.GENERAL,
}

# Event filtering configuration
EVENT_FILTERS = {
    DomainContext.PAY_READY: [
        AGUIEventType.ACCOUNT_STATUS_UPDATE,
        AGUIEventType.PAYMENT_FLOW_UPDATE,
        AGUIEventType.STUCK_ACCOUNT_ALERT,
    ],
    DomainContext.ARTEMIS: [
        AGUIEventType.TACTICAL_OPERATION,
        AGUIEventType.DEPLOYMENT_STATUS,
        AGUIEventType.SWARM_START,
        AGUIEventType.SWARM_PROGRESS,
        AGUIEventType.SWARM_COMPLETE,
        AGUIEventType.SWARM_ERROR,
    ],
    DomainContext.SOPHIA_INTEL: [
        AGUIEventType.INTELLIGENCE_INSIGHT,
        AGUIEventType.PERFORMANCE_METRIC,
        AGUIEventType.OPERATIONAL_UPDATE,
    ],
    DomainContext.SYSTEM: [
        AGUIEventType.SYSTEM_HEALTH,
        AGUIEventType.MEMORY_UPDATE,
        AGUIEventType.STATE_UPDATE,
    ],
}

# Streaming event types that support delta updates
STREAMING_EVENT_TYPES = {AGUIEventType.TEXT_DELTA, AGUIEventType.TOOL_CALL_DELTA}

# Event types that require authentication
AUTHENTICATED_EVENT_TYPES = {
    AGUIEventType.ACCOUNT_STATUS_UPDATE,
    AGUIEventType.PAYMENT_FLOW_UPDATE,
    AGUIEventType.STUCK_ACCOUNT_ALERT,
    AGUIEventType.INTELLIGENCE_INSIGHT,
    AGUIEventType.TACTICAL_OPERATION,
}


def get_domain_from_message(message: dict[str, Any]) -> DomainContext:
    """Extract domain context from message content"""

    message_type = message.get("type", "").lower()
    message_str = str(message).lower()

    # Check message type first
    for key, domain in DOMAIN_MAPPING.items():
        if key in message_type:
            return domain

    # Check message content
    if any(term in message_str for term in ["pay_ready", "stuck_account", "payment"]):
        return DomainContext.PAY_READY
    elif any(term in message_str for term in ["artemis", "deployment", "tactical"]):
        return DomainContext.ARTEMIS
    elif any(term in message_str for term in ["sophia", "intelligence", "insight"]):
        return DomainContext.SOPHIA_INTEL
    elif any(term in message_str for term in ["memory", "metrics", "system"]):
        return DomainContext.SYSTEM

    return DomainContext.GENERAL


def should_stream_event(event_type: AGUIEventType) -> bool:
    """Check if event type supports streaming"""
    return event_type in STREAMING_EVENT_TYPES


def requires_authentication(event_type: AGUIEventType) -> bool:
    """Check if event type requires authentication"""
    return event_type in AUTHENTICATED_EVENT_TYPES


def get_events_for_domain(domain: DomainContext) -> list[AGUIEventType]:
    """Get list of event types for a domain"""
    return EVENT_FILTERS.get(domain, [])
