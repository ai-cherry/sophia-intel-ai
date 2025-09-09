#!/usr/bin/env python3
"""
Phase 1 health checker

Validates:
- Environment keys presence (PORTKEY_API_KEY + VKs referenced by config/models.yaml)
- MCP server health endpoints (8081, 8082, 8084; 8083 optional for Artemis FS)
- Redis/Postgres port reachability
- Portkey configuration (non-network, optional live probe if enabled)

Usage:
  source scripts/env.sh --quiet && python3 scripts/phase1_health.py [--live-portkey]
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
import time
from typing import Dict, List

import yaml


REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
MODELS_YAML = os.path.join(REPO_ROOT, "config", "models.yaml")


def load_models_yaml() -> Dict:
    if not os.path.isfile(MODELS_YAML):
        return {}
    with open(MODELS_YAML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_health(host: str, port: int, path: str = "/health", timeout: float = 1.5) -> bool:
    # Lightweight HTTP GET without external deps
    try:
        import http.client as httplib
        conn = httplib.HTTPConnection(host, port, timeout=timeout)
        conn.request("GET", path)
        resp = conn.getresponse()
        ok = (200 <= resp.status < 300)
        conn.close()
        return ok
    except Exception:
        return False


def check_env_keys(models_cfg: Dict) -> List[str]:
    required = ["PORTKEY_API_KEY"]
    # Scan config for VK names
    vk_names: List[str] = []
    mr = models_cfg.get("model_routing", {})
    for key, entry in mr.items():
        if isinstance(entry, dict):
            if "virtual_key" in entry and isinstance(entry["virtual_key"], str):
                vk_names.append(entry["virtual_key"])
            if "virtual_keys" in entry and isinstance(entry["virtual_keys"], list):
                vk_names.extend([x for x in entry["virtual_keys"] if isinstance(x, str)])
    required.extend(sorted(set(vk_names)))
    missing = [k for k in required if not os.getenv(k)]
    present = [k for k in required if os.getenv(k)]
    print("[env] Required keys:")
    for k in present:
        print(f"  ✓ {k}")
    for k in missing:
        print(f"  ✗ {k} (missing)")
    return missing


def check_mcp():
    print("[mcp] Health endpoints:")
    checks = [
        ("Memory", int(os.getenv("MCP_MEMORY_PORT", "8081"))),
        ("Filesystem (Sophia)", int(os.getenv("MCP_FS_SOPHIA_PORT", os.getenv("MCP_FS_PORT", "8082")))),
        ("Filesystem (Aux)", int(os.getenv("MCP_FS_ARTEMIS_PORT", "8083"))),
        ("Git", int(os.getenv("MCP_GIT_PORT", "8084"))),
        ("Vector", int(os.getenv("MCP_VECTOR_PORT", "8085"))),
        ("Graph", int(os.getenv("MCP_GRAPH_PORT", "8086"))),
    ]
    for name, port in checks:
        ok = http_health("localhost", port)
        mark = "✓" if ok else "✗"
        print(f"  {mark} {name} MCP on :{port}")


def check_infra():
    print("[infra] Ports:")
    redis_ok = port_open("localhost", 6379)
    pg_ok = port_open("localhost", 5432)
    print(f"  {'✓' if redis_ok else '✗'} Redis :6379")
    print(f"  {'✓' if pg_ok else '✗'} Postgres :5432")


def try_live_portkey_probe(enabled: bool):
    if not enabled:
        print("[portkey] Live probe skipped (use --live-portkey to enable)")
        return
    # Best-effort: only checks env presence here to avoid leaking info
    if not os.getenv("PORTKEY_API_KEY"):
        print("[portkey] PORTKEY_API_KEY missing; cannot probe.")
        return
    print("[portkey] Live probe requested, but network availability may vary in dev.\n          Consider provider-specific smoke tests in containers.")


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live-portkey", action="store_true", help="Attempt a live Portkey probe (optional)")
    args = ap.parse_args(argv)

    print("== Phase 1 Health Check ==")
    cfg = load_models_yaml()
    if not cfg:
        print("[config] config/models.yaml missing or empty")
    else:
        print("[config] models.yaml loaded: sections=", ", ".join(cfg.get("model_routing", {}).keys()))

    missing_env = check_env_keys(cfg)
    check_infra()
    check_mcp()
    try_live_portkey_probe(args.live_portkey)

    if missing_env:
        print("\nOne or more required env keys are missing. See ~/.config/artemis/env and scripts/env.sh")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
