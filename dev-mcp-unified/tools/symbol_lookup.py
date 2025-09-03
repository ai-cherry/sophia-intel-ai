from __future__ import annotations
import ast
from pathlib import Path
from typing import Dict


def symbol_lookup(file_path: str | None) -> Dict[str, list]:
    if not file_path:
        return {"functions": [], "classes": []}
    p = Path(file_path)
    if not p.exists():
        return {"error": "file_not_found"}
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        return {"functions": funcs, "classes": classes}
    except Exception as e:
        return {"error": str(e)}

