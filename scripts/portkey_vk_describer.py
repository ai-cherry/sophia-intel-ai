#!/usr/bin/env python3
"""
Portkey VK Describer (safe, non-network by default)

Prints which VK env vars are configured based on config/models.yaml.
Optional: --print-values (redacts middle of keys), --live (reserved for future use).

Usage:
  source scripts/env.sh --quiet && python3 scripts/portkey_vk_describer.py [--print-values]
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, List

import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
MODELS_YAML = os.path.join(REPO_ROOT, "config", "models.yaml")


def load_models_yaml() -> Dict:
    if not os.path.isfile(MODELS_YAML):
        return {}
    with open(MODELS_YAML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def redact(value: str) -> str:
    if not value or len(value) < 8:
        return "(set)"
    return value[:4] + "…" + value[-4:]


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print-values", action="store_true", help="Print redacted env values")
    args = ap.parse_args(argv)

    cfg = load_models_yaml()
    mr = cfg.get("model_routing", {})

    vk_envs: List[str] = ["PORTKEY_API_KEY"]
    for _, entry in mr.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("virtual_key"):
            vk_envs.append(entry["virtual_key"])
        if isinstance(entry.get("virtual_keys"), list):
            vk_envs.extend([x for x in entry["virtual_keys"] if isinstance(x, str)])
    vk_envs = sorted(set(vk_envs))

    print("Portkey VK environment variables (from config/models.yaml):")
    missing = []
    for name in vk_envs:
        val = os.getenv(name)
        if val:
            if args.print_values:
                print(f"  ✓ {name} = {redact(val)}")
            else:
                print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name} (missing)")
            missing.append(name)

    if missing:
        print("\nNote: Add missing keys to ~/.config/artemis/env and re-source scripts/env.sh")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

