#!/usr/bin/env python3
"""
Mint a GitHub App installation access token for ai-cherry/sophia-intel-ai.

Reads env vars:
  APP_ID (or GITHUB_APP_ID)
  APP_PRIVATE_KEY_PATH (or GITHUB_APP_PRIVATE_KEY_PATH)
  APP_INSTALLATION_ID (or GITHUB_APP_INSTALLATION_ID)

If APP_INSTALLATION_ID is not set, lists installations for the App so you can
pick the correct one for your org/repo.

Prints the token to stdout on success.

Requires: pyjwt and requests
  pip install pyjwt cryptography requests
"""
import os
import sys
import time
from pathlib import Path

try:
    import jwt  # PyJWT
except Exception as e:
    sys.stderr.write("PyJWT is required. Install with: pip install pyjwt cryptography\n")
    raise
try:
    import requests
except Exception:
    sys.stderr.write("requests is required. Install with: pip install requests\n")
    raise


def env(*names: str, default: str | None = None) -> str | None:
    for n in names:
        v = os.getenv(n)
        if v:
            return v
    return default


def build_app_jwt(app_id: str, pem_path: str) -> str:
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + 540, "iss": app_id}
    key = Path(pem_path).read_text()
    return jwt.encode(payload, key, algorithm="RS256")


def list_installations(app_jwt: str) -> list[dict]:
    r = requests.get(
        "https://api.github.com/app/installations",
        headers={
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def create_installation_token(app_jwt: str, installation_id: str) -> dict:
    r = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers={
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def main() -> int:
    app_id = env("APP_ID", "GITHUB_APP_ID")
    pem_path = env("APP_PRIVATE_KEY_PATH", "GITHUB_APP_PRIVATE_KEY_PATH")
    installation_id = env("APP_INSTALLATION_ID", "GITHUB_APP_INSTALLATION_ID")

    if not app_id or not pem_path:
        sys.stderr.write("APP_ID and APP_PRIVATE_KEY_PATH must be set (or GITHUB_APP_ID / GITHUB_APP_PRIVATE_KEY_PATH).\n")
        return 2
    if not Path(pem_path).exists():
        sys.stderr.write(f"Private key not found: {pem_path}\n")
        return 2

    app_jwt = build_app_jwt(app_id, pem_path)

    if not installation_id:
        installs = list_installations(app_jwt)
        if not installs:
            sys.stderr.write("No installations found. Install the App on the repository first.\n")
            return 2
        sys.stderr.write("Installations for this App (pick id for ai-cherry/sophia-intel-ai):\n")
        for ins in installs:
            acc = ins.get("account", {})
            repos_url = ins.get("repositories_url")
            sys.stderr.write(f"  id={ins.get('id')} account={acc.get('login')} target_type={ins.get('target_type')} repos_url={repos_url}\n")
        return 0

    token = create_installation_token(app_jwt, installation_id)
    # Print the token only
    print(token.get("token", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

