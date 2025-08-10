# scripts/agents_config.py
from fastapi import APIRouter
import os, re, pathlib, yaml, subprocess

router = APIRouter()

def run(cmd: str) -> str:
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return p.stdout + p.stderr

def scan_env_keys() -> set[str]:
    keys: set[str] = set()
    for p in pathlib.Path(".").rglob("*.py"):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in re.findall(r"os\.getenv\([\"']([A-Z0-9_]+)[\"']\)", text):
            keys.add(m)
    return keys

@router.post("/agent/config-sync")
def config_sync():
    keys = scan_env_keys()

    # Load YAML defaults
    cfg_path = pathlib.Path("config/sophia.yaml")
    cfg = {}
    if cfg_path.exists():
        cfg = yaml.safe_load(cfg_path.read_text()) or {}

    # Ensure .env.example exists
    env_example = pathlib.Path(".env.example")
    env_map = {}
    if env_example.exists():
        for line in env_example.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                env_map[k.strip()] = v

    # Add missing keys with safe placeholders (non-secret)
    changed = False
    for k in sorted(keys):
        if k not in env_map:
            env_map[k] = "CHANGE_ME"
            changed = True
        if k not in cfg:
            cfg[k] = ""  # non-secret default path

    if changed or True:
        # Write back .env.example
        env_lines = [f"{k}={env_map[k]}" for k in sorted(env_map)]
        env_example.write_text("\n".join(env_lines) + "\n")

        # Write back sophia.yaml (keep existing, add new keys)
        cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=True))

    diff = run("git diff")
    summary = "sync config keys between code, .env.example, and config/sophia.yaml"
    return {"summary": summary, "patch": diff}