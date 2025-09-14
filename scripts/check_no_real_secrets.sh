#!/usr/bin/env bash
set -euo pipefail

# Lightweight detector to avoid committing obvious real secrets.
# Allows known-safe placeholders like "example_*_key".

echo "[secrets] Scanning for likely secrets..."

PATTERN='(pk_live_|sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|-----BEGIN (RSA|PRIVATE) KEY-----)'

matches=$(rg -n -S -e "$PATTERN" \
  -g '!**/.git/**' -g '!docs/**' -g '!**/node_modules/**' -g '!LICENSE' || true)

safe_filtered=$(printf "%s" "$matches" | rg -v -e 'example_|EXAMPLE_' || true)

if [ -n "$safe_filtered" ]; then
  echo "[secrets] Potential secrets detected:" >&2
  printf "%s\n" "$safe_filtered" >&2
  exit 1
fi

echo "[secrets] OK: no obvious secrets detected."

