#!/usr/bin/env python3
"""
Lightweight, non-blocking warning for obvious secrets in YAML/JSON.
Prints warnings; always exits 0 to avoid blocking commits.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),  # generic sk- style
    re.compile(r"AIza[0-9A-Za-z\-_]{35}"),  # Google API key
    re.compile(r"xox[aboprs]-[A-Za-z0-9\-]{10,}"),  # Slack tokens
    re.compile(r"github_pat_[A-Za-z0-9_]{10,}"),  # GitHub PAT
    re.compile(r"pplx-[A-Za-z0-9]{20,}"),  # Perplexity
    re.compile(r"tgp_v1_[A-Za-z0-9_\-]{10,}"),  # Together
]

ALLOWED_FILES = {
    # Explicitly allow these to contain placeholders or redacted values
    "pulumi-esc-dev.yaml",
    "pulumi-esc-staging.yaml",
    "pulumi-esc-prod.yaml",
    "centralized_config.yaml",
}

def looks_text(p: Path) -> bool:
    return p.suffix.lower() in {".yml", ".yaml", ".json"}

def main(argv: list[str]) -> int:
    any_warning = False
    for arg in argv:
        p = Path(arg)
        if not p.exists() or not looks_text(p):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # Skip allowed files but still gently warn if pattern density is very high
        skip_strict = p.name in ALLOWED_FILES
        for pat in PATTERNS:
            for m in pat.finditer(text):
                any_warning = True
                print(f"[warn] Potential secret in {p}:{m.start()} → '{m.group(0)[:8]}…'", file=sys.stderr)
        if skip_strict and any_warning:
            print(f"[note] {p.name} contains values that look like secrets. Ensure they are rotated and managed via ESC.", file=sys.stderr)
    # Always pass (non-blocking)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

