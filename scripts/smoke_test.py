#!/usr/bin/env python3
"""
Simple smoke test for local stack.

Checks:
- Sophia API /healthz (8003)
- Bridge API /health and /compile (8004)
- MCP /health (8081, 8082, 8084)
"""
import os
import sys
import json
import time
import argparse
import requests


def check(name: str, url: str, method: str = "GET", json_body=None) -> bool:
    try:
        if method == "GET":
            r = requests.get(url, timeout=3)
        else:
            r = requests.post(url, json=json_body, headers={"Authorization": "Bearer dev-token"}, timeout=5)
        ok = r.status_code == 200
        print(f"{name}: {'OK' if ok else f'FAIL ({r.status_code})'}")
        if not ok:
            try:
                print("  →", r.text[:200])
            except Exception:
                pass
        return ok
    except Exception as e:
        print(f"{name}: ERROR - {e}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bridge-token", default="dev-token")
    args = ap.parse_args()

    total = 0
    passed = 0

    total += 1; passed += check("API 8003 /healthz", "http://localhost:8003/healthz")
    total += 1; passed += check("Bridge 8004 /health", "http://localhost:8004/health")
    total += 1; passed += check(
        "Bridge 8004 /compile",
        "http://localhost:8004/compile",
        method="POST",
        json_body={"task": "smoke test planning", "team": "construction"}
    )
    total += 1; passed += check("MCP memory 8081 /health", "http://localhost:8081/health")
    total += 1; passed += check("MCP fs 8082 /health", "http://localhost:8082/health")
    total += 1; passed += check("MCP git 8084 /health", "http://localhost:8084/health")
    total += 1; passed += check("API 8003 /integrations/health", "http://localhost:8003/integrations/health")

    print(f"\nSummary: {passed}/{total} checks passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
