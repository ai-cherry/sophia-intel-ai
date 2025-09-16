from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/models", tags=["models"]) 


class ModelInfo(BaseModel):
    id: str = Field(..., description="Model identifier (provider/name)")
    provider: Optional[str] = Field(None, description="Provider name")
    display_name: Optional[str] = Field(None, description="Human-friendly name")
    context: Optional[int] = Field(None, description="Context window tokens")
    enabled: bool = Field(True, description="Whether the model is enabled")
    priority: Optional[int] = Field(None, description="Lower means higher priority")


def _load_user_models() -> List[ModelInfo]:
    """Load models from config/user_models_config.yaml if available.

    Fallback to a small default set if the file is missing or invalid.
    """
    config_path = Path("config/user_models_config.yaml")
    items: List[ModelInfo] = []
    if config_path.exists():
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            models = (data.get("models") or {})
            for mid, meta in models.items():
                items.append(
                    ModelInfo(
                        id=mid,
                        provider=(meta or {}).get("provider"),
                        display_name=(meta or {}).get("display_name"),
                        context=(meta or {}).get("context"),
                        enabled=bool((meta or {}).get("enabled", True)),
                        priority=(meta or {}).get("priority"),
                    )
                )
        except Exception:
            # ignore parse errors, fall back
            pass
    if not items:
        items = [
            ModelInfo(id="openai/gpt-4o-mini", provider="openai", display_name="GPT‑4o mini", context=128000),
            ModelInfo(id="anthropic/claude-sonnet-4", provider="anthropic", display_name="Claude Sonnet 4", context=200000),
            ModelInfo(id="google/gemini-2.5-flash", provider="google", display_name="Gemini 2.5 Flash", context=1000000),
            ModelInfo(id="x-ai/grok-code-fast-1", provider="x-ai", display_name="Grok Code Fast 1", context=128000),
        ]
    return items


@router.get("", response_model=List[ModelInfo])
async def list_models() -> List[ModelInfo]:
    return _load_user_models()

