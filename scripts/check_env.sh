#!/bin/bash
# SOPHIA Environment Check Script
# Sources .env.sophia if present and checks for required envs
set -e
if [ -f .env.sophia ]; then
  set -a
  . ./.env.sophia
  set +a
fi
missing=0
for v in LAMBDA_CLOUD_API_KEY GH_API_TOKEN CONTINUE_API_KEY; do
  if [ -z "${!v}" ]; then
    echo "❌ MISSING: $v"
    missing=1
  else
    echo "✓ $v is set (${#v} chars)"
  fi
done
if [ $missing -eq 1 ]; then
  echo "\nSTOP: One or more required environment variables are missing or empty."
  echo "To fix, add them as Codespaces secrets or to .env.sophia, then reload your shell."
  exit 1
else
  echo "All required environment variables are set."
fi
