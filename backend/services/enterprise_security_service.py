# Enterprise Security Service for Sophia AI V9.7
# Implements zero-defect security with MFA, RBAC, and enterprise-grade encryption

import os
import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
import pyotp
import qrcode
from io import BytesIO
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import redis
import logging
from pydantic import BaseModel, EmailStr

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityConfig:
    """Enterprise security configuration"""

    SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    MFA_ISSUER = "Sophia AI Enterprise"
    ENCRYPTION_PASSWORD = os.getenv("ENCRYPTION_PASSWORD", secrets.token_urlsafe(32))
    ENCRYPTION_SALT = os.getenv("ENCRYPTION_SALT", secrets.token_urlsafe(16))

    # Security policies
    PASSWORD_MIN_LENGTH = 12
    PASSWORD_REQUIRE_SPECIAL = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_UPPERCASE = True
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30

class UserRole(BaseModel):
    """User role definition"""
    name: str
    permissions: List[str]
    description: str

class User(BaseModel):
    """User model"""
    id: str
    email: EmailStr
    username: str
    role: str
    is_active: bool = True
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None

class EnterpriseSecurityService:
    """Enterprise-grade security service for Sophia AI"""

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)

        # Initialize encryption
        self._init_encryption()

        # Initialize RBAC
        self._init_rbac()

        # Initialize security monitoring
        self._init_security_monitoring()

    def _init_encryption(self):
        """Initialize encryption service"""
        password = SecurityConfig.ENCRYPTION_PASSWORD.encode()
        salt = SecurityConfig.ENCRYPTION_SALT.encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password))
        self.cipher_suite = Fernet(key)

    def _init_rbac(self):
        """Initialize Role-Based Access Control"""
        self.roles = {
            "admin": UserRole(
                name="admin",
                permissions=[
                    "read", "write", "delete", "manage_users", "manage_system",
                    "view_analytics", "manage_security", "deploy", "configure"
                ],
                description="Full system administrator"
            ),
            "developer": UserRole(
                name="developer", 
                permissions=[
                    "read", "write", "deploy", "view_analytics", "debug",
                    "manage_code", "access_logs"
                ],
                description="Software developer with deployment rights"
            ),
            "analyst": UserRole(
                name="analyst",
                permissions=[
                    "read", "query", "export", "view_analytics", "create_reports"
                ],
                description="Data analyst with read and analytics access"
            ),
            "viewer": UserRole(
                name="viewer",
                permissions=["read", "view_analytics"],
                description="Read-only access to system"
            )
        }

    def _init_security_monitoring(self):
        """Initialize security monitoring and alerting"""
        self.security_events = []
        self.threat_indicators = {
            "failed_logins": {},
            "suspicious_ips": set(),
            "unusual_access_patterns": {}
        }

    # Authentication Methods

    async def authenticate_user(self, username: str, password: str, mfa_token: Optional[str] = None) -> Optional[User]:
        """Authenticate user with optional MFA"""
        try:
            # Get user from database
            user = await self.get_user_by_username(username)
            if not user:
                await self._log_security_event("failed_login", {"username": username, "reason": "user_not_found"})
                return None

            # Check if account is locked
            if user.locked_until and user.locked_until > datetime.utcnow():
                await self._log_security_event("login_attempt_locked", {"username": username})
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"Account locked until {user.locked_until}"
                )

            # Verify password
            if not self.verify_password(password, user.hashed_password):
                await self._handle_failed_login(user)
                return None

            # Verify MFA if enabled
            if user.mfa_enabled:
                if not mfa_token:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="MFA token required"
                    )

                if not self.verify_mfa_token(user.mfa_secret, mfa_token):
                    await self._handle_failed_login(user)
                    return None

            # Reset failed attempts on successful login
            await self._reset_failed_attempts(user)

            # Update last login
            user.last_login = datetime.utcnow()
            await self.update_user(user)

            await self._log_security_event("successful_login", {"username": username})
            return user

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            await self._log_security_event("authentication_error", {"username": username, "error": str(e)})
            return None

    async def _handle_failed_login(self, user: User):
        """Handle failed login attempt"""
        user.failed_login_attempts += 1

        if user.failed_login_attempts >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=SecurityConfig.LOCKOUT_DURATION_MINUTES)
            await self._log_security_event("account_locked", {"username": user.username})

        await self.update_user(user)
        await self._log_security_event("failed_login", {"username": user.username, "attempts": user.failed_login_attempts})

    async def _reset_failed_attempts(self, user: User):
        """Reset failed login attempts"""
        user.failed_login_attempts = 0
        user.locked_until = None
        await self.update_user(user)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return self.pwd_context.hash(password)

    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password meets security requirements"""
        issues = []

        if len(password) < SecurityConfig.PASSWORD_MIN_LENGTH:
            issues.append(f"Password must be at least {SecurityConfig.PASSWORD_MIN_LENGTH} characters")

        if SecurityConfig.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")

        if SecurityConfig.PASSWORD_REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")

        if SecurityConfig.PASSWORD_REQUIRE_SPECIAL and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "strength_score": self._calculate_password_strength(password)
        }

    def _calculate_password_strength(self, password: str) -> float:
        """Calculate password strength score (0-1)"""
        score = 0.0

        # Length score
        score += min(len(password) / 20, 0.3)

        # Character variety score
        if any(c.islower() for c in password):
            score += 0.1
        if any(c.isupper() for c in password):
            score += 0.1
        if any(c.isdigit() for c in password):
            score += 0.1
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 0.2

        # Entropy score
        unique_chars = len(set(password))
        score += min(unique_chars / len(password), 0.2)

        return min(score, 1.0)

    # Multi-Factor Authentication

    async def setup_mfa(self, user: User) -> Dict[str, Any]:
        """Setup MFA for user"""
        try:
            # Generate secret
            secret = pyotp.random_base32()

            # Generate QR code
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user.email,
                issuer_name=SecurityConfig.MFA_ISSUER
            )

            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

            # Store secret (encrypted)
            encrypted_secret = self.encrypt_data(secret)
            user.mfa_secret = encrypted_secret
            await self.update_user(user)

            await self._log_security_event("mfa_setup_initiated", {"username": user.username})

            return {
                "secret": secret,
                "qr_code": f"data:image/png;base64,{qr_code_base64}",
                "backup_codes": self._generate_backup_codes(user)
            }

        except Exception as e:
            logger.error(f"MFA setup error: {e}")
            raise HTTPException(status_code=500, detail="Failed to setup MFA")

    async def verify_mfa_setup(self, user: User, token: str) -> bool:
        """Verify MFA setup with token"""
        try:
            if not user.mfa_secret:
                return False

            secret = self.decrypt_data(user.mfa_secret)

            if self.verify_mfa_token(secret, token):
                user.mfa_enabled = True
                await self.update_user(user)
                await self._log_security_event("mfa_enabled", {"username": user.username})
                return True

            return False

        except Exception as e:
            logger.error(f"MFA verification error: {e}")
            return False

    def verify_mfa_token(self, secret: str, token: str) -> bool:
        """Verify MFA token"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)
        except Exception:
            return False

    def _generate_backup_codes(self, user: User) -> List[str]:
        """Generate backup codes for MFA"""
        codes = []
        for _ in range(10):
            code = secrets.token_hex(4).upper()
            codes.append(code)

        # Store encrypted backup codes
        encrypted_codes = [self.encrypt_data(code) for code in codes]
        # Store in database associated with user

        return codes

    # Role-Based Access Control

    def check_permission(self, user_role: str, required_permission: str) -> bool:
        """Check if user role has required permission"""
        if user_role not in self.roles:
            return False

        return required_permission in self.roles[user_role].permissions

    async def require_permission(self, permission: str):
        """Decorator to require specific permission"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Get current user from context
                current_user = kwargs.get('current_user')
                if not current_user:
                    raise HTTPException(status_code=401, detail="Authentication required")

                if not self.check_permission(current_user.role, permission):
                    await self._log_security_event("unauthorized_access", {
                        "username": current_user.username,
                        "required_permission": permission,
                        "user_role": current_user.role
                    })
                    raise HTTPException(status_code=403, detail="Insufficient permissions")

                return await func(*args, **kwargs)
            return wrapper
        return decorator

    # JWT Token Management

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "type": "access"})

        encoded_jwt = jwt.encode(to_encode, SecurityConfig.SECRET_KEY, algorithm=SecurityConfig.ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=SecurityConfig.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})

        encoded_jwt = jwt.encode(to_encode, SecurityConfig.SECRET_KEY, algorithm=SecurityConfig.ALGORITHM)
        return encoded_jwt

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, SecurityConfig.SECRET_KEY, algorithms=[SecurityConfig.ALGORITHM])

            # Check if token is blacklisted
            if await self._is_token_blacklisted(token):
                return None

            return payload

        except JWTError:
            pass
            return None

    async def blacklist_token(self, token: str):
        """Blacklist a token"""
        try:
            payload = jwt.decode(token, SecurityConfig.SECRET_KEY, algorithms=[SecurityConfig.ALGORITHM])
            exp = payload.get("exp")

            if exp:
                # Store in Redis with expiration
                ttl = exp - int(datetime.utcnow().timestamp())
                if ttl > 0:
                    self.redis_client.setex(f"blacklist:{token}", ttl, "1")

        except JWTError:
            pass
    async def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        return bool(self.redis_client.get(f"blacklist:{token}"))

    # Data Encryption

    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        encrypted_data = self.cipher_suite.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
        return decrypted_data.decode()

    # Security Monitoring

    async def _log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security event for monitoring"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
            "severity": self._get_event_severity(event_type)
        }

        self.security_events.append(event)

        # Store in Redis for real-time monitoring
        self.redis_client.lpush("security_events", str(event))
        self.redis_client.ltrim("security_events", 0, 1000)  # Keep last 1000 events

        # Check for threat patterns
        await self._analyze_threat_patterns(event)

        logger.info(f"Security event: {event_type} - {details}")

    def _get_event_severity(self, event_type: str) -> str:
        """Get severity level for security event"""
        high_severity = ["account_locked", "unauthorized_access", "authentication_error"]
        medium_severity = ["failed_login", "mfa_setup_initiated"]

        if event_type in high_severity:
            return "HIGH"
        elif event_type in medium_severity:
            return "MEDIUM"
        else:
            return "LOW"

    async def _analyze_threat_patterns(self, event: Dict[str, Any]):
        """Analyze security events for threat patterns"""
        event_type = event["event_type"]
        details = event["details"]

        # Detect brute force attacks
        if event_type == "failed_login":
            username = details.get("username")
            if username:
                key = f"failed_logins:{username}"
                count = self.redis_client.incr(key)
                self.redis_client.expire(key, 3600)  # 1 hour window

                if count >= 10:  # 10 failed attempts in 1 hour
                    await self._trigger_security_alert("brute_force_detected", {
                        "username": username,
                        "failed_attempts": count
                    })

        # Detect unusual access patterns
        if event_type == "successful_login":
            username = details.get("username")
            # Implement geolocation and time-based anomaly detection

    async def _trigger_security_alert(self, alert_type: str, details: Dict[str, Any]):
        """Trigger security alert"""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_type": alert_type,
            "details": details,
            "severity": "CRITICAL"
        }

        # Send to monitoring system
        logger.critical(f"SECURITY ALERT: {alert_type} - {details}")

        # Store alert
        self.redis_client.lpush("security_alerts", str(alert))

    # Database Operations (placeholder - implement with your database)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        # Implement database query

    async def update_user(self, user: User):
        """Update user in database"""
        # Implement database update

    # Health Check

    async def health_check(self) -> Dict[str, Any]:
        """Security service health check"""
        try:
            # Check Redis connection
            redis_status = self.redis_client.ping()

            # Check encryption
            sophia_data = "test"
            encrypted = self.encrypt_data(sophia_data)
            decrypted = self.decrypt_data(encrypted)
            encryption_status = sophia_data == decrypted

            return {
                "status": "healthy",
                "redis_connection": redis_status,
                "encryption_service": encryption_status,
                "security_events_count": len(self.security_events),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Initialize global security service
security_service = EnterpriseSecurityService()

# FastAPI dependencies
async def get_current_user(token: str = Depends(security_service.oauth2_scheme)) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = await security_service.verify_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = await security_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception

    return user

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if not security_service.check_permission(current_user.role, "manage_system"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
