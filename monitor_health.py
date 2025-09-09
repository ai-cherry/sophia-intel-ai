#!/usr/bin/env python3
import time, sys
import urllib.request

targets = [
    ("API", "http://localhost:8003/health"),
    ("UI", "http://localhost:3000"),
    ("Telemetry", "http://localhost:5003/api/telemetry/health"),
    ("MCP Memory", "http://localhost:8081/health"),
    ("MCP FS", "http://localhost:8082/health"),
    ("MCP Git", "http://localhost:8084/health"),
]

def check(name, url):
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            ok = r.status == 200
            print(f"{name:12s} {url:45s} {'OK' if ok else r.status}")
    except Exception as e:
        print(f"{name:12s} {url:45s} FAIL - {e}")

if __name__ == "__main__":
    try:
        while True:
            print("\n=== Health ===")
            for n, u in targets:
                check(n, u)
            time.sleep(10)
    except KeyboardInterrupt:
        sys.exit(0)

