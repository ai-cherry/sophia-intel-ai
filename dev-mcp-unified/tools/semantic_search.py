from __future__ import annotations
from pathlib import Path
from typing import List


def semantic_search(query: str, root: str = ".") -> List[dict]:
    # Simple filename/content grep placeholder (replace with vector search)
    results = []
    root_p = Path(root)
    for p in root_p.rglob("*.py"):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
            if query.lower() in text.lower():
                results.append({"file": str(p), "match": query})
                if len(results) >= 20:
                    break
        except Exception:
            continue
    return results

