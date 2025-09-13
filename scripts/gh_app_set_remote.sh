#!/usr/bin/env bash
set -euo pipefail

# Set git remote to use a short-lived GitHub App installation token over HTTPS.
# Requires: python3, pyjwt, requests; scripts/gh_app_token.py in PATH or this repo.
#
# Env vars:
#   APP_ID or GITHUB_APP_ID
#   APP_PRIVATE_KEY_PATH or GITHUB_APP_PRIVATE_KEY_PATH
#   APP_INSTALLATION_ID or GITHUB_APP_INSTALLATION_ID
#   REMOTE (default origin)
#   REPO (default ai-cherry/sophia-intel-ai)

REMOTE="${REMOTE:-origin}"
REPO="${REPO:-ai-cherry/sophia-intel-ai}"
ROOT="$(cd "$(dirname "$0")"/.. && pwd -P)"

TOKEN=$(python3 "$ROOT/scripts/gh_app_token.py")
if [ -z "$TOKEN" ]; then
  echo "Failed to mint installation token. Check env vars and dependencies." >&2
  exit 2
fi

git remote set-url "$REMOTE" "https://x-access-token:${TOKEN}@github.com/${REPO}.git"
echo "✅ Set $REMOTE to HTTPS with a temporary installation token."

