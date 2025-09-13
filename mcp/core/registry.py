from __future__ import annotations
import hashlib
import os
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional
@dataclass
class ParseResult:
    language: str
    success: bool
    duration_ms: float
    details: Dict[str, Any]
class _ParserShim:
    """
    Lightweight parser wrapper that prefers Tree-sitter when available,
    and gracefully falls back to simple heuristics for unsupported envs.
    """
    def __init__(self, language: str):
        self.language = language
        self._ts_parser = None
        # Try best-effort Tree-sitter loading patterns without requiring build steps
        try:
            # Common convenience package (if present): tree_sitter_languages
            from tree_sitter_languages import get_language  # type: ignore
            from tree_sitter import Parser  # type: ignore
            ts_lang = get_language(language)
            p = Parser()
            p.set_language(ts_lang)
            self._ts_parser = p
        except Exception:
            # Fallback to simple parser
            self._ts_parser = None
    def parse(self, content: str) -> Dict[str, Any]:
        if self._ts_parser is not None:
            try:
                tree = self._ts_parser.parse(bytes(content, "utf-8"))
                return {
                    "mode": "tree_sitter",
                    "root": "ok",
                    "node_count_hint": getattr(tree.root_node, "child_count", 0),
                }
            except Exception as e:  # pragma: no cover
                return {"mode": "tree_sitter", "error": str(e)}
        # Simple fallback: count lines/tokens
        return {
            "mode": "fallback",
            "lines": content.count("\n") + 1 if content else 0,
            "tokens": len(content.split()),
        }
class UniversalRegistry:
    """
    Universal Registry for parsers with Tree-sitter priority.
    - Singleton pattern (__new__) ensures a single instance.
    - initialize_parsers() prepares per-language parsers.
    - get_parser(filepath) chooses an appropriate parser based on extension.
    - parse_with_cache(filepath, content) caches results when slow (>100ms).
    """
    _instance: Optional["UniversalRegistry"] = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._parsers: Dict[str, _ParserShim] = {}
        self._cache: Dict[str, ParseResult] = {}
        self._cache_enabled = True
        self._incremental = True
        self._cache_hash_algo = "sha256"
        self.initialize_parsers()
    def initialize_parsers(self) -> None:
        """
        Setup parsers for supported languages. Assumes incremental parsing
        behavior and caches results for improved performance.
        """
        # Languages in priority scope
        languages = ["python", "javascript", "typescript", "go", "rust"]
        for lang in languages:
            self._parsers[lang] = _ParserShim(lang)
    @staticmethod
    @lru_cache(maxsize=64)
    def _ext_to_lang(ext: str) -> Optional[str]:
        ext = ext.lower()
        return {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".go": "go",
            ".rs": "rust",
        }.get(ext)
    def get_parser(self, filepath: str) -> Optional[_ParserShim]:
        path = Path(filepath)
        lang = self._ext_to_lang(path.suffix)
        if not lang:
            # Fallback: python for unknown if file contains typical markers
            return None
        return self._parsers.get(lang)
    def _hash_content(self, content: str) -> str:
        h = hashlib.new(self._cache_hash_algo)
        h.update(content.encode("utf-8"))
        return h.hexdigest()
    def parse_with_cache(self, filepath: str, content: str) -> ParseResult:
        """
        Parse file content with optional caching. If parsing exceeds 100ms,
        result is cached keyed by (filepath, content-hash).
        """
        parser = self.get_parser(filepath)
        lang = "unknown"
        if parser is not None:
            # Infer language from mapping
            lang = next((k for k, v in self._parsers.items() if v is parser), "unknown")
        cache_key = None
        if self._cache_enabled:
            cache_key = f"{filepath}:{self._hash_content(content)}"
            if cache_key in self._cache:
                return self._cache[cache_key]
        start = time.perf_counter()
        details = parser.parse(content) if parser else {"mode": "none"}
        duration_ms = (time.perf_counter() - start) * 1000.0
        result = ParseResult(language=lang, success=True, duration_ms=duration_ms, details=details)
        # Cache if expensive
        if cache_key is not None and duration_ms > 100.0:
            self._cache[cache_key] = result
        return result
# Backwards-compatible accessor
def get_registry() -> UniversalRegistry:
    return UniversalRegistry()
