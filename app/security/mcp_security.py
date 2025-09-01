"""
MCP Security Framework
Enterprise-grade security for MCP server operations
"""

import hashlib
import hmac
import json
import secrets
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import jwt
import redis.asyncio as redis
from cryptography.fernet import Fernet
import base64
import logging
from dataclasses import dataclass
from enum import Enum
from app.core.circuit_breaker import with_circuit_breaker, get_llm_circuit_breaker, get_weaviate_circuit_breaker, get_redis_circuit_breaker, get_webhook_circuit_breaker

logger = logging.getLogger(__name__)

class Permission(Enum):
    """MCP permissions"""
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"
    SEARCH = "search"
    ADMIN = "admin"
    METRICS_READ = "metrics:read"
    CONFIG_WRITE = "config:write"

@dataclass
class Session:
    """MCP session data"""
    assistant_id: str
    token: str
    permissions: List[Permission]
    created_at: datetime
    expires_at: datetime
    metadata: Dict[str, Any]

class SecurityError(Exception):
    """Base security exception"""

class AuthenticationError(SecurityError):
    """Authentication failed"""

class AuthorizationError(SecurityError):
    """Authorization failed"""

class TokenExpiredError(SecurityError):
    """Token has expired"""

class RateLimitError(SecurityError):
    """Rate limit exceeded"""

class MCPSecurityFramework:
    """
    Enterprise security framework for MCP operations
    Handles authentication, authorization, encryption, and audit logging
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        # Generate or load keys
        self.encryption_key = self._get_or_create_key("encryption")
        self.signing_key = self._get_or_create_key("signing")
        
        # JWT configuration
        self.jwt_secret = self._get_or_create_key("jwt")
        self.jwt_algorithm = "HS256"
        self.token_ttl = 3600  # 1 hour
        self.refresh_ttl = 86400 * 7  # 7 days
        
        # Fernet cipher for encryption
        self.cipher = Fernet(self.encryption_key)
        
        # Redis for session management
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        
        # Rate limiting configuration
        self.rate_limits = {
            "default": {"requests": 100, "window": 60},  # 100 req/min
            "search": {"requests": 50, "window": 60},     # 50 searches/min
            "write": {"requests": 20, "window": 60},      # 20 writes/min
        }
        
        # Audit log
        self.audit_enabled = True
        
    async def initialize(self):
        """Initialize Redis connection"""
        if not self.redis:
            self.redis = redis.Redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Security framework initialized")
    
    def _get_or_create_key(self, key_type: str) -> bytes:
        """Get or create encryption/signing key"""
        # In production, load from secure key management service
        # For now, generate deterministic keys (REPLACE IN PRODUCTION!)
        seed = f"sophia-mcp-{key_type}-key-2024"
        if key_type == "encryption":
            # Fernet requires base64-encoded 32-byte key
            key = base64.urlsafe_b64encode(hashlib.sha256(seed.encode()).digest())
        else:
            key = hashlib.sha256(seed.encode()).digest()
        return key
    
    def _get_permissions(self, assistant_id: str) -> List[Permission]:
        """Get permissions for an assistant"""
        # Default permissions (customize based on assistant type)
        default_permissions = [
            Permission.MEMORY_READ,
            Permission.MEMORY_WRITE,
            Permission.SEARCH,
        ]
        
        # Special permissions for specific assistants
        if assistant_id == "admin-claude":
            default_permissions.extend([
                Permission.ADMIN,
                Permission.CONFIG_WRITE,
                Permission.MEMORY_DELETE,
            ])
        
        return default_permissions
    
    @with_circuit_breaker("redis")
    async def generate_assistant_token(
        self,
        assistant_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate time-limited, signed token for assistant
        Returns both access and refresh tokens
        """
        if not self.redis:
            await self.initialize()
        
        # Create session ID
        session_id = secrets.token_urlsafe(32)
        
        # Get permissions
        permissions = self._get_permissions(assistant_id)
        
        # Create JWT payload
        now = datetime.utcnow()
        access_payload = {
            "session_id": session_id,
            "assistant_id": assistant_id,
            "permissions": [p.value for p in permissions],
            "iat": now.timestamp(),
            "exp": (now + timedelta(seconds=self.token_ttl)).timestamp(),
            "type": "access"
        }
        
        refresh_payload = {
            "session_id": session_id,
            "assistant_id": assistant_id,
            "iat": now.timestamp(),
            "exp": (now + timedelta(seconds=self.refresh_ttl)).timestamp(),
            "type": "refresh"
        }
        
        # Generate tokens
        access_token = jwt.encode(access_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        refresh_token = jwt.encode(refresh_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        # Store session in Redis
        session_data = {
            "assistant_id": assistant_id,
            "permissions": [p.value for p in permissions],
            "created_at": now.isoformat(),
            "metadata": metadata or {},
            "active": True
        }
        
        await self.redis.setex(
            f"session:{session_id}",
            self.token_ttl,
            json.dumps(session_data)
        )
        
        # Audit log
        await self._audit_log("token_generated", {
            "assistant_id": assistant_id,
            "session_id": session_id,
            "permissions": [p.value for p in permissions]
        })
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": self.token_ttl,
            "session_id": session_id
        }
    
    @with_circuit_breaker("redis")
    async def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decrypt assistant token"""
        if not self.redis:
            await self.initialize()
        
        try:
            # Decode JWT
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            
            # Check token type
            if payload.get("type") != "access":
                raise AuthenticationError("Invalid token type")
            
            # Check session exists and is active
            session_data = await self.redis.get(f"session:{payload['session_id']}")
            if not session_data:
                raise AuthenticationError("Session not found")
            
            session = json.loads(session_data)
            if not session.get("active"):
                raise AuthenticationError("Session inactive")
            
            # Update session TTL
            await self.redis.expire(f"session:{payload['session_id']}", self.token_ttl)
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise AuthenticationError(f"Invalid token: {e}")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Refresh an access token using refresh token"""
        if not self.redis:
            await self.initialize()
        
        try:
            # Decode refresh token
            payload = jwt.decode(
                refresh_token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            
            # Check token type
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid refresh token")
            
            # Generate new access token
            return await self.generate_assistant_token(
                assistant_id=payload["assistant_id"],
                metadata={"refreshed_from": payload["session_id"]}
            )
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Refresh token has expired")
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise AuthenticationError(f"Token refresh failed: {e}")
    
    async def check_permission(
        self,
        token_payload: Dict,
        required_permission: Permission
    ) -> bool:
        """Check if token has required permission"""
        permissions = token_payload.get("permissions", [])
        return required_permission.value in permissions or Permission.ADMIN.value in permissions
    
    async def check_rate_limit(
        self,
        assistant_id: str,
        operation: str = "default"
    ) -> bool:
        """Check if request is within rate limits"""
        if not self.redis:
            await self.initialize()
        
        limits = self.rate_limits.get(operation, self.rate_limits["default"])
        
        # Create rate limit key
        window = int(time.time() // limits["window"])
        key = f"rate_limit:{assistant_id}:{operation}:{window}"
        
        # Increment counter
        current = await self.redis.incr(key)
        
        # Set expiry on first request
        if current == 1:
            await self.redis.expire(key, limits["window"])
        
        # Check limit
        if current > limits["requests"]:
            await self._audit_log("rate_limit_exceeded", {
                "assistant_id": assistant_id,
                "operation": operation,
                "limit": limits["requests"],
                "current": current
            })
            return False
        
        return True
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_data(self, encrypted: str) -> str:
        """Decrypt sensitive data"""
        encrypted_bytes = base64.b64decode(encrypted)
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return decrypted.decode()
    
    def sign_data(self, data: str) -> str:
        """Sign data with HMAC"""
        signature = hmac.new(
            self.signing_key,
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_signature(self, data: str, signature: str) -> bool:
        """Verify HMAC signature"""
        expected = self.sign_data(data)
        return hmac.compare_digest(expected, signature)
    
    async def _audit_log(self, event: str, data: Dict[str, Any]):
        """Log security events for audit trail"""
        if not self.audit_enabled:
            return
        
        if not self.redis:
            await self.initialize()
        
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "data": data
        }
        
        # Store in Redis list (keep last 10000 entries)
        await self.redis.lpush("audit_log", json.dumps(audit_entry))
        await self.redis.ltrim("audit_log", 0, 9999)
        
        # Also log to standard logger
        logger.info(f"AUDIT: {event} - {json.dumps(data)}")
    
    @with_circuit_breaker("redis")
    async def revoke_session(self, session_id: str):
        """Revoke a session"""
        if not self.redis:
            await self.initialize()
        
        # Mark session as inactive
        session_data = await self.redis.get(f"session:{session_id}")
        if session_data:
            session = json.loads(session_data)
            session["active"] = False
            await self.redis.setex(
                f"session:{session_id}",
                300,  # Keep for 5 minutes for audit
                json.dumps(session)
            )
        
        await self._audit_log("session_revoked", {"session_id": session_id})
    
    @with_circuit_breaker("redis")
    async def get_active_sessions(self, assistant_id: Optional[str] = None) -> List[Dict]:
        """Get list of active sessions"""
        if not self.redis:
            await self.initialize()
        
        sessions = []
        pattern = "session:*"
        
        async for key in self.redis.scan_iter(match=pattern):
            session_data = await self.redis.get(key)
            if session_data:
                session = json.loads(session_data)
                if session.get("active"):
                    if not assistant_id or session["assistant_id"] == assistant_id:
                        session["session_id"] = key.split(":")[-1]
                        sessions.append(session)
        
        return sessions


class SecurityMiddleware:
    """FastAPI middleware for security"""
    
    def __init__(self, security: MCPSecurityFramework):
        self.security = security
    
    async def __call__(self, request, call_next):
        """Process request with security checks"""
        # Extract token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Missing or invalid authorization header"}
            )
        
        token = auth_header.replace("Bearer ", "")
        
        try:
            # Verify token
            payload = await self.security.verify_token(token)
            if not payload:
                raise AuthenticationError("Invalid token")
            
            # Check rate limit
            if not await self.security.check_rate_limit(
                payload["assistant_id"],
                request.url.path.split("/")[-1]
            ):
                raise RateLimitError("Rate limit exceeded")
            
            # Add session info to request
            request.state.session = payload
            
            # Process request
            response = await call_next(request)
            
            # Audit successful request
            await self.security._audit_log("request_success", {
                "assistant_id": payload["assistant_id"],
                "path": str(request.url.path),
                "method": request.method
            })
            
            return response
            
        except TokenExpiredError:
            return JSONResponse(status_code=401, content={"error": "Token expired"})
        except RateLimitError:
            return JSONResponse(status_code=429, content={"error": "Rate limit exceeded"})
        except AuthenticationError as e:
            return JSONResponse(status_code=401, content={"error": str(e)})
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(status_code=500, content={"error": "Internal security error"})