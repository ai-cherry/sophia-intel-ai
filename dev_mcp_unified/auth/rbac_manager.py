"""
Role-Based Access Control Manager for Sophia Intelligence AI
Extends existing JWT authentication with hierarchical roles and permissions.
"""
from __future__ import annotations

import json
import sqlite3
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import jwt
from fastapi import HTTPException, Depends, Header


class UserRole(str, Enum):
    """Hierarchical user roles"""
    OWNER = "owner"
    ADMIN = "admin" 
    MEMBER = "member"
    VIEWER = "viewer"


class Permission(str, Enum):
    """System permissions"""
    # Platform permissions
    USER_MANAGE = "user.manage"
    USER_INVITE = "user.invite"
    SYSTEM_CONFIG = "system.config"
    
    # Domain permissions  
    SOPHIA_READ = "sophia.read"
    SOPHIA_WRITE = "sophia.write"
    ARTEMIS_READ = "artemis.read"
    ARTEMIS_WRITE = "artemis.write"
    
    # Service permissions
    AGENT_CREATE = "agent.create"
    AGENT_EXECUTE = "agent.execute"
    BI_READ = "bi.read"
    BI_WRITE = "bi.write"


@dataclass
class User:
    """User model with role and permissions"""
    user_id: str
    email: str
    role: UserRole
    created_at: datetime
    is_active: bool = True
    permissions: Set[str] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = set()


class RBACManager:
    """Role-Based Access Control Manager"""
    
    # Role hierarchy - higher roles inherit lower permissions
    ROLE_HIERARCHY = {
        UserRole.OWNER: {
            Permission.USER_MANAGE,
            Permission.USER_INVITE,
            Permission.SYSTEM_CONFIG,
            Permission.SOPHIA_READ,
            Permission.SOPHIA_WRITE,
            Permission.ARTEMIS_READ,
            Permission.ARTEMIS_WRITE,
            Permission.AGENT_CREATE,
            Permission.AGENT_EXECUTE,
            Permission.BI_READ,
            Permission.BI_WRITE,
        },
        UserRole.ADMIN: {
            Permission.USER_INVITE,
            Permission.SOPHIA_READ,
            Permission.SOPHIA_WRITE,
            Permission.ARTEMIS_READ,
            Permission.ARTEMIS_WRITE,
            Permission.AGENT_CREATE,
            Permission.AGENT_EXECUTE,
            Permission.BI_READ,
            Permission.BI_WRITE,
        },
        UserRole.MEMBER: {
            Permission.SOPHIA_READ,
            Permission.ARTEMIS_READ,
            Permission.AGENT_EXECUTE,
            Permission.BI_READ,
        },
        UserRole.VIEWER: {
            Permission.SOPHIA_READ,
            Permission.BI_READ,
        }
    }
    
    def __init__(self, db_path: str = "rbac.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize RBAC database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_permissions (
                    user_id TEXT,
                    permission TEXT,
                    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    PRIMARY KEY (user_id, permission)
                )
            """)
            
            # Create default owner user if none exists
            cursor = conn.execute("SELECT COUNT(*) FROM users WHERE role = ?", (UserRole.OWNER,))
            if cursor.fetchone()[0] == 0:
                self.create_user("owner@sophia.ai", UserRole.OWNER)
                
    def create_user(self, email: str, role: UserRole) -> str:
        """Create a new user with specified role"""
        import uuid
        user_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO users (user_id, email, role) VALUES (?, ?, ?)",
                (user_id, email, role.value)
            )
            
            # Grant role-based permissions
            permissions = self.ROLE_HIERARCHY.get(role, set())
            for perm in permissions:
                conn.execute(
                    "INSERT OR IGNORE INTO user_permissions (user_id, permission) VALUES (?, ?)",
                    (user_id, perm.value)
                )
                
        return user_id
        
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT user_id, email, role, created_at, is_active FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
                
            # Get user permissions
            perm_cursor = conn.execute(
                "SELECT permission FROM user_permissions WHERE user_id = ?",
                (user_id,)
            )
            permissions = {row[0] for row in perm_cursor.fetchall()}
            
            return User(
                user_id=row[0],
                email=row[1],
                role=UserRole(row[2]),
                created_at=datetime.fromisoformat(row[3]),
                is_active=bool(row[4]),
                permissions=permissions
            )
            
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT user_id FROM users WHERE email = ?",
                (email,)
            )
            row = cursor.fetchone()
            return self.get_user(row[0]) if row else None
            
    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has specific permission"""
        # If RBAC is disabled, grant all permissions (graceful degradation)
        import os
        if os.getenv('RBAC_ENABLED', 'false').lower() != 'true':
            return True
            
        user = self.get_user(user_id)
        if not user or not user.is_active:
            return False
            
        return permission.value in user.permissions
        
    def check_permission(self, user_id: str, permission: Permission):
        """Check permission and raise HTTP exception if denied"""
        if not self.has_permission(user_id, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission.value}"
            )
            
    def list_users(self, requester_id: str) -> List[User]:
        """List all users (requires admin permission)"""
        self.check_permission(requester_id, Permission.USER_MANAGE)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT user_id FROM users WHERE is_active = TRUE"
            )
            return [self.get_user(row[0]) for row in cursor.fetchall()]
            
    def update_user_role(self, requester_id: str, user_id: str, new_role: UserRole):
        """Update user role (requires owner permission)"""
        self.check_permission(requester_id, Permission.USER_MANAGE)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE users SET role = ? WHERE user_id = ?",
                (new_role.value, user_id)
            )
            
            # Update permissions
            conn.execute("DELETE FROM user_permissions WHERE user_id = ?", (user_id,))
            permissions = self.ROLE_HIERARCHY.get(new_role, set())
            for perm in permissions:
                conn.execute(
                    "INSERT INTO user_permissions (user_id, permission) VALUES (?, ?)",
                    (user_id, perm.value)
                )


# Global RBAC manager instance
rbac_manager = RBACManager()


def verify_token_with_permissions(authorization: Optional[str] = Header(None)) -> Optional[User]:
    """Extended token verification with permission loading"""
    from dev_mcp_unified.core.mcp_server import verify_token, SECRET_KEY
    
    if not authorization:
        return None
        
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_email = payload.get("user")
        
        if not user_email:
            return None
            
        # Get user with permissions
        user = rbac_manager.get_user_by_email(user_email)
        return user
        
    except Exception:
        return None


def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func):
        def wrapper(*args, user: User = Depends(verify_token_with_permissions), **kwargs):
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
                
            if not rbac_manager.has_permission(user.user_id, permission):
                raise HTTPException(
                    status_code=403, 
                    detail=f"Permission denied: {permission.value}"
                )
                
            return func(*args, user=user, **kwargs)
        return wrapper
    return decorator