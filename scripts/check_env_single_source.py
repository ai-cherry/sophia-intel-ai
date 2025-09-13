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

# Limit scan to runtime codepaths to avoid false positives in docs/tests
SCAN_DIRS = [
    "app",
    "backend",
    "services",
    "config",
    "bin",
]

def main() -> int:
    bad: list[tuple[str, str]] = []
    candidates = []
    for d in SCAN_DIRS:
        base = (ROOT / d).resolve()
        if not base.exists():
            continue
        if base.is_file():
            candidates.append(base)
            continue
        for path in base.rglob("*.*"):
            candidates.append(path)
    # Add specific root-managed scripts
    for special in (ROOT / "sophia", ROOT / "unified-system-manager.sh"):
        if special.exists():
            candidates.append(special)
    for path in candidates:
        if path.is_dir():
            continue
        # Skip large/binary and node_modules, .git, etc.
        if any(s in path.parts for s in (".git", "node_modules", ".next", "venv", ".venv", "__pycache__", "backups", "docs", ".devcontainer", "tmp")):
            continue
        # Skip non-source files (allow only code/config types)
        if not any(str(path).endswith(ext) for ext in (".py", ".ts", ".tsx", ".js", ".sh", ".yaml", ".yml", ".json")):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for pat in FORBIDDEN:
            if pat in text:
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
