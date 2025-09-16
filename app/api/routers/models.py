from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/models", tags=["models"]) 


class ModelInfo(BaseModel):
    id: str = Field(..., description="Model identifier (provider/name)")
    provider: Optional[str] = Field(None, description="Provider name")
    display_name: Optional[str] = Field(None, description="Human-friendly name")
    context: Optional[int] = Field(None, description="Context window tokens")
    enabled: bool = Field(True, description="Whether the model is enabled")
    priority: Optional[int] = Field(None, description="Lower means higher priority")


def _config_path() -> Path:
    env_path = os.getenv("MODELS_CONFIG_PATH")
    if env_path:
        return Path(env_path)
    return Path("config/user_models_config.yaml")


def _load_user_models() -> List[ModelInfo]:
    """Load models from config/user_models_config.yaml if available.

    Fallback to a small default set if the file is missing or invalid.
    """
    config_path = _config_path()
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


def _load_yaml(path: Path) -> Dict[str, Any]:
    if path.exists():
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            return {}
    return {}


def _write_yaml(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _mutate_model(model_id: str, mutate: callable) -> List[ModelInfo]:
    path = _config_path()
    data = _load_yaml(path)
    models = data.setdefault("models", {})
    if model_id not in models:
        models[model_id] = {"enabled": True, "priority": 5}
    mutate(models[model_id])
    _write_yaml(path, data)
    return _load_user_models()


class ModelUpdate(BaseModel):
    enabled: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=10)


from app.api.security.rbac import require_admin


@router.post("/{model_id}/enable", response_model=List[ModelInfo], dependencies=[Depends(require_admin)])
async def enable_model(model_id: str) -> List[ModelInfo]:
    return _mutate_model(model_id, lambda m: m.update({"enabled": True}))


@router.post("/{model_id}/disable", response_model=List[ModelInfo], dependencies=[Depends(require_admin)])
async def disable_model(model_id: str) -> List[ModelInfo]:
    return _mutate_model(model_id, lambda m: m.update({"enabled": False}))


@router.post("/{model_id}/priority", response_model=List[ModelInfo], dependencies=[Depends(require_admin)])
async def set_priority(model_id: str, upd: ModelUpdate) -> List[ModelInfo]:
    if upd.priority is None:
        return _load_user_models()
    return _mutate_model(model_id, lambda m: m.update({"priority": int(upd.priority)}))
