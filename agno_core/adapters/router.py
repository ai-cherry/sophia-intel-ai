from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .model_factory import ModelFactory, ConfigError


@dataclass
class TaskSpec:
    task_type: str  # e.g., 'code_generation', 'analysis', 'research', 'creative', 'general'
    urgency_ms: Optional[int] = None
    context_tokens: Optional[int] = None
    creative: bool = False
    strict_quality: bool = False


@dataclass
class SelectedRoute:
    category: str  # logical category from models.yaml (e.g., 'coding') or 'specialized.maverick'
    primary_spec: Dict[str, Any]
    fallback_specs: List[Dict[str, Any]]


class ModelRouter:
    """Rule-based router with fallback chain assembly from models.yaml.

    This class does not perform network calls; it only constructs call specs for Portkey.
    """

    def __init__(self, factory: Optional[ModelFactory] = None):
        self.factory = factory or ModelFactory()
        self.cfg = self.factory._cfg.get("model_routing", {})

    def route(self, spec: TaskSpec) -> SelectedRoute:
        # Category selection
        category, subkey = self._select_category(spec)

        # Build primary
        primary_client = (
            self.factory.create(category, subkey=subkey)
            if subkey is None
            else self.factory.create("specialized", subkey=subkey)
        )
        primary_spec = primary_client.build_call_spec()

        # Build fallbacks
        fallbacks: List[Dict[str, Any]] = self._build_fallbacks(category)

        return SelectedRoute(category if subkey is None else f"{category}.{subkey}", primary_spec, fallbacks)

    def _select_category(self, spec: TaskSpec) -> Tuple[str, Optional[str]]:
        # Urgent tasks route to fast operations
        if spec.urgency_ms is not None and spec.urgency_ms <= 500:
            return "fast_operations", None

        # Large context tasks
        if spec.context_tokens and spec.context_tokens >= 500_000:
            return "advanced_context", None

        # Creative tasks
        if spec.creative and spec.task_type in {"creative", "ideation", "design"}:
            return "specialized", "maverick"

        # Code tasks
        if spec.task_type in {"code_generation", "refactor", "fix", "test"}:
            return "coding", None

        # Deep analysis / reasoning
        if spec.task_type in {"analysis", "architecture", "decision", "reasoning"} or spec.strict_quality:
            return "reasoning", None

        # Exploration/research preference
        if spec.task_type in {"research", "exploration"}:
            return "specialized", "scout"

        # Default
        return "general", None

    def _build_fallbacks(self, category: str) -> List[Dict[str, Any]]:
        fallbacks: List[Dict[str, Any]] = []
        if category == "reasoning":
            entry = self.cfg.get("reasoning", {})
            chain = entry.get("fallback_chain", [])
            for model_name in chain:
                try:
                    fb = self.factory.create_for_model(model_name).build_call_spec()
                    fallbacks.append(fb)
                except Exception as e:
                    fallbacks.append({"error": str(e), "provider_model": model_name})
        elif category == "coding":
            entry = self.cfg.get("coding", {})
            secondary = entry.get("secondary")
            if secondary:
                try:
                    fb = self.factory.create_for_model(secondary).build_call_spec()
                    fallbacks.append(fb)
                except Exception as e:
                    fallbacks.append({"error": str(e), "provider_model": secondary})
        elif category == "general":
            entry = self.cfg.get("general", {})
            fb_model = entry.get("fallback")
            if fb_model:
                try:
                    fallbacks.append(self.factory.create_for_model(fb_model).build_call_spec())
                except Exception as e:
                    fallbacks.append({"error": str(e), "provider_model": fb_model})
        # specialized categories do not add fallbacks by default
        return fallbacks

