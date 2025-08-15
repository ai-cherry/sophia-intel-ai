# apps/dashboard-backend/services/models.py
import os
import re
import unicodedata
from typing import Dict, Any, List

try:
    import httpx
except ImportError:
    import requests as httpx

ALLOWED_NAMES = {
    "Claude Sonnet 4",
    "Gemini 2.0 Flash", 
    "Gemini 2.5 Flash",
    "DeepSeek V3 0324",
    "DeepSeek V3 0324 (free)",
    "Qwen3 Coder",
    "Gemini 2.5 Pro",
    "Claude 3.7 Sonnet",
    "R1 0528 (free)",
    "Kimi K2",
    "gpt-oss-120b",
    "GLM 4.5",
    "Qwen3 Coder (free)",
    "GPT-5",
    "Mistral Nemo",
    "R1 (free)",
    "Qwen3 30B A3B",
    "Gemini 2.5 Flash Lite",
    "GLM 4.5 Air (free)",
    "GPT-4o-mini",
}

def _norm(s: str) -> str:
    """Normalize string for fuzzy matching"""
    s = unicodedata.normalize("NFKD", s or "").lower()
    s = re.sub(r"[^a-z0-9\.\-\s\(\)]", "", s)
    return re.sub(r"\s+", " ", s).strip()

def get_allowed_models_filtered() -> Dict[str, Any]:
    """Get filtered list of allowed models from OpenRouter"""
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        return {
            "status": "degraded",
            "models": [],
            "reason": "missing OPENROUTER_API_KEY",
            "total_approved": len(ALLOWED_NAMES),
            "available_count": 0
        }

    try:
        headers = {"Authorization": f"Bearer {key}"}
        
        if hasattr(httpx, 'get'):
            r = httpx.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=8.0)
        else:
            r = httpx.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=8.0)
            
        if r.status_code != 200:
            return {
                "status": "error",
                "models": [],
                "reason": f"OpenRouter API returned HTTP {r.status_code}",
                "total_approved": len(ALLOWED_NAMES),
                "available_count": 0
            }
            
        payload = r.json()
        items = payload.get("data", [])

        # Normalize allowed names for fuzzy matching
        allow_norm = {_norm(n) for n in ALLOWED_NAMES}

        allowed = []
        for m in items:
            model_id = _norm(m.get("id", ""))
            model_name = _norm(m.get("name") or m.get("id"))
            
            # Check if this model matches any of our allowed names
            if any(an in model_id or an in model_name for an in allow_norm):
                allowed.append({
                    "id": m.get("id"),
                    "name": m.get("name") or m.get("id"),
                    "context_length": m.get("context_length"),
                    "pricing": m.get("pricing", {}),
                    "allowed": True,
                    "status": "available"
                })

        return {
            "status": "ok",
            "total_approved": len(ALLOWED_NAMES),
            "available_count": len(allowed),
            "models": allowed,
            "last_checked": httpx.get.__module__ if hasattr(httpx, 'get') else "requests"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "models": [],
            "reason": str(e),
            "total_approved": len(ALLOWED_NAMES),
            "available_count": 0
        }

def is_model_allowed(model_id: str) -> bool:
    """Check if a specific model ID is in our allow-list"""
    model_norm = _norm(model_id)
    allow_norm = {_norm(n) for n in ALLOWED_NAMES}
    return any(an in model_norm for an in allow_norm)

