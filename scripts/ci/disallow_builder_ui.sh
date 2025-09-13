#!/usr/bin/env bash
set -euo pipefail

# Block reintroduction of the old Builder UI or scaffolding commands

fail=0
err() { echo "[DISALLOW-BUILDER][ERROR] $*"; fail=1; }

# 1) Disallow builder-agno-system directory in repo
if [ -d "builder-agno-system" ]; then
  err "Found forbidden directory: builder-agno-system/ (coding UI must be a separate local setup)"
fi

# 2) Disallow scripts that scaffold sophia-intel-app or builder UI via npx templates
if rg -n "npx\s+create-sophia-intel-app|create\s+builder\-agno\-system" scripts . 2>/dev/null; then
  err "Found UI scaffolding commands (npx create-sophia-intel-app or builder UI). Keep coding UI out of this repo."
fi

if [ $fail -ne 0 ]; then
  exit 2
fi
exit 0

