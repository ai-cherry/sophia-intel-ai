# User Management API Endpoints
# Integration into existing MCP Server at /Users/lynnmusil/sophia-intel-ai/dev_mcp_unified/core/mcp_server.py

from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ===== PYDANTIC MODELS =====

class UserCreateRequest(BaseModel):
    email: EmailStr
    name: str
    role_id: str
    domain_access: Dict[str, str] = {}  # {"artemis": "full", "sophia": "read_only"}
    service_permissions: List[Dict[str, Any]] = []
    send_invite: bool = True

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    role_id: Optional[str] = None

class InviteUserRequest(BaseModel):
    email: EmailStr
    role_id: str
    domain_access: Dict[str, str] = {"artemis": "read_only", "sophia": "none"}
    service_permissions: List[Dict[str, Any]] = []
    expires_in_days: int = 7
    custom_message: Optional[str] = None

class PermissionUpdateRequest(BaseModel):
    user_id: str
    domain_access: Optional[Dict[str, str]] = None
    service_permissions: Optional[List[Dict[str, Any]]] = None
    data_access: Optional[List[Dict[str, Any]]] = None

class AcceptInviteRequest(BaseModel):
    invite_token: str
    name: str
    password: Optional[str] = None  # For local auth

# ===== PERMISSION CHECKING UTILITIES =====

def check_user_permission(user_id: str, permission: str, resource: str = None) -> bool:
    """Check if user has specific permission"""
    # Implementation would query user_roles and platform_roles tables
    # Return True/False based on permission hierarchy
    pass

def get_user_domain_access(user_id: str, domain: str) -> str:
    """Get user's access level for specific domain"""
    # Query domain_access table
    # Return access level: 'full', 'read_only', 'restricted', 'none'
    pass

def audit_action(action: str, actor_id: str, target_user_id: str = None, 
                 resource_type: str = None, old_value: Any = None, 
                 new_value: Any = None, ip_address: str = None):
    """Log user management action to audit trail"""
    # Insert into user_audit table
    pass

# ===== API ENDPOINTS TO ADD TO MCP SERVER =====

# User Management Endpoints
@app.get("/api/admin/users")
async def get_users(
    limit: int = 50, 
    offset: int = 0, 
    status: str = None,
    user: Optional[str] = Depends(verify_token)
):
    """Get list of users (admin only)"""
    if not user or not check_user_permission(user, "user_management"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Query users with pagination and filtering
    # Return user list with roles and status
    return {
        "users": [
            {
                "id": "user_001",
                "email": "admin@company.com", 
                "name": "Admin User",
                "status": "active",
                "role": {"id": "role_owner", "name": "owner", "display_name": "Platform Owner"},
                "domain_access": {"artemis": "full", "sophia": "full"},
                "created_at": "2025-09-03T10:00:00Z",
                "last_login": "2025-09-03T09:30:00Z"
            }
        ],
        "total": 1,
        "limit": limit,
        "offset": offset
    }

@app.post("/api/admin/users")
async def create_user(
    req: UserCreateRequest,
    user: Optional[str] = Depends(verify_token)
):
    """Create new user (admin only)"""
    if not user or not check_user_permission(user, "user_management"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if email already exists
    # Generate user ID and create user record
    # Set up initial permissions based on request
    # Send invitation email if requested
    
    audit_action("user_created", user, resource_type="user")
    
    return {
        "user_id": "new_user_id",
        "email": req.email,
        "status": "pending" if req.send_invite else "active",
        "invite_sent": req.send_invite
    }

@app.post("/api/admin/users/invite")
async def invite_user(
    req: InviteUserRequest,
    user: Optional[str] = Depends(verify_token)
):
    """Send user invitation (admin only)"""
    if not user or not check_user_permission(user, "user_management"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Generate secure invite token
    invite_token = secrets.token_urlsafe(32)
    invite_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=req.expires_in_days)
    
    # Store invitation in database
    # Send invitation email
    
    audit_action("invite_sent", user, resource_type="invitation")
    
    return {
        "invite_id": invite_id,
        "email": req.email,
        "expires_at": expires_at.isoformat(),
        "invite_url": f"{os.getenv('PLATFORM_URL', 'http://localhost:3333')}/invite/{invite_token}"
    }

@app.post("/api/admin/users/{user_id}/permissions")
async def update_user_permissions(
    user_id: str,
    req: PermissionUpdateRequest,
    user: Optional[str] = Depends(verify_token)
):
    """Update user permissions (admin only)"""
    if not user or not check_user_permission(user, "user_management"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate target user exists
    # Update domain access if provided
    # Update service permissions if provided
    # Update data access if provided
    
    audit_action("permissions_updated", user, user_id, "permissions")
    
    return {
        "user_id": user_id,
        "updated": True,
        "changes_applied": {
            "domain_access": req.domain_access is not None,
            "service_permissions": req.service_permissions is not None,
            "data_access": req.data_access is not None
        }
    }

@app.get("/api/admin/users/{user_id}")
async def get_user_details(
    user_id: str,
    user: Optional[str] = Depends(verify_token)
):
    """Get detailed user information (admin or self)"""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Allow users to view their own details or require admin permission
    if user != user_id and not check_user_permission(user, "user_management"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Return comprehensive user details
    return {
        "user": {
            "id": user_id,
            "email": "user@company.com",
            "name": "User Name",
            "status": "active",
            "role": {"id": "role_member", "name": "member", "display_name": "Member"},
            "domain_access": {"artemis": "full", "sophia": "read_only"},
            "service_permissions": [
                {"service": "crm", "permissions": ["read", "write"]},
                {"service": "call_analysis", "permissions": ["read"]}
            ],
            "data_access": [
                {"category": "financial", "level": "none"},
                {"category": "customer_pii", "level": "anonymized"}
            ],
            "created_at": "2025-09-01T10:00:00Z",
            "last_login": "2025-09-03T09:15:00Z"
        }
    }

@app.delete("/api/admin/users/{user_id}")
async def deactivate_user(
    user_id: str,
    user: Optional[str] = Depends(verify_token)
):
    """Deactivate user account (admin only)"""
    if not user or not check_user_permission(user, "user_management"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Set user status to 'deactivated'
    # Revoke all active sessions
    # Maintain audit trail
    
    audit_action("user_deactivated", user, user_id, "user")
    
    return {"user_id": user_id, "status": "deactivated"}

# Invitation Management
@app.post("/api/invites/accept")
async def accept_invitation(req: AcceptInviteRequest):
    """Accept user invitation (public endpoint)"""
    # Validate invite token and expiration
    # Create user account with invited permissions
    # Mark invitation as accepted
    # Generate login session
    
    return {
        "success": True,
        "user_id": "new_user_id",
        "redirect_url": "/dashboard"
    }

@app.get("/api/invites/{token}")
async def get_invitation_details(token: str):
    """Get invitation details (public endpoint)"""
    # Validate token and return invitation info
    return {
        "valid": True,
        "email": "invited@company.com",
        "role": {"name": "member", "display_name": "Member"},
        "domain_access": {"artemis": "read_only", "sophia": "none"},
        "expires_at": "2025-09-10T10:00:00Z"
    }

# Permission Management
@app.get("/api/admin/permissions/matrix")
async def get_permissions_matrix(user: Optional[str] = Depends(verify_token)):
    """Get complete permissions matrix (admin only)"""
    if not user or not check_user_permission(user, "user_management"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {
        "platform_roles": [
            {
                "id": "role_owner",
                "name": "owner", 
                "display_name": "Platform Owner",
                "level": 1,
                "permissions": ["user_management", "platform_admin", "domain_admin"]
            }
        ],
        "domains": [
            {"name": "artemis", "display_name": "Artemis Technical", "access_levels": ["full", "read_only", "none"]},
            {"name": "sophia", "display_name": "Sophia Business", "access_levels": ["full", "read_only", "restricted", "none"]}
        ],
        "services": [
            {"name": "crm", "display_name": "CRM Integration", "permissions": ["read", "write", "admin"]},
            {"name": "call_analysis", "display_name": "Call Analysis", "permissions": ["read", "execute"]},
            {"name": "agent_factory", "display_name": "Agent Factory", "permissions": ["read", "create", "execute", "admin"]}
        ],
        "data_categories": [
            {"name": "financial", "display_name": "Financial Data", "levels": ["full", "anonymized", "aggregated_only", "none"]},
            {"name": "employee_data", "display_name": "Employee Information", "levels": ["full", "limited", "none"]},
            {"name": "customer_pii", "display_name": "Customer PII", "levels": ["full", "anonymized", "none"]}
        ]
    }

# Audit and Reporting
@app.get("/api/admin/audit")
async def get_audit_log(
    limit: int = 100,
    action: str = None,
    user_id: str = None,
    start_date: str = None,
    user: Optional[str] = Depends(verify_token)
):
    """Get user management audit log (admin only)"""
    if not user or not check_user_permission(user, "audit_access"):
        raise HTTPException(status_code=403, detail="Audit access required")
    
    # Query user_audit table with filters
    return {
        "audit_entries": [
            {
                "id": "audit_001",
                "timestamp": "2025-09-03T10:30:00Z",
                "action": "user_created",
                "actor": {"id": "user_admin", "name": "Admin User"},
                "target": {"id": "user_new", "name": "New User"},
                "resource_type": "user",
                "details": "Created with member role"
            }
        ],
        "total": 1,
        "filters": {"action": action, "user_id": user_id, "start_date": start_date}
    }

# Session Management
@app.get("/api/admin/sessions")
async def get_active_sessions(user: Optional[str] = Depends(verify_token)):
    """Get active user sessions (admin only)"""
    if not user or not check_user_permission(user, "user_management"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {
        "active_sessions": [
            {
                "id": "session_001",
                "user": {"id": "user_001", "name": "User Name"},
                "created_at": "2025-09-03T09:00:00Z",
                "last_accessed": "2025-09-03T10:30:00Z",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0..."
            }
        ],
        "total_active": 1
    }

@app.delete("/api/admin/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    user: Optional[str] = Depends(verify_token)
):
    """Revoke user session (admin only)"""
    if not user or not check_user_permission(user, "user_management"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Mark session as inactive
    audit_action("session_revoked", user, resource_type="session")
    
    return {"session_id": session_id, "revoked": True}

# Self-service endpoints
@app.get("/api/profile")
async def get_my_profile(user: Optional[str] = Depends(verify_token)):
    """Get current user's profile"""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Return user's own profile information
    return {
        "user": {
            "id": user,
            "email": "current@user.com",
            "name": "Current User",
            "permissions": {
                "domains": {"artemis": "full", "sophia": "read_only"},
                "services": ["crm:read", "crm:write", "call_analysis:read"]
            }
        }
    }

@app.put("/api/profile")
async def update_my_profile(
    profile: Dict[str, str],
    user: Optional[str] = Depends(verify_token)
):
    """Update current user's profile"""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Allow users to update their own name, but not permissions
    allowed_fields = ["name"]
    updates = {k: v for k, v in profile.items() if k in allowed_fields}
    
    audit_action("profile_updated", user, user, "profile")
    
    return {"updated": True, "fields": list(updates.keys())}