from fastapi import APIRouter, HTTPException, Depends
from app.mcp.memory_adapter import UnifiedMemoryAdapter
from typing import List, Dict, Any

router = APIRouter(prefix="/api/memory", tags=["memory"])

memory_adapter = UnifiedMemoryAdapter()

@router.post("/store")
async def store_memory(
    session_id: str,
    messages: List[Dict],
    metadata: Dict = {}
):
    result = await memory_adapter.store_conversation(
        session_id, messages, metadata
    )
    return result

@router.get("/retrieve/{session_id}")
async def retrieve_memory(
    session_id: str,
    last_n: int = 10,
    include_system: bool = False
):
    return await memory_adapter.retrieve_context(
        session_id, last_n, include_system
    )

# Additional endpoints as per ROO PROMPT (search, export, delete, stats)