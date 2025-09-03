from __future__ import annotations
from pathlib import Path
from typing import Dict


def extract_docs(file_path: str | None) -> Dict[str, str]:
    if not file_path:
        return {"error": "no_file"}
    p = Path(file_path)
    if not p.exists():
        return {"error": "file_not_found"}
    text = p.read_text(encoding="utf-8", errors="ignore")
    lines = [l for l in text.splitlines() if l.strip().startswith(("#","\"\"\""))]
    return {"summary": "\n".join(lines[:200])}

