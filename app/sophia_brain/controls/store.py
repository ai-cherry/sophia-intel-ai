from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


DEFAULT_CONTROLS: Dict[str, Any] = {
    "approvals": {"mode": "low_risk_auto"},  # low-risk auto-apply; risky require approval
    "dedup": {
        "order": ["content_hash", "row_keys", "fuzzy"],
        "row_keys": ["email", "external_id"],
        "fuzzy_fields": ["name", "title"],
        "fuzzy_threshold": 0.88,
    },
    "dock": {"enabled": True, "allowlist": []},
    "rate_strategy": {
        "dev": {"provider_aware_only": True},
        "prod": {"provider_aware": True, "soft_backoff": True},
    },
}


class ControlsStore:
    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.getenv("SOPHIA_BRAIN_CONTROLS", "data/brain_controls.json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(DEFAULT_CONTROLS)

    def load(self) -> Dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return DEFAULT_CONTROLS.copy()

    def save(self, controls: Dict[str, Any]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(controls, indent=2), encoding="utf-8")
        tmp.replace(self.path)

