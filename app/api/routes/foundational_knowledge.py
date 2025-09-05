"""
API endpoints for Foundational Knowledge management
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.middleware.auth import get_current_user, require_admin, require_authentication
from app.api.middleware.rate_limit import rate_limit
from app.core.ai_logger import logger
from app.knowledge.foundational_manager import FoundationalKnowledgeManager
from app.knowledge.models import (
    KnowledgeClassification,
    KnowledgeEntity,
    KnowledgePriority,
    PayReadyContext,
)
from app.sync.airtable_sync import AirtableSync

router = APIRouter(prefix="/api/knowledge", tags=["foundational-knowledge"])


# Request/Response models
class KnowledgeCreateRequest(BaseModel):
    """Request model for creating knowledge"""

    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    classification: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeUpdateRequest(BaseModel):
    """Request model for updating knowledge"""

    name: Optional[str] = None
    category: Optional[str] = None
    classification: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    content: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class KnowledgeResponse(BaseModel):
    """Response model for knowledge entity"""

    id: str
    name: str
    category: str
    classification: str
    priority: int
    content: Dict[str, Any]
    is_foundational: bool
    version: int
    created_at: datetime
    updated_at: datetime
    synced_at: Optional[datetime]


class SyncStatusResponse(BaseModel):
    """Response model for sync status"""

    operation_id: str
    operation_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    records_processed: int
    conflicts_detected: int


# Initialize managers
manager = FoundationalKnowledgeManager()
sync_service = AirtableSync()


# ========== CRUD Endpoints ==========


@router.post("/", response_model=KnowledgeResponse)
@rate_limit(limit=30)  # Allow 30 creates per minute
async def create_knowledge(
    request: KnowledgeCreateRequest, user: dict = Depends(require_authentication)
):
    """Create new foundational knowledge entry"""
    try:
        # Create entity from request
        entity = KnowledgeEntity(
            name=request.name,
            category=request.category,
            content=request.content,
            metadata=request.metadata or {},
        )

        # Set classification if provided
        if request.classification:
            entity.classification = KnowledgeClassification(request.classification)

        # Set priority if provided
        if request.priority:
            entity.priority = KnowledgePriority(request.priority)

        # Create in manager
        created = await manager.create(entity)

        return KnowledgeResponse(
            id=created.id,
            name=created.name,
            category=created.category,
            classification=created.classification.value,
            priority=created.priority.value,
            content=created.content,
            is_foundational=created.is_foundational,
            version=created.version,
            created_at=created.created_at,
            updated_at=created.updated_at,
            synced_at=created.synced_at,
        )

    except Exception as e:
        logger.error(f"Failed to create knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
@rate_limit(limit=60)  # Allow 60 reads per minute
async def get_knowledge(knowledge_id: str, user: Optional[dict] = Depends(get_current_user)):
    """Get knowledge entity by ID"""
    entity = await manager.get(knowledge_id)

    if not entity:
        raise HTTPException(status_code=404, detail="Knowledge not found")

    return KnowledgeResponse(
        id=entity.id,
        name=entity.name,
        category=entity.category,
        classification=entity.classification.value,
        priority=entity.priority.value,
        content=entity.content,
        is_foundational=entity.is_foundational,
        version=entity.version,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        synced_at=entity.synced_at,
    )


@router.put("/{knowledge_id}", response_model=KnowledgeResponse)
@rate_limit(limit=30)  # Allow 30 updates per minute
async def update_knowledge(
    knowledge_id: str, request: KnowledgeUpdateRequest, user: dict = Depends(require_authentication)
):
    """Update existing knowledge entity"""
    # Get existing entity
    entity = await manager.get(knowledge_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Knowledge not found")

    # Update fields if provided
    if request.name:
        entity.name = request.name
    if request.category:
        entity.category = request.category
    if request.classification:
        entity.classification = KnowledgeClassification(request.classification)
    if request.priority:
        entity.priority = KnowledgePriority(request.priority)
    if request.content:
        entity.content = request.content
    if request.metadata:
        entity.metadata.update(request.metadata)
    if request.is_active is not None:
        entity.is_active = request.is_active

    # Update via manager
    updated = await manager.update(entity)

    return KnowledgeResponse(
        id=updated.id,
        name=updated.name,
        category=updated.category,
        classification=updated.classification.value,
        priority=updated.priority.value,
        content=updated.content,
        is_foundational=updated.is_foundational,
        version=updated.version,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
        synced_at=updated.synced_at,
    )


@router.delete("/{knowledge_id}")
@rate_limit(limit=20)  # Allow 20 deletes per minute
async def delete_knowledge(
    knowledge_id: str, user: dict = Depends(require_admin)  # Only admins can delete
):
    """Delete knowledge entity"""
    result = await manager.delete(knowledge_id)

    if not result:
        raise HTTPException(status_code=404, detail="Knowledge not found")

    return {"message": "Knowledge deleted successfully"}


# ========== Search & List Endpoints ==========


@router.get("/", response_model=List[KnowledgeResponse])
@rate_limit(limit=60)  # Allow 60 list requests per minute
async def list_knowledge(
    classification: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_active: bool = Query(True),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user: Optional[dict] = Depends(get_current_user),
):
    """List knowledge entities with filters"""
    entities = await manager.storage.list_knowledge(
        classification=classification,
        category=category,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )

    return [
        KnowledgeResponse(
            id=e.id,
            name=e.name,
            category=e.category,
            classification=e.classification.value,
            priority=e.priority.value,
            content=e.content,
            is_foundational=e.is_foundational,
            version=e.version,
            created_at=e.created_at,
            updated_at=e.updated_at,
            synced_at=e.synced_at,
        )
        for e in entities
    ]


@router.get("/search", response_model=List[KnowledgeResponse])
@rate_limit(limit=30)  # Lower limit for search operations
async def search_knowledge(
    query: str = Query(..., min_length=1),
    include_operational: bool = Query(False),
    user: Optional[dict] = Depends(get_current_user),
):
    """Search knowledge entities"""
    results = await manager.search(query, include_operational)

    return [
        KnowledgeResponse(
            id=e.id,
            name=e.name,
            category=e.category,
            classification=e.classification.value,
            priority=e.priority.value,
            content=e.content,
            is_foundational=e.is_foundational,
            version=e.version,
            created_at=e.created_at,
            updated_at=e.updated_at,
            synced_at=e.synced_at,
        )
        for e in results
    ]


@router.get("/foundational", response_model=List[KnowledgeResponse])
@rate_limit(limit=60)  # Allow 60 foundational list requests per minute
async def list_foundational(user: Optional[dict] = Depends(get_current_user)):
    """List all foundational knowledge"""
    entities = await manager.list_foundational()

    return [
        KnowledgeResponse(
            id=e.id,
            name=e.name,
            category=e.category,
            classification=e.classification.value,
            priority=e.priority.value,
            content=e.content,
            is_foundational=e.is_foundational,
            version=e.version,
            created_at=e.created_at,
            updated_at=e.updated_at,
            synced_at=e.synced_at,
        )
        for e in entities
    ]


# ========== Context Endpoints ==========


@router.get("/context/pay-ready")
@rate_limit(limit=10)  # Very limited for context operations
async def get_pay_ready_context(user: dict = Depends(require_authentication)):
    """Get comprehensive Pay-Ready context"""
    return await manager.get_pay_ready_context()


# ========== Version Endpoints ==========


@router.get("/{knowledge_id}/versions")
@rate_limit(limit=30)  # Allow 30 version history requests per minute
async def get_version_history(knowledge_id: str, user: Optional[dict] = Depends(get_current_user)):
    """Get version history for knowledge entity"""
    versions = await manager.get_version_history(knowledge_id)

    return [
        {
            "version_id": v.version_id,
            "version_number": v.version_number,
            "change_summary": v.change_summary,
            "changed_by": v.changed_by,
            "created_at": v.created_at,
        }
        for v in versions
    ]


@router.post("/{knowledge_id}/restore")
@rate_limit(limit=5)  # Very limited for restore operations
async def restore_version(
    knowledge_id: str,
    version_number: int,
    user: dict = Depends(require_admin),  # Only admins can restore
):
    """Restore knowledge to specific version"""
    try:
        restored = await manager.rollback_to_version(knowledge_id, version_number)

        return KnowledgeResponse(
            id=restored.id,
            name=restored.name,
            category=restored.category,
            classification=restored.classification.value,
            priority=restored.priority.value,
            content=restored.content,
            is_foundational=restored.is_foundational,
            version=restored.version,
            created_at=restored.created_at,
            updated_at=restored.updated_at,
            synced_at=restored.synced_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{knowledge_id}/compare")
@rate_limit(limit=20)  # Allow 20 comparison requests per minute
async def compare_versions(
    knowledge_id: str,
    v1: int = Query(...),
    v2: int = Query(...),
    user: Optional[dict] = Depends(get_current_user),
):
    """Compare two versions of knowledge"""
    try:
        comparison = await manager.compare_versions(knowledge_id, v1, v2)
        return comparison

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ========== Sync Endpoints ==========


@router.post("/sync", response_model=SyncStatusResponse)
@rate_limit(limit=5)  # Very limited for sync operations
async def trigger_sync(
    background_tasks: BackgroundTasks,
    sync_type: str = Query("incremental", regex="^(full|incremental)$"),
    user: dict = Depends(require_admin),  # Only admins can trigger sync
):
    """Trigger Airtable synchronization"""

    async def run_sync():
        if sync_type == "full":
            await sync_service.full_sync()
        else:
            await sync_service.incremental_sync()

    # Run sync in background
    background_tasks.add_task(run_sync)

    # Return immediate response
    return SyncStatusResponse(
        operation_id="pending",
        operation_type=f"{sync_type}_sync",
        status="queued",
        started_at=datetime.utcnow(),
        completed_at=None,
        records_processed=0,
        conflicts_detected=0,
    )


@router.get("/sync/status")
@rate_limit(limit=30)  # Allow 30 sync status requests per minute
async def get_sync_status(user: dict = Depends(require_authentication)):
    """Get current sync status"""
    # Get latest sync operations from storage
    # This is a simplified version
    return {
        "last_sync": datetime.utcnow().isoformat(),
        "status": "idle",
        "pending_conflicts": 0,
    }


# ========== Statistics Endpoint ==========


@router.get("/statistics")
@rate_limit(limit=30)  # Allow 30 statistics requests per minute
async def get_statistics(user: Optional[dict] = Depends(get_current_user)):
    """Get knowledge base statistics"""
    return await manager.get_statistics()
