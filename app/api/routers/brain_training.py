import logging
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
