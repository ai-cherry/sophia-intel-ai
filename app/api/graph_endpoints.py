from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.retrieval.graph_retriever import (
    GraphRetriever,
    GraphSearchRequest as RetrieverSearchRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class GraphSearchRequest(BaseModel):
    query: str = Field(..., description="User query")
    top_k: int = Field(10, ge=1, le=100, description="Max results to return")
    hops: int = Field(0, ge=0, le=3, description="Future multi-hop traversal depth (0 = disabled)")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Metadata filters, e.g., {'repo_path': 'app/'}")
