from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Request, Depends

from app.sophia_brain.controls.store import ControlsStore, DEFAULT_CONTROLS
from app.api.middleware.rbac import ceo_only, get_current_user, PermissionChecker
from app.models.user_configuration import UserConfiguration, FeatureAccess


router = APIRouter(prefix="/api/brain/controls", tags=["sophia-brain-controls"])
store = ControlsStore()


@router.get("")
async def get_controls(request: Request) -> Dict[str, Any]:
    """Get brain control settings - available to users with brain_view permission"""
    user = get_current_user(request)
    if not user.has_feature(FeatureAccess.BRAIN_VIEW):
        raise HTTPException(403, "Insufficient permissions to view brain controls")
    return store.load()


def _validate_payload(payload: Dict[str, Any]) -> None:
    # Minimal structural validation; allow partial updates
    if not isinstance(payload, dict):
        raise HTTPException(400, "Invalid payload")
    for k in payload.keys():
        if k not in DEFAULT_CONTROLS:
            raise HTTPException(400, f"Unknown control group: {k}")


@router.put("")
async def update_controls(request: Request, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Update brain control settings - CEO only for schema changes"""
    user = get_current_user(request)
    
    # Check if this is a schema-related change
    schema_related_keys = ["schema", "table_structure", "field_definitions", "data_model"]
    is_schema_change = any(key in str(payload).lower() for key in schema_related_keys)
    
    if is_schema_change:
        # Schema changes are CEO-only
        if not PermissionChecker.can_modify_schema(user):
            raise HTTPException(
                403, 
                "Schema modifications are restricted to CEO only. "
                "Please contact Lynn for schema change requests."
            )
    else:
        # Non-schema changes require brain_edit permission
        if not user.has_feature(FeatureAccess.BRAIN_EDIT):
            raise HTTPException(403, "Insufficient permissions to edit brain controls")
    
    _validate_payload(payload)
    current = store.load()
    # deep merge
    def merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(a)
        for k, v in b.items():
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                out[k] = merge(out[k], v)
            else:
                out[k] = v
        return out

    updated = merge(current, payload)
    store.save(updated)
    
    # Log schema changes for audit
    if is_schema_change:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"CEO {user.email} modified schema controls: {payload}")
    
    return updated

