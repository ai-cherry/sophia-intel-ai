# User Management Security Implementation

## Authentication & Authorization Security

### 1. JWT Token Security
```python
# Enhanced JWT implementation with security best practices
import secrets
import hashlib
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

class SecureJWTManager:
    def __init__(self):
        # Generate secure signing keys
        self.signing_key = os.getenv("JWT_SIGNING_KEY") or secrets.token_urlsafe(64)
        self.encryption_key = os.getenv("JWT_ENCRYPTION_KEY") or Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
    
    def create_token(self, user_id: str, permissions: dict, expires_hours: int = 24):
        """Create secure, encrypted JWT with minimal payload"""
        payload = {
            "sub": user_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=expires_hours),
            "jti": secrets.token_urlsafe(16),  # Unique token ID for revocation
            "perm_hash": hashlib.sha256(str(sorted(permissions.items())).encode()).hexdigest()[:16]
        }
        
        # Create JWT
        token = jwt.encode(payload, self.signing_key, algorithm="HS256")
        
        # Encrypt the token
        encrypted_token = self.cipher.encrypt(token.encode()).decode()
        
        # Store token hash for revocation checking
        token_hash = hashlib.sha256(encrypted_token.encode()).hexdigest()
        self.store_active_token(user_id, token_hash, payload["jti"], payload["exp"])
        
        return encrypted_token
    
    def verify_token(self, encrypted_token: str):
        """Verify and decrypt JWT token"""
        try:
            # Decrypt token
            token = self.cipher.decrypt(encrypted_token.encode()).decode()
            
            # Verify JWT
            payload = jwt.decode(token, self.signing_key, algorithms=["HS256"])
            
            # Check if token is revoked
            if self.is_token_revoked(payload["jti"]):
                raise jwt.InvalidTokenError("Token has been revoked")
            
            # Verify permissions haven't changed
            current_permissions = self.get_user_permissions(payload["sub"])
            current_hash = hashlib.sha256(str(sorted(current_permissions.items())).encode()).hexdigest()[:16]
            
            if current_hash != payload["perm_hash"]:
                raise jwt.InvalidTokenError("Permissions have changed - re-authentication required")
            
            return payload["sub"], current_permissions
            
        except Exception as e:
            raise jwt.InvalidTokenError(f"Token verification failed: {str(e)}")
```

### 2. Password Security
```python
import bcrypt
import secrets
from password_strength import PasswordPolicy

class PasswordManager:
    def __init__(self):
        # Define password policy
        self.policy = PasswordPolicy.from_names(
            length=12,  # minimum length
            uppercase=1,  # need min. 1 uppercase letters
            numbers=1,  # need min. 1 digits
            special=1,  # need min. 1 special characters
            nonletters=2,  # need min. 2 non-letter characters
        )
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt and salt"""
        # Validate password strength
        violations = self.policy.test(password)
        if violations:
            raise ValueError(f"Password policy violations: {[str(v) for v in violations]}")
        
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_secure_password(self) -> str:
        """Generate cryptographically secure password"""
        # Generate 16-character password with mixed case, numbers, symbols
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(16))
        
        # Ensure it meets policy requirements
        while self.policy.test(password):
            password = ''.join(secrets.choice(alphabet) for _ in range(16))
        
        return password
```

### 3. Rate Limiting & DDoS Protection
```python
from collections import defaultdict, deque
import time
import hashlib

class AdvancedRateLimiter:
    def __init__(self):
        # Different limits for different endpoints
        self.limits = {
            "login": {"requests": 5, "window": 300, "lockout": 900},  # 5 attempts per 5min, 15min lockout
            "invite": {"requests": 10, "window": 3600, "lockout": 0},  # 10 invites per hour
            "password_reset": {"requests": 3, "window": 3600, "lockout": 1800},  # 3 resets per hour
            "api_general": {"requests": 100, "window": 60, "lockout": 0}  # 100 requests per minute
        }
        
        # Track requests per IP + endpoint combination
        self.request_logs = defaultdict(lambda: defaultdict(deque))
        self.lockouts = defaultdict(dict)
    
    def is_allowed(self, ip: str, endpoint: str, user_id: str = None) -> tuple[bool, dict]:
        """Check if request is allowed, return (allowed, info)"""
        now = time.time()
        key = f"{ip}:{endpoint}"
        
        # Check if IP is locked out
        if endpoint in self.lockouts.get(ip, {}):
            lockout_until = self.lockouts[ip][endpoint]
            if now < lockout_until:
                return False, {
                    "reason": "rate_limited",
                    "retry_after": int(lockout_until - now),
                    "endpoint": endpoint
                }
            else:
                # Lockout expired
                del self.lockouts[ip][endpoint]
        
        # Get endpoint limits
        limit_config = self.limits.get(endpoint, self.limits["api_general"])
        window = limit_config["window"]
        max_requests = limit_config["requests"]
        
        # Clean old requests outside window
        request_log = self.request_logs[ip][endpoint]
        cutoff = now - window
        while request_log and request_log[0] <= cutoff:
            request_log.popleft()
        
        # Check if limit exceeded
        if len(request_log) >= max_requests:
            # Apply lockout if configured
            if limit_config["lockout"] > 0:
                self.lockouts.setdefault(ip, {})[endpoint] = now + limit_config["lockout"]
            
            return False, {
                "reason": "rate_limit_exceeded", 
                "requests_made": len(request_log),
                "limit": max_requests,
                "window": window,
                "retry_after": limit_config["lockout"] or window
            }
        
        # Log this request
        request_log.append(now)
        
        return True, {
            "requests_made": len(request_log),
            "limit": max_requests,
            "window": window,
            "remaining": max_requests - len(request_log)
        }

# Apply to specific endpoints
async def rate_limit_endpoint(endpoint_name: str):
    """Decorator for rate limiting endpoints"""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host if request.client else "unknown"
            user_id = None  # Extract from token if available
            
            allowed, info = rate_limiter.is_allowed(client_ip, endpoint_name, user_id)
            
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail=info,
                    headers={"Retry-After": str(info.get("retry_after", 60))}
                )
            
            # Add rate limit headers to response
            response = await func(request, *args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers.update({
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": str(info.get("remaining", 0)),
                    "X-RateLimit-Reset": str(int(time.time() + info["window"]))
                })
            
            return response
        return wrapper
    return decorator
```

### 4. Input Validation & Sanitization
```python
from pydantic import validator, EmailStr
import re
import html
import bleach

class SecureUserInput(BaseModel):
    """Enhanced input validation for user management"""
    
    @validator('email')
    def validate_email(cls, v):
        if not v or len(v) > 254:  # RFC 5321 limit
            raise ValueError('Invalid email length')
        
        # Additional email validation beyond pydantic
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        
        return v.lower().strip()
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Name is required')
        
        if len(v) > 100:
            raise ValueError('Name too long')
        
        # Sanitize HTML and remove control characters
        sanitized = bleach.clean(v.strip(), tags=[], strip=True)
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        
        return sanitized
    
    @validator('role_id')
    def validate_role_id(cls, v):
        if not v or not re.match(r'^role_[a-z_]+$', v):
            raise ValueError('Invalid role ID format')
        return v

def sanitize_sql_input(value: str) -> str:
    """Additional SQL injection protection"""
    dangerous_patterns = [
        r';', r'--', r'/\*', r'\*/', r'xp_', r'sp_', 
        r'exec', r'execute', r'drop', r'create', r'alter',
        r'insert', r'update', r'delete', r'union', r'select'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValueError(f'Potentially dangerous input detected')
    
    return value
```

### 5. Audit Trail Security
```python
import hmac
import json
from datetime import datetime

class SecureAuditLogger:
    def __init__(self):
        self.signing_key = os.getenv("AUDIT_SIGNING_KEY") or secrets.token_urlsafe(32)
    
    def create_audit_entry(self, action: str, actor_id: str, target_id: str = None, 
                          resource_type: str = None, old_value: Any = None, 
                          new_value: Any = None, ip_address: str = None,
                          user_agent: str = None) -> dict:
        """Create tamper-proof audit entry"""
        
        # Create entry data
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "actor_id": actor_id,
            "target_id": target_id,
            "resource_type": resource_type,
            "ip_address": ip_address,
            "user_agent": user_agent[:200] if user_agent else None  # Truncate user agent
        }
        
        # Serialize sensitive data with encryption if needed
        if old_value:
            entry["old_value"] = self.encrypt_sensitive_data(old_value)
        if new_value:
            entry["new_value"] = self.encrypt_sensitive_data(new_value)
        
        # Create integrity signature
        entry_json = json.dumps(entry, sort_keys=True, separators=(',', ':'))
        signature = hmac.new(
            self.signing_key.encode(),
            entry_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        entry["signature"] = signature
        
        return entry
    
    def verify_audit_entry(self, entry: dict) -> bool:
        """Verify audit entry hasn't been tampered with"""
        if "signature" not in entry:
            return False
        
        stored_signature = entry.pop("signature")
        entry_json = json.dumps(entry, sort_keys=True, separators=(',', ':'))
        expected_signature = hmac.new(
            self.signing_key.encode(),
            entry_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Restore signature
        entry["signature"] = stored_signature
        
        return hmac.compare_digest(stored_signature, expected_signature)
    
    def encrypt_sensitive_data(self, data: Any) -> str:
        """Encrypt sensitive audit data"""
        if data is None:
            return None
        
        json_data = json.dumps(data, default=str)
        cipher = Fernet(os.getenv("AUDIT_ENCRYPTION_KEY", Fernet.generate_key()))
        encrypted = cipher.encrypt(json_data.encode())
        return encrypted.decode()
```

## Database Security

### 1. Secure Database Configuration
```sql
-- Enable WAL mode for better concurrency and crash safety
PRAGMA journal_mode=WAL;

-- Set secure permissions
PRAGMA secure_delete=ON;

-- Enable foreign key constraints
PRAGMA foreign_keys=ON;

-- Set reasonable timeout
PRAGMA busy_timeout=5000;

-- Enable query planner debugging (development only)
-- PRAGMA optimize;
```

### 2. Data Encryption at Rest
```python
import sqlite3
from cryptography.fernet import Fernet

class EncryptedSQLiteConnection:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.encryption_key = os.getenv("DB_ENCRYPTION_KEY", Fernet.generate_key())
        self.cipher = Fernet(self.encryption_key)
        
    def encrypt_field(self, value: str) -> str:
        """Encrypt sensitive field"""
        if not value:
            return value
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt_field(self, encrypted_value: str) -> str:
        """Decrypt sensitive field"""
        if not encrypted_value:
            return encrypted_value
        return self.cipher.decrypt(encrypted_value.encode()).decode()

# Usage example for sensitive fields
def store_user_data(email: str, name: str, phone: str = None):
    with get_db_connection() as conn:
        encrypted_phone = encrypt_field(phone) if phone else None
        
        conn.execute("""
            INSERT INTO users (email, name, phone_encrypted, created_at)
            VALUES (?, ?, ?, ?)
        """, (email, name, encrypted_phone, datetime.now().isoformat()))
```

## Network Security

### 1. HTTPS Enforcement
```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Force HTTPS in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
    
    # Only allow specific hosts
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
    )

# Security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response
```

### 2. API Security
```python
# Request size limiting
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom middleware for request validation
@app.middleware("http") 
async def request_validation_middleware(request: Request, call_next):
    # Limit request size (10MB)
    max_size = 10 * 1024 * 1024
    if request.headers.get("content-length"):
        if int(request.headers["content-length"]) > max_size:
            return JSONResponse(
                status_code=413,
                content={"error": "Request too large"}
            )
    
    # Validate Content-Type for POST requests
    if request.method in ["POST", "PUT", "PATCH"]:
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith(("application/json", "multipart/form-data")):
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid content type"}
            )
    
    return await call_next(request)
```

## Deployment Security Checklist

- [ ] Environment variables secured (no secrets in code)
- [ ] Database files have restricted permissions (600)  
- [ ] JWT signing keys are cryptographically secure
- [ ] Rate limiting enabled on all authentication endpoints
- [ ] HTTPS enabled with valid certificates
- [ ] Security headers configured
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention measures
- [ ] XSS protection measures
- [ ] CSRF protection for state-changing operations
- [ ] Audit logging enabled and tamper-proof
- [ ] Regular security updates planned
- [ ] Password policy enforced
- [ ] Session timeout configured appropriately
- [ ] Failed login attempt monitoring
- [ ] Database backups encrypted
- [ ] Network access restricted to necessary ports
- [ ] Admin interface accessible only to authenticated admins