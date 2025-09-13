from __future__ import annotations

from typing import Any, Dict, List


class AuditEngine:
    """Minimal audit validator stub.

    Compares proposed schema to current and surfaces risky changes.
    """

    def validate(self, current: Dict[str, Any], proposed: Dict[str, Any]) -> List[str]:
        warnings: List[str] = []
        current_names = {f.get("name") for f in current.get("fields", [])}
        for f in proposed.get("fields", []):
            name = f.get("name")
            if name not in current_names:
                warnings.append(f"New field '{name}' will be added")
        return warnings

