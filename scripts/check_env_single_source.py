#!/usr/bin/env python3
"""
Enforce single-source env policy: .env.master only.
Fails if code references deprecated env loading patterns.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = [
    "load_dotenv(",
    "~/.config/sophia/env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.security",
]

ALLOW_DIRS = {"docs", ".github", "deploy", "infra"}  # allowed to mention in docs/pipelines

def is_allowed(p: Path) -> bool:
    parts = set(p.parts)
    return any(x in parts for x in ALLOW_DIRS)

def main() -> int:
    bad: list[tuple[str, str]] = []
    for path in ROOT.rglob("*.*"):
        if path.is_dir():
            continue
        # Skip large/binary and node_modules, .git, etc.
        if any(s in path.parts for s in (".git", "node_modules", ".next", "venv", ".venv")):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for pat in FORBIDDEN:
            if pat in text and not is_allowed(path):
                bad.append((str(path), pat))
    if bad:
        print("❌ Forbidden env patterns detected:")
        for f, pat in bad:
            print(f" - {f}: contains '{pat}'")
        print("\nFix: remove alternate env loading; use <repo>/.env.master only.")
        return 1
    print("✅ Env policy check passed: single-source .env.master enforced.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

