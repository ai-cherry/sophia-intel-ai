#!/usr/bin/env python3
"""
Simple Redis-backed queue worker for vector indexing via MCP Vector server.

Queue: env VECTOR_INDEX_QUEUE (default: fs:index:queue)
Item:  JSON with either {"path": "..."} or {"content": "...", "metadata": {...}}

For each item, POST to http://localhost:<MCP_VECTOR_PORT>/index.
"""
from __future__ import annotations
import os
import json
import time
import signal
from typing import Any, Dict

import requests
import redis


def main() -> None:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")
    queue = os.getenv("VECTOR_INDEX_QUEUE", "fs:index:queue")
    vec_port = os.getenv("MCP_VECTOR_PORT", "8085")
    endpoint = f"http://localhost:{vec_port}/index"

    r = redis.Redis.from_url(redis_url)
    running = True

    def handle_sigterm(signum, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    print(f"[queue_worker] listening on {queue} → {endpoint}")
    while running:
        try:
            item = r.blpop(queue, timeout=5)
            if not item:
                continue
            _, raw = item
            try:
                payload: Dict[str, Any] = json.loads(raw.decode("utf-8"))
            except Exception:
                print(f"[queue_worker] bad JSON: {raw[:120]!r}")
                continue
            resp = requests.post(endpoint, json=payload, timeout=15)
            if resp.status_code in (200, 201):
                print(f"[queue_worker] indexed ok: {payload.get('path') or 'content'}")
            else:
                print(f"[queue_worker] index failed {resp.status_code}: {resp.text[:120]}")
        except Exception as e:
            print(f"[queue_worker] error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
