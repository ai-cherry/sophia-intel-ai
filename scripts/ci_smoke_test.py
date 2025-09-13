#!/usr/bin/env python3
"""
CI smoke tests for the multi-agent stack.
Runs quick health checks and minimal round-trips via the WebUI backend.
"""
import json
import os
import sys
import time
import requests
def wait_http(url: str, timeout_s: int = 60) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError(f"Timeout waiting for {url}")
def post_json(url: str, payload: dict, expected: int = 200) -> dict:
    r = requests.post(url, json=payload, timeout=15)
    if r.status_code != expected:
        raise RuntimeError(f"POST {url} got {r.status_code}: {r.text}")
    try:
        return r.json()
    except Exception:
        return {"raw": r.text}
def main() -> int:
    # 1) Wait for services
    wait_http("http://localhost:3001/health", 90)
    for port in (8081, 8082, 8084):  # memory, fs sophia, git
        wait_http(f"http://localhost:{port}/health", 60)
    # 2) Router smoke via WebUI
    result = post_json(
        "http://localhost:3001/agents/complete",
        {
            "task_type": "generation",
            "messages": [{"role": "user", "content": "Say hi"}],
        },
    )
    assert "text" in result, f"No text in completion: {result}"
    # 3) Memory store/search via WebUI tools
    content = "QC smoke marker"
    post_json(
        "http://localhost:3001/tools/invoke",
        {
            "capability": "memory",
            "action": "store",
            "params": {"namespace": "local:sophia", "content": content, "metadata": {"tag": "qc"}},
        },
    )
    search = post_json(
        "http://localhost:3001/tools/invoke",
        {
            "capability": "memory",
            "action": "search",
            "params": {"namespace": "local:sophia", "query": "QC smoke", "limit": 3},
        },
    )
    assert search.get("results"), f"Empty memory search result: {search}"
    # 4) FS list (sophia)
    fs = post_json(
        "http://localhost:3001/tools/invoke",
        {"capability": "fs", "scope": "sophia", "action": "list", "params": {"path": "."}},
    )
    assert "entries" in fs, "FS list missing entries"
    # 5) FS policy denial: attempt to write .env
    try:
        post_json(
            "http://localhost:3001/tools/invoke",
            {
                "capability": "fs",
                "scope": "sophia",
                "action": "write",
                "params": {"path": ".env", "content": "SHOULD_NOT_WRITE"},
            },
            expected=200,  # WebUI returns 200; underlying should return error envelope
        )
    except RuntimeError:
        # If WebUI proxies status codes, we catch here.
        pass
    else:
        # If response was 200, ensure denial present in payload
        # Fetch again but inspect error: Since /tools/invoke returns the raw tool JSON, check for 'error' or 'ok'
        denial = post_json(
            "http://localhost:3001/tools/invoke",
            {
                "capability": "fs",
                "scope": "sophia",
                "action": "write",
                "params": {"path": ".env", "content": "BLOCKED"},
            },
        )
        # Some stacks may wrap error; accept 'ok': False or error key
        if denial.get("ok") is True and "error" not in denial:
            raise RuntimeError(f"FS policy did not deny .env write: {denial}")
    print("QC smoke: PASS")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
