#!/usr/bin/env python3
"""
User Configuration Models for Sophia Intel AI
Handles user profiles, permissions, and access control settings
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, validator


class AccessLevel(str, Enum):
    """User access levels"""
    VIEWER = "viewer"  # Read-only access
    ANALYST = "analyst"  # Can run analyses and queries
    DEVELOPER = "developer"  # Can modify agents and workflows
    ADMIN = "admin"  # Full system access
    OWNER = "owner"  # Organization owner


class FeatureAccess(str, Enum):
    """Individual feature access flags"""
    BRAIN_VIEW = "brain_view"
    BRAIN_EDIT = "brain_edit"
    AGENTS_VIEW = "agents_view"
    AGENTS_CREATE = "agents_create"
    AGENTS_EDIT = "agents_edit"
    INTEGRATIONS_VIEW = "integrations_view"
    INTEGRATIONS_MANAGE = "integrations_manage"
    ANALYTICS_VIEW = "analytics_view"
    ANALYTICS_EXPORT = "analytics_export"
    WORKFLOWS_VIEW = "workflows_view"
    WORKFLOWS_CREATE = "workflows_create"
    WORKFLOWS_EXECUTE = "workflows_execute"
    VOICE_ACCESS = "voice_access"
    API_ACCESS = "api_access"
    BILLING_VIEW = "billing_view"
    BILLING_MANAGE = "billing_manage"
    USERS_VIEW = "users_view"
    USERS_MANAGE = "users_manage"
    SETTINGS_VIEW = "settings_view"
    SETTINGS_MANAGE = "settings_manage"


class DataAccessPolicy(BaseModel):
    """Data access policies for users"""
    allow_pii_access: bool = False
    allowed_data_sources: list[str] = Field(default_factory=list)
    restricted_tables: list[str] = Field(default_factory=list)
    data_retention_days: int = 90
    export_allowed: bool = True
    max_export_rows: int = 10000
    allowed_export_formats: list[str] = Field(
        default_factory=lambda: ["csv", "json", "xlsx"]
    )


class NotificationPreferences(BaseModel):
    """User notification preferences"""
    email_enabled: bool = True
    slack_enabled: bool = False
    in_app_enabled: bool = True
    workflow_completion: bool = True
    error_alerts: bool = True
    daily_summary: bool = False
    weekly_report: bool = True
    alert_threshold: str = "error"  # error, warning, info


class UIPreferences(BaseModel):
    """User interface preferences"""
    theme: str = "light"  # light, dark, auto
    sidebar_collapsed: bool = False
    default_dashboard: str = "overview"
    language: str = "en"
    timezone: str = "America/Los_Angeles"
    date_format: str = "MM/DD/YYYY"
    show_tooltips: bool = True
    animation_enabled: bool = True
    sophia_personality: str = "professional"  # professional, friendly, technical
    voice_enabled: bool = False
    voice_gender: str = "female"


class ApiKeyConfiguration(BaseModel):
    """API key configuration for user"""
    key_id: str
    key_prefix: str  # First 8 chars for identification
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    scopes: list[str] = Field(default_factory=list)
    is_active: bool = True
    description: Optional[str] = None


class UserConfiguration(BaseModel):
    """Main user configuration model"""
    # Core user info
    user_id: str = Field(..., description="Unique user identifier")
    email: EmailStr
    first_name: str
    last_name: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Access control
    access_level: AccessLevel = AccessLevel.VIEWER
    feature_access: list[FeatureAccess] = Field(default_factory=list)
    data_access_policy: DataAccessPolicy = Field(default_factory=DataAccessPolicy)
    
    # Organization
    organization_id: str
    department: Optional[str] = None
    team: Optional[str] = None
    manager_id: Optional[str] = None
    
    # Preferences
    notification_preferences: NotificationPreferences = Field(
        default_factory=NotificationPreferences
    )
    ui_preferences: UIPreferences = Field(default_factory=UIPreferences)
    
    # API access
    api_keys: list[ApiKeyConfiguration] = Field(default_factory=list)
    
    # Status
    is_active: bool = True
    is_verified: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Custom settings
    custom_settings: dict[str, Any] = Field(default_factory=dict)
    
    @validator("display_name", always=True)
    def set_display_name(cls, v, values):
        """Auto-generate display name if not provided"""
        if not v and "first_name" in values and "last_name" in values:
            return f"{values['first_name']} {values['last_name']}"
        return v
    
    @validator("feature_access", always=True)
    def set_default_features(cls, v, values):
        """Set default features based on access level"""
        if not v and "access_level" in values:
            level = values["access_level"]
            if level == AccessLevel.VIEWER:
                return [
                    FeatureAccess.BRAIN_VIEW,
                    FeatureAccess.AGENTS_VIEW,
                    FeatureAccess.INTEGRATIONS_VIEW,
                    FeatureAccess.ANALYTICS_VIEW,
                    FeatureAccess.WORKFLOWS_VIEW,
                ]
            elif level == AccessLevel.ANALYST:
                return [
                    FeatureAccess.BRAIN_VIEW,
                    FeatureAccess.BRAIN_EDIT,
                    FeatureAccess.AGENTS_VIEW,
                    FeatureAccess.INTEGRATIONS_VIEW,
                    FeatureAccess.ANALYTICS_VIEW,
                    FeatureAccess.ANALYTICS_EXPORT,
                    FeatureAccess.WORKFLOWS_VIEW,
                    FeatureAccess.WORKFLOWS_EXECUTE,
                    FeatureAccess.VOICE_ACCESS,
                ]
            elif level == AccessLevel.DEVELOPER:
                return [
                    FeatureAccess.BRAIN_VIEW,
                    FeatureAccess.BRAIN_EDIT,
                    FeatureAccess.AGENTS_VIEW,
                    FeatureAccess.AGENTS_CREATE,
                    FeatureAccess.AGENTS_EDIT,
                    FeatureAccess.INTEGRATIONS_VIEW,
                    FeatureAccess.INTEGRATIONS_MANAGE,
                    FeatureAccess.ANALYTICS_VIEW,
                    FeatureAccess.ANALYTICS_EXPORT,
                    FeatureAccess.WORKFLOWS_VIEW,
                    FeatureAccess.WORKFLOWS_CREATE,
                    FeatureAccess.WORKFLOWS_EXECUTE,
                    FeatureAccess.VOICE_ACCESS,
                    FeatureAccess.API_ACCESS,
                ]
            elif level in [AccessLevel.ADMIN, AccessLevel.OWNER]:
                # Admin/Owner gets all features
                return list(FeatureAccess)
        return v
    
    def has_feature(self, feature: FeatureAccess) -> bool:
        """Check if user has access to a specific feature"""
        return feature in self.feature_access
    
    def can_access_data_source(self, source: str) -> bool:
        """Check if user can access a specific data source"""
        if not self.data_access_policy.allowed_data_sources:
            # Empty list means all sources allowed
            return source not in self.data_access_policy.restricted_tables
        return source in self.data_access_policy.allowed_data_sources
    
    class Config:
        """Pydantic config"""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class UserCreateRequest(BaseModel):
    """Request model for creating a new user"""
    email: EmailStr
    first_name: str
    last_name: str
    access_level: AccessLevel = AccessLevel.VIEWER
    department: Optional[str] = None
    team: Optional[str] = None
    manager_id: Optional[str] = None
    send_welcome_email: bool = True


class UserUpdateRequest(BaseModel):
    """Request model for updating user configuration"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    access_level: Optional[AccessLevel] = None
    feature_access: Optional[list[FeatureAccess]] = None
    data_access_policy: Optional[DataAccessPolicy] = None
    department: Optional[str] = None
    team: Optional[str] = None
    manager_id: Optional[str] = None
    notification_preferences: Optional[NotificationPreferences] = None
    ui_preferences: Optional[UIPreferences] = None
    is_active: Optional[bool] = None
    custom_settings: Optional[dict[str, Any]] = None


class BulkUserOperation(BaseModel):
    """Bulk user operation request"""
    user_ids: list[str]
    operation: str  # activate, deactivate, update_access, delete
    parameters: dict[str, Any] = Field(default_factory=dict)


class UserAccessAudit(BaseModel):
    """User access audit log entry"""
    user_id: str
    action: str
    resource: str
    resource_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
