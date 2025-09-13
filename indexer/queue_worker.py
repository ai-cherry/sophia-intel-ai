#!/usr/bin/env python3
from __future__ import annotations
import os
import json
import time
import hashlib
from pathlib import Path
from typing import Any, Dict

import redis
import requests

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")
CLASS_NAME = os.getenv("VECTOR_CLASS", "BusinessDocument")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")
WORKSPACE_PATH = Path(os.getenv("WORKSPACE_PATH", ".")).resolve()

def headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if WEAVIATE_API_KEY:
        h["Authorization"] = f"Bearer {WEAVIATE_API_KEY}"
    return h

def ensure_class() -> None:
    r = requests.get(f"{WEAVIATE_URL}/v1/schema", headers=headers(), timeout=5)
    r.raise_for_status()
    classes = {c.get("class") for c in r.json().get("classes", [])}
    if CLASS_NAME in classes:
        return
    payload = {
        "class": CLASS_NAME,
        "vectorizer": "text2vec-openai",
        "properties": [
            {"name": "path", "dataType": ["text"]},
            {"name": "content", "dataType": ["text"]},
            {"name": "contentHash", "dataType": ["text"]},
            {"name": "metadata", "dataType": ["text"]},
            {"name": "timestamp", "dataType": ["number"]},
        ],
    }
    cr = requests.post(f"{WEAVIATE_URL}/v1/schema/classes", headers=headers(), data=json.dumps(payload), timeout=8)
    cr.raise_for_status()

def upsert(path: str, content: str) -> None:
    chash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    try:
        del_payload = {"where": {"path": ["contentHash"], "operator": "Equal", "valueString": chash}}
        requests.post(f"{WEAVIATE_URL}/v1/objects/{CLASS_NAME}/delete", headers=headers(), data=json.dumps(del_payload), timeout=8)
    except Exception:
        pass
    payload = {
        "class": CLASS_NAME,
        "properties": {
            "path": path,
            "content": content,
            "contentHash": chash,
            "metadata": json.dumps({}),
            "timestamp": time.time(),
        },
    }
    r = requests.post(f"{WEAVIATE_URL}/v1/objects", headers=headers(), data=json.dumps(payload), timeout=10)
    r.raise_for_status()

def main() -> None:
    r = redis.Redis.from_url(REDIS_URL)
    ensure_class()
    print("[indexer] watching fs:index:queue …")
    while True:
        try:
            _, raw = r.brpop("fs:index:queue", timeout=5) or (None, None)
            if not raw:
                continue
            evt = json.loads(raw)
            rel = evt.get("path", "")
            p = (WORKSPACE_PATH / rel).resolve()
            if not p.exists() or p.is_dir():
                continue
            try:
                content = p.read_text(encoding="utf-8")
            except Exception:
                continue
            upsert(rel, content)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[indexer] error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()

