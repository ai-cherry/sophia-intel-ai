# 🏗️ DUAL AI ORCHESTRATOR TECHNICAL ARCHITECTURE

## Sophia Intelligence Platform & Artemis Command Center

---

## 📋 EXECUTIVE SUMMARY

This document defines the comprehensive technical architecture for the dual AI orchestrator system, featuring distinct business intelligence (Sophia) and technical operations (Artemis) domains with shared infrastructure and cross-domain collaboration patterns.

### 🎯 Architecture Goals

- **Domain Separation**: Clear business vs technical intelligence boundaries
- **Event-Driven Communication**: Async messaging between orchestrators
- **Shared Component Efficiency**: Unified infrastructure with domain-specific abstractions
- **Scalable Deployment**: Container orchestration with independent scaling
- **Cross-Domain Intelligence**: Collaborative AI operations across domains

---

## 🏗️ SYSTEM ARCHITECTURE DESIGN

### 1. HIGH-LEVEL ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                    DUAL AI ORCHESTRATOR SYSTEM                  │
├─────────────────┬─────────────────────┬─────────────────────────┤
│   SOPHIA        │    SHARED           │      ARTEMIS           │
│  INTELLIGENCE   │  INFRASTRUCTURE     │   COMMAND CENTER       │
│   PLATFORM      │                     │                        │
├─────────────────┼─────────────────────┼─────────────────────────┤
│                 │                     │                        │
│ ┌─────────────┐ │ ┌─────────────────┐ │ ┌─────────────────────┐ │
│ │Business AI  │ │ │   Event Bus     │ │ │   Technical AI      │ │
│ │Orchestrator │◄──┤   (Redis/NATS)  │──┤    Orchestrator     │ │
│ └─────────────┘ │ └─────────────────┘ │ └─────────────────────┘ │
│                 │                     │                        │
│ ┌─────────────┐ │ ┌─────────────────┐ │ ┌─────────────────────┐ │
│ │AGNO Business│ │ │  Vector Store   │ │ │  AGNO Technical     │ │
│ │   Teams     │ │ │   (Weaviate)    │ │ │     Teams          │ │
│ └─────────────┘ │ └─────────────────┘ │ └─────────────────────┘ │
│                 │                     │                        │
│ ┌─────────────┐ │ ┌─────────────────┐ │ ┌─────────────────────┐ │
│ │ Sophia UI   │ │ │   MCP Gateway   │ │ │   Artemis UI       │ │
│ │(Port 9000)  │ │ │   (Port 3333)   │ │ │  (Port 8000)       │ │
│ └─────────────┘ │ └─────────────────┘ │ └─────────────────────┘ │
│                 │                     │                        │
└─────────────────┴─────────────────────┴─────────────────────────┘
```

### 2. EVENT-DRIVEN COMMUNICATION PATTERNS

#### **Event Bus Architecture**

```python
# Event Bus Interface Definition
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import asyncio
import json

class EventType(Enum):
    # Cross-domain collaboration events
    SOPHIA_TO_ARTEMIS = "sophia_to_artemis"
    ARTEMIS_TO_SOPHIA = "artemis_to_sophia"

    # Sophia domain events
    BUSINESS_INSIGHT = "business_insight"
    CLIENT_ANALYSIS = "client_analysis"
    MARKET_RESEARCH = "market_research"
    SALES_INTELLIGENCE = "sales_intelligence"

    # Artemis domain events
    CODE_ANALYSIS = "code_analysis"
    SYSTEM_MONITORING = "system_monitoring"
    SECURITY_ALERT = "security_alert"
    PERFORMANCE_ANALYSIS = "performance_analysis"

    # System events
    ORCHESTRATOR_START = "orchestrator_start"
    ORCHESTRATOR_STOP = "orchestrator_stop"
    HEALTH_CHECK = "health_check"

@dataclass
class Event:
    """Universal event structure for cross-domain communication"""
    event_type: EventType
    source_domain: str  # 'sophia' or 'artemis'
    target_domain: Optional[str] = None  # None for broadcast
    payload: Dict[str, Any] = None
    correlation_id: str = None
    timestamp: datetime = None
    priority: int = 1  # 1=low, 5=high
    requires_response: bool = False

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.payload is None:
            self.payload = {}

class EventBus(ABC):
    """Abstract event bus for cross-domain communication"""

    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Publish an event to the bus"""
        pass

    @abstractmethod
    async def subscribe(self, event_type: EventType, handler: callable) -> None:
        """Subscribe to events of a specific type"""
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start the event bus"""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the event bus"""
        pass

class RedisEventBus(EventBus):
    """Redis-based event bus implementation"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        import redis.asyncio as redis
        self.redis = redis.from_url(redis_url)
        self.subscribers = {}
        self.running = False

    async def publish(self, event: Event) -> None:
        """Publish event to Redis streams"""
        stream_name = f"events:{event.event_type.value}"
        payload = {
            "event": json.dumps(event.__dict__, default=str),
            "timestamp": event.timestamp.isoformat()
        }
        await self.redis.xadd(stream_name, payload)

    async def subscribe(self, event_type: EventType, handler: callable) -> None:
        """Subscribe to event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    async def _event_listener(self):
        """Background task to process events"""
        while self.running:
            for event_type in self.subscribers:
                stream_name = f"events:{event_type.value}"
                try:
                    messages = await self.redis.xread({stream_name: '$'}, block=100)
                    for stream, events in messages:
                        for event_id, fields in events:
                            event_data = json.loads(fields[b'event'])
                            event = Event(**event_data)

                            # Dispatch to all handlers
                            for handler in self.subscribers[event_type]:
                                asyncio.create_task(handler(event))

                except Exception as e:
                    logger.error(f"Event processing error: {e}")
                    await asyncio.sleep(1)

            await asyncio.sleep(0.1)

    async def start(self) -> None:
        self.running = True
        self.listener_task = asyncio.create_task(self._event_listener())

    async def stop(self) -> None:
        self.running = False
        if hasattr(self, 'listener_task'):
            self.listener_task.cancel()
        await self.redis.close()
```

#### **Cross-Domain Communication Patterns**

```python
# Cross-Domain Collaboration Interface
class CrossDomainOrchestrator:
    """Handles cross-domain communication between Sophia and Artemis"""

    def __init__(self, domain: str, event_bus: EventBus):
        self.domain = domain
        self.event_bus = event_bus
        self.collaboration_handlers = {}

    async def request_collaboration(
        self,
        target_domain: str,
        request_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request collaboration from another domain"""

        event = Event(
            event_type=EventType.SOPHIA_TO_ARTEMIS if self.domain == 'sophia' else EventType.ARTEMIS_TO_SOPHIA,
            source_domain=self.domain,
            target_domain=target_domain,
            payload={
                "request_type": request_type,
                "context": context,
                "response_channel": f"response:{self.domain}:{uuid4().hex}"
            },
            requires_response=True
        )

        await self.event_bus.publish(event)
        return await self._wait_for_response(event.payload["response_channel"])

    async def register_collaboration_handler(
        self,
        request_type: str,
        handler: callable
    ) -> None:
        """Register handler for collaboration requests"""
        self.collaboration_handlers[request_type] = handler

    async def handle_collaboration_request(self, event: Event) -> None:
        """Handle incoming collaboration request"""
        request_type = event.payload.get("request_type")
        if request_type in self.collaboration_handlers:
            handler = self.collaboration_handlers[request_type]
            result = await handler(event.payload["context"])

            # Send response
            response_event = Event(
                event_type=EventType.ARTEMIS_TO_SOPHIA if self.domain == 'artemis' else EventType.SOPHIA_TO_ARTEMIS,
                source_domain=self.domain,
                target_domain=event.source_domain,
                payload={
                    "response": result,
                    "original_request": event.correlation_id
                }
            )
            await self.event_bus.publish(response_event)
```

### 3. SHARED COMPONENT INTERFACES

#### **Vector Store Partitioning Strategy**

```python
# Vector Store Domain Abstraction
from enum import Enum
from typing import List, Dict, Any, Optional
import weaviate

class VectorDomain(Enum):
    SOPHIA_BUSINESS = "sophia_business"
    ARTEMIS_TECHNICAL = "artemis_technical"
    SHARED_KNOWLEDGE = "shared_knowledge"
    CEO_KNOWLEDGE = "ceo_knowledge"

class DomainVectorStore:
    """Domain-partitioned vector store with cross-domain search"""

    def __init__(self, weaviate_client: weaviate.Client):
        self.client = weaviate_client
        self.domain_schemas = {
            VectorDomain.SOPHIA_BUSINESS: {
                "class": "SophiaBusinessKnowledge",
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "business_context", "dataType": ["string"]},
                    {"name": "client_id", "dataType": ["string"]},
                    {"name": "market_segment", "dataType": ["string"]},
                    {"name": "priority_level", "dataType": ["int"]},
                    {"name": "timestamp", "dataType": ["date"]}
                ]
            },
            VectorDomain.ARTEMIS_TECHNICAL: {
                "class": "ArtemisTechnicalKnowledge",
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "technical_domain", "dataType": ["string"]},
                    {"name": "system_component", "dataType": ["string"]},
                    {"name": "severity_level", "dataType": ["int"]},
                    {"name": "environment", "dataType": ["string"]},
                    {"name": "timestamp", "dataType": ["date"]}
                ]
            },
            VectorDomain.SHARED_KNOWLEDGE: {
                "class": "SharedKnowledge",
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "knowledge_type", "dataType": ["string"]},
                    {"name": "accessibility_level", "dataType": ["string"]},
                    {"name": "source_domain", "dataType": ["string"]},
                    {"name": "timestamp", "dataType": ["date"]}
                ]
            },
            VectorDomain.CEO_KNOWLEDGE: {
                "class": "CEOKnowledgeBase",
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "knowledge_category", "dataType": ["string"]},
                    {"name": "strategic_priority", "dataType": ["int"]},
                    {"name": "confidentiality_level", "dataType": ["string"]},
                    {"name": "timestamp", "dataType": ["date"]}
                ]
            }
        }

    async def initialize_schemas(self) -> None:
        """Initialize vector store schemas for all domains"""
        for domain, schema in self.domain_schemas.items():
            if not self.client.schema.exists(schema["class"]):
                self.client.schema.create_class(schema)

    async def store_knowledge(
        self,
        domain: VectorDomain,
        content: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Store knowledge in domain-specific partition"""
        schema = self.domain_schemas[domain]

        # Prepare object with domain-specific properties
        data_object = {"content": content}
        for prop in schema["properties"]:
            if prop["name"] in metadata:
                data_object[prop["name"]] = metadata[prop["name"]]

        result = self.client.data_object.create(
            data_object=data_object,
            class_name=schema["class"]
        )
        return result

    async def search_domain(
        self,
        domain: VectorDomain,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search within specific domain"""
        schema = self.domain_schemas[domain]

        query_builder = (
            self.client.query
            .get(schema["class"], ["content"] + [prop["name"] for prop in schema["properties"]])
            .with_near_text({"concepts": [query]})
            .with_limit(limit)
        )

        if filters:
            where_filter = self._build_where_filter(filters)
            query_builder = query_builder.with_where(where_filter)

        result = query_builder.do()
        return result.get("data", {}).get("Get", {}).get(schema["class"], [])

    async def cross_domain_search(
        self,
        query: str,
        domains: List[VectorDomain] = None,
        limit_per_domain: int = 5
    ) -> Dict[VectorDomain, List[Dict[str, Any]]]:
        """Search across multiple domains"""
        if domains is None:
            domains = list(VectorDomain)

        results = {}
        for domain in domains:
            results[domain] = await self.search_domain(domain, query, limit=limit_per_domain)

        return results
```

### 4. DATABASE & MEMORY ARCHITECTURE

#### **Conversation History and Session Management**

```python
# Session Management Architecture
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncpg
import json

@dataclass
class ConversationSession:
    session_id: str
    user_id: str
    domain: str  # 'sophia' or 'artemis'
    context_type: str  # 'business' or 'technical'
    started_at: datetime
    last_activity: datetime
    metadata: Dict[str, Any]
    is_active: bool = True

@dataclass
class ConversationMessage:
    message_id: str
    session_id: str
    sender_type: str  # 'user', 'sophia', 'artemis'
    content: str
    timestamp: datetime
    message_type: str  # 'query', 'response', 'collaboration'
    metadata: Dict[str, Any]

class ConversationManager:
    """Manages conversation history and session state"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None

    async def initialize(self) -> None:
        """Initialize database connection pool"""
        self.pool = await asyncpg.create_pool(self.database_url)
        await self._create_tables()

    async def _create_tables(self) -> None:
        """Create conversation tables"""
        async with self.pool.acquire() as connection:
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS conversation_sessions (
                    session_id VARCHAR PRIMARY KEY,
                    user_id VARCHAR NOT NULL,
                    domain VARCHAR NOT NULL,
                    context_type VARCHAR NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    last_activity TIMESTAMP NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    is_active BOOLEAN DEFAULT TRUE,
                    INDEX ON (user_id, domain),
                    INDEX ON (last_activity)
                );

                CREATE TABLE IF NOT EXISTS conversation_messages (
                    message_id VARCHAR PRIMARY KEY,
                    session_id VARCHAR NOT NULL REFERENCES conversation_sessions(session_id),
                    sender_type VARCHAR NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    message_type VARCHAR NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    INDEX ON (session_id, timestamp),
                    INDEX ON (sender_type, timestamp)
                );

                CREATE TABLE IF NOT EXISTS cross_domain_collaborations (
                    collaboration_id VARCHAR PRIMARY KEY,
                    source_session_id VARCHAR NOT NULL,
                    target_domain VARCHAR NOT NULL,
                    request_type VARCHAR NOT NULL,
                    context_data JSONB NOT NULL,
                    response_data JSONB,
                    status VARCHAR DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP,
                    INDEX ON (source_session_id, created_at)
                );
            """)

    async def create_session(
        self,
        user_id: str,
        domain: str,
        context_type: str,
        metadata: Dict[str, Any] = None
    ) -> ConversationSession:
        """Create new conversation session"""
        session_id = f"{domain}_{uuid4().hex}"
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            domain=domain,
            context_type=context_type,
            started_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            metadata=metadata or {}
        )

        async with self.pool.acquire() as connection:
            await connection.execute("""
                INSERT INTO conversation_sessions
                (session_id, user_id, domain, context_type, started_at, last_activity, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, session.session_id, session.user_id, session.domain,
                session.context_type, session.started_at, session.last_activity,
                json.dumps(session.metadata))

        return session

    async def add_message(
        self,
        session_id: str,
        sender_type: str,
        content: str,
        message_type: str = 'query',
        metadata: Dict[str, Any] = None
    ) -> ConversationMessage:
        """Add message to conversation"""
        message = ConversationMessage(
            message_id=f"msg_{uuid4().hex}",
            session_id=session_id,
            sender_type=sender_type,
            content=content,
            timestamp=datetime.utcnow(),
            message_type=message_type,
            metadata=metadata or {}
        )

        async with self.pool.acquire() as connection:
            # Insert message
            await connection.execute("""
                INSERT INTO conversation_messages
                (message_id, session_id, sender_type, content, timestamp, message_type, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, message.message_id, message.session_id, message.sender_type,
                message.content, message.timestamp, message.message_type,
                json.dumps(message.metadata))

            # Update session activity
            await connection.execute("""
                UPDATE conversation_sessions
                SET last_activity = $1
                WHERE session_id = $2
            """, message.timestamp, session_id)

        return message

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[ConversationMessage]:
        """Get conversation history for session"""
        async with self.pool.acquire() as connection:
            rows = await connection.fetch("""
                SELECT * FROM conversation_messages
                WHERE session_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
            """, session_id, limit)

            return [ConversationMessage(**dict(row)) for row in rows]
```

### 5. INTEGRATION PATTERNS

#### **Platform Integration Abstraction Layer**

```python
# Platform Integration Architecture
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncio

@dataclass
class PlatformCredentials:
    platform_name: str
    api_key: str
    additional_config: Dict[str, Any] = None

class PlatformIntegration(ABC):
    """Abstract platform integration interface"""

    @abstractmethod
    async def authenticate(self, credentials: PlatformCredentials) -> bool:
        """Authenticate with platform"""
        pass

    @abstractmethod
    async def fetch_data(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch data from platform"""
        pass

    @abstractmethod
    async def send_data(self, data: Dict[str, Any]) -> bool:
        """Send data to platform"""
        pass

class IntegrationRegistry:
    """Registry for managing platform integrations"""

    def __init__(self):
        self.integrations: Dict[str, PlatformIntegration] = {}
        self.credentials: Dict[str, PlatformCredentials] = {}

    def register_integration(
        self,
        name: str,
        integration: PlatformIntegration,
        credentials: PlatformCredentials
    ) -> None:
        """Register platform integration"""
        self.integrations[name] = integration
        self.credentials[name] = credentials

    async def get_integration(self, name: str) -> Optional[PlatformIntegration]:
        """Get authenticated integration"""
        if name in self.integrations:
            integration = self.integrations[name]
            credentials = self.credentials[name]

            if await integration.authenticate(credentials):
                return integration
        return None

# Configuration Management System
class ConfigurationManager:
    """Centralized configuration management"""

    def __init__(self, config_sources: List[str] = None):
        self.config_sources = config_sources or ['env', 'file', 'database']
        self.config_cache: Dict[str, Any] = {}
        self.domain_configs: Dict[str, Dict[str, Any]] = {}

    async def load_configuration(self) -> None:
        """Load configuration from all sources"""
        for source in self.config_sources:
            await self._load_from_source(source)

    async def _load_from_source(self, source: str) -> None:
        """Load configuration from specific source"""
        if source == 'env':
            await self._load_from_env()
        elif source == 'file':
            await self._load_from_file()
        elif source == 'database':
            await self._load_from_database()

    def get_domain_config(self, domain: str) -> Dict[str, Any]:
        """Get configuration for specific domain"""
        return self.domain_configs.get(domain, {})

    def set_domain_config(self, domain: str, config: Dict[str, Any]) -> None:
        """Set configuration for specific domain"""
        self.domain_configs[domain] = config
```

### 6. SECURITY & AUTHENTICATION

#### **Cross-Domain Authentication Flow**

```python
# Security Architecture
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import jwt
import bcrypt
from enum import Enum

class UserRole(Enum):
    ADMIN = "admin"
    SOPHIA_USER = "sophia_user"
    ARTEMIS_USER = "artemis_user"
    CROSS_DOMAIN_USER = "cross_domain_user"
    READ_ONLY = "read_only"

class Permission(Enum):
    # Sophia permissions
    SOPHIA_READ = "sophia:read"
    SOPHIA_WRITE = "sophia:write"
    SOPHIA_ADMIN = "sophia:admin"

    # Artemis permissions
    ARTEMIS_READ = "artemis:read"
    ARTEMIS_WRITE = "artemis:write"
    ARTEMIS_ADMIN = "artemis:admin"

    # Cross-domain permissions
    CROSS_DOMAIN_COLLABORATE = "cross_domain:collaborate"
    CROSS_DOMAIN_READ = "cross_domain:read"

    # System permissions
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_MONITOR = "system:monitor"

@dataclass
class User:
    user_id: str
    username: str
    email: str
    roles: Set[UserRole]
    permissions: Set[Permission]
    domain_access: Set[str]  # 'sophia', 'artemis', 'shared'
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

class AuthenticationManager:
    """Cross-domain authentication and authorization"""

    def __init__(self, jwt_secret: str, token_expiry_hours: int = 24):
        self.jwt_secret = jwt_secret
        self.token_expiry = timedelta(hours=token_expiry_hours)
        self.active_sessions: Dict[str, datetime] = {}

    async def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user and return token"""
        user = await self._validate_credentials(username, password)
        if user:
            token = self._generate_jwt_token(user)
            self.active_sessions[user.user_id] = datetime.utcnow()
            return {
                "token": token,
                "user": user,
                "expires_at": datetime.utcnow() + self.token_expiry
            }
        return None

    def _generate_jwt_token(self, user: User) -> str:
        """Generate JWT token for authenticated user"""
        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "roles": [role.value for role in user.roles],
            "permissions": [perm.value for perm in user.permissions],
            "domain_access": list(user.domain_access),
            "exp": datetime.utcnow() + self.token_expiry,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return user info"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            user_id = payload["user_id"]

            # Check if session is still active
            if user_id in self.active_sessions:
                return payload
        except jwt.ExpiredSignatureError:
            pass
        except jwt.InvalidTokenError:
            pass

        return None

    async def check_permission(
        self,
        user_token: str,
        required_permission: Permission,
        domain: str = None
    ) -> bool:
        """Check if user has required permission"""
        user_info = await self.validate_token(user_token)
        if not user_info:
            return False

        user_permissions = user_info.get("permissions", [])
        domain_access = user_info.get("domain_access", [])

        # Check permission
        if required_permission.value not in user_permissions:
            return False

        # Check domain access if specified
        if domain and domain not in domain_access:
            return False

        return True

# Rate Limiting and Access Controls
class RateLimiter:
    """Rate limiting for API endpoints"""

    def __init__(self):
        self.request_counts: Dict[str, Dict[datetime, int]] = {}
        self.limits = {
            'sophia': {'requests_per_minute': 60, 'requests_per_hour': 1000},
            'artemis': {'requests_per_minute': 60, 'requests_per_hour': 1000},
            'cross_domain': {'requests_per_minute': 30, 'requests_per_hour': 500}
        }

    async def check_rate_limit(
        self,
        user_id: str,
        domain: str,
        endpoint: str
    ) -> bool:
        """Check if request is within rate limits"""
        current_time = datetime.utcnow()
        key = f"{user_id}:{domain}:{endpoint}"

        if key not in self.request_counts:
            self.request_counts[key] = {}

        # Clean old entries
        self._cleanup_old_entries(key, current_time)

        # Count requests in last minute and hour
        minute_key = current_time.replace(second=0, microsecond=0)
        hour_key = current_time.replace(minute=0, second=0, microsecond=0)

        minute_count = self.request_counts[key].get(minute_key, 0)
        hour_count = sum(
            count for time_key, count in self.request_counts[key].items()
            if time_key >= hour_key
        )

        limits = self.limits.get(domain, self.limits['cross_domain'])

        if (minute_count >= limits['requests_per_minute'] or
            hour_count >= limits['requests_per_hour']):
            return False

        # Increment counter
        self.request_counts[key][minute_key] = minute_count + 1
        return True

    def _cleanup_old_entries(self, key: str, current_time: datetime) -> None:
        """Remove entries older than 1 hour"""
        cutoff_time = current_time - timedelta(hours=1)
        self.request_counts[key] = {
            time_key: count
            for time_key, count in self.request_counts[key].items()
            if time_key >= cutoff_time
        }
```

### 7. DEPLOYMENT ARCHITECTURE

#### **Container Orchestration Strategy**

```yaml
# docker-compose.dual-orchestrator.yml
version: "3.8"

services:
  # Sophia Intelligence Platform
  sophia-orchestrator:
    build:
      context: .
      dockerfile: docker/Dockerfile.sophia
    ports:
      - "9000:9000"
      - "9001:9001" # API port
      - "9002:9002" # WebSocket port
    environment:
      - SOPHIA_PORT=9000
      - SOPHIA_API_PORT=9001
      - SOPHIA_WS_PORT=9002
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://user:pass@postgres:5432/sophia_db
      - WEAVIATE_URL=http://weaviate:8080
    depends_on:
      - redis
      - postgres
      - weaviate
    volumes:
      - sophia_logs:/app/logs
      - sophia_data:/app/data
    networks:
      - sophia_network
      - shared_network
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Artemis Command Center
  artemis-orchestrator:
    build:
      context: .
      dockerfile: docker/Dockerfile.artemis
    ports:
      - "8000:8000"
      - "8001:8001" # API port
      - "8002:8002" # WebSocket port
    environment:
      - ARTEMIS_PORT=8000
      - ARTEMIS_API_PORT=8001
      - ARTEMIS_WS_PORT=8002
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://user:pass@postgres:5432/artemis_db
      - WEAVIATE_URL=http://weaviate:8080
    depends_on:
      - redis
      - postgres
      - weaviate
    volumes:
      - artemis_logs:/app/logs
      - artemis_data:/app/data
    networks:
      - artemis_network
      - shared_network
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # MCP Gateway (Shared Infrastructure)
  mcp-gateway:
    build:
      context: ./dev-mcp-unified
      dockerfile: Dockerfile
    ports:
      - "3333:3333"
      - "3334:3334" # Admin interface
      - "3335:3335" # Monitoring
    environment:
      - MCP_PORT=3333
      - MCP_ADMIN_PORT=3334
      - MCP_MONITOR_PORT=3335
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    volumes:
      - mcp_data:/app/data
    networks:
      - shared_network
    deploy:
      replicas: 1
      resources:
        limits:
          memory: 1G
          cpus: "0.5"

  # Shared Infrastructure Services
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - shared_network
    deploy:
      resources:
        limits:
          memory: 512M

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: dual_orchestrator
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init:/docker-entrypoint-initdb.d
    networks:
      - shared_network

  weaviate:
    image: semitechnologies/weaviate:1.22.4
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "false"
      PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
      DEFAULT_VECTORIZER_MODULE: "none"
      CLUSTER_HOSTNAME: "node1"
    volumes:
      - weaviate_data:/var/lib/weaviate
    networks:
      - shared_network

  # Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - sophia-orchestrator
      - artemis-orchestrator
      - mcp-gateway
    networks:
      - shared_network

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - shared_network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
    networks:
      - shared_network

networks:
  sophia_network:
    driver: bridge
  artemis_network:
    driver: bridge
  shared_network:
    driver: bridge

volumes:
  sophia_logs:
  sophia_data:
  artemis_logs:
  artemis_data:
  mcp_data:
  redis_data:
  postgres_data:
  weaviate_data:
  prometheus_data:
  grafana_data:
```

#### **Load Balancing and Failover Configuration**

```nginx
# nginx/nginx.conf
upstream sophia_backend {
    least_conn;
    server sophia-orchestrator:9000 max_fails=3 fail_timeout=30s;
    server sophia-orchestrator:9000 max_fails=3 fail_timeout=30s backup;
}

upstream artemis_backend {
    least_conn;
    server artemis-orchestrator:8000 max_fails=3 fail_timeout=30s;
    server artemis-orchestrator:8000 max_fails=3 fail_timeout=30s backup;
}

upstream mcp_backend {
    server mcp-gateway:3333 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name sophia.local;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=sophia_api:10m rate=10r/s;

    location / {
        limit_req zone=sophia_api burst=20 nodelay;
        proxy_pass http://sophia_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Health check bypass
        proxy_next_upstream error timeout http_502 http_503 http_504;
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }

    location /ws {
        proxy_pass http://sophia_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name artemis.local;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=artemis_api:10m rate=10r/s;

    location / {
        limit_req zone=artemis_api burst=20 nodelay;
        proxy_pass http://artemis_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Health check bypass
        proxy_next_upstream error timeout http_502 http_503 http_504;
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }
}

server {
    listen 80;
    server_name mcp.local;

    location / {
        proxy_pass http://mcp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 8. MONITORING AND OBSERVABILITY

#### **Comprehensive Monitoring Architecture**

```python
# Monitoring and Observability System
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
import json
from prometheus_client import Counter, Histogram, Gauge, start_http_server

@dataclass
class MetricPoint:
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    metric_type: str  # 'counter', 'gauge', 'histogram'

class OrchestatorMetrics:
    """Metrics collection for dual orchestrator system"""

    def __init__(self, domain: str):
        self.domain = domain

        # Request metrics
        self.request_counter = Counter(
            f'{domain}_requests_total',
            'Total requests processed',
            ['endpoint', 'method', 'status']
        )

        self.request_duration = Histogram(
            f'{domain}_request_duration_seconds',
            'Request processing duration',
            ['endpoint', 'method']
        )

        # Orchestration metrics
        self.active_sessions = Gauge(
            f'{domain}_active_sessions',
            'Number of active conversation sessions'
        )

        self.cross_domain_collaborations = Counter(
            f'{domain}_cross_domain_collaborations_total',
            'Cross-domain collaboration requests',
            ['target_domain', 'request_type', 'status']
        )

        # System health metrics
        self.system_health = Gauge(
            f'{domain}_system_health',
            'System health score (0-100)'
        )

        self.error_rate = Gauge(
            f'{domain}_error_rate',
            'Error rate percentage'
        )

    def record_request(
        self,
        endpoint: str,
        method: str,
        status: int,
        duration: float
    ) -> None:
        """Record request metrics"""
        self.request_counter.labels(
            endpoint=endpoint,
            method=method,
            status=str(status)
        ).inc()

        self.request_duration.labels(
            endpoint=endpoint,
            method=method
        ).observe(duration)

    def record_collaboration(
        self,
        target_domain: str,
        request_type: str,
        status: str
    ) -> None:
        """Record cross-domain collaboration"""
        self.cross_domain_collaborations.labels(
            target_domain=target_domain,
            request_type=request_type,
            status=status
        ).inc()

    def update_system_health(self, health_score: float) -> None:
        """Update system health score"""
        self.system_health.set(health_score)

class HealthMonitor:
    """Health monitoring for orchestrator components"""

    def __init__(self, domain: str):
        self.domain = domain
        self.health_checks = {}
        self.is_running = False

    def register_health_check(
        self,
        name: str,
        check_func: callable,
        interval: int = 60
    ) -> None:
        """Register health check function"""
        self.health_checks[name] = {
            'func': check_func,
            'interval': interval,
            'last_run': None,
            'last_result': None
        }

    async def start_monitoring(self) -> None:
        """Start health monitoring loop"""
        self.is_running = True
        while self.is_running:
            for name, check in self.health_checks.items():
                try:
                    result = await check['func']()
                    check['last_result'] = result
                    check['last_run'] = datetime.utcnow()
                except Exception as e:
                    check['last_result'] = {
                        'status': 'error',
                        'error': str(e),
                        'timestamp': datetime.utcnow()
                    }

                await asyncio.sleep(check['interval'])

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        status = {
            'domain': self.domain,
            'overall_status': 'healthy',
            'checks': {},
            'timestamp': datetime.utcnow()
        }

        for name, check in self.health_checks.items():
            if check['last_result']:
                status['checks'][name] = check['last_result']
                if check['last_result'].get('status') != 'healthy':
                    status['overall_status'] = 'unhealthy'

        return status

# Example health check functions
async def database_health_check() -> Dict[str, Any]:
    """Check database connectivity"""
    try:
        # Simulate database check
        await asyncio.sleep(0.1)
        return {
            'status': 'healthy',
            'response_time_ms': 100,
            'timestamp': datetime.utcnow()
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow()
        }

async def vector_store_health_check() -> Dict[str, Any]:
    """Check vector store connectivity"""
    try:
        # Simulate vector store check
        await asyncio.sleep(0.1)
        return {
            'status': 'healthy',
            'response_time_ms': 50,
            'timestamp': datetime.utcnow()
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow()
        }
```

---

## 🔧 IMPLEMENTATION PATTERNS

### Interface Definitions

```python
# Core interface definitions for dual orchestrator system
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

@dataclass
class OrchestratorResponse:
    content: str
    metadata: Dict[str, Any]
    domain: str
    confidence_score: float
    collaboration_needed: bool = False
    collaboration_target: Optional[str] = None

class DualOrchestrator(ABC):
    """Base interface for both Sophia and Artemis orchestrators"""

    @abstractmethod
    async def process_request(
        self,
        request: str,
        context: Dict[str, Any]
    ) -> OrchestratorResponse:
        """Process incoming request"""
        pass

    @abstractmethod
    async def collaborate(
        self,
        target_domain: str,
        request_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collaborate with other domain"""
        pass

    @abstractmethod
    async def get_health_status(self) -> Dict[str, Any]:
        """Get orchestrator health status"""
        pass

class SophiaOrchestrator(DualOrchestrator):
    """Sophia business intelligence orchestrator"""

    async def process_business_request(
        self,
        request: str,
        business_context: Dict[str, Any]
    ) -> OrchestratorResponse:
        """Process business-focused request"""
        pass

class ArtemisOrchestrator(DualOrchestrator):
    """Artemis technical operations orchestrator"""

    async def process_technical_request(
        self,
        request: str,
        technical_context: Dict[str, Any]
    ) -> OrchestratorResponse:
        """Process technical-focused request"""
        pass
```

### Error Handling and Circuit Breaker Patterns

```python
# Circuit Breaker Implementation
from enum import Enum
from datetime import datetime, timedelta
import asyncio

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker for cross-domain communication"""

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: int = 60,
        success_threshold: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = timedelta(seconds=reset_timeout)
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e

    async def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    async def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time:
            return datetime.utcnow() - self.last_failure_time >= self.reset_timeout
        return False

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass
```

---

## 📊 PERFORMANCE SPECIFICATIONS

### Scalability Targets

- **Request Processing**: 1000+ requests/second per domain
- **Cross-Domain Collaboration**: <500ms latency
- **Vector Store Queries**: <100ms average response time
- **Session Management**: Support for 10,000+ concurrent sessions
- **Memory Usage**: <2GB per orchestrator instance
- **CPU Usage**: <80% under normal load

### Availability Requirements

- **System Uptime**: 99.9% availability target
- **Failover Time**: <30 seconds automatic failover
- **Data Consistency**: Eventually consistent across domains
- **Backup Strategy**: Real-time replication with 15-minute RPO

---

## 🚀 DEPLOYMENT ROADMAP

### Phase 1: Core Infrastructure (Weeks 1-2)

- Set up event bus (Redis/NATS)
- Implement vector store partitioning
- Create authentication system
- Deploy container orchestration

### Phase 2: Domain Orchestrators (Weeks 3-4)

- Implement Sophia business orchestrator
- Implement Artemis technical orchestrator
- Create cross-domain communication
- Add monitoring and health checks

### Phase 3: Integration Layer (Weeks 5-6)

- Platform integration abstractions
- Configuration management system
- Security and rate limiting
- Load balancing and failover

### Phase 4: Optimization & Monitoring (Weeks 7-8)

- Performance tuning
- Advanced monitoring dashboards
- Error handling improvements
- Documentation completion

---

## 💡 KEY ARCHITECTURAL INSIGHTS

1. **Event-Driven Architecture**: Enables loose coupling between domains while maintaining real-time collaboration capabilities.

2. **Domain-Specific Vector Stores**: Partitioned knowledge bases improve query performance and maintain domain context isolation.

3. **Circuit Breaker Pattern**: Prevents cascading failures during cross-domain communication outages.

4. **Shared Infrastructure**: Reduces operational overhead while maintaining domain separation at the application layer.

5. **Container Orchestration**: Provides independent scaling, deployment, and management of domain-specific services.

This architecture provides a robust foundation for the dual AI orchestrator system, enabling both domain specialization and cross-domain collaboration while maintaining high availability, security, and performance standards.
