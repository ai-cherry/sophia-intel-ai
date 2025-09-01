"""
Embedding router with caching for dual-tier embeddings.
Routes to appropriate model based on chunk characteristics.
"""

from __future__ import annotations
import os
import sqlite3
import hashlib
import json
import time
from typing import List, Tuple, Optional
from openai import OpenAI
from app.core.circuit_breaker import with_circuit_breaker, get_llm_circuit_breaker, get_weaviate_circuit_breaker, get_redis_circuit_breaker, get_webhook_circuit_breaker

# Configuration from environment
EMBED_BASE_URL = os.getenv("EMBED_BASE_URL", "https://api.portkey.ai/v1")
EMBED_API_KEY = os.getenv("EMBED_API_KEY", os.getenv("VK_TOGETHER", ""))  # Portkey Virtual Key for Together

# Tier A: Long context, high accuracy (32k tokens)
MODEL_A = os.getenv("EMBED_MODEL_A", "togethercomputer/m2-bert-80M-32k-retrieval")
DIM_A = int(os.getenv("EMBED_DIM_A", "768"))

# Tier B: Fast, frequent use
MODEL_B = os.getenv("EMBED_MODEL_B", "BAAI/bge-large-en-v1.5")
DIM_B = int(os.getenv("EMBED_DIM_B", "1024"))

# Initialize OpenAI client for embeddings (via Portkey)
_EMBED = OpenAI(base_url=EMBED_BASE_URL, api_key=EMBED_API_KEY)

# Cache configuration
_CACHE_PATH = "tmp/embeddings_cache.db"

def _ensure_cache():
    """Ensure cache database exists and is initialized."""
    os.makedirs("tmp", exist_ok=True)
    conn = sqlite3.connect(_CACHE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache(
            sha TEXT NOT NULL,
            model TEXT NOT NULL,
            vec TEXT NOT NULL,
            ts REAL NOT NULL,
            PRIMARY KEY(sha, model)
        )
    """)
    conn.commit()
    return conn

def _sha(data: str) -> str:
    """Generate SHA-1 hash of text."""
    return hashlib.sha1(data.encode("utf-8")).hexdigest()

def _cache_get(conn, sha: str, model: str) -> Optional[List[float]]:
    """Retrieve cached embedding if exists."""
    cur = conn.execute(
        "SELECT vec FROM cache WHERE sha=? AND model=?",
        (sha, model)
    )
    row = cur.fetchone()
    return json.loads(row[0]) if row else None

def _cache_put(conn, sha: str, model: str, vec: List[float]) -> None:
    """Store embedding in cache."""
    conn.execute(
        "INSERT OR REPLACE INTO cache(sha, model, vec, ts) VALUES(?, ?, ?, ?)",
        (sha, model, json.dumps(vec), time.time())
    )
    conn.commit()

@with_circuit_breaker("external_api")
def embed_batch(texts: List[str], model: str) -> List[List[float]]:
    """
    Call Portkey→Together through OpenAI SDK for batch embedding.
    
    Args:
        texts: List of texts to embed
        model: Model identifier
    
    Returns:
        List of embedding vectors
    """
    r = _EMBED.embeddings.create(model=model, input=texts)
    return [d.embedding for d in r.data]

def choose_model_for_chunk(
    text: str,
    lang: Optional[str] = None,
    priority: Optional[str] = None
) -> Tuple[str, int]:
    """
    Choose appropriate embedding model based on chunk characteristics.
    
    Args:
        text: Text content to embed
        lang: Programming language (optional)
        priority: Priority level (optional)
    
    Returns:
        Tuple of (model_name, dimension)
    """
    # Estimate token count (rough: 1 token ≈ 4 chars)
    tok_est = max(1, len(text) // 4)
    
    # Use Tier A for:
    # - High priority chunks
    # - Long chunks (>2k tokens)
    # - Complex languages requiring context
    if priority == "high" or tok_est > 2000 or lang in ["rust", "cpp", "java"]:
        return MODEL_A, DIM_A
    
    # Default to Tier B for speed
    return MODEL_B, DIM_B

def embed_with_cache(texts: List[str], model: str) -> List[List[float]]:
    """
    Embed texts with caching to avoid redundant API calls.
    
    Args:
        texts: List of texts to embed
        model: Model to use
    
    Returns:
        List of embedding vectors
    """
    conn = _ensure_cache()
    out: List[List[float]] = []
    to_fetch_idx = []
    to_fetch_txt = []
    shas = []
    
    # Check cache for each text
    for i, t in enumerate(texts):
        s = _sha(t)
        shas.append(s)
        v = _cache_get(conn, s, model)
        if v is None:
            to_fetch_idx.append(i)
            to_fetch_txt.append(t)
            out.append(None)  # Placeholder
        else:
            out.append(v)
    
    # Fetch missing embeddings
    if to_fetch_txt:
        fresh = embed_batch(to_fetch_txt, model)
        fetch_idx = 0
        for i in range(len(texts)):
            if out[i] is None:  # Was a placeholder
                vec = fresh[fetch_idx]
                fetch_idx += 1
                out[i] = vec
                _cache_put(conn, shas[i], model, vec)
    
    conn.close()
    return out

def clear_cache() -> None:
    """Clear the embedding cache."""
    if os.path.exists(_CACHE_PATH):
        os.remove(_CACHE_PATH)
    print(f"Cleared embedding cache at {_CACHE_PATH}")