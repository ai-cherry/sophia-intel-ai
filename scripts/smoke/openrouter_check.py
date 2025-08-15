#!/usr/bin/env python3
import os, sys, json, httpx

API_KEY = os.environ.get("OPENROUTER_API_KEY")
BASE = os.environ.get("OPENROUTER_BASE", "https://openrouter.ai/api/v1")
REQ_TIMEOUT = float(os.environ.get("SMOKE_HTTP_TIMEOUT", "12"))

if not API_KEY:
    print("MISSING: OPENROUTER_API_KEY", file=sys.stderr); sys.exit(2)

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "HTTP-Referer": "https://sophia-intel.ai",
    "X-Title": "Sophia Intel Smoke",
}
try:
    with httpx.Client(timeout=REQ_TIMEOUT) as c:
        r = c.get(f"{BASE}/models", headers=headers)
        print("GET /models ->", r.status_code)
        if r.status_code != 200:
            print(r.text[:500]); sys.exit(3)
        models = {m.get("id","") for m in r.json().get("data", [])}
        need = {"openai/gpt-4o", "openai/gpt-4o-mini"}
        missing = [m for m in need if m not in models]
        print("approved_present:", sorted(list(need - set(missing))))
        if missing:
            print("MISSING_APPROVED:", missing, file=sys.stderr); sys.exit(4)

        # quick echo chat
        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [{"role":"user","content":"ping"}],
            "max_tokens": 8
        }
        r = c.post(f"{BASE}/chat/completions", headers=headers, json=payload)
        print("POST /chat/completions ->", r.status_code)
        if r.status_code != 200:
            print(r.text[:500]); sys.exit(5)
        j = r.json()
        text = j.get("choices",[{}])[0].get("message",{}).get("content","")[:120]
        print("sample_reply:", json.dumps(text))
        sys.exit(0)
except Exception as e:
    print("ERROR:", repr(e), file=sys.stderr); sys.exit(10)

