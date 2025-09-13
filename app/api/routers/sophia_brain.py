from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, UploadFile, File, Form

from app.sophia_brain.ingestion.file_parser import FileParser
from app.sophia_brain.ingestion.entity_extractor import EntityExtractor
from app.sophia_brain.ingestion.pii_detector import PIIDetector
from app.sophia_brain.airtable.proposal_engine import ProposalEngine
from app.sophia_brain.workflows.approval_system import ApprovalWorkflow
from app.sophia_brain.workflows.audit_logger import AuditLogger


router = APIRouter(prefix="/api/brain/sophia", tags=["sophia-brain"])

_approvals = ApprovalWorkflow()
_audit = AuditLogger()


@router.post("/ingest")
async def ingest_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    content = await file.read()
    parser = FileParser()
    kind, data = parser.parse(file.filename, content)
    extractor = EntityExtractor()
    pii = PIIDetector()
    entities = []
    if kind == "csv" and isinstance(data, list):
        entities = extractor.extract_from_records(data)
    elif kind == "json":
        if isinstance(data, list):
            entities = extractor.extract_from_records(data)
        elif isinstance(data, dict):
            entities = extractor.extract_from_records([data])
    elif kind == "text":
        # best-effort: no entity extraction from raw text in this stub
        pass
    await _audit.log("ingest", {"filename": file.filename, "kind": kind, "entities": len(entities)})
    return {"kind": kind, "entities": entities, "pii_sample": pii.detect_and_classify(str(data)[:2000], file.filename)}


@router.post("/propose-schema")
async def propose_schema_from_entities(payload: Dict[str, Any]) -> Dict[str, Any]:
    entities = payload.get("entities", [])
    engine = ProposalEngine()
    proposal = engine.propose_from_entities(entities)
    await _audit.log("propose_schema", {"fields": len(proposal.get("fields", []))})
    return {"proposal": proposal}


@router.post("/approval")
async def create_approval(payload: Dict[str, Any]) -> Dict[str, Any]:
    proposal = payload.get("proposal", {})
    result = await _approvals.propose_schema_change(proposal)
    await _audit.log("approval_create", {"id": result.get("id")})
    return result


@router.post("/approval/{request_id}/approve")
async def approve(request_id: str) -> Dict[str, Any]:
    result = await _approvals.approve(request_id)
    await _audit.log("approval_approve", {"id": request_id, "result": result})
    return result

