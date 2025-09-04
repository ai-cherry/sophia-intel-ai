"""
Security utilities for MCP Server

This module provides security functions for path validation,
input sanitization, and request verification.
"""

import hashlib
import hmac
import re
import secrets
from pathlib import Path
from typing import Optional, List, Set
from functools import wraps
import jwt
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


class SecurityError(Exception):
    """Base exception for security-related errors"""
    pass


class PathTraversalError(SecurityError):
    """Raised when path traversal is detected"""
    pass


class PathValidator:
    """
    Secure path validation to prevent directory traversal attacks.
    """
    
    # Patterns that indicate potential security issues
    DANGEROUS_PATTERNS = {
        r'\.\./',           # Parent directory traversal
        r'\.\.\\',          # Windows parent directory traversal  
        r'^/',              # Absolute paths
        r'^[A-Za-z]:',      # Windows drive letters
        r'[\x00-\x1f]',     # Control characters
        r'~/',              # Home directory expansion
        r'\$\{.*\}',        # Variable expansion
        r'\$\(.*\)',        # Command substitution
        r'`.*`',            # Backtick command substitution
    }
    
    # Sensitive directories that should never be accessed
    SENSITIVE_DIRS = {
        '.git',
        '.env',
        '.ssh',
        '.aws',
        '.docker',
        'node_modules',
        '__pycache__',
        '.venv',
        'venv',
        '.idea',
        '.vscode',
        'secrets',
        'private',
        'credentials',
    }
    
    # Sensitive file patterns
    SENSITIVE_FILES = {
        r'.*\.key$',
        r'.*\.pem$',
        r'.*\.crt$',
        r'.*\.pfx$',
        r'.*\.p12$',
        r'^\.env.*',
        r'.*_rsa$',
        r'.*_dsa$',
        r'.*\.sqlite$',
        r'.*\.db$',
        r'.*\.kdbx$',
        r'.*secrets.*',
        r'.*password.*',
        r'.*token.*',
        r'.*api[_-]?key.*',
    }
    
    def __init__(self, base_path: Path, allowed_extensions: Optional[Set[str]] = None):
        """
        Initialize path validator with base directory.
        
        Args:
            base_path: Root directory for allowed file access
            allowed_extensions: Set of allowed file extensions (e.g., {'.py', '.js'})
        """
        self.base_path = base_path.resolve()
        self.allowed_extensions = allowed_extensions or set()
        
        # Compile regex patterns for efficiency
        self.dangerous_regex = [re.compile(pattern) for pattern in self.DANGEROUS_PATTERNS]
        self.sensitive_file_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.SENSITIVE_FILES]
    
    def is_safe_path(self, file_path: str) -> bool:
        """
        Validate if a path is safe to access.
        
        Args:
            file_path: Path to validate
            
        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Check for dangerous patterns
            for regex in self.dangerous_regex:
                if regex.search(file_path):
                    return False
            
            # Normalize and resolve the path
            target = Path(file_path).resolve()
            
            # Check if path is within base directory
            try:
                target.relative_to(self.base_path)
            except ValueError:
                # Path is outside base directory
                return False
            
            # Check for sensitive directories
            for part in target.parts:
                if part.lower() in self.sensitive_dirs or part.startswith('.'):
                    return False
            
            # Check for sensitive file patterns
            file_name = target.name.lower()
            for regex in self.sensitive_file_regex:
                if regex.search(file_name):
                    return False
            
            # Check file extension if restrictions are set
            if self.allowed_extensions:
                if not any(target.suffix == ext for ext in self.allowed_extensions):
                    return False
            
            return True
            
        except Exception:
            # Any error in path validation means it's not safe
            return False
    
    def get_safe_path(self, file_path: str) -> Path:
        """
        Get a validated safe path.
        
        Args:
            file_path: Path to validate and return
            
        Returns:
            Validated Path object
            
        Raises:
            PathTraversalError: If path is not safe
        """
        if not self.is_safe_path(file_path):
            raise PathTraversalError(f"Access denied: {file_path}")
        
        return Path(file_path).resolve()


class InputSanitizer:
    """
    Input sanitization utilities.
    """
    
    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 255) -> str:
        """
        Sanitize a filename to be safe for filesystem operations.
        
        Args:
            filename: Original filename
            max_length: Maximum allowed length
            
        Returns:
            Sanitized filename
        """
        # Remove dangerous characters
        safe_chars = re.compile(r'[^a-zA-Z0-9._-]')
        sanitized = safe_chars.sub('_', filename)
        
        # Remove leading dots and spaces
        sanitized = sanitized.lstrip('. ')
        
        # Limit length
        if len(sanitized) > max_length:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            max_name_length = max_length - len(ext) - 1 if ext else max_length
            sanitized = name[:max_name_length] + ('.' + ext if ext else '')
        
        # Ensure non-empty
        if not sanitized:
            sanitized = f"file_{secrets.token_hex(8)}"
        
        return sanitized
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """
        Basic HTML sanitization to prevent XSS.
        
        Args:
            text: Text that may contain HTML
            
        Returns:
            Sanitized text
        """
        # Escape HTML special characters
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '/': '&#x2F;',
        }
        
        for char, escape in replacements.items():
            text = text.replace(char, escape)
        
        return text
    
    @staticmethod
    def sanitize_sql_identifier(identifier: str) -> str:
        """
        Sanitize SQL identifiers (table/column names).
        
        Args:
            identifier: SQL identifier to sanitize
            
        Returns:
            Sanitized identifier
        """
        # Allow only alphanumeric and underscore
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
            raise ValueError(f"Invalid SQL identifier: {identifier}")
        
        # Limit length
        if len(identifier) > 64:
            raise ValueError(f"SQL identifier too long: {identifier}")
        
        return identifier


class RequestSigner:
    """
    Request signing and verification for critical operations.
    """
    
    def __init__(self, secret_key: str):
        """
        Initialize request signer with secret key.
        
        Args:
            secret_key: Secret key for HMAC signing
        """
        self.secret_key = secret_key.encode()
    
    def sign_request(self, body: bytes, timestamp: Optional[int] = None) -> str:
        """
        Sign a request body with HMAC-SHA256.
        
        Args:
            body: Request body as bytes
            timestamp: Optional timestamp to include
            
        Returns:
            Hex-encoded signature
        """
        if timestamp is None:
            timestamp = int(datetime.utcnow().timestamp())
        
        message = f"{timestamp}:{body.decode('utf-8')}".encode()
        signature = hmac.new(self.secret_key, message, hashlib.sha256)
        
        return f"{timestamp}:{signature.hexdigest()}"
    
    def verify_signature(self, body: bytes, signature: str, max_age: int = 300) -> bool:
        """
        Verify request signature.
        
        Args:
            body: Request body as bytes
            signature: Signature to verify (timestamp:hex_signature)
            max_age: Maximum age of signature in seconds
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            timestamp_str, sig = signature.split(':', 1)
            timestamp = int(timestamp_str)
            
            # Check timestamp age
            current_time = int(datetime.utcnow().timestamp())
            if current_time - timestamp > max_age:
                return False
            
            # Verify signature
            expected = self.sign_request(body, timestamp)
            return hmac.compare_digest(expected, signature)
            
        except Exception:
            return False


class JWTManager:
    """
    JWT token management for authentication.
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", expiration_minutes: int = 30):
        """
        Initialize JWT manager.
        
        Args:
            secret_key: Secret key for JWT signing
            algorithm: JWT algorithm (default: HS256)
            expiration_minutes: Token expiration time in minutes
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_minutes = expiration_minutes
        self.bearer = HTTPBearer()
    
    def create_token(self, user_id: str, scopes: List[str] = None) -> str:
        """
        Create a JWT token.
        
        Args:
            user_id: User identifier
            scopes: List of permission scopes
            
        Returns:
            Encoded JWT token
        """
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(minutes=self.expiration_minutes),
            "iat": datetime.utcnow(),
            "scopes": scopes or [],
            "jti": secrets.token_hex(16),  # Unique token ID
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> dict:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """
        Dependency to get current user from JWT token.
        
        Args:
            credentials: Bearer token from request
            
        Returns:
            User information from token
        """
        token = credentials.credentials
        payload = self.verify_token(token)
        return {
            "user_id": payload.get("sub"),
            "scopes": payload.get("scopes", [])
        }


def require_scope(required_scope: str):
    """
    Decorator to require a specific permission scope.
    
    Args:
        required_scope: Required permission scope
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: dict = None, **kwargs):
            if current_user is None:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            if required_scope not in current_user.get("scopes", []):
                raise HTTPException(status_code=403, detail=f"Scope '{required_scope}' required")
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


# Export main classes and functions
__all__ = [
    "SecurityError",
    "PathTraversalError",
    "PathValidator",
    "InputSanitizer",
    "RequestSigner",
    "JWTManager",
    "require_scope",
]