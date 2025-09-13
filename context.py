"""
Repository context builder and analyzer for Sophia CLI.

Builds a map of files, functions, classes, and imports, and surfaces issues.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any
import ast


@dataclass
class FileInfo:
    path: str
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)


class RepoContext:
    def __init__(self, root: Path):
        self.root = root
        self.files: Dict[str, FileInfo] = {}
        self.issues: List[Dict[str, Any]] = []

    def build_map_and_analyze(self) -> Dict[str, Any]:
        self.files.clear()
        self.issues.clear()
        for py in self.root.rglob("*.py"):
            s = str(py)
            if any(seg in s for seg in ("/.venv/", "/site-packages/", "/.git/")):
                continue
            try:
                content = py.read_text()
            except Exception as e:
                self.issues.append({"file": s, "issue": f"read_error: {e}"})
                continue
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                self.issues.append({"file": s, "error": f"SyntaxError: {e}"})
                continue

            functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            imps: List[str] = []
            for n in ast.walk(tree):
                if isinstance(n, ast.Import):
                    for a in n.names:
                        imps.append(a.name)
                elif isinstance(n, ast.ImportFrom):
                    mod = n.module or ""
                    imps.append(mod)
            self.files[s] = FileInfo(path=s, functions=functions, classes=classes, imports=imps)

        return {
            "files": {k: vars(v) for k, v in self.files.items()},
            "issues": self.issues,
        }

