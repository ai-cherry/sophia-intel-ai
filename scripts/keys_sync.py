#!/usr/bin/env python3
"""
Sync .env.master against config/keys_registry.json:
- Preserve existing values
- Add any missing keys (empty placeholder)
- Order by registry sections with comments
"""
from __future__ import annotations
import os
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env.master"
REG_PATH = ROOT / "config/keys_registry.json"

def parse_env_lines(lines: list[str]) -> dict[str, str]:
    env: dict[str, str] = {}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env

def main() -> int:
    if not REG_PATH.exists():
        print(f"Missing registry: {REG_PATH}")
        return 1
    reg = json.loads(REG_PATH.read_text())
    sections: list[dict] = reg.get("order", [])
    existing: dict[str, str] = {}
    if ENV_PATH.exists():
        existing = parse_env_lines(ENV_PATH.read_text(encoding="utf-8", errors="ignore").splitlines())

    # Build new contents
    out: list[str] = []
    out.append("# Sophia Intel AI - Master Environment (single source)\n")
    out.append("# Managed by scripts/keys_sync.py; edit values as needed.\n")
    for sec in sections:
        name = sec.get("section", "")
        keys: list[str] = sec.get("keys", [])
        if name:
            out.append(f"\n# ==== {name} ====")
        for k in keys:
            val = existing.get(k, "")
            # Quote only if the existing contains spaces
            if val and (val.startswith('"') or val.startswith("'")):
                out.append(f"{k}={val}")
            else:
                out.append(f"{k}={val}")

    # Preserve any unknown keys at the end
    known = {k for sec in sections for k in sec.get("keys", [])}
    extras = [k for k in existing.keys() if k not in known]
    if extras:
        out.append("\n# ==== Extras (preserved) ====")
        for k in sorted(extras):
            out.append(f"{k}={existing[k]}")

    content = "\n".join(out) + "\n"
    ENV_PATH.write_text(content, encoding="utf-8")
    try:
        os.chmod(ENV_PATH, 0o600)
    except Exception:
        pass
    print(f"✅ Synced {ENV_PATH} using {REG_PATH}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

