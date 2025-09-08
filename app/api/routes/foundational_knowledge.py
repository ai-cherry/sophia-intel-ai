"""
API endpoints for Foundational Knowledge management
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.middleware.auth import get_current_user, verify_admin_access, verify_api_key
from app.api.middleware.rate_limit import rate_limit
from app.core.ai_logger import logger
from app.knowledge.foundational_manager import FoundationalKnowledgeManager
from app.knowledge.models import (
    KnowledgeClassification,
    KnowledgeEntity,
    KnowledgePriority,
)
from app.sync.airtable_sync import AirtableSync

router = APIRouter(prefix="/api/knowledge", tags=["foundational-knowledge"])


# Create helper dependencies
async def require_authentication(user: str = Depends(verify_api_key)) -> dict:
    """Require authentication for endpoints"""
    return {"user": user}


async def require_admin(user: str = Depends(verify_admin_access)) -> dict:
    """Require admin access for endpoints"""
    return {"user": user}


# Request/Response models
class KnowledgeCreateRequest(BaseModel):
    """Request model for creating knowledge"""

    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    classification: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    content: dict[str, Any]
    metadata: Optional[dict[str, Any]] = None


class KnowledgeUpdateRequest(BaseModel):
    """Request model for updating knowledge"""

    name: Optional[str] = None
    category: Optional[str] = None
    classification: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    content: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class KnowledgeResponse(BaseModel):
    """Response model for knowledge entity"""

    id: str
    name: str
    category: str
    classification: str
    priority: int
    content: dict[str, Any]
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


# Lazy-load managers to avoid initialization at import time
_manager = None
_sync_service = None


def get_manager():
    """Get or create FoundationalKnowledgeManager instance"""
    global _manager
    if _manager is None:
        _manager = FoundationalKnowledgeManager()
    return _manager


def get_sync_service():
    """Get or create AirtableSync instance"""
    global _sync_service
    if _sync_service is None:
        _sync_service = AirtableSync()
    return _sync_service


# ========== CRUD Endpoints ==========


@router.post("/", response_model=KnowledgeResponse)
@rate_limit(limit=30)  # Allow 30 creates per minute
async def create_knowledge(
    request: KnowledgeCreateRequest, __user: dict = Depends(require_authentication)
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
        created = await get_manager().create(entity)

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
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
@rate_limit(limit=60)  # Allow 60 reads per minute
async def get_knowledge(knowledge_id: str, _user: Optional[dict] = Depends(get_current_user)):
    """Get knowledge entity by ID"""
    entity = await get_manager().get(knowledge_id)

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
    knowledge_id: str,
    request: KnowledgeUpdateRequest,
    _user: dict = Depends(require_authentication),
):
    """Update existing knowledge entity"""
    # Get existing entity
    entity = await get_manager().get(knowledge_id)
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
    updated = await get_manager().update(entity)

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
    knowledge_id: str, _user: dict = Depends(require_admin)  # Only admins can delete
):
    """Delete knowledge entity"""
    result = await get_manager().delete(knowledge_id)

    if not result:
        raise HTTPException(status_code=404, detail="Knowledge not found")

    return {"message": "Knowledge deleted successfully"}


# ========== Search & List Endpoints ==========


@router.get("/", response_model=list[KnowledgeResponse])
@rate_limit(limit=60)  # Allow 60 list requests per minute
async def list_knowledge(
    classification: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_active: bool = Query(True),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    _user: Optional[dict] = Depends(get_current_user),
):
    """List knowledge entities with filters"""
    entities = await get_manager().storage.list_knowledge(
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


@router.get("/search", response_model=list[KnowledgeResponse])
@rate_limit(limit=30)  # Lower limit for search operations
async def search_knowledge(
    query: str = Query(..., min_length=1),
    include_operational: bool = Query(False),
    _user: Optional[dict] = Depends(get_current_user),
):
    """Search knowledge entities"""
    results = await get_manager().search(query, include_operational)

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


@router.get("/foundational", response_model=list[KnowledgeResponse])
@rate_limit(limit=60)  # Allow 60 foundational list requests per minute
async def list_foundational(_user: Optional[dict] = Depends(get_current_user)):
    """List all foundational knowledge"""
    entities = await get_manager().list_foundational()

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
async def get_pay_ready_context(_user: dict = Depends(require_authentication)):
    """Get comprehensive Pay-Ready context"""
    return await get_manager().get_pay_ready_context()


# ========== Version Endpoints ==========


@router.get("/{knowledge_id}/versions")
@rate_limit(limit=30)  # Allow 30 version history requests per minute
async def get_version_history(knowledge_id: str, _user: Optional[dict] = Depends(get_current_user)):
    """Get version history for knowledge entity"""
    versions = await get_manager().get_version_history(knowledge_id)

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
    _user: dict = Depends(require_admin),  # Only admins can restore
):
    """Restore knowledge to specific version"""
    try:
        restored = await get_manager().rollback_to_version(knowledge_id, version_number)

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
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{knowledge_id}/compare")
@rate_limit(limit=20)  # Allow 20 comparison requests per minute
async def compare_versions(
    knowledge_id: str,
    v1: int = Query(...),
    v2: int = Query(...),
    _user: Optional[dict] = Depends(get_current_user),
):
    """Compare two versions of knowledge"""
    try:
        comparison = await get_manager().compare_versions(knowledge_id, v1, v2)
        return comparison

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


# ========== Sync Endpoints ==========


@router.post("/sync", response_model=SyncStatusResponse)
@rate_limit(limit=5)  # Very limited for sync operations
async def trigger_sync(
    background_tasks: BackgroundTasks,
    sync_type: str = Query("incremental", regex="^(full|incremental)$"),
    _user: dict = Depends(require_admin),  # Only admins can trigger sync
):
    """Trigger Airtable synchronization"""

    async def run_sync():
        if sync_type == "full":
            await get_sync_service().full_sync()
        else:
            await get_sync_service().incremental_sync()

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
async def get_sync_status(_user: dict = Depends(require_authentication)):
    """Get current sync status with scheduler information"""
    from app.sync.sync_scheduler import get_sync_scheduler

    scheduler = get_sync_scheduler()
    return scheduler.get_status()


@router.get("/sync/history")
@rate_limit(limit=30)  # Allow 30 history requests per minute
async def get_sync_history(
    limit: int = Query(10, ge=1, le=100), _user: dict = Depends(require_authentication)
):
    """Get sync operation history"""
    from app.sync.sync_scheduler import get_sync_scheduler

    scheduler = get_sync_scheduler()
    return scheduler.get_history(limit=limit)


@router.post("/sync/trigger")
@rate_limit(limit=5)  # Very limited for manual sync triggers
async def trigger_manual_sync(
    sync_type: str = Query("incremental", regex="^(full|incremental)$"),
    _user: dict = Depends(require_admin),  # Only admins can trigger manual sync
):
    """Manually trigger a sync operation"""
    from app.sync.sync_scheduler import get_sync_scheduler

    scheduler = get_sync_scheduler()
    result = await scheduler.trigger_manual_sync(sync_type)

    return {"message": f"Manual {sync_type} sync triggered", "result": result}


@router.post("/sync/resume")
@rate_limit(limit=5)  # Very limited for resume operations
async def resume_sync_scheduler(
    _user: dict = Depends(require_admin),  # Only admins can resume scheduler
):
    """Resume sync scheduler after critical failure"""
    from app.sync.sync_scheduler import get_sync_scheduler

    scheduler = get_sync_scheduler()
    await scheduler.resume_scheduler()

    return {"message": "Sync scheduler resumed successfully"}


# ========== Batch Operations ==========


@router.post("/batch/create")
@rate_limit(limit=10)  # Lower limit for batch operations
async def batch_create_knowledge(
    requests: list[KnowledgeCreateRequest], _user: dict = Depends(require_authentication)
):
    """Create multiple knowledge entities in a batch"""
    if len(requests) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 entities per batch")

    results = {"success": [], "failed": []}

    manager = get_manager()

    for idx, request in enumerate(requests):
        try:
            entity = KnowledgeEntity(
                name=request.name,
                category=request.category,
                content=request.content,
                metadata=request.metadata or {},
            )

            if request.classification:
                entity.classification = KnowledgeClassification(request.classification)
            if request.priority:
                entity.priority = KnowledgePriority(request.priority)

            created = await manager.create(entity)
            results["success"].append({"index": idx, "id": created.id, "name": created.name})

        except Exception as e:
            logger.error(f"Failed to create entity {request.name}: {e}")
            results["failed"].append({"index": idx, "name": request.name, "error": str(e)})

    return {
        "total": len(requests),
        "succeeded": len(results["success"]),
        "failed": len(results["failed"]),
        "results": results,
    }


@router.put("/batch/update")
@rate_limit(limit=10)  # Lower limit for batch operations
async def batch_update_knowledge(
    updates: list[dict[str, Any]], _user: dict = Depends(require_authentication)
):
    """Update multiple knowledge entities in a batch"""
    if len(updates) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 entities per batch")

    results = {"success": [], "failed": []}

    manager = get_manager()

    for idx, update in enumerate(updates):
        try:
            entity_id = update.get("id")
            if not entity_id:
                raise ValueError("Entity ID is required")

            entity = await manager.get(entity_id)
            if not entity:
                raise ValueError(f"Entity {entity_id} not found")

            # Update fields
            if "name" in update:
                entity.name = update["name"]
            if "category" in update:
                entity.category = update["category"]
            if "classification" in update:
                entity.classification = KnowledgeClassification(update["classification"])
            if "priority" in update:
                entity.priority = KnowledgePriority(update["priority"])
            if "content" in update:
                entity.content = update["content"]
            if "metadata" in update:
                entity.metadata.update(update["metadata"])
            if "is_active" in update:
                entity.is_active = update["is_active"]

            updated = await manager.update(entity)
            results["success"].append({"index": idx, "id": updated.id, "name": updated.name})

        except Exception as e:
            logger.error(f"Failed to update entity {update.get('id')}: {e}")
            results["failed"].append({"index": idx, "id": update.get("id"), "error": str(e)})

    return {
        "total": len(updates),
        "succeeded": len(results["success"]),
        "failed": len(results["failed"]),
        "results": results,
    }


@router.post("/batch/delete")
@rate_limit(limit=5)  # Very limited for batch deletes
async def batch_delete_knowledge(
    entity_ids: list[str], _user: dict = Depends(require_admin)  # Only admins can batch delete
):
    """Delete multiple knowledge entities in a batch"""
    if len(entity_ids) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 entities per batch delete")

    results = {"success": [], "failed": []}

    manager = get_manager()

    for entity_id in entity_ids:
        try:
            deleted = await manager.delete(entity_id)
            if deleted:
                results["success"].append(entity_id)
            else:
                results["failed"].append({"id": entity_id, "error": "Entity not found"})
        except Exception as e:
            logger.error(f"Failed to delete entity {entity_id}: {e}")
            results["failed"].append({"id": entity_id, "error": str(e)})

    return {
        "total": len(entity_ids),
        "succeeded": len(results["success"]),
        "failed": len(results["failed"]),
        "results": results,
    }


# ========== Statistics Endpoint ==========


@router.get("/statistics")
@rate_limit(limit=30)  # Allow 30 statistics requests per minute
async def get_statistics(_user: Optional[dict] = Depends(get_current_user)):
    """Get knowledge base statistics"""
    return await get_manager().get_statistics()
