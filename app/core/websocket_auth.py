"""
WebSocket Authentication System
Handles JWT token validation, user permissions, tenant isolation, and session management
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import jwt
import redis.asyncio as aioredis
from fastapi import HTTPException, WebSocket
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """User role definitions"""

    ADMIN = "admin"
    SOPHIA_OPERATOR = "sophia_operator"
    PAY_READY_ANALYST = "pay_ready_analyst"
    ARTEMIS_OPERATOR = "artemis_operator"
    VIEWER = "viewer"
    GUEST = "guest"


class TenantType(str, Enum):
    """Tenant type definitions"""

    ENTERPRISE = "enterprise"
    PAY_READY = "pay_ready"
    SOPHIA_INTEL = "sophia_intel"
    ARTEMIS_TACTICAL = "artemis_tactical"
    SHARED = "shared"


@dataclass
class AuthenticatedUser:
    """Authenticated user information"""

    user_id: str
    username: str
    email: str
    role: UserRole
    tenant_id: str
    tenant_type: TenantType
    permissions: set[str]
    session_id: str
    expires_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class SessionInfo:
    """WebSocket session information"""

    session_id: str
    user: AuthenticatedUser
    websocket: WebSocket
    created_at: datetime
    last_heartbeat: datetime
    subscriptions: set[str]
    is_active: bool = True


class WebSocketAuthenticator:
    """
    Handles WebSocket authentication, authorization, and session management
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        token_expiry_minutes: int = 60,
        session_timeout_minutes: int = 30,
        redis_url: str = "redis://localhost:6379",
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expiry_minutes = token_expiry_minutes
        self.session_timeout_minutes = session_timeout_minutes

        # Active sessions
        self.active_sessions: dict[str, SessionInfo] = {}

        # Tenant permissions mapping
        self.tenant_permissions = {
            TenantType.PAY_READY: {
                "view_pay_ready_data",
                "manage_pay_ready_accounts",
                "view_stuck_accounts",
                "manage_pay_ready_workflows",
            },
            TenantType.SOPHIA_INTEL: {
                "view_sophia_intelligence",
                "manage_sophia_operations",
                "view_team_performance",
                "access_operational_insights",
            },
            TenantType.ARTEMIS_TACTICAL: {
                "view_artemis_operations",
                "manage_artemis_swarms",
                "access_tactical_data",
                "deploy_artemis_agents",
            },
            TenantType.ENTERPRISE: {
                "view_all_data",
                "manage_all_operations",
                "admin_access",
                "cross_tenant_access",
            },
        }

        # Role permissions mapping
        self.role_permissions = {
            UserRole.ADMIN: {"*"},  # All permissions
            UserRole.SOPHIA_OPERATOR: {
                "view_sophia_intelligence",
                "manage_sophia_operations",
                "view_team_performance",
                "access_operational_insights",
                "view_system_metrics",
            },
            UserRole.PAY_READY_ANALYST: {
                "view_pay_ready_data",
                "manage_pay_ready_accounts",
                "view_stuck_accounts",
                "manage_pay_ready_workflows",
                "view_system_metrics",
            },
            UserRole.ARTEMIS_OPERATOR: {
                "view_artemis_operations",
                "manage_artemis_swarms",
                "access_tactical_data",
                "deploy_artemis_agents",
                "view_system_metrics",
            },
            UserRole.VIEWER: {"view_public_data", "view_system_metrics"},
            UserRole.GUEST: {"view_public_data"},
        }

        # Initialize Redis for distributed session management
        self.redis: Optional[aioredis.Redis] = None
        self.redis_url = redis_url

    async def initialize(self):
        """Initialize the authenticator"""
        try:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("WebSocket authenticator initialized with Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory sessions: {e}")
            self.redis = None

    async def authenticate_websocket(
        self, websocket: WebSocket, token: Optional[str] = None, client_id: Optional[str] = None
    ) -> AuthenticatedUser:
        """
        Authenticate WebSocket connection

        Args:
            websocket: WebSocket connection
            token: JWT authentication token
            client_id: Optional client identifier

        Returns:
            AuthenticatedUser if authentication succeeds

        Raises:
            HTTPException: If authentication fails
        """
        if not token:
            # Try to get token from query parameters
            query_params = dict(websocket.query_params)
            token = query_params.get("token")

        if not token:
            # Try to get token from headers
            headers = dict(websocket.headers)
            auth_header = headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]

        if not token:
            raise HTTPException(status_code=401, detail="Authentication token required")

        try:
            # Decode and validate JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Extract user information
            user_id = payload.get("user_id")
            username = payload.get("username")
            email = payload.get("email")
            role = UserRole(payload.get("role", "guest"))
            tenant_id = payload.get("tenant_id")
            tenant_type = TenantType(payload.get("tenant_type", "shared"))
            session_id = payload.get("session_id")
            expires_at = datetime.fromtimestamp(payload.get("exp"))

            if not all([user_id, username, tenant_id, session_id]):
                raise HTTPException(status_code=401, detail="Invalid token payload")

            # Check token expiration
            if expires_at < datetime.utcnow():
                raise HTTPException(status_code=401, detail="Token expired")

            # Get user permissions
            permissions = self._get_user_permissions(role, tenant_type)

            # Get client IP and user agent
            client_host = None
            user_agent = None
            if hasattr(websocket, "client") and websocket.client:
                client_host = websocket.client.host
            if hasattr(websocket, "headers"):
                user_agent = dict(websocket.headers).get("user-agent")

            user = AuthenticatedUser(
                user_id=user_id,
                username=username,
                email=email,
                role=role,
                tenant_id=tenant_id,
                tenant_type=tenant_type,
                permissions=permissions,
                session_id=session_id,
                expires_at=expires_at,
                last_activity=datetime.utcnow(),
                ip_address=client_host,
                user_agent=user_agent,
            )

            # Validate session if exists
            await self._validate_session(user)

            logger.info(f"WebSocket authenticated: {username} ({user_id}) from {client_host}")
            return user

        except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")

    def _get_user_permissions(self, role: UserRole, tenant_type: TenantType) -> set[str]:
        """Get user permissions based on role and tenant"""
        permissions = set()

        # Get role permissions
        role_perms = self.role_permissions.get(role, set())
        if "*" in role_perms:
            # Admin has all permissions
            permissions = {"*"}
        else:
            permissions.update(role_perms)

        # Add tenant-specific permissions
        tenant_perms = self.tenant_permissions.get(tenant_type, set())
        permissions.update(tenant_perms)

        return permissions

    async def check_permission(self, user: AuthenticatedUser, required_permission: str) -> bool:
        """
        Check if user has required permission

        Args:
            user: Authenticated user
            required_permission: Required permission string

        Returns:
            True if user has permission
        """
        if "*" in user.permissions:
            return True

        return required_permission in user.permissions

    async def check_tenant_access(
        self, user: AuthenticatedUser, resource_tenant_id: str, resource_type: Optional[str] = None
    ) -> bool:
        """
        Check if user can access resource from specific tenant

        Args:
            user: Authenticated user
            resource_tenant_id: Tenant ID of the resource
            resource_type: Optional resource type for fine-grained control

        Returns:
            True if access allowed
        """
        # Admin and enterprise tenants have cross-tenant access
        if (
            user.role == UserRole.ADMIN
            or user.tenant_type == TenantType.ENTERPRISE
            or "cross_tenant_access" in user.permissions
        ):
            return True

        # Same tenant access
        if user.tenant_id == resource_tenant_id:
            return True

        # Pay Ready specific isolation - very strict
        if resource_type and "pay_ready" in resource_type.lower():
            if user.tenant_type != TenantType.PAY_READY:
                logger.warning(
                    f"Denied Pay Ready access to user {user.username} "
                    f"from tenant {user.tenant_id}"
                )
                return False

        return False

    async def create_session(self, user: AuthenticatedUser, websocket: WebSocket) -> SessionInfo:
        """Create new WebSocket session"""
        session = SessionInfo(
            session_id=user.session_id,
            user=user,
            websocket=websocket,
            created_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow(),
            subscriptions=set(),
            is_active=True,
        )

        self.active_sessions[user.session_id] = session

        # Store in Redis for distributed systems
        if self.redis:
            session_data = {
                "user_id": user.user_id,
                "username": user.username,
                "tenant_id": user.tenant_id,
                "tenant_type": user.tenant_type.value,
                "role": user.role.value,
                "created_at": session.created_at.isoformat(),
                "last_heartbeat": session.last_heartbeat.isoformat(),
                "ip_address": user.ip_address or "",
                "user_agent": user.user_agent or "",
            }

            await self.redis.hset(f"websocket_session:{user.session_id}", mapping=session_data)
            await self.redis.expire(
                f"websocket_session:{user.session_id}", self.session_timeout_minutes * 60
            )

        logger.info(f"Created WebSocket session: {user.session_id} for {user.username}")
        return session

    async def validate_session(self, session_id: str) -> Optional[SessionInfo]:
        """Validate existing session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None

        # Check if session expired
        if not session.is_active:
            return None

        timeout = timedelta(minutes=self.session_timeout_minutes)
        if datetime.utcnow() - session.last_heartbeat > timeout:
            session.is_active = False
            logger.info(f"Session expired: {session_id}")
            return None

        return session

    async def update_session_heartbeat(self, session_id: str):
        """Update session last activity"""
        session = self.active_sessions.get(session_id)
        if session:
            session.last_heartbeat = datetime.utcnow()
            session.user.last_activity = datetime.utcnow()

            # Update in Redis
            if self.redis:
                await self.redis.hset(
                    f"websocket_session:{session_id}",
                    "last_heartbeat",
                    session.last_heartbeat.isoformat(),
                )

    async def close_session(self, session_id: str):
        """Close WebSocket session"""
        session = self.active_sessions.get(session_id)
        if session:
            session.is_active = False

            try:
                if session.websocket.client_state.name != "DISCONNECTED":
                    await session.websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")

            # Remove from active sessions
            del self.active_sessions[session_id]

            # Remove from Redis
            if self.redis:
                await self.redis.delete(f"websocket_session:{session_id}")

            logger.info(f"Closed WebSocket session: {session_id}")

    async def _validate_session(self, user: AuthenticatedUser):
        """Validate session against Redis if available"""
        if not self.redis:
            return

        try:
            session_data = await self.redis.hgetall(f"websocket_session:{user.session_id}")
            if session_data:
                # Validate session data matches user
                if (
                    session_data.get("user_id") != user.user_id
                    or session_data.get("tenant_id") != user.tenant_id
                ):
                    raise HTTPException(status_code=401, detail="Session validation failed")
        except Exception as e:
            logger.error(f"Session validation error: {e}")

    async def refresh_token(self, user: AuthenticatedUser) -> str:
        """Generate refreshed JWT token"""
        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.token_expiry_minutes)

        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "tenant_id": user.tenant_id,
            "tenant_type": user.tenant_type.value,
            "session_id": user.session_id,
            "iat": now,
            "exp": expires,
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        user.expires_at = expires

        logger.info(f"Refreshed token for user: {user.username}")
        return token

    def get_session_metrics(self) -> dict[str, Any]:
        """Get session metrics"""
        active_count = len([s for s in self.active_sessions.values() if s.is_active])

        tenant_breakdown = {}
        role_breakdown = {}

        for session in self.active_sessions.values():
            if session.is_active:
                tenant = session.user.tenant_type.value
                tenant_breakdown[tenant] = tenant_breakdown.get(tenant, 0) + 1

                role = session.user.role.value
                role_breakdown[role] = role_breakdown.get(role, 0) + 1

        return {
            "total_sessions": len(self.active_sessions),
            "active_sessions": active_count,
            "tenant_breakdown": tenant_breakdown,
            "role_breakdown": role_breakdown,
            "session_timeout_minutes": self.session_timeout_minutes,
        }

    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        expired_sessions = []
        timeout = timedelta(minutes=self.session_timeout_minutes)

        for session_id, session in self.active_sessions.items():
            if datetime.utcnow() - session.last_heartbeat > timeout or not session.is_active:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            await self.close_session(session_id)

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    async def start_cleanup_task(self):
        """Start background task for cleaning up expired sessions"""

        async def cleanup_loop():
            while True:
                try:
                    await self.cleanup_expired_sessions()
                    await asyncio.sleep(300)  # Run every 5 minutes
                except Exception as e:
                    logger.error(f"Error in session cleanup: {e}")
                    await asyncio.sleep(60)  # Retry in 1 minute

        asyncio.create_task(cleanup_loop())
        logger.info("Started session cleanup task")
