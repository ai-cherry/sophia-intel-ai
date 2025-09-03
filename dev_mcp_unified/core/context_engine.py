from __future__ import annotations
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


@dataclass
class ContextBundle:
    strategy: str
    files: Dict[str, str]
    symbols: Dict[str, Any] | None = None
    notes: str | None = None


class ContextEngine:
    def __init__(self, repo_root: Optional[str] = None, rules_path: Optional[str] = None):
        self.repo_root = Path(repo_root) if repo_root else Path.cwd()
        self.rules = self._load_rules(rules_path)

    def _load_rules(self, rules_path: Optional[str]) -> Dict[str, Any]:
        default = Path(__file__).resolve().parents[2] / "dev-mcp-unified" / "config" / "rules.yaml"
        path = Path(rules_path) if rules_path else default
        if path.exists():
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
        return {"rules": [], "defaults": {"provider": "claude", "context_strategy": "snippet_with_completions"}}

    def select_action(self, task: str) -> Dict[str, Any]:
        for rule in self.rules.get("rules", []):
            match = rule.get("match", {})
            if match.get("task") == task:
                return rule.get("action", {})
        return self.rules.get("defaults", {})

    def build_context(self, strategy: str, target_file: Optional[str] = None) -> ContextBundle:
        if strategy == "full_file_with_dependencies":
            return self._ctx_full_with_deps(target_file)
        if strategy == "ast_tree_with_symbols":
            return self._ctx_ast_symbols(target_file)
        if strategy == "snippet_with_completions":
            return self._ctx_snippet(target_file)
        if strategy == "pattern_matching_context":
            return self._ctx_pattern(target_file)
        return self._ctx_snippet(target_file)

    def _read_file(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    def _ctx_full_with_deps(self, target_file: Optional[str]) -> ContextBundle:
        files: Dict[str, str] = {}
        notes = ""
        if target_file:
            p = (self.repo_root / target_file).resolve()
            files[target_file] = self._read_file(p)
            try:
                tree = ast.parse(files[target_file])
                imports = [n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)]
                rels = []
                for name in imports[:5]:
                    mod_path = (self.repo_root / f"{name.replace('.', '/')}.py")
                    if mod_path.exists():
                        files[str(mod_path.relative_to(self.repo_root))] = self._read_file(mod_path)
                        rels.append(str(mod_path))
                notes = f"included_deps: {rels[:5]}"
            except Exception:
                pass
        return ContextBundle(strategy="full_file_with_dependencies", files=files, symbols=None, notes=notes)

    def _ctx_ast_symbols(self, target_file: Optional[str]) -> ContextBundle:
        files: Dict[str, str] = {}
        symbols: Dict[str, Any] = {}
        if target_file:
            p = (self.repo_root / target_file).resolve()
            src = self._read_file(p)
            files[target_file] = src
            try:
                tree = ast.parse(src)
                funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                symbols = {"functions": funcs[:50], "classes": classes[:50]}
            except Exception:
                symbols = {}
        return ContextBundle(strategy="ast_tree_with_symbols", files=files, symbols=symbols)

    def _ctx_snippet(self, target_file: Optional[str]) -> ContextBundle:
        files: Dict[str, str] = {}
        if target_file:
            p = (self.repo_root / target_file).resolve()
            content = self._read_file(p)
            files[target_file] = content[:8000]
        return ContextBundle(strategy="snippet_with_completions", files=files)

    def _ctx_pattern(self, target_file: Optional[str]) -> ContextBundle:
        files: Dict[str, str] = {}
        notes = "patterns: security, input_validation, secrets"
        if target_file:
            p = (self.repo_root / target_file).resolve()
            files[target_file] = self._read_file(p)
        return ContextBundle(strategy="pattern_matching_context", files=files, notes=notes)

