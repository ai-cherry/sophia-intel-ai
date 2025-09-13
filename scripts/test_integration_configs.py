#!/usr/bin/env python3
"""
Lightweight config smoke for Slack and Asana integrations using UnifiedConfigManager.
Does not perform network calls; validates that config is discoverable and consistent.
"""
from __future__ import annotations
import sys
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from config.unified_manager import get_config_manager


def show_integration(name: str) -> bool:
    cm = get_config_manager()
    cfg = cm.get_integration_config(name)
    enabled = bool(cfg.get("enabled"))
    tokens = {k: '***' for k, v in cfg.items() if 'token' in k or 'secret' in k}
    print(f"\n{name.upper()}:")
    print(f"  enabled: {enabled}")
    # Do not print tokens; just show presence
    print(f"  keys: {sorted(tokens.keys())}")
    return enabled


def main():
    ok = True
    slack_enabled = show_integration("slack")
    asana_enabled = show_integration("asana")
    linear_enabled = show_integration("linear")
    airtable_enabled = show_integration("airtable")
    # Basic consistency: if enabled, ensure at least one token-like key exists
    cm = get_config_manager()
    sc = cm.get_integration_config("slack")
    if slack_enabled and not any(sc.get(k) for k in ("bot_token", "slack_bot_token", "slack_api_token")):
        print("  WARN: Slack marked enabled but no token present")
        ok = False
    ac = cm.get_integration_config("asana")
    if asana_enabled and not ac.get("pat_token"):
        print("  WARN: Asana marked enabled but no pat_token present")
        ok = False
    lc = cm.get_integration_config("linear")
    if linear_enabled and not lc.get("api_key"):
        print("  WARN: Linear marked enabled but no api_key present")
        ok = False
    at = cm.get_integration_config("airtable")
    if airtable_enabled and not (at.get("api_key") and at.get("base_id")):
        print("  WARN: Airtable marked enabled but missing api_key or base_id")
        ok = False
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
