import logging
import time
import os
import tempfile
from pathlib import Path
from typing import Any, Optional
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.integrations.gong_brain_training_adapter import GongBrainTrainingAdapter
from app.memory.unified_memory_store import UnifiedMemoryStore
from app.swarms.knowledge.brain_training import BrainTrainingPipeline
from .brain_training_rate_limiter import upload_limiter
from app.api.routes.agui_stream import bridge_websocket_event
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/brain-training", tags=["brain-training"])
security = HTTPBearer()
# File size limits
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_BATCH_FILES = 10  # Maximum files in batch upload
# Initialize memory system and adapters
memory_system = UnifiedMemoryStore()
adapter = None
def get_gong_adapter():
    """Get or create Gong brain training adapter"""
    global adapter
    if not adapter:
        adapter = GongBrainTrainingAdapter(
            memory_system=memory_system,
            brain_training_pipeline=BrainTrainingPipeline(
                memory_system=memory_system,
                config={
                    "meta_learning_enabled": True,
                    "reinforcement_learning_enabled": True,
                    "adaptive_learning_rate": True,
                },
            ),
        )
    return adapter
@router.post("/gong/upload")
async def upload_gong_csv(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    learning_objectives: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> JSONResponse:
    """
    Upload and process Gong CSV export for brain training
    Args:
        file: CSV file from Gong export
        learning_objectives: Comma-separated learning objectives
    Returns:
        Initial processing status and job ID
    """
    # Apply rate limiting
    client_id = await upload_limiter.get_client_id(request, credentials.credentials)
    await upload_limiter.check_rate_limit(client_id)
    try:
        # Validate file size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB",
            )
        # Reset file position after reading
        await file.seek(0)
        # Validate file type
        if not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        # Save uploaded file temporarily (already read above)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name
        # Parse learning objectives
        objectives = None
        if learning_objectives:
            objectives = [obj.strip() for obj in learning_objectives.split(",")]
        # Start background processing
        job_id = f"gong_training_{Path(tmp_path).stem}"
        background_tasks.add_task(process_gong_training, tmp_path, objectives, job_id)
        return JSONResponse(
            {
                "status": "processing",
                "job_id": job_id,
                "message": "Gong CSV training started in background",
                "file_name": file.filename,
                "file_size": len(file_content),
                "objectives": objectives or ["Default sales learning objectives"],
            }
        )
    except Exception as e:
        logger.error(f"Error uploading Gong CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


JOBS: dict[str, dict[str, Any]] = {}


@router.post("/upload-universal")
async def upload_universal(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    learning_objectives: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> JSONResponse:
    """
    Upload multiple files (txt, md, csv) to train Sophia's brain.
    Parses text content and stores it in the unified memory with provenance metadata.
    Large or binary formats (pdf/docx) are currently rejected for safety.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(status_code=400, detail=f"Too many files. Maximum {MAX_BATCH_FILES}")
    allowed_ext = {".txt", ".md", ".markdown", ".csv"}
    objectives = [o.strip() for o in (learning_objectives or "").split(",") if o.strip()]

    # Collect tasks for background storage
    async def _store_text(job_id: str, name: str, text: str, meta: dict[str, Any]):
        try:
            await memory_system.store(
                content={"title": name, "text": text},
                metadata=meta,
                tags=["brain_training", "upload"],
            )
            # Update job progress
            try:
                JOBS[job_id]["stored"] += 1
            except Exception:
                pass
            # Broadcast progress via AG-UI stream (best-effort)
            try:
                await bridge_websocket_event(
                    {
                        "type": "brain_upload_progress",
                        "job_id": job_id,
                        "stored": JOBS[job_id]["stored"],
                        "accepted": JOBS[job_id]["accepted"],
                        "deduped": JOBS[job_id]["deduped"],
                        "timestamp": time.time(),
                        "domain": "sophia_intel",
                    }
                )
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"Failed to store memory for {name}: {e}")

    import hashlib as _hashlib
    import uuid as _uuid
    job_id = f"upload_{_uuid.uuid4()}"
    JOBS[job_id] = {"accepted": 0, "rejected": 0, "stored": 0, "deduped": 0, "created_at": time.time()}

    accepted, rejected = [], []
    checksums: set[str] = set()
    total_bytes = 0
    for f in files:
        try:
            suffix = ("." + f.filename.split(".")[-1].lower()) if "." in f.filename else ""
            if suffix not in allowed_ext:
                rejected.append({"file": f.filename, "reason": f"Unsupported extension {suffix}"})
                continue
            raw = await f.read()
            if len(raw) > MAX_FILE_SIZE:
                rejected.append({"file": f.filename, "reason": "File too large"})
                continue
            total_bytes += len(raw)
            if total_bytes > 10 * 1024 * 1024:
                rejected.append({"file": f.filename, "reason": "Aggregate payload too large"})
                continue
            # Decode text conservatively
            try:
                text = raw.decode("utf-8", errors="replace")
            except Exception:
                rejected.append({"file": f.filename, "reason": "Decode failed"})
                continue
            # Optional: sanitize CSV formulas
            if suffix == ".csv":
                sanitized_lines = []
                sanitized = 0
                for line in text.splitlines():
                    if line.startswith(("=", "+", "-", "@")):
                        sanitized_lines.append("'" + line)
                        sanitized += 1
                    else:
                        sanitized_lines.append(line)
                text = "\n".join(sanitized_lines)
            # Deduplicate by checksum within this batch
            digest = _hashlib.sha256(text.encode("utf-8")).hexdigest()
            if digest in checksums:
                JOBS[job_id]["deduped"] += 1
                continue
            checksums.add(digest)
            meta = {
                "source": "upload_universal",
                "filename": f.filename,
                "content_type": f.content_type,
                "objectives": objectives,
                "checksum_sha256": digest,
            }
            JOBS[job_id]["accepted"] += 1
            background_tasks.add_task(_store_text, job_id, f.filename, text, meta)
            accepted.append({"file": f.filename, "size": len(raw)})
        except Exception as e:
            rejected.append({"file": f.filename, "reason": str(e)})
            JOBS[job_id]["rejected"] += 1

    return JSONResponse(
        {
            "status": "queued",
            "job_id": job_id,
            "accepted": accepted,
            "rejected": rejected,
            "message": "Files queued for background ingestion into unified memory",
        }
    )


@router.get("/status/{job_id}")
async def upload_status(job_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)) -> JSONResponse:
    """Get status of a universal upload job."""
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JSONResponse({
        "job_id": job_id,
        **job,
    })
@router.get("/gong/status/{job_id}")
async def get_training_status(
    job_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)
) -> JSONResponse:
    """
    Get status of Gong CSV training job
    Args:
        job_id: Training job identifier
    Returns:
        Current status and results if complete
    """
    try:
        adapter = get_gong_adapter()
        # Get training metrics (includes current session info)
        metrics = await adapter.get_training_metrics()
        # Check if this job is active
        if metrics["brain_training_metrics"].get("current_session_id") == job_id:
            status = "in_progress"
        else:
            # Check if completed (simplified - in production use proper job tracking)
            status = (
                "completed"
                if metrics["gong_training_stats"]["total_calls_trained"] > 0
                else "pending"
            )
        return JSONResponse(
            {
                "job_id": job_id,
                "status": status,
                "metrics": metrics["gong_training_stats"],
                "brain_metrics": metrics["brain_training_metrics"],
            }
        )
    except Exception as e:
        logger.error(f"Error getting training status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/gong/query")
async def query_gong_knowledge(
    request: dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> JSONResponse:
    """
    Query learned Gong sales knowledge
    Args:
        request: Query request with 'query' field
    Returns:
        Answer based on learned Gong data
    """
    try:
        query = request.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        adapter = get_gong_adapter()
        result = await adapter.query_learned_sales_knowledge(query)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error querying Gong knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/gong/feedback")
async def submit_training_feedback(
    request: dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> JSONResponse:
    """
    Submit feedback about Gong training quality
    Args:
        request: Feedback data
    Returns:
        Feedback incorporation results
    """
    try:
        adapter = get_gong_adapter()
        result = await adapter.apply_user_feedback(request)
        return JSONResponse({"status": "feedback_received", "result": result})
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/gong/metrics")
async def get_training_metrics(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> JSONResponse:
    """
    Get comprehensive Gong training metrics
    Returns:
        Training statistics and metrics
    """
    try:
        adapter = get_gong_adapter()
        metrics = await adapter.get_training_metrics()
        return JSONResponse(metrics)
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
async def process_gong_training(
    csv_path: str, objectives: Optional[list[str]], job_id: str
):
    """
    Background task to process Gong CSV training
    Args:
        csv_path: Path to temporary CSV file
        objectives: Learning objectives
        job_id: Job identifier
    """
    try:
        adapter = get_gong_adapter()
        # Run training
        result = await adapter.train_from_gong_csv(
            csv_path=csv_path, learning_objectives=objectives
        )
        logger.info(f"Gong training completed for job {job_id}: {result}")
    except Exception as e:
        logger.error(
            f"Error in background training for job {job_id}: {e}", exc_info=True
        )
        # Store error state for status endpoint
        # Store in Redis or database
    finally:
        # Clean up temp file
        try:
            if os.path.exists(csv_path):
                os.remove(csv_path)
                logger.info(f"Cleaned up temp file: {csv_path}")
        except Exception as cleanup_error:
            logger.error(f"Failed to clean up temp file {csv_path}: {cleanup_error}")
# Export router
__all__ = ["router"]
