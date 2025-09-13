#!/usr/bin/env python3
"""
User Management API Router for Sophia Intel AI
Handles user CRUD operations, permissions, and access control
"""

import logging
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.user_configuration import (
    AccessLevel,
    BulkUserOperation,
    FeatureAccess,
    UserConfiguration,
    UserCreateRequest,
    UserUpdateRequest,
    UserAccessAudit,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/users", tags=["User Management"])
security = HTTPBearer()

# In-memory storage for demo (replace with database)
USERS_STORE: dict[str, UserConfiguration] = {}
AUDIT_LOG: list[UserAccessAudit] = []

# CEO email for special permissions
CEO_EMAIL = "lynn@sophia-intel.ai"  # Update with actual CEO email


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserConfiguration:
    """Get current authenticated user"""
    # This is a simplified auth check - replace with proper JWT validation
    token = credentials.credentials
    # For demo, extract user_id from token (implement proper JWT decoding)
    user_id = "current_user_id"  # Replace with actual extraction
    
    if user_id not in USERS_STORE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    return USERS_STORE[user_id]


def require_permission(feature: FeatureAccess):
    """Dependency to require specific permission"""
    def permission_checker(current_user: UserConfiguration = Depends(get_current_user)):
        if not current_user.has_feature(feature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {feature.value}"
            )
        return current_user
    return permission_checker


def is_ceo(user: UserConfiguration) -> bool:
    """Check if user is CEO"""
    return user.email == CEO_EMAIL or user.access_level == AccessLevel.OWNER


def log_access(
    user_id: str,
    action: str,
    resource: str,
    resource_id: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None,
):
    """Log user access for audit trail"""
    audit_entry = UserAccessAudit(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        success=success,
        error_message=error_message,
    )
    AUDIT_LOG.append(audit_entry)


@router.post("/", response_model=UserConfiguration)
async def create_user(
    request: UserCreateRequest,
    current_user: UserConfiguration = Depends(require_permission(FeatureAccess.USERS_MANAGE)),
) -> UserConfiguration:
    """Create a new user"""
    try:
        # Generate user ID
        user_id = str(uuid4())
        
        # Create user configuration
        user_config = UserConfiguration(
            user_id=user_id,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            access_level=request.access_level,
            organization_id=current_user.organization_id,  # Same org as creator
            department=request.department,
            team=request.team,
            manager_id=request.manager_id,
        )
        
        # Special handling for schema changes - CEO only
        if request.access_level in [AccessLevel.ADMIN, AccessLevel.OWNER]:
            if not is_ceo(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only CEO can create admin/owner users"
                )
        
        # Store user
        USERS_STORE[user_id] = user_config
        
        # Log action
        log_access(
            user_id=current_user.user_id,
            action="create_user",
            resource="user",
            resource_id=user_id,
        )
        
        logger.info(f"Created user: {user_config.email}")
        
        # Send welcome email if requested
        if request.send_welcome_email:
            # TODO: Implement email sending
            pass
        
        return user_config
        
    except Exception as e:
        log_access(
            user_id=current_user.user_id,
            action="create_user",
            resource="user",
            success=False,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/", response_model=list[UserConfiguration])
async def list_users(
    current_user: UserConfiguration = Depends(require_permission(FeatureAccess.USERS_VIEW)),
    access_level: Optional[AccessLevel] = Query(None),
    department: Optional[str] = Query(None),
    team: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[UserConfiguration]:
    """List users with optional filtering"""
    try:
        # Filter users
        filtered_users = list(USERS_STORE.values())
        
        if access_level:
            filtered_users = [u for u in filtered_users if u.access_level == access_level]
        if department:
            filtered_users = [u for u in filtered_users if u.department == department]
        if team:
            filtered_users = [u for u in filtered_users if u.team == team]
        if is_active is not None:
            filtered_users = [u for u in filtered_users if u.is_active == is_active]
        
        # Apply pagination
        paginated_users = filtered_users[offset:offset + limit]
        
        log_access(
            user_id=current_user.user_id,
            action="list_users",
            resource="users",
        )
        
        return paginated_users
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserConfiguration)
async def get_user(
    user_id: str,
    current_user: UserConfiguration = Depends(require_permission(FeatureAccess.USERS_VIEW)),
) -> UserConfiguration:
    """Get a specific user by ID"""
    if user_id not in USERS_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    log_access(
        user_id=current_user.user_id,
        action="get_user",
        resource="user",
        resource_id=user_id,
    )
    
    return USERS_STORE[user_id]


@router.patch("/{user_id}", response_model=UserConfiguration)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    current_user: UserConfiguration = Depends(require_permission(FeatureAccess.USERS_MANAGE)),
) -> UserConfiguration:
    """Update user configuration"""
    try:
        if user_id not in USERS_STORE:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = USERS_STORE[user_id]
        
        # Check if trying to update access level
        if request.access_level and request.access_level != user.access_level:
            if request.access_level in [AccessLevel.ADMIN, AccessLevel.OWNER]:
                if not is_ceo(current_user):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only CEO can grant admin/owner access"
                    )
        
        # Update fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        log_access(
            user_id=current_user.user_id,
            action="update_user",
            resource="user",
            resource_id=user_id,
        )
        
        logger.info(f"Updated user: {user.email}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        log_access(
            user_id=current_user.user_id,
            action="update_user",
            resource="user",
            resource_id=user_id,
            success=False,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: UserConfiguration = Depends(require_permission(FeatureAccess.USERS_MANAGE)),
) -> dict[str, str]:
    """Delete a user (soft delete by deactivating)"""
    try:
        if user_id not in USERS_STORE:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = USERS_STORE[user_id]
        
        # Prevent deleting CEO
        if is_ceo(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete CEO account"
            )
        
        # Soft delete by deactivating
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        log_access(
            user_id=current_user.user_id,
            action="delete_user",
            resource="user",
            resource_id=user_id,
        )
        
        logger.info(f"Deactivated user: {user.email}")
        return {"message": "User deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        log_access(
            user_id=current_user.user_id,
            action="delete_user",
            resource="user",
            resource_id=user_id,
            success=False,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.post("/bulk", response_model=dict[str, Any])
async def bulk_user_operation(
    operation: BulkUserOperation,
    current_user: UserConfiguration = Depends(require_permission(FeatureAccess.USERS_MANAGE)),
) -> dict[str, Any]:
    """Perform bulk operations on multiple users"""
    try:
        results = {"successful": [], "failed": []}
        
        for user_id in operation.user_ids:
            try:
                if user_id not in USERS_STORE:
                    results["failed"].append({
                        "user_id": user_id,
                        "error": "User not found"
                    })
                    continue
                
                user = USERS_STORE[user_id]
                
                if operation.operation == "activate":
                    user.is_active = True
                elif operation.operation == "deactivate":
                    if is_ceo(user):
                        results["failed"].append({
                            "user_id": user_id,
                            "error": "Cannot deactivate CEO"
                        })
                        continue
                    user.is_active = False
                elif operation.operation == "update_access":
                    new_level = operation.parameters.get("access_level")
                    if new_level in [AccessLevel.ADMIN, AccessLevel.OWNER]:
                        if not is_ceo(current_user):
                            results["failed"].append({
                                "user_id": user_id,
                                "error": "Only CEO can grant admin/owner access"
                            })
                            continue
                    user.access_level = new_level
                else:
                    results["failed"].append({
                        "user_id": user_id,
                        "error": f"Unknown operation: {operation.operation}"
                    })
                    continue
                
                user.updated_at = datetime.utcnow()
                results["successful"].append(user_id)
                
            except Exception as e:
                results["failed"].append({
                    "user_id": user_id,
                    "error": str(e)
                })
        
        log_access(
            user_id=current_user.user_id,
            action="bulk_operation",
            resource="users",
            resource_id=",".join(operation.user_ids),
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk operation failed: {str(e)}"
        )


@router.get("/audit/log", response_model=list[UserAccessAudit])
async def get_audit_log(
    current_user: UserConfiguration = Depends(require_permission(FeatureAccess.USERS_MANAGE)),
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[UserAccessAudit]:
    """Get user access audit log"""
    try:
        # Filter audit log
        filtered_log = AUDIT_LOG
        
        if user_id:
            filtered_log = [a for a in filtered_log if a.user_id == user_id]
        if action:
            filtered_log = [a for a in filtered_log if a.action == action]
        
        # Sort by timestamp (newest first)
        filtered_log.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply pagination
        paginated_log = filtered_log[offset:offset + limit]
        
        return paginated_log
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit log: {str(e)}"
        )


@router.post("/schema-changes")
async def manage_schema_changes(
    changes: dict[str, Any],
    current_user: UserConfiguration = Depends(get_current_user),
) -> dict[str, str]:
    """Manage schema changes - CEO only"""
    if not is_ceo(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Schema changes are restricted to CEO only"
        )
    
    try:
        # Log the schema change request
        log_access(
            user_id=current_user.user_id,
            action="schema_change",
            resource="schema",
            resource_id=None,
        )
        
        # TODO: Implement actual schema change logic
        # This would integrate with your Airtable/database schema management
        
        logger.info(f"CEO {current_user.email} requested schema changes")
        
        return {
            "message": "Schema change request submitted for processing",
            "status": "pending_approval"
        }
        
    except Exception as e:
        log_access(
            user_id=current_user.user_id,
            action="schema_change",
            resource="schema",
            success=False,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema change failed: {str(e)}"
        )
