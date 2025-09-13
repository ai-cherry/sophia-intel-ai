from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ModelProfile:
    id: str
    model: str
    temperature: float
    max_tokens: int
    system_prompt: str
    context: str = "general"
    tools: List[str] = None


_PROFILES: Dict[str, ModelProfile] = {
    "sophia-general": ModelProfile(
        id="sophia-general",
        model="openai/gpt-4o-mini",
        temperature=0.5,
        max_tokens=2000,
        system_prompt=(
            "You are Sophia General Assistant. Be concise, correct, and helpful."
        ),
        context="general",
        tools=["filesystem", "git", "memory"],
    ),
    "sophia-architect": ModelProfile(
        id="sophia-architect",
        model="x-ai/grok-4",
        temperature=0.7,
        max_tokens=8000,
        system_prompt=(
            "You are the System Architect for Sophia-Intel-AI."
            " Design scalable architectures, analyze structure, and propose specifications."
        ),
        context="system_architecture",
        tools=["filesystem", "git", "memory"],
    ),
    "sophia-coder": ModelProfile(
        id="sophia-coder",
        model="mistral/codestral-2501",
        temperature=0.3,
        max_tokens=16000,
        system_prompt=(
            "You are the Implementation Specialist for Sophia-Intel-AI."
            " Write clean, efficient code with tests."
        ),
        context="implementation",
        tools=["filesystem", "git"],
    ),
}


def get_model_profile(profile_id: str) -> ModelProfile:
    return _PROFILES.get(profile_id) or _PROFILES["sophia-general"]


def list_model_profiles() -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for p in _PROFILES.values():
        out.append({
            "id": p.id,
            "model": p.model,
            "context": p.context,
            "tools": p.tools or [],
        })
    return out

