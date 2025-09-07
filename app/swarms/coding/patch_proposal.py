from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

from app.mcp.clients.stdio_client import StdioMCPClient


def _ensure_trailing_newline(text: str) -> tuple[str, bool]:
    if text.endswith("\n"):
        return text, False
    return text + "\n", True


def _normalize_whitespace(text: str) -> tuple[str, bool]:
    # Example normalization: convert tabs to 4 spaces (non-destructive example)
    if "\t" not in text:
        return text, False
    return text.replace("\t", "    "), True


def propose_diff_for_file(client: StdioMCPClient, rel_path: str) -> dict[str, Any]:
    """
    Create a minimal, safe patch proposal for a file.
    Prioritizes: trailing newline and tab normalization.
    Returns a dict {path, has_changes, diff}
    """
    file_data = client.fs_read(rel_path)
    original = file_data.get("content", "")

    changed = False
    transformed = original

    transformed, ch1 = _ensure_trailing_newline(transformed)
    changed = changed or ch1
    transformed, ch2 = _normalize_whitespace(transformed)
    changed = changed or ch2

    if not changed:
        return {"path": rel_path, "has_changes": False, "diff": ""}

    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        transformed.splitlines(keepends=True),
        fromfile=f"a/{rel_path}",
        tofile=f"b/{rel_path}",
        lineterm="",
    )
    diff_text = "\n".join(diff)
    return {"path": rel_path, "has_changes": True, "diff": diff_text}


def propose_patches(
    client: StdioMCPClient, paths: list[str], max_files: int = 20
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    count = 0
    root = Path.cwd().resolve()
    for p in paths:
        rp = Path(p)
        if rp.is_dir():
            for f in rp.rglob("*"):
                if f.is_file():
                    try:
                        rel = str(f.resolve().relative_to(root))
                    except Exception:
                        rel = str(f)
                    results.append(propose_diff_for_file(client, rel))
                    count += 1
                    if count >= max_files:
                        return results
        elif rp.is_file():
            try:
                rel = str(rp.resolve().relative_to(root))
            except Exception:
                rel = str(rp)
            results.append(propose_diff_for_file(client, rel))
            count += 1
            if count >= max_files:
                return results
    return results
