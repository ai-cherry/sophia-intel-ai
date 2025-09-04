"""
Input Validation Models for MCP Server

This module provides Pydantic models with comprehensive validation
for all API endpoints to prevent injection attacks and ensure data integrity.
"""

import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, validator, constr, conint
from datetime import datetime


class FilePathValidator:
    """Mixin for file path validation"""
    
    @validator('file_path', 'path', 'filename', check_fields=False)
    def validate_file_path(cls, v: str) -> str:
        """Validate file paths to prevent traversal attacks"""
        if not v:
            raise ValueError("Path cannot be empty")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            '..',  # Parent directory traversal
            '~',   # Home directory
            '$',   # Variable expansion
            '`',   # Command substitution
            '\x00', # Null bytes
            '\n',  # Newlines
            '\r',  # Carriage returns
        ]
        
        for pattern in dangerous_patterns:
            if pattern in v:
                raise ValueError(f"Invalid path: contains dangerous pattern '{pattern}'")
        
        # Check for absolute paths
        if v.startswith('/') or (len(v) > 1 and v[1] == ':'):
            raise ValueError("Absolute paths are not allowed")
        
        # Limit path length
        if len(v) > 500:
            raise ValueError("Path too long (max 500 characters)")
        
        return v


class QueryRequestModel(BaseModel):
    """Validated model for LLM query requests"""
    
    task: constr(min_length=1, max_length=100) = Field(
        ...,
        description="Task type for context selection",
        example="coding"
    )
    question: constr(min_length=1, max_length=10000) = Field(
        ...,
        description="User query or prompt",
        example="How do I implement authentication?"
    )
    llm: Optional[Literal["claude", "openai", "gpt4", "mistral", "llama"]] = Field(
        "claude",
        description="LLM provider to use"
    )
    temperature: Optional[float] = Field(
        0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: Optional[conint(ge=1, le=100000)] = Field(
        4096,
        description="Maximum tokens in response"
    )
    
    @validator('task')
    def validate_task(cls, v: str) -> str:
        """Ensure task contains only safe characters"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Task must contain only alphanumeric characters, hyphens, and underscores")
        return v.lower()
    
    @validator('question')
    def sanitize_question(cls, v: str) -> str:
        """Basic sanitization of user input"""
        # Remove any potential script tags
        v = re.sub(r'<script[^>]*>.*?</script>', '', v, flags=re.DOTALL | re.IGNORECASE)
        # Remove other HTML tags but keep content
        v = re.sub(r'<[^>]+>', '', v)
        # Limit consecutive whitespace
        v = re.sub(r'\s+', ' ', v).strip()
        return v


class FileReadRequest(BaseModel, FilePathValidator):
    """Validated model for file read operations"""
    
    file_path: constr(min_length=1, max_length=500) = Field(
        ...,
        description="Path to file to read"
    )
    encoding: Optional[Literal["utf-8", "ascii", "latin-1"]] = Field(
        "utf-8",
        description="File encoding"
    )
    max_size_mb: Optional[conint(ge=1, le=100)] = Field(
        10,
        description="Maximum file size in MB"
    )


class FileWriteRequest(BaseModel, FilePathValidator):
    """Validated model for file write operations"""
    
    file_path: constr(min_length=1, max_length=500) = Field(
        ...,
        description="Path to file to write"
    )
    content: constr(min_length=0, max_length=10_000_000) = Field(
        ...,
        description="Content to write to file"
    )
    encoding: Optional[Literal["utf-8", "ascii", "latin-1"]] = Field(
        "utf-8",
        description="File encoding"
    )
    create_backup: Optional[bool] = Field(
        True,
        description="Create backup before overwriting"
    )
    
    @validator('content')
    def check_content_safety(cls, v: str) -> str:
        """Check for potentially malicious content patterns"""
        # Check for common script injection patterns
        dangerous_patterns = [
            r'<\?php',  # PHP tags
            r'<%',      # ASP tags
            r'<jsp:',   # JSP tags
            r'exec\s*\(',  # Python/JS exec
            r'eval\s*\(',  # Eval function
            r'__import__',  # Python import
            r'require\s*\(',  # Node.js require
        ]
        
        content_lower = v.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, content_lower):
                raise ValueError(f"Content contains potentially dangerous pattern")
        
        return v


class FileDeleteRequest(BaseModel, FilePathValidator):
    """Validated model for file deletion"""
    
    file_path: constr(min_length=1, max_length=500) = Field(
        ...,
        description="Path to file to delete"
    )
    confirm: bool = Field(
        ...,
        description="Confirmation flag for deletion"
    )
    
    @validator('confirm')
    def must_confirm(cls, v: bool) -> bool:
        """Ensure deletion is confirmed"""
        if not v:
            raise ValueError("Deletion must be confirmed")
        return v


class DirectoryListRequest(BaseModel, FilePathValidator):
    """Validated model for directory listing"""
    
    path: constr(min_length=0, max_length=500) = Field(
        ".",
        description="Directory path to list"
    )
    recursive: Optional[bool] = Field(
        False,
        description="List recursively"
    )
    max_depth: Optional[conint(ge=1, le=5)] = Field(
        3,
        description="Maximum recursion depth"
    )
    include_hidden: Optional[bool] = Field(
        False,
        description="Include hidden files"
    )
    pattern: Optional[constr(max_length=100)] = Field(
        None,
        description="File pattern filter (glob)"
    )
    
    @validator('pattern')
    def validate_pattern(cls, v: Optional[str]) -> Optional[str]:
        """Validate glob pattern for safety"""
        if v:
            # Only allow safe glob patterns
            if not re.match(r'^[a-zA-Z0-9_.*?[\]-]+$', v):
                raise ValueError("Invalid glob pattern")
        return v


class DatabaseQueryRequest(BaseModel):
    """Validated model for database queries"""
    
    operation: Literal["select", "insert", "update", "delete"] = Field(
        ...,
        description="Database operation type"
    )
    table: constr(min_length=1, max_length=64, regex=r'^[a-zA-Z_][a-zA-Z0-9_]*$') = Field(
        ...,
        description="Table name"
    )
    conditions: Optional[Dict[str, Any]] = Field(
        None,
        description="Query conditions"
    )
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Data for insert/update"
    )
    limit: Optional[conint(ge=1, le=1000)] = Field(
        100,
        description="Result limit for select"
    )
    
    @validator('table')
    def validate_table_name(cls, v: str) -> str:
        """Ensure table name is safe"""
        reserved_words = {
            'select', 'insert', 'update', 'delete', 'from', 'where',
            'join', 'union', 'drop', 'create', 'alter', 'grant'
        }
        if v.lower() in reserved_words:
            raise ValueError(f"'{v}' is a reserved SQL keyword")
        return v
    
    @validator('conditions', 'data')
    def validate_data_types(cls, v: Optional[Dict]) -> Optional[Dict]:
        """Validate data types to prevent injection"""
        if v:
            for key, value in v.items():
                # Validate keys
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                    raise ValueError(f"Invalid column name: {key}")
                
                # Validate values (basic type checking)
                if not isinstance(value, (str, int, float, bool, type(None))):
                    raise ValueError(f"Invalid value type for {key}")
                
                # Check string values for SQL injection patterns
                if isinstance(value, str):
                    dangerous_sql = [
                        '--', '/*', '*/', 'xp_', 'sp_', ';',
                        'union', 'select', 'delete', 'insert', 'drop'
                    ]
                    value_lower = value.lower()
                    for pattern in dangerous_sql:
                        if pattern in value_lower:
                            raise ValueError(f"Potentially dangerous SQL pattern in value")
        
        return v


class AuthenticationRequest(BaseModel):
    """Validated model for authentication"""
    
    username: constr(min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_-]+$') = Field(
        ...,
        description="Username"
    )
    password: constr(min_length=8, max_length=128) = Field(
        ...,
        description="Password"
    )
    mfa_code: Optional[constr(regex=r'^\d{6}$')] = Field(
        None,
        description="MFA code if enabled"
    )
    
    @validator('password')
    def validate_password_strength(cls, v: str) -> str:
        """Basic password strength validation"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        # Check for basic complexity (optional, can be configured)
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError("Password must contain uppercase, lowercase, and digits")
        
        return v


class RateLimitRequest(BaseModel):
    """Rate limit information model"""
    
    client_id: str = Field(..., description="Client identifier")
    endpoint: str = Field(..., description="API endpoint")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('endpoint')
    def validate_endpoint(cls, v: str) -> str:
        """Validate endpoint format"""
        if not v.startswith('/'):
            raise ValueError("Endpoint must start with /")
        if len(v) > 200:
            raise ValueError("Endpoint path too long")
        return v


class SearchRequest(BaseModel):
    """Validated model for search operations"""
    
    query: constr(min_length=1, max_length=500) = Field(
        ...,
        description="Search query"
    )
    search_type: Literal["files", "content", "all"] = Field(
        "all",
        description="Type of search"
    )
    max_results: Optional[conint(ge=1, le=100)] = Field(
        20,
        description="Maximum number of results"
    )
    case_sensitive: Optional[bool] = Field(
        False,
        description="Case sensitive search"
    )
    
    @validator('query')
    def sanitize_search_query(cls, v: str) -> str:
        """Sanitize search query"""
        # Remove regex special characters if not in regex mode
        special_chars = r'.*+?[]{}()\|^$'
        for char in special_chars:
            v = v.replace(char, f'\\{char}')
        return v


# Export all validation models
__all__ = [
    "QueryRequestModel",
    "FileReadRequest",
    "FileWriteRequest",
    "FileDeleteRequest",
    "DirectoryListRequest",
    "DatabaseQueryRequest",
    "AuthenticationRequest",
    "RateLimitRequest",
    "SearchRequest",
]