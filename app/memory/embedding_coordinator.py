"""
Unified Embedding Coordinator

Provides a single entry point for generating embeddings with strategy selection:
- performance: fast, frequent use (Tier B)
- accuracy: high-accuracy, long-context (Tier A)
- hybrid: combine providers for improved robustness
- auto: per-text model selection based on content length/language/priority

Backed by the existing embed_router (Portkey Virtual Keys) with SQLite cache.
"""

from __future__ import annotations

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import math

# Reuse existing dual-tier router and cache
from app.memory.embed_router import (
    choose_model_for_chunk,
    embed_with_cache,
    MODEL_A,
    MODEL_B,
    DIM_A,
    DIM_B,
)

logger = logging.getLogger(__name__)


def _l2_normalize(vec: List[float]) -> List[float]:
    """L2-normalize a vector to unit length to stabilize ensemble combination."""
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return vec
    return [v / norm for v in vec]


