from __future__ import annotations

import time
import uuid
from typing import Any, Dict


class ApprovalWorkflow:
    """Minimal in-memory approval workflow for schema proposals.

    In production, persist in DB and add auth/ACL.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}

    async def propose_schema_change(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        rid = str(uuid.uuid4())
        item = {
            "id": rid,
            "status": "pending",
            "proposal": proposal,
            "created_at": time.time(),
        }
        self._store[rid] = item
        return {"id": rid, "status": "pending"}

    async def approve(self, request_id: str) -> Dict[str, Any]:
        if request_id not in self._store:
            return {"error": "not_found"}
        self._store[request_id]["status"] = "approved"
        return {"id": request_id, "status": "approved"}

    async def get(self, request_id: str) -> Dict[str, Any]:
        return self._store.get(request_id, {"error": "not_found"})

