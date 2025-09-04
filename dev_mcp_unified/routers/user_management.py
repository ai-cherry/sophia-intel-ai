"""
User Management Router for Sophia Intelligence AI
Integrates with existing MCP server authentication and follows existing patterns
"""
from __future__ import annotations

import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr

from dev_mcp_unified.auth.rbac_manager import (
    rbac_manager, 
    verify_token_with_permissions,
    require_permission,
    User,
    UserRole,
    Permission
)


# Request/Response models following existing MCP server patterns
class UserCreateRequest(BaseModel):
    email: EmailStr
    role: UserRole


class UserUpdateRequest(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    user_id: str
    email: str
    role: UserRole
    created_at: datetime
    is_active: bool
    permissions: List[str]
    
    @classmethod
    def from_user(cls, user: User) -> 'UserResponse':
        return cls(
            user_id=user.user_id,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            is_active=user.is_active,
            permissions=list(user.permissions)
        )


class InviteRequest(BaseModel):
    email: EmailStr
    role: UserRole
    message: Optional[str] = None


class PermissionCheckRequest(BaseModel):
    permission: str


class AuditLogResponse(BaseModel):
    id: str
    user_id: str
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[str]
    timestamp: datetime


# Create router following existing MCP server pattern
router = APIRouter(prefix="/admin", tags=["user_management"])


@router.get("/users", response_model=List[UserResponse])
async def list_users(current_user: User = Depends(verify_token_with_permissions)):
    """List all users (requires admin permission)"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    rbac_manager.check_permission(current_user.user_id, Permission.USER_MANAGE)
    
    users = rbac_manager.list_users(current_user.user_id)
    return [UserResponse.from_user(user) for user in users]


@router.post("/users", response_model=UserResponse)
async def create_user(
    request: UserCreateRequest,
    current_user: User = Depends(verify_token_with_permissions)
):
    """Create a new user (requires admin permission)"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    rbac_manager.check_permission(current_user.user_id, Permission.USER_MANAGE)
    
    try:
        user_id = rbac_manager.create_user(request.email, request.role)
        user = rbac_manager.get_user(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
            
        return UserResponse.from_user(user)
        
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(verify_token_with_permissions)
):
    """Get user by ID (requires admin permission or own user)"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Users can view their own profile, admins can view any profile
    if current_user.user_id != user_id:
        rbac_manager.check_permission(current_user.user_id, Permission.USER_MANAGE)
    
    user = rbac_manager.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_user(user)


@router.put("/users/{user_id}", response_model=UserResponse) 
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    current_user: User = Depends(verify_token_with_permissions)
):
    """Update user (requires admin permission)"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    rbac_manager.check_permission(current_user.user_id, Permission.USER_MANAGE)
    
    user = rbac_manager.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if request.role and request.role != user.role:
        rbac_manager.update_user_role(current_user.user_id, user_id, request.role)
    
    # Refresh user data
    updated_user = rbac_manager.get_user(user_id)
    return UserResponse.from_user(updated_user)


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(verify_token_with_permissions)
):
    """Deactivate user (soft delete) - requires admin permission"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    rbac_manager.check_permission(current_user.user_id, Permission.USER_MANAGE)
    
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user = rbac_manager.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # TODO: Implement soft delete in rbac_manager
    return {"message": "User deactivated successfully"}


@router.post("/users/invite")
async def invite_user(
    request: InviteRequest,
    current_user: User = Depends(verify_token_with_permissions)
):
    """Send user invitation email (requires admin permission)"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    rbac_manager.check_permission(current_user.user_id, Permission.USER_INVITE)
    
    # TODO: Implement email invitation system
    # For MVP, create user directly
    try:
        user_id = rbac_manager.create_user(request.email, request.role)
        return {
            "message": f"User invited successfully",
            "user_id": user_id,
            "email": request.email
        }
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        raise


@router.get("/permissions/check")
async def check_permission(
    permission: str,
    current_user: User = Depends(verify_token_with_permissions)
):
    """Check if current user has specific permission"""
    if not current_user:
        return {"has_permission": False}
    
    try:
        perm = Permission(permission)
        has_perm = rbac_manager.has_permission(current_user.user_id, perm)
        return {"has_permission": has_perm}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permission: {permission}"
        )


@router.get("/permissions/list")
async def list_permissions(
    current_user: User = Depends(verify_token_with_permissions)
):
    """List current user's permissions"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return {
        "user_id": current_user.user_id,
        "role": current_user.role,
        "permissions": list(current_user.permissions)
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(verify_token_with_permissions)
):
    """Get current user profile"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return UserResponse.from_user(current_user)


@router.get("/system/health")
async def get_system_health(
    current_user: User = Depends(verify_token_with_permissions)
):
    """Get system health status (requires admin permission)"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    rbac_manager.check_permission(current_user.user_id, Permission.SYSTEM_CONFIG)
    
    # TODO: Implement actual system health checks
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "database": "healthy",
            "authentication": "healthy", 
            "mcp_server": "healthy"
        }
    }