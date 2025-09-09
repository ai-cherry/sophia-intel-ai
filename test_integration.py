#!/usr/bin/env python3
import sys
import urllib.request

targets = [
    ("API", "http://localhost:8003/health"),
    ("UI", "http://localhost:3000"),
    ("Telemetry", "http://localhost:5003/api/telemetry/health"),
    ("MCP Memory", "http://localhost:8081/health"),
    ("MCP FS", "http://localhost:8082/health"),
    ("MCP Git", "http://localhost:8084/health"),
]

def ok(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status == 200
    except Exception:
        return False

if __name__ == "__main__":
    failed = []
    for name, url in targets:
        if not ok(url):
            failed.append((name, url))
    if failed:
        for name, url in failed:
            print(f"FAIL: {name} {url}")
        sys.exit(1)
    print("All targets healthy.")
    sys.exit(0)

