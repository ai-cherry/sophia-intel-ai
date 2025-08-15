#!/usr/bin/env python3
import os, sys, httpx, json

URL = os.environ.get("QDRANT_URL")  # e.g. https://...qdrant.io:6333
KEY = os.environ.get("QDRANT_API_KEY")
if not URL or not KEY:
    print("MISSING: QDRANT_URL or QDRANT_API_KEY", file=sys.stderr); sys.exit(2)

try:
    with httpx.Client(timeout=10) as c:
        r = c.get(f"{URL}/collections", headers={"api-key": KEY})
        print("GET /collections ->", r.status_code)
        if r.status_code != 200:
            print(r.text[:500]); sys.exit(3)
        data = r.json()
        names = [c["name"] for c in data.get("result", {}).get("collections", [])]
        print("collections:", json.dumps(names))
        sys.exit(0)
except Exception as e:
    print("ERROR:", repr(e), file=sys.stderr); sys.exit(10)

