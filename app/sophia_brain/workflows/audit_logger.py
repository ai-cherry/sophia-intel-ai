from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict


class AuditLogger:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or "logs")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def log(self, action: str, payload: Dict[str, Any]) -> None:
        entry = {"ts": time.time(), "action": action, "payload": payload}
        f = self.base_dir / "sophia_brain_audit.log"
        with f.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")

