#!/usr/bin/env python3
"""
MCP JWT token generator (no external deps)

Usage:
  python tools/mcp/token.py --aud filesystem --ttl 900 --sub dev

Reads secret from env MCP_JWT_SECRET. Emits a signed HS256 JWT.
"""
import argparse
import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def sign_hs256(secret: str, header: Dict[str, Any], payload: Dict[str, Any]) -> str:
    h = b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p = b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    msg = f"{h}.{p}".encode("ascii")
    sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).digest()
    return f"{h}.{p}.{b64url(sig)}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aud", default=os.getenv("MCP_JWT_AUD", "filesystem"))
    parser.add_argument("--sub", default=os.getenv("USER", "local"))
    parser.add_argument("--ttl", type=int, default=900)
    parser.add_argument("--secret", default=os.getenv("MCP_JWT_SECRET", ""))
    args = parser.parse_args()

    if not args.secret:
        raise SystemExit("MCP_JWT_SECRET not set; export it to generate tokens")

    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": args.sub, "aud": args.aud, "iat": now, "exp": now + args.ttl}
    token = sign_hs256(args.secret, header, payload)
    print(token)


if __name__ == "__main__":
    main()

